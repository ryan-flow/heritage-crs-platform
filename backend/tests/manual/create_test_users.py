"""创建测试用户 101/102/103"""
import sqlite3

conn = sqlite3.connect("heritage_platform.db")
c = conn.cursor()

users = [
    (101, "test_craft", "工艺测试用户"),
    (102, "test_opera", "戏曲测试用户"),
    (103, "test_general", "泛文化测试用户"),
]

for uid, openid, nick in users:
    # 检查是否已存在
    exists = c.execute("SELECT id FROM users WHERE id=?", (uid,)).fetchone()
    if not exists:
        c.execute(
            "INSERT INTO users (id,openid,nickname,role,is_active) VALUES (?,?,?,?,1)",
            (uid, openid, nick, "user"),
        )
        print(f"Created user {uid}: {nick}")
    else:
        # 重置偏好
        c.execute(
            "UPDATE users SET preferred_heritage_types=NULL,preferred_scene_types=NULL,preferred_regions=NULL,score_explicit=0,score_implicit=0,score_dialogue=0,confidence_score=0 WHERE id=?",
            (uid,),
        )
        print(f"Reset user {uid}: {nick}")

conn.commit()

# 清理这些用户的AI对话日志和CRS会话
c.execute("DELETE FROM ai_qa_logs WHERE user_id IN (101,102,103)")
c.execute("DELETE FROM crs_sessions WHERE user_id IN (101,102,103)")
c.execute("DELETE FROM crs_ask_logs WHERE user_id IN (101,102,103)")
c.execute("DELETE FROM recommend_logs WHERE user_id IN (101,102,103)")
conn.commit()
print(f"Cleaned logs for users 101-103")

# 验证
rows = c.execute(
    "SELECT id,nickname,score_explicit,score_implicit,score_dialogue FROM users WHERE id IN (101,102,103)"
).fetchall()
for r in rows:
    print(f"  User {r[0]}: {r[1]}, E={r[2]}, I={r[3]}, D={r[4]}")

conn.close()
