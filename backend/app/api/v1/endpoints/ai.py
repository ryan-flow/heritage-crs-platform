from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.responses import success, error
from app.services.ai_service import (
    ai_answer,
)
from app.services.crs.session import process_ask_answer, get_or_create_session
from app.services.crs.decision import crs_decide
from app.services.recommendation_service import calc_confidence
from app.services.tts_service import text_to_speech
from app.services.recommendation_service import CRS_THRESHOLD_COLD, CRS_THRESHOLD_MIXED, generate_ai_recommend_cards
from app.core.config import settings

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    user_id: int | None = None
    context_cards: list[dict] | None = None


class TTSRequest(BaseModel):
    text: str


class CrsAnswerRequest(BaseModel):
    user_id: int
    session_id: str
    ask_id: str
    answer: str


# ═══════════════════════════════════════════════
# CRS v2.0 接口
# ═══════════════════════════════════════════════

@router.get("/crs/state")
def get_crs_state(user_id: int, db: Session = Depends(get_db)):
    """获取用户当前CRS状态：模式、置信度、维度明细、决策时间线"""
    from app.models.crs_ask_log import CrsAskLog
    confidence_result = calc_confidence(db, user_id)
    session = get_or_create_session(db, user_id)
    # 最近5条ASK记录，构建决策时间线
    ask_logs = db.query(CrsAskLog).filter(
        CrsAskLog.user_id == user_id,
    ).order_by(CrsAskLog.created_at.desc()).limit(5).all()
    ask_timeline = [
        {
            "ask_id": log.ask_id,
            "attribute": log.attribute,
            "question": log.question_text or "",
            "answer": log.answer or "",
            "score_delta": log.score_delta or 0,
            "created_at": str(log.created_at),
        }
        for log in reversed(ask_logs)  # 正序：最早→最近
    ]
    return success({
        "session_id": session.session_id,
        "mode": confidence_result.get("mode", "cold_start"),
        "confidence_score": confidence_result.get("confidence_score", 0),
        "confidence_score_raw": confidence_result.get("confidence_score_raw", confidence_result.get("confidence_score", 0)),
        "stage_progress_percent": confidence_result.get("stage_progress_percent", 0),
        "dimensions": {
            "explicit": confidence_result.get("score_explicit", 0),
            "implicit": confidence_result.get("score_implicit", 0),
            "dialogue": confidence_result.get("score_dialogue", 0),
        },
        "detail": confidence_result.get("detail", {}),
        "turn_count": session.turn_count or 0,
        "last_ask_attribute": session.last_ask_attribute or "",
        "ask_timeline": ask_timeline,
    })


@router.post("/crs/answer")
def submit_crs_answer(payload: CrsAnswerRequest, db: Session = Depends(get_db)):
    """提交用户对ASK提问的回答

    1. 记录回答到CrsAskLog
    2. 更新用户偏好字段
    3. 重新计算置信度
    4. 更新会话模式

    Returns:
        更新后的CRS状态
    """
    from app.models.crs_ask_log import CrsAskLog

    if not payload.answer.strip():
        return error("回答不能为空", status_code=400)

    confidence_result = process_ask_answer(
        db=db,
        user_id=payload.user_id,
        session_id=payload.session_id,
        ask_id=payload.ask_id,
        answer=payload.answer,
    )

    # 重新获取会话状态
    session = get_or_create_session(db, payload.user_id)
    ask_logs = db.query(CrsAskLog).filter(
        CrsAskLog.user_id == payload.user_id,
    ).order_by(CrsAskLog.created_at.desc()).limit(5).all()
    ask_timeline = [
        {
            "ask_id": log.ask_id,
            "attribute": log.attribute,
            "question": log.question_text or "",
            "answer": log.answer or "",
            "score_delta": log.score_delta or 0,
            "created_at": str(log.created_at),
        }
        for log in reversed(ask_logs)
    ]

    return success({
        "session_id": session.session_id,
        "mode": confidence_result.get("mode", "cold_start"),
        "confidence_score": confidence_result.get("confidence_score", 0),
        "confidence_score_raw": confidence_result.get("confidence_score_raw", confidence_result.get("confidence_score", 0)),
        "stage_progress_percent": confidence_result.get("stage_progress_percent", 0),
        "dimensions": {
            "explicit": confidence_result.get("score_explicit", 0),
            "implicit": confidence_result.get("score_implicit", 0),
            "dialogue": confidence_result.get("score_dialogue", 0),
        },
        "detail": confidence_result.get("detail", {}),
        "turn_count": session.turn_count or 0,
        "last_ask_attribute": session.last_ask_attribute or "",
        "ask_timeline": ask_timeline,
        "transition_msg": confidence_result.get("transition_msg", ""),
        "recommend_cards": confidence_result.get("recommend_cards", []),
    })


