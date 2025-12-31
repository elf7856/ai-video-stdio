"""
项目管理API接口
提供RESTful API用于项目创建、管理和监控
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json

from app.models.video import Project as DBProject
from app.models.project import Project as PydanticProject, ProjectStatus, ProjectCreateRequest, ProjectSummary
from app.utils.database import get_db
# 暂时保留 NewAIDirector 的导入，但如果不存在则忽略（为了兼容性，实际上我们会直接操作DB）
# from ..services.director.new_ai_director import NewAIDirector 

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/projects", tags=["项目管理"])

@router.post("/", response_model=Dict[str, Any])
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    创建新的视频项目
    """
    try:
        logger.info(f"收到项目创建请求: {request.title}")
        
        # 将请求数据转换为数据库模型
        # 我们将 Pydantic 模型的额外字段存入 settings JSON 字段
        settings_dict = {
            "target_duration": request.target_duration,
            "enable_narration": request.enable_narration,
            "narration_voice": request.narration_voice,
            "narration_speed": request.narration_speed,
            "style_preferences": request.style_preferences,
            "quality_requirements": request.quality_requirements
        }

        db_project = DBProject(
            name=request.title,
            description=request.script, # 使用 description 存储 script
            settings=settings_dict,
            status="created", # 初始状态
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        # 构造返回给前端的响应
        return {
            "message": "项目创建成功",
            "id": str(db_project.id), # 转为字符串
            "title": db_project.name,
            "target_duration": request.target_duration,
            "status": "created",
            "note": "请使用项目ID查询进度"
        }
        
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("/", response_model=List[ProjectSummary])
async def list_projects(
    status: Optional[str] = None, # 注意这里类型改为 str 以匹配 DB
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取项目列表
    """
    try:
        query = db.query(DBProject)
        
        if status:
            query = query.filter(DBProject.status == status)
            
        # 按时间倒序
        query = query.order_by(DBProject.created_at.desc())
        
        total = query.count()
        projects = query.offset(offset).limit(limit).all()
        
        # 转换为 PydanticSummary
        summary_list = []
        for p in projects:
            # 安全获取 settings 中的 target_duration
            settings = p.settings or {}
            target_duration = settings.get("target_duration", 60)
            
            # 构造 Pydantic 模型
            summary = ProjectSummary(
                id=str(p.id),
                title=p.name or "Untitled",
                status=p.status or "created",
                target_duration=target_duration,
                total_shots=settings.get("total_shots", 0),
                progress_percentage=settings.get("progress", 0.0),
                created_at=p.created_at,
                updated_at=p.updated_at,
                final_video_path=None, # TODO: 从 Video 关联获取
                thumbnail_path=None
            )
            summary_list.append(summary)

        # 添加分页信息到响应头
        headers = {
            "X-Total-Count": str(total),
            "X-Limit": str(limit),
            "X-Offset": str(offset)
        }
        
        return JSONResponse(
            content=[project.dict() for project in summary_list],
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    获取项目详细信息
    """
    try:
        # 尝试将 ID 转为 int
        try:
            db_id = int(project_id)
        except ValueError:
            # 如果不是数字，可能是旧的 UUID，或者无效 ID
            raise HTTPException(status_code=404, detail="项目不存在 (Invalid ID format)")

        project = db.query(DBProject).filter(DBProject.id == db_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        settings = project.settings or {}
        
        # 构建详细响应 (尽可能匹配 PydanticProject 的结构)
        project_detail = {
            "id": str(project.id),
            "title": project.name,
            "script": project.description,
            "target_duration": settings.get("target_duration", 60),
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "progress_percentage": settings.get("progress", 0.0),
            "statistics": {
                "total_shots": settings.get("total_shots", 0),
                "completed_shots": settings.get("completed_shots", 0),
                "failed_shots": settings.get("failed_shots", 0),
                "total_cost": settings.get("total_cost", 0.0),
                "generation_time": settings.get("generation_time", 0.0)
            },
            "output_info": {
                "output_dir": settings.get("output_dir", ""),
                "final_video_path": settings.get("final_video_path", None),
                "thumbnail_path": settings.get("thumbnail_path", None)
            },
            "preferences": {
                "style_preferences": settings.get("style_preferences", {}),
                "quality_requirements": settings.get("quality_requirements", {})
            }
        }
        
        return project_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    删除项目
    """
    try:
        try:
            db_id = int(project_id)
        except ValueError:
             raise HTTPException(status_code=404, detail="项目不存在")

        project = db.query(DBProject).filter(DBProject.id == db_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        db.delete(project)
        db.commit()
        
        return {
            "message": "项目删除成功",
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")