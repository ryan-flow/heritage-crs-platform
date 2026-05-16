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

## Frontend Web 设计系统

### 技术栈
- React 19 + TypeScript + Vite 8
- Tailwind CSS v4（`@theme` 指令定义设计 token，无 tailwind.config.js）
- React Router 7 + TanStack Query 5 + Zustand 5
- Lucide React 图标库

### 设计 Token（定义于 `frontend-web/src/index.css`）
- **品牌色**: 朱砂红 `#9f2d22` (brand), 鎏金 `#c08a3e` (accent), 翠玉绿 `#5b8c5a` (jade)
- **文字色**: 墨色 `#2c2416` (ink), 次墨色 `#5a4430`, 淡墨色 `#8b6a4b`
- **背景**: 宣纸色 `#fdf8f0` (parchment)
- **字体**: 衬线 `Noto Serif SC` / 无衬线 `Noto Sans SC`
- **圆角**: card=28px, hero=36px, pill=999px

### 核心组件
- `GlassCard` — 毛玻璃卡片 (elevated/hover 变体)
- `InkButton` — 水墨按钮 (primary/outline/ghost 变体)
- `SealBadge` — 印章徽章 (cinnabar/gold/jade 颜色)
- `PageTransition` — 页面入场动画包装器
- `DigitalHumanModel` — CSS 绘制黑塔数字人（含情绪驱动动画）

### 微交互动画系统
- `.animate-fade-in-up` — 上滑淡入（0.5s cubic-bezier）
- `.fade-in` / `.fade-in-delay-1/2/3` — 纯淡入 + 延迟变体
- `.rise-in-stagger` — 子元素交错入场
- `.card-interactive` — 可交互卡片 hover lift + active press
- `.guofeng-press` — 国风按压反馈（scale 0.97）
- `.quick-entry-btn` — 快捷入口 hover/active 动效
- `.ping-slow` — 慢速 ping 装饰
- `.breathe-ring` / `.hero-cta-breathe` — 呼吸光环
- `@keyframes fadeInUp, riseIn, breathe, breatheRing, ping`

### 设计原则
1. 所有交互元素必须有 hover + active 反馈
2. 区块之间使用交错入场动画（staggered entrance）
3. 优先使用 `@theme` 设计 token，避免硬编码颜色
4. 图片使用 `loading="lazy"` 懒加载
5. 移动端优先，`max-w-[480px]` 居中，md 断点做桌面适配

## Python 环境
- 使用 Conda 环境 `flask_dev`（`~/.conda/envs/flask_dev`）
- 或主 Python 3.11.8 + `backend/requirements.txt`
