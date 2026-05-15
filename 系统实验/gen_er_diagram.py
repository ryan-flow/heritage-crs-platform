#!/usr/bin/env python3
"""生成系统E-R图（参考论文E-R图风格）"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.set_aspect("equal")
ax.axis("off")

def draw_entity(x, y, w, h, name, attrs):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.02",
                             facecolor="white", edgecolor="black", linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x, y + h/2 - 0.15, name, ha="center", va="top",
            fontsize=11, fontweight="bold", fontfamily="SimSun")
    for i, attr in enumerate(attrs):
        ay = y + h/2 - 0.4 - i * 0.28
        ax.plot([x - w/2 + 0.1, x - w/2 + 0.35], [ay, ay],
                color="black", linewidth=0.6)
        ax.text(x - w/2 + 0.4, ay, attr, ha="left", va="center",
                fontsize=8, fontfamily="SimSun")

def draw_relation(x, y, name):
    rx, ry = 0.55, 0.35
    diamond = mpatches.Polygon(
        [(x, y+ry), (x+rx, y), (x, y-ry), (x-rx, y)],
        closed=True, facecolor="white", edgecolor="black", linewidth=1.2)
    ax.add_patch(diamond)
    ax.text(x, y, name, ha="center", va="center",
            fontsize=8.5, fontfamily="SimSun")

def draw_attr_ellipse(x, y, text):
    ellipse = mpatches.Ellipse((x, y), 0.9, 0.32,
                                 angle=0, facecolor="#f5f5f5",
                                 edgecolor="#666666", linewidth=0.8)
    ax.add_patch(ellipse)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=7.5, fontfamily="SimSun")

# ===== 布局 =====
# 用户表（中心）
draw_entity(10, 9, 1.6, 2.8, "用户表", ["id (PK)", "openid", "nickname", "phone", "role", "is_active", "confidence_score"])

# 左侧实体
draw_entity(3, 11, 1.5, 2.2, "内容表", ["id (PK)", "title", "content_type", "quality_score", "review_status"])
draw_entity(3, 7.5, 1.5, 1.8, "活动表", ["id (PK)", "title", "location", "start_time"])
draw_entity(3, 4.5, 1.5, 1.6, "讨论话题", ["id (PK)", "title", "like_count", "comment_count"])

# 右侧实体
draw_entity(17, 11, 1.5, 1.6, "推荐日志", ["id (PK)", "action", "target_type", "target_id", "source_scene"])
draw_entity(17, 8, 1.5, 1.6, "AI问答记录", ["id (PK)", "question", "answer", "source", "confidence"])
draw_entity(17, 5, 1.5, 1.4, "CRS会话", ["id (PK)", "session_id", "mode", "turn_count"])

# 关系菱形
draw_relation(6.2, 10.5, "收藏")
draw_relation(6.2, 8.2, "报名")
draw_relation(6.2, 5.8, "发帖")
draw_relation(13.8, 10.5, "行为")
draw_relation(13.8, 8.2, "提问")
draw_relation(13.8, 5.5, "参与")

# 连线：实体 -> 关系 -> 实体
def draw_er_line(x1, y1, x2, y2, label_left="", label_right=""):
    style = dict(arrowstyle="-", color="#444444", linewidth=1.0,
                  connectionstyle="arc3,rad=-0.15")
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=style)

# 用户 -> 收藏 -> 内容
draw_er_line(9.1, 10.0, 6.65, 10.5)
draw_er_line(5.85, 10.5, 3.85, 10.8)
ax.text(7.5, 10.7, "M", fontsize=8, fontfamily="Times New Roman")
ax.text(4.9, 10.95, "N", fontsize=8, fontfamily="Times New Roman")

# 用户 -> 报名 -> 活动
draw_er_line(9.1, 8.6, 6.65, 8.2)
draw_er_line(5.85, 8.2, 3.85, 7.9)
ax.text(7.5, 8.45, "M", fontsize=8, fontfamily="Times New Roman")
ax.text(4.9, 8.05, "N", fontsize=8, fontfamily="Times New Roman")

# 用户 -> 发帖 -> 话题
draw_er_line(9.1, 7.4, 6.65, 5.8)
draw_er_line(5.85, 5.8, 3.85, 5.1)
ax.text(7.5, 6.25, "M", fontsize=8, fontfamily="Times New Roman")
ax.text(4.9, 5.35, "N", fontsize=8, fontfamily="Times New Roman")

# 用户 -> 行为 -> 推荐日志
draw_er_line(10.9, 10.0, 13.35, 10.5)
draw_er_line(14.15, 10.5, 16.15, 10.8)
ax.text(12.3, 10.7, "1", fontsize=8, fontfamily="Times New Roman")
ax.text(16.05, 10.95, "M", fontsize=8, fontfamily="Times New Roman")

# 用户 -> 提问 -> AI问答
draw_er_line(10.9, 8.6, 13.35, 8.2)
draw_er_line(14.15, 8.2, 16.15, 8.0)
ax.text(12.3, 8.45, "1", fontsize=8, fontfamily="Times New Roman")
ax.text(16.05, 8.15, "M", fontsize=8, fontfamily="Times New Roman")

# 用户 -> 参与 -> CRS会话
draw_er_line(10.9, 7.0, 13.35, 5.5)
draw_er_line(14.15, 5.5, 16.15, 5.2)
ax.text(12.3, 5.95, "1", fontsize=8, fontfamily="Times New Roman")
ax.text(16.05, 5.35, "1", fontsize=8, fontfamily="Times New Roman")

plt.tight_layout()
out_path = r"d:\桌面\毕业设计\论文正文\图4-2-系统ER图.png"
plt.savefig(out_path, dpi=200, bbox_inches="tight",
            facecolor="white", edgecolor="none")
print(f"E-R图已保存: {out_path}")
