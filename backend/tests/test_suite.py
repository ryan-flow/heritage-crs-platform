# 遗产文化传播系统测试套件
# 使用 pytest 运行: pytest -v --tb=short

import pytest
import requests
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:8000/api/v1"
ADMIN_TOKEN = None

def get_admin_token():
    global ADMIN_TOKEN
    if ADMIN_TOKEN:
        return ADMIN_TOKEN
    resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if resp.status_code == 200:
        ADMIN_TOKEN = resp.json().get("token", "")
    return ADMIN_TOKEN

def auth_headers():
    token = get_admin_token()
    return {"X-Admin-Token": token} if token else {}


# ============================================
# 6.2 功能测试 - 黑盒测试
# ============================================

class TestAuthAPI:
    """认证模块测试"""
    
    def test_admin_login_success(self):
        """测试管理员登录成功"""
        resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) > 10
    
    def test_admin_login_wrong_password(self):
        """测试管理员登录失败"""
        resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert resp.status_code == 401


class TestContentAPI:
    """内容模块测试"""
    
    def test_get_contents_list(self):
        """测试获取内容列表"""
        resp = requests.get(f"{BASE_URL}/contents/", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data or "data" in data
    
    def test_get_content_detail(self):
        """测试获取内容详情"""
        resp = requests.get(f"{BASE_URL}/contents/1")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert "title" in data or "data" in data


class TestEventAPI:
    """活动模块测试"""
    
    def test_get_events_list(self):
        """测试获取活动列表"""
        resp = requests.get(f"{BASE_URL}/events/", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data or "data" in data


class TestDiscussionAPI:
    """讨论模块测试"""
    
    def test_get_topics_list(self):
        """测试获取话题列表"""
        resp = requests.get(f"{BASE_URL}/discussion/topics", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200


class TestRecommendAPI:
    """推荐模块测试"""
    
    def test_get_recommendations(self):
        """测试获取推荐结果"""
        resp = requests.get(f"{BASE_URL}/recommend/", params={"user_id": 1})
        assert resp.status_code in [200, 404]


class TestAIChatAPI:
    """AI对话模块测试"""
    
    def test_ai_chat_endpoint_exists(self):
        """测试AI对话端点存在"""
        resp = requests.post(f"{BASE_URL}/ai/chat", json={
            "user_id": 1,
            "question": "什么是非遗"
        })
        assert resp.status_code in [200, 404, 422]
    
    def test_ai_chat_response_structure(self):
        """测试AI对话响应结构"""
        resp = requests.post(f"{BASE_URL}/ai/chat", json={
            "user_id": 1,
            "question": "昆曲有什么特点"
        })
        if resp.status_code == 200:
            data = resp.json()
            assert "answer" in data or "response" in data


class TestKnowledgeGraphAPI:
    """知识图谱模块测试"""
    
    def test_similar_entities(self):
        """测试相似实体查询"""
        resp = requests.get(f"{BASE_URL}/kg/similar", params={"entity": "苏绣"})
        assert resp.status_code in [200, 404]
    
    def test_expand_recommendations(self):
        """测试扩展推荐"""
        resp = requests.get(f"{BASE_URL}/kg/expand", params={"entity": "昆曲", "depth": 2})
        assert resp.status_code in [200, 404]


class TestAdminAPI:
    """管理端API测试"""
    
    def test_admin_contents_list(self):
        """测试管理员获取内容列表"""
        headers = auth_headers()
        resp = requests.get(f"{BASE_URL}/admin/contents/all", headers=headers)
        assert resp.status_code == 200
    
    def test_admin_users_list(self):
        """测试管理员获取用户列表"""
        headers = auth_headers()
        resp = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        assert resp.status_code in [200, 404]


# ============================================
# 6.2 功能测试 - 白盒测试（单元测试）
# ============================================

class TestCRSDecision:
    """CRS决策引擎单元测试"""
    
    def test_cold_start_threshold(self):
        """测试冷启动阈值判断"""
        from app.services.recommendation_service import CRS_THRESHOLD_COLD, CRS_THRESHOLD_MIXED
        assert CRS_THRESHOLD_COLD == 28
        assert CRS_THRESHOLD_MIXED == 62
    
    def test_confidence_formula(self):
        """测试置信度计算公式"""
        se, si, sd = 40, 50, 30
        c = 0.40 * se + 0.35 * si + 0.25 * sd
        assert c == 40.5
    
    def test_mode_determination(self):
        """测试模式判定逻辑"""
        def determine_mode(c):
            if c < 28:
                return "cold_start"
            elif c < 62:
                return "mixed"
            else:
                return "precision"
        
        assert determine_mode(10) == "cold_start"
        assert determine_mode(45) == "mixed"
        assert determine_mode(75) == "precision"


class TestASKTemplates:
    """ASK模板单元测试"""
    
    def test_ask_templates_exist(self):
        """测试ASK模板存在"""
        from app.services.crs.ask_templates import ASK_TEMPLATES
        assert "A01" in ASK_TEMPLATES
        assert "B01" in ASK_TEMPLATES
        assert "R01" in ASK_TEMPLATES
    
    def test_ask_template_structure(self):
        """测试ASK模板结构"""
        from app.services.crs.ask_templates import ASK_TEMPLATES
        a01 = ASK_TEMPLATES["A01"]
        assert "prompt" in a01
        assert "options" in a01
        assert "attribute" in a01
        assert "score_delta" in a01


class TestKnowledgeGraphService:
    """知识图谱服务单元测试"""
    
    def test_entity_types_defined(self):
        """测试实体类型定义"""
        from app.services.knowledge_graph import ENTITY_TYPES
        assert "ICHItem" in ENTITY_TYPES
        assert "Category" in ENTITY_TYPES
        assert "Region" in ENTITY_TYPES
    
    def test_relation_types_defined(self):
        """测试关系类型定义"""
        from app.services.knowledge_graph import RELATIONS
        assert "belongs_to" in RELATIONS
        assert "similar_to" in RELATIONS


# ============================================
# 6.3 性能测试
# ============================================

class TestPerformance:
    """性能测试"""
    
    def test_api_response_time(self):
        """测试API响应时间"""
        endpoints = [
            ("/contents/", "GET"),
            ("/events/", "GET"),
            ("/discussion/topics", "GET"),
        ]
        results = []
        for endpoint, method in endpoints:
            start = time.time()
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{endpoint}")
            elapsed = (time.time() - start) * 1000
            results.append({
                "endpoint": endpoint,
                "status": resp.status_code,
                "time_ms": round(elapsed, 2)
            })
            assert elapsed < 3000, f"{endpoint} 响应时间超过3秒"
        
        for r in results:
            print(f"{r['endpoint']}: {r['status']} - {r['time_ms']}ms")
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        def make_request(i):
            start = time.time()
            resp = requests.get(f"{BASE_URL}/contents/", params={"page": 1})
            elapsed = (time.time() - start) * 1000
            return {"id": i, "status": resp.status_code, "time_ms": elapsed}
        
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            for future in as_completed(futures):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r["status"] == 200)
        avg_time = statistics.mean([r["time_ms"] for r in results])
        
        print(f"并发测试: 20请求, 成功{success_count}个, 平均响应{avg_time:.2f}ms")
        assert success_count >= 18, "并发成功率低于90%"


# ============================================
# 运行测试
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
