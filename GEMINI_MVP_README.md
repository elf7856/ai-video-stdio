# 🎬 Video Creator Platform - Gemini MVP 版本

## ✅ 已完成的功能

### 后端
- ✅ Gemini API集成（LLM服务）
- ✅ 脚本生成API (`/api/scripts/generate`)
- ✅ 脚本优化API (`/api/scripts/optimize`)
- ✅ 分镜生成API (`/api/scripts/generate-shots`)
- ✅ CORS配置完成

### 前端
- ✅ API客户端配置 (`src/api/client.ts`)
- ✅ 类型定义 (`src/api/types.ts`)
- ✅ 脚本API服务 (`src/api/scripts.ts`)
- ✅ Generate页面完整实现
- ✅ 复制功能
- ✅ 导出Markdown功能

---

## 🚀 快速开始

### 1. 更新Google API密钥

**重要：必须先更新有效的API密钥！**

编辑文件：`.env`

```bash
# 替换为你的有效Google API密钥
GOOGLE_API_KEY=your_valid_api_key_here
```

**获取Google API密钥：**
1. 访问：https://aistudio.google.com/app/apikey
2. 创建新的API密钥
3. 复制密钥并粘贴到`.env`文件

---

### 2. 启动后端

```bash
# 激活Python环境（如果有）
# source venv/bin/activate

# 安装依赖（如果还没装）
pip install -r requirements.txt

# 启动后端服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**后端地址：** http://localhost:8000

**API文档：** http://localhost:8000/docs

---

### 3. 启动前端

```bash
cd frontend

# 安装依赖（已完成，如果需要重装）
# npm install

# 启动前端开发服务器
npm run dev
```

**前端地址：** http://localhost:5173

---

## 📱 使用方法

### 生成视频脚本

1. 打开浏览器访问：http://localhost:5173
2. 点击导航栏的 **"Generate"**
3. 填写表单：
   - **视频主题**：例如"如何使用Python进行数据分析"
   - **视频风格**：选择合适的风格（专业/科技/教育等）
   - **目标时长**：设置视频时长（30-300秒）
   - **额外要求**（可选）：添加特殊要求
4. 点击 **"生成脚本"** 按钮
5. 等待30-60秒，AI会生成：
   - ✅ 完整的视频脚本
   - ✅ 详细的分镜方案
   - ✅ 每个镜头的提示词

### 功能操作

- **复制脚本**：点击脚本区域右上角的复制图标
- **复制提示词**：点击每个镜头右侧的复制图标
- **导出完整脚本**：点击右上角"导出完整脚本"按钮，下载Markdown文件

---

## 🧪 测试API

### 测试后端API是否正常

```bash
# 测试Gemini连接
python3 << 'EOF'
from app.services.llm.service import llm_service

result = llm_service.call([
    {'role': 'user', 'content': '你好，请回复OK'}
], provider='google')

print(f"成功: {result['success']}")
print(f"内容: {result['content']}")
print(f"提供商: {result['provider']}")
EOF
```

**预期输出：**
```
成功: True
内容: OK
提供商: google
```

### 测试脚本生成API

```bash
curl -X POST http://localhost:8000/api/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "如何制作咖啡",
    "style": "生活",
    "targetDuration": 60
  }'
```

---

## 📂 项目结构

```
video_creator_platform/
├── app/
│   ├── api/
│   │   └── scripts.py          # ✅ 新增：脚本生成API
│   ├── services/
│   │   └── llm/
│   │       ├── service.py      # LLM服务（Gemini）
│   │       └── adapters/
│   │           └── google_adapter.py  # Google适配器
│   └── main.py                 # ✅ 已更新：注册scripts路由
├── frontend/
│   └── src/
│       ├── api/                # ✅ 新增：API服务层
│       │   ├── client.ts       # axios配置
│       │   ├── types.ts        # TypeScript类型
│       │   ├── scripts.ts      # 脚本API
│       │   └── index.ts        # 统一导出
│       └── pages/
│           └── Generate.tsx    # ✅ 已重写：完整实现
└── .env                        # ⚠️ 需要更新API密钥
```

---

## ⚠️ 常见问题

### 1. 后端报错：API key not valid

**原因**：`.env`中的Google API密钥无效或过期

**解决**：
1. 访问 https://aistudio.google.com/app/apikey
2. 创建新的API密钥
3. 更新`.env`文件中的`GOOGLE_API_KEY`
4. 重启后端服务器

### 2. 前端报错：Network Error

**原因**：后端服务器未启动或端口不对

**解决**：
1. 确认后端运行在 http://localhost:8000
2. 检查终端是否有错误信息
3. 确认CORS已配置

### 3. 生成速度很慢

**正常现象**：AI生成需要30-60秒

**如果超过2分钟**：
- 检查网络连接
- 检查Google API配额是否用完
- 查看后端日志

### 4. 前端连接后端失败

**检查事项**：
- 后端是否在运行（`http://localhost:8000/docs` 能否访问）
- 前端API配置是否正确（`frontend/src/api/client.ts` line 7）
- 浏览器控制台是否有CORS错误

---

## 🎯 下一步计划

### 短期（1-2周）
- [ ] 实现Content页面（历史记录管理）
- [ ] 添加用户注册/登录
- [ ] 添加使用次数限制

### 中期（2-4周）
- [ ] 实现Templates页面（预置模板）
- [ ] 添加脚本编辑功能
- [ ] 优化UI/UX

### 长期（1-2个月）
- [ ] 部署到生产环境
- [ ] 集成支付系统
- [ ] 添加视频生成API（Kling/Runway）

---

## 💡 使用提示

### 如何写好视频主题

**好的例子：**
- ✅ "如何在30天内学会Python编程"
- ✅ "5个提高工作效率的小技巧"
- ✅ "咖啡拉花入门教程"

**不好的例子：**
- ❌ "编程"（太笼统）
- ❌ "教程"（缺少具体内容）
- ❌ "视频"（没有实际主题）

### 选择合适的风格

- **专业**：商业演讲、产品介绍
- **科技**：技术教程、产品评测
- **生活**：日常vlog、美食制作
- **教育**：知识讲解、技能教学
- **娱乐**：搞笑视频、创意短片

### 额外要求示例

- "需要强调产品的三个核心优势"
- "适合初学者，语言要简单易懂"
- "要有悬念，吸引观众看到最后"
- "包含实际案例和数据支持"

---

## 📞 技术支持

如果遇到问题，请检查：

1. **后端日志**：查看终端输出
2. **前端控制台**：浏览器开发者工具 → Console
3. **API文档**：http://localhost:8000/docs

---

## 🎉 完成清单

在运行系统之前，请确认：

- [ ] 已更新有效的Google API密钥
- [ ] 后端服务器正常运行（端口8000）
- [ ] 前端服务器正常运行（端口5173）
- [ ] 可以访问前端页面
- [ ] 测试生成一次脚本成功

**全部完成后，你就有了一个可用的AI视频脚本生成器！** 🎬
