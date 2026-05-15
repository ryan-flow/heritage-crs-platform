from datetime import datetime, timedelta
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from app.core.database import SessionLocal, Base, engine
from app.models.activity import Activity
from app.models.activity_registration import ActivityRegistration
from app.models.ai_qa_log import AIQALog
from app.models.content import Content
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag
from app.models.discussion_like import DiscussionLike
from app.models.discussion_topic import DiscussionTopic
from app.models.local_knowledge_base import LocalKnowledgeBase
from app.models.recommend_log import RecommendLog
from app.models.user import User


def seed_users(db):
    names = [
        "木兰", "青禾", "江南曲友", "云锦手作", "戏迷阿诚", "民俗观察者", "青年传承营", "非遗采风", "研学队长", "讲解小助理",
        "古琴爱好者", "年画收藏者", "陶瓷学徒", "节俗记录员", "昆曲同好", "手工课堂", "城市导览者", "文化编辑部"
    ]
    users = [User(openid=f"wx_seed_{i+1:03d}", nickname=n, role="user", is_active=True) for i, n in enumerate(names)]
    db.add_all(users)
    db.commit()
    return db.query(User).order_by(User.id.asc()).all()


def seed_contents(db):
    base_rows = [
        ("昆曲的声腔与身段入门图解", "戏曲与表演艺术", "昆曲", "从唱腔、念白与身段程式理解昆曲之美。", True),
        ("古琴的七弦之声：从散音到泛音", "传统音乐", "古琴艺术", "用通俗方式解释古琴音色结构和听赏路径。", True),
        ("中国剪纸纹样中的吉祥语义", "传统美术与工艺", "剪纸", "看懂窗花、团花和喜庆纹样背后的文化隐喻。", False),
        ("南京云锦妆花工艺全流程", "传统美术与工艺", "丝织工艺", "拆解云锦从纹样设计到织造成品的关键工序。", True),
        ("龙泉青瓷的釉色密码", "传统美术与工艺", "陶瓷技艺", "理解青瓷在泥、釉、火中的平衡逻辑。", False),
        ("端午节习俗的地域差异", "岁时节庆与民俗", "端午节", "从龙舟、香囊、艾草看端午节俗多样性。", True),
        ("木版年画的版刻与套色", "传统美术与工艺", "年画艺术", "年画如何把节庆愿景转化为视觉表达。", False),
        ("藏戏面具与角色象征", "戏曲与表演艺术", "藏戏", "通过角色面具读懂藏戏叙事结构。", False),
        ("粤剧舞台节奏与唱做并重", "戏曲与表演艺术", "粤剧", "粤剧为何在当代仍具有传播活力。", True),
        ("宣纸制作中的水与纤维", "传统美术与工艺", "造纸技艺", "从材料科学角度看宣纸何以适配笔墨。", False),
        ("篆刻中的刀法与章法", "传统美术与工艺", "中国篆刻", "方寸之间如何形成节奏与空间秩序。", False),
        ("蚕桑丝织与中国审美传统", "传统美术与工艺", "蚕桑丝织", "丝织工艺如何支撑传统服饰与礼仪文明。", False),
    ]

    rows = []
    for r in range(4):
        for title, chapter, sub, summary, featured in base_rows:
            name = title if r == 0 else f"{title}·专题延展{r}"
            rows.append((name, chapter, sub, summary, featured if r == 0 else False))

    now = datetime.now()
    items = []
    for i, (title, chapter, sub, summary, featured) in enumerate(rows):
        items.append(
            Content(
                title=title,
                content_type="article",
                summary=summary,
                body=f"{summary} 本文进一步给出历史背景、关键概念与当代传播案例，帮助建立系统认知。",
                chapter=chapter,
                sub_chapter=sub,
                status="published",
                published_at=now - timedelta(days=i),
                created_by=-88,
                is_featured=featured,
            )
        )
    db.add_all(items)
    db.commit()
    return db.query(Content).order_by(Content.id.asc()).all()


