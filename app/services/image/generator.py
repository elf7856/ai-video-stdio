import os
import tempfile
import asyncio
import aiohttp
import base64
from typing import Dict, Optional, Tuple, List, Union
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from app.core.config import settings
from app.prompts.base import render_prompt
import litellm
import json
import time
from abc import ABC, abstractmethod
from app.services.llm.analyzer import LLMService

class ImageGeneratorBase(ABC):
    """图像生成器基类"""
    
    @abstractmethod
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, **kwargs) -> str:
        """生成图像"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass

class DalleGenerator(ImageGeneratorBase):
    """DALL-E图像生成器"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.dalle_model
        self.quality = settings.dalle_quality
        self.style = settings.dalle_style
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, **kwargs) -> str:
        """使用DALL-E生成图像"""
        if not self.is_available():
            raise Exception("DALL-E API密钥未配置")
        
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            # DALL-E 3只支持特定尺寸
            if size:
                if size[0] == size[1]:  # 正方形
                    size_str = "1024x1024"
                elif size[0] > size[1]:  # 横向
                    size_str = "1792x1024"
                else:  # 纵向
                    size_str = "1024x1792"
            else:
                size_str = "1024x1024"
            
            response = await client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size_str,
                quality=self.quality,
                style=self.style,
                n=1
            )
            
            # 下载图像
            image_url = response.data[0].url
            output_path = tempfile.mktemp(suffix='.png')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        with open(output_path, 'wb') as f:
                            f.write(await resp.read())
                        return output_path
                    else:
                        raise Exception(f"图像下载失败: {resp.status}")
                        
        except Exception as e:
            raise Exception(f"DALL-E生成失败: {str(e)}")

class StabilityGenerator(ImageGeneratorBase):
    """Stability AI图像生成器"""
    
    def __init__(self):
        self.api_key = settings.stability_api_key
        self.engine = settings.stability_engine
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, **kwargs) -> str:
        """使用Stability AI生成图像"""
        if not self.is_available():
            raise Exception("Stability AI API密钥未配置")
        
        try:
            import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
            from stability_sdk import client
            
            stability_api = client.StabilityInference(
                key=self.api_key,
                verbose=True,
            )
            
            # 设置默认参数
            size = size or settings.image_size
            negative_prompt = negative_prompt or "blurry, low quality, distorted"
            
            answers = stability_api.generate(
                prompt=prompt,
                seed=kwargs.get('seed', 0),
                steps=kwargs.get('steps', 30),
                cfg_scale=kwargs.get('cfg_scale', 7.0),
                width=size[0],
                height=size[1],
                samples=1,
                sampler=generation.SAMPLER_K_DPMPP_2M
            )
            
            output_path = tempfile.mktemp(suffix='.png')
            
            for resp in answers:
                for artifact in resp.artifacts:
                    if artifact.finish_reason == generation.FILTER:
                        raise Exception("内容被过滤")
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        with open(output_path, 'wb') as f:
                            f.write(artifact.binary)
                        return output_path
            
            raise Exception("未生成有效图像")
            
        except Exception as e:
            raise Exception(f"Stability AI生成失败: {str(e)}")

class ReplicateGenerator(ImageGeneratorBase):
    """Replicate图像生成器"""
    
    def __init__(self):
        self.api_key = settings.replicate_api_key
        self.model = settings.replicate_model
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, **kwargs) -> str:
        """使用Replicate生成图像"""
        if not self.is_available():
            raise Exception("Replicate API密钥未配置")
        
        try:
            import replicate
            
            # 设置默认参数
            size = size or settings.image_size
            negative_prompt = negative_prompt or "blurry, low quality, distorted"
            
            output = await asyncio.to_thread(
                replicate.run,
                self.model,
                input={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": size[0],
                    "height": size[1],
                    "num_inference_steps": kwargs.get('steps', 20),
                    "guidance_scale": kwargs.get('guidance_scale', 7.5),
                    "seed": kwargs.get('seed', None)
                }
            )
            
            if output and len(output) > 0:
                image_url = output[0]
                output_path = tempfile.mktemp(suffix='.png')
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            with open(output_path, 'wb') as f:
                                f.write(await resp.read())
                            return output_path
                        else:
                            raise Exception(f"图像下载失败: {resp.status}")
            else:
                raise Exception("未生成有效图像")
                
        except Exception as e:
            raise Exception(f"Replicate生成失败: {str(e)}")

