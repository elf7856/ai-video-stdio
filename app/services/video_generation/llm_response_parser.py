"""
LLM 响应解析和验证模块
提供强壮的 JSON 解析、schema 验证和错误处理
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator, ValidationError

logger = logging.getLogger(__name__)


class ShotSchema(BaseModel):
    """镜头数据 Schema"""
    sequence: int = Field(..., ge=1, description="镜头序号")
    prompt: str = Field(..., min_length=10, description="镜头描述")
    duration: float = Field(..., gt=0, le=8.0, description="镜头时长")
    shotType: str = Field(default="medium shot", description="镜头类型")

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or v.strip() == "":
            raise ValueError("镜头描述不能为空")
        return v.strip()


class ScriptGenerationResponse(BaseModel):
    """脚本生成响应 Schema"""
    script: str = Field(..., min_length=50, description="视频脚本")
    shots: List[ShotSchema] = Field(..., min_items=1, max_items=12, description="镜头列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

    @validator('script')
    def validate_script(cls, v):
        if not v or v.strip() == "":
            raise ValueError("脚本不能为空")
        return v.strip()

    @validator('shots')
    def validate_shots_sequence(cls, v):
        """验证镜头序号连续性"""
        sequences = [shot.sequence for shot in v]
        if len(sequences) != len(set(sequences)):
            raise ValueError("镜头序号不能重复")
        # 允许不从1开始，但必须连续
        sorted_seq = sorted(sequences)
        for i in range(len(sorted_seq) - 1):
            if sorted_seq[i+1] - sorted_seq[i] != 1:
                logger.warning(f"镜头序号不连续: {sequences}")
        return v


class LLMResponseParser:
    """LLM 响应解析器"""

    @staticmethod
    def extract_json_from_markdown(content: str) -> Optional[str]:
        """从 Markdown 代码块中提取 JSON"""
        # 尝试匹配 ```json ... ```
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # 尝试匹配 ``` ... ```
        code_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        return None

    @staticmethod
    def extract_json_from_text(content: str) -> Optional[str]:
        """从文本中提取 JSON 对象"""
        # 查找第一个 { 和最后一个 }
        start = content.find('{')
        end = content.rfind('}')

        if start != -1 and end != -1 and start < end:
            return content[start:end+1]

        return None

    @staticmethod
    def parse_json_safely(json_str: str) -> Optional[Dict[str, Any]]:
        """安全地解析 JSON 字符串"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.debug(f"原始内容: {json_str[:500]}...")
            return None

    @classmethod
    def parse_script_generation_response(
        cls,
        llm_response: str,
        fallback_shot_count: int = 6
    ) -> Optional[ScriptGenerationResponse]:
        """
        解析脚本生成响应

        Args:
            llm_response: LLM 原始响应
            fallback_shot_count: 如果解析失败，使用的默认镜头数

        Returns:
            ScriptGenerationResponse 或 None
        """
        # 1. 尝试从 Markdown 代码块提取
        json_str = cls.extract_json_from_markdown(llm_response)

        # 2. 如果失败，尝试从文本中提取
        if not json_str:
            json_str = cls.extract_json_from_text(llm_response)

        # 3. 如果还是失败，直接尝试解析整个响应
        if not json_str:
            json_str = llm_response.strip()

        # 4. 解析 JSON
        data = cls.parse_json_safely(json_str)
        if not data:
            logger.error("无法从 LLM 响应中提取有效的 JSON")
            return None

        # 5. 验证和清理数据
        try:
            # 确保必需字段存在
            if "script" not in data:
                logger.error("LLM 响应缺少 'script' 字段")
                return None

            if "shots" not in data or not isinstance(data["shots"], list):
                logger.error("LLM 响应缺少 'shots' 字段或格式错误")
                return None

            # 清理和标准化 shots 数据
            cleaned_shots = []
            for i, shot in enumerate(data["shots"]):
                if not isinstance(shot, dict):
                    logger.warning(f"跳过无效的镜头数据: {shot}")
                    continue

                # 确保必需字段存在
                if "prompt" not in shot:
                    logger.warning(f"镜头 {i+1} 缺少 prompt 字段")
                    continue

                # 标准化字段
                cleaned_shot = {
                    "sequence": shot.get("sequence", i + 1),
                    "prompt": shot["prompt"],
                    "duration": float(shot.get("duration", 6.0)),
                    "shotType": shot.get("shotType") or shot.get("shot_type", "medium shot")
                }

                cleaned_shots.append(cleaned_shot)

            data["shots"] = cleaned_shots

            # 6. 使用 Pydantic 验证
            return ScriptGenerationResponse(**data)

        except ValidationError as e:
            logger.error(f"LLM 响应验证失败: {e}")
            logger.debug(f"原始数据: {data}")
            return None
        except Exception as e:
            logger.error(f"解析 LLM 响应时发生未知错误: {e}")
            return None

    @staticmethod
    def create_fallback_response(
        topic: str,
        shot_count: int = 6,
        target_duration: int = 60
    ) -> ScriptGenerationResponse:
        """创建降级响应（当 LLM 解析失败时使用）"""
        shot_duration = target_duration / shot_count

        shots = [
            ShotSchema(
                sequence=i + 1,
                prompt=f"Scene {i+1} for {topic}: Professional cinematic shot with good lighting and composition",
                duration=min(shot_duration, 8.0),
                shotType="medium shot"
            )
            for i in range(shot_count)
        ]

        return ScriptGenerationResponse(
            script=f"This is a video about {topic}. Due to technical issues, a fallback script was generated.",
            shots=shots,
            metadata={"fallback": True}
        )
