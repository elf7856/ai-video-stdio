"""
视频二创服务 (Video Recreation Service)
核心功能：视频理解 → 关键帧提取 → Prompt生成 → 风格转换生成
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.services.llm.service import LLMService, ProviderType
# 使用轻量级处理器（基于 ffmpeg，不需要 cv2/moviepy）
try:
    from app.services.video.processor_lite import VideoProcessor
except ImportError:
    from app.services.video.processor import VideoProcessor
from app.services.video.downloader import VideoDownloader
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RecreationConfig:
    """二创配置"""
    original_video_path: Optional[str] = None  # 原视频路径（本地文件）
    original_video_url: Optional[str] = None   # 原视频URL（在线视频）
    target_style: str = "专业"  # 目标风格（如：动漫风格、科幻风格、复古风格等）
    target_description: Optional[str] = None  # 目标描述（用户自定义）
    shot_count: int = 6  # 目标镜头数
    enable_keyframe_reference: bool = True  # 是否使用关键帧作为参考
    generation_mode: str = "autopilot"  # 生成模式

    def __post_init__(self):
        """验证配置"""
        if not self.original_video_path and not self.original_video_url:
            raise ValueError("必须提供 original_video_path 或 original_video_url 之一")


@dataclass
class VideoAnalysisResult:
    """视频分析结果"""
    overall_summary: str  # 整体摘要
    narrative_structure: str  # 叙事结构
    scenes: List[Dict[str, Any]]  # 场景列表
    key_elements: List[str]  # 关键元素
    mood: str  # 情绪氛围
    duration: float  # 视频时长


@dataclass
class RecreationResult:
    """二创结果"""
    success: bool
    task_id: Optional[str] = None
    analysis: Optional[VideoAnalysisResult] = None
    generated_shots: Optional[List[Dict[str, Any]]] = None
    keyframes: Optional[List[str]] = None
    error: Optional[str] = None


class VideoRecreationService:
    """视频二创服务"""

    def __init__(self):
        self.llm = LLMService(provider=ProviderType.GOOGLE)
        self.video_processor = VideoProcessor()
        self.video_downloader = VideoDownloader()
        self.output_dir = Path(settings.output_dir) / "recreation"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def prepare_video(
        self,
        config: RecreationConfig,
        task_dir: Path
    ) -> str:
        """
        准备视频文件（下载或使用本地文件）

        Args:
            config: 二创配置
            task_dir: 任务目录

        Returns:
            本地视频文件路径
        """
        # 如果提供了本地路径，直接使用
        if config.original_video_path:
            video_path = config.original_video_path
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")

            logger.info(f"使用本地视频: {os.path.basename(video_path)}")
            return video_path

        # 如果提供了 URL，下载视频
        if config.original_video_url:
            logger.info(f"🌐 从 URL 下载视频: {config.original_video_url}")

            # 创建下载目录
            download_dir = task_dir / "downloads"
            download_dir.mkdir(parents=True, exist_ok=True)

            # 下载视频
            result = await self.video_downloader.download_video(
                url=config.original_video_url,
                output_dir=str(download_dir)
            )

            if not result.get("success"):
                raise Exception(f"视频下载失败: {result.get('error', '未知错误')}")

            video_path = result.get("file_path")
            if not video_path or not os.path.exists(video_path):
                raise Exception("视频下载成功但文件不存在")

            logger.info(f"✅ 视频下载完成: {os.path.basename(video_path)}")
            return video_path

        raise ValueError("必须提供 original_video_path 或 original_video_url")

    async def analyze_video(
        self,
        video_path: str
    ) -> VideoAnalysisResult:
        """
        第一步：使用 Gemini 分析视频内容

        Args:
            video_path: 视频文件路径

        Returns:
            VideoAnalysisResult: 视频分析结果
        """
        logger.info(f"🎬 开始分析视频: {os.path.basename(video_path)}")

        # 获取视频基本信息
        video_info = self.video_processor.get_video_info(video_path)
        duration = float(video_info.get("duration", 0))

        # 构建分析提示词
        analysis_prompt = f"""请详细分析这个视频的内容，返回JSON格式：