class LeonardoGenerator(ImageGeneratorBase):
    """Leonardo AI图像生成器"""
    
    def __init__(self):
        self.api_key = settings.leonardo_api_key
        self.model = settings.leonardo_model
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, **kwargs) -> str:
        """使用Leonardo AI生成图像"""
        if not self.is_available():
            raise Exception("Leonardo AI API密钥未配置")
        
        try:
            # 设置默认参数
            size = size or settings.image_size
            negative_prompt = negative_prompt or "blurry, low quality, distorted"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "prompt": prompt,
                "modelId": self.model,
                "width": size[0],
                "height": size[1],
                "num_images": 1,
                "negative_prompt": negative_prompt,
                "promptMagic": kwargs.get('prompt_magic', True),
                "photoReal": kwargs.get('photo_real', False),
                "guidanceScale": kwargs.get('guidance_scale', 7),
                "initStrength": kwargs.get('init_strength', 0.4),
                "initImageUrl": kwargs.get('init_image_url', None),
                "public": False
            }
            
            # 创建生成任务
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://cloud.leonardo.ai/api/rest/v1/generations",
                    headers=headers,
                    json=data
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"创建生成任务失败: {resp.status}")
                    
                    result = await resp.json()
                    generation_id = result['sdGenerationJob']['generationId']
            
            # 等待生成完成
            max_wait = 300  # 5分钟
            wait_time = 0
            while wait_time < max_wait:
                await asyncio.sleep(10)
                wait_time += 10
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            if result['generations_by_pk']['status'] == 'COMPLETE':
                                image_url = result['generations_by_pk']['generated_images'][0]['url']
                                break
                        elif wait_time >= max_wait:
                            raise Exception("生成超时")
            
            # 下载图像
            output_path = tempfile.mktemp(suffix='.png')
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        with open(output_path, 'wb') as f:
                            f.write(await resp.read())
                        return output_path
                    else:
                        raise Exception(f"图像下载失败: {resp.status}")
                        
        except Exception as e:
            raise Exception(f"Leonardo AI生成失败: {str(e)}")

