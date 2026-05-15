from datetime import datetime, timedelta
from pathlib import Path
import json
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
        # reset
        db.query(RecommendLog).delete(); db.query(AIQALog).delete()
        db.query(DiscussionLike).delete(); db.query(DiscussionFavorite).delete(); db.query(DiscussionComment).delete(); db.query(DiscussionTopicTag).delete(); db.query(DiscussionTopic).delete()
        db.query(ActivityRegistration).delete(); db.query(Activity).delete(); db.query(Content).delete(); db.query(LocalKnowledgeBase).delete(); db.query(User).filter(User.role == "user").delete()
        db.commit()

        users = [
            User(openid="wx_curated_001", nickname="林映秋", role="user", is_active=True, preferred_heritage_types=j(["昆曲", "戏曲", "传统音乐"]), preferred_scene_types=j(["知识阅读", "活动体验"]), preferred_regions=j(["江苏", "华东"])),
            User(openid="wx_curated_002", nickname="周见山", role="user", is_active=True, preferred_heritage_types=j(["云锦", "工艺", "传统技艺"]), preferred_scene_types=j(["活动体验", "论坛交流"]), preferred_regions=j(["江苏", "浙江", "华东"])),
            User(openid="wx_curated_003", nickname="陈若禾", role="user", is_active=True, preferred_heritage_types=j(["端午节", "节俗", "民俗"]), preferred_scene_types=j(["活动体验", "论坛交流"]), preferred_regions=j(["广东", "华南"])),
            User(openid="wx_curated_004", nickname="唐子墨", role="user", is_active=True, preferred_heritage_types=j(["中国剪纸", "传统美术"]), preferred_scene_types=j(["知识阅读", "论坛交流"]), preferred_regions=j(["华北", "北京"])),
            User(openid="wx_curated_005", nickname="何闻笛", role="user", is_active=True, preferred_heritage_types=j(["古琴", "传统音乐"]), preferred_scene_types=j(["知识阅读", "活动体验"]), preferred_regions=j(["浙江", "华东"])),
            User(openid="wx_curated_006", nickname="赵小棠", role="user", is_active=True, preferred_heritage_types=j(["粤剧", "戏曲"]), preferred_scene_types=j(["活动体验", "论坛交流"]), preferred_regions=j(["广东", "华南"])),
            User(openid="wx_curated_007", nickname="吴阿宁", role="user", is_active=True, preferred_heritage_types=j(["龙泉青瓷", "传统技艺", "工艺"]), preferred_scene_types=j(["知识阅读", "活动体验"]), preferred_regions=j(["浙江", "华东"])),
            User(openid="wx_curated_008", nickname="许青川", role="user", is_active=True, preferred_heritage_types=j(["宣纸", "书法", "传统美术"]), preferred_scene_types=j(["知识阅读"]), preferred_regions=j(["安徽", "华东"])),
            User(openid="wx_curated_009", nickname="高予安", role="user", is_active=True, preferred_heritage_types=j(["戏曲", "工艺", "节俗"]), preferred_scene_types=j(["知识阅读", "论坛交流", "活动体验"]), preferred_regions=j(["全国", "华南", "华东"])),
            User(openid="wx_curated_010", nickname="宋南枝", role="user", is_active=True, preferred_heritage_types=j(["民俗", "节俗", "端午节"]), preferred_scene_types=j(["活动体验"]), preferred_regions=j(["广东", "福建", "华南"])),
            User(openid="wx_curated_011", nickname="顾澄", role="user", is_active=True, preferred_heritage_types=j(["传统美术", "传统技艺"]), preferred_scene_types=j(["论坛交流", "知识阅读"]), preferred_regions=j(["华北", "北京"])),
            User(openid="wx_curated_012", nickname="梁言初", role="user", is_active=True, preferred_heritage_types=j(["昆曲", "古琴", "云锦"]), preferred_scene_types=j(["活动体验", "知识阅读"]), preferred_regions=j(["江苏", "浙江", "华东"])),
        ]
        db.add_all(users); db.commit(); [db.refresh(u) for u in users]

        now = datetime.now()
        c_rows = [
            ("昆曲导赏阅读笔记：从《牡丹亭》看戏曲审美", "戏曲与表演艺术", "昆曲", "这篇内容适合第一次阅读昆曲专题的用户。", "文章围绕唱腔、身段与叙事节奏三部分展开，帮助读者了解昆曲为什么被称为戏曲审美高峰。建议先阅读角色关系，再结合片段观看，会更容易理解。", users[0].id, True),
            ("古琴入门内容专题：先听散音，再练指法", "传统音乐", "古琴", "古琴阅读内容强调听觉训练优先。", "许多初学者在活动体验中直接练手，容易挫败。更稳妥的路径是先听散音、泛音与按音差别，再进入基础指法。这样内容学习和活动报名会更匹配。", users[4].id, True),
            ("南京云锦工艺专题：纹样、色线与机台协同", "传统美术与工艺", "云锦", "云锦工艺不是单点动作，而是系统协同。", "从工坊观察看，纹样设计会影响色线组织和机台节奏。本文给出可复用的观察清单，适合准备参加活动体验的用户先做阅读了解。", users[1].id, True),
            ("龙泉青瓷内容导读：如何判断釉色层次", "传统美术与工艺", "龙泉青瓷", "青瓷审美需要方法，不只是看亮度。", "建议按‘釉层均匀度—光线层次—器形匹配’三步阅读。读者在论坛讨论中常把亮度当标准，这篇内容专门纠正这一误区。", users[6].id, False),
            ("端午节俗专题：家庭实践与社区活动", "岁时节庆与民俗", "端午节", "端午是典型活态民俗，重在持续实践。", "文章从家庭、社区、公共文化三层解释端午节俗如何传承，给出亲子活动组织建议，适合活动体验场景提前阅读。", users[2].id, True),
            ("中国剪纸课堂内容：图案寓意如何讲清楚", "传统美术与工艺", "中国剪纸", "剪纸内容不应只停留在手工步骤。", "好的课堂应把图案寓意、动手实践和复盘表达结合。本文给出完整教学流程，适合社区课堂和论坛交流用户。", users[3].id, False),
            ("粤剧观演指南：演前导赏比临场硬看更有效", "戏曲与表演艺术", "粤剧", "粤剧新观众需要结构化导赏。", "推荐先阅读角色关系图和关键唱段说明，再参加线下观演活动。演前导赏、演中提示、演后问答是提升体验的三段式。", users[5].id, True),
            ("宣纸与书法：材料选择如何影响笔墨表达", "传统美术与工艺", "宣纸", "宣纸纸性是书法内容学习的关键。", "同笔同墨在不同纸上效果差异明显。本文解释宣纸的吸墨与渗化机制，适合知识阅读场景，也便于引导后续体验活动。", users[7].id, False),
            ("非遗新手入门地图：先读内容、再看活动、最后参加讨论", "导览与学习路径", "入门路径", "给第一次接触非遗的用户一条不容易迷路的探索顺序。", "这篇内容把‘知识阅读—活动体验—社区讨论’串成一条清晰路径，适合首页推荐和 AI 冷启动阶段作为第一篇引导内容，帮助用户更快建立方向感。", users[8].id, True),
            ("为什么同一类非遗，有的人适合先看内容，有的人适合先报活动", "导览与学习路径", "推荐理解", "不同用户的进入方式不同，入门顺序也应该不同。", "文章从时间成本、理解门槛、参与意愿三方面解释为什么推荐不能一刀切，适合在推荐解释场景下作为辅助内容，帮助用户理解系统为何给出不同路线。", users[9].id, True),
            ("从一次点击到一次报名：非遗兴趣是怎样慢慢形成的", "用户理解与传播", "行为观察", "兴趣往往不是一次决定，而是多次接触后的累积结果。", "本文通过内容点击、活动收藏、报名参与和讨论互动四类行为，解释用户兴趣如何逐步收敛，适合做画像变化与行为回流的背景阅读内容。", users[10].id, False),
            ("为什么有些推荐更像在帮你缩小范围，而不是直接给答案", "导览与学习路径", "推荐理解", "好的推荐有时不是马上命中，而是先帮用户确认方向。", "这篇内容用通俗方式说明‘先缩小范围、再精准推荐’的价值，适合 mixed 阶段用户阅读，也有助于解释为什么系统有时会先补内容线索再给活动。", users[11].id, True),
            ("第一次逛非遗平台，怎么判断该先看文章还是先找活动", "导览与学习路径", "入门路径", "很多新用户不是没有兴趣，而是不知道第一步该怎么走。", "文章从时间安排、理解难度和参与成本三个角度，告诉读者什么时候适合先看内容，什么时候适合直接报名活动，适合作为首页推荐的入门指导。", users[0].id, True),
            ("看完导赏内容还是记不住？试试用‘主题—人物—场景’三步法", "导览与学习路径", "学习方法", "给内容阅读用户一个更容易消化非遗知识的小方法。", "无论是看昆曲、粤剧还是节俗内容，先抓主题，再记关键人物或角色，最后对应到具体场景，会比零散浏览更容易建立整体理解。", users[1].id, False),
            ("从展览到工坊：为什么亲手体验后，很多人对非遗的兴趣会突然变强", "用户理解与传播", "体验观察", "体验式接触往往比单纯浏览更容易留下记忆。", "文章结合工坊、课堂和社区活动案例，解释为什么参与感会放大理解深度，也说明为什么很多非遗主题适合把内容阅读和线下体验放在一起看。", users[2].id, True),
            ("非遗讨论区里，什么样的话题更容易让人继续深入了解", "社区互动", "讨论内容", "不是所有热闹的话题都能带来持续兴趣。", "相比只停留在感叹和打卡，带有经验、比较和建议的话题更容易促使用户继续点进内容或活动详情。这类文章适合补足社区到推荐之间的理解链路。", users[3].id, False),
            ("看活动简介时，先看这三件事，能少踩很多坑", "活动体验与参与", "活动选择", "活动选得对不对，往往决定第一次体验是否顺利。", "这篇文章建议优先看活动适合人群、是否有导赏环节、参与门槛高不高，尤其适合第一次接触戏曲、工艺和节俗活动的用户。", users[4].id, True),
            ("为什么有些人明明喜欢看内容，却迟迟不愿报名活动", "用户理解与传播", "行为观察", "兴趣和行动之间，常常还隔着一步安全感。", "文章分析时间成本、社交压力、理解门槛和陌生感四个原因，解释为什么‘喜欢看’不一定会立刻变成‘愿意参加’，适合用来丰富行为观察类内容。", users[5].id, False),
        ]
        contents = [Content(title=t, content_type="article", chapter=ch, sub_chapter=sub, summary=s, body=b, status="published", review_status="approved", quality_score=0.91 + (i % 4) * 0.02, is_featured=f, published_at=now - timedelta(days=i), created_by=uid) for i, (t, ch, sub, s, b, uid, f) in enumerate(c_rows)]
        db.add_all(contents)

        a_rows = [
            ("昆曲《牡丹亭》导赏活动", "江苏·市文化馆小剧场", "市文化馆非遗部", 4, 80, "活动包含导赏、片段观演和问答，适合先阅读内容再报名参加。", True),
            ("古琴听赏与入门体验", "浙江·城市书房多功能厅", "传统音乐推广联盟", 6, 45, "先讲听赏，再做基础指法体验，降低新手门槛。", True),
            ("云锦妆花工艺开放工坊", "江苏·非遗体验馆A区", "云锦传承工作室", 9, 30, "展示纹样与机台协同流程，提供小班体验位。", True),
            ("龙泉青瓷手作与审美活动", "浙江·陶艺实验空间", "青瓷青年社", 11, 36, "先做审美导读，再进行坯体体验。", False),
            ("端午节俗亲子社区活动", "广东·社区文化活动中心", "节俗文化促进会", 13, 60, "香囊制作、节俗故事和亲子协作任务。", True),
            ("中国剪纸社区课堂", "北京·城南社区文化站", "社区美育项目组", 15, 50, "图案寓意讲解+课堂实践+复盘表达。", False),
            ("粤剧观演与交流活动", "广东·岭南戏曲工作坊", "戏曲普及计划", 18, 70, "演前导赏、演中提示、演后交流。", True),
            ("宣纸书写材料认知活动", "安徽·书画实践教室", "书画材料研究社", 21, 40, "同笔同墨对照实验，理解纸性影响。", False),
        ]
        activities = [Activity(title=t, location=loc, organizer=org, start_time=now + timedelta(days=d), end_time=now + timedelta(days=d, hours=2, minutes=30), max_participants=mp, description=desc, notes="建议提前15分钟签到。", is_featured=feat, status="open") for t, loc, org, d, mp, desc, feat in a_rows]
        db.add_all(activities); db.commit(); [db.refresh(a) for a in activities]

        t_rows = [
            (users[0], "看完昆曲导赏内容再去活动，理解效率翻倍", "先阅读再参加活动，真的比直接去看更容易进入戏曲语境。大家还有哪些昆曲阅读内容推荐？", ["戏曲", "昆曲", "讨论"]),
            (users[1], "云锦工艺活动里最难的是协同节奏", "不是单个动作难，而是纹样、色线和机台要同步。论坛里有做过工坊助教的朋友吗？", ["工艺", "云锦", "论坛"]),
            (users[6], "龙泉青瓷‘温润’我现在按三步判断", "先看釉层，再看光线层次，最后看器形匹配，这样比只看亮度靠谱。", ["传统技艺", "龙泉青瓷", "讨论"]),
            (users[2], "端午活动怎么做才不止打卡", "我们准备把节俗故事、亲子任务和复盘讨论连起来，欢迎给建议。", ["节俗", "端午节", "社区"]),
            (users[3], "剪纸课堂里，寓意讲解必须前置", "学生做完作品却说不出寓意，说明课堂结构还不够。大家怎么改进？", ["传统美术", "中国剪纸", "课堂"]),
            (users[5], "粤剧活动前发角色关系图，观演体验明显提升", "新观众反馈‘终于能跟上’，这个方法值得推广到更多戏曲活动。", ["粤剧", "戏曲", "活动"]),
            (users[4], "古琴学习先练耳朵，后练手", "听赏阶段打好基础后，指法学习更稳，挫败感小很多。", ["古琴", "传统音乐", "经验"]),
            (users[7], "宣纸对笔墨表现影响太直观了", "做了同笔同墨对照实验后，学生马上理解什么叫纸性。", ["宣纸", "书法", "教学"]),
            (users[8], "第一次用黑塔问推荐，真的比自己乱翻省时间", "我先回答了偏好问题，再看推荐卡，感觉比直接刷列表更容易找到想深入了解的方向。", ["黑塔", "CRS", "体验反馈"]),
            (users[9], "画像页如果能告诉我为什么被判成这个模式就更好了", "我能看到偏好标签了，但更想知道是哪些行为把我推到 mixed 或 precision。", ["画像", "CRS模式", "建议"]),
            (users[10], "推荐解释里我最喜欢看‘为什么是现在推荐’", "单纯告诉我推荐这个还不够，策略上下文那层其实特别能建立信任感。", ["推荐解释", "explain", "讨论"]),
            (users[11], "社区讨论最好能带动活动报名，而不是停在聊天", "如果帖子能把我顺势引到活动或内容详情，闭环会更完整。", ["社区", "活动转化", "建议"]),
        ]
        topics = [DiscussionTopic(user_id=u.id, nickname=u.nickname, title=tt, content=ct, image_urls="[]", is_featured=(i % 3 == 0), like_count=0, favorite_count=0, comment_count=0) for i, (u, tt, ct, _) in enumerate(t_rows)]
        db.add_all(topics); db.commit(); [db.refresh(t) for t in topics]
        for tp, (_, _, _, tags) in zip(topics, t_rows):
            for tag in tags: db.add(DiscussionTopicTag(topic_id=tp.id, tag=tag))

        comments = [
            DiscussionComment(topic_id=topics[0].id, user_id=users[11].id, nickname=users[11].nickname, content="同意，先阅读内容再参加活动，推荐质量会更准。"),
            DiscussionComment(topic_id=topics[1].id, user_id=users[6].id, nickname=users[6].nickname, content="工坊里节奏断了就很难补，确实是协同难。"),
            DiscussionComment(topic_id=topics[3].id, user_id=users[9].id, nickname=users[9].nickname, content="亲子任务要有分工，不然容易变成家长代做。"),
            DiscussionComment(topic_id=topics[5].id, user_id=users[0].id, nickname=users[0].nickname, content="关系图+唱段提示是我见过最有效的组合。"),
            DiscussionComment(topic_id=topics[6].id, user_id=users[4].id, nickname=users[4].nickname, content="我也建议先固定两首曲目反复听。"),
        ]
        db.add_all(comments)

        likes = [(topics[0].id, users[2].id), (topics[0].id, users[5].id), (topics[1].id, users[1].id), (topics[3].id, users[9].id), (topics[5].id, users[0].id), (topics[6].id, users[11].id)]
        favs = [(topics[0].id, users[8].id), (topics[3].id, users[9].id), (topics[5].id, users[5].id)]
        for tid, uid in likes: db.add(DiscussionLike(topic_id=tid, user_id=uid))
        for tid, uid in favs: db.add(DiscussionFavorite(topic_id=tid, user_id=uid))
        for t in topics:
            t.like_count = sum(1 for x in likes if x[0] == t.id)
            t.favorite_count = sum(1 for x in favs if x[0] == t.id)
            t.comment_count = sum(1 for c in comments if c.topic_id == t.id)

        regs = [
            (activities[0].id, users[0].id, "registered", "昆曲导赏进阶"), (activities[0].id, users[11].id, "registered", "戏曲专题学习"),
            (activities[1].id, users[4].id, "registered", "古琴入门"), (activities[2].id, users[1].id, "registered", "工艺协同观察"),
            (activities[3].id, users[6].id, "registered", "青瓷实践"), (activities[4].id, users[2].id, "registered", "亲子节俗体验"),
            (activities[6].id, users[5].id, "registered", "粤剧观演"), (activities[7].id, users[7].id, "registered", "材料认知"),
        ]
        for aid, uid, st, rm in regs: db.add(ActivityRegistration(activity_id=aid, user_id=uid, status=st, remark=rm))

        kb_rows = [
            ("昆曲入门先做什么？", "先阅读导赏内容，再参加活动观演，最后在论坛讨论复盘。", "昆曲,戏曲,内容,活动,论坛", "戏曲与表演艺术", "昆曲"),
            ("古琴为什么要听赏优先？", "先建立音色识别，再练指法，推荐链路会更稳定。", "古琴,传统音乐,知识阅读", "传统音乐", "古琴"),
            ("云锦工艺难点在哪里？", "难在纹样、色线、机台协同，适合先看内容再去活动体验。", "云锦,工艺,活动体验", "传统美术与工艺", "云锦"),
            ("端午为什么是活态民俗？", "因为节俗实践持续发生在家庭和社区活动场景。", "端午节,节俗,民俗", "岁时节庆与民俗", "端午节"),
            ("粤剧新观众最常见问题？", "不了解角色关系和唱段结构，可用演前导赏解决。", "粤剧,戏曲,导赏", "戏曲与表演艺术", "粤剧"),
            ("宣纸学习为什么要做对照实验？", "同笔同墨在不同纸上的差异最能建立材料认知。", "宣纸,书法,传统美术", "传统美术与工艺", "宣纸"),
            ("龙泉青瓷如何判断温润？", "看釉层均匀度、光线层次和器形匹配。", "龙泉青瓷,传统技艺", "传统美术与工艺", "龙泉青瓷"),
            ("剪纸课堂如何提升质量？", "前置寓意讲解，后置复盘表达，避免只做手工。", "中国剪纸,传统美术,课堂", "传统美术与工艺", "中国剪纸"),
            ("第一次和黑塔聊天，为什么它会先问我偏好？", "因为很多人刚进入时还没想清楚要看什么，先从兴趣和体验方式聊起，通常更容易找到合适的内容和活动。", "黑塔,入门,偏好,导览", "导览与学习路径", "智能导览"),
            ("为什么有时候推荐理由会强调‘适合你现在看’，而不是只讲内容本身？", "因为同一条内容放在不同阶段价值不一样。有时你需要的是入门线索，有时需要的是更深入的体验，所以推荐理由也会跟着变化。", "推荐理由,入门,体验,阶段", "导览与学习路径", "推荐理解"),
            ("为什么我最近看了几篇内容后，首页推荐会慢慢变得更集中？", "通常是因为你的阅读和参与方向开始稳定了，系统会优先把相近主题、相近体验方式的内容继续往前排。", "首页推荐,阅读行为,兴趣变化", "用户理解与传播", "行为观察"),
            ("社区里点赞和评论多的话题，为什么不一定都适合直接推荐给我？", "因为讨论热度说明大家愿意交流，但不一定代表它正好符合你的当前兴趣方向，所以还要结合你最近看的内容和活动倾向一起判断。", "社区,热度,推荐判断", "社区互动", "讨论内容"),
            ("第一次接触非遗时，为什么常常会同时看到内容、活动和讨论三种入口？", "因为很多人需要先了解一点背景，再看看能不能参与体验，最后再从别人的讨论里补足感受，这三种入口放在一起更方便判断下一步。", "内容,活动,讨论,入门路径", "导览与学习路径", "入门路径"),
            ("为什么有时候系统不给我很确定的答案，而是先推荐几个方向？", "如果你的兴趣还在形成中，先给几个方向反而更有帮助。这样既不会把范围卡得太死，也更容易找到你真正想深入的主题。", "方向推荐,入门,兴趣形成", "导览与学习路径", "推荐理解"),
        ]
        for q, a, k, ch, sub in kb_rows:
            db.add(LocalKnowledgeBase(question=q, answer=a, qa_answer=a, keywords=k, chapter=ch, sub_chapter=sub, source="人工策编-算法对齐", status="active"))

        # feed recommendation logs/qa for personalization
        logs = [
            (users[0].id, "click", "content", 1, "home"), (users[0].id, "view", "event", 1, "activity"), (users[0].id, "click", "topic", 1, "discussion"),
            (users[1].id, "click", "content", 3, "home"), (users[1].id, "view", "event", 3, "activity"), (users[1].id, "click", "topic", 2, "discussion"),
            (users[2].id, "click", "content", 5, "home"), (users[2].id, "view", "event", 5, "activity"), (users[2].id, "click", "topic", 4, "discussion"),
            (users[5].id, "click", "content", 7, "home"), (users[5].id, "view", "event", 7, "activity"), (users[5].id, "click", "topic", 6, "discussion"),
        ]
        for uid, act, tp, tid, sc in logs: db.add(RecommendLog(user_id=uid, action=act, target_type=tp, target_id=tid, source_scene=sc, explain_json="{}"))

        qa = [
            (users[0].id, "我想了解昆曲活动和导赏阅读", "建议先看昆曲内容，再报导赏活动。"),
            (users[1].id, "云锦工艺活动报名后还需要先读什么", "先看云锦协同流程内容更有效。"),
            (users[2].id, "端午节俗亲子活动怎么安排", "可用讲解+体验+复盘三段式。"),
            (users[5].id, "粤剧观演前要准备什么", "先看角色关系和唱段导读。"),
        ]
        for uid, qx, ax in qa: db.add(AIQALog(user_id=uid, question=qx, answer=ax, source="local_kb", confidence=0.92))

        db.commit()
        print("已写入人工高质量数据（算法对齐）：users=12, contents=18, activities=8, topics=12, kb=14")
    finally:
        db.close()


if __name__ == "__main__":
    main()
