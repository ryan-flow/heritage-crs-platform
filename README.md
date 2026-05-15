# 中国非遗文化数字平台

**基于CRS推荐与AI数字人的非遗文化传播系统** — 王子轩 大数据222 仲恺农业工程学院

- **小程序前端**：微信小程序原生开发（WeChat Mini Program）
- **Web 前端**：React 19 + TypeScript + Vite + Tailwind CSS（[frontend-web/](frontend-web/)）
- **后端**：Python + FastAPI + SQLAlchemy
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **AI 模块**：本地知识库检索 + 豆包大模型 + 联网搜索兜底 + TTS 语音合成
- **推荐系统**：CRS（对话式推荐系统）三维置信度状态机 + 多信号融合排序

## 目录结构
frontend/miniprogram/
├── app.js                       全局入口（app.globalData）
├── app.json                     页面路由注册
├── app.wxss                     全局样式
│
├── pages/                       页面目录
│   ├── auth/login/              登录页
│   │
│   ├── user/                    用户端页面
│   │   ├── home/                首页 ⭐
│   │   ├── ai/                  AI数字人对话页 ⭐ 1545行
│   │   ├── profile/             个人中心+画像展示
│   │   ├── content/             内容列表 + detail/内容详情
│   │   ├── activity/            活动列表 + detail/详情 + register/报名
│   │   ├── discussion/          社区列表 + detail/帖子详情
│   │   ├── preferences/         偏好设置
│   │   ├── culture/             非遗文化
│   │   ├── history/             浏览历史
│   │   └── places/              非遗场馆
│   │
│   └── admin/                   管理端页面
│       ├── dashboard/           数据看板
│       ├── content-manage/      内容管理
│       ├── activity-manage/     活动管理
│       ├── topic-manage/        帖子管理
│       └── user-manage/         用户管理
│
├── components/                  复用组件
│   ├── digital-human/           数字人黑塔组件
│   └── digital-human-model/     数字人3D模型组件
│
├── custom-tab-bar/              自定义底部导航栏
│
├── utils/                       工具模块
│   ├── request.js               HTTP请求封装
│   ├── digital-human.js         数字人行为逻辑
│   ├── media.js                 图片URL转换
│   └── auth.js                  认证工具
│
└── styles/theme.wxss            主题样式变量
frontend-web/                    Web 前端（React + Vite）
├── src/
│   ├── App.tsx                  路由定义（21 条路由）
│   ├── main.tsx                 入口（QueryClient + BrowserRouter）
│   ├── lib/api.ts               API 封装 + 图片 URL 构建
│   ├── stores/                  状态管理（auth-store, chat-store）
│   ├── components/
│   │   ├── layout/              AppLayout（含 TabBar）+ AdminLayout
│   │   ├── digital-human/       数字人组件（表情 + 语音）
│   │   └── recommend/           推荐卡片组件
│   └── pages/                   21 个页面（完整覆盖小程序功能）
│       ├── auth/                登录/注册
│       ├── home/                首页推荐流
│       ├── ai/                  AI 数字人对话 ⭐
│       ├── content/             内容列表 + 详情
│       ├── activity/            活动列表 + 详情 + 报名
│       ├── discussion/          社区列表 + 详情
│       ├── profile/             个人中心
│       ├── preferences/         偏好设置
│       ├── places/              非遗场馆
│       ├── history/             浏览历史
│       ├── culture/             非遗文化 + 详情
│       └── admin/               管理后台（5 页面）
│
backend/
├── main.py                      启动入口：uvicorn 从这里启动
│
├── app/
│   ├── core/                    核心配置层
│   │   ├── config.py            数据库路径、豆包API密钥、系统提示词
│   │   ├── database.py          SQLAlchemy 连接引擎
│   │   └── responses.py         统一返回格式 {code, message, data}
│   │
│   ├── models/                  数据模型层（16张表的ORM定义）
│   │   ├── user.py              用户表
│   │   ├── content.py           非遗内容表
│   │   ├── activity.py          线下活动表
│   │   ├── discussion_topic.py  社区帖子表
│   │   ├── recommend_log.py     推荐行为日志表
│   │   ├── crs_session.py       CRS会话表
│   │   ├── crs_ask_log.py       CRS提问记录表
│   │   ├── ai_qa_log.py         AI问答记录表
│   │   ├── local_knowledge_base.py  本地知识库表
│   │   └── ...                  其他模型
│   │   
│   │
│   ├── api/v1/                  接口层（路由+端点）
│   │   ├── router.py            总路由：把所有子路由注册到 app
│   │   └── endpoints/           12个端点文件
│   │       ├── ai.py            /ai/chat、/ai/crs/state、/ai/crs/answer
│   │       ├── recommend.py     /recommend/feed、/recommend/track
│   │       ├── content.py       /content/* 内容CRUD
│   │       ├── event.py         /activity/* 活动CRUD
│   │       ├── discussion.py    /discussion/* 社区CRUD
│   │       ├── auth.py          /auth/* 登录认证
│   │       ├── user.py          /user/* 用户信息
│   │       ├── kg.py            /kg/* 知识图谱查询
│   │       ├── admin.py         /admin/* 管理端接口
│   │       ├── stats.py         /stats/* 统计数据
│   │       └── material.py      /material/* 电子资料
│   │       命名：每个文件对应一个业务域
│   │
│   ├── services/                业务服务层（核心逻辑）
│   │   ├── ai_service.py         AI问答主入口 
│   │   │                         职责：接收问题→搜知识库→调豆包→跑CRS→生成推荐→返回
│   │   ├── recommendation_service.py  推荐引擎 
│   │   │                         职责：画像构建、置信度计算、内容排序打分
│   │   ├── knowledge_graph.py    知识图谱服务 
│   │   │                         职责：相似实体、扩展推荐、最短路径
│   │   ├── knowledge_base.py     本地知识库检索
│   │   ├── doubao_client.py      豆包大模型API调用
│   │   ├── tts_service.py        TTS语音合成（三级降级）
│   │   ├── web_search_service.py 联网搜索兜底
│   │   ├── content_governance.py 内容质量检查
│   │   └── display_enrichment.py 前端展示层数据加工
│   │
│   │   └── crs/                  CRS子系统（8个文件）
│   │       ├── decision.py       五策略决策引擎 
│   │       ├── mappings.py       6个偏好映射字典 
│   │       ├── preference.py     偏好同步4条路径
│   │       ├── ask_templates.py  13套ASK提问模板
│   │       ├── session.py        会话管理+ASK回答处理
│   │       ├── questions.py      推荐问题生成
│   │       └── constants.py      阈值、术语列表
│   │       
│   │
│   └── web/
│       └── admin.html            Web管理端（单文件SPA）
│
├── scripts/                     数据库脚本
│   ├── seed_recommendation_content_pack.py  种子数据生成
│   ├── import_*.py              知识库批量导入
│   ├── rebuild_*.py             数据重建脚本
│   └── ...                      其他工具脚本
│
├── crawler/                     非遗内容爬虫模块
├── tests/                       测试文件
├── storage/covers/              封面图片存储
├── docs/                        文档
└── *.db                         数据库文件
- `backend`：FastAPI 后端服务
- `backend/crawler`：非遗图文采集与清洗规则
- `backend/scripts`：正式数据导入、审计、回补、升级脚本
- `backend/tests/manual`：手工联调、烟雾测试、CRS 流程验证脚本
- `backend/tools/archive`：历史热修复、诊断扫描、临时测试产物归档
- `frontend/miniprogram`：微信小程序
- `frontend-web`：Web 前端 SPA（React + Vite）
- `database`：数据库初始化与种子数据脚本
- `docs`：毕设文档与接口文档草案
- `deploy`：本地部署与容器化配置

### backend 目录约定

- `backend/app`：正式后端应用代码，启动入口为 `app.main:app`
- `backend/scripts`：当前仍会复用的正式脚本
- `backend/tests/manual`：需要人工执行的联调/验证脚本，不作为正式自动化测试框架
- `backend/tools/archive/admin_hotfix`：历史一次性页面/结构热修复脚本归档
- `backend/tools/archive/debug_scan`：历史诊断、扫描、校验脚本归档
- `backend/tools/archive/misc`：零散测试产物归档

> 约定：后续不要再把临时修补脚本、扫描脚本和手工测试脚本直接堆放到 `backend/` 根目录。

## 快速开始

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Web 管理端：`http://127.0.0.1:8000/admin-web`

### 微信小程序
打开微信开发者工具，导入 `frontend/miniprogram`

### Web 前端（新增）
```bash
cd frontend-web
npm install        # 安装依赖
npm run dev        # 开发模式 http://localhost:5173
npm run build      # 生产构建 → dist/
```
Vite 已配置 `/api` 代理到后端 `http://192.168.1.111:8000`，开发时无需配置 CORS。也可修改 `vite.config.ts` 中的 proxy target 指向你的后端地址。

> 当前代码已兼容 SQLite 启动自动补列，不要求每次手工删库重建。

## 非遗采集模块

已新增首版采集工程，目标是为推荐算法、AI 问答和前端内容页提供统一图文数据源。

### 采集输出目录

- `backend/storage/web_crawl/raw/{site}/pages`：栏目页原始 HTML
- `backend/storage/web_crawl/raw/{site}/html`：详情页原始 HTML
- `backend/storage/web_crawl/raw/{site}/json`：单篇清洗结果与种子 URL
- `backend/storage/web_crawl/assets/images`：下载后的图片素材
- `backend/storage/web_crawl/cleaned/contents.jsonl`：通过验收的统一内容数据
- `backend/storage/web_crawl/cleaned/rejected.jsonl`：被过滤掉的低质量内容
- `backend/storage/web_crawl/state`：断点续跑状态

### 当前候选站点优先级

1. `中国非物质文化遗产网`：官方权威，适合作为知识库主干和首个落地站点
2. `中国非遗馆`：适合补充专题展览和高质量视觉素材
3. `中国文化报非遗专题`：适合扩充新闻语料与相关推荐
4. `地方文旅非遗专题站`：适合补充地域标签和地方项目

### 运行命令

进入 `backend` 后执行：

- 输出站点清单：`python scripts/run_heritage_crawler.py sources`
- 评估候选站点：`python scripts/run_heritage_crawler.py evaluate`
- 发现首个站点详情页：`python scripts/run_heritage_crawler.py discover ihchina --max-pages 5`
- 抓取首个站点内容：`python scripts/run_heritage_crawler.py crawl ihchina --max-items 20`
- 导入清洗后的内容：`python scripts/import_crawled_contents.py`

### 统一字段结构

采集结果统一输出为：

```json
{
  "source_site": "site_name",
  "source_url": "https://example.com/article/123",
  "crawl_time": "2026-04-11T20:00:00",
  "title": "苏绣的历史与工艺特点",
  "summary": "介绍苏绣的发展脉络、代表技法与当代传承。",
  "content": "正文内容……",
  "cover_image": "storage/web_crawl/assets/images/xxx.jpg",
  "image_urls": ["storage/web_crawl/assets/images/xxx1.jpg"],
  "category": "traditional_craft",
  "region": "江苏",
  "tags": ["苏绣", "刺绣", "传统技艺", "江苏"],
  "publish_time": "2024-05-01",
  "author": "某站点",
  "content_type": "article",
  "quality_score": 0.92
}
```

## 内容治理与知识库治理

本项目已补齐从采集到展示的内容治理闭环，重点解决网页采集语料中的乱码、目录页、元信息页、重复内容和低质量残片污染问题。

### 内容表治理字段

`contents` 已扩展以下字段：

- `source_site`：来源站点
- `source_url`：来源链接
- `content_hash`：正文哈希，用于重复检测
- `quality_score`：质量评分
- `review_status`：审核状态（`pending` / `approved` / `rejected`）
- `import_batch`：导入批次

### 已实现的治理能力

1. **采集清洗**
   - 标题清洗
   - 正文清洗
   - 摘要提取
   - 标签去重
2. **低质量识别**
   - 正文过短
   - 标题过短
   - 目录页 / 摘要页 / 元信息页识别
   - 明显乱码标题与乱码正文识别
   - 重复内容识别
3. **审计与回退**
   - 审计报告生成
   - 问题内容回退 `draft`
   - 审核状态更新
4. **白名单回补**
   - 从已审核内容中筛选高质量候选
   - 自动回补为正式发布内容
   - 自动为优质内容加精
5. **AI 使用边界**
   - 内容展示、推荐和 AI 推荐卡优先只使用：
     - `status = published`
     - `review_status = approved`
     - `quality_score >= 0.8`

### 常用治理脚本

- SQLite 内容治理字段升级：
  - `python backend/scripts/upgrade_sqlite_contents_governance.py`
- 存量内容审计：
  - `python backend/scripts/audit_and_clean_contents.py`
- 审计并回写，同时将问题内容打回草稿：
  - `python backend/scripts/audit_and_clean_contents.py --apply --set-draft`
- 高质量白名单回补：
  - `python backend/scripts/promote_content_whitelist.py`

### Web 管理端与治理能力

后端已提供内容审计、白名单候选、白名单回补、统计导出等管理接口，Web 管理端入口为 `http://127.0.0.1:8000/admin-web`。

当前管理端单页仍在持续整合中，已覆盖的主方向包括：

- 内容列表与编辑
- 活动列表与编辑
- 用户管理
- 统计与导出
- 质量检查相关入口（与后端治理接口联动）

## 毕设可提炼的创新点

如果用于论文或答辩展示，当前系统可以突出以下创新点：

1. **非遗垂直知识治理链路**
   - 不只是采集网页，而是形成“采集—清洗—审计—回补—展示”的闭环。
2. **面向非结构化网页文本的质量评分机制**
   - 综合标题长度、正文长度、摘要质量、标签、地区、来源与坏信号检测。
3. **低质量语料隔离策略**
   - 将问题内容自动降级为 `draft`，避免污染前台展示与 AI 检索。
4. **白名单回补机制**
   - 在清洗后不是简单删除数据，而是从候选中重新筛出可展示内容，提高系统可用性。
5. **AI 与内容治理联动**
   - 通过审核状态与质量评分控制 AI 推荐卡的内容来源，提升回答可信度。
6. **个性化推荐与 AI 数字人融合**
   - 综合用户偏好、浏览记录、活动报名、社区互动与 AI 提问历史构建轻量用户画像。
   - 在首页、内容页、活动页、讨论页输出个性化推荐结果与推荐理由。
   - 在 AI 数字人问答中同步返回文化专题、活动、帖子推荐，形成“问答—推荐—浏览—参与”的闭环。

## 个性化推荐与 AI 融合说明

### 推荐信号来源

系统当前已接入以下推荐信号：

- **显式偏好**：非遗类型偏好、场景偏好、地区偏好
- **隐式行为**：内容详情浏览、活动详情浏览、帖子详情浏览
- **互动行为**：推荐曝光、推荐点击、讨论点赞、讨论收藏、评论互动
- **参与行为**：活动报名记录
- **语义行为**：AI 提问关键词与提问历史

### 推荐对象

推荐模块会统一输出三类对象：

- 文化专题内容
- 非遗活动
- 社区讨论帖子

### 推荐策略概述

当前推荐不是单一热度排序，而是采用轻量多信号融合策略：

1. 根据用户偏好和历史行为构建画像
2. 提取用户近期更关注的非遗类型、场景与地区信息
3. 对内容、活动、帖子分别进行匹配打分
4. 综合质量分、热度、新鲜度与去重策略输出推荐结果
5. 生成可解释的推荐理由，提升用户对推荐结果的理解

### AI 数字人融合方式

AI 数字人功能已与推荐模块打通：

- 用户提问时，系统先结合当前问题语义更新推荐上下文
- AI 回答后同步返回推荐卡片
- 推荐卡片可直接跳转到内容详情、活动详情和讨论详情
- AI 页会展示推荐依据，例如“偏好画像 / 浏览记录 / AI提问”

这使系统从单纯知识问答升级为“知识讲解 + 个性化导览 + 行动推荐”的综合服务模式。

## 当前状态说明

当前项目已经不只是展示型小程序，而是具备基础的内容治理与知识治理能力，适合作为毕业设计继续扩展：

- 可继续增加权威站点采集
- 可继续优化乱码检测规则
- 可继续补充人工审核工作流
- 可继续把治理过程写入论文实验与系统设计章节

> 当前项目已具备继续扩展业务逻辑、页面细节、真实站点采集与论文写作表达的基础。 
