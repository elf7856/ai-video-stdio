# 🎬 视频内容分析演示

## 快速开始

这个演示展示如何使用我们的视频内容分析工具，从视频URL获取AI生成的内容总结。

### 1. 准备工作

确保已配置API密钥：
```bash
export GOOGLE_API_KEY="your_google_api_key"
# 或
export OPENAI_API_KEY="your_openai_api_key"
# 或  
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### 2. 测试系统

运行快速测试确保一切正常：
```bash
python examples/test_video_analysis.py
```

### 3. 开始分析

使用简单的交互式工具：
```bash
python examples/simple_video_analysis.py
```

## 🎯 使用示例

### 示例1: 分析YouTube视频

```bash
python examples/simple_video_analysis.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**预期输出:**
```
🎬 正在分析视频: https://www.youtube.com/watch?v=dQw4w9WgXcQ
--------------------------------------------------
📊 获取视频信息...
✅ 标题: Rick Astley - Never Gonna Give You Up (Official Video)
📺 平台: youtube
⏱️ 时长: 3分33秒

📥 下载视频...
✅ 下载完成: Rick Astley - Never Gonna Give You Up (Official Video).webm

🤖 AI分析中...
💡 生成改进建议...
🧹 已清理临时文件

============================================================
📋 视频内容分析结果
============================================================

📺 视频信息:
   🎬 标题: Rick Astley - Never Gonna Give You Up (Official Video)
   🌐 平台: youtube
   🔗 链接: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ⏱️ 时长: 3分33秒

📝 AI内容总结:
   这是一个1987年的经典流行音乐视频，展现了80年代的音乐风格和视觉美学。
   视频包含舞蹈表演、复古服装设计和典型的MTV时代制作特色。
   歌曲具有朗朗上口的旋律和积极向上的情感表达。

💡 AI改进建议:
   现代重制建议：可以考虑提升视频画质到4K分辨率
   增加字幕支持多种语言，提高国际观众可访问性
   可以制作幕后花絮版本，展示拍摄过程和时代背景

⏰ 分析时间: 2024-12-XX XX:XX:XX
============================================================
```

### 示例2: 分析B站视频

```bash
python examples/simple_video_analysis.py "https://www.bilibili.com/video/BV1xx411c7mu"
```

### 示例3: 交互模式

```bash
python examples/simple_video_analysis.py
```

然后选择:
```
请选择:
1. 输入视频URL分析
2. 使用示例URL  
3. 退出

请输入选择 (1-3): 1

请输入视频URL: https://www.youtube.com/watch?v=your_video_id
```

## 🔧 支持的平台

| 平台 | 状态 | 说明 |
|------|------|------|
| ✅ YouTube | 完全支持 | 可能需要cookies验证 |
| ✅ Bilibili | 完全支持 | 支持BV号和av号 |
| ✅ TikTok | 基本支持 | 仅公开视频 |
| ✅ Instagram | 基本支持 | 仅公开视频 |
| ✅ Twitter/X | 基本支持 | 视频推文 |
| ✅ 直链视频 | 完全支持 | .mp4, .webm等格式 |

## 📊 输出说明

### 基本信息
- **标题**: 视频原始标题
- **平台**: 视频来源平台  
- **时长**: 视频总时长
- **链接**: 原始URL

### AI分析结果
- **内容总结**: AI对视频内容的理解和概括
- **关键要点**: 视频中的重要信息点
- **风格分析**: 视频的制作风格和特点
- **目标受众**: 分析视频的目标观众群体

### 改进建议
- **内容优化**: 如何改进视频内容
- **技术建议**: 画质、音质等技术改进
- **推广建议**: 如何提高视频传播效果

## ⚠️ 常见问题

### Q: 下载失败怎么办？
A: 
1. 确认视频URL正确且可访问
2. 检查网络连接
3. 某些平台可能需要cookies验证
4. 私人视频无法下载

### Q: AI分析结果不准确？
A:
1. 确保API密钥有效且有额度
2. 网络连接可能导致API调用超时
3. 尝试重新运行分析
4. 考虑更换LLM服务提供商

### Q: 如何处理超时？
A:
1. 检查网络连接稳定性
2. 尝试更短的视频
3. 增加timeout参数值
4. 减少retry_count避免长时间等待

### Q: 支持哪些语言？
A:
- 输出语言：中文（可修改prompt调整）
- 视频语言：支持多种语言的视频分析
- API语言：依赖所选LLM服务的语言能力

## 🚀 进阶使用

### 自定义分析

修改`simple_video_analysis.py`中的分析参数：

```python
# 调整超时时间
analysis_result = await analyzer.analyze_video_content(
    video_info=video_metadata,
    timeout=60,  # 增加到60秒
    retry_count=3  # 增加重试次数
)
```

### 批量分析

使用`video_content_analysis.py`进行批量处理：

```python
video_urls = [
    "https://www.youtube.com/watch?v=video1",
    "https://www.youtube.com/watch?v=video2",
    # 添加更多URL
]
```

### 结果保存

分析结果会自动保存到`outputs/video_analysis_results.json`:

```json
{
  "success": true,
  "timestamp": "2024-12-XX",
  "video_info": {
    "title": "视频标题",
    "platform": "youtube",
    "duration": 213,
    "url": "原始URL"
  },
  "content_analysis": {
    "success": true,
    "summary": "AI生成的内容总结"
  },
  "improvement_suggestions": {
    "success": true,
    "suggestions": "AI生成的改进建议"
  }
}
```

---

## 📝 开发者说明

这个工具是基于以下技术构建的：

- **视频下载**: yt-dlp
- **AI分析**: Google Gemini / OpenAI / Anthropic
- **API调用**: litellm (统一多个LLM接口)
- **异步处理**: asyncio

核心文件：
- `app/services/llm/analyzer.py` - LLM分析服务
- `app/services/video/downloader.py` - 视频下载服务
- `examples/simple_video_analysis.py` - 简单分析工具
- `examples/video_content_analysis.py` - 完整分析工具

---

**🎉 享受AI视频分析的乐趣！** 