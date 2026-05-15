"""
CRS循环深度测试 - 模拟真实用户用推荐问题进行多轮对话
v2.1.2 验证 + 推荐问题覆盖率测试

测试策略：
1. 每轮对话优先使用系统返回的recommended_questions
2. 跟踪完整的 cold_start → mixed → precision 路径
3. 重点验证第2/3轮推荐问题的命中效果
4. 记录每轮的E/I/D分数变化

用法：python test_crs_realistic.py
"""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"


def api(method: str, path: str, data: dict | None = None) -> dict:
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
                                headers={"Content-Type": "application/json"} if body else {})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": json.loads(e.read())}


def print_state(state: dict, label: str = ""):
    """打印CRS状态摘要"""
    mode = state.get("mode", "?")
    conf = state.get("confidence_score", 0)
    dims = state.get("dimensions", {})
    e = dims.get("explicit", 0)
    i = dims.get("implicit", 0)
    d = dims.get("dialogue", 0)
    turn = state.get("turn_count", 0)
    ask_attr = state.get("last_ask_attribute", "")

    print(f"  [{label}] mode={mode} conf={conf} E={e} I={i} D={d} turn={turn} last_attr={ask_attr}")


def create_test_user(tag: str) -> int:
    """通过wx-login接口创建测试用户"""
    result = api("POST", "/auth/wx-login", {
        "code": f"test_{tag}_crs",
        "nickname": f"测试_{tag}",
    })
    data = result.get("data", {})
    uid = data.get("user_id")
    if uid:
        print(f"  + 创建用户: {tag} (id={uid})")
        return uid
    # 可能已存在（openid相同返回旧用户）
    print(f"  ! 创建用户返回: {json.dumps(result, ensure_ascii=False)[:100]}")
    return uid or 0


def get_crs_state(user_id: int) -> dict:
    """获取CRS状态"""
    return api("GET", f"/ai/crs/state?user_id={user_id}")


def reset_crs(user_id: int) -> dict:
    """重置CRS会话"""
    return api("POST", f"/ai/crs/reset?user_id={user_id}")


def ask_crs(user_id: int, session_id: str, ask_id: str, answer: str) -> dict:
    """回答ASK提问"""
    return api("POST", "/ai/crs/answer", {
        "user_id": user_id,
        "session_id": session_id,
        "ask_id": ask_id,
        "answer": answer,
    })


def chat_ai(user_id: int, question: str) -> dict:
    """AI对话（模拟推荐问题点击）"""
    return api("POST", "/ai/chat", {
        "user_id": user_id,
        "question": question,
    })


def track_action(user_id: int, content_id: int, action: str = "click") -> dict:
    """记录浏览行为"""
    return api("POST", "/recommend/track", {
        "user_id": user_id,
        "content_id": content_id,
        "action": action,
        "source_scene": "ai_chat",
    })


# ═══════════════════════════════════════════════
# 测试1: 纯ASK路径（3轮 → mixed）
# ═══════════════════════════════════════════════
def test_ask_only_path():
    print("\n" + "=" * 60)
    print("测试1: 纯ASK路径 - 冷启动3轮到mixed")
    print("=" * 60)

    uid = create_test_user("ask_only")
    if not uid:
        print("  ✗ 无法创建用户，跳过")
        return

    # 重置
    reset = reset_crs(uid)
    print(f"  重置CRS: {json.dumps(reset.get('data', {}), ensure_ascii=False)[:80]}")

    state = get_crs_state(uid)
    data = state.get("data", {})
    session_id = data.get("session_id", "")
    print_state(data, "初始")

    # ASK-1: 类目偏好（A01）
    r1 = ask_crs(uid, session_id, "A01", "传统工艺")
    d1 = r1.get("data", {})
    print_state(d1, "ASK-1(A01→传统工艺)")

    # ASK-2: 地区偏好（A02）
    r2 = ask_crs(uid, session_id, "A02", "华南地区")
    d2 = r2.get("data", {})
    print_state(d2, "ASK-2(A02→华南地区)")

    # ASK-3: 场景偏好（A03）
    r3 = ask_crs(uid, session_id, "A03", "线下体验")
    d3 = r3.get("data", {})
    print_state(d3, "ASK-3(A03→线下体验)")

    # 验证
    conf = d3.get("confidence_score", 0)
    mode = d3.get("mode", "")
    if mode == "mixed" or conf >= 40:
        print(f"  ✅ 3轮ASK收敛到mixed (conf={conf})")
    else:
        print(f"  ❌ 3轮ASK未达mixed (conf={conf}, mode={mode})")

    return uid


