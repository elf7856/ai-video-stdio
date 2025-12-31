"""
项目管理器
负责项目生命周期管理、文件组织和进度追踪
"""
import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.models.project import Project, ProjectStatus, ProjectSummary, ProjectCreateRequest
from app.models.shot import Shot, ShotPlan, ShotStatus
from app.models.timing import TimingPlan

logger = logging.getLogger(__name__)


class ProjectManager:
    """项目管理器"""

    def __init__(self, base_output_dir: str = "./outputs"):
        self.base_output_dir = Path(base_output_dir)
        self.projects_dir = self.base_output_dir / "projects"
        self.temp_dir = self.base_output_dir / "temp"

        # 确保基础目录存在
        self._ensure_directories()

        # 内存中的项目缓存
        self._project_cache: Dict[str, Project] = {}

        logger.info(f"ProjectManager初始化完成，输出目录: {self.base_output_dir}")

    def _ensure_directories(self):
        """确保必要的目录结构存在"""
        directories = [
            self.base_output_dir,
            self.projects_dir,
            self.temp_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"确保目录存在: {directory}")

    def create_project(self, request: ProjectCreateRequest) -> Project:
        """创建新项目"""
        logger.info(f"创建新项目: {request.title}")

        # 创建项目实例
        project = Project(
            title=request.title,
            script=request.script,
            target_duration=request.target_duration,
            enable_narration=request.enable_narration,
            narration_voice=request.narration_voice or "default",
            narration_speed=request.narration_speed,
            style_preferences=request.style_preferences or {},
            quality_requirements=request.quality_requirements or {}
        )

        # 建立项目目录结构
        project_dir = self._setup_project_directories(project.id)
        project.output_dir = str(project_dir)

        # 保存项目元数据
        self._save_project_metadata(project)

        # 创建初始日志
        self._create_initial_logs(project)

        # 缓存项目
        self._project_cache[project.id] = project

        logger.info(f"项目创建成功: {project.id} -> {project_dir}")
        return project

    def _setup_project_directories(self, project_id: str) -> Path:
        """建立项目目录结构"""
        project_dir = self.projects_dir / project_id

        # 创建标准化的项目目录结构
        subdirs = [
            "raw_clips",      # 原始AI生成片段
            "thumbnails",     # 缩略图
            "metadata",       # 项目元数据
            "logs"           # 详细日志
        ]

        for subdir in subdirs:
            (project_dir / subdir).mkdir(parents=True, exist_ok=True)

        logger.debug(f"项目目录结构创建完成: {project_dir}")
        return project_dir

    def _save_project_metadata(self, project: Project):
        """保存项目元数据"""
        if not project.output_dir:
            return

        metadata_dir = Path(project.output_dir) / "metadata"
        project_info_file = metadata_dir / "project_info.json"

        try:
            with open(project_info_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_metadata_dict(), f, ensure_ascii=False, indent=2)

            logger.debug(f"项目元数据已保存: {project_info_file}")
        except Exception as e:
            logger.error(f"保存项目元数据失败: {e}")

    def _create_initial_logs(self, project: Project):
        """创建初始日志文件"""
        if not project.output_dir:
            return

        logs_dir = Path(project.output_dir) / "logs"

        # 创建项目时间线日志
        timeline_log = logs_dir / "project_timeline.log"
        with open(timeline_log, 'w', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] 项目创建: {project.title}\n")
            f.write(f"[{datetime.now().isoformat()}] 目标时长: {project.target_duration}秒\n")
            f.write(f"[{datetime.now().isoformat()}] 项目状态: {project.status.value}\n")

    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        # 首先检查缓存
        if project_id in self._project_cache:
            return self._project_cache[project_id]

        # 从文件系统加载
        project = self._load_project_from_disk(project_id)
        if project:
            self._project_cache[project_id] = project

        return project

    def _load_project_from_disk(self, project_id: str) -> Optional[Project]:
        """从磁盘加载项目"""
        project_dir = self.projects_dir / project_id
        if not project_dir.exists():
            return None

        metadata_file = project_dir / "metadata" / "project_info.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 重建项目对象
            project = Project(
                id=data["id"],
                title=data["title"],
                script=data["script"],
                target_duration=data["target_duration"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                status=ProjectStatus(data["status"]),
                output_dir=str(project_dir),
                enable_narration=data.get("enable_narration", False),
                narration_voice=data.get("narration_voice", "default"),
                narration_speed=data.get("narration_speed", 1.0),
                narration_audio_path=data.get("narration_audio_path"),
                style_preferences=data.get("style_preferences", {}),
                quality_requirements=data.get("quality_requirements", {}),
                total_shots=data.get("total_shots", 0),
                completed_shots=data.get("completed_shots", 0),
                failed_shots=data.get("failed_shots", 0),
                total_cost=data.get("total_cost", 0.0),
                generation_time=data.get("generation_time", 0.0)
            )

            return project
        except Exception as e:
            logger.error(f"从磁盘加载项目失败 {project_id}: {e}")
            return None

    def update_project(self, project: Project):
        """更新项目"""
        if project.id in self._project_cache:
            self._project_cache[project.id] = project

        # 保存到磁盘
        self._save_project_metadata(project)

        # 记录更新日志
        self._log_project_event(project, f"项目更新: {project.status.value}")

    def update_project_status(self, project_id: str, new_status: ProjectStatus, message: str = ""):
        """更新项目状态"""
        project = self.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return False

        old_status = project.status
        project.update_status(new_status)

        # 保存更新
        self.update_project(project)

        # 记录状态变更
        status_message = f"状态变更: {old_status.value} -> {new_status.value}"
        if message:
            status_message += f" ({message})"

        self._log_project_event(project, status_message)

        logger.info(f"项目状态已更新 {project_id}: {old_status.value} -> {new_status.value}")
        return True

    def save_shot_plan(self, project_id: str, shot_plan: ShotPlan):
        """保存分镜计划"""
        project = self.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return False

        metadata_dir = Path(project.output_dir) / "metadata"
        shot_plan_file = metadata_dir / "shot_plan.json"

        try:
            with open(shot_plan_file, 'w', encoding='utf-8') as f:
                json.dump(shot_plan.to_dict(), f, ensure_ascii=False, indent=2)

            # 更新项目统计
            project.total_shots = shot_plan.total_shots
            self.update_project(project)

            self._log_project_event(project, f"分镜计划已保存: {shot_plan.total_shots}个镜头")
            logger.info(f"分镜计划已保存 {project_id}: {shot_plan.total_shots}个镜头")
            return True
        except Exception as e:
            logger.error(f"保存分镜计划失败 {project_id}: {e}")
            return False

    def save_timing_plan(self, project_id: str, timing_plan: TimingPlan):
        """保存时长规划"""
        project = self.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return False

        metadata_dir = Path(project.output_dir) / "metadata"
        timing_plan_file = metadata_dir / "timing_plan.json"

        try:
            with open(timing_plan_file, 'w', encoding='utf-8') as f:
                json.dump(timing_plan.to_dict(), f, ensure_ascii=False, indent=2)

            self._log_project_event(project, f"时长规划已保存: 总时长{timing_plan.actual_total_duration}秒")
            logger.info(f"时长规划已保存 {project_id}: 总时长{timing_plan.actual_total_duration}秒")
            return True
        except Exception as e:
            logger.error(f"保存时长规划失败 {project_id}: {e}")
            return False

    def save_raw_clip(self, project_id: str, shot: Shot, file_path: str) -> bool:
        """保存原始生成片段"""
        project = self.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return False

        raw_clips_dir = Path(project.output_dir) / "raw_clips"
        target_filename = shot.get_filename()
        target_path = raw_clips_dir / target_filename

        try:
            # 如果源文件和目标文件不同，则复制
            if os.path.abspath(file_path) != os.path.abspath(target_path):
                shutil.copy2(file_path, target_path)

            # 更新镜头信息
            shot.file_path = str(target_path)
            shot.update_status(ShotStatus.COMPLETED)

            # 更新项目统计
            project.add_shot_result(success=True, cost=shot.generation_cost, time=shot.generation_time)
            self.update_project(project)

            self._log_project_event(project, f"镜头片段已保存: {target_filename}")
            logger.info(f"原始片段已保存 {project_id}: {target_filename}")
            return True
        except Exception as e:
            logger.error(f"保存原始片段失败 {project_id}/{shot.id}: {e}")
            return False

    def save_final_video(self, project_id: str, video_path: str) -> bool:
        """保存最终合成视频"""
        project = self.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return False

        project_dir = Path(project.output_dir)
        target_filename = f"final_video_{project.target_duration}s.mp4"
        target_path = project_dir / target_filename

        try:
            # 如果源文件和目标文件不同，则复制
            if os.path.abspath(video_path) != os.path.abspath(target_path):
                shutil.copy2(video_path, target_path)

            # 更新项目信息
            project.final_video_path = str(target_path)
            project.update_status(ProjectStatus.COMPLETED)
            self.update_project(project)

            self._log_project_event(project, f"最终视频已保存: {target_filename}")
            logger.info(f"最终视频已保存 {project_id}: {target_filename}")
            return True
        except Exception as e:
            logger.error(f"保存最终视频失败 {project_id}: {e}")
            return False

    def list_projects(self, status_filter: Optional[ProjectStatus] = None) -> List[ProjectSummary]:
        """列出项目摘要"""
        summaries = []

        if not self.projects_dir.exists():
            return summaries

        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project = self._load_project_from_disk(project_dir.name)
            if not project:
                continue

            # 状态过滤
            if status_filter and project.status != status_filter:
                continue

            summary = ProjectSummary(
                id=project.id,
                title=project.title,
                status=project.status,
                target_duration=project.target_duration,
                total_shots=project.total_shots,
                progress_percentage=project.get_progress_percentage(),
                created_at=project.created_at,
                updated_at=project.updated_at,
                final_video_path=project.final_video_path,
                thumbnail_path=project.thumbnail_path
            )
            summaries.append(summary)

        # 按更新时间倒序排列
        summaries.sort(key=lambda x: x.updated_at, reverse=True)

        logger.info(f"列出项目摘要: {len(summaries)}个项目")
        return summaries

    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project_dir = self.projects_dir / project_id
        if not project_dir.exists():
            logger.warning(f"要删除的项目不存在: {project_id}")
            return False

        try:
            # 从缓存中移除
            self._project_cache.pop(project_id, None)

            # 删除项目目录
            shutil.rmtree(project_dir)

            logger.info(f"项目已删除: {project_id}")
            return True
        except Exception as e:
            logger.error(f"删除项目失败 {project_id}: {e}")
            return False

    def cleanup_temp_files(self, project_id: Optional[str] = None):
        """清理临时文件"""
        if project_id:
            # 清理特定项目的临时文件
            project_temp_dir = self.temp_dir / project_id
            if project_temp_dir.exists():
                try:
                    shutil.rmtree(project_temp_dir)
                    logger.info(f"项目临时文件已清理: {project_id}")
                except Exception as e:
                    logger.error(f"清理项目临时文件失败 {project_id}: {e}")
        else:
            # 清理所有临时文件
            if self.temp_dir.exists():
                try:
                    shutil.rmtree(self.temp_dir)
                    self.temp_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("所有临时文件已清理")
                except Exception as e:
                    logger.error(f"清理临时文件失败: {e}")

    def _log_project_event(self, project: Project, event: str):
        """记录项目事件日志"""
        if not project.output_dir:
            return

        logs_dir = Path(project.output_dir) / "logs"
        timeline_log = logs_dir / "project_timeline.log"

        try:
            with open(timeline_log, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] {event}\n")
        except Exception as e:
            logger.error(f"记录项目事件失败: {e}")

    def get_project_statistics(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        stats = {
            "total_projects": 0,
            "status_distribution": {},
            "total_videos_generated": 0,
            "total_cost": 0.0,
            "total_generation_time": 0.0,
            "average_shots_per_project": 0.0
        }

        if not self.projects_dir.exists():
            return stats

        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                project = self._load_project_from_disk(project_dir.name)
                if project:
                    projects.append(project)

        stats["total_projects"] = len(projects)

        if projects:
            # 状态分布
            for project in projects:
                status = project.status.value
                stats["status_distribution"][status] = stats["status_distribution"].get(status, 0) + 1

            # 完成的项目统计
            completed_projects = [p for p in projects if p.status == ProjectStatus.COMPLETED]
            stats["total_videos_generated"] = len(completed_projects)

            # 总成本和时间
            stats["total_cost"] = sum(p.total_cost for p in projects)
            stats["total_generation_time"] = sum(p.generation_time for p in projects)

            # 平均镜头数
            total_shots = sum(p.total_shots for p in projects if p.total_shots > 0)
            projects_with_shots = len([p for p in projects if p.total_shots > 0])
            if projects_with_shots > 0:
                stats["average_shots_per_project"] = total_shots / projects_with_shots

        return stats
