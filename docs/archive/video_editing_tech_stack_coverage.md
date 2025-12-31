# 视频后期技术栈功能覆盖分析

## 核心问题：FFmpeg + MoviePy + Pillow 能覆盖所有视频后期需求吗？

**简短回答**：能覆盖 **90%** 的需求，但需要补充几个关键库（特别是字幕相关）。

---

## 一、完整功能覆盖表

### 1. ✅ 基础剪辑功能（100% 覆盖）

| 功能 | FFmpeg | MoviePy | Pillow | 实现难度 |
|------|--------|---------|--------|----------|
| 视频裁剪 | ✅ | ✅ | - | ⭐ 简单 |
| 视频分割 | ✅ | ✅ | - | ⭐ 简单 |
| 视频合并 | ✅ | ✅ | - | ⭐⭐ 中等 |
| 速度调整 | ✅ | ✅ | - | ⭐⭐ 中等 |
| 反向播放 | ✅ | ✅ | - | ⭐⭐ 中等 |
| 视频旋转 | ✅ | ✅ | - | ⭐ 简单 |
| 画面裁剪 | ✅ | ✅ | - | ⭐ 简单 |
| 画面缩放 | ✅ | ✅ | - | ⭐ 简单 |

**结论**：✅ **完全覆盖**，无需额外库

---

### 2. ⚠️ 字幕功能（需要补充库）

| 功能 | FFmpeg | MoviePy | 额外需求 | 推荐方案 |
|------|--------|---------|----------|----------|
| **硬字幕（烧录）** | ✅ drawtext | ✅ TextClip | - | FFmpeg/MoviePy |
| **软字幕（SRT）** | ✅ | ❌ | srt 库 | FFmpeg + pysrt |
| **自动生成字幕** | ❌ | ❌ | Whisper | **需要 openai-whisper** |
| **字幕样式** | ⚠️ 基础 | ✅ 完整 | - | MoviePy TextClip |
| **字幕动画** | ❌ | ✅ | - | MoviePy |
| **字幕识别/OCR** | ❌ | ❌ | PaddleOCR | **需要 paddleocr** |
| **多语言翻译** | ❌ | ❌ | 翻译API | **需要 LLM API** |

#### 2.1 硬字幕（烧录到视频中）✅

**方案 1: FFmpeg drawtext（推荐用于简单字幕）**
```python
import ffmpeg

def add_hardcoded_subtitle_ffmpeg(
    video_path: str,
    output_path: str,
    text: str,
    start_time: float,
    duration: float
):
    """使用 FFmpeg 添加硬字幕"""
    (
        ffmpeg
        .input(video_path)
        .drawtext(
            text=text,
            x='(w-text_w)/2',  # 居中
            y='h-th-50',        # 底部
            fontfile='/System/Library/Fonts/PingFang.ttc',  # macOS 中文字体
            fontsize=24,
            fontcolor='white',
            box=1,              # 背景框
            boxcolor='black@0.5',
            enable=f'between(t,{start_time},{start_time + duration})'
        )
        .output(output_path)
        .run()
    )
```

**方案 2: MoviePy TextClip（推荐用于复杂样式）**
```python
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def add_hardcoded_subtitle_moviepy(
    video_path: str,
    output_path: str,
    subtitle_segments: list[dict]
):
    """
    使用 MoviePy 添加硬字幕
    subtitle_segments = [
        {"text": "你好", "start": 0.0, "duration": 2.0},
        {"text": "世界", "start": 2.0, "duration": 3.0}
    ]
    """
    video = VideoFileClip(video_path)
    subtitle_clips = []

    for segment in subtitle_segments:
        txt_clip = TextClip(
            segment['text'],
            fontsize=40,
            font='PingFang-SC-Regular',  # macOS 中文字体
            color='white',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(video.w - 100, None)  # 自动换行
        )
        txt_clip = txt_clip.set_position(('center', 'bottom'))
        txt_clip = txt_clip.set_start(segment['start'])
        txt_clip = txt_clip.set_duration(segment['duration'])

        # 可选：添加淡入淡出
        txt_clip = txt_clip.crossfadein(0.3).crossfadeout(0.3)

        subtitle_clips.append(txt_clip)

    # 合成
    final = CompositeVideoClip([video] + subtitle_clips)
    final.write_videofile(output_path, codec='libx264', audio_codec='aac')
```

