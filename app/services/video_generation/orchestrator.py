"""
视频生成编排服务 (Orchestrator) - 终极全功能版
包含：脚本生成、图片绘制、质量检测、自动重绘、视频渲染、视频合并、配音合成
"""

import os
import json
import logging
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from app.services.llm.service import LLMService, ProviderType
from app.services.video_generation.base_client import VideoGenerationRequest
from app.services.video_generation.google_robust_client import RobustGoogleVideoClient
from app.services.image.google_imagen_generator import GoogleImagenGenerator
from app.services.video.processor import VideoProcessor
from app.services.audio.tts_service import TTSService
from app.services.timing.allocator import TimingAllocator
from app.prompts.video_generation import ScriptGenerationPrompt
from app.services.storage import get_storage_service
from app.core.config import settings

# 导入质量检查服务
try:
    from app.services.quality import VideoQualityChecker, QualityCheckConfig
    QUALITY_SERVICE_AVAILABLE = True
except ImportError:
    QUALITY_SERVICE_AVAILABLE = False

# DB Integration
from app.models.editor.database import EditorProjectDB, ProjectStatusEnum
from app.utils.database import SessionLocal

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    WAITING_CONFIRMATION = "waiting_confirmation"
    GENERATING_VIDEOS = "generating_videos"
    CHECKING_QUALITY = "checking_quality"
    REGENERATING = "regenerating"
    MERGING_VIDEOS = "merging_videos"
    GENERATING_NARRATION = "generating_narration"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class GenerationConfig:
    topic: str
    style: str = "专业"
    target_duration: int = 60
    shot_count: int = 6
    enable_narration: bool = False
    narration_voice: str = "chinese_female"
    enable_quality_check: bool = True
    quality_threshold: float = 0.5

@dataclass
class ShotInfo:
    sequence: int
    prompt: str
    duration: float
    shot_type: str = "medium shot"
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    status: str = "pending"
    quality_score: Optional[float] = None

@dataclass
class TaskState:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    script: str = ""
    shots: List[ShotInfo] = field(default_factory=list)
    final_video_path: Optional[str] = None
    narration_audio_path: Optional[str] = None
    logs: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    config: Optional[GenerationConfig] = None
    user_id: Optional[int] = None

    def add_log(self, message: str, level: str = "info"):
        self.logs.append({"timestamp": datetime.now().strftime("%H:%M:%S"), "message": message, "level": level})

    def to_dict(self) -> Dict[str, Any]:
        def format_path(path: Optional[str]) -> Optional[str]:
            if not path: return None
            # Fix for local paths
            clean_path = path.replace("\\", "/") 
            if clean_path.startswith("./"):
                clean_path = clean_path[2:]
            
            # If it looks like a relative path to outputs
            if clean_path.startswith("outputs/"):
                clean_path = "/" + clean_path
                
            return clean_path

        return {
            "taskId": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "script": self.script,
            "shots": [
                {
                    "sequence": s.sequence, "prompt": s.prompt, "duration": s.duration,
                    "shotType": s.shot_type, "imagePath": format_path(s.image_path),
                    "videoPath": format_path(s.video_path), "status": s.status, "qualityScore": s.quality_score
                } for s in self.shots
            ],
            "finalVideo": format_path(self.final_video_path),
            "narrationAudioPath": format_path(self.narration_audio_path),
            "config": {
                "topic": self.config.topic if self.config else "",
                "shot_count": self.config.shot_count if self.config else 6
            } if self.config else None,
            "logs": self.logs,
            "createdAt": self.created_at
        }

