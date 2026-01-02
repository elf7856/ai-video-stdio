# YouTube视频上传功能 - 完整指南

## 🎯 目标

实现通过YouTube Data API v3自动上传视频到YouTube的功能。

---

## 📋 前置要求

### 1. 安装依赖

#### 方法1: 使用 uv（推荐，极速安装）

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖（包含YouTube上传所需的包）
uv pip install -r requirements.txt
```

#### 方法2: 使用 pip

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

> 💡 **为什么推荐 uv？**
> - 安装速度快10-100倍
> - 更好的依赖解析
> - 详细指南: [INSTALL_WITH_UV.md](./INSTALL_WITH_UV.md)

### 2. 创建Google Cloud项目

#### 步骤1: 创建项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com)
2. 点击顶部的项目下拉菜单
3. 点击"新建项目"
4. 输入项目名称（如 "Video Creator Platform"）
5. 点击"创建"

#### 步骤2: 启用YouTube Data API v3
1. 在左侧菜单选择"API和服务" -> "库"
2. 搜索"YouTube Data API v3"
3. 点击进入，点击"启用"

#### 步骤3: 创建OAuth 2.0凭据
1. 在左侧菜单选择"API和服务" -> "凭据"
2. 点击"创建凭据" -> "OAuth 2.0 客户端ID"
3. 如果是第一次，需要先配置"OAuth同意屏幕":
   - 用户类型选择"外部"
   - 填写应用名称、用户支持电子邮件
   - 开发者联系信息填写邮箱
   - 点击"保存并继续"
   - 作用域页面直接"保存并继续"
   - 测试用户添加你的Gmail账号
   - 点击"保存并继续"

4. 回到创建OAuth客户端ID:
   - 应用类型选择"桌面应用"或"Web应用"
   - 如果选"Web应用"，添加授权重定向URI:
     - `http://localhost:8080/`
     - `http://localhost:5173/oauth/callback`
   - 点击"创建"

5. 下载凭据JSON文件，保存为 `client_secret.json`

---

## 🔧 配置方法

### 方法1: 使用环境变量（推荐用于生产）

在 `.env` 文件中添加：

```env
# YouTube OAuth配置
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 方法2: 使用client_secret.json文件（推荐用于开发）

将下载的 `client_secret.json` 放在项目根目录。

---

## 🚀 测试YouTube上传

### 测试1: OAuth授权流程

创建测试脚本 `test_youtube_auth.py`:

```python
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    """获取认证的YouTube服务"""
    creds = None

    # 检查是否有保存的token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # 如果没有有效凭证，让用户登录
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 使用client_secret.json进行授权
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=8080)

        # 保存凭证供下次使用
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('youtube', 'v3', credentials=creds)

if __name__ == '__main__':
    print("开始YouTube认证...")
    youtube = get_authenticated_service()
    print("✅ 认证成功!")

    # 测试API - 获取频道信息
    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        mine=True
    )
    response = request.execute()

    print("\n频道信息:")
    for channel in response['items']:
        print(f"  频道名: {channel['snippet']['title']}")
        print(f"  订阅数: {channel['statistics']['subscriberCount']}")
        print(f"  视频数: {channel['statistics']['videoCount']}")
```

运行测试：

```bash
python test_youtube_auth.py
```

**预期结果**:
- 浏览器会自动打开Google登录页面
- 登录并授权后，会生成 `token.json` 文件
- 终端显示你的频道信息

### 测试2: 上传简单视频

创建测试脚本 `test_youtube_upload.py`:

```python
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_video(youtube, video_path, title, description):
    """上传视频到YouTube"""

    # 构建视频元数据
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['test', 'upload'],
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus': 'private'  # private, public, unlisted
        }
    }

    # 创建媒体上传对象
    media = MediaFileUpload(
        video_path,
        mimetype='video/*',
        resumable=True,
        chunksize=10 * 1024 * 1024  # 10MB chunks
    )

    # 执行上传
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"开始上传: {title}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"上传进度: {int(status.progress() * 100)}%")

    print(f"✅ 上传完成!")
    print(f"视频ID: {response['id']}")
    print(f"视频链接: https://www.youtube.com/watch?v={response['id']}")

    return response

if __name__ == '__main__':
    # 加载token
    creds = Credentials.from_authorized_user_file('token.json')
    youtube = build('youtube', 'v3', credentials=creds)

    # 上传测试视频
    video_path = './outputs/videos/test_video.mp4'  # 替换为你的视频路径

    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        exit(1)

    upload_video(
        youtube,
        video_path,
        title="测试上传 - 请勿观看",
        description="这是一个API上传测试视频"
    )
```

运行测试：

```bash
python test_youtube_upload.py
```

---

## 🔌 集成到现有系统

### 步骤1: 配置平台

使用API配置YouTube：

```bash
# 首先需要获取access_token和refresh_token
# 运行上面的test_youtube_auth.py后，从token.json中获取

cat token.json
# 会看到类似输出:
# {
#   "token": "ya29.a0AfH6SMB...",
#   "refresh_token": "1//0gH...",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "client_id": "xxx.apps.googleusercontent.com",
#   "client_secret": "xxx",
#   "scopes": ["https://www.googleapis.com/auth/youtube.upload"]
# }
```

然后配置平台：

```bash
curl -X POST http://localhost:8000/api/upload/configure-platform \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "youtube",
    "enabled": true,
    "access_token": "从token.json复制",
    "refresh_token": "从token.json复制",
    "client_id": "从token.json复制",
    "client_secret": "从token.json复制"
  }'