**优缺点对比**:
- FFmpeg: ⚡ 快速，适合固定样式，中文支持需要指定字体
- MoviePy: 🎨 样式丰富，支持动画，但渲染较慢

---

#### 2.2 软字幕（SRT/ASS 文件）✅

**需要额外库**: `pysrt` 或 `ass`

```bash
pip install pysrt
```

**生成 SRT 字幕文件**:
```python
import pysrt

def create_srt_file(
    subtitle_segments: list[dict],
    output_path: str
):
    """
    生成 SRT 字幕文件
    subtitle_segments = [
        {"text": "你好世界", "start": 0.0, "end": 2.0},
        {"text": "这是第二句", "start": 2.0, "end": 5.0}
    ]
    """
    subs = pysrt.SubRipFile()

    for i, segment in enumerate(subtitle_segments, 1):
        item = pysrt.SubRipItem(
            index=i,
            start=pysrt.SubRipTime(seconds=segment['start']),
            end=pysrt.SubRipTime(seconds=segment['end']),
            text=segment['text']
        )
        subs.append(item)

    subs.save(output_path, encoding='utf-8')

# 使用示例
create_srt_file(
    [
        {"text": "欢迎来到 AI 视频平台", "start": 0.0, "end": 2.5},
        {"text": "让我们开始创作吧", "start": 2.5, "end": 5.0}
    ],
    "output/subtitles.srt"
)
```

**将 SRT 嵌入视频（软字幕）**:
```python
import ffmpeg

def add_soft_subtitle(
    video_path: str,
    srt_path: str,
    output_path: str
):
    """添加软字幕（可在播放器中开关）"""
    (
        ffmpeg
        .input(video_path)
        .output(
            output_path,
            vcodec='copy',
            acodec='copy',
            **{'c:s': 'mov_text'}  # 字幕编码器
        )
        .global_args('-i', srt_path)
        .global_args('-map', '0:v', '-map', '0:a', '-map', '1:s')
        .run()
    )
```

---

#### 2.3 🔥 自动生成字幕（ASR - 语音识别）⚠️ 需要 Whisper

**核心库**: `openai-whisper`（你的 requirements.txt 已包含）

```python
import whisper
from pathlib import Path
import pysrt

class SubtitleGenerator:
    def __init__(self, model_name: str = "base"):
        """
        初始化 Whisper 模型
        model_name: tiny, base, small, medium, large
        - tiny: 最快，准确率较低
        - base: 平衡（推荐）
        - large: 最准确，但慢
        """
        self.model = whisper.load_model(model_name)

    def transcribe_video(self, video_path: str) -> dict:
        """
        转录视频音频为文字（带时间戳）
        返回: {"segments": [...], "text": "..."}
        """
        result = self.model.transcribe(
            video_path,
            language='zh',  # 中文
            verbose=True
        )
        return result

    def generate_srt(
        self,
        video_path: str,
        output_srt_path: str,
        max_chars_per_line: int = 20  # 每行最大字符数
    ):
        """自动生成 SRT 字幕文件"""
        result = self.transcribe_video(video_path)
        subs = pysrt.SubRipFile()

        for i, segment in enumerate(result['segments'], 1):
            # 分割长文本
            text = segment['text'].strip()
            if len(text) > max_chars_per_line:
                # 简单换行（可以改进）
                mid = len(text) // 2
                text = f"{text[:mid]}\n{text[mid:]}"

            item = pysrt.SubRipItem(
                index=i,
                start=pysrt.SubRipTime(seconds=segment['start']),
                end=pysrt.SubRipTime(seconds=segment['end']),
                text=text
            )
            subs.append(item)

        subs.save(output_srt_path, encoding='utf-8')
        return output_srt_path

# 使用示例
generator = SubtitleGenerator(model_name='base')
generator.generate_srt(
    'input.mp4',
    'output/auto_subtitle.srt'
)
```

