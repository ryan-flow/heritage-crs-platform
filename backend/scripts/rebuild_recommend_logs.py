# -*- coding: utf-8 -*-
"""Rebuild recommend_logs to match the current database state.
Strategy:
  - Lin Yingqiu (uid=1, C=71.3): precision mode user,
    explicit preferences: [传统工艺, 戏曲与表演艺术]
    -> mostly expose+click on those two categories, small amount on others
  - Zhou Jianshan (uid=2, C=51.3): mixed mode user
    explicit: [岁时节庆与民俗, 传统工艺]
    -> moderate engagement across 3-4 categories
  - WeChat user (uid=14, C=11.5): cold_start, explicit=0
    -> random light exploration

Format: expose -> click (some) -> view (some of clicks)
Realistic ratios: 60% expose get clicked, 30% of clicks get viewed
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json, random

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.recommend_log import RecommendLog

# Content id ranges (from rebuild_contents_balanced.py):
# 传统工艺:1-14, 戏曲与表演艺术:15-28, 岁时节庆与民俗:29-42,
# 传统音乐:43-54, 传统美术:55-66, 保护制度:67-76,
# 传统医药:77-86, 传承实践:87-96
CHAPTER_CONTENT = {
    "传统工艺":          (1, 14),
    "戏曲与表演艺术":    (15, 28),
    "岁时节庆与民俗":    (29, 42),
    "传统音乐":          (43, 54),
    "传统美术":          (55, 66),
    "保护制度":          (67, 76),
    "传统医药":          (77, 86),
    "传承实践":          (87, 96),
}

# Activity id ranges (80 total, ordered by rebuild_activities_balanced.py):
CHAPTER_EVENT = {
    "传统工艺":          (1, 12),
    "戏曲与表演艺术":    (13, 24),
    "岁时节庆与民俗":    (25, 36),
    "传统音乐":          (37, 46),
    "传统美术":          (47, 58),
    "保护制度":          (59, 64),
    "传统医药":          (65, 72),
    "传承实践":          (73, 80),
}

random.seed(20260413)


def log_entry(user_id, action, target_type, target_id, scene, meta=None):
    """Build a recommend_log dict matching the actual DB schema."""
    item = {
        "user_id": user_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "source_scene": scene,
        "explain_json": json.dumps(meta) if meta else None,
    }
    return item


def make_content_logs(uid: int, chapters: list, expose_each: int) -> list:
    logs = []
    now = datetime.now()
    for ch in chapters:
        lo, hi = CHAPTER_CONTENT[ch]
        ids = list(range(lo, hi + 1))
        random.shuffle(ids)
        for rank, cid in enumerate(ids[:expose_each]):
            ts = now - timedelta(hours=rank * 2 + random.randint(0, 3))
            meta = {"reason": "基于偏好推荐", "chapter": ch, "rank": rank}
            logs.append(log_entry(uid, "expose", "content", cid, "home", meta))
            if random.random() < 0.55:
                meta2 = dict(meta)
                logs.append(log_entry(uid, "click", "content", cid, "home", meta2))
                if random.random() < 0.30:
                    meta3 = dict(meta)
                    logs.append(log_entry(uid, "view", "content", cid, "home", meta3))
    return logs


def make_event_logs(uid: int, chapters: list, expose_each: int) -> list:
    logs = []
    now = datetime.now()
    for ch in chapters:
        lo, hi = CHAPTER_EVENT.get(ch, (1, 10))
        ids = list(range(lo, hi + 1))
        random.shuffle(ids)
        for rank, eid in enumerate(ids[:expose_each]):
            ts = now - timedelta(hours=rank * 3 + random.randint(0, 5))
            meta = {"reason": "推荐相关活动", "chapter": ch}
            logs.append(log_entry(uid, "expose", "event", eid, "activity", meta))
            if random.random() < 0.45:
                meta2 = dict(meta)
                logs.append(log_entry(uid, "click", "event", eid, "activity", meta2))
                if random.random() < 0.40:
                    meta3 = dict(meta)
                    logs.append(log_entry(uid, "register", "event", eid, "activity", meta3))
    return logs


def make_topic_logs(uid: int, expose_each: int) -> list:
    logs = []
    now = datetime.now()
    topic_ids = list(range(1, 173))
    random.shuffle(topic_ids)
    for rank, tid in enumerate(topic_ids[:expose_each]):
        ts = now - timedelta(hours=rank * 4 + random.randint(0, 8))
        meta = {"reason": "根据社区热点推荐"}
        logs.append(log_entry(uid, "expose", "topic", tid, "discussion", meta))
        if random.random() < 0.40:
            meta2 = dict(meta)
            logs.append(log_entry(uid, "click", "topic", tid, "discussion", meta2))
    return logs


def main():
    db = SessionLocal()
    try:
        # Clear old logs
        db.query(RecommendLog).delete()
        db.commit()
        print("Cleared old recommend_logs")

        now = datetime.now()

        # ── Lin Yingqiu (uid=1): precision mode ──
        # explicit=[传统工艺, 戏曲与表演艺术], also browses music/美术
        all_logs = []
        all_logs += make_content_logs(1, ["传统工艺", "戏曲与表演艺术", "传统音乐", "传统美术"], 5)
        all_logs += make_event_logs(1, ["传统工艺", "戏曲与表演艺术", "传统音乐"], 4)
        all_logs += make_topic_logs(1, 8)
        print(f"Lin Yingqiu logs: {len(all_logs)}")

        # ── Zhou Jianshan (uid=2): mixed mode ──
        all_logs += make_content_logs(2, ["岁时节庆与民俗", "传统工艺", "传统音乐"], 4)
        all_logs += make_event_logs(2, ["岁时节庆与民俗", "传统美术"], 3)
        all_logs += make_topic_logs(2, 6)
        print(f"Zhou Jianshan logs: {len(all_logs)}")

        # ── WeChat user (uid=14): cold_start ──
        all_logs += make_content_logs(14, list(CHAPTER_CONTENT.keys()), 2)
        all_logs += make_event_logs(14, list(CHAPTER_EVENT.keys())[:4], 2)
        all_logs += make_topic_logs(14, 4)
        print(f"WeChat user logs: {len(all_logs)}")

        # Insert all
        for item in all_logs:
            db.add(RecommendLog(**item))
        db.commit()
        print(f"\nInserted {len(all_logs)} recommend_logs")

        # Report
        from sqlalchemy import text as _text
        cur = db.execute(_text("""
            SELECT action, target_type, COUNT(*) as cnt
            FROM recommend_logs
            GROUP BY action, target_type
            ORDER BY cnt DESC
        """))
        total = 0
        print("\nFinal distribution:")
        for action, target_type, cnt in cur:
            print(f"  {action:<10} / {target_type:<10}: {cnt:>4}")
            total += cnt
        print(f"  TOTAL: {total}")

        # Validate: all target_ids exist
        from sqlalchemy import text
        bad_content = db.execute(text(
            "SELECT COUNT(*) FROM recommend_logs WHERE target_type='content' "
            "AND target_id NOT IN (SELECT id FROM contents)"
        )).scalar()
        bad_event = db.execute(text(
            "SELECT COUNT(*) FROM recommend_logs WHERE target_type='event' "
            "AND target_id NOT IN (SELECT id FROM activities)"
        )).scalar()
        bad_topic = db.execute(text(
            "SELECT COUNT(*) FROM recommend_logs WHERE target_type='topic' "
            "AND target_id NOT IN (SELECT id FROM discussion_topics)"
        )).scalar()
        print(f"\nIntegrity check:")
        print(f"  Orphan content refs: {bad_content}")
        print(f"  Orphan event refs:   {bad_event}")
        print(f"  Orphan topic refs:    {bad_topic}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
