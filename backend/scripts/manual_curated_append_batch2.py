from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.content import Content
from app.models.activity import Activity
from app.models.activity_registration import ActivityRegistration
from app.models.discussion_topic import DiscussionTopic
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_like import DiscussionLike
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag
from app.models.local_knowledge_base import LocalKnowledgeBase
from app.models.recommend_log import RecommendLog
from app.models.ai_qa_log import AIQALog


def j(v):
    return json.dumps(v, ensure_ascii=False)


def main() -> None:
    db = SessionLocal()
    try:
        # 1) 补齐历史微信用户画像
        wx_user = db.query(User).filter(User.role == "user", User.openid.like("wx_%"), User.preferred_heritage_types.is_(None)).first()
        if wx_user:
            wx_user.preferred_heritage_types = j(["戏曲", "节俗", "传统美术"])
            wx_user.preferred_scene_types = j(["知识阅读", "活动体验", "论坛交流"])
            wx_user.preferred_regions = j(["广东", "华南", "全国"])
            if not wx_user.nickname:
                wx_user.nickname = "微信用户"

        # 2) 继续人工高质量数据（算法对齐）
        now = datetime.now()

        user_by_name = {u.nickname: u for u in db.query(User).filter(User.role == "user").all()}

        c_rows = [
            ("木版年画导读：从节日图像到在地生活记忆", "传统美术与工艺", "木版年画", "木版年画不只是年节装饰，更是民间叙事载体。", "本文聚焦木版年画在当代传播中的三个关键点：图像寓意、版刻工序和在地生活语境。建议先阅读门神与吉祥图像的基础寓意，再对照地方流派差异，最后结合论坛讨论中的家庭记忆案例复盘，能更快建立可迁移的理解框架。", "顾澄", True),
            ("非遗研学活动设计：怎样让‘看热闹’变成‘会表达’", "传承实践", "研学方法", "面向学校与社区的非遗研学活动设计指南。", "高质量研学不应只停留在参观打卡。有效结构通常是‘导入问题—现场观察—任务体验—表达复盘’四段。文章给出可直接套用的任务卡模板和评价维度，方便推荐系统将“知识阅读”用户转化为“活动体验”用户。", "高予安", True),
            ("二十四节气内容专题：把农时知识翻译成现代生活提示", "岁时节庆与民俗", "二十四节气", "节气内容可作为民俗类推荐的稳定入口。", "这篇专题围绕立春、芒种、霜降三个节点，解释节气在饮食、起居和社区活动中的现实意义。相比抽象概念讲解，文章采用“问题+场景+行动建议”的组织方式，更利于AI问答和推荐理由生成。", "宋南枝", False),
            ("非遗数字化记录实践：短视频之外，结构化采集更关键", "保护制度", "数字化保护", "讨论非遗数字化中的结构化采集与可追溯。", "很多项目重传播轻归档，导致后续知识复用困难。本文提出最小可行采集结构：项目名、工序段、场景、口述关键词、地域标签与来源时间。该结构能直接服务推荐系统特征抽取，也有利于知识库沉淀。", "高予安", False),
        ]

        new_contents = []
        for i, (t, ch, sub, s, b, author, feat) in enumerate(c_rows):
            u = user_by_name.get(author)
            if not u:
                continue
            new_contents.append(
                Content(
                    title=t,
                    content_type="article",
                    chapter=ch,
                    sub_chapter=sub,
                    summary=s,
                    body=b,
                    status="published",
                    review_status="approved",
                    quality_score=0.92 + (i * 0.01),
                    is_featured=feat,
                    published_at=now - timedelta(hours=10 + i * 7),
                    created_by=u.id,
                )
            )
        db.add_all(new_contents)

        a_rows = [
            ("木版年画版刻体验场", "天津·年画工坊体验区", "年画教育项目组", 8, 42, "先看版刻流程，再做一版套色体验，最后集中复盘图像寓意。", True),
            ("非遗研学活动设计公开课（教师专场）", "广州·公共文化服务中心", "非遗研学协作组", 10, 55, "面向教师和讲解员，现场拆解活动模板与评价表。", True),
            ("节气生活方式分享会", "福州·社区文化空间", "民俗传播志愿队", 12, 48, "围绕二十四节气做饮食、起居与社区活动提案交流。", False),
            ("非遗数字化采集工作坊", "杭州·数字文化实验室", "非遗数字化工作站", 14, 32, "教授最小可行采集结构，现场完成一条项目数据录入。", True),
        ]
        new_activities = [
            Activity(
                title=t,
                location=loc,
                organizer=org,
                start_time=now + timedelta(days=d),
                end_time=now + timedelta(days=d, hours=2, minutes=20),
                max_participants=cap,
                description=desc,
                notes="建议提前15分钟到场，现场发放任务卡。",
                is_featured=feat,
                status="open",
            )
            for t, loc, org, d, cap, desc, feat in a_rows
        ]
        db.add_all(new_activities)
        db.commit()
        for x in new_activities:
            db.refresh(x)

        t_rows = [
            ("顾澄", "木版年画课堂里，学生最容易忽略‘图像寓意’", "我试了先讲寓意再做版刻，学生复盘质量明显提高。大家在课堂里怎么设计提问？", ["木版年画", "传统美术", "课堂"]),
            ("高予安", "研学活动里‘任务卡’比讲解更能留住注意力", "同样时长下，有任务卡的小组复盘明显更完整。是否可以做平台模板共享？", ["研学", "活动设计", "传承实践"]),
            ("宋南枝", "节气内容怎么讲才不空？我用‘今日能做什么’", "把节气拆成饮食、作息、社区实践三条，用户反馈更愿意收藏。", ["二十四节气", "民俗", "内容策编"]),
            ("高予安", "数字化采集别只拍视频，结构化字段更重要", "后续知识库复用时，字段齐全的数据价值远高于单条短视频。", ["数字化保护", "知识库", "方法论"]),
        ]

        new_topics = []
        for i, (author, title, content, tags) in enumerate(t_rows):
            u = user_by_name.get(author)
            if not u:
                continue
            tp = DiscussionTopic(
                user_id=u.id,
                nickname=u.nickname,
                title=title,
                content=content,
                image_urls="[]",
                is_featured=(i == 1),
                like_count=0,
                favorite_count=0,
                comment_count=0,
            )
            db.add(tp)
            db.commit()
            db.refresh(tp)
            new_topics.append((tp, tags))
            for tg in tags:
                db.add(DiscussionTopicTag(topic_id=tp.id, tag=tg))
            db.commit()

        # 评论/点赞/收藏
        if new_topics:
            c1 = DiscussionComment(topic_id=new_topics[0][0].id, user_id=user_by_name["唐子墨"].id, nickname="唐子墨", content="先讲寓意确实有效，学生更容易形成完整表达。")
            c2 = DiscussionComment(topic_id=new_topics[1][0].id, user_id=user_by_name["林映秋"].id, nickname="林映秋", content="任务卡还能反向做推荐特征，很实用。")
            c3 = DiscussionComment(topic_id=new_topics[3][0].id, user_id=user_by_name["许青川"].id, nickname="许青川", content="结构化字段能直接进入知识库，这点非常关键。")
            db.add_all([c1, c2, c3])

            db.add(DiscussionLike(topic_id=new_topics[1][0].id, user_id=user_by_name["高予安"].id))
            db.add(DiscussionLike(topic_id=new_topics[1][0].id, user_id=user_by_name["何闻笛"].id))
            db.add(DiscussionLike(topic_id=new_topics[0][0].id, user_id=user_by_name["顾澄"].id))
            db.add(DiscussionFavorite(topic_id=new_topics[1][0].id, user_id=user_by_name["林映秋"].id))

            for tp, _ in new_topics:
                tp.like_count = db.query(DiscussionLike).filter(DiscussionLike.topic_id == tp.id).count()
                tp.favorite_count = db.query(DiscussionFavorite).filter(DiscussionFavorite.topic_id == tp.id).count()
                tp.comment_count = db.query(DiscussionComment).filter(DiscussionComment.topic_id == tp.id).count()

        # 报名行为（用于 event 热度）
        reg_pairs = [
            (new_activities[0].id, user_by_name["顾澄"].id, "registered", "课堂升级研究"),
            (new_activities[1].id, user_by_name["高予安"].id, "registered", "教师专场"),
            (new_activities[1].id, user_by_name["林映秋"].id, "registered", "活动模板学习"),
            (new_activities[2].id, user_by_name["宋南枝"].id, "registered", "节气传播"),
            (new_activities[3].id, user_by_name["许青川"].id, "registered", "采集方法实践"),
        ]
        for aid, uid, st, rm in reg_pairs:
            db.add(ActivityRegistration(activity_id=aid, user_id=uid, status=st, remark=rm))

        # 知识库
        kb_rows = [
            ("木版年画课堂如何提升学习效果？", "建议采用‘寓意导入—版刻实践—复盘表达’三段式，能显著提高学生表达完整度。", "木版年画,课堂,传统美术", "传统美术与工艺", "木版年画"),
            ("研学活动任务卡为什么重要？", "任务卡能把观察、体验和表达连成闭环，提升参与与复盘质量。", "研学,活动设计,传承实践", "传承实践", "研学方法"),
            ("节气内容如何增强用户收藏意愿？", "用‘今天能做什么’组织信息，比抽象概念更容易被保存和转发。", "二十四节气,民俗,内容策编", "岁时节庆与民俗", "二十四节气"),
            ("非遗数字化采集最小字段有哪些？", "至少包含项目名、工序段、场景、关键词、地域标签、来源时间，便于后续推荐和知识复用。", "数字化保护,结构化采集,知识库", "保护制度", "数字化保护"),
            ("如何让知识阅读用户转化为活动体验用户？", "在内容中嵌入明确活动入口与参与收益说明，并保持场景一致性。", "推荐转化,知识阅读,活动体验", "传承实践", "活动设计"),
            ("论坛讨论数据如何服务推荐算法？", "高质量帖子标签、互动热度和问题类型可作为主题偏好与场景偏好的补充信号。", "论坛交流,推荐算法,特征", "数字化体验", "推荐实践"),
        ]
        for q, a, kw, ch, sub in kb_rows:
            db.add(LocalKnowledgeBase(question=q, answer=a, qa_answer=a, keywords=kw, chapter=ch, sub_chapter=sub, source="人工策编-算法对齐-第二批", status="active"))

        # 行为日志与AI提问（强化个性化）
        c_id = {c.title: c.id for c in db.query(Content).all()}
        a_id = {a.title: a.id for a in db.query(Activity).all()}
        t_id = {t.title: t.id for t in db.query(DiscussionTopic).all()}

        new_logs = [
            (user_by_name["顾澄"].id, "click", "content", c_id.get("木版年画导读：从节日图像到在地生活记忆"), "home"),
            (user_by_name["顾澄"].id, "view", "event", a_id.get("木版年画版刻体验场"), "activity"),
            (user_by_name["高予安"].id, "click", "content", c_id.get("非遗研学活动设计：怎样让‘看热闹’变成‘会表达’"), "home"),
            (user_by_name["高予安"].id, "view", "event", a_id.get("非遗研学活动设计公开课（教师专场）"), "activity"),
            (user_by_name["宋南枝"].id, "click", "content", c_id.get("二十四节气内容专题：把农时知识翻译成现代生活提示"), "home"),
            (user_by_name["宋南枝"].id, "click", "topic", t_id.get("节气内容怎么讲才不空？我用‘今日能做什么’"), "discussion"),
            (user_by_name["许青川"].id, "click", "content", c_id.get("非遗数字化记录实践：短视频之外，结构化采集更关键"), "home"),
            (user_by_name["许青川"].id, "view", "event", a_id.get("非遗数字化采集工作坊"), "activity"),
        ]
        for uid, action, tp, tid, scene in new_logs:
            if tid:
                db.add(RecommendLog(user_id=uid, action=action, target_type=tp, target_id=tid, source_scene=scene, explain_json="{}"))

        qa_rows = [
            (user_by_name["顾澄"].id, "木版年画课程先看哪类内容再报名活动？", "先看图像寓意与版刻工序导读，再报名体验活动。"),
            (user_by_name["高予安"].id, "研学活动如何提升复盘质量？", "建议引入任务卡并设置表达评分维度。"),
            (user_by_name["许青川"].id, "数字化采集怎么做才便于后续推荐？", "采用结构化字段采集，保证可检索与可复用。"),
        ]
        for uid, q, a in qa_rows:
            db.add(AIQALog(user_id=uid, question=q, answer=a, source="local_kb", confidence=0.93))

        db.commit()
        print("第二批人工高质量数据已完成并入库。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
