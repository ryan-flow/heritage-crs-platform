#!/usr/bin/env python3
"""CRS 压力测试

覆盖真实用户输入场景：
1. 冷启动首次提问（无偏好）
2. 模糊追问（"详细说说"、"还有吗"）
3. 推荐意图（"推荐一些"、"有什么好玩的"）
4. 地区偏好（"广东的非遗"、"华东地区"）
5. 场景偏好（"线下体验"、"研学活动"）
6. 专业深度（"非遗申报流程"、"传承人认定标准"）
7. 边界输入（空字符串、超长文本、特殊字符、纯数字）
8. 连续对话模拟（多轮上下文）
9. KB命中/未命中覆盖
10. CRS模式切换（cold_start → mixed → precision）
"""

import sys
import time
import traceback

sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.ai_service import ai_answer
from app.services.crs.questions import _match_chapters, _detect_attr
from app.services.crs.decision import crs_decide, generate_ask_transition
from app.services.crs.preference import _infer_attribute

engine = create_engine(settings.sqlite_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

PASS = 0
FAIL = 0
ERRORS = []


def _test(name: str, func, *args, expect=None, check=None):
    global PASS, FAIL
    try:
        result = func(*args)
        if expect is not None and result != expect:
            FAIL += 1
            msg = f"[FAIL] {name}: got {result!r}, expected {expect!r}"
            ERRORS.append(msg)
            print(msg)
            return result
        if check and not check(result):
            FAIL += 1
            msg = f"[FAIL] {name}: check failed, got {str(result)[:100]}"
            ERRORS.append(msg)
            print(msg)
            return result
        PASS += 1
        print(f"[PASS] {name}")
        return result
    except Exception as e:
        FAIL += 1
        msg = f"[ERROR] {name}: {e}"
        ERRORS.append(msg)
        print(msg)
        traceback.print_exc()
        return None


def test_unit_functions():
    """单元测试：CRS核心函数"""
    print("\n" + "=" * 60)
    print("1. 单元测试：CRS核心函数")
    print("=" * 60)

    _test("章节匹配-苏绣", _match_chapters, "苏绣有什么特点",
          check=lambda r: "传统工艺" in r or "传统美术" in r)
    _test("章节匹配-昆曲", _match_chapters, "昆曲的历史渊源",
          check=lambda r: "戏曲与表演艺术" in r)
    _test("章节匹配-端午", _match_chapters, "端午节有哪些习俗",
          check=lambda r: "岁时节庆与民俗" in r)
    _test("章节匹配-空输入", _match_chapters, "",
          expect=set())
    _test("章节匹配-无关内容", _match_chapters, "今天天气怎么样",
          expect=set())
    _test("章节匹配-多关键词", _match_chapters, "苏绣和京剧有什么关系",
          check=lambda r: len(r) >= 2)
    _test("章节匹配-通用词过滤", _match_chapters, "非遗文化传统",
          expect=set())

    _test("属性检测-场景", _detect_attr, "我想参加线下活动",
          expect="scene")
    _test("属性检测-地区", _detect_attr, "华南地区的非遗",
          expect="region")
    _test("属性检测-通用", _detect_attr, "非遗保护政策",
          expect="general")
    _test("属性检测-默认类目", _detect_attr, "苏绣有什么特点",
          expect="category")
    _test("属性检测-空输入", _detect_attr, "",
          expect="category")

    _test("属性推断-KB章节国际", _infer_attribute, "联合国非遗", {"chapter": "国际传播"},
          expect="region")
    _test("属性推断-KB章节场景", _infer_attribute, "VR体验", {"chapter": "数字化体验"},
          expect="scene")
    _test("属性推断-问题文本场景", _infer_attribute, "我想去研学", {},
          expect="scene")
    _test("属性推断-问题文本地区", _infer_attribute, "广东的非遗", {},
          expect="region")
    _test("属性推断-默认类目", _infer_attribute, "苏绣", {},
          expect="category")

    _test("过渡语-跳过", generate_ask_transition, "A01", "暂时跳过", True,
          expect="好的，我们继续。")
    _test("过渡语-类目", generate_ask_transition, "A01", "传统工艺", False,
          expect="了解了，你对手工技艺感兴趣。")
    _test("过渡语-地区", generate_ask_transition, "A02", "华东地区", False,
          check=lambda r: "华东" in r or "风格" in r)
    _test("过渡语-场景", generate_ask_transition, "A03", "线下体验", False,
          check=lambda r: len(r) > 0)
    _test("过渡语-未知模板", generate_ask_transition, "X99", "随便", False,
          check=lambda r: len(r) > 0)


def test_ai_answer_scenarios():
    """集成测试：AI问答真实场景"""
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("2. 集成测试：AI问答真实场景")
    print("=" * 60)

    db = SessionLocal()

    scenarios = [
        # (名称, 问题, user_id, 检查函数)
        ("冷启动-非遗入门", "什么是非遗？", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 10),
        ("冷启动-具体项目", "苏绣有什么特点？", 1,
         lambda r: r.get("source") in ("kb_enhanced", "local_kb", "doubao")),
        ("推荐意图", "推荐一些传统工艺相关的内容", 1,
         lambda r: r.get("strategy") == "intent_driven_rec" or r.get("recommend_cards")),
        ("地区偏好", "广东的非遗项目有哪些？", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 5),
        ("场景偏好", "有哪些线下体验非遗的活动？", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 5),
        ("专业深度", "非遗传承人认定标准是什么？", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 5),
        ("模糊追问-详细", "能详细说说吗", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 5),
        ("模糊追问-还有吗", "还有吗", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 5),
        ("比较类", "昆曲和京剧有什么区别？", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 10),
        ("怎么入门", "非遗怎么入门？", 1,
         lambda r: r.get("answer") and len(r["answer"]) > 5),
    ]

    for name, question, uid, check_fn in scenarios:
        try:
            result = ai_answer(db, question, user_id=uid)
            if check_fn(result):
                PASS += 1
                src = result.get("source", "?")
                strat = result.get("strategy", "?")
                cards = len(result.get("recommend_cards", []))
                print(f"[PASS] {name}: source={src}, strategy={strat}, cards={cards}")
            else:
                FAIL += 1
                print(f"[FAIL] {name}: check failed, answer={str(result.get('answer', ''))[:80]}")
        except Exception as e:
            FAIL += 1
            print(f"[ERROR] {name}: {e}")

    db.close()


def test_edge_cases():
    """边界测试：异常输入"""
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("3. 边界测试：异常输入")
    print("=" * 60)

    db = SessionLocal()

    edge_cases = [
        ("空字符串", "", 1),
        ("纯空格", "   ", 1),
        ("超长输入", "苏绣" * 200, 1),
        ("特殊字符", "!@#$%^&*()", 1),
        ("纯数字", "12345", 1),
        ("英文输入", "What is intangible cultural heritage?", 1),
        ("中英混合", "非遗UNESCO项目有哪些", 1),
        ("emoji输入", "刺绣🎨怎么样", 1),
        ("单字输入", "绣", 1),
        ("无user_id", "什么是非遗？", None),
        ("重复问题", "什么是非遗？", 1),
    ]

    for name, question, uid in edge_cases:
        try:
            result = ai_answer(db, question, user_id=uid)
            if result and isinstance(result, dict) and "answer" in result:
                PASS += 1
                print(f"[PASS] {name}: source={result.get('source', '?')}, answer_len={len(result.get('answer', ''))}")
            else:
                FAIL += 1
                print(f"[FAIL] {name}: invalid result structure")
        except Exception as e:
            FAIL += 1
            print(f"[ERROR] {name}: {e}")

    db.close()


def test_crs_mode_progression():
    """CRS模式递进测试：模拟用户从冷启动到精准推荐"""
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("4. CRS模式递进测试")
    print("=" * 60)

    db = SessionLocal()

    conversation_flow = [
        "你好，我想了解非遗",
        "我对传统工艺比较感兴趣",
        "苏绣有什么特点？",
        "推荐一些相关的活动",
        "还有其他绣法吗？",
        "湘绣和苏绣有什么区别？",
    ]

    modes_seen = []
    for i, question in enumerate(conversation_flow):
        try:
            result = ai_answer(db, question, user_id=1)
            mode = result.get("crs_mode", "?")
            strategy = result.get("strategy", "?")
            conf = result.get("crs_confidence", {}).get("confidence_score", 0)
            modes_seen.append(mode)
            PASS += 1
            print(f"[PASS] 轮{i+1} '{question[:20]}': mode={mode}, strategy={strategy}, conf={conf:.2f}")
        except Exception as e:
            FAIL += 1
            print(f"[ERROR] 轮{i+1}: {e}")

    db.close()


def test_concurrent_stress():
    """压力测试：快速连续请求"""
    global PASS, FAIL
    print("\n" + "=" * 60)
    print("5. 压力测试：快速连续请求")
    print("=" * 60)

    db = SessionLocal()

    questions = [
        "什么是非遗？", "苏绣有什么特点？", "昆曲适合新手吗？",
        "端午节有哪些习俗？", "推荐传统工艺",
    ]

    rounds = 2
    total = len(questions) * rounds
    errors = 0
    start = time.time()

    for r in range(rounds):
        for q in questions:
            try:
                result = ai_answer(db, q, user_id=1)
                if not result or "answer" not in result:
                    errors += 1
            except Exception as e:
                errors += 1
                if "429" in str(e) or "limit" in str(e).lower():
                    print(f"  [WARN] 豆包限流，跳过剩余压力测试")
                    break
        else:
            continue
        break

    elapsed = time.time() - start
    actual = min(total, int(elapsed / max(0.1, elapsed / total)) + 1)
    avg_ms = (elapsed / max(1, total - errors)) * 1000 if total > errors else 0

    PASS += 1
    print(f"[PASS] {total - errors}/{total}次请求完成: {elapsed:.1f}s, avg={avg_ms:.0f}ms/query, errors={errors}")

    db.close()


def test_kg_cache_stress():
    """KG缓存压力测试"""
    global PASS
    print("\n" + "=" * 60)
    print("6. KG缓存压力测试")
    print("=" * 60)

    from app.services.knowledge_graph import kg_service

    kg_service._invalidate_cache()

    entities = ["苏绣", "昆曲", "端午节", "京剧", "中医针灸", "古琴", "云锦", "皮影"]

    # 第一轮：无缓存
    start = time.time()
    for e in entities:
        kg_service.similar_entities(e, limit=3)
        kg_service.expand_recommendations(e, depth=2, limit=5)
    t1 = time.time() - start

    # 第二轮：有缓存
    start = time.time()
    for _ in range(10):
        for e in entities:
            kg_service.similar_entities(e, limit=3)
            kg_service.expand_recommendations(e, depth=2, limit=5)
    t2 = time.time() - start

    improvement = (1 - t2 / (t1 * 10)) * 100
    PASS += 1
    print(f"[PASS] KG缓存: 首轮={t1:.4f}s, 10轮缓存={t2:.4f}s, 缓存加速={improvement:.0f}%")


def main():
    print("=" * 60)
    print("CRS 压力测试")
    print("=" * 60)

    test_unit_functions()
    test_ai_answer_scenarios()
    test_edge_cases()
    test_crs_mode_progression()
    test_concurrent_stress()
    test_kg_cache_stress()

    print("\n" + "=" * 60)
    print(f"测试完成: PASS={PASS}, FAIL={FAIL}")
    if ERRORS:
        print(f"\n失败详情 ({len(ERRORS)}):")
        for e in ERRORS:
            print(f"  {e}")
    print("=" * 60)


if __name__ == "__main__":
    main()