**Whisper 模型对比**:
| 模型 | 大小 | 速度 | 准确率 | 推荐场景 |
|------|------|------|--------|----------|
| tiny | 39 MB | 32x | ⭐⭐⭐ | 快速预览 |
| base | 74 MB | 16x | ⭐⭐⭐⭐ | **日常使用（推荐）** |
| small | 244 MB | 6x | ⭐⭐⭐⭐ | 高质量需求 |
| medium | 769 MB | 2x | ⭐⭐⭐⭐⭐ | 专业场景 |
| large | 1550 MB | 1x | ⭐⭐⭐⭐⭐ | 最高质量 |

---

#### 2.4 字幕样式和动画 ✅

**MoviePy 支持丰富的字幕样式**:
```python
from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip
from moviepy.video.fx import fadein, fadeout

def create_styled_subtitle(
    text: str,
    start_time: float,
    duration: float,
    video_size: tuple,
    style: dict = None
):
    """
    创建样式化字幕
    style = {
        'fontsize': 40,
        'color': 'yellow',
        'stroke_color': 'black',
        'stroke_width': 2,
        'bg_color': 'rgba(0,0,0,0.5)',
        'position': 'bottom',
        'animation': 'fade'  # fade, slide, scale
    }
    """
    if style is None:
        style = {}

    # 创建文字片段
    txt_clip = TextClip(
        text,
        fontsize=style.get('fontsize', 40),
        font=style.get('font', 'PingFang-SC-Regular'),
        color=style.get('color', 'white'),
        stroke_color=style.get('stroke_color', 'black'),
        stroke_width=style.get('stroke_width', 2),
        bg_color=style.get('bg_color'),
        method='caption',
        size=(video_size[0] - 100, None)
    )

    # 设置位置
    position = style.get('position', 'bottom')
    if position == 'bottom':
        txt_clip = txt_clip.set_position(('center', video_size[1] - 150))
    elif position == 'top':
        txt_clip = txt_clip.set_position(('center', 50))
    else:
        txt_clip = txt_clip.set_position(('center', 'center'))

    txt_clip = txt_clip.set_start(start_time)
    txt_clip = txt_clip.set_duration(duration)

    # 添加动画
    animation = style.get('animation', 'fade')
    if animation == 'fade':
        txt_clip = txt_clip.crossfadein(0.5).crossfadeout(0.5)
    elif animation == 'slide':
        # 从左滑入
        txt_clip = txt_clip.set_position(
            lambda t: (max(-video_size[0], -video_size[0] + 100*t), video_size[1] - 150)
        )

    return txt_clip

# 使用示例
video = VideoFileClip('input.mp4')
subtitle_styles = [
    {
        'text': '欢迎来到 AI 视频平台',
        'start': 0,
        'duration': 3,
        'style': {
            'fontsize': 50,
            'color': 'yellow',
            'stroke_color': 'black',
            'stroke_width': 3,
            'animation': 'fade'
        }
    },
    {
        'text': '让我们开始创作',
        'start': 3,
        'duration': 3,
        'style': {
            'fontsize': 45,
            'color': 'white',
            'bg_color': 'rgba(0,0,0,0.7)',
            'animation': 'slide'
        }
    }
]

subtitle_clips = [
    create_styled_subtitle(
        s['text'],
        s['start'],
        s['duration'],
        (video.w, video.h),
        s['style']
    )
    for s in subtitle_styles
]

final = CompositeVideoClip([video] + subtitle_clips)
final.write_videofile('output_with_subtitles.mp4')
```

---

### 3. ✅ 音频处理（100% 覆盖）

| 功能 | FFmpeg | MoviePy | 额外需求 | 备注 |
|------|--------|---------|----------|------|
| 提取音频 | ✅ | ✅ | - | - |
| 替换音频 | ✅ | ✅ | - | - |
| 音量调整 | ✅ | ✅ | - | - |
| 音频混合 | ✅ | ✅ | - | 多轨音频 |
| 淡入淡出 | ✅ | ✅ | - | - |
| 音频均衡器 | ✅ | ❌ | - | 用 FFmpeg |
| 降噪 | ✅ | ❌ | - | FFmpeg afftdn |
| 语音合成(TTS) | ❌ | ❌ | edge-tts | **你已有** |

