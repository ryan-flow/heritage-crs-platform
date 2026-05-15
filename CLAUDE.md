# 非遗文化传播系统 (Heritage CRS Platform) — CLAUDE.md

## 项目概述
基于 CRS 推荐与 AI 数字人的非遗文化传播系统（毕业设计）。
- **Backend**: Python Flask/FastAPI + AI（豆包 TTS + DeepSeek 对话）+ CRS 推荐 + 知识图谱
- **Frontend**: 微信小程序 (`frontend/`) + React Web 端 (`frontend-web/`)
- **Database**: SQLite (`heritage_platform.db` / `knowledge_graph.db`)
- **Deploy**: Docker / Railway / Render / Tencent CloudBase

## 目录结构
| 路径 | 用途 |
|---|---|
| `backend/app/` | Flask/FastAPI 主应用代码 |
| `backend/crawler/` | 数据爬虫 |
| `backend/storage/` | 文件存储 |
| `backend/tools/` | 辅助工具脚本 |
| `backend/scripts/` | 运维脚本 |
| `frontend/miniprogram/` | 微信小程序前端 |
| `frontend-web/src/` | React Web 前端（Vite + TypeScript） |
| `database/` | 数据库文件 |
| `docs/` | 论文文档、参考文献 |

## AI 服务
- **豆包 (Doubao)**: TTS 语音合成 (`DOUBAO_TTS_APPID`, `DOUBAO_TTS_ACCESS_TOKEN`) + 对话 (`DOUBAO_API_KEY`)
- **DeepSeek**: 对话/分析 (`DEEPSEEK_API_KEY`)
- 凭据位置：`backend/.env`（详见凭据索引 memory）

## 常用命令
- 启动后端：`cd backend && python -m app` 或 `docker-compose up`
- 启动 Web 前端：`cd frontend-web && npm run dev`
- 微信小程序：用微信开发者工具打开 `frontend/` 目录

## 部署配置
- `backend/Dockerfile` + `docker-compose.yml` — Docker 部署
- `backend/railway.json` — Railway 部署
- `backend/render.yaml` — Render 部署
- `backend/cloudbaserc.json` + `cloudbase.yaml` — 腾讯云 CloudBase 部署

## Python 环境
- 使用 Conda 环境 `flask_dev`（`~/.conda/envs/flask_dev`）
- 或主 Python 3.11.8 + `backend/requirements.txt`
