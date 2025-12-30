# 视频创作平台 - 前端

这是一个基于 Vue 3 + TypeScript + Element Plus 的视频创作平台前端项目。

## 🚀 技术栈

- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全的JavaScript超集
- **Element Plus** - Vue 3的UI组件库
- **Vue Router** - Vue.js官方路由管理器
- **Axios** - HTTP客户端
- **Vite** - 下一代前端构建工具

## 📦 安装依赖

```bash
# 安装Node.js (如果还没有安装)
# 从 https://nodejs.org/ 下载并安装

# 安装项目依赖
npm install
```

## 🛠️ 开发

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 类型检查
npm run type-check
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/          # 公共组件
│   │   ├── NavBar.tsx      # 导航栏组件
│   │   └── NavBar.css      # 导航栏样式
│   ├── views/              # 页面组件
│   │   ├── Home.tsx        # 首页
│   │   ├── Home.css        # 首页样式
│   │   ├── VideoDownload.tsx # 视频下载页
│   │   ├── VideoDownload.css # 视频下载页样式
│   │   ├── VideoList.tsx   # 视频列表页
│   │   ├── VideoList.css   # 视频列表页样式
│   │   ├── VideoEdit.tsx   # 视频编辑页
│   │   └── VideoEdit.css   # 视频编辑页样式
│   ├── services/           # API服务
│   │   └── api.ts          # API接口
│   ├── types/              # TypeScript类型定义
│   │   └── index.ts        # 类型定义
│   ├── router/             # 路由配置
│   │   └── index.ts        # 路由定义
│   ├── App.tsx             # 主应用组件
│   ├── App.css             # 主应用样式
│   └── main.ts             # 应用入口
├── index.html              # HTML模板
├── package.json            # 项目配置
├── tsconfig.json           # TypeScript配置
├── vite.config.ts          # Vite配置
└── README.md               # 项目说明
```

## 🌟 特性

- **纯TypeScript** - 所有组件都使用TypeScript编写
- **JSX语法** - 使用JSX语法编写Vue组件
- **类型安全** - 完整的TypeScript类型定义
- **响应式设计** - 适配不同屏幕尺寸
- **模块化样式** - 每个组件都有独立的CSS文件

## 🔧 配置说明

### 开发环境
- 开发服务器运行在 `http://localhost:3000`
- API代理到 `http://localhost:8000`

### 生产环境
- 构建后的文件在 `dist/` 目录
- 需要配置后端API地址

## 📝 使用说明

1. **视频下载** - 支持URL直接下载和Cookies下载
2. **视频列表** - 查看已下载的视频
3. **视频编辑** - 使用自然语言编辑视频

## 🚀 部署

```bash
# 构建生产版本
npm run build

# 部署dist目录到Web服务器
```

## �� 许可证

MIT License 