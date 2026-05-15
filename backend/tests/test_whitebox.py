# 白盒测试脚本（需要在backend目录下运行）
# 测试核心算法和业务逻辑

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

def run_whitebox_tests():
    print("\n" + "="*60)
    print(f"白盒测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = []
    passed = 0
    failed = 0
    
    # 1. CRS阈值测试
    print("\n【CRS决策引擎测试】")
    try:
        from app.services.recommendation_service import CRS_THRESHOLD_COLD, CRS_THRESHOLD_MIXED
        test1 = CRS_THRESHOLD_COLD == 28
        test2 = CRS_THRESHOLD_MIXED == 62
        icon = "✓" if test1 and test2 else "✗"
        print(f"  {icon} CRS阈值配置: cold={CRS_THRESHOLD_COLD}, mixed={CRS_THRESHOLD_MIXED}")
        if test1 and test2:
            passed += 1
        else:
            failed += 1
        results.append({"name": "CRS阈值配置", "passed": test1 and test2})
    except Exception as e:
        print(f"  ✗ CRS阈值配置: 导入失败 - {e}")
        failed += 1
        results.append({"name": "CRS阈值配置", "passed": False, "error": str(e)})
    
    # 2. 置信度公式测试
    try:
        from app.services.recommendation_service import calc_confidence
        print(f"  ✓ 置信度计算函数: 已导入")
        passed += 1
        results.append({"name": "置信度计算函数", "passed": True})
    except Exception as e:
        print(f"  ✗ 置信度计算函数: 导入失败 - {e}")
        failed += 1
        results.append({"name": "置信度计算函数", "passed": False, "error": str(e)})
    
    # 3. ASK模板测试
    print("\n【ASK模板测试】")
    try:
        from app.services.crs.ask_templates import ASK_TEMPLATES, SKIP_ANSWERS, RECOMMEND_INTENT_TERMS
        has_a = all(k in ASK_TEMPLATES for k in ["A01", "A02", "A03", "A04", "A05"])
        has_b = all(k in ASK_TEMPLATES for k in ["B01", "B02", "B03", "B04", "B05"])
        has_r = all(k in ASK_TEMPLATES for k in ["R01", "R02", "R03"])
        icon = "✓" if has_a and has_b and has_r else "✗"
        print(f"  {icon} ASK模板完整性: A组5个, B组5个, R组3个, 共{len(ASK_TEMPLATES)}个")
        if has_a and has_b and has_r:
            passed += 1
        else:
            failed += 1
        results.append({"name": "ASK模板完整性", "passed": has_a and has_b and has_r})
        
        # 测试SKIP_ANSWERS
        skip_ok = "跳过" in SKIP_ANSWERS or "暂时跳过" in SKIP_ANSWERS
        icon2 = "✓" if skip_ok else "✗"
        print(f"  {icon2} 跳过答案集合: {len(SKIP_ANSWERS)}项")
        if skip_ok:
            passed += 1
        else:
            failed += 1
        results.append({"name": "跳过答案集合", "passed": skip_ok})
    except Exception as e:
        print(f"  ✗ ASK模板测试: 导入失败 - {e}")
        failed += 2
        results.append({"name": "ASK模板测试", "passed": False, "error": str(e)})
    
    # 4. 知识图谱测试
    print("\n【知识图谱测试】")
    try:
        from app.services.knowledge_graph import ENTITY_TYPES, RELATIONS, KnowledgeGraphService
        entity_ok = len(ENTITY_TYPES) >= 5
        relation_ok = len(RELATIONS) >= 5
        icon = "✓" if entity_ok and relation_ok else "✗"
        print(f"  {icon} 实体类型: {len(ENTITY_TYPES)}种 - {list(ENTITY_TYPES.keys())[:3]}...")
        print(f"  {icon} 关系类型: {len(RELATIONS)}种 - {list(RELATIONS.keys())[:3]}...")
        if entity_ok and relation_ok:
            passed += 1
        else:
            failed += 1
        results.append({"name": "知识图谱结构", "passed": entity_ok and relation_ok})
    except Exception as e:
        print(f"  ✗ 知识图谱测试: 导入失败 - {e}")
        failed += 1
        results.append({"name": "知识图谱结构", "passed": False, "error": str(e)})
    
    # 5. CRS决策测试
    print("\n【CRS决策测试】")
    try:
        from app.services.crs.decision import crs_decide, select_cold_start_ask
        print(f"  ✓ CRS决策函数: 已导入")
        passed += 1
        results.append({"name": "CRS决策函数", "passed": True})
    except Exception as e:
        print(f"  ✗ CRS决策函数: 导入失败 - {e}")
        failed += 1
        results.append({"name": "CRS决策函数", "passed": False, "error": str(e)})
    
    # 6. 数据模型测试
    print("\n【数据模型测试】")
    try:
        from app.models import User, Content, Activity, DiscussionTopic
        print(f"  ✓ 核心数据模型: User, Content, Activity, DiscussionTopic")
        passed += 1
        results.append({"name": "核心数据模型", "passed": True})
    except Exception as e:
        print(f"  ✗ 核心数据模型: 导入失败 - {e}")
        failed += 1
        results.append({"name": "核心数据模型", "passed": False, "error": str(e)})
    
    # 汇总
    total = passed + failed
    rate = passed / total * 100 if total > 0 else 0
    
    print("\n" + "-"*60)
    print(f"  白盒测试总数: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print(f"  通过率: {rate:.1f}%")
    print("-"*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "白盒测试",
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(rate, 1),
        "results": results
    }
    
    with open("d:\\桌面\\毕业设计\\backend\\tests\\whitebox_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: tests/whitebox_report.json")
    
    return report


if __name__ == "__main__":
    run_whitebox_tests()
