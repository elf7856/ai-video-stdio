import os
import shutil
import logging
from abc import ABC, abstractmethod
from typing import Optional, Union
from pathlib import Path
from datetime import datetime
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)

class BaseStorage(ABC):
    """存储服务抽象基类"""

    @abstractmethod
    def save(self, file_path_or_content: Union[str, bytes], object_name: str) -> str:
        """
        保存文件
        :param file_path_or_content: 本地文件路径 或 二进制内容
        :param object_name: 目标对象名称 (例如: videos/demo.mp4)
        :return: 文件的访问URL
        """
        pass

    @abstractmethod
    def get_url(self, object_name: str) -> str:
        """获取文件访问URL"""
        pass

    @abstractmethod
    def exists(self, object_name: str) -> bool:
        """检查文件是否存在"""
        pass


class LocalStorage(BaseStorage):
    """本地存储实现 (用于开发/测试)"""

    def __init__(self, base_dir: str = "outputs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # 确保子目录存在
        (self.base_dir / "videos").mkdir(exist_ok=True)
        (self.base_dir / "images").mkdir(exist_ok=True)
        (self.base_dir / "audio").mkdir(exist_ok=True)

    def save(self, file_path_or_content: Union[str, bytes], object_name: str) -> str:
        # 移除 object_name 开头的 /
        if object_name.startswith("/"):
            object_name = object_name[1:]
            
        target_path = self.base_dir / object_name
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if isinstance(file_path_or_content, str):
                # 如果是路径，进行复制
                src_path = Path(file_path_or_content)
                if not src_path.exists():
                    raise FileNotFoundError(f"Source file not found: {src_path}")
                
                # 【新增】防碰撞检查：如果源路径和目标路径相同，跳过复制
                if src_path.resolve() == target_path.resolve():
                    logger.debug(f"Source and target are the same, skipping copy: {src_path}")
                else:
                    shutil.copy2(src_path, target_path)
            else:
                # 如果是二进制，直接写入
                with open(target_path, "wb") as f:
                    f.write(file_path_or_content)
            
            return self.get_url(object_name)
        except Exception as e:
            logger.error(f"Local storage save failed: {e}")
            raise

    def get_url(self, object_name: str) -> str:
        # 移除 object_name 开头的 /
        if object_name.startswith("/"):
            object_name = object_name[1:]
        
        # 返回相对路径，由前端决定基准域名
        return f"/outputs/{object_name}"

    def exists(self, object_name: str) -> bool:
        return (self.base_dir / object_name).exists()


class OSSStorage(BaseStorage):
    """
    OSS/S3 对象存储实现 (用于生产环境)
    支持 AWS S3, Aliyun OSS, MinIO 等兼容 S3 协议的服务
    """

    def __init__(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            logger.error("boto3 not installed. Please run 'pip install boto3'")
            raise

        self.bucket_name = settings.oss_bucket_name
        self.cdn_domain = settings.cdn_domain
        self.endpoint = settings.oss_endpoint
        
        if not all([settings.oss_access_key_id, settings.oss_access_key_secret, self.bucket_name]):
            logger.warning("OSS credentials not fully configured!")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.oss_access_key_id,
            aws_secret_access_key=settings.oss_access_key_secret,
            endpoint_url=f"https://{self.endpoint}" if self.endpoint else None,
            region_name=settings.oss_region,
            config=Config(s3={'addressing_style': 'virtual'})
        )

    def save(self, file_path_or_content: Union[str, bytes], object_name: str) -> str:
        if object_name.startswith("/"):
            object_name = object_name[1:]

        try:
            extra_args = {'ACL': 'public-read'} # 默认设为公开读
            
            # 根据后缀设置 Content-Type
            content_type = self._guess_content_type(object_name)
            if content_type:
                extra_args['ContentType'] = content_type

            if isinstance(file_path_or_content, str):
                self.s3_client.upload_file(
                    file_path_or_content, 
                    self.bucket_name, 
                    object_name,
                    ExtraArgs=extra_args
                )
            else:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file_path_or_content,
                    **extra_args
                )
            
            return self.get_url(object_name)
        except Exception as e:
            logger.error(f"OSS upload failed: {e}")
            raise

    def get_url(self, object_name: str) -> str:
        if object_name.startswith("/"):
            object_name = object_name[1:]
            
        if self.cdn_domain:
            # 去除CDN域名末尾的 /
            domain = self.cdn_domain.rstrip("/")
            return f"{domain}/{object_name}"
        
        # 默认 S3/OSS URL
        if self.endpoint:
            return f"https://{self.bucket_name}.{self.endpoint}/{object_name}"
        return f"https://{self.bucket_name}.s3.amazonaws.com/{object_name}"

    def exists(self, object_name: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except:
            return False

    def _guess_content_type(self, filename: str) -> Optional[str]:
        import mimetypes
        return mimetypes.guess_type(filename)[0]


# 工厂模式
def get_storage_service() -> BaseStorage:
    if settings.storage_type.lower() == "oss":
        return OSSStorage()
    return LocalStorage()