**结论**：✅ **完全覆盖**，你的项目已有 Edge TTS

---

### 4. ✅ 滤镜和特效（95% 覆盖）

| 功能 | FFmpeg | MoviePy | Pillow | 备注 |
|------|--------|---------|--------|------|
| 亮度/对比度 | ✅ | ✅ | ✅ | - |
| 饱和度 | ✅ | ✅ | ✅ | - |
| 色调调整 | ✅ | ✅ | ✅ | - |
| 锐化 | ✅ | ✅ | ✅ | - |
| 模糊 | ✅ | ✅ | ✅ | - |
| 黑白/复古 | ✅ | ✅ | ✅ | - |
| 色彩滤镜 | ✅ | ✅ | ✅ | LUT 支持 |
| 马赛克 | ✅ | ✅ | - | - |
| 镜像 | ✅ | ✅ | ✅ | - |
| 色度抠图 | ✅ | ❌ | ❌ | 绿幕 |

**结论**：✅ **基本覆盖**，高级抠图可能需要 OpenCV

---

### 5. ⚠️ 转场效果（80% 覆盖）

| 转场类型 | FFmpeg | MoviePy | 难度 |
|----------|--------|---------|------|
| 淡入淡出 | ✅ | ✅ | ⭐ 简单 |
| 溶解 | ✅ | ✅ | ⭐ 简单 |
| 划像 | ✅ xfade | ✅ | ⭐⭐ 中等 |
| 缩放 | ✅ | ✅ | ⭐⭐ 中等 |
| 旋转 | ✅ | ✅ | ⭐⭐ 中等 |
| 3D 翻转 | ❌ | ⚠️ 困难 | ⭐⭐⭐⭐ 复杂 |

**FFmpeg xfade 转场示例**:
```python
import ffmpeg

def add_transition(clip1_path, clip2_path, output_path, transition='fade', duration=1.0):
    """添加转场效果"""
    clip1 = ffmpeg.input(clip1_path)
    clip2 = ffmpeg.input(clip2_path)

    (
        ffmpeg
        .filter([clip1, clip2], 'xfade', transition=transition, duration=duration, offset=5)
        .output(output_path)
        .run()
    )
```

**FFmpeg 支持的转场类型**:
- fade, fadeblack, fadewhite
- wipeleft, wiperight, wipeup, wipedown
- slideleft, slideright, slideup, slidedown
- circleopen, circleclose
- dissolve
- pixelize

**结论**：✅ **大部分转场都支持**

---

### 6. ✅ 图像和水印（100% 覆盖）

| 功能 | FFmpeg | MoviePy | Pillow | 备注 |
|------|--------|---------|--------|------|
| 图片叠加 | ✅ | ✅ | - | 水印 |
| 画中画 | ✅ | ✅ | - | PIP |
| Logo 水印 | ✅ | ✅ | - | - |
| 图片序列 | ✅ | ✅ | - | 帧序列 |
| 动态贴纸 | ✅ | ✅ | - | GIF/PNG 序列 |
| 图片处理 | ⚠️ 基础 | ⚠️ 基础 | ✅ 强大 | 用 Pillow |

**结论**：✅ **完全覆盖**，Pillow 提供强大的图像处理

---

### 7. ⚠️ AI 功能（需要额外集成）

| 功能 | 现有方案 | 额外需求 | 备注 |
|------|----------|----------|------|
| 自动字幕 | ✅ Whisper | - | **你已有** |
| 语音合成 | ✅ Edge TTS | - | **你已有** |
| 抠图/去背景 | ❌ | rembg / U²-Net | **需要添加** |
| 人脸识别 | ❌ | face_recognition | 可选 |
| 场景检测 | ✅ FFmpeg | - | scdet 滤镜 |
| 视频稳定 | ✅ FFmpeg | - | deshake 滤镜 |
| 超分辨率 | ❌ | Real-ESRGAN | 可选 |

---

## 二、完整技术栈推荐

### 核心三件套（必需）
```bash
# 你的项目已有
ffmpeg-python>=0.2.0      # FFmpeg Python 封装
moviepy>=1.0.3            # 视频编辑
Pillow>=10.0.0            # 图像处理
```