# ═══════════════════════════════════════════════
# 测试2: 纯推荐问题AI对话路径
# ═══════════════════════════════════════════════
def test_recommended_questions_path():
    print("\n" + "=" * 60)
    print("测试2: 推荐问题AI对话路径 - 用recommended_questions驱动")
    print("=" * 60)

    uid = create_test_user("recq")
    if not uid:
        print("  ✗ 无法创建用户，跳过")
        return

    # 重置
    reset_crs(uid)
    state = get_crs_state(uid)
    data = state.get("data", {})
    print_state(data, "初始")

    # 收集每轮返回的recommended_questions
    all_rec_questions = []
    rounds = []

    # 冷启动推荐问题（第一轮用category类）
    cold_questions = [
        "传统工艺有哪些适合入门体验的项目？",
        "戏曲音乐类非遗，新手从哪个看起比较好？",
        "民俗节俗类非遗有什么特别有趣的？",
        "饮食医药类非遗和日常生活有什么关系？",
    ]

    # 逐轮发问，跟踪推荐问题
    for i, q in enumerate(cold_questions):
        print(f"\n  --- 第{i+1}轮对话 ---")
        print(f"  问: {q}")
        result = chat_ai(uid, q)

        # 提取信息
        answer_preview = ""
        rec_data = result.get("data", result)
        if isinstance(rec_data, dict):
            answer_preview = (rec_data.get("answer", "") or "")[:60]
            rec_qs = rec_data.get("recommended_questions", [])
            source = rec_data.get("source", "")
            kb_hit = rec_data.get("kb_matched", False)
            confidence = rec_data.get("confidence", 0)

            if rec_qs:
                all_rec_questions.append(rec_qs)
                print(f"  答: {answer_preview}...")
                print(f"  来源: {source} | KB命中: {kb_hit} | 置信: {confidence}")
                print(f"  📋 推荐问题({len(rec_qs)}): {rec_qs}")
            else:
                print(f"  答: {answer_preview}...")
                print(f"  来源: {source} | 无推荐问题")

        # 检查CRS状态
        crs = get_crs_state(uid)
        crs_data = crs.get("data", {})
        print_state(crs_data, f"第{i+1}轮后")

        rounds.append({
            "round": i + 1,
            "question": q,
            "source": rec_data.get("source", "") if isinstance(rec_data, dict) else "",
            "recommended_questions": rec_qs if isinstance(rec_data, dict) and rec_qs else [],
        })

        # 如果已到mixed，继续用mixed阶段的推荐问题
        mode = crs_data.get("mode", "")
        if mode == "mixed" and i >= 3:
            print(f"\n  🎉 第{i+1}轮后已到mixed模式！继续用mixed推荐问题...")
            break

    # 如果进入mixed，用mixed阶段的推荐问题继续
    crs = get_crs_state(uid)
    crs_data = crs.get("data", {})
    mode = crs_data.get("mode", "")

    if mode == "mixed":
        mixed_questions = [
            "有没有适合自己动手体验的非遗项目？",
            "如果想系统地了解一个非遗类别，推荐什么顺序？",
            "非遗和旅游融合为什么越来越常见？",
            "现在最热门的非遗体验活动有哪些？",
        ]
        for i, q in enumerate(mixed_questions):
            print(f"\n  --- mixed第{i+1}轮对话 ---")
            print(f"  问: {q}")
            result = chat_ai(uid, q)
            rec_data = result.get("data", result)
            if isinstance(rec_data, dict):
                answer_preview = (rec_data.get("answer", "") or "")[:60]
                rec_qs = rec_data.get("recommended_questions", [])
                source = rec_data.get("source", "")
                print(f"  答: {answer_preview}...")
                print(f"  来源: {source}")
                if rec_qs:
                    print(f"  📋 推荐问题({len(rec_qs)}): {rec_qs}")

            crs = get_crs_state(uid)
            crs_data = crs.get("data", {})
            print_state(crs_data, f"mixed第{i+1}轮后")

            new_mode = crs_data.get("mode", "")
            if new_mode == "precision":
                print(f"\n  🎉🎉 进入precision模式！")
                break

    # 打印汇总
    print("\n" + "-" * 40)
    print(f"  推荐问题覆盖率: {len(all_rec_questions)}轮返回了推荐问题")
    print(f"  最终模式: {crs_data.get('mode', 'unknown')}")
    print(f"  最终conf: {crs_data.get('confidence_score', 0)}")

    return uid


