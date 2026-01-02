# Google Veo API 配额指南

## 问题说明

你遇到的 `429 RESOURCE_EXHAUSTED` 错误**不是因为赠金用完了**，而是触发了 **API 速率限制 (Rate Limit)**。

## 配额类型

### 1. 速率限制 (Rate Limits)
- **每分钟请求数 (RPM)**: 免费层为 **2 RPM**
- **每天请求数 (RPD)**: 免费层为 **50 RPD**

### 2. 使用量限制
- 你的赠金额度
- 计费账户余额

## 查看配额的方法

### 方法1: 运行检查脚本
```bash
python check_api_quota.py
```

### 方法2: 访问在线仪表板
1. **API Key 管理**: https://aistudio.google.com/apikey
   - 查看你的 API Key
   - 查看使用统计

2. **配额文档**: https://ai.google.dev/gemini-api/docs/rate-limits
   - 了解不同模型的配额限制

3. **Google Cloud Console**: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
   - 查看详细的配额使用情况
   - 申请配额提升

4. **计费信息**: https://console.cloud.google.com/billing
   - 查看赠金余额
   - 查看账单详情

## 已实施的解决方案

### 自动速率限制保护

代码已更新，新增以下功能：

1. **请求间延迟**
   - 每个视频生成请求之间自动等待 35 秒
   - 避免触发 RPM=2 的限制

2. **自动重试机制**
   - 遇到 429 错误时，等待 60 秒后自动重试一次
   - 提高生成成功率

3. **详细日志**
   ```
   [task_xxx] ⏳ 等待 35秒 以避免触发速率限制...
   [task_xxx] ⚠️ 触发速率限制，等待60秒后重试...
   ```

## 使用建议

### 免费层用户
- ✅ **减少镜头数量**: 建议 3-4 个镜头/视频
- ✅ **分批生成**: 不要一次性生成太多视频
- ✅ **使用脚本预览**: 先生成脚本确认，再生成视频

### 升级到付费层
如果需要更高的配额，可以：
1. 设置计费账户: https://console.cloud.google.com/billing
2. 配额会自动提升到:
   - RPM: 1,000+
   - 无每日限制

## 时间估算

### 免费层 (RPM=2)
生成 8 个镜头视频的时间：
- 每个镜头: ~70 秒生成 + 35 秒等待 = 105 秒
- 8 个镜头: 8 × 105 = **约 14 分钟**

### 付费层 (RPM=1000)
生成 8 个镜头视频的时间：
- 每个镜头: ~70 秒（可并行）
- 8 个镜头: **约 2-3 分钟**

## 错误类型对照

| 错误代码 | 错误信息 | 原因 | 解决方案 |
|---------|---------|------|---------|
| 429 | RESOURCE_EXHAUSTED | 触发速率限制 (RPM/RPD) | 等待后重试，或升级计划 |
| 403 | PERMISSION_DENIED | API Key 无效或无权限 | 检查 API Key 配置 |
| 400 | INVALID_ARGUMENT | 请求参数错误 | 检查提示词和参数 |

## 监控你的使用情况

### 实时检查
```bash
# 运行检查脚本
python check_api_quota.py

# 查看最近的任务
ls -lht outputs/tasks/ | head -5

# 查看任务详情
cat outputs/tasks/task_xxx.json | python -m json.tool
```

### 统计使用量
```bash
# 统计今天生成的视频数量
find outputs/videos -name "*.mp4" -mtime -1 | wc -l

# 查看今天的总成本
python -c "
import json, glob
tasks = glob.glob('outputs/tasks/*.json')
total_cost = 0
for task in tasks:
    with open(task) as f:
        data = json.load(f)
        for v in data.get('generatedVideos', []):
            if v['status'] == 'success':
                total_cost += v.get('cost', 0)
print(f'总成本: \${total_cost:.2f}')
"
```

## 常见问题

### Q: 为什么我有赠金还是报错？
A: 赠金充足 ≠ 无速率限制。免费层依然有 RPM=2 的限制。

### Q: 如何提升速率限制？
A: 设置计费账户后，配额会自动提升到付费层标准。

### Q: 等待时间能缩短吗？
A: 免费层必须遵守 RPM=2 限制。升级到付费层后可以并行生成。

### Q: 今天用完了 RPD=50，明天会重置吗？
A: 是的，每日配额会在 UTC 00:00 重置。

## 总结

✅ **你的赠金没问题** - API 测试调用成功
⚠️ **问题是速率限制** - 免费层 RPM=2
✨ **已自动修复** - 代码已添加智能延迟和重试机制

现在你可以继续生成视频了，系统会自动处理速率限制问题！
