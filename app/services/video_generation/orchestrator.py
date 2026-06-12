"""
视频生成编排服务 (Orchestrator) - 终极全功能版
包含：脚本生成、图片绘制、质量检测、自动重绘、视频渲染、视频合并、配音合成
"""

import os
import re
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
from app.services.video_generation.google_robust_client import RobustGoogleVideoClient, VertexAIVideoClient
from app.services.video_generation.agents.script_writer_agent import ScriptWriterAgent
from app.services.video_generation.agents.prompt_evaluator_agent import PromptEvaluatorAgent
from app.services.video_generation.agents.character_manager_agent import CharacterManagerAgent
from app.services.video_generation.agents.director_agent import DirectorAgent
from app.services.video_generation.generation_strategy_agent import GenerationStrategyAgent
from app.schemas.production_bible import ProductionBible
from app.services.image.google_imagen_generator import GoogleImagenGenerator
from app.services.ingest import VideoSourceService
# 使用轻量级处理器（基于 ffmpeg，不需要 cv2/moviepy）
from app.services.video.processor_lite import VideoProcessor
from app.services.audio.tts_service import TTSService
from app.services.timing.allocator import TimingAllocator
from app.services.storage import get_storage_service
from app.core.config import settings

# 导入新的解析器和配置
from app.services.video_generation.llm_response_parser import (
    LLMResponseParser,
    ScriptGenerationResponse
)
from app.config.prompts import VideoScriptPrompts, PromptConfig

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
    PARTIAL_SUCCESS = "partial_success"
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
    generation_mode: str = "manual"  # "manual" | "autopilot"
    additional_requirements: str = ""
    source_material: Optional[Dict[str, Any]] = None

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
    error: Optional[str] = None

@dataclass
class TaskState:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    script: str = ""
    script_metadata: Dict[str, Any] = field(default_factory=dict)
    shots: List[ShotInfo] = field(default_factory=list)
    final_video_path: Optional[str] = None
    narration_audio_path: Optional[str] = None
    logs: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    config: Optional[GenerationConfig] = None
    user_id: Optional[int] = None
    visual_style_guide: Dict[str, str] = field(default_factory=dict)
    bible: Optional[ProductionBible] = None
    strategy_decision: Dict[str, Any] = field(default_factory=dict)

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
            "scriptMetadata": self.script_metadata,
            "shots": [
                {
                    "sequence": s.sequence, "prompt": s.prompt, "duration": s.duration,
                    "shotType": s.shot_type, "imagePath": format_path(s.image_path),
                    "videoPath": format_path(s.video_path), "status": s.status,
                    "qualityScore": s.quality_score, "error": s.error
                } for s in self.shots
            ],
            "finalVideo": format_path(self.final_video_path),
            "narrationAudioPath": format_path(self.narration_audio_path),
            "config": {
                "topic": self.config.topic if self.config else "",
                "style": self.config.style if self.config else "",
                "target_duration": self.config.target_duration if self.config else 60,
                "shot_count": self.config.shot_count if self.config else 6,
                "enable_narration": self.config.enable_narration if self.config else False,
                "narration_voice": self.config.narration_voice if self.config else "chinese_female",
                "generation_mode": self.config.generation_mode if self.config else "manual",
                "additional_requirements": self.config.additional_requirements if self.config else "",
                "source_material": self.config.source_material if self.config else None,
            } if self.config else None,
            "sourceMaterial": self.config.source_material if self.config else None,
            "logs": self.logs,
            "createdAt": self.created_at,
            "visualStyleGuide": self.visual_style_guide,
            "bible": self.bible.model_dump() if self.bible else None,
            "strategyDecision": self.strategy_decision or None,
        }

