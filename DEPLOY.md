# 非遗文化传播系统 — 部署指南

## 快速开始（Docker Compose — 推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/oldking-yes/heritage-crs-platform.git
cd heritage-crs-platform/backend

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env, 填入 DOUBAO_API_KEY / DOUBAO_TTS_APPID / DOUBAO_TTS_ACCESS_TOKEN
# DATABASE_URL 默认指向本地 Docker PostgreSQL，无需修改

# 3. 一键启动（PostgreSQL + 后端 API）
docker compose up --build

# 4. 验证
curl http://localhost:8000/
# → {"message":"China Intangible Cultural Heritage Platform API running"}
```

## 本地开发（无 Docker）

```bash
# 需要本地有可访问的 PostgreSQL 实例，设置 DATABASE_URL 环境变量
export DATABASE_URL=postgresql://heritage:heritage123@localhost:5432/heritage

# 后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend-web
npm install
npm run dev
```

## 数据库

PostgreSQL 16。`DATABASE_URL` 环境变量指定连接串。

| 环境 | 数据库地址 |
|------|-----------|
| Docker Compose | `postgresql://heritage:heritage123@postgres:5432/heritage`（自动） |
| 本地开发 | 自行设置 `DATABASE_URL` |
| 生产（云） | 托管 PostgreSQL（Supabase / Railway / Aiven）|

## 部署到云平台

### Railway

```bash
# Railway 会自动识别 railway.json
# 需在 Railway Dashboard 设置以下环境变量：
# - DATABASE_URL: Railway 提供的 PostgreSQL URL
# - DOUBAO_API_KEY
# - DOUBAO_TTS_APPID
# - DOUBAO_TTS_ACCESS_TOKEN
# - ADMIN_TOKEN（自动生成）
```

### Supabase（数据库托管）

1. 在 [supabase.com](https://supabase.com) 创建项目
2. 获取数据库连接字符串（Project Settings → Database → Connection string）
3. 设置环境变量 `DATABASE_URL` 为上一步的值

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | 否 | PostgreSQL 连接串，不设则用 SQLite |
| `DOUBAO_API_KEY` | 是 | 豆包大模型 API Key |
| `DOUBAO_TTS_APPID` | 是 | 豆包语音合成 APP ID |
| `DOUBAO_TTS_ACCESS_TOKEN` | 是 | 豆包语音合成 Access Token |
| `ADMIN_TOKEN` | 否 | 管理后台 Token，默认 DFY7-... |
| `ADMIN_USERNAME` | 否 | 管理员用户名（默认 admin） |
| `ADMIN_PASSWORD` | 否 | 管理员密码（默认 admin123） |

## 架构图

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  React Web   │────▶│  FastAPI Backend │────▶│  PostgreSQL  │
│  (Vite + TS) │     │  (uvicorn)       │     │  (pg 16)     │
└──────────────┘     └──────────────────┘     └──────────────┘
                           │
                     ┌─────┴──────┐
                     │            │
              ┌──────┴──┐  ┌─────┴─────┐
              │ DeepSeek │  │ 豆包 TTS  │
              │ 对话 AI  │  │  语音合成  │
              └─────────┘  └───────────┘
```
