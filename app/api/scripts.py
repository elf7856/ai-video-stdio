"""
脚本生成API - 使用Gemini生成视频脚本和分镜
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from app.services.llm.service import llm_service
from app.services.planning.duration_planner import DurationPlanner
from app.prompts.video_generation import ScriptGenerationPrompt # Add import

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scripts", tags=["脚本生成"])


class ScriptGenerateRequest(BaseModel):
    """脚本生成请求"""
    topic: str
    style: Optional[str] = "专业"
    targetDuration: Optional[int] = None  # 可选，如果不提供则自动计算
    shotCount: Optional[int] = None # Add shotCount
    additionalRequirements: Optional[str] = None


class Shot(BaseModel):
    """单个镜头"""
    sequence: int
    prompt: str
    duration: float
    shotType: Optional[str] = None


class ScriptGenerateResponse(BaseModel):
    """脚本生成响应"""
    success: bool
    script: str
    shots: List[Shot]
    totalDuration: float
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/generate", response_model=ScriptGenerateResponse)
async def generate_script(request: ScriptGenerateRequest):
    """
    生成视频脚本和分镜

    使用Gemini AI根据用户输入的主题生成完整的视频脚本和分镜方案
    """
    try:
        # 自动计算时长（如果未提供）
        if request.targetDuration is None:
            estimated_duration = DurationPlanner.estimate_duration_from_topic(
                request.topic,
                request.style
            )
            logger.info(f"自动估算视频时长: {estimated_duration}秒 (主题长度: {len(request.topic)}字, 风格: {request.style})")
            request.targetDuration = estimated_duration

        logger.info(f"收到脚本生成请求: 主题={request.topic}, 风格={request.style}, 时长={request.targetDuration}秒")

        # 使用统一的提示词构建器
        prompt = ScriptGenerationPrompt.build(
            topic=request.topic,
            style=request.style,
            target_duration=request.targetDuration,
            shot_count=request.shotCount or 6,
            additional_requirements=request.additionalRequirements or ""
        )

        # 调用Gemini
        result = llm_service.call(
            messages=[{"role": "user", "content": prompt}],
            provider="google",
            temperature=0.7,
            max_tokens=2000
        )

        if not result["success"]:
            logger.error(f"Gemini调用失败: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"AI生成失败: {result.get('error', '未知错误')}"
            )

        content = result["content"]
        logger.info(f"Gemini返回内容长度: {len(content)}")

        # 解析Gemini返回的JSON
        import json
        import re

        # 提取JSON内容（去除可能的markdown代码块标记）
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个内容
            json_str = content.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}\n内容: {content[:500]}")
            raise HTTPException(
                status_code=500,
                detail="AI返回格式错误，无法解析"
            )

        # 验证必需字段
        if "script" not in data or "shots" not in data:
            raise HTTPException(
                status_code=500,
                detail="AI返回数据不完整"
            )

        # 构建响应
        shots = [
            Shot(
                sequence=shot.get("sequence", idx + 1),
                prompt=shot.get("prompt", ""),
                duration=float(shot.get("duration", 10.0)),
                shotType=shot.get("shotType")
            )
            for idx, shot in enumerate(data["shots"])
        ]

        total_duration = sum(shot.duration for shot in shots)

        response = ScriptGenerateResponse(
            success=True,
            script=data["script"],
            shots=shots,
            totalDuration=total_duration,
            metadata={
                "style": request.style,
                "shotCount": len(shots),
                "provider": result["provider"],
                "model": result.get("model", "gemini")
            }
        )

        logger.info(f"脚本生成成功: {len(shots)}个镜头, 总时长{total_duration}秒")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"脚本生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"服务器错误: {str(e)}"
        )


@router.post("/optimize")
async def optimize_script(script: str):
    """
    优化现有脚本

    使用Gemini优化用户提供的脚本，使其更专业、更有吸引力
    """
    try:
        prompt = f"""你是一个专业的视频脚本编辑专家。请优化以下脚本，使其更加专业、吸引人。

**原始脚本:**
{script}

**优化要求:**
1. 保持原意和核心内容
2. 优化语言表达，使其更流畅
3. 增强情感渲染和视觉感
4. 优化节奏感

请返回优化后的完整脚本。
"""

        result = llm_service.call(
            messages=[{"role": "user", "content": prompt}],
            provider="google",
            temperature=0.6
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"优化失败: {result.get('error', '未知错误')}"
            )

        return {
            "success": True,
            "optimizedScript": result["content"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"脚本优化失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器错误: {str(e)}"
        )


@router.post("/generate-shots")
async def generate_shot_prompts(script: str, shotCount: int = 5):
    """
    从脚本生成分镜提示词

    根据完整脚本，生成指定数量的分镜描述
    """
    try:
        prompt = f"""你是一个专业的视频分镜师。请根据以下脚本，创建{shotCount}个详细的分镜描述。

**脚本:**
{script}

**要求:**
1. 创建{shotCount}个镜头
2. 每个镜头包含详细的视觉描述
3. 描述要具体，包含场景、主体、动作、光线、氛围等
4. 适合用于AI视频生成（如Runway、Pika等）

请按JSON格式返回：
{{
    "shots": [
        {{
            "sequence": 1,
            "prompt": "详细的视觉描述...",
            "duration": 10.0,
            "shotType": "镜头类型"
        }}
    ]
}}
"""

        result = llm_service.call(
            messages=[{"role": "user", "content": prompt}],
            provider="google",
            temperature=0.7
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"生成失败: {result.get('error', '未知错误')}"
            )

        # 解析JSON
        import json
        import re

        content = result["content"]
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content.strip()

        data = json.loads(json_str)

        return {
            "success": True,
            "shots": data.get("shots", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分镜生成失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器错误: {str(e)}"
        )
