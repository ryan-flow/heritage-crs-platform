# AGENTS.md — 非遗平台 Web 端给 Agent 的视觉实现规范

任何 agent 进入本项目修改前端时，必须遵守以下规则。核心目标：**将微信小程序的界面布局，用 frontend-web 的中国风设计语言重新实现，不是照搬代码，而是融合风格。**

---

## 0. 项目速查

| 项 | 路径 |
|---|---|
| 设计 Token 定义 | `frontend-web/src/index.css` — 所有颜色、字体、圆角、动画在这里 |
| 数字人组件 | `frontend-web/src/components/digital-human/DigitalHumanModel.tsx` |
| 数字人 CSS | `frontend-web/src/components/digital-human/DigitalHumanModel.css` |
| 核心 UI 组件 | `frontend-web/src/components/ui/` (GlassCard, InkButton, SealBadge) |
| 参考截图 | `frontend-web/public/wechat-miniprogram-reference.jpg` |
| 小程序源码 | `frontend/` (WXML/WXSS) |

## 1. 视觉铁律（不许碰的底线）

1. **禁止紫色渐变或蓝紫 AI 风** — 本项目品牌色是朱砂红 `#9f2d22`，背景是宣纸色 `#fdf8f0`。
2. **禁止引入第三方 UI 库** — shadcn/ui、MUI、Ant Design 统统不要。所有组件基于 `index.css` 已有的 class 手写。
3. **禁止纯白背景平面卡片** — 必须用 `.glass-card`（毛玻璃 + 暖色底 + 阴影），有层次感。
4. **禁止静态页面无动画** — 只要出现一个无 hover/active 反馈的按钮，或者一个无入场动画的区块，就是不合格。
5. **禁止硬编码颜色 hex** — 必须用 `index.css` `@theme` 中定义的 token，或者 Tailwind 类名如 `text-brand`、`bg-parchment`。
6. **数字人必须保留且增强交互** — 黑塔是 CSS 纯绘制，不是图片。不能替换为 emoji 或静态图片。

## 2. 数字人点击反馈链路

当用户点击数字人时，必须触发以下完整的反馈链（不是只做一项）：

```
点击 → 缩反馈 guofeng-press (scale 0.97, 150ms)
     → 心情标签 mood-tag 淡入淡出 (opacity transition 0.3s)
     → 轨道光环 orbit-1/orbit-2 转速翻倍 (animation-duration 减半, 1s)
     → 粒子 spark-1/2/3 burst 扩散 (scale(1.6), opacity 0→1→0, 0.6s)
     → 底座 pedestal 亮度脉冲 (brightness 1.3, 0.4s)
     → 如有 onSpeak → 触发 TTS 语音播报
     → 所有效果 600ms 后复原
```

实现方式：给 `.dhm-stage` 添加一个 `clicked` class，用 CSS 处理上述动画，JS 中 `setTimeout` 移除。参考 `DigitalHumanModel.css` 中现有的动画定义。

## 3. 现有动画类名速查

直接用这些 class，不要重新定义：

| class | 何时用 | 不要滥用 |
|---|---|---|
| `.rise-in-stagger` | 卡片列表容器，子元素逐项入场 | 单个元素不要用 |
| `.animate-fade-in-up` | 页面主区块入场 | 每个 div 都加 |
| `.fade-in` | 轻量元素入场 | — |
| `.card-interactive` | 可点击卡片 | 装饰性卡片 |
| `.guofeng-press` | 按钮、数字人、可点击图标 | 静态文字 |
| `.breathe-ring` | 重要 CTA 按钮 | 所有按钮 |
| `.page-enter` | 页面根 div | 嵌套页面 |
| `.msg-enter` | 聊天消息气泡 | — |

## 4. 颜色分配表