# ═══════════════════════════════════════════════
# 测试3: 混合路径（ASK + 推荐问题 + 行为数据）
# ═══════════════════════════════════════════════
def test_hybrid_path():
    print("\n" + "=" * 60)
    print("测试3: 混合路径 - ASK + 推荐问题 + 行为数据")
    print("=" * 60)

    uid = create_test_user("hybrid")
    if not uid:
        print("  ✗ 无法创建用户，跳过")
        return

    reset_crs(uid)
    state = get_crs_state(uid)
    data = state.get("data", {})
    session_id = data.get("session_id", "")
    print_state(data, "初始")

    # 阶段1: 2轮ASK
    print("\n  --- ASK阶段 ---")
    r1 = ask_crs(uid, session_id, "A01", "传统工艺")
    d1 = r1.get("data", {})
    print_state(d1, "ASK-1(A01→传统工艺)")

    r2 = ask_crs(uid, session_id, "A02", "华东地区")
    d2 = r2.get("data", {})
    print_state(d2, "ASK-2(A02→华东地区)")

    # 阶段2: 2轮推荐问题AI对话
    print("\n  --- 推荐问题对话阶段 ---")
    q1 = "传统工艺有哪些适合入门体验的项目？"
    print(f"  问: {q1}")
    result1 = chat_ai(uid, q1)
    rec1 = result1.get("data", result1)
    if isinstance(rec1, dict):
        rec_qs1 = rec1.get("recommended_questions", [])
        print(f"  📋 推荐问题: {rec_qs1}")
    crs1 = get_crs_state(uid)
    print_state(crs1.get("data", {}), "AI对话1后")

    q2 = "华东地区有哪些特色非遗项目？"
    print(f"  问: {q2}")
    result2 = chat_ai(uid, q2)
    rec2 = result2.get("data", result2)
    if isinstance(rec2, dict):
        rec_qs2 = rec2.get("recommended_questions", [])
        print(f"  📋 推荐问题: {rec_qs2}")
    crs2 = get_crs_state(uid)
    print_state(crs2.get("data", {}), "AI对话2后")

    # 阶段3: 行为数据（模拟点击）
    print("\n  --- 行为数据阶段 ---")
    # 先获取推荐内容
    rec_payload = api("GET", f"/recommend?user_id={uid}")
    contents = rec_payload.get("data", {}).get("contents", [])
    if contents:
        # 模拟点击3个内容
        for idx, c in enumerate(contents[:3]):
            cid = c.get("id")
            if cid:
                track_action(uid, cid, "click")
                print(f"  点击内容: {c.get('title', '?')} (id={cid})")

    crs3 = get_crs_state(uid)
    d3 = crs3.get("data", {})
    print_state(d3, "行为数据后")

    # 判断最终状态
    mode = d3.get("mode", "")
    conf = d3.get("confidence_score", 0)
    if mode == "precision" or conf >= 70:
        print(f"  ✅ 混合路径到达precision (conf={conf})")
    elif mode == "mixed":
        print(f"  ⚠️ 到达mixed但未到precision (conf={conf})，需更多行为数据")
    else:
        print(f"  ❌ 仍为cold_start (conf={conf})")

    return uid


