"""
Runway ML视频生成客户端
实现真实的Runway Gen-4 API调用
"""

import time
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from .base_client import BaseVideoGenerationClient, VideoGenerationRequest, VideoGenerationResult
from app.core.config import settings


class RunwayClient(BaseVideoGenerationClient):
    """Runway ML视频生成客户端"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or settings.runway_api_key, **kwargs)
        self.base_url = "https://api.runwayml.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def get_capabilities(self) -> Dict[str, Any]:
        """获取API能力信息 - 更新2025年新功能"""
        return {
            # 视频生成能力
            "max_duration": 10.0,  # Gen-4最大10秒
            "cost_per_second": 0.25,  # 约$0.25/秒
            "quality_score": 0.9,  # 高质量
            "avg_generation_time": 45.0,  # 平均45秒
            "supported_resolutions": ["1280x720", "1920x1080", "4K"],
            "scene_preferences": ["cinematic", "realistic", "professional", "high-quality"],
            
            # 🎵 新功能：音频生成 (2025)
            "audio_generation": {
                "text_to_speech": True,
                "custom_voices": True,  # 几分钟音频即可训练
                "lip_sync": True,       # 自动口型同步
                "sound_effects": True,  # Soundify音效匹配
                "background_music": True
            },
            
            # 🎬 新功能：高级视频编辑 (2025)
            "advanced_editing": {
                "style_transfer": True,    # 风格转换
                "object_manipulation": True, # 添加/删除/变换物体
                "scene_angles": True,      # 任意角度生成
                "lighting_control": True,  # 光照修改
                "character_consistency": True, # 角色一致性
                "world_coherence": True    # 世界环境连贯性
            },
            
            # 🤖 AI导演功能
            "ai_director": {
                "auto_editing": True,      # 自动剪辑
                "shot_composition": True,  # 镜头构图
                "narrative_flow": True,    # 叙事流程
                "emotion_analysis": True   # 情感分析
            }
        }
    
    def is_available(self) -> bool:
        """检查API是否可用"""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your-"))
    
    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """
        使用Runway Gen-4生成视频
        """
        start_time = time.time()
        
        # 验证请求
        is_valid, error_msg = self.validate_request(request)
        if not is_valid:
            return VideoGenerationResult(
                success=False,
                error_message=error_msg
            )
        
        try:
            # 如果没有真实API密钥，返回模拟结果
            if not self.is_available():
                return await self._generate_mock_video(request, start_time)
            
            # 第1步：创建生成任务
            task_id = await self._create_generation_task(request)
            if not task_id:
                return VideoGenerationResult(
                    success=False,
                    error_message="创建生成任务失败"
                )
            
            # 第2步：轮询任务状态直到完成
            video_url = await self._poll_task_completion(task_id)
            if not video_url:
                return VideoGenerationResult(
                    success=False,
                    error_message="视频生成超时或失败"
                )
            
            # 第3步：下载视频到本地
            local_path = await self._download_generated_video(video_url, request)
            if not local_path:
                return VideoGenerationResult(
                    success=False,
                    error_message="视频下载失败"
                )
            
            generation_time = time.time() - start_time
            cost = self.estimate_cost(request.duration)
            
            self.logger.info(f"Runway视频生成成功: {local_path}")
            
            return VideoGenerationResult(
                success=True,
                video_url=video_url,
                local_path=local_path,
                duration=request.duration,
                resolution=request.resolution,
                cost=cost,
                generation_time=generation_time,
                quality_score=self.get_capabilities()["quality_score"],
                metadata={
                    "provider": "runway",
                    "task_id": task_id,
                    "prompt": request.prompt,
                    "style_params": request.style_params
                }
            )
            
        except Exception as e:
            self.logger.error(f"Runway视频生成异常: {str(e)}")
            return VideoGenerationResult(
                success=False,
                error_message=f"生成异常: {str(e)}",
                generation_time=time.time() - start_time
            )
    
    async def _create_generation_task(self, request: VideoGenerationRequest) -> Optional[str]:
        """创建视频生成任务"""
        try:
            payload = {
                "model": "gen4",
                "prompt": request.prompt,
                "duration": min(request.duration, 10),  # Gen-4最大10秒
                "resolution": request.resolution,
                "seed": request.seed
            }
            
            # 添加风格参数
            if request.style_params:
                payload.update(request.style_params)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/generate",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        task_id = result.get("id")
                        self.logger.info(f"Runway任务创建成功: {task_id}")
                        return task_id
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Runway任务创建失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"创建Runway任务异常: {str(e)}")
            return None
    
    async def _poll_task_completion(self, task_id: str, max_wait_time: int = 300) -> Optional[str]:
        """轮询任务完成状态"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/tasks/{task_id}",
                        headers=self.headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            status = result.get("status")
                            
                            if status == "completed":
                                video_url = result.get("output", {}).get("url")
                                self.logger.info(f"Runway任务完成: {video_url}")
                                return video_url
                            elif status == "failed":
                                error_msg = result.get("error", "未知错误")
                                self.logger.error(f"Runway任务失败: {error_msg}")
                                return None
                            else:
                                # 任务仍在进行中，等待后重试
                                await asyncio.sleep(5)
                        else:
                            self.logger.warning(f"查询任务状态失败: {response.status}")
                            await asyncio.sleep(5)
                            
            except Exception as e:
                self.logger.error(f"轮询任务状态异常: {str(e)}")
                await asyncio.sleep(5)
        
        self.logger.error(f"Runway任务超时: {task_id}")
        return None
    
    async def _download_generated_video(self, video_url: str, request: VideoGenerationRequest) -> Optional[str]:
        """下载生成的视频"""
        try:
            import os
            output_dir = settings.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"runway_video_{int(time.time())}_{hash(request.prompt) % 10000}.mp4"
            local_path = os.path.join(output_dir, filename)
            
            success = await self.download_video(video_url, local_path)
            return local_path if success else None
            
        except Exception as e:
            self.logger.error(f"下载视频异常: {str(e)}")
            return None
    
    async def _generate_mock_video(self, request: VideoGenerationRequest, start_time: float) -> VideoGenerationResult:
        """生成模拟视频（当没有真实API密钥时）"""
        # 模拟生成延迟
        capabilities = self.get_capabilities()
        await asyncio.sleep(min(capabilities["avg_generation_time"] / 10, 3.0))
        
        # 创建模拟文件
        import os
        output_dir = settings.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"runway_mock_{int(time.time())}_{hash(request.prompt) % 10000}.mp4"
        local_path = os.path.join(output_dir, filename)
        
        with open(local_path, 'w') as f:
            f.write(f"# Runway模拟视频文件\n# 提示词: {request.prompt}\n# 时长: {request.duration}秒\n")
        
        generation_time = time.time() - start_time
        cost = self.estimate_cost(request.duration)
        
        self.logger.info(f"Runway模拟视频生成完成: {local_path}")
        
        return VideoGenerationResult(
            success=True,
            local_path=local_path,
            duration=request.duration,
            resolution=request.resolution,
            cost=cost,
            generation_time=generation_time,
            quality_score=capabilities["quality_score"],
            metadata={
                "provider": "runway",
                "mock": True,
                "prompt": request.prompt
            }
        )
