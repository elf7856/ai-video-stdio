"""
视频编辑器API - 提供视频编辑、渲染、字幕等功能
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
import logging
import uuid

from app.models.editor import EditorProject, ProjectStatus, Timeline, SubtitleFile
from app.services.editor import TimelineRenderer, SubtitleService
from app.core.config import settings
from app.utils.database import get_db
from app.crud.editor import EditorProjectCRUD, SubtitleCRUD

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/editor", tags=["视频编辑器"])

# 服务实例
timeline_renderer = TimelineRenderer()
subtitle_service = SubtitleService()


class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str
    description: Optional[str] = None
    timeline: Optional[Timeline] = None


class RenderRequest(BaseModel):
    """渲染请求"""
    project_id: str
    quality: str = "high"  # low/medium/high


class SubtitleGenerateRequest(BaseModel):
    """字幕生成请求"""
    project_id: str
    video_path: str
    language: str = "zh"


@router.post("/projects", response_model=EditorProject)
async def create_project(request: ProjectCreateRequest, db: Session = Depends(get_db)):
    """
    创建新的编辑项目

    创建一个新项目，可以包含初始的时间轴数据
    """
    try:
        project_id = f"editor_project_{uuid.uuid4().hex[:12]}"

        project = EditorProject(
            id=project_id,
            name=request.name,
            description=request.description,
            timeline=request.timeline,
            status=ProjectStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 保存到数据库
        EditorProjectCRUD.create(db, project)

        logger.info(f"创建编辑项目: {project_id} - {request.name}")
        return project

    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}", response_model=EditorProject)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """
    获取项目详情

    返回指定ID的项目信息，包括时间轴和渲染状态
    """
    project = EditorProjectCRUD.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    return project


@router.put("/projects/{project_id}", response_model=EditorProject)
async def update_project(project_id: str, timeline: Timeline, db: Session = Depends(get_db)):
    """
    更新项目时间轴

    更新项目的时间轴配置
    """
    project = EditorProjectCRUD.update(db, project_id, {"timeline": timeline})
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    logger.info(f"更新项目时间轴: {project_id}")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """
    删除项目

    删除指定ID的项目
    """
    success = EditorProjectCRUD.delete(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")

    logger.info(f"删除项目: {project_id}")
    return {"message": "项目已删除", "project_id": project_id}


@router.get("/projects")
async def list_projects(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取项目列表

    返回所有项目，可按状态过滤
    """
    projects = EditorProjectCRUD.list(db, status=status, limit=limit, offset=offset)
    return projects


@router.post("/render")
async def render_timeline(
    render_request: RenderRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    渲染视频（后台任务）

    将项目的时间轴渲染为视频文件，返回任务ID用于查询进度
    """
    project_id = render_request.project_id

    project = EditorProjectCRUD.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not project.timeline:
        raise HTTPException(status_code=400, detail="项目没有时间轴数据")

    if project.status == ProjectStatus.RENDERING:
        raise HTTPException(status_code=400, detail="项目正在渲染中")

    # 设置状态为渲染中
    EditorProjectCRUD.update(db, project_id, {
        "status": ProjectStatus.RENDERING,
        "render_progress": 0.0
    })

    # 生成输出路径
    output_dir = Path(settings.output_dir) / "editor"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_id}_{int(datetime.now().timestamp())}.mp4"

    # 在后台执行渲染
    background_tasks.add_task(
        render_video_task,
        project_id,
        project.timeline,
        output_path,
        render_request.quality
    )

    logger.info(f"开始渲染项目: {project_id}")

    return {
        "message": "渲染任务已启动",
        "project_id": project_id,
        "output_path": str(output_path)
    }


async def render_video_task(
    project_id: str,
    timeline: Timeline,
    output_path: Path,
    quality: str
):
    """
    后台渲染任务

    在后台线程中执行实际的视频渲染
    """
    from app.utils.database import SessionLocal
    db = SessionLocal()

    try:
        project = EditorProjectCRUD.get(db, project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return

        logger.info(f"[{project_id}] 开始渲染...")

        # 执行渲染
        await timeline_renderer.render(
            timeline=timeline,
            output_path=output_path,
            quality=quality
        )

        # 更新项目状态
        EditorProjectCRUD.update(db, project_id, {
            "status": ProjectStatus.COMPLETED,
            "render_progress": 100.0,
            "output_path": str(output_path)
        })

        logger.info(f"[{project_id}] ✅ 渲染完成: {output_path}")

    except Exception as e:
        logger.error(f"[{project_id}] 渲染失败: {e}", exc_info=True)

        # 更新失败状态
        EditorProjectCRUD.update(db, project_id, {
            "status": ProjectStatus.FAILED,
            "render_error": str(e)
        })
    finally:
        db.close()


@router.post("/subtitle/generate", response_model=SubtitleFile)
async def generate_subtitle(request: SubtitleGenerateRequest):
    """
    自动生成字幕

    使用Whisper ASR从视频中自动生成字幕
    """
    try:
        video_path = Path(request.video_path)

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="视频文件不存在")

        logger.info(f"生成字幕: {video_path}")

        # 生成字幕
        subtitle_file = await subtitle_service.generate_auto_subtitles(
            video_path=video_path,
            language=request.language,
            project_id=request.project_id
        )

        return subtitle_file

    except Exception as e:
        logger.error(f"字幕生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subtitle/import")
async def import_subtitle(
    project_id: str,
    file: UploadFile = File(...)
):
    """
    导入SRT字幕文件

    上传并导入SRT格式的字幕文件
    """
    try:
        if not file.filename.endswith('.srt'):
            raise HTTPException(status_code=400, detail="只支持SRT格式")

        # 保存上传的文件
        temp_dir = Path(settings.upload_dir) / "subtitles"
        temp_dir.mkdir(parents=True, exist_ok=True)
        srt_path = temp_dir / f"{project_id}_{file.filename}"

        with open(srt_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 导入字幕
        subtitle_file = await subtitle_service.import_srt(
            srt_path=srt_path,
            project_id=project_id
        )

        logger.info(f"导入字幕文件: {srt_path}")

        return subtitle_file

    except Exception as e:
        logger.error(f"字幕导入失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subtitle/{subtitle_id}/export")
async def export_subtitle(subtitle_id: str):
    """
    导出字幕为SRT文件

    将字幕导出为SRT格式文件
    """
    # 这里需要从存储中获取字幕文件
    # 简化实现：直接返回下载链接
    return {
        "message": "字幕导出功能需要实现字幕存储",
        "subtitle_id": subtitle_id
    }


@router.post("/preview")
async def render_preview(project_id: str, max_duration: float = 10.0):
    """
    渲染预览视频

    快速渲染前几秒的预览，用于实时查看效果
    """
    if project_id not in projects_storage:
        raise HTTPException(status_code=404, detail="项目不存在")

    project = projects_storage[project_id]

    if not project.timeline:
        raise HTTPException(status_code=400, detail="项目没有时间轴数据")

    try:
        # 生成预览路径
        preview_dir = Path(settings.output_dir) / "editor" / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_path = preview_dir / f"{project_id}_preview.mp4"

        # 渲染预览
        await timeline_renderer.render_preview(
            timeline=project.timeline,
            output_path=preview_path,
            max_duration=max_duration
        )

        return {
            "success": True,
            "preview_path": str(preview_path),
            "duration": max_duration
        }

    except Exception as e:
        logger.error(f"预览渲染失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
