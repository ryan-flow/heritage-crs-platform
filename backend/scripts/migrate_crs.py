"""迁移脚本：为crs_sessions表添加asked_attributes列"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "heritage_platform.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查列是否已存在
cursor.execute("PRAGMA table_info(crs_sessions)")
cols = [row[1] for row in cursor.fetchall()]

if "asked_attributes" not in cols:
    cursor.execute('ALTER TABLE crs_sessions ADD COLUMN asked_attributes TEXT DEFAULT "[]"')
    conn.commit()
    print("asked_attributes 列已添加")
else:
    print("asked_attributes 列已存在，跳过")

# 验证
cursor.execute("PRAGMA table_info(crs_sessions)")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

conn.close()
