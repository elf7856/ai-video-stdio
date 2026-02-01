# 解决 Vite 构建错误：@webav 模块无法解析

## 问题描述

在 Vercel/Railway 等部署平台构建时，可能遇到以下错误：

```
[vite]: Rollup failed to resolve import "@webav/av-canvas" from "/path/frontend/src/hooks/useAVCanvas.ts".
This is most likely unintended because it can break your application at runtime.
```

## 原因

`@webav` 包虽然安装在 `node_modules` 中，但没有在 `package.json` 的 `dependencies` 中声明，导致：
1. TypeScript 类型检查通过（因为有 `webav.d.ts` 类型声明）
2. 但 Vite 打包时无法找到实际的模块

## 解决方案

### 已修复 ✅

在最新的提交中，已经将 `@webav` 包添加到 `package.json`：

```json
{
  "dependencies": {
    "@webav/av-canvas": "^1.2.8",
    "@webav/av-cliper": "^1.2.8",
    "@webav/av-recorder": "^1.2.8",
    "mp4box": "^2.3.0"
  }
}
```

### 如果仍然遇到问题

#### 1. 拉取最新代码

```bash
git pull origin main
# 或
git pull origin dev
```

#### 2. 重新安装依赖

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 3. 本地测试构建

```bash
npm run build
```

#### 4. 如果遇到 npm 权限问题

```bash
# macOS/Linux
sudo chown -R $(whoami) ~/.npm

# 或者清理缓存
npm cache clean --force
```

## 部署平台配置

### Vercel

Vercel 会自动：
1. 检测到 `package.json`
2. 运行 `npm install`
3. 运行 `npm run build`

**无需额外配置**，只要 `package.json` 正确即可。

### Railway

Railway 使用 Dockerfile 构建前端：

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建
RUN npm run build
```

**无需额外配置**，Dockerfile 会自动安装所有依赖。

### Netlify

在 `netlify.toml` 中配置：

```toml
[build]
  base = "frontend"
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "20"
```

## 验证修复

### 本地验证

```bash
cd frontend

# 1. 检查包是否在 package.json 中
grep "@webav" package.json

# 应该看到：
# "@webav/av-canvas": "^1.2.8",
# "@webav/av-cliper": "^1.2.8",
# "@webav/av-recorder": "^1.2.8",

# 2. 检查包是否已安装
npm list @webav/av-canvas

# 应该看到：
# @webav/av-canvas@1.2.8

# 3. 运行构建
npm run build

# 应该成功构建，没有 "Rollup failed to resolve import" 错误
```

### 部署平台验证

1. **推送代码到 GitHub**
   ```bash
   git push origin main
   ```

2. **触发重新部署**
   - Vercel: 自动触发
   - Railway: 自动触发
   - Netlify: 自动触发

3. **查看构建日志**
   - 确认 `npm install` 成功
   - 确认 `npm run build` 成功
   - 没有 Rollup 错误

## 相关文件

- `frontend/package.json` - 依赖声明
- `frontend/src/types/webav.d.ts` - TypeScript 类型声明
- `frontend/src/hooks/useAVCanvas.ts` - 使用 @webav 的主要文件

## 技术说明

### 为什么需要两个文件？

1. **package.json** - 告诉 npm/Vite 需要安装哪些包
2. **webav.d.ts** - 告诉 TypeScript 这些包的类型定义

两者缺一不可：
- 只有 `package.json`：TypeScript 类型检查失败
- 只有 `webav.d.ts`：Vite 打包失败（当前问题）

### @webav 包说明

- **@webav/av-canvas**: 视频画布渲染引擎
- **@webav/av-cliper**: 视频剪辑核心库
- **@webav/av-recorder**: 视频录制功能
- **mp4box**: MP4 文件解析库（@webav 的依赖）

这些包用于实现专业的视频编辑器功能，包括：
- 多轨道时间线
- 实时视频预览
- 帧级精确控制
- 视频合成和导出

## 故障排查

### 问题 1: 构建时仍然报错

**检查**:
```bash
cat frontend/package.json | grep "@webav"
```

**如果没有输出**，说明 package.json 没有更新：
```bash
git pull origin main
cd frontend
npm install
```

### 问题 2: npm install 失败

**错误**: `EACCES: permission denied`

**解决**:
```bash
sudo chown -R $(whoami) ~/.npm
npm cache clean --force
npm install
```

### 问题 3: 类型错误

**错误**: `Cannot find module '@webav/av-canvas'`

**检查**:
```bash
ls frontend/src/types/webav.d.ts
```

**如果文件不存在**：
```bash
git pull origin main
```

## 总结

✅ **已修复**: `@webav` 包已添加到 `package.json`
✅ **已推送**: main 和 dev 分支都已更新
✅ **已测试**: 本地构建成功

**下次部署时应该不会再出现此错误！** 🎉
