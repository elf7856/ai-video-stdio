# 视频创作平台 - 使用示例

这个目录包含了各种使用示例，帮助你快速上手视频创作平台的功能。

## 📁 示例文件列表

### 🎬 视频内容分析示例

#### 1. `simple_video_analysis.py` - 简单视频分析 ⭐ **推荐新手使用**
最简单易用的视频内容分析工具，支持交互式操作。

**功能:**
- 输入视频URL，获得AI生成的内容总结
- 支持YouTube、B站、TikTok等主流平台
- 提供改进建议
- 自动清理临时文件

**使用方法:**
```bash
# 交互模式
python examples/simple_video_analysis.py

# 直接分析指定URL
python examples/simple_video_analysis.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 2. `video_content_analysis.py` - 完整视频分析
功能更全面的视频分析示例，包含详细的分析流程。

**功能:**
- 完整的视频分析流程
- 批量分析支持
- 结果保存到JSON文件
- 关键时刻提取

**使用方法:**
```bash
python examples/video_content_analysis.py
```

### 🔧 其他示例

#### 3. `basic_usage.py` - 基础功能使用
展示平台各个组件的基本使用方法。

**功能:**
- TTS语音生成
- 图像生成
- 视频编辑
- 自然语言处理

#### 4. `video_processing_flow.py` - 完整处理流程
展示从URL到最终视频的完整处理流程。

**功能:**
- 视频下载
- 内容分析
- 摘要生成
- 自然语言编辑

## 🚀 快速开始

### 1. 环境准备

确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### 2. API密钥配置

至少配置一个LLM服务的API密钥：

```bash
# 推荐：Google Gemini (免费额度较多)
export GOOGLE_API_KEY="your_google_api_key"

# 或者 OpenAI
export OPENAI_API_KEY="your_openai_api_key"

# 或者 Anthropic
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### 3. 运行示例

对于新手，推荐从简单示例开始：

```bash
cd /path/to/video_creator_platform
python examples/simple_video_analysis.py
```

然后按照提示输入视频URL即可。

## 📋 使用场景

### 🎯 场景1: 内容创作者分析竞品
```bash
# 分析热门视频，获取内容总结和改进建议
python examples/simple_video_analysis.py "竞品视频URL"
```

### 🎯 场景2: 教育工作者分析教学视频
```bash
# 分析教育视频，提取关键知识点
python examples/video_content_analysis.py
# 然后选择详细分析模式
```

### 🎯 场景3: 批量分析多个视频
```python
# 在video_content_analysis.py中修改video_urls列表
video_urls = [
    "https://www.youtube.com/watch?v=video1",
    "https://www.youtube.com/watch?v=video2",
    # 添加更多URL
]
```

## 🔧 支持的视频平台

- ✅ **YouTube** - 完全支持
- ✅ **Bilibili (B站)** - 完全支持
- ✅ **TikTok** - 支持公开视频
- ✅ **Instagram** - 支持公开视频
- ✅ **Twitter/X** - 支持视频推文
- ✅ **直链视频** - 支持.mp4等格式

## 📊 输出格式

### 分析结果包含：

1. **基本信息**
   - 视频标题
   - 平台来源
   - 视频时长
   - 原始URL

2. **AI内容总结**
   - 内容概述
   - 关键要点
   - 主题分类
   - 情感分析

3. **改进建议**
   - 内容优化建议
   - 结构改进建议
   - 观众参与度提升建议

4. **关键时刻**（可选）
   - 重要片段标识
   - 时间戳信息

## ⚠️ 注意事项

1. **API配置**: 确保至少配置一个LLM API密钥
2. **网络连接**: 需要稳定的网络连接下载视频
3. **存储空间**: 临时下载的视频会占用存储空间（分析完成后自动清理）
4. **版权问题**: 请确保有权分析所选视频内容
5. **API限制**: 注意各API服务商的调用频率限制

## 🆘 常见问题

### Q: 视频下载失败怎么办？
A: 
- 检查视频URL是否正确且可访问
- 确认视频是公开的，非私人视频
- 尝试更换网络环境

### Q: AI分析结果不准确？
A: 
- 确保API密钥有效且有足够额度
- 尝试使用不同的LLM服务
- 检查视频内容是否适合AI分析

### Q: 如何自定义分析内容？
A: 
- 修改`app/services/llm/analyzer.py`中的分析提示词
- 或在示例代码中调整分析参数

## 📞 获取帮助

如果遇到问题，可以：
1. 查看项目根目录的README.md
2. 检查日志文件了解详细错误信息
3. 提交Issue描述问题

---

**快速体验建议**: 先运行`simple_video_analysis.py`，输入一个YouTube视频URL，体验基本功能！ 