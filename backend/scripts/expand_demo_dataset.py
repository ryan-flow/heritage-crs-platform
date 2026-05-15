from pathlib import Path
import random
import sys
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.activity import Activity
from app.models.content import Content


COVERS_DIR = BASE_DIR / "storage" / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

PALETTES = [
    ("#261611", "#8D2A1D"),
    ("#1E2230", "#7D5A3D"),
    ("#2B1F30", "#A44E34"),
    ("#1D2A2F", "#7C633E"),
    ("#2E1B18", "#B26C42"),
]

TOPICS = [
    ("昆曲", "戏曲与表演艺术", "昆曲"),
    ("古琴艺术", "传统音乐", "古琴"),
    ("中国剪纸", "传统美术与工艺", "剪纸"),
    ("南京云锦", "传统美术与工艺", "丝织"),
    ("龙泉青瓷", "传统美术与工艺", "陶瓷"),
    ("端午节", "岁时节庆与民俗", "节俗"),
    ("木版年画", "传统美术与工艺", "年画"),
    ("藏戏", "戏曲与表演艺术", "藏戏"),
    ("粤剧", "戏曲与表演艺术", "粤剧"),
    ("宣纸制作", "传统美术与工艺", "造纸"),
]

EVENT_TYPES = ["沉浸展演", "亲子研学", "工坊体验", "非遗讲座", "夜场导览"]
LOCATIONS = ["文化服务中心", "非遗体验馆", "城市会客厅", "社区展馆", "古街活动区"]


SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='720' viewBox='0 0 1200 720'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='{c1}'/>
      <stop offset='100%' stop-color='{c2}'/>
    </linearGradient>
  </defs>
  <rect width='1200' height='720' fill='url(#bg)' rx='34'/>
  <circle cx='920' cy='140' r='200' fill='rgba(255,255,255,0.08)'/>
  <text x='86' y='122' fill='#FFE4C0' font-size='30' font-family='Microsoft YaHei, sans-serif'>{chapter}</text>
  <text x='86' y='258' fill='#FFF8F0' font-size='80' font-weight='700' font-family='Microsoft YaHei, sans-serif'>{title}</text>
  <text x='86' y='326' fill='rgba(255,242,231,0.9)' font-size='32' font-family='Microsoft YaHei, sans-serif'>{sub}</text>
  <text x='86' y='430' fill='rgba(255,241,230,0.9)' font-size='30' font-family='Microsoft YaHei, sans-serif'>{line1}</text>
  <text x='86' y='476' fill='rgba(255,241,230,0.9)' font-size='30' font-family='Microsoft YaHei, sans-serif'>{line2}</text>
</svg>"""


def make_cover(filename: str, chapter: str, title: str, sub: str, line1: str, line2: str) -> str:
    c1, c2 = random.choice(PALETTES)
    content = SVG.format(c1=c1, c2=c2, chapter=chapter, title=title, sub=sub, line1=line1[:28], line2=line2[:28])
    path = COVERS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return f"/static/covers/{filename}"


def seed_contents(db, size: int = 80):
    db.query(Content).filter(Content.created_by == -77).delete()
    db.commit()

    for i in range(size):
        topic, chapter, sub = TOPICS[i % len(TOPICS)]
        title = f"{topic}专题导览第{i+1}期"
        summary = f"围绕{topic}的历史脉络、技艺结构与当代传承做深入解析，帮助你快速建立完整认知。"
        body = (
            f"本期聚焦{topic}，从历史来源、核心技艺、代表作品、当代传播四个层面展开。"
            f"内容强调结构化阅读与场景化理解，适合用于课程、讲解和公众传播。\n"
            f"同时结合活动与论坛热度，给出“先看什么、再看什么、如何参与体验”的行动建议。"
        )
        cover = make_cover(
            f"content_seed_{i+1}.svg",
            chapter,
            title,
            sub,
            "结构化梳理非遗核心知识",
            "连接内容阅读、活动体验与社区讨论",
        )
        db.add(
            Content(
                title=title,
                cover_url=cover,
                content_type="article",
                summary=summary,
                body=body,
                chapter=chapter,
                sub_chapter=sub,
                status="published",
                created_by=-77,
            )
        )
    db.commit()


def seed_events(db, size: int = 60):
    db.query(Activity).filter(Activity.organizer == "非遗平台自动扩展数据").delete()
    db.commit()

    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    for i in range(size):
        topic, chapter, sub = TOPICS[i % len(TOPICS)]
        et = EVENT_TYPES[i % len(EVENT_TYPES)]
        title = f"{topic}{et}活动第{i+1}场"
        location = f"{random.choice(LOCATIONS)}·{chapter}专区"
        start = base + timedelta(days=(i % 30) + 1, hours=(i % 6) + 9)
        end = start + timedelta(hours=2)
        cover = make_cover(
            f"event_seed_{i+1}.svg",
            "非遗活动",
            title,
            sub,
            "沉浸式体验+导览讲解",
            "支持在线报名与推荐",
        )
        db.add(
            Activity(
                title=title,
                cover_url=cover,
                location=location,
                organizer="非遗平台自动扩展数据",
                start_time=start,
                end_time=end,
                max_participants=40 + (i % 5) * 10,
                description=f"本场活动聚焦{topic}，包含讲解、互动与体验环节，适合公众与学生参与。",
                notes="请提前10分钟签到，建议穿着便于活动的服装。",
                status="open" if i % 8 != 0 else "closed",
            )
        )
    db.commit()


def main():
    db = SessionLocal()
    try:
        seed_contents(db, size=120)
        seed_events(db, size=80)
        print("扩展完成：contents=120, events=80")
    finally:
        db.close()


if __name__ == "__main__":
    main()
