# 性能测试脚本
# 测试API响应时间和并发处理能力

import requests
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

def get_admin_token():
    resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if resp.status_code == 200:
        return resp.json().get("token", "")
    return ""

TOKEN = get_admin_token()
HEADERS = {"X-Admin-Token": TOKEN} if TOKEN else {}


def test_single_request(endpoint, method="GET", data=None):
    """单次请求测试"""
    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=10)
        elif method == "POST":
            resp = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=HEADERS, timeout=10)
        elapsed = (time.time() - start) * 1000
        return {
            "endpoint": endpoint,
            "status": resp.status_code,
            "time_ms": round(elapsed, 2),
            "success": resp.status_code in [200, 201]
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status": 0,
            "time_ms": round((time.time() - start) * 1000, 2),
            "success": False,
            "error": str(e)
        }


def test_response_time():
    """响应时间测试"""
    print("\n" + "="*60)
    print("响应时间测试")
    print("="*60)
    
    endpoints = [
        ("/contents/", "GET", "内容列表"),
        ("/events/", "GET", "活动列表"),
        ("/discussion/topics", "GET", "话题列表"),
        ("/recommend/", "GET", "推荐接口"),
        ("/kg/similar?entity=苏绣", "GET", "知识图谱"),
        ("/admin/contents/all", "GET", "管理端内容"),
    ]
    
    results = []
    for endpoint, method, name in endpoints:
        r = test_single_request(endpoint, method)
        r["name"] = name
        results.append(r)
        status_icon = "✓" if r["success"] else "✗"
        print(f"  {status_icon} {name}: {r['status']} - {r['time_ms']}ms")
    
    success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
    avg_time = statistics.mean([r["time_ms"] for r in results])
    
    print(f"\n  成功率: {success_rate:.1f}%")
    print(f"  平均响应时间: {avg_time:.2f}ms")
    
    return {
        "test_name": "响应时间测试",
        "success_rate": success_rate,
        "avg_time_ms": round(avg_time, 2),
        "details": results
    }


def test_concurrent_load(concurrent_users=10, requests_per_user=5):
    """并发负载测试"""
    print("\n" + "="*60)
    print(f"并发负载测试 ({concurrent_users}用户 x {requests_per_user}请求)")
    print("="*60)
    
    def user_session(user_id):
        results = []
        for i in range(requests_per_user):
            r = test_single_request("/contents/", "GET")
            r["user_id"] = user_id
            results.append(r)
        return results
    
    all_results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(user_session, i) for i in range(concurrent_users)]
        for future in as_completed(futures):
            all_results.extend(future.result())
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in all_results if r["success"])
    success_rate = success_count / len(all_results) * 100
    avg_time = statistics.mean([r["time_ms"] for r in all_results])
    p50 = statistics.median([r["time_ms"] for r in all_results])
    p90 = sorted([r["time_ms"] for r in all_results])[int(len(all_results) * 0.9)]
    
    print(f"  总请求数: {len(all_results)}")
    print(f"  成功请求: {success_count}")
    print(f"  成功率: {success_rate:.1f}%")
    print(f"  总耗时: {total_time:.2f}s")
    print(f"  吞吐量: {len(all_results)/total_time:.1f} req/s")
    print(f"  平均响应: {avg_time:.2f}ms")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P90: {p90:.2f}ms")
    
    return {
        "test_name": "并发负载测试",
        "concurrent_users": concurrent_users,
        "total_requests": len(all_results),
        "success_count": success_count,
        "success_rate": round(success_rate, 1),
        "total_time_s": round(total_time, 2),
        "throughput_rps": round(len(all_results)/total_time, 1),
        "avg_time_ms": round(avg_time, 2),
        "p50_ms": round(p50, 2),
        "p90_ms": round(p90, 2)
    }


def test_ai_chat_performance():
    """AI对话性能测试"""
    print("\n" + "="*60)
    print("AI对话性能测试")
    print("="*60)
    
    questions = [
        "昆曲有什么特点",
        "苏绣和湘绣的区别",
        "非遗保护的意义",
    ]
    
    results = []
    for q in questions:
        start = time.time()
        try:
            resp = requests.post(f"{BASE_URL}/ai/chat", json={
                "user_id": 1,
                "question": q
            }, timeout=30)
            elapsed = (time.time() - start) * 1000
            results.append({
                "question": q,
                "status": resp.status_code,
                "time_ms": round(elapsed, 2),
                "success": resp.status_code == 200
            })
            icon = "✓" if resp.status_code == 200 else "✗"
            print(f"  {icon} '{q[:15]}...': {resp.status_code} - {elapsed:.0f}ms")
        except Exception as e:
            results.append({
                "question": q,
                "status": 0,
                "time_ms": 0,
                "success": False,
                "error": str(e)
            })
            print(f"  ✗ '{q[:15]}...': 错误 - {e}")
    
    success_results = [r for r in results if r["success"]]
    if success_results:
        avg_time = statistics.mean([r["time_ms"] for r in success_results])
        print(f"\n  AI对话平均响应: {avg_time:.0f}ms")
    
    return {
        "test_name": "AI对话性能测试",
        "results": results
    }


def run_all_performance_tests():
    """运行所有性能测试"""
    print("\n" + "="*60)
    print(f"性能测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "tests": []
    }
    
    report["tests"].append(test_response_time())
    report["tests"].append(test_concurrent_load(10, 5))
    report["tests"].append(test_ai_chat_performance())
    
    with open("d:\\桌面\\毕业设计\\backend\\tests\\performance_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("测试报告已保存: tests/performance_report.json")
    print("="*60)
    
    return report


if __name__ == "__main__":
    run_all_performance_tests()
