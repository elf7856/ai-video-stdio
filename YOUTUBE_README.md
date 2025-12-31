# 🎬 YouTube自动上传功能 - 开始使用

## 📖 文档导航

根据你的需求选择：

### 🚀 我想快速测试（5分钟）
👉 阅读 [YOUTUBE_QUICK_START.md](./YOUTUBE_QUICK_START.md)

**你将得到**:
- 最简化的步骤
- 清晰的命令
- 立即可用的测试脚本

### 📚 我想了解完整细节
👉 阅读 [YOUTUBE_UPLOAD_GUIDE.md](./YOUTUBE_UPLOAD_GUIDE.md)

**你将得到**:
- Google Cloud配置详细截图
- OAuth认证完整流程
- API配额管理
- 故障排除指南
- 完整工作流程示例

### 💻 我想看实现总结
👉 阅读 [YOUTUBE_IMPLEMENTATION_SUMMARY.md](./YOUTUBE_IMPLEMENTATION_SUMMARY.md)

**你将得到**:
- 架构设计说明
- 代码位置和关键逻辑
- 技术对比分析
- 未来扩展建议

---

## ⚡ 3步开始

### 1. 安装依赖
```bash
# 推荐使用 uv（速度快10倍）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -r requirements.txt

# 或使用传统 pip
pip install google-api-python-client google-auth-oauthlib
```

> 💡 使用 uv 安装全部依赖只需10-30秒！详见 [INSTALL_WITH_UV.md](./INSTALL_WITH_UV.md)

### 2. 获取凭据
1. 访问 https://console.cloud.google.com
2. 创建项目 -> 启用"YouTube Data API v3"
3. 创建OAuth凭据（桌面应用）
4. 下载并重命名为 `client_secret.json`

### 3. 运行测试
```bash
# 认证
python test_youtube_auth.py

# 上传
python test_youtube_upload.py
```

**完成！** 你的视频现在在YouTube上了 🎉

---

## 📁 文件说明

### 测试脚本
- `test_youtube_auth.py` - OAuth认证测试
- `test_youtube_upload.py` - 视频上传测试

### 文档
- `YOUTUBE_QUICK_START.md` - 5分钟快速开始
- `YOUTUBE_UPLOAD_GUIDE.md` - 完整指南（600行）
- `YOUTUBE_IMPLEMENTATION_SUMMARY.md` - 技术总结

### 生成的文件（不要提交到git）
- `client_secret.json` - OAuth凭据
- `token.json` - 访问令牌

---

## 🎯 功能特性

✅ **已实现**:
- YouTube官方API上传
- OAuth 2.0认证
- 断点续传（10MB分块）
- 实时进度跟踪
- 自动token刷新
- 前端上传界面
- RESTful API接口

⏳ **计划中**:
- 缩略图自动上传
- 视频统计分析
- 定时发布
- 批量上传

---

## ⚠️ 重要提示

1. **配额限制**: 每天10,000单位，约可上传6个视频
2. **文件安全**: `client_secret.json`和`token.json`不要公开
3. **隐私设置**: 测试时建议用"private"模式
4. **网络要求**: 需要稳定网络连接

---

## 🆘 遇到问题？

### 常见错误

**"OAuth client was not found"**
- 检查client_id和client_secret是否正确

**"quotaExceeded"**
- 超过每日配额，等到第二天或申请增加

**"The user has not granted permission"**
- 检查OAuth同意屏幕配置
- 确保添加了测试用户

### 获取帮助

1. 查看文档FAQ部分
2. 检查终端错误信息
3. 访问 https://developers.google.com/youtube/v3

---

## 🎓 工作原理

```
用户 -> FastAPI -> YouTubeUploader -> YouTube API
                       ↓
                   OAuth 2.0 认证
                       ↓
                   分块上传（10MB）
                       ↓
                   返回视频URL
```

---

## 📊 测试输出示例

```bash
$ python test_youtube_auth.py

====================================================
🎬 YouTube认证测试
====================================================

🌐 即将打开浏览器进行授权...
✅ 授权成功!
💾 凭证已保存到 token.json

====================================================
🧪 测试YouTube API
====================================================

📺 正在获取频道信息...

✅ 频道信息:
  📛 频道名: 我的频道
  👥 订阅数: 100
  🎬 视频数: 5
  👁️  观看数: 1000

====================================================
✅ 所有测试通过!
====================================================
```

```bash
$ python test_youtube_upload.py

====================================================
📤 开始上传视频
====================================================

📁 文件信息:
  路径: ./outputs/videos/video.mp4
  大小: 25.30 MB

⏫ 正在上传...
  进度: 10%
  进度: 20%
  ...
  进度: 100%

✅ 上传完成!

🎬 视频信息:
  视频ID: dQw4w9WgXcQ
  视频链接: https://www.youtube.com/watch?v=dQw4w9WgXcQ
  隐私状态: private

====================================================
✅ 测试成功!
====================================================
```

---

## 🚀 下一步

### 集成到你的工作流

```python
# 生成视频后自动上传
from app.services.upload import upload_manager, VideoMetadata, Platform

async def auto_publish(video_path):
    metadata = VideoMetadata(
        title="AI生成视频",
        description="自动上传测试",
        tags=["AI"]
    )

    task = await upload_manager.upload_to_platforms(
        video_path=video_path,
        metadata=metadata,
        platforms=[Platform.YOUTUBE]
    )

    print(f"视频链接: {task.results[0].video_url}")
```

### 使用前端界面

1. 启动后端: `uvicorn app.main:app --reload`
2. 启动前端: `cd frontend && npm run dev`
3. 访问: http://localhost:5173/upload

---

**🎉 开始创作和分享你的视频吧！**

有问题？查看详细文档：
- 快速开始: [YOUTUBE_QUICK_START.md](./YOUTUBE_QUICK_START.md)
- 完整指南: [YOUTUBE_UPLOAD_GUIDE.md](./YOUTUBE_UPLOAD_GUIDE.md)
