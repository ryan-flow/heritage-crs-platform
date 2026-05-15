from pathlib import Path
import random
import sys
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.activity import Activity
from app.models.content import Content
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag
from app.models.discussion_like import DiscussionLike
from app.models.discussion_topic import DiscussionTopic
from app.models.user import User


random.seed(20260411)

TAG_WHITELIST = ["戏曲", "工艺", "节俗", "求科普", "活动反馈", "传统音乐", "传统美术", "传统技艺", "民俗"]

PROJECTS = [
    ("昆曲", "戏曲与表演艺术", "昆曲", "戏曲"),
    ("粤剧", "戏曲与表演艺术", "粤剧", "戏曲"),
    ("藏戏", "戏曲与表演艺术", "藏戏", "戏曲"),
    ("古琴", "传统音乐", "古琴艺术", "传统音乐"),
    ("二十四节气", "岁时节庆与民俗", "节气", "民俗"),
    ("端午节", "岁时节庆与民俗", "节俗", "节俗"),
    ("中国剪纸", "传统美术与工艺", "剪纸", "传统美术"),
    ("木版年画", "传统美术与工艺", "年画", "传统美术"),
    ("南京云锦", "传统美术与工艺", "丝织工艺", "工艺"),
    ("龙泉青瓷", "传统美术与工艺", "陶瓷技艺", "传统技艺"),
    ("宣纸制作", "传统美术与工艺", "造纸技艺", "传统技艺"),
    ("中国书法", "传统美术与工艺", "书法", "传统美术"),
    ("中医针灸", "传统医药", "针灸", "医药"),
    ("中药炮制", "传统医药", "中药", "医药"),
    ("茶文化", "传统医药", "茶艺", "医药"),
]

CONTENT_TITLE_TEMPLATES = [
    "{project}入门避坑：第一次接触先看这三件事",
    "在地走访手记：{project}到底难在哪",
    "把{project}讲明白：一文看懂历史和当下",
    "观演/观展后记：我重新理解了{project}",
    "给新手的{project}体验指南",
    "{project}为什么总被反复提及？",
    "别只看热闹，{project}可以这样看门道",
]

ACTIVITY_TITLE_TEMPLATES = [
    "{project}周末体验场",
    "{project}公开导赏",
    "{project}亲子手作课",
    "{project}城市夜场体验",
    "{project}新手入门工作坊",
]

ORGANIZERS = [
    "市文化馆非遗部",
    "城南社区文化站",
    "青年非遗志愿团",
    "非遗体验合作社",
    "公共文化服务中心",
    "在地工艺研究社",
]

LOCATIONS = [
    "市文化馆二层体验教室",
    "老城街区公共空间",
    "非遗体验馆A区",
    "社区文化活动中心",
    "滨河展演空间",
    "城市书房多功能厅",
]

REALISTIC_USERS = [
    "阿岚", "小余", "陈同学", "木木", "远山", "老郑", "南风", "一只青团", "阿泽", "小陈妈妈", "周末看展人", "流苏"
]


def ensure_users(db: Session) -> list[User]:
    users = db.query(User).filter(User.role == "user").all()
    if len(users) >= 12:
        return users

    existing_openids = {u.openid for u in users}
    for idx, name in enumerate(REALISTIC_USERS):
        openid = f"wx_real_{idx + 1:03d}"
        if openid in existing_openids:
            continue
        db.add(User(openid=openid, nickname=name, role="user", is_active=True))
    db.commit()
    return db.query(User).filter(User.role == "user").all()


def cleanup_ai_style_data(db: Session) -> None:
    # 1) 内容：删除明显脚本生成风格
    db.query(Content).filter(Content.created_by.in_([-108, -88, -77])).delete(synchronize_session=False)

    # 2) 活动：删除明显脚本批量生成
    db.query(Activity).filter(
        or_(
            Activity.organizer.in_(["非遗平台智能推荐内容池", "非遗平台自动扩展数据"]),
            Activity.title.like("%加场%"),
            Activity.title.like("%第%场%"),
        )
    ).delete(synchronize_session=False)

    # 3) 帖子：删除明显脚本生成
    bad_topics = db.query(DiscussionTopic).filter(
        or_(
            DiscussionTopic.user_id == -108,
            DiscussionTopic.nickname == "非遗内容中心",
            DiscussionTopic.title.like("%讨论延展%"),
            DiscussionTopic.title.like("%第%次观察%"),
        )
    ).all()
    bad_ids = [t.id for t in bad_topics]
    if bad_ids:
        db.query(DiscussionComment).filter(DiscussionComment.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionLike).filter(DiscussionLike.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionFavorite).filter(DiscussionFavorite.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionTopicTag).filter(DiscussionTopicTag.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionTopic).filter(DiscussionTopic.id.in_(bad_ids)).delete(synchronize_session=False)

    db.commit()


