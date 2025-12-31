# 用户管理系统待实现功能 (User Management TODO)

> 最后更新: 2025-12-17

## 📋 实现计划概览

### ✅ 已完成 (Completed)
- [x] 基础用户认证系统（JWT Token）
- [x] 用户注册和登录
- [x] 会员等级系统（FREE/PRO/ENTERPRISE）
- [x] 管理员权限管理

---

## 🚀 P0 - 正在实现 (In Progress)

### 1. 配额管理系统 (Quota Management System)
**优先级**: 🔴 P0 - 必须立即实现
**状态**: 🔄 进行中
**预计完成**: 2025-12-17

#### 1.1 数据库模型扩展
- [ ] 在 User 模型添加配额相关字段
  - `video_quota`: 每月视频生成配额
  - `video_generated`: 当月已生成视频数
  - `storage_quota_mb`: 存储空间配额（MB）
  - `storage_used_mb`: 已使用存储空间
  - `api_calls_quota`: API 调用配额
  - `api_calls_used`: 已使用 API 调用数
  - `quota_reset_date`: 配额重置日期
  - `created_at`: 账户创建时间
  - `updated_at`: 最后更新时间

#### 1.2 配额中间件
- [ ] 创建配额检查中间件 `app/api/middleware/quota.py`
- [ ] 实现视频生成配额检查
- [ ] 实现存储空间配额检查
- [ ] 实现 API 调用配额检查
- [ ] 配额超限时返回清晰的错误信息

#### 1.3 配额管理 API
- [ ] `GET /users/me/quota` - 查询当前用户配额使用情况
- [ ] `POST /admin/users/{user_id}/quota/reset` - 管理员重置用户配额
- [ ] `PATCH /admin/users/{user_id}/quota` - 管理员调整用户配额

#### 1.4 自动配额重置
- [ ] 创建定时任务每月重置配额
- [ ] 实现按会员等级分配不同配额
  - FREE: 10 videos/month, 1GB storage, 1000 API calls
  - PRO: 100 videos/month, 10GB storage, 10000 API calls
  - ENTERPRISE: 无限制或自定义

#### 1.5 使用统计集成
- [ ] 在视频生成时自动增加计数器
- [ ] 在文件上传时更新存储使用量
- [ ] 在 API 调用时增加计数器

---

## 📅 P1 - 本周实现 (This Week)

### 2. 认证功能完善
**优先级**: 🟡 P1
**预计完成**: 2025-12-18

- [ ] **Token 刷新机制**
  - [ ] 添加 Refresh Token 模型
  - [ ] `POST /auth/refresh` - 刷新 Access Token
  - [ ] 实现 Refresh Token 轮换机制

- [ ] **密码管理**
  - [ ] `POST /auth/forgot-password` - 发送重置密码邮件
  - [ ] `POST /auth/reset-password` - 重置密码
  - [ ] `POST /users/me/change-password` - 修改密码
  - [ ] 集成邮件服务（SendGrid/AWS SES）

- [ ] **用户登出**
  - [ ] `POST /auth/logout` - 登出并撤销 Token
  - [ ] Token 黑名单机制（Redis）

### 3. 使用统计系统
**优先级**: 🟡 P1
**预计完成**: 2025-12-19

- [ ] **创建使用记录模型**
  - [ ] `UserUsageLog` 模型（记录每次操作）
  - [ ] 字段：user_id, action_type, resource_id, cost, timestamp

- [ ] **统计查询 API**
  - [ ] `GET /users/me/statistics` - 查询个人使用统计
    - 本月视频生成数
    - 存储使用情况
    - API 调用统计
    - 成本统计
  - [ ] `GET /users/me/usage-history` - 查询历史使用记录

---

## 📆 P2 - 下个版本 (Next Version)

### 4. 安全增强
**优先级**: 🟢 P2
**预计完成**: 2025-12-24

- [ ] **登录安全**
  - [ ] 登录失败次数限制（5次/15分钟）
  - [ ] IP 封禁机制
  - [ ] 可疑登录通知

- [ ] **两步验证 (2FA)**
  - [ ] TOTP 支持（Google Authenticator）
  - [ ] 备份码生成
  - [ ] `POST /users/me/2fa/enable` - 启用 2FA
  - [ ] `POST /users/me/2fa/verify` - 验证 2FA

- [ ] **审计日志**
  - [ ] `UserAuditLog` 模型
  - [ ] 记录所有敏感操作
  - [ ] `GET /admin/audit-logs` - 查询审计日志

### 5. 会话管理
**优先级**: 🟢 P2
**预计完成**: 2025-12-25

- [ ] **多设备管理**
  - [ ] `UserSession` 模型
  - [ ] `GET /users/me/sessions` - 查看所有活跃会话
  - [ ] `DELETE /users/me/sessions/{session_id}` - 撤销特定会话
  - [ ] `DELETE /users/me/sessions/all` - 撤销所有其他会话

### 6. 邮箱验证
**优先级**: 🟢 P2
**预计完成**: 2025-12-26

- [ ] 注册后发送验证邮件
- [ ] `GET /auth/verify-email?token=xxx` - 验证邮箱
- [ ] `POST /auth/resend-verification` - 重新发送验证邮件
- [ ] 未验证用户限制功能使用

---

## 🎨 P3 - 未来改进 (Future)

### 7. 前端集成
- [ ] 登录页面
- [ ] 注册页面
- [ ] 用户中心仪表板
- [ ] 配额使用可视化
- [ ] 使用统计图表

### 8. 高级功能
- [ ] OAuth 第三方登录（Google, GitHub）
- [ ] 团队/组织管理
- [ ] API Key 管理
- [ ] Webhook 配置
- [ ] 导出个人数据（GDPR）

---

## 📊 技术债务 (Technical Debt)

- [ ] 添加数据库迁移脚本（Alembic）
- [ ] 添加单元测试覆盖
- [ ] 添加集成测试
- [ ] API 文档完善（OpenAPI/Swagger）
- [ ] 性能优化（数据库索引）
- [ ] 监控和告警

---

## 📝 实现进度追踪

| 功能模块 | 状态 | 开始时间 | 完成时间 | 负责人 |
|---------|------|----------|----------|--------|
| 配额管理系统 | 🔄 进行中 | 2025-12-17 | - | Claude |
| Token 刷新 | ⏸️ 待开始 | - | - | - |
| 密码管理 | ⏸️ 待开始 | - | - | - |
| 使用统计 | ⏸️ 待开始 | - | - | - |

---

## 🔗 相关文档

- [用户管理系统文档](./user_management.md) - 已实现功能的详细文档
- [API 参考](./api_reference.md) - API 接口文档
