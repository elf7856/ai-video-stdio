"""
Standalone video source processing service.

Each step is intentionally callable by itself so we can validate the video URL
pipeline before wiring it into the main generation flow.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.audio.asr_service import asr_service
from app.services.llm.service import LLMService, ProviderType
from app.services.video.downloader import VideoDownloader
from app.services.video.processor_lite import VideoProcessor

logger = logging.getLogger(__name__)


class VideoSourceService:
    """Download, transcribe, frame-sample, summarize, and analyze a video source."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_root = Path(output_dir or settings.output_dir) / "video_sources"
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.downloader = VideoDownloader()
        self.processor = VideoProcessor()
        self.llm = LLMService(provider=ProviderType.GOOGLE)

    async def download_from_url(self, url: str, source_id: Optional[str] = None) -> Dict[str, Any]:
        """Download a URL to a local file and return metadata."""
        source_id = source_id or self._new_source_id()
        source_dir = self._source_dir(source_id)
        downloads_dir = source_dir / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        result = await self.downloader.download_video(url=url, output_dir=str(downloads_dir))
        if not result.get("success"):
            return {
                "success": False,
                "sourceId": source_id,
                "url": url,
                "step": "download",
                "error": result.get("error", "视频下载失败"),
            }

        video_path = result.get("file_path")
        info = self.get_video_info(video_path) if video_path else {"success": False}
        payload = {
            "success": True,
            "sourceId": source_id,
            "url": url,
            "videoPath": video_path,
            "publicPath": self._public_path(video_path),
            "title": result.get("title") or (Path(video_path).stem if video_path else ""),
            "duration": result.get("duration") or (info.get("videoInfo") or {}).get("duration"),
            "platform": result.get("platform"),
            "videoInfo": info.get("videoInfo"),
        }
        self._write_json(source_dir / "download.json", payload)
        return payload

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Read local video metadata with ffprobe."""
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "step": "info", "error": "视频文件不存在"}

        info = self.processor.get_video_info(video_path)
        if "error" in info:
            return {"success": False, "step": "info", "error": info["error"]}

        return {
            "success": True,
            "videoPath": video_path,
            "publicPath": self._public_path(video_path),
            "videoInfo": info,
        }

    async def transcribe_video(
        self,
        video_path: str,
        language: str = "zh-CN",
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe a local video file with the configured ASR providers."""
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "step": "transcribe", "error": "视频文件不存在"}

        try:
            result = await asr_service.transcribe_video(video_path, language=language, provider=provider)
            payload = {
                "success": True,
                "videoPath": video_path,
                "transcript": result.text,
                "confidence": result.confidence,
                "timestamps": result.timestamps,
                "language": result.language,
                "provider": result.provider,
            }
            self._write_json(self._artifact_dir_for_video(video_path) / "transcript.json", payload)
            return payload
        except Exception as e:
            logger.error(f"视频转写失败: {e}")
            return {"success": False, "step": "transcribe", "error": str(e)}

    def extract_keyframes(
        self,
        video_path: str,
        max_frames: int = 12,
        strategy: str = "uniform",
        timestamps: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Extract keyframes from a local video."""
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "step": "keyframes", "error": "视频文件不存在"}

        info_result = self.get_video_info(video_path)
        if not info_result.get("success"):
            return info_result

        video_info = info_result["videoInfo"]
        duration = float(video_info.get("duration") or 0)
        if duration <= 0:
            return {"success": False, "step": "keyframes", "error": "无法读取视频时长"}

        max_frames = max(1, min(max_frames, 30))
        times = self._normalize_timestamps(timestamps, duration, max_frames)
        if not times:
            times = self._sample_times(duration, max_frames, strategy)
            strategy = "uniform"
        frames_dir = self._artifact_dir_for_video(video_path) / "keyframes"
        frames_dir.mkdir(parents=True, exist_ok=True)

        keyframes: List[Dict[str, Any]] = []
        for index, timestamp in enumerate(times, start=1):
            output_path = frames_dir / f"keyframe_{index:03d}.jpg"
            ok = self._extract_single_frame(video_path, timestamp, output_path)
            if ok:
                keyframes.append({
                    "index": index,
                    "timestamp": timestamp,
                    "framePath": str(output_path),
                    "publicPath": self._public_path(str(output_path)),
                })

        payload = {
            "success": True,
            "videoPath": video_path,
            "duration": duration,
            "strategy": strategy,
            "sourceTimestamps": "model_understanding" if timestamps else "uniform",
            "keyframes": keyframes,
        }
        self._write_json(self._artifact_dir_for_video(video_path) / "keyframes.json", payload)
        return payload

    async def understand_video_with_model(
        self,
        video_path: str,
        language: str = "zh-CN",
        max_segments: int = 12,
    ) -> Dict[str, Any]:
        """Use a multimodal model to understand video structure and representative timestamps."""
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "step": "video_understanding", "error": "视频文件不存在"}

        model_name = settings.video_understanding_model or "gemini-3.1-flash-lite"
        try:
            info_result = self.get_video_info(video_path)
            video_duration = float((info_result.get("videoInfo") or {}).get("duration") or 0)
            model_video_path = self._prepare_video_understanding_input(video_path)
            parsed, usage = await asyncio.to_thread(
                self._call_video_understanding_model,
                model_video_path,
                model_name,
                language,
                max_segments,
            )
            parsed = self._sanitize_video_understanding_analysis(parsed, video_duration, max_segments)
            payload = {
                "success": True,
                "videoPath": video_path,
                "modelVideoPath": model_video_path,
                "modelVideoPublicPath": self._public_path(model_video_path),
                "usedProxy": model_video_path != video_path,
                "originalFileSize": os.path.getsize(video_path) if os.path.exists(video_path) else None,
                "modelFileSize": os.path.getsize(model_video_path) if os.path.exists(model_video_path) else None,
                "model": model_name,
                "mediaResolution": settings.video_understanding_media_resolution,
                "analysis": parsed,
                "usage": usage,
            }
            self._write_json(self._artifact_dir_for_video(video_path) / "video_understanding.json", payload)
            return payload
        except Exception as e:
            logger.warning(f"模型视频理解失败: {e}")
            return {
                "success": False,
                "step": "video_understanding",
                "videoPath": video_path,
                "model": model_name,
                "error": str(e),
            }

    async def summarize_video(
        self,
        video_path: str,
        transcript: Optional[str] = None,
        language: str = "zh-CN",
    ) -> Dict[str, Any]:
        """Generate a concise summary from transcript and video metadata."""
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "step": "summary", "error": "视频文件不存在"}

        info_result = self.get_video_info(video_path)
        if not info_result.get("success"):
            return info_result

        if transcript is None:
            transcript_result = await self.transcribe_video(video_path, language=language)
            transcript = transcript_result.get("transcript", "") if transcript_result.get("success") else ""

        prompt = f"""请基于以下视频信息生成二创前置摘要。只返回 JSON。

视频信息：
{json.dumps(info_result.get("videoInfo", {}), ensure_ascii=False)}

转写文本：
{(transcript or "")[:5000]}

返回格式：
{{
  "summary": "3-5句话概括视频内容",
  "main_topic": "核心主题",
  "target_audience": "可能受众",
  "key_points": ["要点1", "要点2", "要点3"],
  "usable_for_recreation": true
}}
"""
        parsed = await self._json_llm(prompt, fallback={
            "summary": self._fallback_summary(info_result.get("videoInfo", {}), transcript),
            "main_topic": Path(video_path).stem,
            "target_audience": "未知",
            "key_points": [],
            "usable_for_recreation": True,
        })
        payload = {
            "success": True,
            "videoPath": video_path,
            "summary": parsed,
            "transcriptUsed": bool(transcript),
        }
        self._write_json(self._artifact_dir_for_video(video_path) / "summary.json", payload)
        return payload

    async def analyze_style_structure(
        self,
        video_path: str,
        transcript: Optional[str] = None,
        keyframes: Optional[List[Dict[str, Any]]] = None,
        language: str = "zh-CN",
    ) -> Dict[str, Any]:
        """Analyze narrative structure and reusable visual style."""
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "step": "structure", "error": "视频文件不存在"}

        info_result = self.get_video_info(video_path)
        if not info_result.get("success"):
            return info_result

        if transcript is None:
            transcript_result = await self.transcribe_video(video_path, language=language)
            transcript = transcript_result.get("transcript", "") if transcript_result.get("success") else ""

        if keyframes is None:
            frames_result = self.extract_keyframes(video_path, max_frames=8)
            keyframes = frames_result.get("keyframes", []) if frames_result.get("success") else []

        frame_notes = await self._describe_keyframes(keyframes[:4])
        prompt = f"""你是视频二创分析师。请分析原视频的叙事结构和可复用风格，只返回 JSON。

视频信息：
{json.dumps(info_result.get("videoInfo", {}), ensure_ascii=False)}

转写文本：
{(transcript or "")[:5000]}

关键帧描述：
{json.dumps(frame_notes, ensure_ascii=False)}

返回格式：
{{
  "overall_summary": "整体内容摘要",
  "narrative_structure": "开头-发展-高潮-结尾结构",
  "hook": "开头钩子",
  "pacing": "节奏判断",
  "visual_style": {{
    "color_palette": "色彩",
    "lighting": "光线",
    "camera": "镜头语言",
    "editing": "剪辑方式",
    "mood": "情绪氛围"
  }},
  "recreation_strategy": "二创时建议保留和改写的点",
  "scenes": [
    {{
      "sequence": 1,
      "timestamp_start": 0,
      "timestamp_end": 5,
      "description": "场景描述",
      "purpose": "叙事作用"
    }}
  ]
}}
"""
        parsed = await self._json_llm(prompt, fallback={
            "overall_summary": self._fallback_summary(info_result.get("videoInfo", {}), transcript),
            "narrative_structure": "未知",
            "hook": "",
            "pacing": "",
            "visual_style": {
                "color_palette": "",
                "lighting": "",
                "camera": "",
                "editing": "",
                "mood": "",
            },
            "recreation_strategy": "",
            "scenes": [],
        })
        payload = {
            "success": True,
            "videoPath": video_path,
            "analysis": parsed,
            "keyframeDescriptions": frame_notes,
            "transcriptUsed": bool(transcript),
        }
        self._write_json(self._artifact_dir_for_video(video_path) / "style_structure.json", payload)
        return payload

    async def select_key_segments(
        self,
        video_path: str,
        video_understanding: Optional[Dict[str, Any]] = None,
        transcript: Optional[str] = None,
        language: str = "zh-CN",
        target_count: int = 8,
        min_duration: float = 2.0,
        max_duration: float = 15.0,
    ) -> Dict[str, Any]:
        """Select reusable source segments for review, recreation, and future V2V models."""
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "step": "segments", "error": "视频文件不存在"}

        info_result = self.get_video_info(video_path)
        if not info_result.get("success"):
            return info_result

        duration = float((info_result.get("videoInfo") or {}).get("duration") or 0)
        target_count = max(1, min(int(target_count or 8), 20))
        min_duration = max(0.5, float(min_duration or 2.0))
        max_duration = max(min_duration, min(float(max_duration or 15.0), 30.0))

        understanding_analysis = self._extract_understanding_analysis(video_understanding)
        fallback_segments = self._fallback_key_segments(
            understanding_analysis,
            duration=duration,
            target_count=target_count,
            min_duration=min_duration,
            max_duration=max_duration,
        )

        prompt = f"""你是短视频二创的片段选择 Agent。请从原视频中挑选最值得复用或改写的关键片段，只返回 JSON。

语言：{language}
原视频时长：{duration:.2f} 秒
目标片段数量：最多 {target_count} 个
单段时长要求：{min_duration:.1f}-{max_duration:.1f} 秒。超过上限时，请围绕代表时间点裁出最有信息量的窗口。

模型视频理解：
{json.dumps(understanding_analysis, ensure_ascii=False)[:6000]}

转写摘录：
{(transcript or "")[:3000]}

返回格式：
{{
  "strategy": "整体选择策略",
  "segments": [
    {{
      "sequence": 1,
      "start": 0,
      "end": 8,
      "representativeTimestamp": 3,
      "type": "hook|context|demo|turning_point|evidence|payoff|reference|skip",
      "title": "片段标题",
      "description": "片段内容",
      "reason": "为什么值得保留/改写/跳过",
      "suggestedUse": "keep|rewrite|remix|reference|skip",
      "priority": 5
    }}
  ]
}}

选择标准：
- 优先选择开头钩子、论点变化、演示步骤、视觉主体明确、能代表原视频风格的片段。
- 对低信息密度、等待、纯加载、重复解释、片尾客套内容给出 skip，除非它对理解流程必要。
- suggestedUse=reference 的片段应适合作为后续 video-to-video / reference video 的 2-15 秒素材。
- representativeTimestamp 必须在 start 和 end 之间。
"""
        parsed = await self._json_llm(prompt, fallback={
            "strategy": "基于模型视频理解的语义段，优先保留开头、演示步骤、转折和可参考视觉片段。",
            "segments": fallback_segments,
        })
        segments = self._sanitize_key_segments(
            parsed.get("segments") if isinstance(parsed, dict) else [],
            duration=duration,
            target_count=target_count,
            min_duration=min_duration,
            max_duration=max_duration,
            fallback_segments=fallback_segments,
        )
        payload = {
            "success": True,
            "videoPath": video_path,
            "duration": duration,
            "strategy": parsed.get("strategy") if isinstance(parsed, dict) else "",
            "segmentDurationRange": {
                "min": min_duration,
                "max": max_duration,
            },
            "segments": segments,
        }
        self._write_json(self._artifact_dir_for_video(video_path) / "segments.json", payload)
        return payload

    async def analyze_all_from_url(
        self,
        url: str,
        language: str = "zh-CN",
        max_frames: int = 12,
    ) -> Dict[str, Any]:
        """Convenience orchestration for manual testing; each step is still available separately."""
        download = await self.download_from_url(url)
        if not download.get("success"):
            return download

        video_path = download["videoPath"]
        video_understanding = await self.understand_video_with_model(
            video_path,
            language=language,
            max_segments=max_frames,
        )
        duration = float((download.get("videoInfo") or {}).get("duration") or download.get("duration") or 0)
        representative_timestamps = self._timestamps_from_video_understanding(
            video_understanding,
            max_frames=max_frames,
            duration=duration,
        )
        transcript = await self.transcribe_video(video_path, language=language)
        key_segments = await self.select_key_segments(
            video_path,
            video_understanding=video_understanding,
            transcript=transcript.get("transcript") if transcript.get("success") else "",
            language=language,
            target_count=max_frames,
        )
        segment_timestamps = self._timestamps_from_key_segments(
            key_segments,
            max_frames=max_frames,
            duration=duration,
        )
        frames = self.extract_keyframes(
            video_path,
            max_frames=max_frames,
            strategy="recommended_segments" if segment_timestamps else ("model_understanding" if representative_timestamps else "uniform"),
            timestamps=segment_timestamps or representative_timestamps,
        )
        summary = await self.summarize_video(
            video_path,
            transcript=transcript.get("transcript") if transcript.get("success") else "",
            language=language,
        )
        structure = await self.analyze_style_structure(
            video_path,
            transcript=transcript.get("transcript") if transcript.get("success") else "",
            keyframes=frames.get("keyframes", []),
            language=language,
        )
        return {
            "success": True,
            "sourceId": download["sourceId"],
            "download": download,
            "videoUnderstanding": video_understanding,
            "transcript": transcript,
            "keySegments": key_segments,
            "keyframes": frames,
            "summary": summary,
            "styleStructure": structure,
        }

    def _new_source_id(self) -> str:
        return f"video_src_{uuid.uuid4().hex[:12]}"

    def _source_dir(self, source_id: str) -> Path:
        d = self.output_root / source_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _artifact_dir_for_video(self, video_path: str) -> Path:
        path = Path(video_path).resolve()
        if path.parent.name == "downloads":
            d = path.parent.parent
        else:
            d = path.parent / "video_source_artifacts"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _sample_times(self, duration: float, max_frames: int, strategy: str) -> List[float]:
        if max_frames == 1:
            return [round(max(0.0, duration / 2), 2)]

        # Avoid exact 0 and exact end, which often produce black frames.
        start = min(1.0, max(0.0, duration * 0.05))
        end = max(start, duration - min(1.0, duration * 0.05))
        step = (end - start) / (max_frames - 1)
        return [round(start + step * i, 2) for i in range(max_frames)]

    def _normalize_timestamps(
        self,
        timestamps: Optional[List[float]],
        duration: float,
        max_frames: int,
    ) -> List[float]:
        if not timestamps:
            return []

        normalized: List[float] = []
        seen = set()
        for value in timestamps:
            try:
                timestamp = float(value)
            except (TypeError, ValueError):
                continue
            timestamp = min(max(timestamp, 0.1), max(duration - 0.1, 0.1))
            rounded = round(timestamp, 2)
            bucket = round(rounded, 1)
            if bucket in seen:
                continue
            seen.add(bucket)
            normalized.append(rounded)

        normalized.sort()
        return normalized[:max_frames]

    def _timestamps_from_video_understanding(
        self,
        result: Dict[str, Any],
        max_frames: int,
        duration: Optional[float] = None,
    ) -> List[float]:
        if not result.get("success"):
            return []

        analysis = result.get("analysis") or {}
        timestamps = analysis.get("representative_timestamps") or []

        for segment in analysis.get("semantic_segments") or []:
            timestamp = segment.get("representative_timestamp")
            if timestamp is None:
                start = segment.get("timestamp_start")
                end = segment.get("timestamp_end")
                if start is not None and end is not None:
                    try:
                        timestamp = (float(start) + float(end)) / 2
                    except (TypeError, ValueError):
                        timestamp = None
            if timestamp is not None:
                timestamps.append(timestamp)

        return self._normalize_timestamps(timestamps, duration or float("inf"), max_frames)

    def _timestamps_from_key_segments(
        self,
        result: Dict[str, Any],
        max_frames: int,
        duration: Optional[float] = None,
    ) -> List[float]:
        if not result.get("success"):
            return []

        timestamps: List[float] = []
        for segment in result.get("segments") or []:
            timestamp = segment.get("representativeTimestamp")
            if timestamp is None:
                start = segment.get("start")
                end = segment.get("end")
                if start is not None and end is not None:
                    try:
                        timestamp = (float(start) + float(end)) / 2
                    except (TypeError, ValueError):
                        timestamp = None
            if timestamp is not None:
                timestamps.append(timestamp)

        return self._normalize_timestamps(timestamps, duration or float("inf"), max_frames)

    def _extract_understanding_analysis(self, video_understanding: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not video_understanding:
            return {}
        if "analysis" in video_understanding and isinstance(video_understanding.get("analysis"), dict):
            return video_understanding.get("analysis") or {}
        return video_understanding

    def _fallback_key_segments(
        self,
        analysis: Dict[str, Any],
        duration: float,
        target_count: int,
        min_duration: float,
        max_duration: float,
    ) -> List[Dict[str, Any]]:
        semantic_segments = analysis.get("semantic_segments") or []
        if not semantic_segments and duration > 0:
            sample_times = self._sample_times(duration, target_count, "uniform")
            semantic_segments = [
                {
                    "sequence": i + 1,
                    "timestamp_start": max(0.0, ts - max_duration / 2),
                    "timestamp_end": min(duration, ts + max_duration / 2),
                    "representative_timestamp": ts,
                    "title": f"片段 {i + 1}",
                    "description": "",
                    "purpose": "均匀采样片段",
                }
                for i, ts in enumerate(sample_times)
            ]

        fallback: List[Dict[str, Any]] = []
        total = len(semantic_segments)
        for index, segment in enumerate(semantic_segments[:target_count], start=1):
            try:
                raw_start = float(segment.get("timestamp_start", 0) or 0)
                raw_end = float(segment.get("timestamp_end", raw_start + max_duration) or raw_start + max_duration)
            except (TypeError, ValueError):
                continue

            raw_start = min(max(raw_start, 0.0), max(duration, 0.0))
            raw_end = min(max(raw_end, raw_start + min_duration), duration or raw_end)
            try:
                representative = float(segment.get("representative_timestamp"))
            except (TypeError, ValueError):
                representative = (raw_start + raw_end) / 2

            start, end = self._fit_segment_window(
                raw_start,
                raw_end,
                representative,
                duration,
                min_duration,
                max_duration,
            )
            representative = round(min(max(representative, start), end), 2)
            suggested_use = "reference"
            segment_type = "reference"
            priority = 3
            if index == 1:
                segment_type = "hook"
                suggested_use = "keep"
                priority = 5
            elif index == total:
                segment_type = "payoff"
                suggested_use = "rewrite"
                priority = 3
            elif "演示" in str(segment.get("purpose") or segment.get("description") or ""):
                segment_type = "demo"
                suggested_use = "reference"
                priority = 4

            fallback.append({
                "sequence": index,
                "start": start,
                "end": end,
                "duration": round(end - start, 2),
                "representativeTimestamp": representative,
                "type": segment_type,
                "title": segment.get("title") or f"片段 {index}",
                "description": segment.get("description") or segment.get("visual_description") or "",
                "reason": segment.get("purpose") or "该片段在原视频结构中有代表性，可作为二创参考。",
                "suggestedUse": suggested_use,
                "priority": priority,
                "seedanceReady": 2 <= round(end - start, 2) <= 15,
                "source": "fallback_from_video_understanding",
            })
        return fallback

    def _sanitize_key_segments(
        self,
        segments: Any,
        duration: float,
        target_count: int,
        min_duration: float,
        max_duration: float,
        fallback_segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not isinstance(segments, list):
            segments = []

        allowed_types = {"hook", "context", "demo", "turning_point", "evidence", "payoff", "reference", "skip"}
        allowed_uses = {"keep", "rewrite", "remix", "reference", "skip"}
        cleaned_segments: List[Dict[str, Any]] = []
        seen = set()

        for index, segment in enumerate(segments, start=1):
            if not isinstance(segment, dict):
                continue
            try:
                start = float(segment.get("start"))
                end = float(segment.get("end"))
            except (TypeError, ValueError):
                continue

            try:
                representative = float(segment.get("representativeTimestamp"))
            except (TypeError, ValueError):
                representative = (start + end) / 2

            start, end = self._fit_segment_window(
                start,
                end,
                representative,
                duration,
                min_duration,
                max_duration,
            )
            if end <= start:
                continue

            representative = round(min(max(representative, start), end), 2)
            bucket = (round(start, 1), round(end, 1))
            if bucket in seen:
                continue
            seen.add(bucket)

            segment_type = str(segment.get("type") or "reference").strip()
            suggested_use = str(segment.get("suggestedUse") or "reference").strip()
            if segment_type not in allowed_types:
                segment_type = "reference"
            if suggested_use not in allowed_uses:
                suggested_use = "reference"
            try:
                priority = int(segment.get("priority", 3))
            except (TypeError, ValueError):
                priority = 3

            cleaned_segments.append({
                "sequence": len(cleaned_segments) + 1,
                "start": start,
                "end": end,
                "duration": round(end - start, 2),
                "representativeTimestamp": representative,
                "type": segment_type,
                "title": str(segment.get("title") or f"片段 {index}")[:120],
                "description": str(segment.get("description") or "")[:800],
                "reason": str(segment.get("reason") or "")[:800],
                "suggestedUse": suggested_use,
                "priority": min(max(priority, 1), 5),
                "seedanceReady": 2 <= round(end - start, 2) <= 15,
                "source": segment.get("source") or "segment_selector_agent",
            })

            if len(cleaned_segments) >= target_count:
                break

        if not cleaned_segments:
            cleaned_segments = fallback_segments[:target_count]

        return cleaned_segments

    def _fit_segment_window(
        self,
        start: float,
        end: float,
        representative: float,
        duration: float,
        min_duration: float,
        max_duration: float,
    ) -> Tuple[float, float]:
        duration = max(float(duration or 0), 0.0)
        if duration > 0:
            start = min(max(start, 0.0), duration)
            end = min(max(end, start), duration)
            representative = min(max(representative, 0.0), duration)
        else:
            start = max(start, 0.0)
            end = max(end, start)

        current = end - start
        if current > max_duration:
            half = max_duration / 2
            start = representative - half
            end = representative + half
        elif current < min_duration:
            half = min_duration / 2
            center = representative if start <= representative <= end else (start + end) / 2
            start = center - half
            end = center + half

        if duration > 0:
            if start < 0:
                end = min(duration, end - start)
                start = 0.0
            if end > duration:
                start = max(0.0, start - (end - duration))
                end = duration
        else:
            start = max(start, 0.0)
            end = max(end, start + min_duration)

        if end - start > max_duration:
            end = start + max_duration
        if end - start < min_duration and duration > 0:
            end = min(duration, start + min_duration)
            start = max(0.0, end - min_duration)

        return round(start, 2), round(end, 2)

    def _sanitize_video_understanding_analysis(
        self,
        analysis: Dict[str, Any],
        duration: float,
        max_segments: int,
    ) -> Dict[str, Any]:
        if not analysis or duration <= 0:
            return analysis

        clean_segments: List[Dict[str, Any]] = []
        for segment in analysis.get("semantic_segments") or []:
            try:
                start = float(segment.get("timestamp_start", 0) or 0)
                end = float(segment.get("timestamp_end", start) or start)
            except (TypeError, ValueError):
                continue

            if start >= duration or end <= 0:
                continue

            start = round(min(max(start, 0.0), duration), 2)
            end = round(min(max(end, start), duration), 2)
            if end <= start:
                end = round(min(duration, start + 0.1), 2)

            try:
                representative = float(segment.get("representative_timestamp"))
            except (TypeError, ValueError):
                representative = (start + end) / 2
            representative = round(min(max(representative, start), end), 2)

            cleaned = dict(segment)
            cleaned["timestamp_start"] = start
            cleaned["timestamp_end"] = end
            cleaned["representative_timestamp"] = representative
            clean_segments.append(cleaned)

        clean_segments = clean_segments[:max_segments]
        timestamps = list(analysis.get("representative_timestamps") or [])
        timestamps.extend(segment.get("representative_timestamp") for segment in clean_segments)

        clean_analysis = dict(analysis)
        clean_analysis["semantic_segments"] = clean_segments
        clean_analysis["representative_timestamps"] = self._normalize_timestamps(timestamps, duration, max_segments)
        return clean_analysis

    def _prepare_video_understanding_input(self, video_path: str) -> str:
        """Create a low-bandwidth proxy video for model understanding."""
        if not settings.video_understanding_use_proxy:
            return video_path

        artifact_dir = self._artifact_dir_for_video(video_path)
        source_key = hashlib.sha1(str(Path(video_path).resolve()).encode("utf-8")).hexdigest()[:10]
        proxy_path = artifact_dir / f"understanding_proxy_{Path(video_path).stem[:40]}_{source_key}.mp4"

        source_mtime = os.path.getmtime(video_path)
        if proxy_path.exists() and proxy_path.stat().st_size > 0 and proxy_path.stat().st_mtime >= source_mtime:
            return str(proxy_path)

        try:
            self._create_video_understanding_proxy(video_path, str(proxy_path))
            if proxy_path.exists() and proxy_path.stat().st_size > 0:
                return str(proxy_path)
        except Exception as e:
            logger.warning(f"生成视频理解代理失败，回退原视频: {e}")

        return video_path

    def _create_video_understanding_proxy(self, video_path: str, output_path: str) -> None:
        max_width = max(160, int(settings.video_understanding_proxy_max_width or 640))
        fps = max(0.2, float(settings.video_understanding_proxy_fps or 1.0))
        crf = min(max(int(settings.video_understanding_proxy_crf or 32), 18), 40)
        vf = f"scale='min({max_width},iw)':-2,fps={fps}"

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", vf,
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", str(crf),
            "-movflags", "+faststart",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

    def _call_video_understanding_model(
        self,
        video_path: str,
        model_name: str,
        language: str,
        max_segments: int,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        from google import genai
        from google.genai import types

        client = self._create_google_client(genai)
        prompt = self._video_understanding_prompt(language, max_segments)
        media_resolution = self._media_resolution_value(types, for_part=True)
        video_part = self._video_part_for_model(client, types, video_path, media_resolution)
        config_kwargs: Dict[str, Any] = {
            "temperature": 0.2,
            "max_output_tokens": 3000,
            "response_mime_type": "application/json",
        }
        config_media_resolution = self._media_resolution_value(types, for_part=False)
        if config_media_resolution is not None:
            config_kwargs["media_resolution"] = config_media_resolution

        try:
            config = types.GenerateContentConfig(**config_kwargs)
        except TypeError:
            config_kwargs.pop("media_resolution", None)
            config = types.GenerateContentConfig(**config_kwargs)

        response = client.models.generate_content(
            model=model_name,
            contents=[video_part, prompt],
            config=config,
        )
        content = response.text or ""
        parsed = self._parse_json_content(content, fallback=self._fallback_video_understanding())
        usage = {}
        if getattr(response, "usage_metadata", None):
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
            }
        return parsed, usage

    def _create_google_client(self, genai_module):
        if settings.vertex_api_key:
            return genai_module.Client(vertexai=True, api_key=settings.vertex_api_key)
        if settings.vertex_project_id:
            return genai_module.Client(
                vertexai=True,
                project=settings.vertex_project_id,
                location=settings.vertex_location,
            )
        if settings.google_api_key:
            return genai_module.Client(api_key=settings.google_api_key)
        raise RuntimeError("未配置 Google / Vertex API key，无法进行视频理解")

    def _upload_video_file(self, client, video_path: str):
        try:
            return client.files.upload(path=video_path)
        except TypeError:
            return client.files.upload(file=video_path)

    def _video_part_for_model(self, client, types_module, video_path: str, media_resolution):
        """Return a video input part that works for both AI Studio and Vertex."""
        if settings.vertex_api_key or settings.vertex_project_id:
            with open(video_path, "rb") as f:
                return types_module.Part.from_bytes(
                    data=f.read(),
                    mime_type=self._mime_type_for_video(video_path),
                    media_resolution=media_resolution,
                )

        uploaded_file = self._upload_video_file(client, video_path)
        self._wait_for_google_file(uploaded_file, client)
        return uploaded_file

    def _media_resolution_value(self, types_module, for_part: bool):
        media_resolution = (settings.video_understanding_media_resolution or "").lower()
        if media_resolution not in {"low", "medium", "high"}:
            return None

        enum_name = {
            "low": "MEDIA_RESOLUTION_LOW",
            "medium": "MEDIA_RESOLUTION_MEDIUM",
            "high": "MEDIA_RESOLUTION_HIGH",
        }[media_resolution]
        enum_cls = types_module.PartMediaResolutionLevel if for_part else types_module.MediaResolution
        try:
            return getattr(enum_cls, enum_name)
        except Exception:
            logger.debug("当前 google-genai SDK 不支持 media_resolution 配置，已忽略")
            return None

    def _mime_type_for_video(self, video_path: str) -> str:
        ext = Path(video_path).suffix.lower()
        if ext == ".webm":
            return "video/webm"
        if ext == ".mov":
            return "video/quicktime"
        return "video/mp4"

    def _wait_for_google_file(self, uploaded_file, client, timeout: int = 180) -> None:
        start = time.time()
        current_file = uploaded_file
        while time.time() - start < timeout:
            state = self._google_file_state(current_file)
            if state in {"ACTIVE", "SUCCEEDED", "READY", ""}:
                return
            if state in {"FAILED", "ERROR"}:
                raise RuntimeError(f"Google 文件处理失败: {state}")
            time.sleep(2)
            if hasattr(client, "files") and hasattr(client.files, "get") and getattr(current_file, "name", None):
                current_file = client.files.get(name=current_file.name)

        raise TimeoutError("等待 Google 文件处理超时")

    def _google_file_state(self, file_obj) -> str:
        state = getattr(file_obj, "state", "")
        if state is None:
            return ""
        return getattr(state, "name", str(state)).upper()

    def _video_understanding_prompt(self, language: str, max_segments: int) -> str:
        return f"""你是视频理解与二创策划模型。请完整理解这段视频，输出 JSON，不要输出 Markdown。

语言：{language}
最多输出 {max_segments} 个语义段。

JSON 格式：
{{
  "overall_summary": "用3-5句话概括视频内容",
  "main_topic": "核心主题",
  "target_audience": "可能受众",
  "narrative_structure": "开头-发展-高潮-结尾结构",
  "hook": "开头钩子",
  "pacing": "节奏与信息密度",
  "visual_style": {{
    "color_palette": "色彩",
    "lighting": "光线",
    "camera": "镜头语言",
    "editing": "剪辑方式",
    "mood": "情绪氛围"
  }},
  "semantic_segments": [
    {{
      "sequence": 1,
      "timestamp_start": 0,
      "timestamp_end": 5,
      "representative_timestamp": 2.5,
      "title": "段落标题",
      "description": "该段发生了什么",
      "visual_description": "画面主体、场景、构图、字幕/屏幕内容",
      "audio_or_speech_summary": "这一段的语音或音频信息",
      "purpose": "该段在叙事里的作用"
    }}
  ],
  "representative_timestamps": [2.5, 8.0],
  "recreation_strategy": "二创时建议保留、改写和规避的点",
  "content_warnings": []
}}

要求：
- representative_timestamp 必须在对应段落内，适合用作关键帧截图。
- 优先选择能代表视觉主体、场景转折、论点变化、演示步骤的时间点。
- 避免选择黑场、转场、纯字幕页、模糊画面。
- 如果看不清语音内容，也要基于画面给出结构理解。
"""

    def _fallback_video_understanding(self) -> Dict[str, Any]:
        return {
            "overall_summary": "",
            "main_topic": "",
            "target_audience": "",
            "narrative_structure": "",
            "hook": "",
            "pacing": "",
            "visual_style": {
                "color_palette": "",
                "lighting": "",
                "camera": "",
                "editing": "",
                "mood": "",
            },
            "semantic_segments": [],
            "representative_timestamps": [],
            "recreation_strategy": "",
            "content_warnings": [],
        }

    def _extract_single_frame(self, video_path: str, timestamp: float, output_path: Path) -> bool:
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(timestamp),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                str(output_path),
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path.exists() and output_path.stat().st_size > 0
        except Exception as e:
            logger.warning(f"关键帧提取失败 {timestamp}s: {e}")
            return False

    async def _describe_keyframes(self, keyframes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        adapter = self.llm.adapters.get("google")
        if not adapter or not hasattr(adapter, "vision_call"):
            return [
                {
                    "index": f.get("index"),
                    "timestamp": f.get("timestamp"),
                    "description": "视觉描述不可用",
                }
                for f in keyframes
            ]

        descriptions: List[Dict[str, Any]] = []
        for frame in keyframes:
            frame_path = frame.get("framePath")
            if not frame_path or not os.path.exists(frame_path):
                continue
            try:
                with open(frame_path, "rb") as img:
                    result = await asyncio.to_thread(
                        adapter.vision_call,
                        "请用一句中文描述这张视频关键帧的主体、场景、色彩和镜头感觉。",
                        img.read(),
                        max_tokens=180,
                        temperature=0.2,
                    )
                descriptions.append({
                    "index": frame.get("index"),
                    "timestamp": frame.get("timestamp"),
                    "description": result.get("content") if result.get("success") else "",
                })
            except Exception as e:
                descriptions.append({
                    "index": frame.get("index"),
                    "timestamp": frame.get("timestamp"),
                    "description": f"视觉描述失败: {e}",
                })
        return descriptions

    async def _json_llm(self, prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await asyncio.to_thread(
                self.llm.simple_call,
                prompt,
                timeout=30,
                retry_count=1,
                max_tokens=1800,
            )
            content = result.get("content", "")
            return self._parse_json_content(content, fallback)
        except Exception as e:
            logger.warning(f"LLM JSON 解析失败，使用 fallback: {e}")
        return fallback

    def _parse_json_content(self, content: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        try:
            json_match = re.search(r"```json\s*(.*?)\s*```", content or "", re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            json_match = re.search(r"\{[\s\S]*\}", content or "")
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(content)
        except Exception:
            return fallback

    def _fallback_summary(self, video_info: Dict[str, Any], transcript: Optional[str]) -> str:
        if transcript:
            compact = re.sub(r"\s+", " ", transcript).strip()
            return compact[:360] + ("..." if len(compact) > 360 else "")
        duration = video_info.get("duration")
        resolution = video_info.get("resolution")
        return f"本地视频，时长 {duration}s，分辨率 {resolution}。暂无转写文本。"

    def _public_path(self, path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        try:
            output_root = Path(settings.output_dir).resolve()
            target = Path(path).resolve()
            rel = target.relative_to(output_root)
            return f"/outputs/{rel.as_posix()}"
        except Exception:
            return None

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
