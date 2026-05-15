"""单步AI问答测试，检查偏好反哺是否生效"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import sqlite3
import json
import urllib.request

DB = "D:/桌面/毕业设计/backend/heritage_platform.db"
UID = 101

def db_check(label):
    conn = sqlite3.connect(DB)
    r = conn.execute(
        "SELECT preferred_heritage_types,preferred_scene_types,preferred_regions,"
        "score_explicit,score_implicit,score_dialogue FROM users WHERE id=?",
        (UID,),
    ).fetchone()
    conn.close()
    print(f"  [{label}] heritage={r[0]}, scene={r[1]}, region={r[2]}, E={r[3]}, I={r[4]}, D={r[5]}")
    return r

def ai_chat(question):
    data = json.dumps({"user_id": UID, "question": question}).encode()
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/ai/chat", data=data, method="POST"
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    d = result.get("data", result)
    source = d.get("source", "?")
    rec_qs = d.get("recommended_questions", [])
    print(f"  AI source={source}, rec_qs={rec_qs}")
    return result

# 1. 初始状态
print("=== User 101 单步测试 ===")
db_check("初始")

# 2. 第1轮
print("\n--- 第1轮: 苏绣有什么特点？ ---")
ai_chat("苏绣有什么特点？")
db_check("R1后")

# 3. 第2轮
print("\n--- 第2轮: 紫砂壶怎么鉴别真假？ ---")
ai_chat("紫砂壶怎么鉴别真假？")
db_check("R2后")

# 4. 第3轮
print("\n--- 第3轮: 四大名绣各有什么特色？ ---")
ai_chat("四大名绣各有什么特色？")
db_check("R3后")

# 5. CRS状态
print("\n--- CRS状态 ---")
req2 = urllib.request.Request(
    f"http://localhost:8000/api/v1/ai/crs/state?user_id={UID}", method="GET"
)
with urllib.request.urlopen(req2, timeout=10) as resp:
    crs = json.loads(resp.read().decode())
print(f"  CRS: {json.dumps(crs.get('data', crs), ensure_ascii=False, indent=2)}")