@router.post("/crs/reset")
def reset_crs_session(
    user_id: int,
    clear_profile: bool = False,
    db: Session = Depends(get_db),
):
    """重置CRS会话（用户主动重置或会话超时）

    参数:
        user_id: 用户ID
        clear_profile: True时同时清零用户偏好画像和置信度分数（演示用）
                       False（默认）时只重置当前对话会话，保留历史偏好
    """
    from app.models.crs_session import CrsSession
    from app.models.user import User
    # 将旧会话设为不活跃
    db.query(CrsSession).filter(
        CrsSession.user_id == user_id,
        CrsSession.is_active == 1,
    ).update({"is_active": 0})
    db.commit()

    # 可选：清零用户画像（演示/测试用）
    if clear_profile:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.preferred_heritage_types = "[]"
            user.preferred_scene_types = "[]"
            user.preferred_regions = "[]"
            user.confidence_score = 0.0
            user.score_explicit = 0.0
            user.score_implicit = 0.0
            user.score_dialogue = 0.0
            db.commit()

    # 创建新会话
    session = get_or_create_session(db, user_id)
    # clear_profile 时使用缓存（已被上方强制归零），否则重新计算
    confidence_result = calc_confidence(db, user_id, use_cache=bool(clear_profile))

    return success({
        "session_id": session.session_id,
        "mode": confidence_result.get("mode", "cold_start"),
        "confidence_score": confidence_result.get("confidence_score", 0),
        "confidence_score_raw": confidence_result.get("confidence_score_raw", confidence_result.get("confidence_score", 0)),
        "stage_progress_percent": confidence_result.get("stage_progress_percent", 0),
        "profile_cleared": clear_profile,
    })


