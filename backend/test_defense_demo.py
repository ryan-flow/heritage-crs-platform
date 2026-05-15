#!/usr/bin/env python3
"""答辩演示路径检测脚本

8轮对话完整覆盖 CRS 推荐算法核心能力：
  R1 冷启动+KB高置信度命中
  R2 KG实体识别+偏好同步
  R3 追问检测+KG相似推荐
  R4 推荐意图驱动策略
  R5 场景偏好检测
  R6 民俗类KB命中+KG实体
  R7 医药类跨类目KB命中
  R8 兜底回答/特定KB回答

每轮检测：结构正确性 + AI回答质量审查
"""
import sys
import time
import json

sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.ai_service import ai_answer
from app.services.recommendation_service import calc_confidence
from app.models.user import User

engine = create_engine(settings.sqlite_url)
Session = sessionmaker(bind=engine)

DEMO_USER_ID = 16

ROUNDS = [
    {
        "id": "R1",
        "name": "冷启动+KB高置信度命中",
        "question": "昆曲为什么被称为百戏之祖？",
        "expect": {
            "source_in": ["kb_enhanced", "local_kb"],
            "min_confidence": 0.80,
            "has_cards": True,
            "kg_entity": "",
            "answer_keywords": ["昆曲", "戏曲"],
        },
    },
    {
        "id": "R2",
        "name": "KG实体识别+偏好同步",
        "question": "苏绣有什么特点",
        "expect": {
            "source_in": ["kb_enhanced", "local_kb", "doubao"],
            "min_confidence": 0.70,
            "has_cards": True,
            "kg_entity": "苏绣",
            "answer_keywords": ["绣", "工艺"],
        },
    },
    {
        "id": "R3",
        "name": "追问检测+KG相似推荐",
        "question": "蜀绣和苏绣有什么区别",
        "expect": {
            "source_in": ["kb_enhanced", "doubao", "local_kb"],
            "min_confidence": 0.60,
            "has_cards": True,
            "kg_entity": "苏绣",
            "kg_similar_has": ["蜀绣", "湘绣"],
            "answer_keywords": ["绣"],
        },
    },
    {
        "id": "R4",
        "name": "推荐意图驱动策略",
        "question": "推荐一些传统工艺的内容",
        "expect": {
            "source_in": ["kb_enhanced", "doubao", "local_kb"],
            "min_confidence": 0.60,
            "has_cards": True,
            "strategy_in": ["intent_driven_rec", "precision", "mixed"],
            "kg_entity": "",
            "answer_keywords": ["内容", "活动"],
        },
    },
    {
        "id": "R5",
        "name": "场景偏好检测",
        "question": "有没有线下体验活动",
        "expect": {
            "source_in": ["kb_enhanced", "doubao", "local_kb"],
            "min_confidence": 0.60,
            "has_cards": True,
            "strategy_in": ["intent_driven_rec", "precision", "mixed"],
            "kg_entity": "",
            "answer_keywords": ["活动", "体验"],
        },
    },
    {
        "id": "R6",
        "name": "民俗类KB命中+KG实体",
        "question": "端午节为什么属于活态非遗",
        "expect": {
            "source_in": ["kb_enhanced", "local_kb", "doubao"],
            "min_confidence": 0.70,
            "has_cards": True,
            "kg_entity": "端午节",
            "answer_keywords": ["端午", "非遗"],
        },
    },
    {
        "id": "R7",
        "name": "医药类跨类目KB命中",
        "question": "中医针灸的原理是什么",
        "expect": {
            "source_in": ["kb_enhanced", "local_kb", "doubao"],
            "min_confidence": 0.70,
            "has_cards": True,
            "kg_entity": "中医针灸",
            "answer_keywords": ["针", "穴位"],
        },
    },
    {
        "id": "R8",
        "name": "特定KB回答-保护阶段",
        "question": "中国非遗保护经历了哪些重要阶段",
        "expect": {
            "source_in": ["kb_enhanced", "local_kb", "doubao", "fallback"],
            "min_confidence": 0.50,
            "has_cards": True,
            "kg_entity": "",
            "answer_keywords": ["保护", "阶段"],
        },
    },
]

