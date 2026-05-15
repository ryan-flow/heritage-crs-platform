import sqlite3
conn = sqlite3.connect('heritage_platform.db')
cur = conn.cursor()

cur.execute("SELECT chapter, COUNT(*) as cnt FROM local_knowledge_base WHERE status='active' GROUP BY chapter ORDER BY cnt DESC")
rows = cur.fetchall()
print('=== 各章节题目数量 ===')
for r in rows:
    print(f'  {r[0]}: {r[1]}条')

print('\n=== 传统工艺章节题目(前10) ===')
cur.execute("SELECT question FROM local_knowledge_base WHERE chapter='传统工艺' AND status='active' LIMIT 10")
for r in cur.fetchall():
    print(f'  - {r[0]}')

print('\n=== 传承实践章节题目(前10) ===')
cur.execute("SELECT question FROM local_knowledge_base WHERE chapter='传承实践' AND status='active' LIMIT 10")
for r in cur.fetchall():
    print(f'  - {r[0]}')

print('\n=== 非遗基础认知章节题目(前10) ===')
cur.execute("SELECT question FROM local_knowledge_base WHERE chapter='非遗基础认知' AND status='active' LIMIT 10")
for r in cur.fetchall():
    print(f'  - {r[0]}')

conn.close()
