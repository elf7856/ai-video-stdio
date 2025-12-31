"""
多平台上传API路由
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
import logging
import os

from app.services.upload.base import Platform, PlatformConfig, VideoMetadata
from app.services.upload.manager import upload_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["Upload"])

# ==================== Request/Response Models ====================

class PlatformConfigRequest(BaseModel):
    """平台配置请求"""
    platform: Platform
    enabled: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    cookies: Optional[dict] = None
    session_data: Optional[dict] = None

class VideoUploadRequest(BaseModel):
    """视频上传请求"""
    video_path: str  # 已生成的视频路径
    title: str
    description: str
    tags: List[str] = []
    category: Optional[str] = None
    thumbnail_path: Optional[str] = None
    cover_image: Optional[str] = None
    privacy: str = "public"
    platforms: List[Platform]  # 要上传到的平台列表

    # 平台特定选项
    topic: Optional[str] = None
    allow_comment: bool = True
    allow_download: bool = True
    allow_duet: bool = True

class UploadTaskResponse(BaseModel):
    """上传任务响应"""
    task_id: str
    status: str
    platforms: List[str]
    results: List[dict]
    created_at: str
    completed_at: Optional[str] = None

# ==================== API Endpoints ====================

@router.post("/configure-platform")
async def configure_platform(config_request: PlatformConfigRequest):
    """
    配置平台认证信息
    """
    try:
        config = PlatformConfig(
            platform=config_request.platform,
            enabled=config_request.enabled,
            api_key=config_request.api_key,
            api_secret=config_request.api_secret,
            access_token=config_request.access_token,
            refresh_token=config_request.refresh_token,
            client_id=config_request.client_id,
            client_secret=config_request.client_secret,
            cookies=config_request.cookies,
            session_data=config_request.session_data
        )

        upload_manager.configure_platform(config)

        return {
            "success": True,
            "message": f"Platform {config_request.platform.value} configured successfully"
        }

    except Exception as e:
        logger.error(f"Failed to configure platform: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configured-platforms")
async def get_configured_platforms():
    """
    获取已配置的平台列表
    """
    try:
        platforms = upload_manager.get_configured_platforms()
        return {
            "platforms": [p.value for p in platforms],
            "count": len(platforms)
        }
    except Exception as e:
        logger.error(f"Failed to get configured platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_video(request: VideoUploadRequest, background_tasks: BackgroundTasks):
    """
    上传视频到多个平台
    """
    try:
        # 验证视频文件存在
        if not os.path.exists(request.video_path):
            raise HTTPException(status_code=404, detail=f"Video file not found: {request.video_path}")

        # 验证至少选择了一个平台
        if not request.platforms:
            raise HTTPException(status_code=400, detail="No platforms selected")

        # 构建元数据
        metadata = VideoMetadata(
            title=request.title,
            description=request.description,
            tags=request.tags,
            category=request.category,
            thumbnail_path=request.thumbnail_path,
            cover_image=request.cover_image,
            privacy=request.privacy,
            topic=request.topic,
            allow_comment=request.allow_comment,
            allow_download=request.allow_download,
            allow_duet=request.allow_duet
        )

        # 创建上传任务
        task = await upload_manager.upload_to_platforms(
            video_path=request.video_path,
            metadata=metadata,
            platforms=request.platforms
        )

        return {
            "success": True,
            "task_id": task.task_id,
            "message": f"Upload started for {len(request.platforms)} platforms"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}")
async def get_upload_task(task_id: str):
    """
    获取上传任务状态
    """
    try:
        task = upload_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        return {
            "task_id": task.task_id,
            "status": task.status,
            "platforms": [p.value for p in task.platforms],
            "results": [
                {
                    "platform": r.platform.value,
                    "status": r.status.value,
                    "video_id": r.video_id,
                    "video_url": r.video_url,
                    "error": r.error,
                    "uploaded_at": r.uploaded_at
                }
                for r in task.results
            ],
            "created_at": task.created_at,
            "completed_at": task.completed_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks")
async def get_all_tasks():
    """
    获取所有上传任务
    """
    try:
        tasks = upload_manager.get_all_tasks()
        return {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "platforms": [p.value for p in task.platforms],
                    "results_count": len(task.results),
                    "created_at": task.created_at,
                    "completed_at": task.completed_at
                }
                for task in tasks
            ],
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task/{task_id}/retry")
async def retry_failed_uploads(task_id: str):
    """
    重试失败的上传
    """
    try:
        task = await upload_manager.retry_failed_uploads(task_id)
        return {
            "success": True,
            "task_id": task.task_id,
            "status": task.status,
            "message": "Retry completed"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Retry failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/video")
async def delete_video(video_id: str, platforms: List[Platform]):
    """
    从多个平台删除视频
    """
    try:
        results = await upload_manager.delete_video_from_platforms(video_id, platforms)
        return {
            "success": all(results.values()),
            "results": {
                platform.value: success
                for platform, success in results.items()
            }
        }
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_upload_stats():
    """
    获取上传统计信息
    """
    try:
        stats = upload_manager.get_platform_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== OAuth相关 ====================

@router.get("/oauth/youtube/authorize-url")
async def get_youtube_oauth_url(redirect_uri: str):
    """
    获取YouTube OAuth授权URL
    """
    try:
        from google_auth_oauthlib.flow import Flow

        # 需要客户端配置文件
        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/youtube.upload']
        )
        flow.redirect_uri = redirect_uri

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        return {
            "authorization_url": authorization_url,
            "state": state
        }

    except Exception as e:
        logger.error(f"Failed to get OAuth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/oauth/youtube/callback")
async def youtube_oauth_callback(code: str, redirect_uri: str):
    """
    处理YouTube OAuth回调
    """
    try:
        from google_auth_oauthlib.flow import Flow

        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/youtube.upload']
        )
        flow.redirect_uri = redirect_uri

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # 自动配置YouTube平台
        config = PlatformConfig(
            platform=Platform.YOUTUBE,
            enabled=True,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret
        )

        upload_manager.configure_platform(config)

        return {
            "success": True,
            "message": "YouTube authorized successfully",
            "access_token": credentials.token
        }

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