class VideoGenerationOrchestrator:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or settings.output_dir
        self.llm = LLMService(provider=ProviderType.GOOGLE)
        self.video_client = RobustGoogleVideoClient()
        self.image_generator = GoogleImagenGenerator()
        self.video_processor = VideoProcessor()
        self.tts_service = TTSService()
        self.timing_allocator = TimingAllocator()
        self.storage = get_storage_service()
        self.projects_dir = Path(self.output_dir) / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_dir(self, task_id: str) -> Path:
        d = self.projects_dir / task_id
        for sub in ["images", "videos", "audio"]:
            (d / sub).mkdir(parents=True, exist_ok=True)
        return d

    def _get_local_path(self, path_or_url: Optional[str]) -> Optional[str]:
        if not path_or_url: return None
        
        # 移除开头的 /
        clean_path = path_or_url
        if clean_path.startswith("/"):
            clean_path = clean_path[1:]
            
        # 如果是 URL
        if "http" in path_or_url and "/outputs/" in path_or_url:
            rel_path = path_or_url.split("/outputs/")[-1]
            return str(Path(settings.output_dir) / rel_path)
            
        # 如果是本地路径 (以 outputs/ 开头)
        if clean_path.startswith("outputs/"):
            # 确保是相对于当前工作目录的路径
            # settings.output_dir 通常是 "outputs"
            if clean_path.startswith(f"{settings.output_dir}/"):
                return clean_path
            else:
                # 这种情况应该比较少见，但以防万一
                return str(Path(settings.output_dir) / clean_path.replace("outputs/", "", 1))
                
        return path_or_url

    def _save_task_state(self, state: TaskState):
        p_dir = self._get_project_dir(state.task_id)
        with open(p_dir / "state.json", 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

    def load_task_state(self, task_id: str) -> Optional[TaskState]:
        file_path = self.projects_dir / task_id / "state.json"
        if not file_path.exists(): return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            state = TaskState(task_id=data.get("taskId"), status=TaskStatus(data.get("status")), progress=data.get("progress"), script=data.get("script", ""), final_video_path=data.get("finalVideo"), narration_audio_path=data.get("narrationAudioPath"), logs=data.get("logs", []), created_at=data.get("createdAt"))
            c = data.get("config")
            if c: state.config = GenerationConfig(topic=c.get("topic",""), shot_count=c.get("shot_count",6))
            for s in data.get("shots", []):
                state.shots.append(ShotInfo(sequence=s.get("sequence"), prompt=s.get("prompt"), duration=s.get("duration"), shot_type=s.get("shotType"), image_path=s.get("imagePath"), video_path=s.get("videoPath"), status=s.get("status"), quality_score=s.get("qualityScore")))
            return state
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return None

    async def generate_full_video(self, config: GenerationConfig, task_id: str, user_id: int):
        state = TaskState(task_id=task_id, config=config, user_id=user_id)
        self._save_task_state(state)
        try:
            # 1. 脚本生成
            state.add_log("🎬 正在构思脚本...")
            prompt = ScriptGenerationPrompt.build(topic=config.topic, shot_count=config.shot_count)
            res = await asyncio.to_thread(self.llm.call, messages=[{"role": "user", "content": prompt}])
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', res["content"], re.DOTALL)
            data = json.loads(json_match.group(1) if json_match else res["content"].strip())
            state.script = data["script"]
            state.shots = [ShotInfo(sequence=i+1, prompt=s["prompt"], duration=s.get("duration", 6)) for i, s in enumerate(data["shots"][:config.shot_count])]
            state.status = TaskStatus.GENERATING_SCRIPT
            self._save_task_state(state)

            # 2. 分镜图生成
            for i, shot in enumerate(state.shots):
                state.add_log(f"🎨 正在绘制分镜图 {i+1}/{len(state.shots)}...")
                l_path = await asyncio.to_thread(self.image_generator.generate_image, prompt=shot.prompt)
                if l_path:
                    shot.image_path = self.storage.save(l_path, f"projects/{task_id}/images/{os.path.basename(l_path)}")
                state.progress = 20 + (10 * (i+1) / len(state.shots))
                self._save_task_state(state)

            state.status = TaskStatus.WAITING_CONFIRMATION
            state.add_log("✅ 规划完成，等待确认")
            self._save_task_state(state)
            self._sync_to_db(state)
        except Exception as e:
            logger.error(f"任务失败: {e}")
            state.status = TaskStatus.FAILED
            self._save_task_state(state)

    async def continue_from_confirmation(self, state: TaskState, script: str, shots: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None):
        state.add_log("🚀 方案已确认，开始渲染视频...")
        state.status = TaskStatus.GENERATING_VIDEOS
        if options and state.config:
            state.config.enable_narration = options.get("enable_narration", False)
            state.config.narration_voice = options.get("narration_voice", "chinese_female")
        state.script = script
        state.shots = [ShotInfo(sequence=s.get("sequence"), prompt=s.get("prompt"), duration=s.get("duration"), shot_type=s.get("shotType", "medium shot"), image_path=s.get("imagePath")) for s in shots]
        self._save_task_state(state)

        try:
            # 1. 渲染视频片段
            for i, shot in enumerate(state.shots):
                state.add_log(f"🎥 正在渲染镜头 {i+1}...")
                local_img = self._get_local_path(shot.image_path)
                req = VideoGenerationRequest(prompt=shot.prompt, duration=min(shot.duration, 8.0), image_path=local_img)
                res = await self.video_client.generate_video(req)
                if res.success:
                    # 将生成的视频归档到项目目录
                    shot_filename = f"shot_{shot.sequence}_{uuid.uuid4().hex[:6]}.mp4"
                    project_video_path = self.storage.save(res.local_path, f"projects/{task_id}/videos/{shot_filename}")
                    
                    shot.video_path = project_video_path
                    shot.status = "success"
                    
                    # 【核心修复】获取并更新视频的真实时长
                    try:
                        # storage.save 返回的是 URL/路径，我们需要本地绝对路径来读取信息
                        # 如果是本地存储，project_video_path 可能是相对路径，也可能是 URL
                        # 我们直接用 res.local_path (原始文件) 或者重新解析路径
                        # 这里最稳妥的是用刚才生成的 res.local_path，但在 save 后可能被移除了
                        # 所以我们最好在 save 之前读取，或者重新定位文件
                        
                        # 由于 save 方法对于本地存储只是 copy，原始 res.local_path 还在（直到我们 remove）
                        # 我们先读取时长
                        video_info = self.video_processor.get_video_info(res.local_path)
                        if "duration" in video_info:
                            real_duration = float(video_info["duration"])
                            logger.info(f"Shot {shot.sequence} 真实时长: {real_duration}s (预设: {shot.duration}s)")
                            shot.duration = real_duration
                    except Exception as e:
                        logger.warning(f"获取视频真实时长失败: {e}")

                    # 尝试清理原始临时文件
                    try:
                        if os.path.exists(res.local_path):
                            os.remove(res.local_path)
                    except: pass
                else: shot.status = "failed"
                state.progress = 35 + (45 * (i+1) / len(state.shots))
                self._save_task_state(state)

            # 2. 质量检查与重绘 (恢复功能)
            if QUALITY_SERVICE_AVAILABLE and state.config and state.config.enable_quality_check:
                await self._stage_quality_check(state)

            # 3. 合并视频
            state.status = TaskStatus.MERGING_VIDEOS
            state.add_log("🔗 正在合并最终视频...")
            vids = [s.video_path for s in state.shots if s.status == "success" and s.video_path]
            if vids:
                f_name = f"final_{state.task_id}.mp4"
                f_local = str(self.projects_dir / state.task_id / "videos" / f_name)
                if await asyncio.to_thread(self.video_processor.merge_videos, vids, f_local):
                    state.final_video_path = self.storage.save(f_local, f"projects/{state.task_id}/videos/final.mp4")
            
            # 4. 配音
            if state.config and state.config.enable_narration:
                state.add_log("🎙️ 正在合成 AI 配音...")
                res = await self.tts_service.generate_speech(text=state.script, voice=state.config.narration_voice)
                if res["success"]:
                    state.narration_audio_path = self.storage.save(res["output_path"], f"projects/{state.task_id}/audio/voice.mp3")

            state.status = TaskStatus.COMPLETED
            state.progress = 100
            state.add_log("🎉 视频制作完成！")
            self._save_task_state(state)
            self._sync_to_db(state)
        except Exception as e:
            logger.error(f"渲染过程出错: {e}")
            state.status = TaskStatus.FAILED
            self._save_task_state(state)

    async def _stage_quality_check(self, state: TaskState):
        """恢复：视频质量检查与自动修复逻辑"""
        state.status = TaskStatus.CHECKING_QUALITY
        state.add_log("🔍 正在检查视频质量...")
        try:
            checker = VideoQualityChecker(config=QualityCheckConfig(min_acceptable_score=state.config.quality_threshold))
            for shot in state.shots:
                if shot.status == "success" and shot.video_path:
                    res = checker.check_video(shot.video_path, shot.prompt)
                    shot.quality_score = res.overall_score
                    if res.needs_regeneration:
                        state.add_log(f"⚠️ 镜头 {shot.sequence} 质量较低 ({res.overall_score:.2f})，正在尝试重绘...", "warning")
                        req = VideoGenerationRequest(prompt=shot.prompt, duration=min(shot.duration, 8.0), image_path=self._get_local_path(shot.image_path))
                        retry_res = await self.video_client.generate_video(req)
                        if retry_res.success:
                            shot.video_path = retry_res.local_path
                            state.add_log(f"✅ 镜头 {shot.sequence} 重绘成功", "success")
            checker.cleanup()
        except Exception as e:
            logger.warning(f"质量检查跳过: {e}")

    def _sync_to_db(self, state: TaskState):
        db = SessionLocal()
        try:
            pid = f"proj_{state.task_id}"
            project = db.query(EditorProjectDB).filter(EditorProjectDB.id == pid).first()
            if not project:
                # Ensure user_id is passed as string if it exists
                user_id_str = str(state.user_id) if state.user_id else None
                project = EditorProjectDB(
                    id=pid, 
                    name=state.config.topic if state.config else "Video", 
                    status=ProjectStatusEnum.DRAFT, 
                    created_at=datetime.utcnow(),
                    created_by=user_id_str  # Persist User ID
                )
                db.add(project)
            if state.status == TaskStatus.COMPLETED:
                project.status = ProjectStatusEnum.COMPLETED
                project.output_path = state.final_video_path
            db.commit()
        except: db.rollback()
        finally: db.close()

_orchestrator = None
def get_orchestrator():
    global _orchestrator
    if _orchestrator is None: _orchestrator = VideoGenerationOrchestrator()
    return _orchestrator