class MidjourneyGenerator(ImageGeneratorBase):
    """Midjourney图像生成器（通过Discord API）"""
    
    def __init__(self, channel_id: str = None):
        self.api_key = settings.midjourney_api_key
        self.channel_id = channel_id
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.channel_id)
    
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, **kwargs) -> str:
        """使用Midjourney生成图像"""
        if not self.is_available():
            raise Exception("Midjourney API密钥或频道ID未配置")
        
        try:
            headers = {
                "Authorization": f"Bot {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送生成命令
            data = {
                "content": f"/imagine {prompt}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://discord.com/api/v10/channels/{self.channel_id}/messages",
                    headers=headers,
                    json=data
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"发送Midjourney命令失败: {resp.status}")
                    
                    result = await resp.json()
                    message_id = result['id']
            
            # 等待生成完成（这里需要实现轮询逻辑）
            # 由于Midjourney的复杂性，这里只是示例框架
            raise Exception("Midjourney集成需要更复杂的实现")
            
        except Exception as e:
            raise Exception(f"Midjourney生成失败: {str(e)}")

class LocalGenerator(ImageGeneratorBase):
    """本地Stable Diffusion生成器"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.default_image_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self._load_model()
    
    def _load_model(self):
        """加载图像生成模型"""
        try:
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                safety_checker=None
            )
            
            # 使用更快的调度器
            self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipeline.scheduler.config
            )
            
            if self.device == "cuda":
                self.pipeline = self.pipeline.to(self.device)
                self.pipeline.enable_attention_slicing()
            
        except Exception as e:
            print(f"模型加载失败: {str(e)}")
            self.pipeline = None
    
    def is_available(self) -> bool:
        return self.pipeline is not None
    
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, **kwargs) -> str:
        """使用本地模型生成图像"""
        if not self.is_available():
            raise Exception("本地模型未加载")
        
        try:
            # 设置默认参数
            size = size or settings.image_size
            negative_prompt = negative_prompt or "low quality, blurry, distorted"
            
            # 生成图像
            image = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                height=size[1],
                width=size[0],
                num_inference_steps=kwargs.get('steps', 20),
                guidance_scale=kwargs.get('guidance_scale', 7.5)
            ).images[0]
            
            # 保存图像
            output_path = tempfile.mktemp(suffix='.png')
            image.save(output_path)
            return output_path
            
        except Exception as e:
            raise Exception(f"本地生成失败: {str(e)}")

class ImageGenerator:
    """统一的图像生成器"""
    
    def __init__(self, provider: str = None):
        self.provider = provider or settings.default_image_provider
        self.llm_service = LLMService()
        self.generators = {
            'dalle': DalleGenerator(),
            'stability': StabilityGenerator(),
            'replicate': ReplicateGenerator(),
            'leonardo': LeonardoGenerator(),
            'midjourney': MidjourneyGenerator(),
            'local': LocalGenerator()
        }
        self.current_generator = self.generators.get(self.provider)
        
        if not self.current_generator or not self.current_generator.is_available():
            # 尝试其他可用的生成器
            for name, generator in self.generators.items():
                if generator.is_available():
                    self.provider = name
                    self.current_generator = generator
                    break
    
    async def generate_image_description(self, content_requirement: str, 
                                       style_requirement: str = "realistic",
                                       scene_description: str = "",
                                       emotion: str = "neutral",
                                       technical_specs: str = "high quality") -> str:
        """使用LLM生成详细的图像描述"""
        try:
            prompt = render_prompt("image_description_generation",
                                 content_requirement=content_requirement,
                                 style_requirement=style_requirement,
                                 scene_description=scene_description,
                                 emotion=emotion,
                                 technical_specs=technical_specs)
            
            messages = [
                {"role": "system", "content": render_prompt("image_description_expert_role")},
                {"role": "user", "content": prompt}
            ]
            
            content = await self.llm_service.complete(messages, task_type="generation")
            return content.strip()
            
        except Exception as e:
            print(f"图像描述生成失败: {str(e)}")
            return content_requirement
    
    async def generate_image(self, prompt: str, negative_prompt: str = None,
                           size: Tuple[int, int] = None, provider: str = None,
                           **kwargs) -> str:
        """生成图像"""
        if provider and provider != self.provider:
            generator = self.generators.get(provider)
            if not generator or not generator.is_available():
                raise Exception(f"指定的生成器 {provider} 不可用")
        else:
            generator = self.current_generator
        
        if not generator:
            raise Exception("没有可用的图像生成器")
        
        try:
            return await generator.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                size=size,
                **kwargs
            )
        except Exception as e:
            # 如果当前生成器失败，尝试其他可用的生成器
            for name, alt_generator in self.generators.items():
                if name != self.provider and alt_generator.is_available():
                    try:
                        return await alt_generator.generate_image(
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            size=size,
                            **kwargs
                        )
                    except:
                        continue
            
            raise e
    
    async def generate_image_with_description(self, content_requirement: str,
                                            style: str = "realistic", **kwargs) -> str:
        """基于内容需求生成图像描述并生成图像"""
        # 首先生成详细的图像描述
        description = await self.generate_image_description(
            content_requirement=content_requirement,
            style_requirement=style
        )
        
        # 应用风格预设
        styled_description = self.apply_style_preset(description, style)
        
        # 生成图像
        return await self.generate_image(styled_description, **kwargs)
    
    async def generate_image_batch(self, prompts: list, **kwargs) -> list:
        """批量生成图像"""
        tasks = []
        for prompt in prompts:
            task = self.generate_image(prompt, **kwargs)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def apply_style_preset(self, prompt: str, style: str) -> str:
        """应用风格预设"""
        style_prompts = {
            "realistic": f"{prompt}, highly detailed, photorealistic, 8k resolution",
            "anime": f"{prompt}, anime style, vibrant colors, detailed illustration",
            "cartoon": f"{prompt}, cartoon style, simple colors, clean lines",
            "oil_painting": f"{prompt}, oil painting style, artistic, textured",
            "watercolor": f"{prompt}, watercolor painting, soft colors, flowing",
            "cyberpunk": f"{prompt}, cyberpunk style, neon lights, futuristic",
            "vintage": f"{prompt}, vintage style, retro colors, old fashioned",
            "minimalist": f"{prompt}, minimalist style, simple, clean, geometric"
        }
        
        return style_prompts.get(style, prompt)
    
    async def generate_with_style(self, prompt: str, style: str, **kwargs) -> str:
        """使用指定风格生成图像"""
        styled_prompt = self.apply_style_preset(prompt, style)
        return await self.generate_image(styled_prompt, **kwargs)
    
    def get_available_providers(self) -> List[str]:
        """获取可用的生成器列表"""
        return [name for name, generator in self.generators.items() 
                if generator.is_available()]
    
    def get_provider_info(self) -> Dict[str, Dict]:
        """获取所有生成器的信息"""
        info = {}
        for name, generator in self.generators.items():
            info[name] = {
                'available': generator.is_available(),
                'current': name == self.provider
            }
        return info

# 保持原有的ImageEditor和ImageServiceManager类
class ImageEditor:
    """图像编辑工具"""
    
    @staticmethod
    def resize_image(image_path: str, target_size: Tuple[int, int], 
                    output_path: str = None) -> str:
        """调整图像尺寸"""
        try:
            with Image.open(image_path) as img:
                resized = img.resize(target_size, Image.Resampling.LANCZOS)
                
                if output_path is None:
                    output_path = tempfile.mktemp(suffix='.png')
                
                resized.save(output_path)
                return output_path
                
        except Exception as e:
            print(f"图像调整失败: {str(e)}")
            return None
    
    @staticmethod
    def apply_filter(image_path: str, filter_type: str, 
                    output_path: str = None) -> str:
        """应用滤镜效果"""
        try:
            with Image.open(image_path) as img:
                if filter_type == "grayscale":
                    filtered = img.convert('L').convert('RGB')
                elif filter_type == "sepia":
                    # 简单的棕褐色滤镜
                    filtered = img.convert('RGB')
                    data = filtered.getdata()
                    new_data = []
                    for item in data:
                        r, g, b = item
                        new_r = int(0.393 * r + 0.769 * g + 0.189 * b)
                        new_g = int(0.349 * r + 0.686 * g + 0.168 * b)
                        new_b = int(0.272 * r + 0.534 * g + 0.131 * b)
                        new_data.append((min(255, new_r), min(255, new_g), min(255, new_b)))
                    filtered.putdata(new_data)
                else:
                    filtered = img
                
                if output_path is None:
                    output_path = tempfile.mktemp(suffix='.png')
                
                filtered.save(output_path)
                return output_path
                
        except Exception as e:
            print(f"滤镜应用失败: {str(e)}")
            return None
    
    @staticmethod
    def add_text_overlay(image_path: str, text: str, position: str = "bottom",
                        font_size: int = 40, color: str = "white",
                        output_path: str = None) -> str:
        """添加文字覆盖"""
        try:
            from PIL import ImageDraw, ImageFont
            
            with Image.open(image_path) as img:
                draw = ImageDraw.Draw(img)
                
                # 尝试加载字体，如果失败则使用默认字体
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # 计算文字位置
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                img_width, img_height = img.size
                
                if position == "top":
                    x = (img_width - text_width) // 2
                    y = 10
                elif position == "bottom":
                    x = (img_width - text_width) // 2
                    y = img_height - text_height - 10
                elif position == "center":
                    x = (img_width - text_width) // 2
                    y = (img_height - text_height) // 2
                else:
                    x, y = 10, 10
                
                # 绘制文字
                draw.text((x, y), text, fill=color, font=font)
                
                if output_path is None:
                    output_path = tempfile.mktemp(suffix='.png')
                
                img.save(output_path)
                return output_path
                
        except Exception as e:
            print(f"文字覆盖失败: {str(e)}")
            return None

class ImageServiceManager:
    """图像服务管理器"""
    
    def __init__(self):
        self.generator = ImageGenerator()
        self.editor = ImageEditor()
    
    async def generate_image(self, prompt: str, style: str = None, 
                           provider: str = None, **kwargs) -> str:
        """生成图像"""
        if style:
            return await self.generator.generate_with_style(prompt, style, provider=provider, **kwargs)
        else:
            return await self.generator.generate_image(prompt, provider=provider, **kwargs)
    
    def edit_image(self, image_path: str, operation: str, **kwargs) -> str:
        """编辑图像"""
        if operation == "resize":
            return self.editor.resize_image(image_path, **kwargs)
        elif operation == "filter":
            return self.editor.apply_filter(image_path, **kwargs)
        elif operation == "text":
            return self.editor.add_text_overlay(image_path, **kwargs)
        else:
            return None
    
    def get_available_providers(self) -> List[str]:
        """获取可用的图像生成器"""
        return self.generator.get_available_providers()
    
    def get_provider_info(self) -> Dict[str, Dict]:
        """获取生成器信息"""
        return self.generator.get_provider_info() 