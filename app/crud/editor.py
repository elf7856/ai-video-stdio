"""
视频编辑器CRUD操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from app.models.editor.database import EditorProjectDB, SubtitleFileDB, ProjectStatusEnum
from app.models.editor import EditorProject, ProjectStatus, Timeline, SubtitleFile, SubtitleSegment


class EditorProjectCRUD:
    """编辑项目CRUD操作"""

    @staticmethod
    def create(db: Session, project: EditorProject) -> EditorProjectDB:
        """创建项目"""
        db_project = EditorProjectDB(
            id=project.id,
            name=project.name,
            description=project.description,
            timeline_json=project.timeline.dict() if project.timeline else None,
            status=ProjectStatusEnum(project.status),
            output_path=project.output_path,
            output_format=project.output_format,
            output_quality=project.output_quality,
            render_progress=project.render_progress,
            render_error=project.render_error,
            created_by=project.created_by
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get(db: Session, project_id: str) -> Optional[EditorProject]:
        """获取项目"""
        db_project = db.query(EditorProjectDB).filter(EditorProjectDB.id == project_id).first()
        if not db_project:
            return None
        return EditorProjectCRUD._to_pydantic(db_project)

    @staticmethod
    def list(
        db: Session,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[EditorProject]:
        """获取项目列表"""
        query = db.query(EditorProjectDB)

        if user_id:
            query = query.filter(EditorProjectDB.created_by == user_id)

        if status:
            query = query.filter(EditorProjectDB.status == status)

        query = query.order_by(EditorProjectDB.updated_at.desc())
        query = query.offset(offset).limit(limit)

        db_projects = query.all()
        return [EditorProjectCRUD._to_pydantic(p) for p in db_projects]

    @staticmethod
    def update(db: Session, project_id: str, updates: Dict[str, Any]) -> Optional[EditorProject]:
        """更新项目"""
        db_project = db.query(EditorProjectDB).filter(EditorProjectDB.id == project_id).first()
        if not db_project:
            return None

        for key, value in updates.items():
            if key == "timeline" and value:
                setattr(db_project, "timeline_json", value.dict())
            elif key == "status":
                setattr(db_project, "status", ProjectStatusEnum(value))
            elif hasattr(db_project, key):
                setattr(db_project, key, value)

        db_project.updated_at = datetime.now()
        db.commit()
        db.refresh(db_project)
        return EditorProjectCRUD._to_pydantic(db_project)

    @staticmethod
    def delete(db: Session, project_id: str) -> bool:
        """删除项目"""
        db_project = db.query(EditorProjectDB).filter(EditorProjectDB.id == project_id).first()
        if not db_project:
            return False

        db.delete(db_project)
        db.commit()
        return True

    @staticmethod
    def _to_pydantic(db_project: EditorProjectDB) -> EditorProject:
        """转换为Pydantic模型"""
        timeline = None
        if db_project.timeline_json:
            timeline = Timeline(**db_project.timeline_json)

        return EditorProject(
            id=db_project.id,
            name=db_project.name,
            description=db_project.description,
            timeline=timeline,
            status=ProjectStatus(db_project.status.value),
            output_path=db_project.output_path,
            output_format=db_project.output_format,
            output_quality=db_project.output_quality,
            render_progress=db_project.render_progress,
            render_error=db_project.render_error,
            created_by=db_project.created_by,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at
        )


class SubtitleCRUD:
    """字幕CRUD操作"""

    @staticmethod
    def create(db: Session, subtitle: SubtitleFile) -> SubtitleFileDB:
        """创建字幕"""
        db_subtitle = SubtitleFileDB(
            id=subtitle.id,
            project_id=subtitle.project_id,
            language=subtitle.language,
            segments_json=[seg.dict() for seg in subtitle.segments],
            default_font_size=subtitle.default_font_size,
            default_color=subtitle.default_color,
            default_font_family=subtitle.default_font_family,
            default_position=subtitle.default_position
        )
        db.add(db_subtitle)
        db.commit()
        db.refresh(db_subtitle)
        return db_subtitle

    @staticmethod
    def get(db: Session, subtitle_id: str) -> Optional[SubtitleFile]:
        """获取字幕"""
        db_subtitle = db.query(SubtitleFileDB).filter(SubtitleFileDB.id == subtitle_id).first()
        if not db_subtitle:
            return None
        return SubtitleCRUD._to_pydantic(db_subtitle)

    @staticmethod
    def get_by_project(db: Session, project_id: str) -> List[SubtitleFile]:
        """获取项目的所有字幕"""
        db_subtitles = db.query(SubtitleFileDB).filter(
            SubtitleFileDB.project_id == project_id
        ).all()
        return [SubtitleCRUD._to_pydantic(s) for s in db_subtitles]

    @staticmethod
    def delete(db: Session, subtitle_id: str) -> bool:
        """删除字幕"""
        db_subtitle = db.query(SubtitleFileDB).filter(SubtitleFileDB.id == subtitle_id).first()
        if not db_subtitle:
            return False

        db.delete(db_subtitle)
        db.commit()
        return True

    @staticmethod
    def _to_pydantic(db_subtitle: SubtitleFileDB) -> SubtitleFile:
        """转换为Pydantic模型"""
        segments = [SubtitleSegment(**seg) for seg in db_subtitle.segments_json]

        return SubtitleFile(
            id=db_subtitle.id,
            project_id=db_subtitle.project_id,
            language=db_subtitle.language,
            segments=segments,
            default_font_size=db_subtitle.default_font_size,
            default_color=db_subtitle.default_color,
            default_font_family=db_subtitle.default_font_family,
            default_position=db_subtitle.default_position,
            created_at=db_subtitle.created_at,
            updated_at=db_subtitle.updated_at
        )