# ═══════════════════════════════════════════════
# 测试4: 推荐问题内容覆盖度检查
# ═══════════════════════════════════════════════
def test_recommended_questions_coverage():
    print("\n" + "=" * 60)
    print("测试4: 推荐问题内容覆盖度 - 冷启动vs混合vs精准")
    print("=" * 60)

    # 测试不同问题类型的推荐问题返回
    test_questions = {
        "类目-工艺": "传统工艺有哪些适合入门体验的项目？",
        "类目-戏曲": "戏曲音乐类非遗，新手从哪个看起比较好？",
        "类目-民俗": "民俗节俗类非遗有什么特别有趣的？",
        "类目-饮食": "饮食医药类非遗和日常生活有什么关系？",
        "地区-华东": "华东地区有哪些特色非遗项目？",
        "地区-华南": "华南地区的非遗和北方有什么不同？",
        "场景-体验": "我想找一些可以线下体验的非遗活动",
        "场景-阅读": "有没有适合深度阅读了解的非遗内容？",
        "通用-概述": "非遗和普通传统文化有什么区别？",
        "通用-数量": "中国目前有多少项世界级非遗？",
        "混合-体验": "有没有适合自己动手体验的非遗项目？",
        "混合-系统": "如果想系统地了解一个非遗类别，推荐什么顺序？",
        "具体-苏绣": "苏绣的特点和技法是什么？",
        "具体-昆曲": "昆曲的历史和代表作有哪些？",
        "具体-景泰蓝": "景泰蓝的制作工艺复杂吗？",
    }

    uid = create_test_user("coverage")
    if not uid:
        print("  ✗ 无法创建用户，跳过")
        return

    reset_crs(uid)

    kb_hit_count = 0
    rec_q_count = 0
    total = len(test_questions)

    for label, q in test_questions.items():
        result = chat_ai(uid, q)
        rec_data = result.get("data", result)
        if not isinstance(rec_data, dict):
            print(f"  [{label}] 返回异常")
            continue

        source = rec_data.get("source", "")
        kb_hit = rec_data.get("kb_matched", False)
        rec_qs = rec_data.get("recommended_questions", [])
        confidence = rec_data.get("confidence", 0)
        answer_len = len(rec_data.get("answer", "") or "")

        if kb_hit:
            kb_hit_count += 1
        if rec_qs:
            rec_q_count += 1

        hit_marker = "🎯" if kb_hit else "❌"
        rec_marker = f"📋{len(rec_qs)}" if rec_qs else "—"
        print(f"  [{label}] {hit_marker} src={source} conf={confidence} ans={answer_len}字 {rec_marker}")
        if rec_qs:
            print(f"         推荐问题: {rec_qs}")

    print(f"\n  KB命中率: {kb_hit_count}/{total} ({kb_hit_count/total*100:.0f}%)")
    print(f"  推荐问题返回率: {rec_q_count}/{total} ({rec_q_count/total*100:.0f}%)")

    # 检查最终CRS状态
    crs = get_crs_state(uid)
    d = crs.get("data", {})
    print_state(d, "15轮对话后")


# ═══════════════════════════════════════════════
# 测试5: 第2/3轮推荐问题质量 - 个性化推荐问题
# ═══════════════════════════════════════════════
def test_round2_3_questions():
    print("\n" + "=" * 60)
    print("测试5: 第2/3轮推荐问题质量 - 是否随用户偏好变化")
    print("=" * 60)

    # 两个用户走不同方向，看推荐问题是否差异化
    for profile_name, first_q, second_q in [
        ("工艺爱好者", "传统工艺有哪些适合入门体验的项目？", "刺绣和织锦哪个更容易上手？"),
        ("戏曲爱好者", "戏曲音乐类非遗，新手从哪个看起比较好？", "昆曲和京剧的区别是什么？"),
        ("饮食文化", "饮食医药类非遗和日常生活有什么关系？", "中药炮制技艺有哪些讲究？"),
    ]:
        print(f"\n  ── 用户: {profile_name} ──")
        uid = create_test_user(f"r23_{profile_name}")
        if not uid:
            continue

        reset_crs(uid)

        # 第1轮
        print(f"  第1轮: {first_q}")
        r1 = chat_ai(uid, first_q)
        d1 = r1.get("data", r1)
        if isinstance(d1, dict):
            rec_qs1 = d1.get("recommended_questions", [])
            print(f"  📋 第1轮推荐问题: {rec_qs1}")

        # 第2轮
        print(f"  第2轮: {second_q}")
        r2 = chat_ai(uid, second_q)
        d2 = r2.get("data", r2)
        if isinstance(d2, dict):
            rec_qs2 = d2.get("recommended_questions", [])
            print(f"  📋 第2轮推荐问题: {rec_qs2}")

        # 第3轮 - 用第2轮的推荐问题
        if rec_qs2:
            third_q = rec_qs2[0]
            print(f"  第3轮(点推荐): {third_q}")
            r3 = chat_ai(uid, third_q)
            d3 = r3.get("data", r3)
            if isinstance(d3, dict):
                rec_qs3 = d3.get("recommended_questions", [])
                print(f"  📋 第3轮推荐问题: {rec_qs3}")

        crs = get_crs_state(uid)
        d = crs.get("data", {})
        print_state(d, f"{profile_name} 3轮后")


# ═══════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    print("CRS循环深度测试 v2.1.2")
    print("后端: http://localhost:8000")
    print()

    try:
        urllib.request.urlopen(f"{BASE.replace('/api/v1','')}/docs", timeout=3)
        print("✓ 后端连接正常")
    except Exception as e:
        print(f"✗ 后端不可达: {e}")
        sys.exit(1)

    # 执行所有测试
    test_ask_only_path()
    test_recommended_questions_path()
    test_hybrid_path()
    test_recommended_questions_coverage()
    test_round2_3_questions()

    print("\n" + "=" * 60)
    print("全部测试完成！")
    print("=" * 60)
