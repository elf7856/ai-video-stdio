from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
import os
from datetime import datetime

from app.services.image.generator import ImageServiceManager
from app.core.config import settings

router = APIRouter(prefix="/api/images", tags=["images"])

# 初始化图像服务
image_manager = ImageServiceManager()

@router.get("/providers")
async def get_available_providers():
    """获取可用的图像生成器列表"""
    try:
        providers = image_manager.get_available_providers()
        provider_info = image_manager.get_provider_info()
        
        return {
            "available_providers": providers,
            "provider_info": provider_info,
            "default_provider": settings.default_image_provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取生成器信息失败: {str(e)}")

@router.post("/generate")
async def generate_image(
    prompt: str,
    style: Optional[str] = None,
    provider: Optional[str] = None,
    size: Optional[str] = None,  # "512x512", "1024x1024", etc.
    negative_prompt: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """生成图像"""
    try:
        # 解析尺寸
        image_size = None
        if size:
            try:
                width, height = map(int, size.split('x'))
                image_size = (width, height)
            except:
                raise HTTPException(status_code=400, detail="尺寸格式错误，请使用 '宽x高' 格式")
        
        # 生成图像
        image_path = await image_manager.generate_image(
            prompt=prompt,
            style=style,
            provider=provider,
            size=image_size,
            negative_prompt=negative_prompt
        )
        
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=500, detail="图像生成失败")
        
        # 返回图像文件
        return FileResponse(
            image_path,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")

@router.post("/generate-with-description")
async def generate_image_with_description(
    content_requirement: str,
    style: Optional[str] = "realistic",
    provider: Optional[str] = None,
    size: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """基于内容需求生成图像描述并生成图像"""
    try:
        # 解析尺寸
        image_size = None
        if size:
            try:
                width, height = map(int, size.split('x'))
                image_size = (width, height)
            except:
                raise HTTPException(status_code=400, detail="尺寸格式错误，请使用 '宽x高' 格式")
        
        # 生成图像
        image_path = await image_manager.generator.generate_image_with_description(
            content_requirement=content_requirement,
            style=style,
            size=image_size,
            provider=provider
        )
        
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=500, detail="图像生成失败")
        
        # 返回图像文件
        return FileResponse(
            image_path,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")

@router.post("/generate-batch")
async def generate_image_batch(
    prompts: List[str],
    style: Optional[str] = None,
    provider: Optional[str] = None,
    size: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """批量生成图像"""
    try:
        if len(prompts) > 10:
            raise HTTPException(status_code=400, detail="批量生成最多支持10个提示词")
        
        # 解析尺寸
        image_size = None
        if size:
            try:
                width, height = map(int, size.split('x'))
                image_size = (width, height)
            except:
                raise HTTPException(status_code=400, detail="尺寸格式错误，请使用 '宽x高' 格式")
        
        # 批量生成图像
        results = await image_manager.generator.generate_image_batch(
            prompts=prompts,
            style=style,
            size=image_size,
            negative_prompt=negative_prompt,
            provider=provider
        )
        
        # 处理结果
        successful_paths = []
        failed_prompts = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_prompts.append({
                    "index": i,
                    "prompt": prompts[i],
                    "error": str(result)
                })
            elif result and os.path.exists(result):
                successful_paths.append(result)
            else:
                failed_prompts.append({
                    "index": i,
                    "prompt": prompts[i],
                    "error": "生成失败"
                })
        
        return {
            "successful_count": len(successful_paths),
            "failed_count": len(failed_prompts),
            "successful_paths": successful_paths,
            "failed_prompts": failed_prompts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量生成失败: {str(e)}")

@router.post("/edit")
async def edit_image(
    image_path: str,
    operation: str,  # resize, filter, text
    **kwargs
):
    """编辑图像"""
    try:
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="图像文件不存在")
        
        result_path = image_manager.edit_image(image_path, operation, **kwargs)
        
        if not result_path or not os.path.exists(result_path):
            raise HTTPException(status_code=500, detail="图像编辑失败")
        
        # 返回编辑后的图像文件
        return FileResponse(
            result_path,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=edited_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像编辑失败: {str(e)}")

@router.get("/styles")
async def get_available_styles():
    """获取可用的风格列表"""
    styles = {
        "realistic": "写实风格，高细节，照片级质量",
        "anime": "动漫风格，鲜艳色彩，详细插画",
        "cartoon": "卡通风格，简单色彩，清晰线条",
        "oil_painting": "油画风格，艺术感，质感笔触",
        "watercolor": "水彩画风格，柔和色彩，流动感",
        "cyberpunk": "赛博朋克风格，霓虹灯，未来感",
        "vintage": "复古风格，复古色彩，老式风格",
        "minimalist": "极简风格，简单，干净，几何"
    }
    
    return {
        "styles": styles,
        "default_style": "realistic"
    } 