{{
    "overall_summary": "视频整体内容摘要（2-3句话）",
    "narrative_structure": "叙事结构描述（开头-发展-高潮-结尾）",
    "scenes": [
        {{
            "sequence": 1,
            "timestamp_start": 0.0,
            "timestamp_end": 5.0,
            "description": "场景详细描述",
            "key_actions": "主要动作",
            "visual_elements": "视觉元素",
            "mood": "情绪氛围"
        }}
    ],
    "key_elements": ["关键元素1", "关键元素2"],
    "mood": "整体情绪氛围",
    "duration": {duration}
}}

要求：
1. 识别视频中的主要场景和镜头切换
2. 描述每个场景的视觉内容、动作、情绪
3. 提取关键元素（人物、物体、环境等）
4. 分析整体叙事结构和情绪氛围
"""

        # 调用 Gemini 视频理解 API
        try:
            # 获取 Google Adapter
            adapter = self.llm.adapters.get("google")
            if not adapter:
                raise Exception("Google适配器不可用")

            # 调用视频理解
            result = adapter.video_call(
                prompt=analysis_prompt,
                video_path=video_path
            )

            if not result["success"]:
                raise Exception(result.get("error", "视频分析失败"))

            # 解析 JSON 结果
            content = result["content"]

            # 尝试提取 JSON（可能包含在 markdown 代码块中）
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content

            analysis_data = json.loads(json_str)

            # 构建分析结果
            analysis_result = VideoAnalysisResult(
                overall_summary=analysis_data.get("overall_summary", ""),
                narrative_structure=analysis_data.get("narrative_structure", ""),
                scenes=analysis_data.get("scenes", []),
                key_elements=analysis_data.get("key_elements", []),
                mood=analysis_data.get("mood", ""),
                duration=analysis_data.get("duration", duration)
            )

            logger.info(f"✅ 视频分析完成，识别到 {len(analysis_result.scenes)} 个场景")

            return analysis_result

        except Exception as e:
            logger.error(f"视频分析失败: {e}")
            raise

    async def extract_keyframes(
        self,
        video_path: str,
        scenes: List[Dict[str, Any]],
        output_dir: Path
    ) -> List[str]:
        """
        第二步：提取关键帧

        Args:
            video_path: 视频文件路径
            scenes: 场景列表
            output_dir: 输出目录

        Returns:
            关键帧路径列表
        """
        logger.info(f"🖼️ 开始提取关键帧，共 {len(scenes)} 个场景")

        keyframes = []
        keyframe_dir = output_dir / "keyframes"
        keyframe_dir.mkdir(parents=True, exist_ok=True)

        for i, scene in enumerate(scenes):
            try:
                # 计算场景中间时间点
                start_time = scene.get("timestamp_start", 0)
                end_time = scene.get("timestamp_end", start_time + 5)
                mid_time = (start_time + end_time) / 2

                # 提取关键帧
                output_path = keyframe_dir / f"keyframe_{i+1}.jpg"

                success = await asyncio.to_thread(
                    self.video_processor.extract_frame,
                    video_path,
                    str(output_path),
                    mid_time
                )

                if success and output_path.exists():
                    keyframes.append(str(output_path))
                    logger.info(f"✅ 提取关键帧 {i+1}/{len(scenes)}: {mid_time:.1f}s")
                else:
                    logger.warning(f"⚠️ 关键帧 {i+1} 提取失败")
                    keyframes.append(None)

            except Exception as e:
                logger.error(f"提取关键帧 {i+1} 失败: {e}")
                keyframes.append(None)

        logger.info(f"✅ 关键帧提取完成，成功 {len([k for k in keyframes if k])} 个")

        return keyframes

    async def generate_recreation_prompts(
        self,
        analysis: VideoAnalysisResult,
        config: RecreationConfig
    ) -> List[Dict[str, Any]]:
        """
        第三步：生成二创 Prompts

        Args:
            analysis: 视频分析结果
            config: 二创配置

        Returns:
            镜头列表（包含 prompt）
        """
        logger.info(f"📝 开始生成二创 Prompts，目标风格: {config.target_style}")

        # 构建风格转换提示词
        style_prompt = f"""基于以下原视频分析结果，生成 {config.shot_count} 个镜头的视频生成提示词。

原视频分析：
- 整体摘要: {analysis.overall_summary}
- 叙事结构: {analysis.narrative_structure}
- 关键元素: {', '.join(analysis.key_elements)}
- 情绪氛围: {analysis.mood}

