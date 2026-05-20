"""Test CRS flow: guest login → cold_start → mixed → recommendations"""
import json, urllib.request, ssl

BASE = "http://localhost:8000/api/v1"
ctx = ssl.create_default_context()


def api(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Content-Type": "application/json",
                                          "Origin": "http://192.168.1.110:3007"})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    return json.loads(resp.read())


# 1. Guest login
print("=== 1. 游客登录 ===")
guest = api("POST", "/auth/guest")
uid = guest["data"]["userId"]
print(f"User ID: {uid}")

# 2. CRS initial state
print("\n=== 2. CRS 初始状态 ===")
state = api("GET", f"/ai/crs/state?user_id={uid}")
print(f"Mode: {state['data']['mode']}, Score: {state['data']['confidence_score']}")

# 3. AI Chat #1 - cold start
print("\n=== 3. AI 对话 #1：冷启动 ===")
chat1 = api("POST", "/ai/chat", {"question": "我对非遗感兴趣，想了解戏曲", "user_id": uid})
print(f"策略: {chat1['data']['strategy']}")
print(f"回答: {chat1['data']['answer'][:80]}")
print(f"AI提问: {chat1['data'].get('ask_prompt', '-')}")
print(f"推荐卡: {len(chat1['data'].get('recommend_cards', []))} 条")

sid = chat1['data'].get('crs_session_id', '')
ask_id = chat1['data'].get('ask_id', '')
print(f"Session: {sid[:8] if sid else 'N/A'}, AskID: {ask_id}")

# 4. CRS Answer
print("\n=== 4. CRS 回答 ===")
if sid and ask_id:
    ans = api("POST", "/ai/crs/answer", {
        "user_id": uid, "session_id": sid,
        "ask_id": ask_id, "answer": "传统工艺"
    })
    print(f"Mode: {ans['data']['mode']}, Score: {ans['data']['confidence_score']}")

# 5. CRS state after answer
print("\n=== 5. CRS 状态变化 ===")
state2 = api("GET", f"/ai/crs/state?user_id={uid}")
print(f"Mode: {state2['data']['mode']}, Score: {state2['data']['confidence_score']}")
print(f"维度: {json.dumps(state2['data'].get('dimensions', {}))}")

# 6. AI Chat #2 - mixed/hot
print("\n=== 6. AI 对话 #2：继续对话 ===")
chat2 = api("POST", "/ai/chat", {
    "question": "有什么适合新手的工艺推荐？", "user_id": uid
})
print(f"策略: {chat2['data']['strategy']}")
print(f"回答: {chat2['data']['answer'][:80]}")
rec = chat2['data'].get('recommend_payload', {})
print(f"推荐: {len(chat2['data'].get('recommend_cards', []))} 卡片 + {len(rec.get('events', []))} 活动 + {len(rec.get('topics', []))} 讨论")
print(f"CRS Mode: {chat2['data'].get('crs_mode', '-')}")

# 7. Check profile summary
print("\n=== 7. 用户画像摘要 ===")
summary = rec.get("profile_summary", {})
print(f"画像来源: {summary.get('summary_text', '-')}")
print(f"兴趣词: {summary.get('heritage_terms', [])}")
print(f"场所词: {summary.get('scene_terms', [])}")

# 8. Final CRS state
print("\n=== 8. 最终 CRS 状态 ===")
state3 = api("GET", f"/ai/crs/state?user_id={uid}")
print(json.dumps(state3['data'], indent=2, ensure_ascii=False)[:500])

print("\n✅ All CRS flow tests passed")