class VideoGenerationOrchestrator:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or settings.output_dir
        self.llm = LLMService(provider=ProviderType.GOOGLE)
        # 优先用 Vertex AI，没有 vertex key 才降级到 AI Studio
        if settings.vertex_api_key or settings.vertex_project_id:
            self.video_client = VertexAIVideoClient()
        else:
            self.video_client = RobustGoogleVideoClient()
        self.image_generator = GoogleImagenGenerator()
        self.video_processor = VideoProcessor()
        self.tts_service = TTSService()
        self.timing_allocator = TimingAllocator()
        self.storage = get_storage_service()
        self.projects_dir = Path(self.output_dir) / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.script_writer = ScriptWriterAgent()
        self.prompt_evaluator = PromptEvaluatorAgent()
        self.character_manager = CharacterManagerAgent(output_dir=self.output_dir)
        self.director = DirectorAgent(output_dir=self.output_dir)
        self.strategy_agent = GenerationStrategyAgent()
        # 视频生成并发数：避免超出 API 速率限制
        self._video_semaphore = asyncio.Semaphore(2)

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

    async def _extract_visual_style(self, script: str, style: str) -> Dict[str, str]:
        """从脚本文本中提取视觉风格关键词，比硬编码更准确"""
        try:
            prompt = f"""Extract a concise visual style guide from this video script. Output ONLY JSON, no extra text.

Script: {script[:800]}

Output format:
{{"color_palette": "...", "lighting_style": "...", "visual_quality": "...", "overall_mood": "..."}}"""
            res = await asyncio.to_thread(
                self.llm.call,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = res.get("content", "")
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"视觉风格提取失败，使用默认值: {e}")
        return {
            "color_palette": "natural, professional tones",
            "lighting_style": "soft natural light",
            "visual_quality": "cinematic, high quality",
            "overall_mood": style
        }

    async def _extract_characters_from_script(self, script: str) -> List[Dict[str, Any]]:
        """从脚本中提取主要角色和视觉关键词"""
        try:
            prompt = f"""Identify main characters/subjects (people, animals, key objects) in this script that need visual consistency across shots.
Output ONLY a JSON array (empty array [] if none), no extra text.

Script: {script[:600]}

Output format:
[{{"name": "...", "description": "brief english visual description", "visual_keywords": ["kw1", "kw2", "kw3"], "consistency_required": true}}]"""
            res = await asyncio.to_thread(
                self.llm.call,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = res.get("content", "")
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"角色提取失败: {e}")
        return []

    def _inject_character_keywords(
        self,
        shots: List[ShotInfo],
        char_result: "CharacterManagementResult"  # type: ignore
    ) -> int:
        """将角色一致性关键词注入到 shot prompts 尾部，返回修改数量"""
        if not char_result.character_assets:
            return 0
        # 构建关键词后缀：所有需要一致性的角色的 visual_keywords
        consistency_keywords = []
        for asset in char_result.character_assets:
            if asset.consistency_level in ("high", "medium") and asset.visual_keywords:
                consistency_keywords.extend(asset.visual_keywords)
        if not consistency_keywords:
            return 0
        suffix = ", ".join(dict.fromkeys(consistency_keywords))  # 去重保序
        count = 0
        for shot in shots:
            if suffix.lower() not in shot.prompt.lower():
                shot.prompt = f"{shot.prompt}, {suffix}"
                count += 1
        return count

    def _inject_character_keywords_direct(self, shots: List[ShotInfo], characters: list) -> int:
        """直接从 ScriptWriterAgent 的 Character 列表注入关键词，无需 CharacterManagerAgent"""
        keywords = []
        for c in characters:
            kws = getattr(c, 'visual_keywords', None) or c.get('visual_keywords', []) if isinstance(c, dict) else []
            if not kws and hasattr(c, 'visual_keywords'):
                kws = c.visual_keywords
            if getattr(c, 'consistency_required', True) if not isinstance(c, dict) else c.get('consistency_required', True):
                keywords.extend(kws)
        if not keywords:
            return 0
        suffix = ", ".join(dict.fromkeys(keywords))  # 去重保序
        count = 0
        for shot in shots:
            if suffix.lower() not in shot.prompt.lower():
                shot.prompt = f"{shot.prompt}, {suffix}"
                count += 1
        return count

    def _simplify_prompt_for_retry(self, prompt: str) -> str:
        """第一次重试：去除复杂修饰词，保留核心主体+运动+基础风格"""
        # 移除过于具体的技术词汇，保留核心描述
        simplify_patterns = [
            r'\b(anamorphic|bokeh|film grain|lens flare|chromatic aberration|vignette)\b',
            r'\b(hyper-?realistic|ultra-?detailed|photorealistic)\b',
            r'\b\d+[Kk]\b',  # 移除 4K/8K 等
            r'\b(professional cinematography|professional photography)\b',
        ]
        simplified = prompt
        for pattern in simplify_patterns:
            simplified = re.sub(pattern, '', simplified, flags=re.IGNORECASE)
        # 清理多余逗号和空格
        simplified = re.sub(r',\s*,', ',', simplified).strip().strip(',').strip()
        return simplified

    def _minimal_fallback_prompt(self, original_prompt: str, duration: float) -> str:
        """第二次重试：极简 prompt，只保留主体+最基本的运动"""
        # 提取前 10 个词作为主体描述
        words = original_prompt.split()[:12]
        subject = ' '.join(words)
        motion = "slow cinematic camera movement" if duration >= 5 else "smooth motion"
        return f"{subject}, {motion}, cinematic"

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
            state = TaskState(task_id=data.get("taskId"), status=TaskStatus(data.get("status")), progress=data.get("progress"), script=data.get("script", ""), script_metadata=data.get("scriptMetadata", {}), final_video_path=data.get("finalVideo"), narration_audio_path=data.get("narrationAudioPath"), logs=data.get("logs", []), created_at=data.get("createdAt"))
            c = data.get("config")
            if c:
                state.config = GenerationConfig(
                    topic=c.get("topic", ""),
                    style=c.get("style", "专业"),
                    target_duration=c.get("target_duration", 60),
                    shot_count=c.get("shot_count", 6),
                    enable_narration=c.get("enable_narration", False),
                    narration_voice=c.get("narration_voice", "chinese_female"),
                    generation_mode=c.get("generation_mode", "manual"),
                    additional_requirements=c.get("additional_requirements", ""),
                    source_material=c.get("source_material") or data.get("sourceMaterial"),
                )
            for s in data.get("shots", []):
                state.shots.append(ShotInfo(
                    sequence=s.get("sequence"),
                    prompt=s.get("prompt"),
                    duration=s.get("duration"),
                    shot_type=s.get("shotType"),
                    image_path=s.get("imagePath"),
                    video_path=s.get("videoPath"),
                    status=s.get("status"),
                    quality_score=s.get("qualityScore"),
                    error=s.get("error"),
                ))
            state.visual_style_guide = data.get("visualStyleGuide", {})
            state.strategy_decision = data.get("strategyDecision") or {}
            bible_data = data.get("bible")
            if bible_data:
                try:
                    state.bible = ProductionBible.model_validate(bible_data)
                except Exception as e:
                    logger.warning(f"反序列化 bible 失败，忽略: {e}")
            return state
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return None

    def _strategy_decision_to_dict(self, decision: Any) -> Dict[str, Any]:
        """Serialize StrategyDecision without leaking Enum objects into state.json."""
        return {
            "strategy": decision.strategy.value,
            "reason": decision.reason,
            "steps": decision.steps,
            "estimated_cost": decision.estimated_cost,
            "estimated_time": decision.estimated_time,
            "requires_asset_search": decision.requires_asset_search,
            "requires_character_ref": decision.requires_character_ref,
            "requires_first_frames": decision.requires_first_frames,
            "confidence": decision.confidence,
        }

    async def _record_strategy_decision(self, state: TaskState, config: GenerationConfig) -> None:
        """Run strategy analysis in observe-only mode and persist the recommendation."""
        try:
            source_material = config.source_material or {}
            decision = await self.strategy_agent.decide_strategy({
                "topic": config.topic,
                "style": config.style,
                "target_duration": config.target_duration,
                "shot_count": config.shot_count,
                "generation_mode": config.generation_mode,
                "user_urls": [source_material.get("url")] if source_material.get("url") else [],
                "source_type": source_material.get("type"),
                "budget_constraint": "medium",
                "quality_requirement": "medium",
            })
            state.strategy_decision = self._strategy_decision_to_dict(decision)
            state.add_log(
                f"🧭 策略建议（仅记录）：{decision.strategy.value} | "
                f"置信度 {decision.confidence:.0%} | "
                f"预估 ${decision.estimated_cost:.2f} / {decision.estimated_time:.0f}秒",
                "info",
            )
            if decision.reason:
                state.add_log(f"🧭 策略理由：{decision.reason}", "info")
            self._save_task_state(state)
        except Exception as e:
            logger.warning(f"策略记录跳过: {e}")
            state.add_log(f"⚠️ 策略分析暂不可用，已跳过：{e}", "warning")
            self._save_task_state(state)

    async def _prepare_source_material(self, state: TaskState, config: GenerationConfig) -> None:
        """Hydrate video source URLs before script and storyboard generation."""
        source = config.source_material or {}
        if source.get("type") != "video" or source.get("videoAnalysis"):
            return

        url = source.get("url")
        if not url:
            return

        try:
            state.add_log("🔗 正在下载并分析视频来源...", "info")
            self._save_task_state(state)

            max_frames = min(max(config.shot_count or 6, 6), 12)
            analysis = await VideoSourceService().analyze_all_from_url(
                url,
                language="zh-CN",
                max_frames=max_frames,
            )
            if not analysis.get("success"):
                source["status"] = "failed"
                source["error"] = analysis.get("error", "视频来源分析失败")
                source["metadata"] = {
                    **(source.get("metadata") or {}),
                    "analysisStatus": "failed",
                }
                config.source_material = source
                state.config = config
                state.add_log(f"⚠️ 视频来源分析失败：{source['error']}", "warning")
                self._save_task_state(state)
                return

            config.source_material = self._video_analysis_to_source_material(source, analysis)
            state.config = config
            title = config.source_material.get("title") or config.source_material.get("url")
            keyframes = (config.source_material.get("videoAnalysis") or {}).get("keyframes") or []
            state.add_log(
                f"✅ 视频来源已分析：{title} | "
                f"{len(keyframes)} 个关键帧 | "
                f"转写={'可用' if self._video_transcript_text(config.source_material) else '不可用'}",
                "info",
            )
            self._save_task_state(state)
        except Exception as e:
            logger.warning(f"视频来源分析跳过: {e}")
            source["status"] = "failed"
            source["error"] = str(e)
            source["metadata"] = {
                **(source.get("metadata") or {}),
                "analysisStatus": "failed",
            }
            config.source_material = source
            state.config = config
            state.add_log(f"⚠️ 视频来源分析暂不可用，已使用 URL 文本继续：{e}", "warning")
            self._save_task_state(state)

    def _video_analysis_to_source_material(self, source: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        download = analysis.get("download") or {}
        video_understanding = analysis.get("videoUnderstanding") or {}
        transcript = analysis.get("transcript") or {}
        key_segments_result = analysis.get("keySegments") or {}
        keyframes_result = analysis.get("keyframes") or {}
        summary_result = analysis.get("summary") or {}
        structure_result = analysis.get("styleStructure") or {}

        summary_data = summary_result.get("summary") or {}
        if isinstance(summary_data, str):
            summary_text = summary_data
            summary_payload: Dict[str, Any] = {"summary": summary_data}
        else:
            summary_text = summary_data.get("summary") or ""
            summary_payload = summary_data

        keyframes = [
            {
                "index": frame.get("index"),
                "timestamp": frame.get("timestamp"),
                "framePath": frame.get("framePath"),
                "publicPath": frame.get("publicPath"),
            }
            for frame in (keyframes_result.get("keyframes") or [])
        ]

        transcript_text = transcript.get("transcript") or ""
        metadata = dict(source.get("metadata") or {})
        metadata.update({
            "platform": download.get("platform") or metadata.get("platform"),
            "videoInfo": download.get("videoInfo"),
            "download": {
                "videoPath": download.get("videoPath"),
                "publicPath": download.get("publicPath"),
                "duration": download.get("duration"),
            },
            "analysisStatus": "ready",
        })

        material = dict(source)
        material.update({
            "sourceId": analysis.get("sourceId") or source.get("sourceId"),
            "originalSourceId": source.get("sourceId"),
            "type": "video",
            "url": download.get("url") or source.get("url"),
            "title": download.get("title") or source.get("title"),
            "summary": summary_text or source.get("summary", ""),
            "status": "analyzed",
            "error": None,
            "videoPath": download.get("videoPath"),
            "publicPath": download.get("publicPath"),
            "duration": download.get("duration"),
            "platform": download.get("platform"),
            "videoInfo": download.get("videoInfo"),
            "metadata": metadata,
            "videoAnalysis": {
                "videoUnderstanding": {
                    "success": video_understanding.get("success", False),
                    "model": video_understanding.get("model"),
                    "mediaResolution": video_understanding.get("mediaResolution"),
                    "usedProxy": video_understanding.get("usedProxy"),
                    "modelVideoPath": video_understanding.get("modelVideoPath"),
                    "modelVideoPublicPath": video_understanding.get("modelVideoPublicPath"),
                    "originalFileSize": video_understanding.get("originalFileSize"),
                    "modelFileSize": video_understanding.get("modelFileSize"),
                    "analysis": video_understanding.get("analysis") or {},
                    "usage": video_understanding.get("usage") or {},
                    "error": video_understanding.get("error"),
                },
                "summary": summary_payload,
                "styleStructure": structure_result.get("analysis") or {},
                "recommendedSegments": {
                    "success": key_segments_result.get("success", False),
                    "strategy": key_segments_result.get("strategy"),
                    "segmentDurationRange": key_segments_result.get("segmentDurationRange") or {},
                    "segments": key_segments_result.get("segments") or [],
                    "error": key_segments_result.get("error"),
                },
                "transcript": {
                    "text": transcript_text,
                    "excerpt": self._truncate_text(transcript_text, 4000),
                    "confidence": transcript.get("confidence"),
                    "language": transcript.get("language"),
                    "provider": transcript.get("provider"),
                    "success": transcript.get("success", False),
                    "error": transcript.get("error"),
                },
                "keyframes": keyframes,
                "keyframeDescriptions": structure_result.get("keyframeDescriptions") or [],
            },
        })
        return material

    def _truncate_text(self, value: Optional[str], limit: int) -> str:
        text = re.sub(r"\s+", " ", value or "").strip()
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "..."

    def _video_transcript_text(self, source: Dict[str, Any]) -> str:
        return ((source.get("videoAnalysis") or {}).get("transcript") or {}).get("text") or ""

    def _build_creative_brief(self, config: GenerationConfig) -> str:
        """Combine the user's intent with optional source material."""
        sections = [f"用户需求：{config.topic.strip()}"]

        if config.additional_requirements:
            sections.append(f"补充要求：{config.additional_requirements.strip()}")

        source = config.source_material or {}
        if source:
            source_lines = [
                "参考来源：",
                f"- 类型：{source.get('type', 'unknown')}",
                f"- URL：{source.get('url', '')}",
            ]
            if source.get("title"):
                source_lines.append(f"- 标题：{source['title']}")
            if source.get("summary"):
                source_lines.append(f"- 摘要：{source['summary']}")
            if source.get("videoPath"):
                source_lines.append(f"- 本地视频：{source['videoPath']}")
            if source.get("duration"):
                source_lines.append(f"- 原视频时长：{source['duration']} 秒")
            video_info = source.get("videoInfo") or (source.get("metadata") or {}).get("videoInfo")
            if video_info:
                source_lines.append(f"- 视频信息：{json.dumps(video_info, ensure_ascii=False)[:600]}")
            video_analysis = source.get("videoAnalysis") or {}
            if video_analysis:
                summary = video_analysis.get("summary") or {}
                if summary:
                    source_lines.append(f"- 结构化摘要：{json.dumps(summary, ensure_ascii=False)[:1200]}")
                understanding = (video_analysis.get("videoUnderstanding") or {}).get("analysis") or {}
                if understanding:
                    source_lines.append(f"- 模型视频理解：{json.dumps(understanding, ensure_ascii=False)[:1800]}")
                recommended_segments = (video_analysis.get("recommendedSegments") or {}).get("segments") or []
                if recommended_segments:
                    source_lines.append(
                        f"- 推荐二创片段：{json.dumps(recommended_segments[:8], ensure_ascii=False)[:1800]}"
                    )
                transcript = video_analysis.get("transcript") or {}
                transcript_excerpt = transcript.get("excerpt") or self._truncate_text(transcript.get("text"), 2400)
                if transcript_excerpt:
                    source_lines.append(f"- 转写摘录：{transcript_excerpt[:2400]}")
                structure = video_analysis.get("styleStructure") or {}
                if structure:
                    source_lines.append(f"- 叙事/风格分析：{json.dumps(structure, ensure_ascii=False)[:1600]}")
                keyframe_descriptions = video_analysis.get("keyframeDescriptions") or []
                if keyframe_descriptions:
                    source_lines.append(
                        f"- 关键帧描述：{json.dumps(keyframe_descriptions[:6], ensure_ascii=False)[:1200]}"
                    )
                keyframes = video_analysis.get("keyframes") or []
                if keyframes:
                    source_lines.append(
                        f"- 关键帧路径：{json.dumps(keyframes[:6], ensure_ascii=False)[:1000]}"
                    )
            raw_content = (source.get("rawContent") or "").strip()
            if raw_content:
                source_lines.append(f"- 页面正文摘录：{raw_content[:1600]}")
            product_info = (source.get("metadata") or {}).get("productInfo")
            if product_info:
                source_lines.append(f"- 结构化信息：{json.dumps(product_info, ensure_ascii=False)[:800]}")
            sections.append("\n".join(source_lines))

        return "\n\n".join(sections)

    def _log_source_material(self, state: TaskState, config: GenerationConfig) -> None:
        source = config.source_material or {}
        if not source:
            return
        state.add_log(
            f"🔗 已接入来源：{source.get('type', 'unknown')} | "
            f"{source.get('title') or source.get('domain') or source.get('url')}",
            "info",
        )
        if source.get("summary"):
            state.add_log(f"🔗 来源摘要：{source['summary'][:220]}", "info")

    async def generate_full_video(self, config: GenerationConfig, task_id: str, user_id: int):
        state = TaskState(task_id=task_id, config=config, user_id=user_id)
        self._save_task_state(state)
        try:
            await self._prepare_source_material(state, config)
            await self._record_strategy_decision(state, config)
            self._log_source_material(state, config)
            creative_brief = self._build_creative_brief(config)

            # 1. DirectorAgent：一次产出全局蓝图 ProductionBible（脚本+分镜+角色参考图+风格）
            state.status = TaskStatus.GENERATING_SCRIPT
            state.progress = 5
            state.add_log("🎬 总导演开始构建全局蓝图...")
            self._save_task_state(state)
            try:
                bible, script_result = await self.director.build_bible(
                    brief=creative_brief,
                    task_id=task_id,
                    style=config.style,
                    target_duration=config.target_duration,
                    shot_count=config.shot_count,
                    generate_character_refs=False,
                )
                state.bible = bible
                state.script = script_result.script
                state.visual_style_guide = script_result.visual_style_guide
                state.script_metadata = self.script_writer.to_dict(script_result)

                # 用 bible 的 shot_graph 作为权威 shots（保留与旧 ShotInfo 兼容）
                shots_to_use = script_result.shots
                if bible.shot_graph:
                    state.shots = [
                        ShotInfo(sequence=s.sequence, prompt=s.prompt, duration=s.duration, shot_type=s.shot_type)
                        for s in bible.shot_graph
                    ]
                    char_with_refs = sum(1 for c in bible.characters if c.reference_image_path)
                    scene_with_refs = sum(1 for sc in bible.scenes if sc.reference_image_path)
                    state.add_log(
                        f"✅ 蓝图完成：{len(state.shots)} 镜头 / "
                        f"{len(bible.scenes)} 场景（{scene_with_refs} 张参考图） / "
                        f"{len(bible.characters)} 角色（{char_with_refs} 张参考图） / "
                        f"叙事={bible.narrative_arc}"
                    )

                    # 输出详细剧本信息到日志
                    meta = script_result.metadata
                    estimated_total = sum(s.duration for s in shots_to_use)
                    state.add_log(f"📋 预计时长：{estimated_total:.0f}秒（{estimated_total/60:.1f}分钟）", "info")
                    state.add_log(f"🎭 叙事结构：{meta.narrative.arc_type.value} | 主题：{meta.theme}", "info")
                    if meta.emotional_tone:
                        state.add_log(f"🎞️ 情绪：{meta.emotional_tone} | 受众：{meta.target_audience}", "info")

                    # 角色信息
                    if meta.characters:
                        chars_summary = "、".join([f"{c.name}({c.description[:20]}...)" if len(c.description) > 20 else f"{c.name}({c.description})" for c in meta.characters[:3]])
                        state.add_log(f"👥 角色：{chars_summary}", "info")

                    # 视觉风格
                    if script_result.visual_style_guide:
                        vsg = script_result.visual_style_guide
                        style_parts = []
                        if vsg.get("color_palette"): style_parts.append(f"色调={vsg['color_palette']}")
                        if vsg.get("lighting_style"): style_parts.append(f"光线={vsg['lighting_style']}")
                        if vsg.get("overall_mood"): style_parts.append(f"氛围={vsg['overall_mood']}")
                        if style_parts:
                            state.add_log(f"🎨 视觉风格：{' | '.join(style_parts)}", "info")

                    # 逐镜头输出
                    state.add_log("─" * 50, "info")
                    for i, s in enumerate(shots_to_use):
                        prompt_preview = s.prompt[:80] + "..." if len(s.prompt) > 80 else s.prompt
                        state.add_log(f"[镜头{s.sequence}] {s.shot_type} | {s.duration}s → {prompt_preview}", "info")
                    state.add_log("─" * 50, "info")

                    # 完整剧本文本
                    if script_result.script:
                        script_lines = script_result.script.strip().split("\n")
                        state.add_log("📝 剧本文案：", "info")
                        for line in script_lines[:20]:  # 最多输出20行
                            if line.strip():
                                state.add_log(f"  {line}", "info")
                        if len(script_lines) > 20:
                            state.add_log(f"  ... (共{len(script_lines)}行)", "info")
                else:
                    raise ValueError("ScriptWriterAgent 未生成分镜，启用降级方案")

            except Exception as e:
                # 降级：使用旧的 VideoScriptPrompts 方案
                logger.warning(f"ScriptWriterAgent 失败，降级到 VideoScriptPrompts: {e}")
                state.add_log("⚠️ 使用备用方案生成剧本...", "warning")
                prompt = VideoScriptPrompts.build_prompt(
                    topic=creative_brief, style=config.style,
                    target_duration=config.target_duration, shot_count=config.shot_count
                )
                res = await asyncio.to_thread(self.llm.call, messages=[{"role": "user", "content": prompt}], timeout=PromptConfig.TIMEOUT)
                parsed_response = LLMResponseParser.parse_script_generation_response(res["content"], fallback_shot_count=config.shot_count or 6)
                if not parsed_response:
                    parsed_response = LLMResponseParser.create_fallback_response(topic=config.topic, shot_count=config.shot_count or 6, target_duration=config.target_duration or 60)
                state.script = parsed_response.script
                shots_to_use = parsed_response.shots[:config.shot_count] if config.shot_count else parsed_response.shots
                state.shots = [ShotInfo(sequence=s.sequence, prompt=s.prompt, duration=s.duration, shot_type=s.shotType) for s in shots_to_use]
                state.visual_style_guide = {"color_palette": "natural, professional tones", "lighting_style": "soft natural light", "visual_quality": "cinematic, high quality", "overall_mood": config.style}

            state.status = TaskStatus.GENERATING_SCRIPT
            state.progress = 15
            self._save_task_state(state)

            # 角色关键词注入（纯文本操作，0次 LLM call）
            try:
                characters_raw = []
                if hasattr(script_result, 'metadata') and script_result.metadata.characters:
                    characters_raw = script_result.metadata.characters
                if characters_raw:
                    injected = self._inject_character_keywords_direct(state.shots, characters_raw)
                    if injected:
                        state.add_log(f"🎭 已为 {injected} 个镜头注入角色一致性关键词")
            except Exception as e:
                logger.warning(f"角色关键词注入跳过: {e}")

            # Prompt 前置质量评估与优化（在生成视频之前）
            try:
                state.add_log("🔍 评估并优化分镜 prompt...")
                state.progress = 20
                self._save_task_state(state)
                storyboard_dicts = [
                    {"sequence": s.sequence, "prompt": s.prompt, "duration": s.duration}
                    for s in state.shots
                ]
                characters_dicts = [
                    {"name": c.name, "description": c.description, "visual_keywords": c.visual_keywords}
                    for c in (script_result.metadata.characters if hasattr(script_result, 'metadata') else [])
                ]
                evaluation = await self.prompt_evaluator.evaluate_storyboard(
                    storyboard=storyboard_dicts,
                    visual_style_guide=state.visual_style_guide,
                    characters=characters_dicts or None
                )
                # 应用优化后的 prompt
                optimized_count = 0
                for shot_eval in evaluation.shot_evaluations:
                    if shot_eval.optimized_prompt:
                        idx = shot_eval.shot_id - 1
                        if 0 <= idx < len(state.shots):
                            state.shots[idx].prompt = shot_eval.optimized_prompt
                            state.shots[idx].quality_score = shot_eval.quality_score
                            optimized_count += 1
                if optimized_count:
                    state.add_log(f"✅ 已优化 {optimized_count} 个镜头的 prompt（整体质量: {evaluation.overall_quality_score:.2f}）")
                else:
                    state.add_log(f"✅ Prompt 质量评估完成（整体质量: {evaluation.overall_quality_score:.2f}）")
            except Exception as e:
                logger.warning(f"Prompt 评估跳过: {e}")

            self._save_task_state(state)

            # 2. 分镜图顺序生成（每个 shot 按 bible 取角色参考图，保证视觉一致性）
            state.add_log(f"🎨 顺序绘制 {len(state.shots)} 张分镜图...")
            state.progress = 25
            self._save_task_state(state)

            def _refs_for_shot(seq: int) -> List[str]:
                """从 bible 取该镜头需要的参考图本地路径列表"""
                if not state.bible:
                    return []
                raw_refs = state.bible.get_reference_images_for_shot(seq)
                local_refs: List[str] = []
                for r in raw_refs:
                    lp = self._get_local_path(r)
                    if lp and os.path.exists(lp):
                        local_refs.append(lp)
                return local_refs

            async def _generate_one_image(shot: ShotInfo, idx: int, attempt_label: str = "initial") -> bool:
                refs = _refs_for_shot(shot.sequence)
                if refs and state.bible:
                    breakdown = state.bible.get_reference_breakdown_for_shot(shot.sequence)
                    state.add_log(
                        f"  镜头 {shot.sequence} 使用 {len(refs)} 张参考图（场景 {breakdown['scene']} / 角色 {breakdown['character']}）锁定一致性",
                        "info",
                    )
                    self._save_task_state(state)
                for attempt in range(1):
                    try:
                        l_path = await self.image_generator.generate_image(
                            prompt=shot.prompt,
                            reference_images=refs or None,
                        )
                        if l_path:
                            shot.image_path = self.storage.save(l_path, f"projects/{task_id}/images/{os.path.basename(l_path)}")
                            state.add_log(f"✅ 分镜图 {idx+1} 生成完成", "success")
                            self._save_task_state(state)
                        return True
                    except Exception as e:
                        logger.error(f"分镜图 {idx+1} 生成失败 ({attempt_label}): {e}")
                        state.add_log(f"⚠️ 分镜图 {idx+1} 生成失败，进入重试队列：{e}", "warning")
                        self._save_task_state(state)
                        return False
                return False

            image_retry_queue: List[tuple[ShotInfo, int]] = []

            # 顺序生成；失败项放入任务内重试队列，不在底层做固定 QPM 节流。
            for i, shot in enumerate(state.shots):
                ok = await _generate_one_image(shot, i)
                if not ok:
                    image_retry_queue.append((shot, i))

            retry_delays = [3, 5, 10]
            for retry_round, delay in enumerate(retry_delays, start=1):
                if not image_retry_queue:
                    break
                state.add_log(
                    f"🔁 分镜图重试队列第 {retry_round} 轮："
                    f"{len(image_retry_queue)} 张等待 {delay}s 后重试",
                    "warning",
                )
                self._save_task_state(state)
                await asyncio.sleep(delay)

                pending: List[tuple[ShotInfo, int]] = []
                for shot, idx in image_retry_queue:
                    if shot.image_path:
                        continue
                    ok = await _generate_one_image(shot, idx, attempt_label=f"retry-{retry_round}")
                    if not ok:
                        pending.append((shot, idx))
                image_retry_queue = pending

            if image_retry_queue:
                failed_sequences = ", ".join(str(shot.sequence) for shot, _ in image_retry_queue)
                state.add_log(f"⚠️ 分镜图重试后仍失败：镜头 {failed_sequences}", "warning")
                self._save_task_state(state)

            state.progress = 30
            self._save_task_state(state)

            if config.generation_mode == "autopilot":
                # 托管模式：跳过人工确认，直接渲染视频
                state.add_log("🤖 托管模式：自动继续渲染视频...")
                shots_dicts = [
                    {"sequence": s.sequence, "prompt": s.prompt, "duration": s.duration,
                     "shotType": s.shot_type, "imagePath": s.image_path}
                    for s in state.shots
                ]
                await self.continue_from_confirmation(state, state.script, shots_dicts)
            else:
                state.status = TaskStatus.WAITING_CONFIRMATION
                state.add_log("✅ 规划完成，等待确认")
                self._save_task_state(state)
                self._sync_to_db(state)
        except Exception as e:
            logger.error(f"任务失败: {e}")
            state.add_log(f"❌ 任务失败：{e}", "error")
            state.status = TaskStatus.FAILED
            self._save_task_state(state)

    async def continue_from_confirmation(self, state: TaskState, script: str, shots: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None):
        state.add_log("🚀 方案已确认，开始渲染视频...")
        state.status = TaskStatus.GENERATING_VIDEOS
        if options and state.config:
            state.config.enable_narration = options.get("enable_narration", False)
            state.config.narration_voice = options.get("narration_voice", "chinese_female")
        state.script = script
        normalized_shots: List[Dict[str, Any]] = []
        for shot in shots:
            if isinstance(shot, dict):
                normalized_shots.append(shot)
            elif hasattr(shot, "model_dump"):
                normalized_shots.append(shot.model_dump())
            elif hasattr(shot, "dict"):
                normalized_shots.append(shot.dict())
            else:
                normalized_shots.append({
                    "sequence": getattr(shot, "sequence", None),
                    "prompt": getattr(shot, "prompt", ""),
                    "duration": getattr(shot, "duration", 5),
                    "shotType": getattr(shot, "shotType", "medium shot"),
                    "imagePath": getattr(shot, "imagePath", None),
                    "videoPath": getattr(shot, "videoPath", None),
                })
        state.shots = [
            ShotInfo(
                sequence=s.get("sequence"),
                prompt=s.get("prompt", ""),
                duration=s.get("duration", 5),
                shot_type=s.get("shotType", "medium shot"),
                image_path=s.get("imagePath"),
                video_path=s.get("videoPath"),
                status=s.get("status", "pending"),
                quality_score=s.get("qualityScore"),
            )
            for s in normalized_shots
        ]
        self._save_task_state(state)

        try:
            # 1. 渲染视频片段（并行，semaphore 限流）
            visual_style_guide = state.visual_style_guide or {"overall_mood": state.config.style if state.config else "专业"}
            state.add_log(f"🎥 开始并行渲染 {len(state.shots)} 个镜头（最多 2 个同时进行）...")
            completed_count = 0

            def _bible_context_for_shot(seq: int) -> Dict[str, Any]:
                """从 bible 取出当前镜头的 scene/characters/transition/上一镜头摘要"""
                ctx: Dict[str, Any] = {
                    "scene_context": None,
                    "characters_in_shot": None,
                    "previous_shot_summary": None,
                    "transition": None,
                }
                if not state.bible:
                    return ctx
                bible_shot = next((sg for sg in state.bible.shot_graph if sg.sequence == seq), None)
                if not bible_shot:
                    return ctx
                ctx["transition"] = bible_shot.continuity.value
                if bible_shot.characters_in_shot:
                    ctx["characters_in_shot"] = bible_shot.characters_in_shot
                scene = state.bible.get_scene(bible_shot.scene_id)
                if scene:
                    ctx["scene_context"] = {
                        "location": scene.location,
                        "time_of_day": scene.time_of_day,
                        "mood": scene.mood,
                    }
                # 上一镜头摘要：仅当 continuous/match_cut 时下游才用，但这里都填上
                prev = next(
                    (sg for sg in state.bible.shot_graph if sg.sequence == seq - 1),
                    None,
                )
                if prev:
                    ctx["previous_shot_summary"] = prev.prompt
                return ctx

            async def _render_one_shot(shot: ShotInfo) -> None:
                nonlocal completed_count
                async with self._video_semaphore:
                    state.add_log(f"🎬 渲染镜头 {shot.sequence}...")
                    local_img = self._get_local_path(shot.image_path)
                    duration = min(shot.duration, 8.0)

                    # 从 bible 取上下文
                    bible_ctx = _bible_context_for_shot(shot.sequence)
                    if bible_ctx["transition"] and bible_ctx["transition"] != "cut":
                        state.add_log(
                            f"  镜头 {shot.sequence} transition={bible_ctx['transition']}，prompt 将承接上一镜头",
                            "info",
                        )

                    # 生成 Veo 优化的视频 prompt（首帧已有图，专注运动描述；附带 bible 上下文）
                    video_prompt = shot.prompt
                    try:
                        video_prompt = await self.prompt_evaluator.convert_image_to_video_prompt(
                            image_prompt=shot.prompt,
                            duration=duration,
                            visual_style_guide=visual_style_guide,
                            has_reference_image=bool(local_img),
                            scene_context=bible_ctx["scene_context"],
                            characters_in_shot=bible_ctx["characters_in_shot"],
                            previous_shot_summary=bible_ctx["previous_shot_summary"],
                            transition=bible_ctx["transition"],
                        )
                        shot.prompt = video_prompt
                    except Exception as e:
                        logger.warning(f"镜头 {shot.sequence} prompt 转换失败，使用原始 prompt: {e}")

                    # 渲染，失败最多重试 2 次
                    MAX_ATTEMPTS = 3
                    for attempt in range(MAX_ATTEMPTS):
                        # 第 2 次重试用简化 prompt，降低失败概率
                        if attempt == 1:
                            retry_prompt = self._simplify_prompt_for_retry(video_prompt)
                            state.add_log(f"🔄 镜头 {shot.sequence} 第 {attempt+1} 次重试（简化 prompt）...", "warning")
                        elif attempt == 2:
                            retry_prompt = self._minimal_fallback_prompt(shot.prompt, duration)
                            state.add_log(f"🔄 镜头 {shot.sequence} 第 {attempt+1} 次重试（最小 prompt）...", "warning")
                        else:
                            retry_prompt = video_prompt

                        req = VideoGenerationRequest(prompt=retry_prompt, duration=duration, image_path=local_img)
                        res = await self.video_client.generate_video(req)

                        if res.success:
                            shot_filename = f"shot_{shot.sequence}_{uuid.uuid4().hex[:6]}.mp4"
                            project_video_path = self.storage.save(res.local_path, f"projects/{state.task_id}/videos/{shot_filename}")
                            shot.video_path = project_video_path
                            shot.status = "success"
                            try:
                                video_info = self.video_processor.get_video_info(res.local_path)
                                if "duration" in video_info:
                                    shot.duration = float(video_info["duration"])
                            except Exception: pass
                            try:
                                if os.path.exists(res.local_path):
                                    os.remove(res.local_path)
                            except: pass
                            suffix = f"（第 {attempt+1} 次尝试）" if attempt > 0 else ""
                            state.add_log(f"✅ 镜头 {shot.sequence} 渲染完成{suffix}", "success")
                            break
                        else:
                            if attempt < MAX_ATTEMPTS - 1:
                                shot.error = res.error_message
                                if res.error_message:
                                    state.add_log(
                                        f"⚠️ 镜头 {shot.sequence} 第 {attempt+1} 次生成失败：{res.error_message[:300]}",
                                        "warning",
                                    )
                                await asyncio.sleep(3)
                            else:
                                shot.status = "failed"
                                shot.error = res.error_message
                                state.add_log(f"❌ 镜头 {shot.sequence} 渲染失败（已重试 {MAX_ATTEMPTS} 次）", "error")

                    completed_count += 1
                    state.progress = 35 + (45 * completed_count / len(state.shots))
                    self._save_task_state(state)

            await asyncio.gather(*[_render_one_shot(shot) for shot in state.shots])

            # 2. 合并视频
            state.status = TaskStatus.MERGING_VIDEOS
            state.add_log("🔗 正在合并最终视频...")
            vids = [self._get_local_path(s.video_path) for s in state.shots if s.status == "success" and s.video_path]
            vids = [v for v in vids if v and os.path.exists(v)]
            merge_success = False
            if vids:
                f_name = f"final_{state.task_id}.mp4"
                f_local = str(self.projects_dir / state.task_id / "videos" / f_name)
                if await asyncio.to_thread(self.video_processor.merge_videos, vids, f_local):
                    state.final_video_path = self.storage.save(f_local, f"projects/{state.task_id}/videos/final.mp4")
                    merge_success = True
                else:
                    state.add_log("❌ 最终视频合并失败，已保留成功生成的单镜头视频", "error")
            else:
                state.add_log("❌ 没有可用于合并的视频片段", "error")
            
            # 4. 配音
            if state.config and state.config.enable_narration:
                state.add_log("🎙️ 正在合成 AI 配音...")
                res = await self.tts_service.generate_speech(text=state.script, voice=state.config.narration_voice)
                if res["success"]:
                    state.narration_audio_path = self.storage.save(res["output_path"], f"projects/{state.task_id}/audio/voice.mp3")

            successful_shots = [s for s in state.shots if s.status == "success" and s.video_path]
            failed_shots = [s for s in state.shots if s.status == "failed"]

            if merge_success and len(successful_shots) == len(state.shots):
                state.status = TaskStatus.COMPLETED
                state.progress = 100
                state.add_log("🎉 视频制作完成！")
            elif successful_shots:
                state.status = TaskStatus.PARTIAL_SUCCESS
                state.progress = 100
                failed_list = ", ".join(str(s.sequence) for s in failed_shots) or "无"
                state.add_log(
                    f"⚠️ 视频生成部分完成：成功 {len(successful_shots)}/{len(state.shots)} 个镜头，失败镜头：{failed_list}",
                    "warning",
                )
            else:
                state.status = TaskStatus.FAILED
                state.progress = 100
                state.add_log("❌ 视频生成失败：所有镜头均未生成成功", "error")
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
            elif state.status in (TaskStatus.FAILED, TaskStatus.PARTIAL_SUCCESS):
                project.status = ProjectStatusEnum.FAILED
                project.output_path = state.final_video_path
            db.commit()
        except: db.rollback()
        finally: db.close()

_orchestrator = None
def get_orchestrator():
    global _orchestrator
    if _orchestrator is None: _orchestrator = VideoGenerationOrchestrator()
    return _orchestrator
