import csv
import io
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.responses import success
from app.models.activity import Activity
from app.models.activity_registration import ActivityRegistration
from app.models.ai_qa_log import AIQALog
from app.models.content import Content
from app.models.discussion_topic import DiscussionTopic
from app.models.recommend_log import RecommendLog
from app.models.user import User

router = APIRouter()


def _build_dashboard(db: Session) -> dict:
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)

    ai_today = db.query(AIQALog).filter(AIQALog.created_at >= today_start).count()
    ai_week = db.query(AIQALog).filter(AIQALog.created_at >= week_start).count()

    source_counts = db.query(AIQALog.source, func.count(AIQALog.id)).group_by(AIQALog.source).all()
    source_map = {s: c for s, c in source_counts}
    total_ai = max(1, sum(source_map.values()))

    local_hit_rate = round((source_map.get("local_kb", 0) / total_ai) * 100, 2)
    web_rate = round((source_map.get("web_search", 0) / total_ai) * 100, 2)

    avg_conf = db.query(func.avg(AIQALog.confidence)).scalar() or 0

    reg_total = db.query(ActivityRegistration).count()
    reg_active = db.query(ActivityRegistration).filter(ActivityRegistration.status.in_(["registered", "checked_in", "completed"])).count()

    recommend_click = db.query(RecommendLog).filter(RecommendLog.action == "click").count()
    recommend_expose = db.query(RecommendLog).filter(RecommendLog.action == "expose").count()
    recommend_ctr = round((recommend_click / recommend_expose) * 100, 2) if recommend_expose else 0.0

    event_click = db.query(RecommendLog).filter(RecommendLog.action == "click", RecommendLog.target_type == "event").count()
    event_reg = db.query(ActivityRegistration).count()
    event_conversion = round((event_reg / event_click) * 100, 2) if event_click else 0.0

    return {
        "ai": {
            "today_questions": ai_today,
            "week_questions": ai_week,
            "local_hit_rate": local_hit_rate,
            "web_rate": web_rate,
            "avg_confidence": float(avg_conf),
            "source_breakdown": source_map,
        },
        "recommend": {
            "expose": recommend_expose,
            "click": recommend_click,
            "ctr": recommend_ctr,
            "event_click": event_click,
            "event_registration": event_reg,
            "event_conversion": event_conversion,
        },
        "activity": {
            "registration_total": reg_total,
            "registration_active": reg_active,
        },
    }


@router.get("/overview", dependencies=[Depends(require_admin)])
def get_overview(db: Session = Depends(get_db)):
    return success(
        {
            "user_count": db.query(User).count(),
            "content_count": db.query(Content).count(),
            "event_count": db.query(Activity).count(),
            "registration_count": db.query(ActivityRegistration).count(),
            "topic_count": db.query(DiscussionTopic).count(),
            "ai_qa_count": db.query(AIQALog).count(),
        }
    )


@router.get("/dashboard", dependencies=[Depends(require_admin)])
def dashboard(db: Session = Depends(get_db)):
    return success(_build_dashboard(db))


@router.get("/dashboard-public")
def dashboard_public(db: Session = Depends(get_db)):
    return success(_build_dashboard(db))


@router.get("/registrations/export-csv", dependencies=[Depends(require_admin)])
def export_registrations_csv(db: Session = Depends(get_db)):
    rows = (
        db.query(ActivityRegistration, User, Activity)
        .join(User, User.id == ActivityRegistration.user_id)
        .join(Activity, Activity.id == ActivityRegistration.activity_id)
        .order_by(ActivityRegistration.id.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["报名ID", "用户ID", "昵称", "活动ID", "活动标题", "状态", "备注", "报名时间"])
    for reg, user, activity in rows:
        writer.writerow([reg.id, user.id, user.nickname or "", activity.id, activity.title, reg.status, reg.remark or "", reg.created_at])

    content = output.getvalue()
    output.close()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=registrations.csv"},
    )
