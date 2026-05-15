import urllib.request, urllib.error, json

BASE = "http://127.0.0.1:8000/api/v1"

# 登录
data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request(BASE + "/auth/admin/login", data=data, method="POST")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req) as r:
    resp = json.loads(r.read())
token = resp["data"]["token"]
print(f"登录 OK, token={token[:15]}...")

# 测 admin/contents/all
req2 = urllib.request.Request(BASE + "/admin/contents/all")
req2.add_header("X-Admin-Token", token)
try:
    with urllib.request.urlopen(req2) as r:
        data2 = json.loads(r.read())
        items = data2.get("data", {}).get("items", [])
        print(f"GET /admin/contents/all -> 200, items={len(items)}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"GET /admin/contents/all -> {e.code} {body[:200]}")

# 测 admin/contents/1
req3 = urllib.request.Request(BASE + "/admin/contents/1")
req3.add_header("X-Admin-Token", token)
try:
    with urllib.request.urlopen(req3) as r:
        data3 = json.loads(r.read())
        print(f"GET /admin/contents/1 -> 200, title={data3.get('data',{}).get('title','')[:30]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"GET /admin/contents/1 -> {e.code} {body[:200]}")
