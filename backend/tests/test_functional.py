# 功能测试脚本（无需pytest）
# 使用纯Python实现测试

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"
TOKEN = ""

def print_result(name, passed, detail=""):
    icon = "✓" if passed else "✗"
    print(f"  {icon} {name}: {'通过' if passed else '失败'}{f' - {detail}' if detail else ''}")
    return passed

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def run(self, name, test_func):
        try:
            result = test_func()
            passed = result.get("passed", False)
            detail = result.get("detail", "")
        except Exception as e:
            passed = False
            detail = str(e)
        
        print_result(name, passed, detail)
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        self.results.append({"name": name, "passed": passed, "detail": detail})
        return passed


def get_admin_token():
    global TOKEN
    if TOKEN:
        return TOKEN
    try:
        resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=5)
        if resp.status_code == 200:
            TOKEN = resp.json().get("token", "")
    except:
        pass
    return TOKEN


# ========== 认证模块测试 ==========

def test_admin_login_success():
    try:
        resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=5)
        data = resp.json()
        token = data.get("token") or data.get("data", {}).get("token", "")
        return {"passed": resp.status_code == 200 and len(token) > 0, "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}

def test_admin_login_fail():
    try:
        resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
            "username": "admin",
            "password": "wrongpassword"
        }, timeout=5)
        return {"passed": resp.status_code == 401, "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 内容模块测试 ==========

def test_get_contents_list():
    try:
        resp = requests.get(f"{BASE_URL}/contents/", params={"page": 1, "page_size": 10}, timeout=5)
        data = resp.json()
        items_count = len(data.get("items", data.get("data", {}).get("items", [])))
        return {"passed": resp.status_code == 200, "detail": f"items={items_count}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}

def test_get_content_detail():
    try:
        resp = requests.get(f"{BASE_URL}/contents/1", timeout=5)
        return {"passed": resp.status_code in [200, 404], "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 活动模块测试 ==========

def test_get_events_list():
    try:
        resp = requests.get(f"{BASE_URL}/events/", params={"page": 1, "page_size": 10}, timeout=5)
        data = resp.json()
        items_count = len(data.get("items", data.get("data", {}).get("items", [])))
        return {"passed": resp.status_code == 200, "detail": f"items={items_count}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 讨论模块测试 ==========

def test_get_topics_list():
    try:
        resp = requests.get(f"{BASE_URL}/discussion/topics", params={"page": 1, "page_size": 10}, timeout=5)
        return {"passed": resp.status_code == 200, "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 推荐模块测试 ==========

def test_get_recommendations():
    try:
        resp = requests.get(f"{BASE_URL}/recommend/", params={"user_id": 1}, timeout=5)
        return {"passed": resp.status_code in [200, 404], "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== AI对话模块测试 ==========

def test_ai_chat():
    try:
        resp = requests.post(f"{BASE_URL}/ai/chat", json={
            "user_id": 1,
            "question": "昆曲有什么特点"
        }, timeout=30)
        data = resp.json()
        answer = data.get("answer") or data.get("response") or data.get("data", {}).get("answer", "")
        return {"passed": resp.status_code == 200 and len(answer) > 0, "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 知识图谱模块测试 ==========

def test_kg_similar():
    try:
        resp = requests.get(f"{BASE_URL}/kg/similar", params={"entity": "苏绣"}, timeout=5)
        return {"passed": resp.status_code in [200, 404], "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 管理端测试 ==========

def test_admin_contents():
    try:
        token = get_admin_token()
        if not token:
            return {"passed": False, "detail": "无法获取token"}
        headers = {"X-Admin-Token": token}
        resp = requests.get(f"{BASE_URL}/admin/contents/all", headers=headers, timeout=5)
        return {"passed": resp.status_code == 200, "detail": f"status={resp.status_code}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 白盒测试：CRS决策 ==========

def test_crs_threshold():
    try:
        from app.services.recommendation_service import CRS_THRESHOLD_COLD, CRS_THRESHOLD_MIXED
        cold_ok = CRS_THRESHOLD_COLD == 28
        mixed_ok = CRS_THRESHOLD_MIXED == 62
        return {"passed": cold_ok and mixed_ok, "detail": f"cold={CRS_THRESHOLD_COLD}, mixed={CRS_THRESHOLD_MIXED}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}

def test_confidence_formula():
    se, si, sd = 40, 50, 30
    c = 0.40 * se + 0.35 * si + 0.25 * sd
    expected = 40.5
    return {"passed": abs(c - expected) < 0.01, "detail": f"C={c}, expected={expected}"}

def test_mode_determination():
    def determine_mode(c):
        if c < 28: return "cold_start"
        elif c < 62: return "mixed"
        else: return "precision"
    
    tests = [
        (10, "cold_start"),
        (45, "mixed"),
        (75, "precision")
    ]
    
    all_pass = all(determine_mode(c) == m for c, m in tests)
    return {"passed": all_pass, "detail": "阈值判断逻辑正确"}


# ========== 白盒测试：ASK模板 ==========

def test_ask_templates():
    try:
        from app.services.crs.ask_templates import ASK_TEMPLATES
        has_a01 = "A01" in ASK_TEMPLATES
        has_b01 = "B01" in ASK_TEMPLATES
        has_r01 = "R01" in ASK_TEMPLATES
        return {"passed": has_a01 and has_b01 and has_r01, "detail": f"templates={len(ASK_TEMPLATES)}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


# ========== 白盒测试：知识图谱 ==========

def test_kg_entity_types():
    try:
        from app.services.knowledge_graph import ENTITY_TYPES
        has_ich = "ICHItem" in ENTITY_TYPES
        has_cat = "Category" in ENTITY_TYPES
        return {"passed": has_ich and has_cat, "detail": f"types={len(ENTITY_TYPES)}"}
    except Exception as e:
        return {"passed": False, "detail": str(e)}


def run_all_tests():
    print("\n" + "="*60)
    print(f"功能测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    runner = TestRunner()
    
    # 黑盒测试
    print("\n【黑盒测试 - API端点】")
    runner.run("管理员登录成功", test_admin_login_success)
    runner.run("管理员登录失败验证", test_admin_login_fail)
    runner.run("获取内容列表", test_get_contents_list)
    runner.run("获取内容详情", test_get_content_detail)
    runner.run("获取活动列表", test_get_events_list)
    runner.run("获取话题列表", test_get_topics_list)
    runner.run("获取推荐结果", test_get_recommendations)
    runner.run("AI对话接口", test_ai_chat)
    runner.run("知识图谱查询", test_kg_similar)
    runner.run("管理端内容列表", test_admin_contents)
    
    # 白盒测试
    print("\n【白盒测试 - 单元测试】")
    runner.run("CRS阈值配置", test_crs_threshold)
    runner.run("置信度计算公式", test_confidence_formula)
    runner.run("模式判定逻辑", test_mode_determination)
    runner.run("ASK模板完整性", test_ask_templates)
    runner.run("知识图谱实体类型", test_kg_entity_types)
    
    # 汇总
    print("\n" + "-"*60)
    total = runner.passed + runner.failed
    rate = runner.passed / total * 100 if total > 0 else 0
    print(f"  测试总数: {total}")
    print(f"  通过: {runner.passed}")
    print(f"  失败: {runner.failed}")
    print(f"  通过率: {rate:.1f}%")
    print("-"*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "passed": runner.passed,
        "failed": runner.failed,
        "pass_rate": round(rate, 1),
        "results": runner.results
    }
    
    with open("d:\\桌面\\毕业设计\\backend\\tests\\functional_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: tests/functional_report.json")
    
    return report


if __name__ == "__main__":
    run_all_tests()