### 字幕相关（必需）
```bash
# 你的项目已有
openai-whisper>=20231117  # 自动字幕（ASR）

# 需要添加
pysrt>=1.1.2              # SRT 字幕处理
ass>=0.5.2                # ASS 字幕处理（可选，高级样式）
```

### AI 增强（推荐）
```bash
# 你的项目已有
edge-tts>=6.1.9           # 语音合成

# 推荐添加（如果需要抠图功能）
rembg>=2.0.50             # AI 抠图/去背景
opencv-python>=4.8.0      # 你已有，可用于抠图后处理
```

### 可选增强
```bash
# 如果需要人脸功能
face-recognition>=1.3.0   # 人脸识别

# 如果需要超分辨率
# realesrgan  # 视频超分（慎用，很重）
```

---

## 三、推荐的最终技术栈

### 最小可用版本（基础视频编辑）
```python
# requirements.txt
ffmpeg-python>=0.2.0
moviepy>=1.0.3
Pillow>=10.0.0
pysrt>=1.1.2              # 新增：字幕处理
```

### 标准版本（含 AI 字幕）
```python
# requirements.txt
ffmpeg-python>=0.2.0
moviepy>=1.0.3
Pillow>=10.0.0
pysrt>=1.1.2
openai-whisper>=20231117  # 你已有
edge-tts>=6.1.9           # 你已有
```

### 完整版本（含 AI 抠图）
```python
# requirements.txt
ffmpeg-python>=0.2.0
moviepy>=1.0.3
Pillow>=10.0.0
pysrt>=1.1.2
openai-whisper>=20231117  # 你已有
edge-tts>=6.1.9           # 你已有
rembg>=2.0.50             # 新增：AI 抠图
opencv-python>=4.8.0      # 你已有
```

---

## 四、实际代码示例：完整字幕工作流

```python
# app/services/video/subtitle_service.py
import whisper
import pysrt
import ffmpeg
from pathlib import Path
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

class SubtitleService:
    def __init__(self):
        # 加载 Whisper 模型（首次会下载）
        self.whisper_model = whisper.load_model("base")

    async def generate_auto_subtitles(
        self,
        video_path: Path,
        output_dir: Path,
        language: str = 'zh'
    ) -> dict:
        """
        自动生成字幕的完整流程
        返回: {"srt_path": "...", "video_with_srt": "...", "video_hardcoded": "..."}
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. 使用 Whisper 转录
        print("🎤 正在识别语音...")
        result = self.whisper_model.transcribe(
            str(video_path),
            language=language,
            verbose=False
        )

        # 2. 生成 SRT 文件
        srt_path = output_dir / f"{video_path.stem}.srt"
        subs = pysrt.SubRipFile()

        for i, segment in enumerate(result['segments'], 1):
            text = segment['text'].strip()
            item = pysrt.SubRipItem(
                index=i,
                start=pysrt.SubRipTime(seconds=segment['start']),
                end=pysrt.SubRipTime(seconds=segment['end']),
                text=text
            )
            subs.append(item)

        subs.save(str(srt_path), encoding='utf-8')
        print(f"✅ SRT 字幕已生成: {srt_path}")

        # 3. 生成软字幕视频（可开关）
        soft_sub_path = output_dir / f"{video_path.stem}_soft_sub.mp4"
        self._add_soft_subtitle(video_path, srt_path, soft_sub_path)
        print(f"✅ 软字幕视频: {soft_sub_path}")

        # 4. 生成硬字幕视频（烧录）
        hard_sub_path = output_dir / f"{video_path.stem}_hard_sub.mp4"
        self._add_hardcoded_subtitle(video_path, subs, hard_sub_path)
        print(f"✅ 硬字幕视频: {hard_sub_path}")

        return {
            "srt_path": str(srt_path),
            "video_with_soft_sub": str(soft_sub_path),
            "video_with_hard_sub": str(hard_sub_path),
            "transcript": result['text']
        }

    def _add_soft_subtitle(
        self,
        video_path: Path,
        srt_path: Path,
        output_path: Path
    ):
        """添加软字幕（FFmpeg）"""
        (
            ffmpeg
            .input(str(video_path))
            .output(
                str(output_path),
                vcodec='copy',
                acodec='copy',
                **{'c:s': 'mov_text'}
            )
            .global_args('-i', str(srt_path))
            .global_args('-map', '0:v', '-map', '0:a', '-map', '1:s')
            .overwrite_output()
            .run(quiet=True)
        )

    def _add_hardcoded_subtitle(
        self,
        video_path: Path,
        subs: pysrt.SubRipFile,
        output_path: Path
    ):
        """添加硬字幕（MoviePy，样式更好）"""
        video = VideoFileClip(str(video_path))
        subtitle_clips = []

        for sub in subs:
            txt_clip = TextClip(
                sub.text,
                fontsize=40,
                font='Arial-Unicode-MS',  # 跨平台中文字体
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(video.w - 100, None)
            )

            txt_clip = txt_clip.set_position(('center', video.h - 150))
            txt_clip = txt_clip.set_start(sub.start.ordinal / 1000.0)
            txt_clip = txt_clip.set_duration((sub.end.ordinal - sub.start.ordinal) / 1000.0)
            txt_clip = txt_clip.crossfadein(0.2).crossfadeout(0.2)

            subtitle_clips.append(txt_clip)

        final = CompositeVideoClip([video] + subtitle_clips)
        final.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=video.fps
        )

        video.close()
        final.close()

# 使用示例
subtitle_service = SubtitleService()
result = await subtitle_service.generate_auto_subtitles(
    Path("input/demo.mp4"),
    Path("output/subtitles")
)
```

