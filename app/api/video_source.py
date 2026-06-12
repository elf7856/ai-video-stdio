"""
Standalone video source APIs.

These endpoints are for validating and retrying the source-video pipeline step
by step. The main generation orchestrator also uses the same service in its
background source-material preparation step.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ingest import VideoSourceService

router = APIRouter(prefix="/api/video-source", tags=["video-source"])


class DownloadRequest(BaseModel):
    url: str = Field(..., description="视频 URL")
    sourceId: Optional[str] = Field(default=None, description="可选来源 ID")


class VideoPathRequest(BaseModel):
    videoPath: str = Field(..., description="本地视频路径")


class TranscribeRequest(VideoPathRequest):
    language: str = Field(default="zh-CN", description="语言代码")
    provider: Optional[str] = Field(default=None, description="ASR provider")


class KeyframesRequest(VideoPathRequest):
    maxFrames: int = Field(default=12, ge=1, le=30, description="最多关键帧数量")
    strategy: str = Field(default="uniform", description="抽帧策略")


class VideoUnderstandingRequest(VideoPathRequest):
    language: str = Field(default="zh-CN", description="语言代码")
    maxSegments: int = Field(default=12, ge=1, le=30, description="最多语义段数量")


class KeySegmentsRequest(VideoPathRequest):
    videoUnderstanding: Optional[Dict[str, Any]] = Field(default=None, description="可选已有模型视频理解结果")
    transcript: Optional[str] = Field(default=None, description="可选已有转写文本")
    language: str = Field(default="zh-CN", description="语言代码")
    targetCount: int = Field(default=8, ge=1, le=20, description="推荐片段数量")
    minDuration: float = Field(default=2.0, ge=0.5, le=15.0, description="单段最短时长")
    maxDuration: float = Field(default=15.0, ge=2.0, le=30.0, description="单段最长时长")


class SummaryRequest(VideoPathRequest):
    transcript: Optional[str] = Field(default=None, description="可选已有转写文本")
    language: str = Field(default="zh-CN", description="语言代码")


class StyleStructureRequest(VideoPathRequest):
    transcript: Optional[str] = Field(default=None, description="可选已有转写文本")
    keyframes: Optional[List[Dict[str, Any]]] = Field(default=None, description="可选已有关键帧列表")
    language: str = Field(default="zh-CN", description="语言代码")


class AnalyzeUrlRequest(BaseModel):
    url: str = Field(..., description="视频 URL")
    language: str = Field(default="zh-CN", description="语言代码")
    maxFrames: int = Field(default=12, ge=1, le=30, description="最多关键帧数量")


def _service() -> VideoSourceService:
    return VideoSourceService()


def _raise_if_failed(result: Dict[str, Any]) -> Dict[str, Any]:
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "处理失败"))
    return result


@router.post("/download")
async def download_video_source(request: DownloadRequest):
    """Step 1: download video URL and return a local path."""
    result = await _service().download_from_url(request.url, source_id=request.sourceId)
    return _raise_if_failed(result)


@router.post("/info")
async def get_video_source_info(request: VideoPathRequest):
    """Read local video metadata with ffprobe."""
    result = _service().get_video_info(request.videoPath)
    return _raise_if_failed(result)


@router.post("/transcribe")
async def transcribe_video_source(request: TranscribeRequest):
    """Step 2: transcribe a downloaded/local video."""
    result = await _service().transcribe_video(
        request.videoPath,
        language=request.language,
        provider=request.provider,
    )
    return _raise_if_failed(result)


@router.post("/keyframes")
async def extract_video_source_keyframes(request: KeyframesRequest):
    """Step 3: extract standalone keyframes from a downloaded/local video."""
    result = _service().extract_keyframes(
        request.videoPath,
        max_frames=request.maxFrames,
        strategy=request.strategy,
    )
    return _raise_if_failed(result)


@router.post("/understand")
async def understand_video_source(request: VideoUnderstandingRequest):
    """Use the configured multimodal model to understand video structure."""
    result = await _service().understand_video_with_model(
        request.videoPath,
        language=request.language,
        max_segments=request.maxSegments,
    )
    return _raise_if_failed(result)


@router.post("/segments")
async def select_video_source_key_segments(request: KeySegmentsRequest):
    """Select reusable source-video segments for review and recreation."""
    result = await _service().select_key_segments(
        request.videoPath,
        video_understanding=request.videoUnderstanding,
        transcript=request.transcript,
        language=request.language,
        target_count=request.targetCount,
        min_duration=request.minDuration,
        max_duration=request.maxDuration,
    )
    return _raise_if_failed(result)


@router.post("/summary")
async def summarize_video_source(request: SummaryRequest):
    """Step 4: generate a text summary from metadata and transcript."""
    result = await _service().summarize_video(
        request.videoPath,
        transcript=request.transcript,
        language=request.language,
    )
    return _raise_if_failed(result)


@router.post("/style-structure")
async def analyze_video_source_style_structure(request: StyleStructureRequest):
    """Step 5: analyze narrative structure and reusable visual style."""
    result = await _service().analyze_style_structure(
        request.videoPath,
        transcript=request.transcript,
        keyframes=request.keyframes,
        language=request.language,
    )
    return _raise_if_failed(result)


@router.post("/analyze-url")
async def analyze_video_source_from_url(request: AnalyzeUrlRequest):
    """
    Convenience endpoint for full manual testing.

    The individual endpoints above are the canonical building blocks.
    """
    result = await _service().analyze_all_from_url(
        request.url,
        language=request.language,
        max_frames=request.maxFrames,
    )
    return _raise_if_failed(result)
