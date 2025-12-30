from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.models.video import Video, VideoEdit, VideoCreate, VideoResponse, VideoEditCreate, VideoEditResponse
from app.services.video.processor import VideoProcessor
from app.services.video.manager import VideoProcessingManager
from app.services.llm.analyzer import VideoAnalyzer
from app.core.config import settings
from app.utils.database import get_db
from app.services.video.downloader import VideoDownloader

router = APIRouter(prefix="/api/videos", tags=["videos"])

# 初始化服务
video_processor = VideoProcessor()
video_analyzer = VideoAnalyzer()
video_manager = VideoProcessingManager()

@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """上传视频文件"""
    
    # 检查文件格式
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.allowed_video_formats:
        raise HTTPException(status_code=400, detail="不支持的文件格式")
    
    # 检查文件大小
    if file.size > settings.max_file_size:
        raise HTTPException(status_code=400, detail="文件大小超过限制")
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 获取视频信息
    video_info = video_processor.get_video_info(file_path)
    if "error" in video_info:
        raise HTTPException(status_code=500, detail=video_info["error"])
    
    # 创建数据库记录
    video = Video(
        filename=filename,
        original_path=file_path,
        title=title or file.filename,
        description=description,
        duration=video_info.get("duration"),
        resolution=video_info.get("resolution"),
        file_size=video_info.get("file_size"),
        format=file_ext[1:]  # 去掉点号
    )
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    return VideoResponse.from_orm(video)

@router.post("/process-url")
async def process_video_from_url(
    url: str,
    auto_analyze: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """从URL处理视频"""
    
    # 验证URL格式
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="无效的URL格式")
    
    # 在后台处理视频
    if background_tasks:
        background_tasks.add_task(process_video_url_background, url, auto_analyze, db)
        return {
            "message": "视频处理已开始",
            "url": url,
            "auto_analyze": auto_analyze
        }
    else:
        # 同步处理
        result = await video_manager.process_video_from_url(url, auto_analyze)
        
        if result["success"]:
            # 保存到数据库
            video = Video(
                filename=os.path.basename(result["video_path"]),
                original_path=result["video_path"],
                title=result["video_title"],
                description=f"从 {result['platform']} 下载",
                duration=result["video_info"].get("duration"),
                resolution=result["video_info"].get("resolution"),
                file_size=result["video_info"].get("file_size"),
                format="mp4",
                analysis=result["analysis"],
                tags=result["analysis"].get("tags") if result["analysis"] else None
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            return {
                "success": True,
                "video": VideoResponse.from_orm(video),
                "processing_result": result
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])

async def process_video_url_background(url: str, auto_analyze: bool, db: Session):
    """后台处理URL视频"""
    try:
        result = await video_manager.process_video_from_url(url, auto_analyze)
        
        if result["success"]:
            # 保存到数据库
            video = Video(
                filename=os.path.basename(result["video_path"]),
                original_path=result["video_path"],
                title=result["video_title"],
                description=f"从 {result['platform']} 下载",
                duration=result["video_info"].get("duration"),
                resolution=result["video_info"].get("resolution"),
                file_size=result["video_info"].get("file_size"),
                format="mp4",
                analysis=result["analysis"],
                tags=result["analysis"].get("tags") if result["analysis"] else None
            )
            
            db.add(video)
            db.commit()
            
            print(f"视频处理完成: {result['video_title']}")
        else:
            print(f"视频处理失败: {result['error']}")
            
    except Exception as e:
        print(f"后台视频处理失败: {str(e)}")

@router.post("/{video_id}/analyze")
async def analyze_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """分析视频内容"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 在后台任务中进行分析
    background_tasks.add_task(analyze_video_background, video_id, db)
    
    return {"message": "视频分析已开始", "video_id": video_id}

async def analyze_video_background(video_id: int, db: Session):
    """后台分析视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return
    
    try:
        # 使用视频管理器进行分析
        analysis_result = await video_manager.analyze_video_content(video.original_path)
        
        if analysis_result["success"]:
            # 更新数据库
            video.analysis = analysis_result["analysis"]
            if "tags" in analysis_result["analysis"]:
                video.tags = analysis_result["analysis"]["tags"]
            
            db.commit()
            print(f"视频分析完成: {video.title}")
        else:
            print(f"视频分析失败: {analysis_result['error']}")
        
    except Exception as e:
        print(f"视频分析失败: {str(e)}")

