import os
import tempfile
import asyncio
import aiohttp
import re
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, parse_qs
import yt_dlp
from app.core.config import settings

class VideoDownloader:
    """视频下载器"""
    
    def __init__(self):
        youtube_extra_opts = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'sleep_interval': 1,
            'max_sleep_interval': 3,
            'sleep_interval_subtitles': 1,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'socket_timeout': 30,
            'http_chunk_size': 10485760,
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],
                    'player_skip': ['js'],
                }
            }
        }
        self.platform_download_configs = {
            'youtube': {
                'fmt': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
                'extra_opts': youtube_extra_opts,
            },
            'bilibili': {'fmt': 'best'},
            'tiktok': {},
            'instagram': {},
            'twitter': {},
            'general': {'fallback_to_http': True},
        }
        self.supported_platforms = set(self.platform_download_configs.keys())
    
    async def download_video(self, url: str, output_dir: str = None, cookies_file: str = None) -> Dict:
        """下载视频"""
        try:
            # 识别平台
            platform = self._identify_platform(url)
            
            # 设置输出目录
            if output_dir is None:
                output_dir = settings.upload_dir
            
            os.makedirs(output_dir, exist_ok=True)
            
            platform, config = self._get_platform_download_config(platform)
            return await self._download_with_ytdlp(
                url=url,
                output_dir=output_dir,
                platform=platform,
                cookies_file=cookies_file,
                **config,
            )
                
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

    def _get_platform_download_config(self, platform: str) -> Tuple[str, Dict]:
        if platform in self.platform_download_configs:
            return platform, self.platform_download_configs[platform]
        return 'general', self.platform_download_configs['general']

    def _locate_downloaded_file(self, ydl: yt_dlp.YoutubeDL, info: Dict, output_dir: str) -> Optional[str]:
        """Locate the file yt-dlp wrote, including non-ASCII titles."""
        candidates = []

        if info:
            for key in ("filepath", "_filename"):
                if info.get(key):
                    candidates.append(info[key])

            for item in info.get("requested_downloads") or []:
                for key in ("filepath", "_filename"):
                    if item.get(key):
                        candidates.append(item[key])

            try:
                candidates.append(ydl.prepare_filename(info))
            except Exception:
                pass

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate

        try:
            files = [
                os.path.join(output_dir, file)
                for file in os.listdir(output_dir)
                if not file.endswith((".part", ".ytdl", ".temp"))
            ]
            files = [file for file in files if os.path.isfile(file)]
            files.sort(key=os.path.getmtime, reverse=True)
            return files[0] if files else None
        except Exception:
            return None

    def _build_ytdlp_options(
        self,
        output_dir: str,
        fmt: str,
        cookies_file: str = None,
        extra_opts: Optional[Dict] = None
    ) -> Dict:
        opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'format': fmt,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookies_file if cookies_file else None,
        }
        if extra_opts:
            opts.update(extra_opts)
        return opts

    async def _download_with_ytdlp(
        self,
        url: str,
        output_dir: str,
        platform: str,
        fmt: str = 'best[ext=mp4]/best',
        cookies_file: str = None,
        extra_opts: Optional[Dict] = None,
        fallback_to_http: bool = False
    ) -> Dict:
        """Shared yt-dlp download flow for supported platforms."""
        try:
            ydl_opts = self._build_ytdlp_options(output_dir, fmt, cookies_file, extra_opts)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown_title')

                ydl.download([url])
                downloaded_file = self._locate_downloaded_file(ydl, info, output_dir)

                if downloaded_file and os.path.exists(downloaded_file):
                    return {
                        "success": True,
                        "file_path": downloaded_file,
                        "title": title,
                        "duration": info.get('duration'),
                        "platform": platform
                    }

                return {
                    "success": False,
                    "error": "下载完成但找不到文件",
                    "file_path": None
                }

        except Exception as e:
            if fallback_to_http:
                return await self._download_direct_http(url, output_dir, cookies_file)
            return {
                "success": False,
                "error": f"{platform}下载失败: {str(e)}",
                "file_path": None
            }
    
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