目标风格: {config.target_style}
{f'目标描述: {config.target_description}' if config.target_description else ''}

场景列表：
{json.dumps(analysis.scenes, ensure_ascii=False, indent=2)}

要求：
1. 保持原视频的叙事结构和核心内容
2. 将视觉风格转换为 {config.target_style}
3. 生成 {config.shot_count} 个镜头，每个镜头包含详细的视觉描述
4. 每个镜头的 prompt 要适合 text-to-video 或 image-to-video 生成
5. 保持镜头之间的连贯性

返回JSON格式：
{{
    "script": "整体脚本描述",
    "shots": [
        {{
            "sequence": 1,
            "prompt": "详细的视觉描述，包含风格、场景、动作、氛围",
            "duration": 5.0,
            "shot_type": "镜头类型（如：wide shot, close-up等）",
            "reference_scene": 1
        }}
    ]
}}
"""

        try:
            # 调用 LLM 生成 prompts
            result = await asyncio.to_thread(
                self.llm.call,
                messages=[{"role": "user", "content": style_prompt}]
            )

            if not result["success"]:
                raise Exception(result.get("error", "Prompt生成失败"))

            # 解析 JSON 结果
            content = result["content"]

            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content

            prompts_data = json.loads(json_str)

            shots = prompts_data.get("shots", [])

            logger.info(f"✅ 生成 {len(shots)} 个镜头的 Prompts")

            return shots

        except Exception as e:
            logger.error(f"Prompt生成失败: {e}")
            raise

    async def recreate_video(
        self,
        config: RecreationConfig,
        user_id: int
    ) -> RecreationResult:
        """
        完整的视频二创流程

        Args:
            config: 二创配置
            user_id: 用户ID

        Returns:
            RecreationResult: 二创结果
        """
        try:
            # 创建输出目录
            import uuid
            task_id = f"recreation_{uuid.uuid4().hex[:8]}"
            task_dir = self.output_dir / task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"🚀 开始视频二创任务: {task_id}")

            # 步骤0: 准备视频（下载或使用本地文件）
            logger.info("📥 步骤0: 准备视频文件...")
            video_path = await self.prepare_video(config, task_dir)

            # 步骤1: 视频分析
            logger.info("📊 步骤1: 分析原视频...")
            analysis = await self.analyze_video(video_path)

            # 步骤2: 提取关键帧（如果启用）
            keyframes = []
            if config.enable_keyframe_reference:
                logger.info("🖼️ 步骤2: 提取关键帧...")
                keyframes = await self.extract_keyframes(
                    video_path,
                    analysis.scenes,
                    task_dir
                )

            # 步骤3: 生成二创 Prompts
            logger.info("📝 步骤3: 生成二创 Prompts...")
            shots = await self.generate_recreation_prompts(analysis, config)

            # 步骤4: 关联关键帧到镜头
            if keyframes and config.enable_keyframe_reference:
                for i, shot in enumerate(shots):
                    # 找到对应的关键帧
                    ref_scene = shot.get("reference_scene", i + 1) - 1
                    if 0 <= ref_scene < len(keyframes) and keyframes[ref_scene]:
                        shot["imagePath"] = keyframes[ref_scene]

            # 保存分析结果
            analysis_file = task_dir / "analysis.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "analysis": {
                        "overall_summary": analysis.overall_summary,
                        "narrative_structure": analysis.narrative_structure,
                        "scenes": analysis.scenes,
                        "key_elements": analysis.key_elements,
                        "mood": analysis.mood,
                        "duration": analysis.duration
                    },
                    "shots": shots,
                    "config": {
                        "target_style": config.target_style,
                        "target_description": config.target_description,
                        "shot_count": config.shot_count
                    }
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 视频二创准备完成，任务ID: {task_id}")

            return RecreationResult(
                success=True,
                task_id=task_id,
                analysis=analysis,
                generated_shots=shots,
                keyframes=keyframes
            )

        except Exception as e:
            logger.error(f"视频二创失败: {e}")
            return RecreationResult(
                success=False,
                error=str(e)
            )


# 全局实例
_recreation_service = None


def get_recreation_service() -> VideoRecreationService:
    """获取视频二创服务实例"""
    global _recreation_service
    if _recreation_service is None:
        _recreation_service = VideoRecreationService()
    return _recreation_service
