"""查看KB中按章节分组的问题列表"""
import sqlite3

conn = sqlite3.connect("heritage_platform.db")

# 按章节统计
rows = conn.execute(
    "SELECT chapter, COUNT(*) FROM local_knowledge_base WHERE status='active' GROUP BY chapter ORDER BY COUNT(*) DESC"
).fetchall()
for ch, cnt in rows:
    print(f"{ch}: {cnt}")
print()

# 每个章节的短问题
for ch, _ in rows:
    qs = conn.execute(
        "SELECT question FROM local_knowledge_base WHERE status='active' AND chapter=? ORDER BY length(question) LIMIT 8",
        (ch,),
    ).fetchall()
    print(f"--- {ch} ---")
    for q in qs:
        print(f"  {q[0]}")
    print()

conn.close()