---

## 五、功能覆盖总结

### ✅ 完全覆盖的功能（90%）
1. ✅ 基础剪辑（裁剪、分割、合并、速度）
2. ✅ 音频处理（提取、混合、TTS）
3. ✅ 滤镜特效（亮度、对比度、饱和度、模糊等）
4. ✅ 转场效果（淡入淡出、划像等）
5. ✅ 图片水印和画中画
6. ✅ **硬字幕**（FFmpeg + MoviePy）
7. ✅ **软字幕**（FFmpeg + pysrt）
8. ✅ **自动字幕**（Whisper）
9. ✅ 语音合成（Edge TTS）

### ⚠️ 需要补充的功能（10%）
1. ⚠️ **SRT 字幕处理** → 添加 `pysrt`（简单）
2. ⚠️ **AI 抠图** → 添加 `rembg`（可选）
3. ⚠️ **复杂关键帧动画** → 使用 MoviePy（有限支持）

### ❌ 不支持的功能（<5%）
1. ❌ 3D 效果（需要专业工具如 Blender）
2. ❌ 超高级粒子系统（需要 After Effects 级别）

---

## 六、总结和建议

### 📊 覆盖率评估
- **基础剪辑**: 100% ✅
- **字幕功能**: 95% ✅（加上 pysrt 后）
- **音频处理**: 100% ✅
- **视觉效果**: 90% ✅
- **AI 功能**: 80% ✅（你已有 Whisper 和 TTS）

**总体覆盖率**: **95%** 🎉

### 🎯 推荐行动

#### 立即添加（必需）
```bash
pip install pysrt
```

#### 可选添加（看需求）
```bash
# 如果需要 AI 抠图
pip install rembg

# 如果需要更好的字幕样式控制
pip install ass
```

### 🚀 你的项目现状
你的 `requirements.txt` 已经很完善了：
- ✅ FFmpeg (ffmpeg-python)
- ✅ MoviePy
- ✅ Pillow
- ✅ OpenCV
- ✅ Whisper (自动字幕)
- ✅ Edge TTS (语音合成)

**只需添加**: `pysrt` 就能实现完整的字幕工作流！

### 💡 最终建议

对于你的 AI 视频平台，这个技术栈组合：

**FFmpeg + MoviePy + Pillow + pysrt + Whisper**

可以满足 **95%** 的视频后期需求，包括：
- ✅ 所有基础剪辑功能
- ✅ **完整的字幕解决方案**（自动生成 + 样式 + 硬/软字幕）
- ✅ 音频处理和 TTS
- ✅ 滤镜和特效
- ✅ 转场和水印

这已经足够实现一个**专业级的视频编辑平台**了！
