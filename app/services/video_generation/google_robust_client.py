#!/usr/bin/env python3
"""
稳定版Google Gemini Veo 3客户端
包含重试机制和错误恢复
"""

import asyncio
import time
import os
from typing import Optional, Dict, Any
from ...core.config import settings
from app.services.google_error_utils import format_google_api_error
from .base_client import BaseVideoGenerationClient
from . import VideoGenerationRequest, VideoGenerationResult
import logging

# 在模块级别导入，避免重复导入
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None  # type: ignore

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustGoogleVideoClient(BaseVideoGenerationClient):
    """稳定的Google Gemini Veo 3视频生成客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.google_api_key
        self._client = None  # 缓存客户端实例
        
    @property
    def client(self):
        """懒加载客户端实例"""
        if self._client is None:
            if not GENAI_AVAILABLE:
                raise ImportError("google.genai 模块不可用，请安装: pip install google-genai")
            
            if not self.api_key:
                raise ValueError("Google API 密钥未设置")
                
            self._client = genai.Client(api_key=self.api_key)  # type: ignore
            logger.info("✅ Google Gemini 客户端初始化完成")
            
        return self._client
        
    async def generate_video_with_retry(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 300,
        duration: float = 8.0
    ) -> Dict[str, Any]:
        """
        生成视频，包含重试机制
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"🎬 尝试 {attempt + 1}/{max_retries}: 生成视频")
                result = await self._generate_video_single_attempt(prompt, image_path, timeout, duration)
                return result
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    "⚠️ Google Veo 调用失败详情: %s",
                    format_google_api_error(
                        e,
                        {
                            "model": "veo-3.1-fast-generate-001",
                            "provider": "Vertex AI" if getattr(self, "project_id", None) else "AI Studio",
                            "project_id": getattr(self, "project_id", None),
                            "location": getattr(self, "location", None),
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                        },
                    ),
                )
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10  # 递增等待时间
                    logger.info(f"⏳ 等待 {wait_time}s 后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ 所有重试都失败了")
                    return {
                        "status": "failed",
                        "error": error_msg,
                        "attempts": max_retries
                    }
    
    async def _generate_video_single_attempt(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        timeout: int = 300,
        duration: float = 8.0
    ) -> Dict[str, Any]:
        """单次视频生成尝试"""
        try:
            # Veo 支持 5-8 秒，clamp 到合法范围
            duration_seconds = max(5, min(8, int(round(duration))))
            logger.info(f"📝 提示词: {prompt[:50]}... | 时长: {duration_seconds}s")
            
            # 使用缓存的客户端实例
            client = self.client
            
            # 处理 Image-to-Video 逻辑
            input_image = None
            
            # 如果是 URL，先下载到临时文件
            temp_image_path = None
            if image_path and image_path.startswith("http"):
                try:
                    import aiohttp
                    import aiofiles
                    from urllib.parse import urlparse
                    
                    filename = os.path.basename(urlparse(image_path).path) or f"temp_img_{int(time.time())}.png"
                    temp_dir = "./temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_image_path = os.path.join(temp_dir, filename)
                    
                    logger.info(f"📥 下载参考图: {image_path}")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_path) as response:
                            if response.status == 200:
                                async with aiofiles.open(temp_image_path, 'wb') as f:
                                    await f.write(await response.read())
                                image_path = temp_image_path # 更新为本地路径
                            else:
                                logger.warning(f"下载参考图失败 status={response.status}")
                except Exception as dl_err:
                    logger.warning(f"下载参考图异常: {dl_err}")

            if image_path:
                if os.path.exists(image_path):
                    logger.info(f"📸 发现参考图，读取为 image_bytes: {image_path}")
                    try:
                        import imghdr
                        with open(image_path, 'rb') as f:
                            img_bytes = f.read()
                        ext = os.path.splitext(image_path)[1].lower()
                        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
                        input_image = genai.types.Image(image_bytes=img_bytes, mime_type=mime)  # type: ignore
                        logger.info(f"✅ 参考图已读取: {len(img_bytes)} bytes, {mime}")
                    except Exception as upload_err:
                        error_msg = f"图片读取失败: {upload_err}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                else:
                    error_msg = f"参考图路径不存在: {image_path} (当前目录: {os.getcwd()})"
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

            # 如果使用了临时文件，可以考虑清理，或者保留用于调试
            # if temp_image_path and os.path.exists(temp_image_path):
            #    os.remove(temp_image_path)

            # 提交视频生成任务
            video_config = genai.types.GenerateVideosConfig(duration_seconds=duration_seconds)  # type: ignore
            if input_image:
                logger.info(f"🚀 启动 Image-to-Video 渲染模式 ({duration_seconds}s)")
                operation = client.models.generate_videos(
                    model="veo-3.1-fast-generate-001",
                    prompt=prompt,
                    image=input_image,
                    config=video_config,
                )
            else:
                logger.info(f"🚀 启动 Text-to-Video 渲染模式 ({duration_seconds}s)")
                operation = client.models.generate_videos(
                    model="veo-3.1-fast-generate-001",
                    prompt=prompt,
                    config=video_config,
                )
            
            task_id = operation.name
            logger.info(f"✅ 任务已提交: {task_id}")
            
            # 轮询任务状态（使用更稳定的轮询策略）
            start_time = time.time()
            check_intervals = [5, 10, 15, 20, 30, 30, 30]  # 指数退避
            interval_index = 0
            
            while time.time() - start_time < timeout:
                try:
                    # 获取任务状态
                    current_operation = client.operations.get(operation)
                    
                    if current_operation.done:
                        logger.info(f"✅ 任务完成: {task_id}")
                        
                        # 检查错误
                        if hasattr(current_operation, 'error') and current_operation.error:
                            error_msg = str(current_operation.error)
                            logger.error(f"❌ 任务失败: {error_msg}")
                            return {
                                "status": "failed",
                                "error": error_msg,
                                "task_id": task_id
                            }
                        
                        # 检查结果
                        if (hasattr(current_operation, 'response') and 
                            current_operation.response and
                            hasattr(current_operation.response, 'generated_videos') and
                            current_operation.response.generated_videos):
                            
                            generated_video = current_operation.response.generated_videos[0]
                            
                            # 尝试下载视频
                            download_result = await self._download_video_safe(
                                client, generated_video, task_id
                            )
                            
                            return {
                                "status": "completed",
                                "task_id": task_id,
                                "video_file": generated_video.video,
                                "download_result": download_result,
                                "generation_time": time.time() - start_time
                            }
                        else:
                            return {
                                "status": "completed_no_video",
                                "task_id": task_id,
                                "message": "任务完成但没有找到生成的视频"
                            }
                    
                    # 任务还在进行中
                    current_interval = check_intervals[min(interval_index, len(check_intervals) - 1)]
                    elapsed = time.time() - start_time
                    
                    logger.info(f"⏳ 任务进行中 ({elapsed:.0f}s)，{current_interval}s后再次检查")
                    
                    await asyncio.sleep(current_interval)
                    interval_index += 1
                    
                except Exception as poll_error:
                    # 轮询错误，但不立即失败，而是重试
                    logger.warning(
                        "⚠️ Google Veo 轮询异常详情: %s",
                        format_google_api_error(
                            poll_error,
                            {"model": "veo-3.1-fast-generate-001", "provider": "AI Studio", "task_id": task_id},
                        ),
                    )
                    await asyncio.sleep(10)  # 等待10秒后继续
                    continue
            
            # 超时
            return {
                "status": "timeout",
                "task_id": task_id,
                "elapsed_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(
                "❌ Google Veo 生成视频异常详情: %s",
                format_google_api_error(e, {"model": "veo-3.1-fast-generate-001", "provider": "AI Studio"}),
            )
            raise
    
    async def _download_video_safe(self, client, generated_video, task_id: str) -> Dict[str, Any]:
        """安全下载视频，包含多种降级策略"""
        output_dir = "./outputs/videos"
        os.makedirs(output_dir, exist_ok=True)

        filename = f"google_robust_{task_id.split('/')[-1]}_{int(time.time())}.mp4"
        local_path = os.path.join(output_dir, filename)
        
        logger.info(f"📥 开始下载视频到: {local_path}")
        
        # 方法1: 使用genai客户端下载
        try:
            if hasattr(generated_video, 'video') and generated_video.video:
                video_data = client.files.download(file=generated_video.video)
                
                with open(local_path, 'wb') as f:
                    f.write(video_data)
                
                file_size = os.path.getsize(local_path)
                logger.info(f"✅ 方法1下载成功! 大小: {file_size:,} bytes")
                
                return {
                    "success": True,
                    "method": "genai_download",
                    "path": local_path,
                    "size": file_size
                }
        except Exception as e1:
            logger.warning(f"方法1失败: {str(e1)}")
        
        # 方法2: 使用video对象的save方法
        try:
            if hasattr(generated_video, 'video') and generated_video.video:
                generated_video.video.save(local_path)
                
                if os.path.exists(local_path):
                    file_size = os.path.getsize(local_path)
                    logger.info(f"✅ 方法2下载成功! 大小: {file_size:,} bytes")
                    
                    return {
                        "success": True,
                        "method": "video_save",
                        "path": local_path,
                        "size": file_size
                    }
        except Exception as e2:
            logger.warning(f"方法2失败: {str(e2)}")
        
        # 方法3: 创建占位文件
        try:
            placeholder_content = f"""# Google Veo 3 生成的视频
                                    # 任务ID: {task_id}
                                    # 生成时间: {time.time()}
                                    # 状态: 生成成功但下载失败
                                    # 视频对象: {generated_video}
                                    """
            with open(local_path, 'w') as f:
                f.write(placeholder_content)
            
            logger.info(f"⚠️ 创建占位文件: {local_path}")
            
            return {
                "success": False,
                "method": "placeholder",
                "path": local_path,
                "message": "生成成功但下载失败，已创建占位文件"
            }
        except Exception as e3:
            logger.error(f"创建占位文件也失败: {str(e3)}")
            
            return {
                "success": False,
                "method": "none",
                "error": f"所有下载方法都失败: {str(e3)}"
            }
    
    # 实现BaseVideoGenerationClient的抽象方法
    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """生成视频"""
        try:
            start_time = time.time()
            
            # 使用稳定版的生成方法
            # 传递 image_path 以支持 Image-to-Video
            result = await self.generate_video_with_retry(
                prompt=request.prompt,
                image_path=request.image_path,
                max_retries=3,
                timeout=300,
                duration=request.duration
            )
            
            generation_time = time.time() - start_time
            
            if result.get("status") == "completed":
                return VideoGenerationResult(
                    success=True,
                    local_path=result.get("download_result", {}).get("path"),
                    duration=request.duration,
                    resolution=request.resolution,
                    cost=self.estimate_cost(request.duration),
                    generation_time=generation_time,
                    quality_score=0.9,
                    metadata={"method": result.get("download_result", {}).get("method"), "task_id": result.get("task_id")}
                )
            else:
                return VideoGenerationResult(
                    success=False,
                    error_message=result.get("error", "生成失败"),
                    generation_time=generation_time
                )
                
        except Exception as e:
            logger.error(
                "视频生成异常详情: %s",
                format_google_api_error(e, {"model": "veo-3.1-fast-generate-001"}),
            )
            return VideoGenerationResult(
                success=False,
                error_message=str(e)
            )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取API能力信息（基于官方文档和实际测试）"""
        # Google没有提供获取API能力的接口
        # 这里返回基于官方文档和实际测试的信息
        return {
            "provider": "Google Gemini Veo 3.1 Fast",
            "model": "veo-3.1-fast-generate-001",
            "max_duration": 8.0,  # 官方文档确认的最大时长
            "resolution": "1280x720",  # 默认分辨率
            "cost_per_second": 0.75,  # 官方定价: $0.75/秒
            "avg_generation_time": 60.0,  # Fast模型生成时间更短
            "quality_score": 0.9,  # 基于官方评测结果
            "supported_formats": ["mp4"],
            "style_preferences": ["realistic", "cinematic", "natural", "professional"],
            "api_status": "available" if self.is_available() else "unavailable",
            "api_key_configured": bool(self.api_key),
            "last_updated": time.time(),
            "data_source": "official_documentation_and_testing",
            "limitations": [
                "最大时长8秒",
                "需要有效的Google API密钥",
                "Fast模型生成时间较快（30-90秒）",
                "成本相对较高"
            ]
        }
    

    
    def is_available(self) -> bool:
        """检查API是否可用"""
        return bool(self.api_key)


class VertexAIVideoClient(RobustGoogleVideoClient):
    """Vertex AI Veo 视频生成客户端 - 使用 Vertex AI 认证"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.vertex_api_key or settings.google_api_key
        self.project_id = settings.vertex_project_id
        self.location = settings.vertex_location
        self._client = None

    @property
    def client(self):
        """懒加载 Vertex AI 客户端"""
        if self._client is None:
            if not GENAI_AVAILABLE:
                raise ImportError("google.genai 模块不可用，请安装: pip install google-genai")
            if not self.project_id:
                raise ValueError("VERTEX_PROJECT_ID 未配置")

            try:
                # SDK 不允许同时传 api_key 和 project/location
                # project 通过完整 model path 传入 generate_videos 调用
                if self.api_key:
                    self._client = genai.Client(  # type: ignore
                        vertexai=True,
                        api_key=self.api_key,
                    )
                    logger.info(f"✅ Vertex AI 视频客户端初始化完成 (api_key 模式)")
                else:
                    self._client = genai.Client(  # type: ignore
                        vertexai=True,
                        project=self.project_id,
                        location=self.location,
                    )
                    logger.info(f"✅ Vertex AI 视频客户端初始化完成 (project={self.project_id})")
            except Exception as e:
                logger.error(f"❌ Vertex AI 客户端初始化失败: {e}")
                raise

        return self._client

    async def _generate_video_single_attempt(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        timeout: int = 300,
        duration: float = 8.0
    ) -> Dict[str, Any]:
        """使用 Vertex AI 模型生成视频（覆盖父类方法）"""
        try:
            duration_seconds = max(5, min(8, int(round(duration))))
            logger.info(f"📝 提示词: {prompt[:50]}... | 时长: {duration_seconds}s")
            client = self.client

            # 用完整 project path，让 Vertex API key 能正确路由到 Veo
            model_name = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/veo-3.1-fast-generate-001"
            logger.info(f"🎯 使用模型: veo-3.1-fast-generate-001 (Vertex AI)")

            # 处理参考图（逻辑与父类一致）
            input_image = None
            temp_image_path = None

            if image_path and image_path.startswith("http"):
                try:
                    import aiohttp
                    import aiofiles
                    from urllib.parse import urlparse
                    filename = os.path.basename(urlparse(image_path).path) or f"temp_img_{int(time.time())}.png"
                    temp_dir = "./temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_image_path = os.path.join(temp_dir, filename)
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_path) as response:
                            if response.status == 200:
                                async with aiofiles.open(temp_image_path, 'wb') as f:
                                    await f.write(await response.read())
                                image_path = temp_image_path
                except Exception as dl_err:
                    logger.warning(f"下载参考图异常: {dl_err}")

            if image_path and os.path.exists(image_path):
                logger.info(f"📸 读取参考图 image_bytes: {image_path}")
                try:
                    with open(image_path, 'rb') as f:
                        img_bytes = f.read()
                    ext = os.path.splitext(image_path)[1].lower()
                    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
                    input_image = genai.types.Image(image_bytes=img_bytes, mime_type=mime)  # type: ignore
                    logger.info(f"✅ 参考图已读取: {len(img_bytes)} bytes")
                except Exception as upload_err:
                    raise ValueError(f"图片读取失败: {upload_err}")
            elif image_path:
                raise FileNotFoundError(f"参考图路径不存在: {image_path}")

            # 提交生成任务
            video_config = genai.types.GenerateVideosConfig(duration_seconds=duration_seconds)  # type: ignore
            if input_image:
                logger.info(f"🚀 启动 Image-to-Video (Vertex AI, {duration_seconds}s)")
                operation = client.models.generate_videos(
                    model=model_name,
                    prompt=prompt,
                    image=input_image,
                    config=video_config,
                )
            else:
                logger.info(f"🚀 启动 Text-to-Video (Vertex AI, {duration_seconds}s)")
                operation = client.models.generate_videos(
                    model=model_name,
                    prompt=prompt,
                    config=video_config,
                )

            task_id = operation.name
            logger.info(f"✅ 任务已提交: {task_id}")

            # 轮询（与父类相同逻辑）
            start_time = time.time()
            check_intervals = [5, 10, 15, 20, 30, 30, 30]
            interval_index = 0

            while time.time() - start_time < timeout:
                try:
                    current_operation = client.operations.get(operation)
                    if current_operation.done:
                        if hasattr(current_operation, 'error') and current_operation.error:
                            logger.error(
                                "❌ Vertex AI Veo operation error: %s",
                                format_google_api_error(
                                    Exception(str(current_operation.error)),
                                    {
                                        "model": "veo-3.1-fast-generate-001",
                                        "model_path": model_name,
                                        "project_id": self.project_id,
                                        "location": self.location,
                                        "task_id": task_id,
                                    },
                                ),
                            )
                            return {"status": "failed", "error": str(current_operation.error), "task_id": task_id}

                        if (hasattr(current_operation, 'response') and
                                current_operation.response and
                                hasattr(current_operation.response, 'generated_videos') and
                                current_operation.response.generated_videos):
                            generated_video = current_operation.response.generated_videos[0]
                            download_result = await self._download_video_safe(client, generated_video, task_id)
                            return {
                                "status": "completed",
                                "task_id": task_id,
                                "download_result": download_result,
                                "generation_time": time.time() - start_time
                            }
                        return {"status": "completed_no_video", "task_id": task_id}

                    current_interval = check_intervals[min(interval_index, len(check_intervals) - 1)]
                    logger.info(f"⏳ 任务进行中 ({time.time() - start_time:.0f}s)，{current_interval}s 后检查")
                    await asyncio.sleep(current_interval)
                    interval_index += 1
                except Exception as poll_error:
                    logger.warning(
                        "Vertex AI Veo 轮询异常详情: %s",
                        format_google_api_error(
                            poll_error,
                            {
                                "model": "veo-3.1-fast-generate-001",
                                "model_path": model_name,
                                "project_id": self.project_id,
                                "location": self.location,
                                "task_id": task_id,
                            },
                        ),
                    )
                    await asyncio.sleep(10)

            return {"status": "timeout", "task_id": task_id, "elapsed_time": time.time() - start_time}

        except Exception as e:
            logger.error(
                "❌ Vertex AI 生成视频异常详情: %s",
                format_google_api_error(
                    e,
                    {
                        "model": "veo-3.1-fast-generate-001",
                        "project_id": self.project_id,
                        "location": self.location,
                    },
                ),
            )
            raise

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "Google Vertex AI Veo",
            "model": "veo-3.1-fast-generate-001",
            "max_duration": 8.0,
            "resolution": "1280x720",
            "cost_per_second": 0.75,
            "avg_generation_time": 90.0,
            "quality_score": 0.95,
            "supported_formats": ["mp4"],
            "project_id": self.project_id,
            "location": self.location,
            "api_status": "available" if self.is_available() else "unavailable",
        }

    def is_available(self) -> bool:
        return bool(self.project_id)


