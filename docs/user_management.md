# 用户管理系统文档 (User Management System Documentation)

## 1. 概述 (Overview)

本项目已实现一个基础的用户管理系统，为构建 SaaS 应用提供用户注册、登录、身份验证和授权的基础能力。该系统采用 FastAPI 框架，结合 SQLAlchemy 进行数据持久化，并使用 JWT (JSON Web Token) 进行无状态认证。

**核心功能包括：**
*   用户注册：创建新用户账户。
*   用户登录：通过邮箱和密码获取访问令牌 (Access Token)。
*   身份验证：使用 JWT 验证用户身份。
*   用户信息获取：查询当前登录用户信息或特定用户信息。
*   权限管理：区分普通用户和超级用户 (is_superuser)。
*   SaaS 特性：支持用户会员等级 (tier: free, pro, enterprise)。

## 2. 系统架构 (System Architecture)

| 组件         | 文件路径                        | 职责                                    |
| ------------ | ------------------------------- | --------------------------------------- |
| **数据库模型** | `app/models/user.py`            | 定义 `User` 数据库表结构                |
| **Pydantic Schemas** | `app/schemas/user.py`           | 定义用户相关的请求/响应数据结构和验证规则 |
|              | `app/schemas/token.py`          | 定义 Token 相关的请求/响应数据结构      |
| **核心安全** | `app/core/security.py`          | 密码哈希 (Bcrypt) 和 JWT Token 的生成/验证逻辑 |
| **CRUD 操作** | `app/crud/user.py`              | 封装用户数据的数据库操作 (创建、读取、更新) |
| **API 依赖** | `app/api/deps.py`               | 提供 `get_current_user` 等依赖注入函数，用于验证用户身份和权限 |
| **API 路由** | `app/api/auth.py`               | 包含用户注册、登录、Token 获取等认证相关接口 |
|              | `app/api/users.py`              | 包含获取用户信息、管理员用户管理等接口    |
| **配置**     | `app/core/config.py`            | 配置 JWT Secret Key, 算法和 Token 有效期 |
| **主应用**   | `app/main.py`                   | 集成用户管理路由，确保数据库模型初始化    |

## 3. 数据库结构 (Database Schema)

`app/models/user.py` 中定义的 `User` 模型对应数据库中的 `users` 表。

```python
# app/models/user.py
from sqlalchemy import Boolean, Column, Integer, String, Enum as SAEnum
import enum
from app.utils.database import Base

class UserTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    tier = Column(SAEnum(UserTier), default=UserTier.FREE)
```

**字段说明:** 
*   `id` (Integer): 用户唯一标识符，主键。
*   `email` (String): 用户邮箱，唯一且被索引，用作登录账号。
*   `hashed_password` (String): 加密后的用户密码。
*   `full_name` (String): 用户全名，可选。
*   `is_active` (Boolean): 标识用户账户是否激活，默认为 `True`。
*   `is_superuser` (Boolean): 标识用户是否为超级管理员，默认为 `False`。
*   `tier` (Enum): 用户会员等级，默认为 `UserTier.FREE`。

## 4. 配置 (Configuration)

在 `app/core/config.py` 中，需要设置以下 JWT 相关的环境变量或直接赋值：

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... 其他配置 ...

    # 安全配置
    secret_key: str = "your-secret-key-here-change-in-production" # **重要：生产环境中务必修改为强随机字符串**
    algorithm: str = "HS256" # JWT 加密算法
    access_token_expire_minutes: int = 30 # Access Token 有效期（分钟）

    # ... 其他配置 ...