@router.post("/{video_id}/summary")
async def generate_video_summary(
    video_id: int,
    summary_type: str = "text",
    db: Session = Depends(get_db)
):
    """生成视频摘要"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    try:
        summary_result = await video_manager.generate_video_summary(
            video.original_path, summary_type
        )
        
        if summary_result["success"]:
            return {
                "success": True,
                "summary_type": summary_type,
                "content": summary_result["content"],
                "analysis": summary_result["analysis"]
            }
        else:
            raise HTTPException(status_code=500, detail=summary_result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {str(e)}")

@router.post("/{video_id}/edit")
async def edit_video(
    video_id: int,
    instruction: str,
    db: Session = Depends(get_db)
):
    """使用自然语言编辑视频"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    try:
        edit_result = await video_manager.process_natural_language_edit(
            video.original_path, instruction
        )
        
        if edit_result["success"]:
            return {
                "success": True,
                "edit_type": edit_result["edit_type"],
                "instruction_analysis": edit_result["instruction_analysis"],
                "content_description": edit_result["content_description"],
                "result": edit_result["result"]
            }
        else:
            raise HTTPException(status_code=500, detail=edit_result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频编辑失败: {str(e)}")

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """获取视频信息"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    return VideoResponse.from_orm(video)

@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取视频列表"""
    videos = db.query(Video).offset(skip).limit(limit).all()
    return [VideoResponse.from_orm(video) for video in videos]

@router.post("/{video_id}/edit", response_model=VideoEditResponse)
async def create_video_edit(
    video_id: int,
    edit_data: VideoEditCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建视频编辑任务"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 创建编辑记录
    video_edit = VideoEdit(
        video_id=video_id,
        instruction=edit_data.instruction,
        edit_type=edit_data.edit_type,
        start_time=edit_data.start_time,
        end_time=edit_data.end_time,
        duration=edit_data.duration
    )
    
    db.add(video_edit)
    db.commit()
    db.refresh(video_edit)
    
    # 在后台执行编辑任务
    background_tasks.add_task(process_video_edit_background, video_edit.id, db)
    
    return VideoEditResponse.from_orm(video_edit)

async def process_video_edit_background(edit_id: int, db: Session):
    """后台处理视频编辑"""
    edit = db.query(VideoEdit).filter(VideoEdit.id == edit_id).first()
    if not edit:
        return
    
    try:
        # 更新状态为处理中
        edit.status = "processing"
        db.commit()
        
        # 获取视频信息
        video = db.query(Video).filter(Video.id == edit.video_id).first()
        
        # 使用视频管理器处理编辑
        edit_result = await video_manager.process_natural_language_edit(
            video.original_path, edit.instruction
        )
        
        if edit_result["success"]:
            # 更新状态为完成
            edit.status = "completed"
            edit.completed_at = datetime.utcnow()
            edit.generated_content = {
                "instruction_analysis": edit_result["instruction_analysis"],
                "content_description": edit_result["content_description"],
                "result": edit_result["result"]
            }
            
            # 如果有输出文件，保存路径
            if edit_result["result"]["success"] and "output_path" in edit_result["result"]:
                edit.output_path = edit_result["result"]["output_path"]
        else:
            # 更新状态为失败
            edit.status = "failed"
        
        db.commit()
        
    except Exception as e:
        # 更新状态为失败
        edit.status = "failed"
        db.commit()
        print(f"视频编辑失败: {str(e)}")

@router.get("/{video_id}/download")
async def download_video(video_id: int, db: Session = Depends(get_db)):
    """下载视频文件"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if not os.path.exists(video.original_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    return FileResponse(
        video.original_path,
        filename=video.filename,
        media_type="video/mp4"
    )

@router.get("/platforms/supported")
async def get_supported_platforms():
    """获取支持的视频平台"""
    return {
        "platforms": [
            "youtube",
            "bilibili", 
            "tiktok",
            "instagram",
            "twitter",
            "general"
        ],
        "description": "支持从这些平台下载视频"
    }

@router.post("/url/info")
async def get_video_info_from_url(url: str):
    """从URL获取视频信息（不下载）"""
    try:
        downloader = VideoDownloader()
        info = await downloader.get_video_info(url)
        
        if info["success"]:
            return {
                "success": True,
                "info": info
            }
        else:
            raise HTTPException(status_code=400, detail=info["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取视频信息失败: {str(e)}")

@router.post("/download-with-cookies")
async def download_video_with_cookies(
    url: str = Form(...),
    cookies_content: str = Form(..., description="Base64编码的cookies.txt文件内容")
):
    """使用用户提供的cookies下载视频"""
    try:
        import base64
        import tempfile
        import os
        
        # 解码cookies内容
        try:
            cookies_data = base64.b64decode(cookies_content).decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cookies文件解码失败: {str(e)}")
        
        # 创建临时cookies文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(cookies_data)
            temp_cookies_path = f.name
        
        try:
            # 使用cookies下载视频
            downloader = VideoDownloader()
            result = await downloader.download_video(url, cookies_file=temp_cookies_path)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "视频下载成功",
                    "file_path": result["file_path"],
                    "title": result.get("title"),
                    "duration": result.get("duration"),
                    "platform": result.get("platform")
                }
            else:
                raise HTTPException(status_code=400, detail=f"下载失败: {result['error']}")
                
        finally:
            # 清理临时cookies文件
            if os.path.exists(temp_cookies_path):
                os.unlink(temp_cookies_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}") 