# 非遗 Web 前端项目 — Agent 交接手册

## 项目位置
`d:/桌面/毕业设计/frontend-web/`

## 技术栈
React 19 + TypeScript + Vite 8 + Tailwind CSS 4 + React Router 7 + TanStack Query 5 + Zustand 5 + Lucide React

## 设计参考
- **小程序源码（参考对标）**: `d:/桌面/毕业设计/frontend/miniprogram/pages/`
- **设计 Token**: `frontend-web/src/index.css`（@theme 指令）
- **核心组件**: `frontend-web/src/components/ui/`（GlassCard, InkButton, ChipPill, CoverImage）

## 设计系统关键值

### 颜色
| 角色 | 值 |
|------|-----|
| 品牌主色 | `#9f2d22` |
| 鎏金辅助 | `#c08a3e` |
| 翠玉绿 | `#5b8c5a` |
| 主文字 | `#2c2416` |
| 次要文字 | `#7b6141` |
| 宣纸背景 | `#fdf8f0` |
| 卡片底 | `rgba(255, 251, 245, 0.96)` |
| 卡片阴影 | `0 7px 17px rgba(121,58,31,0.10)` |

### 圆角
- 卡片 14px、Hero 36px、按钮 999px（全 pill）

### 按钮渐变
- primary: `135deg, #9f2d22 → #c04833`
- secondary: `135deg, #c08a3e → #d5a24d`

### 页面背景
```css
linear-gradient(180deg, #fff8ef 0%, #f7efe0 42%, #f7f3eb 100%)
```

### Hero 渐变
- 默认: `160deg, #5c1a1a → #9f2d22 → #b34130 → #8b4513`
- AI/首页（小程序风格）: `135deg, #5B3A7A → #6B3A5B → #7a4020 → #8B4513`

### 小程序 Hero 阴影
```css
box-shadow: 0 22px 46px rgba(65, 32, 92, 0.24)
```

## API
- 本地: `http://localhost:8000/api/v1`（后端在 port 8000）
- `.env.local` 不提交，`vercel.json` 有生产环境变量
- `buildImageUrl()` 在 `src/lib/api.ts`，已处理好存储路径映射

## 当前状态

### 已完成
- 全局 Token 对齐（色值、圆角、阴影、卡片背景、按钮渐变方向）
- GlassCard 与小程序卡片风格对齐
- InkButton 新增 secondary 金色渐变变体 + active translateY
- ChipPill 组件（三种变体）
- buildImageUrl 路径映射扩展
- **首页已重构**（双栏 Hero + 今日推荐集中卡 + CRS 模式标签 + 策略来源条 + 快捷入口 2 个）

### 待办

#### 1. AiChatPage 增强（10 项）
计划文件: `C:\Users\老王\.claude\plans\lexical-pondering-frog.md`
包括：空状态引导语 / 换一批按钮 / Layer divider 分隔线 / 庆祝动效改进 / 卡片赞踩反馈 / KG 实体面板 / Action Task 清单 / 冷启动问答池

#### 2. 其他页面逐页对齐小程序
- ContentListPage / ContentDetailPage — 卡片风格、间距
- ActivityListPage / ActivityDetailPage — 同上
- ProfilePage — CRS 信号面板风格
- DiscussionListPage / DiscussionDetailPage — 讨论卡片

#### 3. 图片资源
- content ID 1 和 16（昆曲入门避坑）的封面图需要替换，目前用的是 `content_001_1.jpg`，内容不匹配
- 其他 `content_N_1.jpg` 是外部 AI 工具批量生成的（脚本不可用）
- 现有 SVG 生成器: `backend/scripts/generate_content_covers.py`

### 已知问题
- 后端（uvicorn port 8000）不稳定，可能意外退出，需重启
- 外网图片下载被 GFW 阻挡

## 验证
```bash
npx tsc --noEmit          # 类型检查
npm run build              # 构建
node snap.cjs              # Playwright 截图（已有脚本）
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000  # 启动后端
```

## 小程序参考（关键设计模式）
- 全部按钮用 pill 形状（999px radius）
- 卡片毛玻璃半透明暖色底
- CRS 模式标签：cold_start 暖米色 / mixed 棕褐色 / precision 朱砂红
- 层分隔线（Layer divider）: 细线 + 标签 + 细线
- 快速入口备注文字: `text-[10px] text-ink-muted` 尺寸
