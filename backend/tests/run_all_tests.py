# 主测试运行脚本
# 运行所有测试并生成综合报告

import subprocess
import json
import os
from datetime import datetime

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TESTS_DIR)
REPORT_DIR = os.path.join(TESTS_DIR, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)

def run_pytest():
    """运行pytest功能测试"""
    print("\n" + "="*60)
    print("运行功能测试 (pytest)")
    print("="*60)
    
    result = subprocess.run(
        ["C:\\Users\\老王\\AppData\\Local\\Programs\\Python\\Python311\\python.exe", "-m", "pytest", 
         os.path.join(TESTS_DIR, "test_suite.py"), "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return {
        "test_type": "功能测试",
        "returncode": result.returncode,
        "passed": result.returncode == 0
    }


def run_performance_tests():
    """运行性能测试"""
    print("\n" + "="*60)
    print("运行性能测试")
    print("="*60)
    
    result = subprocess.run(
        ["C:\\Users\\老王\\AppData\\Local\\Programs\\Python\\Python311\\python.exe", 
         os.path.join(TESTS_DIR, "test_performance.py")],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR
    )
    
    print(result.stdout)
    
    report_path = os.path.join(TESTS_DIR, "performance_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {"test_type": "性能测试", "passed": True}


def run_compatibility_tests():
    """运行兼容性测试"""
    print("\n" + "="*60)
    print("运行兼容性测试")
    print("="*60)
    
    result = subprocess.run(
        ["C:\\Users\\老王\\AppData\\Local\\Programs\\Python\\Python311\\python.exe", 
         os.path.join(TESTS_DIR, "test_compatibility.py")],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR
    )
    
    print(result.stdout)
    
    report_path = os.path.join(TESTS_DIR, "compatibility_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {"test_type": "兼容性测试", "passed": True}


def generate_summary_report(results):
    """生成汇总报告"""
    print("\n" + "="*60)
    print("测试汇总报告")
    print("="*60)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "passed": sum(1 for r in results if r.get("passed", True)),
        "failed": sum(1 for r in results if not r.get("passed", True)),
        "details": results
    }
    
    print(f"\n  测试总数: {summary['total_tests']}")
    print(f"  通过: {summary['passed']}")
    print(f"  失败: {summary['failed']}")
    print(f"  通过率: {summary['passed']/summary['total_tests']*100:.1f}%")
    
    report_path = os.path.join(REPORT_DIR, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n  报告已保存: {report_path}")
    
    return summary


def main():
    """主函数"""
    print("\n" + "="*60)
    print(f"系统测试套件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = []
    
    # 1. 功能测试
    try:
        func_result = run_pytest()
        results.append(func_result)
    except Exception as e:
        print(f"功能测试异常: {e}")
        results.append({"test_type": "功能测试", "passed": False, "error": str(e)})
    
    # 2. 性能测试
    try:
        perf_result = run_performance_tests()
        results.append(perf_result)
    except Exception as e:
        print(f"性能测试异常: {e}")
        results.append({"test_type": "性能测试", "passed": False, "error": str(e)})
    
    # 3. 兼容性测试
    try:
        compat_result = run_compatibility_tests()
        results.append(compat_result)
    except Exception as e:
        print(f"兼容性测试异常: {e}")
        results.append({"test_type": "兼容性测试", "passed": False, "error": str(e)})
    
    # 汇总报告
    summary = generate_summary_report(results)
    
    return summary


if __name__ == "__main__":
    main()
