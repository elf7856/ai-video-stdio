# 文档说明

## 核心文档（必读）

### 1. `PROJECT_STATUS.md` - 项目状态总览
- **用途**: 查看整体进度和模块完成情况
- **更新**: 每次新增功能后更新
- **阅读时间**: 3 分钟

### 2. `EDITOR_SPEC.md` - 视频编辑器技术规范
- **用途**: 编辑器模块开发的核心技术文档
- **包含**: 数据模型、API、代码示例
- **阅读时间**: 10 分钟
- **适用**: 直接用于编码，无冗余内容

### 3. `api_reference.md` - API 接口文档
- **用途**: 现有 API 的使用说明
- **适用**: 前端开发、API 调用

---

## 参考文档（可选）

- `guide.md` - 使用指南
- `image_generation.md` - 图像生成说明

---

## 归档文档 (`archive/`)

所有规划、分析、详细设计文档已移至 `archive/` 目录：
- 这些文档包含大量背景分析和决策过程
- 开发时**不需要阅读**
- 仅供参考或了解决策背景时查看

归档文档列表：
- `video_editor_detailed_design.md` (2001行) - 详细设计全文档
- `opencut_integration_analysis.md` (783行) - OpenCut 分析
- `video_editing_tech_stack_coverage.md` (786行) - 技术栈覆盖分析
- `development_cost_analysis.md` (648行) - 成本分析
- `web_architecture_analysis.md` (508行) - 架构分析
- 其他历史文档...

---

## 文档原则

### ✅ 好的文档
- 简洁（< 500 行）
- 直接可用于开发
- 只包含必要的技术细节
- 及时更新

### ❌ 避免的文档
- 超长（> 1000 行）
- 过多的背景分析
- 重复的内容
- 过时的计划

---

## 快速导航

**我想...**
- 了解项目整体状态 → `PROJECT_STATUS.md`
- 开发编辑器功能 → `EDITOR_SPEC.md`
- 调用现有 API → `api_reference.md`
- 了解决策背景 → `archive/` 目录
