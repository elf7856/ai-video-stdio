"""
音频服务 API
提供 TTS（文字转语音）和 ASR（语音识别）功能
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid

from app.core.config import settings
from app.services.audio.tts_service import TTSService
from app.services.audio.asr_service import ASRService

router = APIRouter(prefix="/api/audio", tags=["音频服务"])

# Pydantic 模型
class TTSRequest(BaseModel):
    text: str
    voice: str = "chinese_female"
    language: str = "zh-CN"
    speed: float = 1.0

class TTSResponse(BaseModel):
    success: bool
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None

class ASRResponse(BaseModel):
    success: bool
    transcript: str
    segments: list
    language: str
    confidence: float


@router.post("/tts/generate")
async def generate_speech(request: TTSRequest):
    """
    文字转语音 (TTS)

    支持的语音类型：
    - chinese_female, chinese_male
    - english_female, english_male
    - japanese_female, korean_female
    """
    try:
        tts = TTSService()
        result = await tts.generate_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "TTS 生成失败")
            )

        return FileResponse(
            path=result["output_path"],
            media_type='audio/mpeg',
            filename=f"tts_{uuid.uuid4().hex[:8]}.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 生成失败: {str(e)}")


@router.post("/asr/transcribe", response_model=ASRResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "zh-CN",
    return_timestamps: bool = True
):
    """
    语音识别 (ASR) - 音频转文字

    支持格式: mp3, wav, m4a, ogg
    支持语言: zh-CN, en-US, ja-JP, ko-KR
    """
    try:
        # 保存上传的音频文件
        audio_id = str(uuid.uuid4())
        file_path = os.path.join(settings.upload_dir, f"{audio_id}_{file.filename}")

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 执行 ASR
        asr_service = ASRService()
        asr_result = await asr_service.transcribe_audio(
            file_path,
            language=language,
            return_timestamps=return_timestamps
        )

        # 转换结果
        if hasattr(asr_result, "to_dict"):
            asr_dict = asr_result.to_dict()
        else:
            asr_dict = asr_result if isinstance(asr_result, dict) else {}

        return ASRResponse(
            success=True,
            transcript=asr_dict.get("text", ""),
            segments=asr_dict.get("timestamps", []),
            language=asr_dict.get("language", language),
            confidence=asr_dict.get("confidence", 0.0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR 转录失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@router.get("/tts/voices")
async def get_available_voices():
    """
    获取可用的 TTS 语音列表
    """
    tts = TTSService()
    return {
        "voices": {
            "chinese": ["chinese_female", "chinese_male"],
            "english": ["english_female", "english_male"],
            "japanese": ["japanese_female"],
            "korean": ["korean_female"]
        },
        "default": "chinese_female"
    }


@router.get("/asr/languages")
async def get_supported_languages():
    """
    获取 ASR 支持的语言列表
    """
    return {
        "languages": [
            {"code": "zh-CN", "name": "中文"},
            {"code": "en-US", "name": "English"},
            {"code": "ja-JP", "name": "日本語"},
            {"code": "ko-KR", "name": "한국어"}
        ],
        "default": "zh-CN"
    }