def seed_activities(db):
    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    base_rows = [
        ("昆曲折子戏沉浸导赏夜", "城市文化中心·戏曲剧场", "市级非遗展演中心", 3, True),
        ("古琴雅集与听赏工作坊", "非遗体验馆·古琴厅", "传统音乐推广联盟", 6, True),
        ("剪纸纹样亲子体验课", "社区文化驿站", "非遗公益课堂", 8, False),
        ("云锦织造公开工坊", "传统工艺实践基地", "云锦传承工作室", 10, True),
        ("龙泉青瓷手作体验营", "陶艺实验空间", "青瓷青年社", 12, False),
        ("端午民俗体验周末场", "滨河活动广场", "节俗文化促进会", 15, True),
        ("木版年画套色体验日", "版画工坊", "年画教育项目组", 18, False),
        ("粤剧基本身段体验课", "岭南戏曲工作坊", "戏曲普及计划", 20, False),
        ("宣纸与水墨材料认知营", "书画实践教室", "书画材料研究社", 23, False),
        ("非遗青年讲解员训练营", "公共文化服务中心", "青年传承行动", 26, True),
    ]

    rows = []
    for r in range(4):
        for title, location, organizer, d, featured in base_rows:
            name = title if r == 0 else f"{title}·加场{r}"
            rows.append((name, location, organizer, d + r * 28, featured if r == 0 else False))

    items = []
    for i, (title, location, organizer, d, featured) in enumerate(rows):
        st = base + timedelta(days=d, hours=10 + (i % 4))
        et = st + timedelta(hours=2)
        items.append(
            Activity(
                title=title,
                location=location,
                organizer=organizer,
                start_time=st,
                end_time=et,
                max_participants=40 + (i % 4) * 10,
                description=f"{title}：包含讲解、互动与实操环节，适合公众参与。",
                notes="建议提前10分钟签到，名额有限。",
                status="open" if i % 9 != 0 else "closed",
                is_featured=featured,
            )
        )
    db.add_all(items)
    db.commit()
    return db.query(Activity).order_by(Activity.id.asc()).all()


def seed_knowledge(db):
    qa_rows = [
        ("昆曲为什么被称为百戏之祖？", "昆曲在中国戏曲史上影响深远，许多剧种在音乐与表演上都曾借鉴其审美经验。", "戏曲,昆曲", "戏曲与表演艺术", "昆曲"),
        ("古琴适合怎样入门？", "建议从听赏经典曲目入手，再学习散音、泛音、按音三类基本音色识别。", "古琴,传统音乐", "传统音乐", "古琴艺术"),
        ("端午节为什么是活态非遗？", "因为它在现实生活中持续被实践，具有可参与、可传承、可更新的文化生命力。", "端午节,节俗", "岁时节庆与民俗", "端午节"),
        ("云锦工艺难点在哪里？", "难点在于纹样组织、色线控制与木机配合，需要长期经验累积。", "云锦,丝织", "传统美术与工艺", "丝织工艺"),
        ("如何理解非遗保护与创新？", "保护强调真实性与连续性，创新强调当代传播与使用场景，二者需要平衡推进。", "保护,创新", "保护制度", "实践路径"),
    ]
    for r in range(8):
        for q, a, k, c, s in qa_rows:
            qq = q if r == 0 else f"{q}（延展问法{r}）"
            db.add(LocalKnowledgeBase(question=qq, answer=a, qa_answer=a, keywords=k, chapter=c, sub_chapter=s, source="heritage_seed_v2", status="active"))
    db.commit()