@router.get("/crs/debug")
def debug_crs_state(
    user_id: int,
    question: str = "你好",
    sim_new_user: bool = False,
    db: Session = Depends(get_db),
):
    """CRS策略可视调试接口（答辩演示用）

    返回完整的CRS决策链路：用户画像 → 置信度计算 → 策略决策 → ASK选择

    参数 sim_new_user=True 时，模拟冷启动新用户（置信度归零、偏好清空），
    方便答辩时展示完整的冷启动→混合→精准升级过程。
    """
    from app.models.crs_ask_log import CrsAskLog
    from app.models.user import User
    from app.services.recommendation_service import generate_recommendation_payload, generate_ai_recommend_cards
    from app.services.knowledge_base import search_local_knowledge
    from app.services.crs import ASK_TEMPLATES
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error("用户不存在", status_code=404)

    # 模拟冷启动：临时覆盖用户数据
    if sim_new_user:
        import json as _json
        _orig = {
            "preferred_heritage_types": user.preferred_heritage_types,
            "preferred_scene_types": user.preferred_scene_types,
            "preferred_regions": user.preferred_regions,
            "confidence_score": user.confidence_score,
            "score_explicit": user.score_explicit,
            "score_implicit": user.score_implicit,
            "score_dialogue": user.score_dialogue,
        }
        user.preferred_heritage_types = "[]"
        user.preferred_scene_types = "[]"
        user.preferred_regions = "[]"
        user.confidence_score = 0
        user.score_explicit = 0
        user.score_implicit = 0
        user.score_dialogue = 0

    # 1. 用户画像快照
    import json as _json
    profile_snapshot = {
        "user_id": user.id,
        "preferred_heritage_types": _json.loads(user.preferred_heritage_types or "[]"),
        "preferred_scene_types": _json.loads(user.preferred_scene_types or "[]"),
        "preferred_regions": _json.loads(user.preferred_regions or "[]"),
        "confidence_score": user.confidence_score,
        "score_explicit": user.score_explicit,
        "score_implicit": user.score_implicit,
        "score_dialogue": user.score_dialogue,
        "is_simulated_new_user": sim_new_user,
    }

    # 2. 置信度计算明细
    confidence_result = calc_confidence(db, user_id)

    # 3. CRS会话状态
    session = get_or_create_session(db, user_id)
    session_snapshot = {
        "session_id": session.session_id,
        "mode": session.mode,
        "turn_count": session.turn_count,
        "last_ask_attribute": session.last_ask_attribute,
        "last_ask_id": session.last_ask_id,
        "asked_attributes": session.get_asked_attributes() if hasattr(session, "get_asked_attributes") else _json.loads(session.asked_attributes or "[]"),
        "is_active": session.is_active,
    }

    # 4. ASK历史记录
    ask_logs = db.query(CrsAskLog).filter(
        CrsAskLog.user_id == user_id,
    ).order_by(CrsAskLog.created_at.desc()).limit(10).all()
    ask_history = [
        {
            "ask_id": log.ask_id,
            "attribute": log.attribute,
            "question": log.question_text,
            "answer": log.answer,
            "score_delta": log.score_delta,
            "created_at": str(log.created_at),
        }
        for log in ask_logs
    ]

    # 5. 策略决策
    rec_payload = generate_recommendation_payload(db, user_id, context_text=question, scene="ai")
    kb_result = search_local_knowledge(db, question)
    strategy_payload = crs_decide(question, confidence_result, session, rec_payload, kb_result)

    # 6. 推荐卡片
    recommend_cards = generate_ai_recommend_cards(db, user_id, question)

    result = success({
        "question": question,
        "profile": profile_snapshot,
        "confidence": confidence_result,
        "session": session_snapshot,
        "ask_history": ask_history,
        "strategy": strategy_payload,
        "available_templates": list(ASK_TEMPLATES.keys()),
        "recommend_cards_count": len(recommend_cards),
    })

    # 模拟冷启动：恢复原始数据（不真正修改用户记录）
    if sim_new_user:
        for k, v in _orig.items():
            setattr(user, k, v)

    return result