```

## 5. API 接口 (API Endpoints)

所有接口的响应模型都定义在 `app/schemas/user.py` 和 `app/schemas/token.py` 中。

### 认证接口 (`/auth`)

#### 1. 用户注册 (Register User)

*   **URL:** `/auth/register`
*   **方法:** `POST`
*   **功能:** 创建一个新的用户账户。
*   **请求体:** `application/json`
    ```json
    {
      "email": "newuser@example.com",
      "password": "securepassword123",
      "full_name": "New User Name",
      "is_active": true,
      "is_superuser": false,
      "tier": "free"
    }
    ```
*   **响应 (200 OK):** `application/json`
    ```json
    {
      "email": "newuser@example.com",
      "is_active": true,
      "is_superuser": false,
      "full_name": "New User Name",
      "tier": "free",
      "id": 1
    }
    ```
*   **错误 (400 Bad Request):** 如果邮箱已存在。

#### 2. 用户登录并获取 Access Token

*   **URL:** `/auth/login/access-token`
*   **方法:** `POST`
*   **功能:** 验证用户邮箱和密码，成功后返回 JWT Access Token。
*   **请求体:** `application/x-www-form-urlencoded` (这是 OAuth2PasswordRequestForm 的标准格式)
    ```
    username=newuser@example.com&password=securepassword123
    ```
*   **响应 (200 OK):** `application/json`
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
*   **错误 (400 Bad Request):** 邮箱或密码不正确，或用户未激活。

#### 3. 测试 Access Token

*   **URL:** `/auth/test-token`
*   **方法:** `POST`
*   **功能:** 验证提供的 Access Token 是否有效，并返回当前用户信息。
*   **Header:** `Authorization: Bearer <your_access_token>`
*   **响应 (200 OK):** 返回当前用户信息 (User Schema)。
*   **错误 (403 Forbidden):** Token 无效或缺失。

### 用户管理接口 (`/users`)

这些接口通常需要认证，并且部分可能需要管理员权限。

#### 1. 获取当前登录用户的信息

*   **URL:** `/users/me`
*   **方法:** `GET`
*   **功能:** 获取当前通过 Access Token 认证的用户信息。
*   **Header:** `Authorization: Bearer <your_access_token>`
*   **响应 (200 OK):** 返回当前用户信息 (User Schema)。
*   **错误 (403 Forbidden):** Token 无效或缺失。

#### 2. 获取所有用户列表 (仅限超级管理员)

*   **URL:** `/users/`
*   **方法:** `GET`
*   **功能:** 返回所有注册用户的列表。
*   **Header:** `Authorization: Bearer <your_access_token>`
*   **查询参数:** `skip` (int, default=0), `limit` (int, default=100) 用于分页。
*   **响应 (200 OK):** `application/json` (User Schema 列表)。
*   **错误 (403 Forbidden):** Token 无效或缺失，或用户不是超级管理员。

#### 3. 通过 ID 获取特定用户信息 (仅限超级管理员或自身)

*   **URL:** `/users/{user_id}`
*   **方法:** `GET`
*   **功能:** 通过用户 ID 获取特定用户的信息。普通用户只能获取自己的信息。
*   **Header:** `Authorization: Bearer <your_access_token>`
*   **路径参数:** `user_id` (int)
*   **响应 (200 OK):** 返回指定用户信息 (User Schema)。
*   **错误 (403 Forbidden):** Token 无效或缺失，或用户无权查看该用户信息。
*   **错误 (404 Not Found):** 用户不存在。

#### 4. 创建用户 (仅限超级管理员)

*   **URL:** `/users/`
*   **方法:** `POST`
*   **功能:** 由超级管理员创建新用户账户。
*   **Header:** `Authorization: Bearer <your_access_token>`
*   **请求体:** `application/json` (同 `/auth/register`)
*   **响应 (200 OK):** 返回创建的用户信息。
*   **错误 (403 Forbidden):** Token 无效或缺失，或用户不是超级管理员。
*   **错误 (400 Bad Request):** 邮箱已存在。

## 6. 使用示例 (Usage Example)

首先，确保服务正在运行 (`uvicorn app.main:app --reload`)。

### 步骤 1: 注册一个新用户

```bash
curl -X POST "http://localhost:8000/auth/register" \
-H "Content-Type: application/json" \
-d 
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "New User Name",
  "tier": "free"
}
```

### 步骤 2: 登录并获取 Access Token

```bash
curl -X POST "http://localhost:8000/auth/login/access-token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=newuser@example.com&password=securepassword123"
```
响应示例：
```json
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type":"bearer"}
```
复制 `access_token` 的值，例如 `YOUR_ACCESS_TOKEN`。

### 步骤 3: 访问受保护资源 (获取当前用户信息)

```bash
curl -X GET "http://localhost:8000/users/me" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
响应示例：
```json
{
  "email": "newuser@example.com",
  "is_active": true,
  "is_superuser": false,
  "full_name": "New User Name",
  "tier": "free",
  "id": 1
}
```

### 步骤 4: 尝试以非管理员身份访问管理员接口 (会失败)

```bash
curl -X GET "http://localhost:8000/users/" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
响应示例 (400 Bad Request)：
```json
{"detail":"The user doesn't have enough privileges"}
```
如果需要测试管理员功能，可以在注册时设置 `is_superuser: true`，或者通过数据库手动修改用户。

---
**重要提示**: 生产环境中务必将 `secret_key` 替换为强随机字符串，并考虑使用 HTTPS。