| 场景 | 背景/底色 | 文字色 | 点缀/边框 |
|---|---|---|---|
| 页面背景 | `bg-parchment` 或 `linear-gradient(180deg, #fff8ef, #f7efe0, #f7f3eb)` | `text-ink` | — |
| 毛玻璃卡片 | `linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))` | `text-ink-secondary` | `border: 1px solid rgba(219,191,155,0.18)` |
| AI 消息 | `#fbf4ea → #f7ead7` | `#473022` | `rgba(226,197,163,0.34)` |
| 用户消息 | `#aa4634 → #c65b43` | `#fff9f4` | — |
| 主按钮 | `#9f2d22 → #c04833` | white | `box-shadow: 0 8px 20px rgba(159,45,34,0.24)` |
| 金色按钮 | `#b98535 → #d7a953` | white | `box-shadow: 0 4px 12px rgba(185,133,53,0.15)` |
| 推荐卡片 | `rgba(255,250,243,0.92)` | `#2f2419` | `rgba(238,216,191,0.82)` |
| AI Hero 区 | `radial-gradient(...) + #5B3A7A→#8B4513` | `#fff9f1` | `rgba(255,238,220,0.08)` |
| 分隔线 | `linear-gradient(90deg, transparent, #d4c4aa, transparent)` | — | — |

## 5. 页面实现优先级与规范

### P0 — AI 对话页（最重要）
- 文件：`frontend-web/src/pages/ai/AiChatPage.tsx`
- **必须保留**：CRS 置信度面板（三维置信度条 + 时间线）、模式升级庆祝 overlay（粒子+弹跳 `🎉`+模式名）、ASK 追问卡片、延伸推荐卡片（含解释展开/收起）、打字机效果、TTS 语音按钮
- **必须增强**：数字人点击反馈链路（见上方第 2 节）、消息入场 `.msg-enter`、追问按钮 hover 变色

### P1 — 首页
- 新建：`frontend-web/src/pages/home/HomePage.tsx`
- 参考：小程序首页 + CLAUDE.md 设计系统的配色
- **结构**：
  1. Hero 区 — 数字人 `variant="hero" size={200}` + 标题"黑塔·非遗导览" + 副标题 + 开始对话 CTA（`.hero-cta-breathe`）
  2. 快捷入口 4 宫格 — AI 导览 / 浏览非遗 / 非遗活动 / 社区讨论，每格有图标+文字，`.quick-entry-btn`
  3. 推荐内容流 — 标题"为你推荐"，`.rise-in-stagger` 包裹的卡片列表
  4. 底部科普卡 — 非遗小知识，随机展示，`.card-interactive`

### P2 — 内容浏览页
- 筛选芯片栏：`.chip` / `.chip-active`，选中态朱砂红渐变
- 内容卡片网格：移动端单列，md 双列
- 详情页：`GlassCard elevated` + AI 浮窗入口

### P3 — 活动页 / P4 — 社区页
- 按小程序对应页面布局，使用本设计的卡片、按钮、芯片组件重新实现

## 6. 实现检查清单

每完成一个页面改动，逐条确认：

- [ ] 所有颜色来自 `@theme` 或 Tailwind token，无硬编码 `#xxxxxx`
- [ ] 每个按钮/可点击元素有 hover + active 反馈
- [ ] 每个区块容器用了入场动画 class
- [ ] 卡片用了 `.glass-card` 或 `.card-interactive`，有阴影层次
- [ ] 移动端 ≤480px 居中，`md:` 断点桌面适配
- [ ] 数字人在当前页面可见，点击有反馈
- [ ] 滚动条颜色与设计系统一致（`#d4c4aa`）
- [ ] 没有引入任何第三方 UI 库

## 7. 禁止事项清单

- 禁止 `bg-white`、`bg-gray-50` 白底卡片
- 禁止 `shadow-sm`、`shadow-md` — 本项目阴影统一用 `rgba(121,58,31,x)` 暖棕系
- 禁止 `rounded-lg`、`rounded-xl` — 用 `rounded-[20px]` 或 `rounded-[28px]`（card token）
- 禁止 `font-sans` 直接使用 — 本项目 `font-sans` 已定义为 `Noto Sans SC`，直接用
- 禁止紫色、蓝色、粉色作为主色调
- 禁止把数字人换成图片或移除
