#!/usr/bin/env python3
"""生成系统分层架构图（参考论文风格）"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(18, 12))
ax.set_xlim(0, 18)
ax.set_ylim(0, 12)
ax.set_aspect("equal")
ax.axis("off")

def draw_layer(x, y, w, h, title):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.01",
                             facecolor="#fafafa", edgecolor="#333333",
                             linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x, y + h/2 - 0.15, title, ha="center", va="top",
            fontsize=13, fontweight="bold", fontfamily="SimSun")

def draw_box(x, y, w, h, text, fillcolor="#ffffff"):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.01",
                             facecolor=fillcolor, edgecolor="#555555",
                             linewidth=1.0)
    ax.add_patch(rect)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=9, fontfamily="SimSun")

def draw_arrow_down(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2 + 0.05), xytext=(x1, y1 - 0.05),
                arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.5))

# ===== 第一层：前端交互层 =====
draw_layer(9, 10.8, 16, 1.6, "第一层 前端交互层")

# 用户端子区域
rect = FancyBboxPatch((4.5, 10.0), 7.5, 1.2,
                         boxstyle="round,pad=0.01",
                         facecolor="#e8f4f8", edgecolor="#888888",
                         linewidth=1.0, linestyle="--")
ax.add_patch(rect)
ax.text(8.25, 10.5, "微信小程序用户端", fontsize=10, fontfamily="SimSun", ha="center")
boxes_u = ["首页", "内容页", "活动页", "讨论页", "AI对话页", "个人中心", "偏好设置"]
for i, b in enumerate(boxes_u):
    bx = 1.8 + i * 1.05
    draw_box(bx, 9.75, 0.85, 0.45, b, "#d0e8f2")

# 管理端子区域
rect = FancyBboxPatch((12.5, 10.0), 4.5, 1.2,
                         boxstyle="round,pad=0.01",
                         facecolor="#fff3e0", edgecolor="#888888",
                         linewidth=1.0, linestyle="--")
ax.add_patch(rect)
ax.text(14.75, 10.5, "管理端", fontsize=10, fontfamily="SimSun", ha="center")
boxes_a = ["内容管理", "活动管理", "讨论管理", "用户管理"]
for i, b in enumerate(boxes_a):
    bx = 13.0 + i * 1.05
    draw_box(bx, 9.75, 0.85, 0.45, b, "#ffe0b2")

# 箭头：L1 -> L2
for x in [4.5, 9, 13.5]:
    draw_arrow_down(x, 9.35, x, 8.65)

# ===== 第二层：接口服务层 =====
draw_layer(9, 8.0, 16, 1.0, "第二层 接口服务层（FastAPI RESTful API）")
api_names = ["AI问答接口", "CRS状态接口", "用户画像接口", "内容接口", "活动接口", "讨论区接口", "登录接口"]
for i, a in enumerate(api_names):
    bx = 2.5 + i * 2.1
    draw_box(bx, 7.7, 1.8, 0.45, a, "#e3f2fd")

# 箭头：L2 -> L3
for x in [4.5, 9, 13.5]:
    draw_arrow_down(x, 7.25, x, 6.55)

# ===== 第三层：核心能力层 =====
draw_layer(9, 5.9, 16, 1.0, "第三层 核心能力层")

# AI服务
rect = FancyBboxPatch((3.0, 5.4), 4.0, 0.8,
                         boxstyle="round,pad=0.01",
                         facecolor="#fce4ec", edgecolor="#888888",
                         linewidth=1.0)
ax.add_patch(rect)
ax.text(5.0, 5.68, "AI服务\nai_service.py", fontsize=9, fontfamily="SimSun", ha="center", va="center")
ai_items = ["问答组织", "会话管理", "ASK-REC决策"]
for i, item in enumerate(ai_items):
    draw_box(2.3 + i*1.35, 5.08, 1.15, 0.28, item, "#f8bbd0")

# 推荐服务
rect = FancyBboxPatch((7.5, 5.4), 4.0, 0.8,
                         boxstyle="round,pad=0.01",
                         facecolor="#e8f5e9", edgecolor="#888888",
                         linewidth=1.0)
ax.add_patch(rect)
ax.text(9.5, 5.68, "推荐服务\nrecommendation_service.py", fontsize=9, fontfamily="SimSun", ha="center", va="center")
rec_items = ["画像构建", "置信度计算", "三路排序"]
for i, item in enumerate(rec_items):
    draw_box(6.8 + i*1.35, 5.08, 1.15, 0.28, item, "#c8e6c9")

# 增强服务
rect = FancyBboxPatch((12.0, 5.4), 5.0, 0.8,
                         boxstyle="round,pad=0.01",
                         facecolor="#fff8e1", edgecolor="#888888",
                         linewidth=1.0)
ax.add_patch(rect)
ax.text(14.5, 5.68, "增强服务", fontsize=9, fontweight="bold", fontfamily="SimSun", ha="center", va="center")
enh_items = ["本地知识检索", "知识图谱增强", "联网补充", "TTS语音播报"]
for i, item in enumerate(enh_items):
    draw_box(11.0 + i*1.2, 5.08, 1.0, 0.28, item, "#ffecb3")

# 箭头：L3 -> L4
for x in [5, 9.5, 14.5]:
    draw_arrow_down(x, 5.0, x, 4.3)

# ===== 第四层：数据与外部服务层 =====
draw_layer(9, 3.7, 16, 1.0, "第四层 数据与外部服务层")

# 内部数据
rect = FancyBboxPatch((3.0, 3.1), 6.0, 0.9,
                         boxstyle="round,pad=0.01",
                         facecolor="#ede7f6", edgecolor="#888888",
                         linewidth=1.0)
ax.add_patch(rect)
ax.text(6.0, 3.48, "内部数据存储", fontsize=10, fontweight="bold", fontfamily="SimSun", ha="center")
data_items = ["SQLite<br/>业务数据库", "本地知识库", "推荐日志", "CRS会话数据"]
for i, d in enumerate(data_items):
    draw_box(2.0 + i*1.5, 3.05, 1.25, 0.38, d, "#d1c4e9")

# 外部服务
rect = FancyBboxPatch((11.5, 3.1), 5.5, 0.9,
                         boxstyle="round,pad=0.01",
                         facecolor="#e0f2f1", edgecolor="#888888",
                         linewidth=1.0)
ax.add_patch(rect)
ax.text(14.25, 3.48, "外部服务", fontsize=10, fontweight="bold", fontfamily="SimSun", ha="center")
ext_items = ["豆包大模型API", "联网搜索API", "微信登录"]
for i, e in enumerate(ext_items):
    draw_box(10.5 + i*1.7, 3.05, 1.45, 0.38, e, "#b2ebf2")

plt.tight_layout()
out_path = r"d:\桌面\毕业设计\论文正文\图4-1-系统分层架构图.png"
plt.savefig(out_path, dpi=200, bbox_inches="tight",
            facecolor="white", edgecolor="none")
print(f"架构图已保存: {out_path}")
