"""
对话式视频生成服务
支持用户与AI进行多轮对话，动态调整脚本和分镜
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from app.services.llm.service import LLMService
from app.services.video_generation.orchestrator import VideoGenerationOrchestrator
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConversationalGenerationService:
    """对话式视频生成服务"""

    def __init__(self):
        self.llm_service = LLMService()
        self.orchestrator = VideoGenerationOrchestrator()

    async def start_conversation(
        self,
        user_id: int,
        initial_topic: str,
        style: str = "专业",
        shot_count: int = 6,
        target_duration: int = 60
    ) -> Dict[str, Any]:
        """
        开始一个新的对话式生成会话

        Args:
            user_id: 用户ID
            initial_topic: 初始主题
            style: 视频风格
            shot_count: 镜头数量
            target_duration: 目标时长

        Returns:
            包含会话ID、初始脚本和AI响应的字典
        """
        logger.info(f"开始对话式生成会话: {initial_topic}")

        # 生成初始脚本和分镜
        script_result = await self.orchestrator.generate_script(
            topic=initial_topic,
            style=style,
            shot_count=shot_count,
            target_duration=target_duration
        )

        if not script_result.get("success"):
            return {
                "success": False,
                "error": script_result.get("error", "脚本生成失败")
            }

        script = script_result.get("script", "")
        shots = script_result.get("shots", [])

        # 构建初始对话历史
        conversation_history = [
            {
                "role": "user",
                "content": initial_topic,
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": f"我已经为您生成了初始脚本和分镜方案。\n\n{script}\n\n您可以告诉我需要调整的地方，比如：\n- 修改某个镜头的内容\n- 调整整体风格或节奏\n- 增加或删除镜头\n- 修改脚本内容",
                "script": script,
                "shots": shots,
                "timestamp": datetime.now().isoformat()
            }
        ]

        return {
            "success": True,
            "conversation_history": conversation_history,
            "script": script,
            "shots": shots,
            "metadata": {
                "topic": initial_topic,
                "style": style,
                "shot_count": shot_count,
                "target_duration": target_duration
            }
        }

    async def process_user_message(
        self,
        user_id: int,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        current_script: str,
        current_shots: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理用户消息并生成AI响应

        Args:
            user_id: 用户ID
            user_message: 用户消息
            conversation_history: 对话历史
            current_script: 当前脚本
            current_shots: 当前分镜
            metadata: 元数据（主题、风格等）

        Returns:
            包含AI响应、更新后的脚本和分镜的字典
        """
        logger.info(f"处理用户消息: {user_message[:50]}...")

        # 添加用户消息到历史
        conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # 分析用户意图并修改脚本
        modification_result = await self._analyze_and_modify(
            user_message=user_message,
            conversation_history=conversation_history,
            current_script=current_script,
            current_shots=current_shots,
            metadata=metadata
        )

        if not modification_result.get("success"):
            ai_response = f"抱歉，我在处理您的请求时遇到了问题：{modification_result.get('error')}"
            conversation_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "success": False,
                "error": modification_result.get("error"),
                "conversation_history": conversation_history,
                "script": current_script,
                "shots": current_shots
            }

        # 获取修改后的脚本和分镜
        new_script = modification_result.get("script", current_script)
        new_shots = modification_result.get("shots", current_shots)
        ai_explanation = modification_result.get("explanation", "")

        # 构建AI响应
        ai_response = f"{ai_explanation}\n\n{new_script}\n\n如果您对这个方案满意，可以点击确认生成视频。如果还需要调整，请继续告诉我。"

        conversation_history.append({
            "role": "assistant",
            "content": ai_response,
            "script": new_script,
            "shots": new_shots,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "conversation_history": conversation_history,
            "script": new_script,
            "shots": new_shots,
            "ai_response": ai_response
        }

    async def _analyze_and_modify(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        current_script: str,
        current_shots: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析用户意图并修改脚本和分镜

        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            current_script: 当前脚本
            current_shots: 当前分镜
            metadata: 元数据

        Returns:
            包含修改后的脚本、分镜和解释的字典
        """
        # 构建提示词
        prompt = self._build_modification_prompt(
            user_message=user_message,
            conversation_history=conversation_history,
            current_script=current_script,
            current_shots=current_shots,
            metadata=metadata
        )

        # 调用LLM进行分析和修改
        llm_result = await self.llm_service.call(
            prompt=prompt,
            temperature=0.7,
            max_tokens=4000
        )

        if not llm_result.get("success"):
            return {
                "success": False,
                "error": llm_result.get("error", "LLM调用失败")
            }

        # 解析LLM响应
        response_text = llm_result.get("content", "")

        try:
            # 尝试从响应中提取JSON
            parsed_result = self._parse_llm_response(response_text)

            return {
                "success": True,
                "script": parsed_result.get("script", current_script),
                "shots": parsed_result.get("shots", current_shots),
                "explanation": parsed_result.get("explanation", "我已经根据您的要求进行了调整。")
            }
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return {
                "success": False,
                "error": f"解析响应失败: {str(e)}"
            }

    def _build_modification_prompt(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        current_script: str,
        current_shots: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """构建修改脚本的提示词"""

        # 构建对话历史摘要
        history_summary = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}..."
            for msg in conversation_history[-5:]  # 只取最近5条
        ])

        # 构建分镜摘要
        shots_summary = "\n".join([
            f"镜头{shot['sequence']}: {shot.get('prompt', shot.get('description', ''))} ({shot.get('duration', 0)}秒)"
            for shot in current_shots
        ])

        prompt = f"""你是一个专业的视频脚本编辑助手。用户正在与你对话，希望调整视频脚本和分镜方案。

**原始主题**: {metadata.get('topic', '')}
**视频风格**: {metadata.get('style', '专业')}
**目标时长**: {metadata.get('target_duration', 60)}秒
**镜头数量**: {metadata.get('shot_count', 6)}个

**对话历史**:
{history_summary}

**当前脚本**:
{current_script}

**当前分镜**:
{shots_summary}

**用户最新要求**:
{user_message}

请根据用户的要求，修改脚本和分镜方案。你需要：
1. 理解用户的具体需求（是修改某个镜头、调整风格、还是重新规划）
2. 对脚本和分镜进行相应的修改
3. 保持视频的整体连贯性和专业性
4. 确保修改后的总时长接近目标时长

请以JSON格式返回结果：
{{
  "explanation": "简要说明你做了哪些修改",
  "script": "修改后的完整脚本",
  "shots": [
    {{
      "sequence": 1,
      "description": "镜头描述",
      "prompt": "视频生成提示词",
      "duration": 10,
      "scene_type": "场景类型"
    }}
  ]
}}

注意：
- shots数组必须包含所有镜头，即使某些镜头没有修改
- 每个镜头必须包含sequence、description、prompt、duration字段
- 确保JSON格式正确，可以被解析
"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """解析LLM响应，提取JSON"""

        # 尝试直接解析JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # 尝试从markdown代码块中提取JSON
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试查找第一个完整的JSON对象
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError("无法从响应中提取有效的JSON")

    async def confirm_and_generate(
        self,
        user_id: int,
        task_id: str,
        final_script: str,
        final_shots: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        确认脚本并开始生成视频

        Args:
            user_id: 用户ID
            task_id: 任务ID
            final_script: 最终脚本
            final_shots: 最终分镜
            options: 生成选项（旁白、配音等）

        Returns:
            生成结果
        """
        logger.info(f"确认脚本并开始生成视频: {task_id}")

        # 调用orchestrator生成视频
        result = await self.orchestrator.generate_videos_for_shots(
            shots=final_shots,
            task_id=task_id,
            options=options or {}
        )

        return result
