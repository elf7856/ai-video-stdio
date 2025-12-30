import os
import tempfile
import asyncio
import aiohttp
import re
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, parse_qs
import yt_dlp
from pytube import YouTube
from app.core.config import settings

class VideoDownloader:
    """视频下载器"""
    
    def __init__(self):
        self.supported_platforms = {
            'youtube': self._download_youtube,
            'bilibili': self._download_bilibili,
            'tiktok': self._download_tiktok,
            'instagram': self._download_instagram,
            'twitter': self._download_twitter,
            'general': self._download_general
        }
    
    async def download_video(self, url: str, output_dir: str = None, cookies_file: str = None) -> Dict:
        """下载视频"""
        try:
            # 识别平台
            platform = self._identify_platform(url)
            
            # 设置输出目录
            if output_dir is None:
                output_dir = settings.upload_dir
            
            os.makedirs(output_dir, exist_ok=True)
            
            # 下载视频
            if platform in self.supported_platforms:
                result = await self.supported_platforms[platform](url, output_dir, cookies_file)
                return result
            else:
                # 尝试通用下载
                return await self._download_general(url, output_dir, cookies_file)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"下载失败: {str(e)}",
                "file_path": None
            }
    
    def _identify_platform(self, url: str) -> str:
        """识别视频平台"""
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'bilibili.com' in url_lower or 'b23.tv' in url_lower:
            return 'bilibili'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        else:
            return 'general'
    
    async def _download_youtube(self, url: str, output_dir: str, cookies_file: str = None) -> Dict:
        """下载YouTube视频"""
        try:
            # 使用yt-dlp下载
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'cookies': cookies_file
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown_title')
                
                # 下载视频
                ydl.download([url])
                
                # 查找下载的文件
                downloaded_file = None
                for file in os.listdir(output_dir):
                    if title.lower().replace(' ', '_') in file.lower() or 'unknown_title' in file:
                        downloaded_file = os.path.join(output_dir, file)
                        break
                
                if downloaded_file and os.path.exists(downloaded_file):
                    return {
                        "success": True,
                        "file_path": downloaded_file,
                        "title": title,
                        "duration": info.get('duration'),
                        "platform": "youtube"
                    }
                else:
                    return {
                        "success": False,
                        "error": "下载完成但找不到文件",
                        "file_path": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"YouTube下载失败: {str(e)}",
                "file_path": None
            }
    
    async def _download_bilibili(self, url: str, output_dir: str, cookies_file: str = None) -> Dict:
        """下载B站视频"""
        try:
            # 使用yt-dlp下载B站视频
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'best',  # 改为best，不限制格式
                'quiet': True,
                'no_warnings': True,
                'cookies': cookies_file
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown_title')
                
                ydl.download([url])
                
                # 查找下载的文件
                downloaded_file = None
                for file in os.listdir(output_dir):
                    if title.lower().replace(' ', '_') in file.lower() or 'unknown_title' in file:
                        downloaded_file = os.path.join(output_dir, file)
                        break
                
                if downloaded_file and os.path.exists(downloaded_file):
                    return {
                        "success": True,
                        "file_path": downloaded_file,
                        "title": title,
                        "duration": info.get('duration'),
                        "platform": "bilibili"
                    }
                else:
                    return {
                        "success": False,
                        "error": "下载完成但找不到文件",
                        "file_path": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"B站下载失败: {str(e)}",
                "file_path": None
            }
    
    async def _download_tiktok(self, url: str, output_dir: str, cookies_file: str = None) -> Dict:
        """下载TikTok视频"""
        try:
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'cookies': cookies_file
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown_title')
                
                ydl.download([url])
                
                # 查找下载的文件
                downloaded_file = None
                for file in os.listdir(output_dir):
                    if title.lower().replace(' ', '_') in file.lower() or 'unknown_title' in file:
                        downloaded_file = os.path.join(output_dir, file)
                        break
                
                if downloaded_file and os.path.exists(downloaded_file):
                    return {
                        "success": True,
                        "file_path": downloaded_file,
                        "title": title,
                        "duration": info.get('duration'),
                        "platform": "tiktok"
                    }
                else:
                    return {
                        "success": False,
                        "error": "下载完成但找不到文件",
                        "file_path": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"TikTok下载失败: {str(e)}",
                "file_path": None
            }
    
    async def _download_instagram(self, url: str, output_dir: str, cookies_file: str = None) -> Dict:
        """下载Instagram视频"""
        try:
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'cookies': cookies_file
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown_title')
                
                ydl.download([url])
                
                # 查找下载的文件
                downloaded_file = None
                for file in os.listdir(output_dir):
                    if title.lower().replace(' ', '_') in file.lower() or 'unknown_title' in file:
                        downloaded_file = os.path.join(output_dir, file)
                        break
                
                if downloaded_file and os.path.exists(downloaded_file):
                    return {
                        "success": True,
                        "file_path": downloaded_file,
                        "title": title,
                        "duration": info.get('duration'),
                        "platform": "instagram"
                    }
                else:
                    return {
                        "success": False,
                        "error": "下载完成但找不到文件",
                        "file_path": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Instagram下载失败: {str(e)}",
                "file_path": None
            }
    
    async def _download_twitter(self, url: str, output_dir: str, cookies_file: str = None) -> Dict:
        """下载Twitter视频"""
        try:
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'cookies': cookies_file
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown_title')
                
                ydl.download([url])
                
                # 查找下载的文件
                downloaded_file = None
                for file in os.listdir(output_dir):
                    if title.lower().replace(' ', '_') in file.lower() or 'unknown_title' in file:
                        downloaded_file = os.path.join(output_dir, file)
                        break
                
                if downloaded_file and os.path.exists(downloaded_file):
                    return {
                        "success": True,
                        "file_path": downloaded_file,
                        "title": title,
                        "duration": info.get('duration'),
                        "platform": "twitter"
                    }
                else:
                    return {
                        "success": False,
                        "error": "下载完成但找不到文件",
                        "file_path": None
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Twitter下载失败: {str(e)}",
                "file_path": None
            }
    
    async def _download_general(self, url: str, output_dir: str, cookies_file: str = None) -> Dict:
        """通用视频下载"""
        try:
            # 尝试使用yt-dlp下载
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'cookies': cookies_file
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown_title')
                
                ydl.download([url])
                
                # 查找下载的文件
                downloaded_file = None
                for file in os.listdir(output_dir):
                    if title.lower().replace(' ', '_') in file.lower() or 'unknown_title' in file:
                        downloaded_file = os.path.join(output_dir, file)
                        break
                
                if downloaded_file and os.path.exists(downloaded_file):
                    return {
                        "success": True,
                        "file_path": downloaded_file,
                        "title": title,
                        "duration": info.get('duration'),
                        "platform": "general"
                    }
                else:
                    return {
                        "success": False,
                        "error": "下载完成但找不到文件",
                        "file_path": None
                    }
                    
        except Exception as e:
            # 如果yt-dlp失败，尝试直接HTTP下载
            return await self._download_direct_http(url, output_dir, cookies_file)
    
    async def _download_direct_http(self, url: str, output_dir: str, cookies_file: str = None) -> Dict:
        """直接HTTP下载"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # 从URL或响应头获取文件名
                        filename = self._get_filename_from_url(url, response)
                        file_path = os.path.join(output_dir, filename)
                        
                        with open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        return {
                            "success": True,
                            "file_path": file_path,
                            "title": filename,
                            "duration": None,
                            "platform": "http"
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP下载失败: {response.status}",
                            "file_path": None
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": f"直接下载失败: {str(e)}",
                "file_path": None
            }
    
    def _get_filename_from_url(self, url: str, response: aiohttp.ClientResponse) -> str:
        """从URL或响应头获取文件名"""
        # 尝试从Content-Disposition头获取文件名
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename:
                return filename.group(1)
        
        # 从URL路径获取文件名
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and '/' in path:
            filename = path.split('/')[-1]
            if filename and '.' in filename:
                return filename
        
        # 从Content-Type推断扩展名
        content_type = response.headers.get('Content-Type', '')
        if 'video/mp4' in content_type:
            return f"video_{int(asyncio.get_event_loop().time())}.mp4"
        elif 'video/webm' in content_type:
            return f"video_{int(asyncio.get_event_loop().time())}.webm"
        else:
            return f"video_{int(asyncio.get_event_loop().time())}.mp4"
    
    async def get_video_info(self, url: str) -> Dict:
        """获取视频信息（不下载）"""
        try:
            platform = self._identify_platform(url)
            
            if platform in self.supported_platforms:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    return {
                        "success": True,
                        "title": info.get('title', 'Unknown'),
                        "duration": info.get('duration'),
                        "description": info.get('description', ''),
                        "uploader": info.get('uploader', ''),
                        "view_count": info.get('view_count'),
                        "platform": platform,
                        "thumbnail": info.get('thumbnail'),
                        "formats": [f.get('format_id') for f in info.get('formats', [])]
                    }
            else:
                return {
                    "success": False,
                    "error": f"不支持的平台: {platform}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"获取视频信息失败: {str(e)}"
            }

async def test_downloader():
    """测试视频下载器"""
    print("🚀 视频下载器测试")
    print("=" * 50)
    
    downloader = VideoDownloader()
    
    # 测试URL列表
    test_urls = [
        # YouTube测试（需要替换为实际可用的URL）
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        
        # B站测试（需要替换为实际可用的URL）
        "https://www.bilibili.com/video/BV1xx411c7mu",
        
        # 通用HTTP视频测试
        "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📹 测试 {i}: {url}")
        print("-" * 30)
        
        # 1. 识别平台
        platform = downloader._identify_platform(url)
        print(f"识别平台: {platform}")
        
        # 2. 获取视频信息（不下载）
        print("获取视频信息...")
        info_result = await downloader.get_video_info(url)
        
        if info_result["success"]:
            print(f"✅ 信息获取成功:")
            print(f"   标题: {info_result.get('title', 'N/A')}")
            print(f"   时长: {info_result.get('duration', 'N/A')}秒")
            print(f"   平台: {info_result.get('platform', 'N/A')}")
            print(f"   上传者: {info_result.get('uploader', 'N/A')}")
        else:
            print(f"❌ 信息获取失败: {info_result.get('error', 'Unknown error')}")
        
        # 3. 询问是否下载
        print("\n是否下载此视频？(y/n): ", end="")
        try:
            # 允许用户选择是否下载
            download_choice = input().lower()
        except KeyboardInterrupt:
            print("\n测试被用户中断")
            break
        
        if download_choice == 'y':
            print("开始下载...")
            download_result = await downloader.download_video(url)
            
            if download_result["success"]:
                print(f"✅ 下载成功:")
                print(f"   文件路径: {download_result['file_path']}")
                print(f"   标题: {download_result.get('title', 'N/A')}")
                print(f"   时长: {download_result.get('duration', 'N/A')}秒")
                print(f"   平台: {download_result.get('platform', 'N/A')}")
            else:
                print(f"❌ 下载失败: {download_result.get('error', 'Unknown error')}")
        else:
            print("跳过下载")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("\n💡 提示:")
    print("1. 请确保已安装 yt-dlp: pip install yt-dlp")
    print("2. 某些平台可能需要特殊配置或代理")
    print("3. 下载大文件时请确保有足够的磁盘空间")
    print("4. 请遵守各平台的使用条款")

def test_platform_identification():
    """测试平台识别功能"""
    print("\n🔍 平台识别测试")
    print("-" * 30)
    
    downloader = VideoDownloader()
    
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://www.bilibili.com/video/BV1xx411c7mu", "bilibili"),
        ("https://b23.tv/xxx", "bilibili"),
        ("https://www.tiktok.com/@user/video/123", "tiktok"),
        ("https://www.instagram.com/p/xxx/", "instagram"),
        ("https://twitter.com/user/status/123", "twitter"),
        ("https://x.com/user/status/123", "twitter"),
        ("https://example.com/video.mp4", "general")
    ]
    
    for url, expected in test_cases:
        result = downloader._identify_platform(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url} -> {result} (期望: {expected})")

if __name__ == "__main__":
    import asyncio
    
    print("🎬 Video Downloader 测试程序")
    print("=" * 60)
    
    # 运行平台识别测试
    test_platform_identification()
    
    # 运行下载器测试
    print("\n" + "=" * 60)
    asyncio.run(test_downloader()) 