def seed_topics(db, users):
    base_topics = [
        ("看完昆曲《牡丹亭》后最大的感受", "第一次完整看《牡丹亭》，最震撼的是唱词和身段把人物情绪层层铺开。大家会推荐哪一版入门？", ["戏曲", "求科普"], True),
        ("云锦现场体验后，才理解什么叫工艺门槛", "今天参加云锦工坊，发现一个细节都要反复校准，机器无法替代人的判断。", ["工艺", "活动反馈"], True),
        ("端午活动值得带孩子参加吗？", "想周末带孩子体验端午民俗，大家觉得哪些环节最有参与感？", ["节俗", "活动反馈"], False),
        ("古琴入门是不是很难？", "最近开始听古琴，感觉很安静但也很难懂，求推荐入门路径。", ["传统音乐", "求科普"], False),
        ("剪纸课堂最适合做哪类主题", "做课堂活动时，动物主题和节令主题哪个更容易上手？", ["传统美术", "活动反馈"], False),
        ("粤剧体验课后，发现节奏感特别重要", "老师说先把节奏走稳再谈情绪表达，这句话太有用了。", ["戏曲", "活动反馈"], True),
        ("龙泉青瓷为什么看起来温润", "看展时总听到‘温润如玉’，从材料上该怎么理解？", ["传统技艺", "求科普"], False),
        ("我做了一份非遗研学路线，求建议", "路线包含内容阅读、活动体验和讨论复盘，大家看看哪里还能优化。", ["民俗", "活动反馈"], True),
        ("木版年画套色比想象中复杂", "每一版对位误差都影响整体效果，真的很考验耐心。", ["传统美术", "工艺"], False),
    ]

    topics_data = []
    for r in range(4):
        for t, c, tags, featured in base_topics:
            title = t if r == 0 else f"{t}·讨论延展{r}"
            topics_data.append((title, c, tags, featured if r == 0 else False))

    topics = []
    for idx, (title, content, tags, featured) in enumerate(topics_data):
        u = users[idx % len(users)]
        topic = DiscussionTopic(
            user_id=u.id,
            nickname=u.nickname,
            title=title,
            content=content,
            image_urls="[]",
            like_count=0,
            favorite_count=0,
            comment_count=0,
            is_featured=featured,
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)
        topics.append(topic)
        for t in tags:
            db.add(DiscussionTopicTag(topic_id=topic.id, tag=t))
        db.commit()

    for i, topic in enumerate(topics):
        like_users = users[: (4 + (i % 7))]
        fav_users = users[: (3 + (i % 5))]
        comment_users = users[: (3 + (i % 6))]

        for u in like_users:
            db.add(DiscussionLike(topic_id=topic.id, user_id=u.id))
        for u in fav_users:
            db.add(DiscussionFavorite(topic_id=topic.id, user_id=u.id))
        for j, u in enumerate(comment_users):
            db.add(DiscussionComment(topic_id=topic.id, user_id=u.id, nickname=u.nickname, content=f"我对这个话题的看法是第{j + 1}点，确实有启发。"))

        topic.like_count = len(like_users)
        topic.favorite_count = len(fav_users)
        topic.comment_count = len(comment_users)

    db.commit()
    return topics


def seed_registrations(db, users, activities):
    rows = []
    for i, act in enumerate(activities):
        picked = users[: (6 + (i % 7))]
        for j, u in enumerate(picked):
            status = "registered"
            if j % 5 == 0:
                status = "checked_in"
            if j % 8 == 0:
                status = "completed"
            rows.append(ActivityRegistration(activity_id=act.id, user_id=u.id, remark="自动生成演示报名", status=status))
    db.add_all(rows)
    db.commit()


def seed_logs(db, users, contents, activities, topics):
    for i, u in enumerate(users):
        for qn in range(5):
            db.add(AIQALog(user_id=u.id, question=f"非遗问题示例{i}-{qn}", answer="这是一条演示回答。", source="local_kb", confidence=0.78))
        for c in contents[:20]:
            db.add(RecommendLog(user_id=u.id, action="expose", target_type="content", target_id=c.id, source_scene="home"))
            if (u.id + c.id) % 2 == 0:
                db.add(RecommendLog(user_id=u.id, action="click", target_type="content", target_id=c.id, source_scene="home"))
        for a in activities[:20]:
            db.add(RecommendLog(user_id=u.id, action="expose", target_type="event", target_id=a.id, source_scene="activity_page"))
            if (u.id + a.id) % 3 == 0:
                db.add(RecommendLog(user_id=u.id, action="click", target_type="event", target_id=a.id, source_scene="activity_page"))
        for t in topics[:20]:
            db.add(RecommendLog(user_id=u.id, action="expose", target_type="topic", target_id=t.id, source_scene="discussion_page"))
    db.commit()


def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = seed_users(db)
        contents = seed_contents(db)
        activities = seed_activities(db)
        seed_knowledge(db)
        topics = seed_topics(db, users)
        seed_registrations(db, users, activities)
        seed_logs(db, users, contents, activities, topics)
        print("已完成全量演示数据重建：全国非遗内容、活动、帖子、互动、热榜与加精数据已就绪。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