def seed_contents(db: Session, amount: int = 120) -> None:
    now = datetime.now()
    items: list[Content] = []
    for i in range(amount):
        project, chapter, sub, _ = PROJECTS[i % len(PROJECTS)]
        title = random.choice(CONTENT_TITLE_TEMPLATES).format(project=project)
        summary = random.choice([
            f"围绕{project}做一次不空泛的入门梳理，适合第一次接触的读者。",
            f"把{project}放回真实场景里，聊聊它为什么仍然能打动人。",
            f"从现场体验出发，复盘{project}最容易忽略的细节。",
        ])
        body = (
            f"这篇内容不是百科抄录，而是基于展演、活动和访谈整理出来的实用笔记。"
            f"先讲{project}的来历，再拆解关键技艺和观赏门道，最后给出“新手先看什么、现场怎么体验”的建议。"
        )
        items.append(
            Content(
                title=title,
                content_type="article",
                summary=summary,
                body=body,
                chapter=chapter,
                sub_chapter=sub,
                status="published",
                published_at=now - timedelta(hours=i * 6),
                created_by=-66,
                is_featured=(i % 17 == 0),
            )
        )
    db.add_all(items)
    db.commit()


def seed_activities(db: Session, amount: int = 90) -> None:
    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    items: list[Activity] = []
    for i in range(amount):
        project, _, _, _ = PROJECTS[i % len(PROJECTS)]
        title = random.choice(ACTIVITY_TITLE_TEMPLATES).format(project=project)
        organizer = random.choice(ORGANIZERS)
        location = random.choice(LOCATIONS)
        start = base + timedelta(days=(i % 45) + 1, hours=9 + (i % 6))
        end = start + timedelta(hours=2)
        items.append(
            Activity(
                title=title,
                location=location,
                organizer=organizer,
                start_time=start,
                end_time=end,
                max_participants=30 + (i % 5) * 10,
                description=(
                    f"本场活动围绕{project}设置“导览+体验+答疑”三段流程，"
                    f"更适合第一次接触非遗的用户，也欢迎家长带孩子参加。"
                ),
                notes="建议提前15分钟到场；名额有限，满额后关闭报名。",
                status="open" if i % 9 != 0 else "closed",
                is_featured=(i % 16 == 0),
            )
        )
    db.add_all(items)
    db.commit()


def seed_topics(db: Session, users: list[User], amount: int = 160) -> None:
    if not users:
        return

    topics: list[DiscussionTopic] = []
    for i in range(amount):
        project, _, _, default_tag = PROJECTS[i % len(PROJECTS)]
        author = users[i % len(users)]
        title = random.choice([
            f"昨天去看了{project}，有几个细节想请教大家",
            f"第一次体验{project}，我踩过的坑给后来人做个参考",
            f"关于{project}，你们会推荐先看演出还是先看资料？",
            f"周末带家人参加了{project}活动，真实感受分享",
        ])
        content = random.choice([
            f"我是纯新手，昨天现场看完{project}后最大的感受是“门槛高但很上头”。有没有适合入门的资料或视频清单？",
            f"这次活动流程是先讲背景再做体验，两个小时其实挺紧凑。个人建议主持人多留10分钟给提问。",
            f"我原来以为{project}就是看看热闹，现场才发现很多细节需要提前知道，不然很容易错过重点。",
            f"家里小朋友对{project}反应意外地好，尤其是互动环节。想问下还有没有类似亲子友好的活动推荐？",
        ])

        topic = DiscussionTopic(
            user_id=author.id,
            nickname=author.nickname,
            title=title,
            content=content,
            image_urls="[]",
            is_featured=(i % 20 == 0),
            like_count=0,
            favorite_count=0,
            comment_count=0,
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)
        topics.append(topic)

        tags = {default_tag}
        if random.random() > 0.5:
            tags.add(random.choice(TAG_WHITELIST))
        for t in tags:
            db.add(DiscussionTopicTag(topic_id=topic.id, tag=t))
        db.commit()

    for idx, topic in enumerate(topics):
        others = [u for u in users if u.id != topic.user_id]
        if not others:
            continue
        like_users = random.sample(others, min(len(others), 2 + (idx % 6)))
        fav_users = random.sample(others, min(len(others), 1 + (idx % 4)))
        comment_users = random.sample(others, min(len(others), 1 + (idx % 3)))

        for u in like_users:
            db.add(DiscussionLike(topic_id=topic.id, user_id=u.id))
        for u in fav_users:
            db.add(DiscussionFavorite(topic_id=topic.id, user_id=u.id))

        for u in comment_users:
            comment_text = random.choice([
                "这个点说得挺实在，我上次也有同感。",
                "我建议先看一场线下活动，再回来看资料会更容易懂。",
                "感谢分享，正好准备周末去体验，参考价值很高。",
                "同意，现场讲解质量真的很关键。",
            ])
            db.add(
                DiscussionComment(
                    topic_id=topic.id,
                    user_id=u.id,
                    nickname=u.nickname,
                    content=comment_text,
                )
            )

        topic.like_count = len(like_users)
        topic.favorite_count = len(fav_users)
        topic.comment_count = len(comment_users)

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        users = ensure_users(db)
        cleanup_ai_style_data(db)
        seed_contents(db, amount=120)
        seed_activities(db, amount=90)
        seed_topics(db, users, amount=160)
        print("已完成真人化数据替换：contents=120, events=90, topics=160")
    finally:
        db.close()


if __name__ == "__main__":
    main()
