# 🎬 AI Video Creator & NLE Platform

> **AI 驱动的端到端视频创作平台**：从创意构思、AI 导演、Google Veo 视频生成，到基于 Web 的专业非线性编辑（NLE），一站式完成。

![Status](https://img.shields.io/badge/Status-Beta-blue)
![Python](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.12-green)
![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20MUI-blue)
![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED)

## ✨ 核心特性 (Key Features)

### 1. 🤖 AI 导演工作流 (AI Director Workflow)
*   **智能脚本创作**：输入一个简短的主题（Topic），AI 自动生成分镜头脚本、提示词和时长规划。
*   **交互式分镜确认**：在生成视频前，先生成静态分镜图（Storyboard）。用户确认画面风格一致性后，再进行视频渲染。
*   **图生视频 (Image-to-Video)**：深度集成 **Google Gemini Veo** 模型，严格基于分镜图生成动态视频，确保画面连贯性。

### 2. 🎞️ 专业级网页编辑器 (Web NLE Studio)
*   **非线性时间轴 (Timeline)**：支持缩放（Zoom）、拖拽、多片段拼接。
*   **实时预览引擎**：基于全局时间轴的实时预览，点击时间尺任意跳转。
*   **胶卷视图 (Filmstrip)**：底栏显示真实的视频逐帧缩略图，剪辑更精准。
*   **非破坏性编辑**：
    *   **Trimming**：调整镜头时长，只播放精华片段。
    *   **Filters**：实时滤镜（复古、黑白、冷暖色调）。
    *   **Transitions**：镜头间转场效果（淡入淡出、溶解等）。

### 3. 🛠️ 稳健的后端架构
*   **项目制管理**：所有素材（视频、图片、音频）自动归档到 `projects/` 目录，持久化存储。
*   **自动时长校准**：生成时自动探测视频真实时长，拒绝虚假进度条。
*   **容错机制**：前端预览失败自动降级，后端生成失败自动重试。

---

## 🚀 快速开始 (Quick Start)

### 方式一：使用 Docker (推荐)

最简单的运行方式。确保本地已安装 Docker 和 Docker Compose。

1.  **配置环境变量**
    ```bash
    cp .env.example .env
    # 编辑 .env 文件，填入你的 GOOGLE_API_KEY
    ```

2.  **构建并启动**
    ```bash
    docker-compose up --build -d
    ```

3.  **访问应用**
    打开浏览器访问 `http://localhost:80`

### 方式二：本地开发 (Manual Setup)

#### 后端 (Backend)

1.  安装依赖 (推荐使用 Python 3.10+)
    ```bash
    pip install -r requirements.txt
    ```
2.  初始化数据库
    ```bash
    alembic upgrade head
    ```
3.  启动服务
    ```bash
    python -m uvicorn app.main:app --reload --port 8000
    ```

#### 前端 (Frontend)

1.  进入前端目录
    ```bash
    cd frontend
    ```
2.  安装依赖
    ```bash
    npm install
    # 或
    pnpm install
    ```
3.  启动开发服务器
    ```bash
    npm run dev
    ```
4.  访问 `http://localhost:3000`

---

## 📂 项目结构 (Project Structure)

```
.
├── app/
│   ├── api/            # API 路由 (Endpoints)
│   ├── core/           # 全局配置 (Config & Security)
│   ├── models/         # 数据库模型 (SQLAlchemy)
│   ├── services/       # 核心业务逻辑
│   │   ├── video_generation/  # AI 视频生成编排 (Orchestrator)
│   │   ├── video/             # 视频处理 (MoviePy)
│   │   └── image/             # 图片生成
│   └── main.py         # 入口文件
├── frontend/
│   ├── src/
│   │   ├── components/ # UI 组件 (Timeline, PreviewPanel)
│   │   ├── pages/      # 页面 (Generate, Editor)
│   │   ├── stores/     # 状态管理 (Zustand)
│   │   └── utils/      # 工具函数 (URL handling)
├── alembic/            # 数据库迁移脚本
├── outputs/            # 生成产物 (挂载卷)
│   └── projects/       # 按项目归档的素材
└── docker-compose.yml
```

## ⚠️ 注意事项

*   **API Key**: 必须配置有效的 `GOOGLE_API_KEY` 才能使用视频生成功能。
*   **网络环境**: 确保你的服务器可以访问 Google Gemini API。
*   **存储**: 在 Docker 模式下，`outputs/` 目录已挂载到宿主机，重启容器数据不会丢失。

## 📝 License

MIT