@router.get("/crs/stats")
def crs_statistics(db: Session = Depends(get_db)):
    """CRS系统统计数据（答辩演示用）

    返回全局CRS指标：ASK回答率、偏好分布、模式迁移统计、冷启动收敛速度
    """
    from app.models.crs_session import CrsSession
    from app.models.crs_ask_log import CrsAskLog
    from app.models.user import User
    from sqlalchemy import func
    import json as _json

    # 1. 用户模式分布
    total_users = db.query(func.count(User.id)).scalar() or 1
    cold_count = db.query(func.count(User.id)).filter(
        User.confidence_score.is_not(None), User.confidence_score < CRS_THRESHOLD_COLD
    ).scalar() or 0
    mixed_count = db.query(func.count(User.id)).filter(
        User.confidence_score.is_not(None),
        User.confidence_score >= CRS_THRESHOLD_COLD,
        User.confidence_score < CRS_THRESHOLD_MIXED,
    ).scalar() or 0
    precision_count = db.query(func.count(User.id)).filter(
        User.confidence_score.is_not(None), User.confidence_score >= CRS_THRESHOLD_MIXED
    ).scalar() or 0
    mode_distribution = {
        "cold_start": cold_count,
        "mixed": mixed_count,
        "precision": precision_count,
    }

    # 2. ASK回答率（使用is_skipped精确统计）
    total_asks = db.query(func.count(CrsAskLog.id)).scalar() or 0
    real_answered = db.query(func.count(CrsAskLog.id)).filter(
        CrsAskLog.is_skipped.is_(False)
    ).scalar() or 0
    skipped_count = db.query(func.count(CrsAskLog.id)).filter(
        CrsAskLog.is_skipped.is_(True)
    ).scalar() or 0
    ask_answer_rate = round(real_answered / max(total_asks, 1) * 100, 1)
    ask_skip_rate = round(skipped_count / max(total_asks, 1) * 100, 1)

    # 3. 各ASK模板运营化统计（展示次数=记录次数，回答率/跳过率/选项分布）
    from app.services.crs import ASK_TEMPLATES as _ASK_TEMPLATES
    ask_template_stats = {}
    for ask_id_key, tmpl in _ASK_TEMPLATES.items():
        shown = db.query(func.count(CrsAskLog.id)).filter(
            CrsAskLog.ask_id == ask_id_key
        ).scalar() or 0
        answered = db.query(func.count(CrsAskLog.id)).filter(
            CrsAskLog.ask_id == ask_id_key,
            CrsAskLog.is_skipped.is_(False),
        ).scalar() or 0
        skipped_t = db.query(func.count(CrsAskLog.id)).filter(
            CrsAskLog.ask_id == ask_id_key,
            CrsAskLog.is_skipped.is_(True),
        ).scalar() or 0
        # 选项分布
        option_dist = {}
        for row in db.query(CrsAskLog.answer, func.count(CrsAskLog.id)).filter(
            CrsAskLog.ask_id == ask_id_key
        ).group_by(CrsAskLog.answer).all():
            if row[0]:
                option_dist[row[0]] = row[1]
        # 该模板带来的模式升级率：回答后达到precision的用户占比
        upgrade_count = 0
        if answered > 0:
            user_ids_with_this_ask = db.query(CrsAskLog.user_id).filter(
                CrsAskLog.ask_id == ask_id_key,
                CrsAskLog.is_skipped.is_(False),
            ).distinct().subquery()
            from sqlalchemy import select as sa_sel
            upgrade_count = db.query(func.count(User.id)).filter(
                User.id.in_(sa_sel(user_ids_with_this_ask)),
                User.confidence_score.is_not(None),
                User.confidence_score >= CRS_THRESHOLD_MIXED,
            ).scalar() or 0
        ask_template_stats[ask_id_key] = {
            "prompt": tmpl["prompt"],
            "attribute": tmpl["attribute"],
            "shown": shown,
            "answered": answered,
            "skipped": skipped_t,
            "answer_rate": round(answered / max(shown, 1) * 100, 1),
            "skip_rate": round(skipped_t / max(shown, 1) * 100, 1),
            "option_distribution": option_dist,
            "mode_upgrade_count": upgrade_count,
            "mode_upgrade_rate": round(upgrade_count / max(answered, 1) * 100, 1),
        }

    # 3b. 兼容旧字段ask_template_usage
    ask_template_usage = {k: v["shown"] for k, v in ask_template_stats.items()}

    # 4. 偏好类型分布
    heritage_type_dist = {}
    for user in db.query(User).filter(User.preferred_heritage_types.is_not(None)).all():
        types = _json.loads(user.preferred_heritage_types or "[]")
        for t in types:
            heritage_type_dist[t] = heritage_type_dist.get(t, 0) + 1

    # 5. 平均置信度
    avg_confidence = db.query(func.avg(User.confidence_score)).filter(
        User.confidence_score.is_not(None)
    ).scalar() or 0

    # 6. 冷启动收敛速度（v2.0.7d）
    convergence_data = []
    precision_sessions = db.query(CrsSession).filter(
        CrsSession.mode == "precision"
    ).all()
    for session in precision_sessions:
        ask_count = db.query(func.count(CrsAskLog.id)).filter(
            CrsAskLog.session_id == session.session_id,
            CrsAskLog.answer.is_not(None),
            CrsAskLog.answer != "",
        ).scalar() or 0
        if ask_count > 0:
            convergence_data.append({
                "session_id": session.session_id,
                "turns": ask_count,
                "user_id": session.user_id,
            })

    turns_distribution = {"1_turn": 0, "2_turns": 0, "3_turns": 0, "4_turns": 0, "5_plus": 0}
    for item in convergence_data:
        t = item["turns"]
        if t <= 1:
            turns_distribution["1_turn"] += 1
        elif t == 2:
            turns_distribution["2_turns"] += 1
        elif t == 3:
            turns_distribution["3_turns"] += 1
        elif t == 4:
            turns_distribution["4_turns"] += 1
        else:
            turns_distribution["5_plus"] += 1

    avg_convergence_turns = round(
        sum(d["turns"] for d in convergence_data) / max(len(convergence_data), 1), 1
    )

    return success({
        "total_users": total_users,
        "users_with_confidence": cold_count + mixed_count + precision_count,
        "mode_distribution": mode_distribution,
        "ask_stats": {
            "total_asks": total_asks,
            "answered": real_answered,
            "skipped": skipped_count,
            "answer_rate": ask_answer_rate,
            "skip_rate": ask_skip_rate,
        },
        "ask_template_usage": ask_template_usage,
        "ask_template_stats": ask_template_stats,
        "heritage_type_distribution": heritage_type_dist,
        "avg_confidence": round(float(avg_confidence), 1),
        "convergence": {
            "avg_turns_to_precision": avg_convergence_turns,
            "precision_session_count": len(convergence_data),
            "turns_distribution": turns_distribution,
            "detail": convergence_data[:20],
        },
        # 7. 行为闭环诊断（v2.0.7f）
        "behavior_loop": _build_behavior_loop_stats(db),
    })