PASS = 0
FAIL = 0
WARN = 0


def _check(cond, label, detail=""):
    global PASS, FAIL, WARN
    if cond:
        PASS += 1
        tag = "PASS"
    else:
        if "quality" in label or "keyword" in label:
            WARN += 1
            tag = "WARN"
        else:
            FAIL += 1
            tag = "FAIL"
    msg = f"  [{tag}] {label}"
    if detail:
        msg += f": {detail}"
    print(msg)
    return cond


def review_answer_quality(answer, question, expect):
    """审查AI回答质量"""
    issues = []

    if not answer or len(answer) < 10:
        issues.append("回答过短(<10字)")
    elif len(answer) > 500:
        issues.append("回答过长(>500字)")

    if "来源" in answer and "豆包" in answer:
        issues.append("回答含豆包来源标记(未清洗)")

    if "抱歉" in answer and "无法" in answer:
        if "fallback" not in expect.get("source_in", []):
            issues.append("非兜底场景出现拒绝回答")

    keywords = expect.get("answer_keywords", [])
    hit = [kw for kw in keywords if kw in answer]
    if keywords and not hit:
        issues.append(f"回答未包含预期关键词{keywords}")

    return issues


def show_user_state(db, user_id, label=""):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"  [!] User {user_id} 不存在")
        return None
    conf = calc_confidence(db, user_id)
    state = {
        "heritage": user.preferred_heritage_types,
        "scene": user.preferred_scene_types,
        "region": user.preferred_regions,
        "mode": conf.get("mode", "?"),
        "score": conf.get("confidence_score", 0),
    }
    if label:
        print(f"  {label}: mode={state['mode']}(C={state['score']:.1f}), "
              f"heritage={state['heritage']}, scene={state['scene']}, region={state['region']}")
    return state


