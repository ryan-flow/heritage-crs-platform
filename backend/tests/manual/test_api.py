import urllib.request, urllib.error, json

BASE = "http://127.0.0.1:8000/api/v1"

def api(path, token=None, method="GET", body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-Admin-Token", token)
    try:
        with urllib.request.urlopen(req) as resp:
            return {"code": 200, "data": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        return {"code": e.code, "error": e.read().decode()}

# 登录
login = api("/auth/admin/login", method="POST", body={"username":"admin","password":"admin123"})
print("登录:", login.get("code"), login.get("error",""))
token = login.get("data", {}).get("token", "")
print("Token:", token[:20] + "..." if token else "无")

# 测 /admin/contents/all
r = api("/admin/contents/all", token)
items = r.get("data", {}).get("data", {}).get("items", [])
print(f"/admin/contents/all -> code={r.get('code')} items={len(items)}")

# 测 /admin/contents/1
r2 = api("/admin/contents/1", token)
title = r2.get("data", {}).get("data", {}).get("title", "")
print(f"/admin/contents/1 -> code={r2.get('code')} title={str(title)[:30]}")