def _build_behavior_loop_stats(db: Session) -> dict:
    """行为闭环诊断统计

    展示曝光、点击、浏览、报名等行为对画像和推荐的闭环影响：
    - 各行为类型分布（expose/click/view/feedback_like/feedback_dislike）
    - 推荐CTR（曝光→点击转化率）
    - 推荐深度阅读率（曝光→浏览转化率）
    - 活动报名转化率（浏览→报名）
    - 满意度（feedback_like vs feedback_dislike）
    - 行为对置信度的影响（有行为用户 vs 无行为用户的平均置信度对比）
    """
    from app.models.recommend_log import RecommendLog
    from app.models.activity_registration import ActivityRegistration
    from app.models.user import User
    from sqlalchemy import func, select as sa_select

    # ── 1. 各行为类型分布 ──
    action_distribution = {}
    for row in db.query(
        RecommendLog.action, func.count(RecommendLog.id)
    ).group_by(RecommendLog.action).all():
        action_distribution[row[0]] = row[1]

    # ── 2. 各推荐类型分布 ──
    type_distribution = {}
    for row in db.query(
        RecommendLog.target_type, func.count(RecommendLog.id)
    ).group_by(RecommendLog.target_type).all():
        type_distribution[row[0]] = row[1]

    # ── 3. CTR：曝光→点击（排除点赞/收藏/评论的假click） ──
    total_expose = action_distribution.get("expose", 0)
    # 真实click = 全部click - 假click（topic_like/topic_favorite/topic_comment）
    fake_click_count = db.query(func.count(RecommendLog.id)).filter(
        RecommendLog.action == "click",
        RecommendLog.source_scene.in_(["topic_like", "topic_favorite", "topic_comment"]),
    ).scalar() or 0
    total_click = action_distribution.get("click", 0) - fake_click_count
    ctr = round(total_click / max(total_expose, 1) * 100, 1)

    # ── 4. 深度阅读率：曝光→浏览 ──
    # 口径说明：view 实际语义为"进入详情页"，非深度阅读完成
    total_view = action_distribution.get("view", 0)
    view_rate = round(total_view / max(total_expose, 1) * 100, 1)

    # ── 5. 满意度 ──
    # 口径说明：feedback 来自 AI 对话页，当前实现为对当轮推荐卡片逐条记录反馈
    feedback_like = action_distribution.get("feedback_like", 0)
    feedback_dislike = action_distribution.get("feedback_dislike", 0)
    total_feedback = feedback_like + feedback_dislike
    satisfaction_rate = round(feedback_like / max(total_feedback, 1) * 100, 1)

    # ── 6. 活动报名转化率 ──
    total_registrations = db.query(func.count(ActivityRegistration.id)).scalar() or 0

    # ── 7. 行为对置信度的影响 ──
    # 有行为用户（至少1条真实click/view/feedback）vs 无行为用户
    # 排除点赞/收藏/评论冒充的假click
    users_with_behavior = db.query(RecommendLog.user_id).filter(
        RecommendLog.user_id.is_not(None),
        RecommendLog.action.in_(["click", "view", "feedback_like", "feedback_dislike"]),
        ~RecommendLog.source_scene.in_(["topic_like", "topic_favorite", "topic_comment"]),
    ).distinct().subquery()

    active_users_conf = db.query(func.avg(User.confidence_score)).filter(
        User.id.in_(sa_select(users_with_behavior)),
        User.confidence_score.is_not(None),
    ).scalar() or 0

    inactive_users_conf = db.query(func.avg(User.confidence_score)).filter(
        User.id.not_in(sa_select(users_with_behavior)),
        User.confidence_score.is_not(None),
    ).scalar() or 0

    # ── 8. 行为→画像：各行为平均带来的隐式分变化 ──
    avg_implicit_active = db.query(func.avg(User.score_implicit)).filter(
        User.id.in_(sa_select(users_with_behavior)),
    ).scalar() or 0

    avg_implicit_inactive = db.query(func.avg(User.score_implicit)).filter(
        User.id.not_in(sa_select(users_with_behavior)),
    ).scalar() or 0

    # ── 9. 行为时间线：最近7天每日行为量 ──
    from datetime import datetime, timedelta
    daily_actions = []
    for i in range(6, -1, -1):
        day_start = (datetime.now() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_count = db.query(func.count(RecommendLog.id)).filter(
            RecommendLog.created_at >= day_start,
            RecommendLog.created_at < day_end,
        ).scalar() or 0
        daily_actions.append({
            "date": day_start.strftime("%m-%d"),
            "count": day_count,
        })

    return {
        "total_actions": sum(action_distribution.values()),
        "action_distribution": action_distribution,
        "action_distribution_note": "click中含点赞/收藏/评论的假click，CTR已排除",
        "fake_click_count": fake_click_count,
        "real_click_count": total_click,
        "type_distribution": type_distribution,
        "ctr": ctr,
        "view_rate": view_rate,
        "view_rate_note": "view=进入详情页（非深度阅读完成），此为近似指标",
        "satisfaction": {
            "like": feedback_like,
            "dislike": feedback_dislike,
            "rate": satisfaction_rate,
            "note": "仅来自AI对话页，当前按推荐卡片逐条记录反馈",
        },
        "activity_registrations": total_registrations,
        "confidence_impact": {
            "active_users_avg_confidence": round(float(active_users_conf), 1),
            "inactive_users_avg_confidence": round(float(inactive_users_conf), 1),
            "delta": round(float(active_users_conf) - float(inactive_users_conf), 1),
            "description": "有行为用户平均置信度 vs 无行为用户差值",
        },
        "implicit_score_impact": {
            "active_users_avg": round(float(avg_implicit_active), 1),
            "inactive_users_avg": round(float(avg_implicit_inactive), 1),
            "delta": round(float(avg_implicit_active) - float(avg_implicit_inactive), 1),
            "description": "行为→隐式偏好分的变化（浏览/点击越多分越高）",
        },
        "daily_actions_7d": daily_actions,
    }


@router.get("/crs/demo")
def crs_demo_flow(user_id: int, db: Session = Depends(get_db)):
    """CRS三阶段升级演示接口（答辩演示专用）

    模拟完整的 冷启动→探索中→精准推荐 升级流程：
    1. 阶段0：模拟新用户，展示冷启动状态
    2. 阶段1：回答A01（选择类目），展示mixed状态
    3. 阶段2：回答A02+A03，展示precision状态

    不修改用户真实数据，仅做临时模拟。
    """
    from app.models.user import User
    import json as _json

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error("用户不存在", status_code=404)

    # 保存原始数据
    orig = {
        "preferred_heritage_types": user.preferred_heritage_types,
        "preferred_scene_types": user.preferred_scene_types,
        "preferred_regions": user.preferred_regions,
        "confidence_score": user.confidence_score,
        "score_explicit": user.score_explicit,
        "score_implicit": user.score_implicit,
        "score_dialogue": user.score_dialogue,
    }

    results = []

    # ── 阶段0：冷启动 ──
    user.preferred_heritage_types = "[]"
    user.preferred_scene_types = "[]"
    user.preferred_regions = "[]"
    user.confidence_score = 0
    user.score_explicit = 0
    user.score_implicit = 0
    user.score_dialogue = 0
    conf_0 = calc_confidence(db, user_id)
    strategy_0 = crs_decide("你好", conf_0, None, {}, {})
    results.append({
        "stage": "cold_start",
        "stage_display": "冷启动",
        "confidence": conf_0,
        "strategy": strategy_0,
        "user_profile": {
            "preferred_heritage_types": [],
            "preferred_scene_types": [],
            "preferred_regions": [],
        }
    })

    # ── 阶段1：回答A01 → mixed ──
    user.preferred_heritage_types = _json.dumps(["工艺"], ensure_ascii=False)
    user.score_explicit = 25
    conf_1 = calc_confidence(db, user_id)
    strategy_1 = crs_decide("传统工艺怎么入门", conf_1, None, {}, {})
    results.append({
        "stage": "mixed",
        "stage_display": "探索中",
        "confidence": conf_1,
        "strategy": strategy_1,
        "user_profile": {
            "preferred_heritage_types": ["工艺"],
            "preferred_scene_types": [],
            "preferred_regions": [],
        },
        "ask_answered": {"ask_id": "A01", "answer": "传统工艺", "attribute": "category"}
    })

    # ── 阶段2：回答A02+A03 → precision ──
    user.preferred_scene_types = _json.dumps(["知识阅读"], ensure_ascii=False)
    user.preferred_regions = _json.dumps(["华南"], ensure_ascii=False)
    user.score_explicit = 65
    user.score_implicit = 40
    user.score_dialogue = 30
    conf_2 = calc_confidence(db, user_id)
    strategy_2 = crs_decide("帮我推荐一些适合入门的非遗内容", conf_2, None, {}, {})
    results.append({
        "stage": "precision",
        "stage_display": "精准推荐",
        "confidence": conf_2,
        "strategy": strategy_2,
        "user_profile": {
            "preferred_heritage_types": ["工艺"],
            "preferred_scene_types": ["知识阅读"],
            "preferred_regions": ["华南"],
        },
        "ask_answered": [
            {"ask_id": "A01", "answer": "传统工艺", "attribute": "category"},
            {"ask_id": "A02", "answer": "本地推荐", "attribute": "region"},
            {"ask_id": "A03", "answer": "阅读了解", "attribute": "scene"},
        ]
    })

    # 恢复原始数据
    for k, v in orig.items():
        setattr(user, k, v)

    return success({
        "demo_title": "CRS三阶段升级演示",
        "demo_desc": "模拟新用户从冷启动到精准推荐的完整流程",
        "stages": results,
        "mode_progression": "cold_start → mixed → precision",
        "confidence_formula": "C = 0.4×S_explicit + 0.35×S_implicit + 0.25×S_dialogue",
        "thresholds": {
            "cold_start": f"< {CRS_THRESHOLD_COLD}",
            "mixed": f"{CRS_THRESHOLD_COLD} - {CRS_THRESHOLD_MIXED}",
            "precision": f"≥ {CRS_THRESHOLD_MIXED}",
        }
    })


# ═══════════════════════════════════════════════
# AI 对话接口
# ═══════════════════════════════════════════════

@router.post("/chat")
def chat_ai(payload: AskRequest, db: Session = Depends(get_db)):
    result = ai_answer(db, payload.question, payload.user_id, context_cards=payload.context_cards)

    strategy = result.get("strategy", "")
    if not (result.get("recommend_cards") or []) and strategy in ("cold_start_ask", "recovery_ask"):
        rec_payload = result.get("recommend_payload") or {}
        fallback_cards = generate_ai_recommend_cards(
            db,
            payload.user_id,
            payload.question,
            rec_payload=rec_payload if rec_payload else None,
            prefer_hot=True,
        )
        if fallback_cards:
            result["recommend_cards"] = fallback_cards[:2]

    return success(result)


@router.post("/ask")
def ask_ai_compat(payload: AskRequest, db: Session = Depends(get_db)):
    # 兼容旧接口，内部复用 chat 逻辑
    result = ai_answer(db, payload.question, payload.user_id)
    strategy = result.get("strategy", "")
    if not (result.get("recommend_cards") or []) and strategy in ("cold_start_ask", "recovery_ask"):
        rec_payload = result.get("recommend_payload") or {}
        fallback_cards = generate_ai_recommend_cards(
            db,
            payload.user_id,
            payload.question,
            rec_payload=rec_payload if rec_payload else None,
            prefer_hot=True,
        )
        if fallback_cards:
            result["recommend_cards"] = fallback_cards[:2]
    return success(result)


@router.post("/chat/stream")
def chat_ai_stream(payload: AskRequest, db: Session = Depends(get_db)):
    """
    流式AI对话接口（SSE）— CRS v2.0

    复用 ai_answer() 的完整逻辑（KB命中→豆包润色→CRS决策→推荐），
    仅将最终回答改为流式输出，确保与 /chat 行为一致。

    事件类型：
    - crs_state: CRS状态（模式、置信度、ASK信息）
    - content: 打字机文本流
    - answer_source: 回答来源标记
    - recommend: 推荐卡片
    - done: 结束标记
    """
    question = (payload.question or "").strip()
    user_id = payload.user_id

    if not question:
        return error("问题不能为空", status_code=400)

    if not settings.doubao_api_key:
        return error("AI服务未配置", status_code=503)

    # 复用 ai_answer 获取完整结果（KB+CRS+推荐），answer部分用流式替代
    result = ai_answer(db, question, user_id, context_cards=payload.context_cards)
    answer_text = result.get("answer", "")
    source = result.get("source", "")

    # 提取CRS数据
    crs_confidence = result.get("crs_confidence", {})
    crs_data = {
        "session_id": result.get("crs_session_id", ""),
        "mode": result.get("crs_mode", "cold_start"),
        "confidence_score": crs_confidence.get("confidence_score", 0),
        "dimensions": crs_confidence.get("dimensions", {}),
        "dimension_raw": {
            "score_explicit": crs_confidence.get("score_explicit", 0),
            "score_implicit": crs_confidence.get("score_implicit", 0),
            "score_dialogue": crs_confidence.get("score_dialogue", 0),
        },
    }
    crs_strategy = {}
    if result.get("strategy"):
        crs_strategy = {
            "strategy": result.get("strategy", ""),
            "strategy_note": result.get("strategy_note", ""),
            "ask_prompt": result.get("ask_prompt", ""),
            "ask_options": result.get("ask_options", []),
            "ask_id": result.get("ask_id", ""),
            "ask_attribute": result.get("ask_attribute", ""),
            "score_delta": result.get("score_delta", 0),
        }
    recommend_cards = result.get("recommend_cards", [])

    def event_generator():
        # 事件1：CRS状态
        if crs_data:
            yield f"data: {json.dumps({'type': 'crs_state', **crs_data}, ensure_ascii=False)}\n\n"

        # 事件2：CRS策略（ASK卡片）
        if crs_strategy and crs_strategy.get("strategy"):
            yield f"data: {json.dumps({'type': 'crs_strategy', **crs_strategy}, ensure_ascii=False)}\n\n"

        # 事件3：回答来源
        if source:
            yield f"data: {json.dumps({'type': 'answer_source', 'source': source}, ensure_ascii=False)}\n\n"

        # 事件4：文本内容（一次性输出完整回答，模拟流式效果）
        if answer_text:
            # 将回答按句切分，模拟打字机效果
            chunk_size = 8
            for i in range(0, len(answer_text), chunk_size):
                chunk = answer_text[i:i + chunk_size]
                data = json.dumps({"type": "content", "content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"

        # 事件5：推荐卡片
        if recommend_cards:
            data = json.dumps({"type": "recommend", "cards": recommend_cards[:3]}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/tts")
async def tts(payload: TTSRequest):
    try:
        url = await text_to_speech(payload.text)
        if not url:
            return error("语音生成失败，请稍后重试", status_code=503)
        return success({"audio_url": url})
    except ValueError as e:
        return error(str(e), status_code=400)
    except Exception:
        return error("语音服务异常，请稍后重试", status_code=500)