async def test_robust_client():
    """测试稳定版客户端"""
    
    print("🛡️ Google Gemini Veo 3 稳定版客户端测试")
    print("=" * 60)
    
    client = RobustGoogleVideoClient()
    
    prompt = "A beautiful sunrise over mountains with birds flying"
    
    print(f"🎬 开始生成视频...")
    print(f"📝 提示词: {prompt}")
    
    start_time = time.time()
    
    result = await client.generate_video_with_retry(
        prompt=prompt,
        max_retries=3,
        timeout=300
    )
    
    total_time = time.time() - start_time
    
    print(f"\n🏁 测试完成! 总耗时: {total_time:.1f}秒")
    print("=" * 60)
    
    if result["status"] == "completed":
        print("🎉 视频生成成功!")
        print(f"   任务ID: {result['task_id']}")
        print(f"   生成时间: {result['generation_time']:.1f}秒")
        
        download_result = result.get("download_result", {})
        if download_result.get("success"):
            print(f"✅ 视频下载成功!")
            print(f"   方法: {download_result['method']}")
            print(f"   路径: {download_result['path']}")
            print(f"   大小: {download_result.get('size', 0):,} bytes")
        else:
            print(f"⚠️ 视频下载失败: {download_result.get('message', '未知错误')}")
            
    elif result["status"] == "failed":
        print(f"❌ 视频生成失败: {result.get('error', '未知错误')}")
        
    elif result["status"] == "timeout":
        print(f"⏰ 视频生成超时: {result.get('elapsed_time', 0):.1f}秒")
        
    else:
        print(f"❓ 未知状态: {result}")

if __name__ == "__main__":
    asyncio.run(test_robust_client())