def run_round(db, round_def, round_num):
    global PASS, FAIL, WARN
    rid = round_def["id"]
    name = round_def["name"]
    question = round_def["question"]
    expect = round_def["expect"]

    print(f"\n{'='*60}")
    print(f"{rid} 第{round_num}轮: {name}")
    print(f"  输入: 「{question}」")
    print(f"{'='*60}")

    state_before = show_user_state(db, DEMO_USER_ID, "对话前状态")

    t0 = time.time()
    try:
        result = ai_answer(db, question, user_id=DEMO_USER_ID)
    except Exception as e:
        print(f"  [FAIL] ai_answer异常: {e}")
        FAIL += 1
        return None
    elapsed = time.time() - t0

    answer = result.get("answer", "")
    source = result.get("source", "")
    confidence = result.get("confidence", 0)
    strategy = result.get("strategy", "")
    crs_mode = result.get("crs_mode", "")
    kg_entity = result.get("kg_entity", "")
    kg_similar = result.get("kg_similar", {})
    cards = result.get("recommend_cards", [])
    crs_conf = result.get("crs_confidence", {})
    ask_prompt = result.get("ask_prompt", "")
    ask_options = result.get("ask_options", [])
    rec_questions = result.get("recommended_questions", [])

    print(f"\n  ── 回答 ──")
    print(f"  {answer[:200]}{'...' if len(answer) > 200 else ''}")
    print(f"\n  ── 结构输出 ──")
    print(f"  source={source}, confidence={confidence:.2f}")
    print(f"  strategy={strategy}({result.get('strategy_display', '')}), crs_mode={crs_mode}")
    print(f"  kg_entity={kg_entity}, cards={len(cards)}")
    if kg_entity:
        similar_names = [item.get("entity", "") for item in kg_similar.get("items", [])[:3]]
        print(f"  kg_similar={similar_names}")
    if ask_prompt:
        print(f"  ask_prompt={ask_prompt[:50]}")
    if ask_options:
        opts = [o[:15] if isinstance(o, str) else o.get('text', '')[:15] for o in (ask_options or [])[:3]]
        print(f"  ask_options={opts}")
    if rec_questions:
        qs = [q[:20] if isinstance(q, str) else q.get('text', '')[:20] for q in rec_questions[:3]]
        print(f"  recommended_questions={qs}")
    print(f"  耗时={elapsed:.1f}s")

    state_after = show_user_state(db, DEMO_USER_ID, "对话后状态")

    print(f"\n  ── 结构检测 ──")

    _check(source in expect["source_in"], f"{rid}-source",
           f"expect={expect['source_in']}, got={source}")

    _check(confidence >= expect["min_confidence"], f"{rid}-confidence",
           f"expect>={expect['min_confidence']}, got={confidence:.2f}")

    if "has_cards" in expect:
        _check(bool(cards) == expect["has_cards"], f"{rid}-cards",
               f"expect={'有' if expect['has_cards'] else '无'}卡片, got={len(cards)}张")

    if "kg_entity" in expect and expect["kg_entity"]:
        _check(kg_entity == expect["kg_entity"], f"{rid}-kg_entity",
               f"expect={expect['kg_entity']}, got={kg_entity}")

    if "strategy_in" in expect:
        _check(strategy in expect["strategy_in"], f"{rid}-strategy",
               f"expect={expect['strategy_in']}, got={strategy}")

    if "kg_similar_has" in expect:
        similar_names = [item.get("entity", "") for item in kg_similar.get("items", [])]
        hit = [e for e in expect["kg_similar_has"] if e in similar_names]
        _check(len(hit) > 0, f"{rid}-kg_similar",
               f"expect含{expect['kg_similar_has']}, got={similar_names}")

    print(f"\n  ── 回答质量审查 ──")
    issues = review_answer_quality(answer, question, expect)
    if issues:
        for issue in issues:
            _check(False, f"{rid}-quality", issue)
    else:
        _check(True, f"{rid}-quality", "回答质量合格")

    _check(len(answer) >= 15, f"{rid}-answer_len",
           f"回答长度={len(answer)}字")

    _check(elapsed < 30, f"{rid}-response_time",
           f"耗时={elapsed:.1f}s")

    return result


def main():
    global PASS, FAIL, WARN

    print("=" * 60)
    print("答辩演示路径检测")
    print("=" * 60)

    db = Session()

    print(f"\n演示用户: User[{DEMO_USER_ID}]")
    show_user_state(db, DEMO_USER_ID, "初始状态")

    results = []
    for i, r in enumerate(ROUNDS, 1):
        result = run_round(db, r, i)
        results.append(result)
        if i < len(ROUNDS):
            time.sleep(2)

    print(f"\n\n{'='*60}")
    print("答辩路径总览")
    print(f"{'='*60}")
    print(f"{'轮次':<6}{'问题':<28}{'来源':<14}{'策略':<18}{'模式':<10}{'KG实体':<10}{'卡片':<6}")
    print("-" * 92)
    for i, (r, result) in enumerate(zip(ROUNDS, results), 1):
        if result:
            q_short = r["question"][:12] + ("..." if len(r["question"]) > 12 else "")
            print(f"{r['id']:<6}{q_short:<28}{result.get('source', ''):<14}"
                  f"{result.get('strategy', ''):<18}{result.get('crs_mode', ''):<10}"
                  f"{result.get('kg_entity', '-'):<10}{len(result.get('recommend_cards', [])):<6}")
        else:
            print(f"{r['id']:<6}{r['question'][:12]:<28}FAILED")

    print(f"\n{'='*60}")
    print(f"检测结果: PASS={PASS}, WARN={WARN}, FAIL={FAIL}")
    if FAIL == 0:
        print("✓ 所有结构检测通过，答辩路径可用")
    else:
        print("✗ 存在FAIL项，需要修复后再答辩")
    print(f"{'='*60}")

    db.close()


if __name__ == "__main__":
    main()
