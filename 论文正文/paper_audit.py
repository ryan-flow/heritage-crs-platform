# -*- coding: utf-8 -*-
"""论文vs代码一致性审查脚本"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ===== 审计结果 =====
issues = []

# 1. 检查CRS阈值
print("=" * 60)
print("【1】CRS置信度阈值")
print("=" * 60)
# 代码中: CRS_THRESHOLD_COLD=28, CRS_THRESHOLD_MIXED=62
# 论文需要检查是否声明了C<40 / 40-70 / C>=70 还是 C<28 / 28-62 / C>=62
print("代码实际值: cold<28, mixed 28-62, precision>=62")
print("需要检查论文中声明的是哪个版本")

# 2. 检查5维/6维信号源
print("\n" + "=" * 60)
print("【2】用户画像信号源数量")
print("=" * 60)
code_signals = [
    "信号1: 用户偏好画像 (preferred_heritage_types等)",
    "信号2: 当前问题上下文 (context_text)",
    "信号3: 浏览记录 (RecommendLog click/view)",
    "信号4: AI提问记录 (AIQALog)",
    "信号5: 活动报名 (ActivityRegistration)",
    "信号6: 社区互动 (点赞/收藏/评论)"
]
print("代码中build_user_profile()实际有6个信号源:")
for s in code_signals:
    print(f"  {s}")
print("需要检查论文声明的是5维还是6维")

# 3. 检查API路由数量
print("\n" + "=" * 60)
print("【3】API路由组数量")
print("=" * 60)
routes = [
    "auth", "users", "contents", "content-favorites", "events",
    "materials", "discussion", "recommend", "ai", "kg", "stats", "admin"
]
print(f"代码中router.py实际注册了{len(routes)}组路由:")
for r in routes:
    print(f"  /api/v1/{r}")
print("需要检查论文中声明的API路由数量")

# 4. 检查数据库表数量
print("\n" + "=" * 60)
print("【4】数据库表数量")
print("=" * 60)
tables = [
    "1.users", "2.contents", "3.activities", "4.activity_registrations",
    "5.ai_qa_logs", "6.crs_sessions", "7.crs_ask_logs", "8.recommend_logs",
    "9.local_knowledge_base", "10.electronic_materials", "11.discussion_topics",
    "12.discussion_comments", "13.discussion_likes", "14.discussion_favorites",
    "15.discussion_topic_tags", "16.content_favorites"
]
print(f"schema.sql + models实际有{len(tables)}张表:")
for t in tables:
    print(f"  {t}")
print("需要检查论文声明16张表，且表格编号与顺序一致")

# 5. TTS三级降级
print("\n" + "=" * 60)
print("【5】TTS降级策略")
print("=" * 60)
print("代码实现: 豆包TTS v3 → 豆包TTS v1 → Edge-TTS")
print("需要检查论文描述的降级层级是否一致")

# 6. AI五级回退
print("\n" + "=" * 60)
print("【6】AI问答五级回退")
print("=" * 60)
fallback_levels = [
    "L1: KB命中(conf>=0.8) → 豆包润色 (source=kb_enhanced, confidence=0.92)",
    "L2: KB低置信度(0.45<=conf<0.8) → 豆包参考 (source=doubao, confidence=0.78)",
    "L3: KB未命中 → 豆包直答合并调用 (source=doubao, confidence=0.75)",
    "L4: 豆包失败 → 联网搜索+豆包润色 (source=web_enhanced, confidence=0.65)",
    "L5: 全部失败 → 兜底回答 (source=fallback, confidence=0.25)"
]
for lvl in fallback_levels:
    print(f"  {lvl}")
print("需要检查论文描述的五级回退层级与置信度是否一致")

# 7. 前端TabBar
print("\n" + "=" * 60)
print("【7】前端TabBar页签")
print("=" * 60)
print("代码实际: 主页/文化/活动/讨论/我的 (5个TabBar)")
print("需要检查论文声明的TabBar数量和名称")

print("\n\n" + "=" * 60)
print("请根据以上检查点，对照论文全文进行逐一核查")
print("=" * 60)