```

### 步骤2: 上传视频

```bash
curl -X POST http://localhost:8000/api/upload/upload \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "./outputs/videos/veo_20231207_123456.mp4",
    "title": "我的第一个AI生成视频",
    "description": "使用AI技术自动生成的视频内容",
    "tags": ["AI", "技术", "创新"],
    "category": "tech",
    "privacy": "private",
    "platforms": ["youtube"]
  }'
```

### 步骤3: 查询上传状态

```bash
# 从上一步的响应中获取task_id
curl http://localhost:8000/api/upload/task/upload_xxx
```

---

## 🎨 使用前端界面

### 步骤1: 启动前端

```bash
cd frontend
npm run dev
```

### 步骤2: 访问上传页面

打开浏览器访问: http://localhost:5173/upload

### 步骤3: 配置YouTube

1. 点击右上角设置图标
2. 按照OAuth流程授权
3. 或者手动输入token信息

### 步骤4: 上传视频

1. 填写视频路径
2. 填写标题、描述、标签
3. 选择YouTube平台
4. 点击"发布到 1 个平台"

---

## 📊 YouTube API配额

### 配额限制

YouTube Data API有每日配额限制：

- **默认配额**: 每天10,000单位
- **上传视频**: 约1,600单位/次
- **每天大约可上传**: 6个视频

### 配额成本

| 操作 | 配额成本 |
|------|---------|
| 上传视频 | 1,600 |
| 插入缩略图 | 50 |
| 查询视频状态 | 1 |
| 列出频道信息 | 1 |

### 增加配额

如果需要更高配额：
1. 访问 [Google Cloud Console](https://console.cloud.google.com)
2. 转到"API和服务" -> "配额"
3. 搜索"YouTube Data API v3"
4. 点击"申请配额增加"
5. 填写申请表单说明用途

---

## 🐛 常见问题

### Q1: "The OAuth client was not found"

**原因**: client_id或client_secret错误

**解决**:
1. 重新检查Google Cloud Console中的凭据
2. 确保正确复制了完整的client_id和client_secret
3. 重新下载client_secret.json

### Q2: "Access blocked: This app's request is invalid"

**原因**: OAuth同意屏幕未正确配置

**解决**:
1. 在Google Cloud Console配置OAuth同意屏幕
2. 添加测试用户（你的Gmail账号）
3. 确保应用处于"测试"状态

### Q3: "The user has not granted the app the permission"

**原因**: 作用域(scope)不正确

**解决**:
1. 确保请求的scope是 `https://www.googleapis.com/auth/youtube.upload`
2. 删除旧的token.json
3. 重新运行授权流程

### Q4: "quotaExceeded"

**原因**: 超过每日配额限制

**解决**:
1. 等到第二天（配额每天重置）
2. 申请增加配额
3. 减少上传频率

### Q5: token.json过期

**原因**: access_token有效期只有1小时

**解决**:
- 使用refresh_token自动刷新
- 我们的实现已自动处理token刷新

---

## 🔐 安全建议

### 1. 保护敏感文件

添加到 `.gitignore`:
```
client_secret.json
token.json
.env
```

### 2. 不要公开分享

- client_secret
- access_token
- refresh_token

这些信息可以完全控制你的YouTube账号！

### 3. 定期轮换密钥

如果怀疑泄露：
1. 在Google Cloud Console删除旧凭据
2. 创建新的OAuth客户端ID
3. 重新授权

---

## 📝 完整工作流程示例

### 场景: 自动上传AI生成的视频

```python
import asyncio
from app.services.upload.manager import upload_manager
from app.services.upload.base import VideoMetadata, Platform, PlatformConfig

async def main():
    # 1. 配置YouTube平台（只需配置一次）
    config = PlatformConfig(
        platform=Platform.YOUTUBE,
        enabled=True,
        access_token="你的access_token",
        refresh_token="你的refresh_token",
        client_id="你的client_id",
        client_secret="你的client_secret"
    )
    upload_manager.configure_platform(config)

    # 2. 准备视频元数据
    metadata = VideoMetadata(
        title="AI生成的风景视频",
        description="""
        这是一个使用AI技术自动生成的风景视频。

        技术栈：
        - Google Veo (视频生成)
        - Gemini (脚本生成)
        - 自动化上传

        #AI #科技 #创新
        """,
        tags=["AI", "人工智能", "视频生成", "科技"],
        category="tech",
        privacy="public"
    )

    # 3. 上传视频
    task = await upload_manager.upload_to_platforms(
        video_path="./outputs/videos/scenic_video.mp4",
        metadata=metadata,
        platforms=[Platform.YOUTUBE]
    )

    # 4. 检查结果
    for result in task.results:
        if result.status == "success":
            print(f"✅ 上传成功!")
            print(f"视频链接: {result.video_url}")
        else:
            print(f"❌ 上传失败: {result.error}")

if __name__ == '__main__':
    asyncio.run(main())
```

---

## 🎯 下一步

YouTube上传功能完成后，可以考虑：

1. **添加缩略图生成**
   - 自动从视频中提取精彩画面
   - 使用AI生成吸引人的缩略图

2. **优化元数据**
   - 自动生成SEO友好的标题
   - 智能标签推荐
   - 最佳发布时间建议

3. **视频管理**
   - 查看视频统计数据
   - 批量编辑视频信息
   - 定时发布功能

4. **多账号支持**
   - 支持多个YouTube频道
   - 账号切换
   - 团队协作

---

## 📚 参考资源

- [YouTube Data API v3 文档](https://developers.google.com/youtube/v3)
- [Python客户端库文档](https://github.com/googleapis/google-api-python-client)
- [OAuth 2.0 完整指南](https://developers.google.com/identity/protocols/oauth2)
- [配额和限制](https://developers.google.com/youtube/v3/getting-started#quota)

---

**✅ 现在你可以开始测试YouTube上传功能了！**

按照上面的步骤一步步来，遇到问题查看FAQ部分。
