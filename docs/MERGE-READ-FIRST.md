# 非遗文化传播系统 — 模块定位清单（面向求职面试）

## 定位说明

以下将项目所有模块按面试展示价值分为三级：

- **⭐ 主角**：面试时必须展示的核心创新点，CRS + AI 数字人
- **◻ 配角**：支撑平台运作的基础功能，展示时一句话带过
- **· 噪音**：与核心创新无关，面试时不主动提及；代码保留不动

## 模块定位清单

### ⭐ 主角 — CRS 对话式推荐 + AI 数字人

| 模块 | 文件/路径 | 面试展示价值 | 理由 |
|------|-----------|-------------|------|
| CRS 三维置信度决策引擎 | `backend/app/services/crs/decision.py` | ⭐⭐⭐ | 五策略状态机：cold_start_ask → mixed_rec → precision_rec，阈值驱动模式切换。展示对推荐系统"冷启动→探索→利用"的完整理解 |
| CRS 偏好映射 + 同步 | `crs/mappings.py` + `crs/preference.py` | ⭐⭐⭐ | 6个偏好映射词典、4条偏好同步路径。展示如何将用户自然语言回答转化为结构化画像 |
| CRS ASK提问模板 | `crs/ask_templates.py` | ⭐⭐ | 13套提问模板，覆盖不同偏好维度。展示"AI引导用户表达需求"的产品思路 |
| CRS 会话管理 | `crs/session.py` | ⭐⭐ | 会话生命周期管理、ASK回答处理、模式切换 |
| 推荐引擎 | `recommendation_service.py` | ⭐⭐⭐ | 画像构建（显式40%+隐式35%+对话25%三维置信度）、多信号融合排序、AI推荐卡片生成 |
| AI问答主入口 | `ai_service.py` | ⭐⭐⭐ | 五级回退策略：KB润色→豆包直答→联网兜底。集成CRS ASK-REC状态机 |
| AI对话端点 | `endpoints/ai.py` | ⭐⭐⭐ | `/ai/chat`、`/ai/crs/state`、`/ai/crs/answer`、TTS。AI数字人的路由层 |
| 推荐端点 | `endpoints/recommend.py` | ⭐⭐⭐ | `/recommend/?scene=home` 推荐订阅源 + `/recommend/track` 行为追踪 |
| 数字人组件（Web） | `frontend-web/src/components/digital-human/` | ⭐⭐⭐ | CSS绘制的黑塔数字人，3种情绪状态（curious/thinking/confident）对应CRS三阶段，点击触发TTS语音 |
| AI聊天页（Web） | `frontend-web/src/pages/ai/AiChatPage.tsx` | ⭐⭐⭐ | CRS ASK问答、推荐卡片流、TTS语音播放、数字人情绪联动 |
| 推荐卡片组件 | `frontend-web/src/components/recommend/` | ⭐⭐ | 推荐内容的卡片化展示，含推荐理由 |
| 聊天/CRS状态管理 | `frontend-web/src/stores/chat-store.ts` | ⭐⭐ | Zustand管理的CRS状态 + 消息历史 + 推荐卡片 |
| 豆包大模型客户端 | `doubao_client.py` | ⭐⭐ | 火山引擎Chat Completions API调用（兼容OpenAI格式） |
| TTS语音合成 | `tts_service.py` | ⭐⭐ | 三级降级策略：豆包v3 → 豆包v1 → Edge-TTS。体现对容错设计的意识 |
| 本地知识库 | `knowledge_base.py` | ⭐ | AI问答的知识来源。作为CRS/AI的背景存在 |
| 推荐信号生成 | `endpoints/recommend.py` + `crs/questions.py` | ⭐⭐ | 推荐问题生成、画像摘要、推荐理由生成 |

### ◻ 配角 — 平台基础功能（不主动展示，回答问题时一句话带过）

| 模块 | 文件/路径 | 面试展示价值 | 在 README 中的位置 |
|------|-----------|-------------|-------------------|
| 内容CRUD | `endpoints/content.py` | ⭐ | 第二章节"平台功能概览"一句话 |
| 活动CRUD | `endpoints/event.py` | ⭐ | 同上 |
| 社区讨论 | `endpoints/discussion.py` | ⭐ | 同上 |
| 用户认证 | `endpoints/auth.py` + `endpoints/user.py` | ⭐ | 同上 |
| Web前端页面（除AI外） | `frontend-web/src/pages/` | ⭐ | 一句话列出 |
| 前端布局/导航 | `layout/AppLayout.tsx` | — | 不提细节 |
| 16个数据库模型 | `models/*.py` | — | 不提细节 |
| 显示丰富 | `display_enrichment.py` | — | 不提细节 |
| 内容治理 | `content_governance.py` | — | 附录"技术细节"一句话 |
| 知识图谱 | `knowledge_graph.py` | ⭐ | 附录"扩展能力"一句话：独立SQLite图数据库，66个实体+64个三元组 |

### · 噪音 — 不主动提及，面试官不问不解释，代码保留不动

| 模块 | 文件/路径 | 面试展示价值 | 处理方式 |
|------|-----------|-------------|---------|
| 微信小程序全部代码 | `frontend/miniprogram/` | 面试官打不开，不提 | README 附录一句话 |
| 管理后端 | `endpoints/admin.py` + `stats.py` + `admin.html` | 与核心创新无关 | 不提及 |
| 爬虫模块 | `crawler/` (14个文件) | 数据采集基础设施，不是创新点 | 只出现在"数据来源"一句话中 |
| 管理端前端页面 | `pages/admin/*` | 与核心创新无关 | 不提及 |
| 数据脚本 | `scripts/` (30+个) | 一次性运维脚本 | 不提及 |
| 论文文档 | `docs/`、`论文正文/`、`参考论文/` | 不在README展示 | 不提及 |
| 答辩材料 | `答辩演示文件夹/`、`系统实验/` | 内部材料 | 不提及 |
| 部署配置 | `deploy/`、`railway.json`、`render.yaml` | 只保留Docker Compose概念 | DEPLOY.md保留，README不细讲 |
| 根目录杂项 | 测试脚本、截图、`.docx` | 无面试价值 | 不提及 |

## 面试官可能会问 & 你的回答

| 面试官问 | 你的回答要点 |
|----------|------------|
| "这个项目的核心创新是什么？" | CRS对话式推荐 + AI数字人。传统推荐系统只能根据历史行为推荐，我们让AI数字人主动提问了解用户偏好，3轮对话即可达到冷启动后的混合推荐状态 |
| "CRS的三个模式怎么工作的？" | cold_start：AI提问探索 → mixed：边问边推荐 → precision：精准推荐。每个阶段AI数字人的表情和语气都不同 |
| "置信度怎么计算的？" | 三维加权：显式偏好40% + 隐式行为35% + 对话语义25%。三个维度各自独立计算再融合 |
| "AI数字人和推荐系统怎么联动的？" | 用户提问→AI提取偏好→更新画像→CRS决策→同步返回推荐卡片→用户可点击查看。形成"问答→推荐→浏览→参与"闭环 |
| "用了什么技术栈？" | 后端FastAPI+SQLAlchemy+PostgreSQL，前端React+Vite+Tailwind，AI是火山引擎豆包大模型，语音合成豆包TTS |
| "数据哪里来的？" | 本地知识库（约40条）+ 豆包大模型知识 + Pixabay英文关键词搜索配图 |
