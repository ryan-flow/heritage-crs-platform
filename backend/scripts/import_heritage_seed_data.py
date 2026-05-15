from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.content import Content
from app.models.local_knowledge_base import LocalKnowledgeBase


SEED_SOURCE = "heritage_seed_v1"
COVERS_DIR = BASE_DIR / "storage" / "covers"


HERITAGE_ITEMS = [
    {
        "slug": "kunqu",
        "title": "昆曲",
        "chapter": "戏曲与表演艺术",
        "sub_chapter": "昆曲",
        "summary": "昆曲以曲词典雅、唱腔婉转和表演细腻著称，被视为中国戏曲审美传统中的重要代表。",
        "body": "昆曲形成较早，长期在中国戏曲发展中占有重要位置。它的唱腔讲究水磨腔的细腻流转，文学性、音乐性和身段表演高度统一，既能表现抒情之美，也能承载人物情感的深层变化。今天谈中国古典戏曲之美，昆曲常常是绕不开的一门艺术，因为它不仅保留了传统戏曲的程式，也展现了中国文人审美、舞台节奏与叙事气质的综合魅力。",
        "keywords": ["昆曲", "戏曲", "水磨腔", "表演艺术"],
        "qa": [
            ("昆曲为什么被称为百戏之祖？", "昆曲常被称为“百戏之祖”，主要是因为它在中国戏曲发展史上影响深远，很多后来的剧种在音乐、表演和审美上都曾吸收昆曲经验。它并不是简单意义上的“最早”，而是被视作古典戏曲成熟形态的重要代表。"),
            ("昆曲最吸引人的艺术特点是什么？", "昆曲最吸引人的地方在于唱腔细腻、文学气质浓、表演讲究分寸感。它不像某些剧种那样以强烈冲突取胜，而是通过水磨般的旋律和极精致的身段，把人物情绪一点点渗出来。"),
        ],
    },
    {
        "slug": "guqin",
        "title": "古琴艺术",
        "chapter": "传统音乐",
        "sub_chapter": "古琴艺术",
        "summary": "古琴艺术强调音色、气韵与人格修养的统一，是中国传统音乐中极具精神气质的一支。",
        "body": "古琴不仅是一种乐器，也是一整套审美与修习方式。它的声音清远含蓄，重视散音、泛音与按音之间的层次变化，演奏时讲究呼吸、节奏和意境的统一。古琴文化长期与诗文、书画、园林和士人修养相互关联，因此人们谈古琴，往往不仅在谈音乐技巧，也在谈一种安静、克制而有深度的文化气质。",
        "keywords": ["古琴", "传统音乐", "雅乐", "琴曲"],
        "qa": [
            ("古琴为什么不仅仅是一种乐器？", "因为古琴背后连接着中国传统的审美观、修养观和生活方式。它不仅要求演奏者掌握指法，更强调心境、节奏和意境，所以古琴常被看作一种融合音乐、文学与人格修炼的综合艺术。"),
            ("古琴的音色有什么特别之处？", "古琴的音色不以宏大响亮取胜，而是讲究清、微、淡、远。它的声音有很多细微层次，适合表现静思、山水、怀古等更内敛的情绪，这也是它区别于很多舞台型乐器的重要地方。"),
        ],
    },
    {
        "slug": "paper-cutting",
        "title": "中国剪纸",
        "chapter": "传统美术与工艺",
        "sub_chapter": "中国剪纸",
        "summary": "中国剪纸以纸为媒介，把祝福、礼俗与地域审美转化为富有生命力的图案艺术。",
        "body": "剪纸广泛存在于节庆、婚嫁、祈福和日常装饰之中，它看似材料简单，却在构图、纹样和刀法上形成了极丰富的传统。不同地区的剪纸风格差异明显，有的朴拙热烈，有的细密秀雅，但共同之处是都把民间生活经验和吉祥观念浓缩进了一张纸里。它既是视觉艺术，也是民俗记忆的承载方式。",
        "keywords": ["剪纸", "民间美术", "窗花", "传统工艺"],
        "qa": [
            ("中国剪纸为什么能代表民间审美？", "因为剪纸直接来自民间生活。它的题材常常围绕花鸟、人物、节令和吉祥寓意展开，既实用又富有情感，所以很能体现普通百姓对生活、礼俗和美好愿望的表达。"),
            ("剪纸只有装饰作用吗？", "不只是装饰。剪纸还和婚礼、春节、祭祀、祝寿等礼俗紧密相关，很多图案本身就带有祝福、祈愿和身份认同的意义，因此它兼具艺术价值和文化功能。"),
        ],
    },
    {
        "slug": "yunjin",
        "title": "南京云锦木机妆花手工织造技艺",
        "chapter": "传统美术与工艺",
        "sub_chapter": "丝织工艺",
        "summary": "南京云锦以华丽庄重的纹样和复杂精细的织造流程闻名，是中国高等级丝织工艺的重要代表。",
        "body": "南京云锦的价值不仅体现在成品绚丽，还体现在完整而复杂的工艺体系之中。从设计纹样、配色、整经到木机妆花的协同操作，每一个环节都高度依赖经验与手工配合。它长期与礼制、服饰和织物美学相连接，因此既是织造技术成果，也是中国传统纹样与色彩系统的集中体现。",
        "keywords": ["云锦", "南京云锦", "丝织", "妆花"],
        "qa": [
            ("南京云锦为什么显得特别华丽？", "因为云锦在纹样布局、色彩组合和织造层次上都非常讲究，它追求的是一种厚重、富丽又不失秩序感的视觉效果。很多人看到云锦，会立刻感受到中国传统织物特有的庄重与精美。"),
            ("云锦技艺难在哪里？", "难点在于它不是单一动作，而是一整套复杂流程的配合。图样理解、色线组织、木机操作和经验判断缺一不可，所以云锦的传承门槛很高，也更能体现手工技艺的珍贵。"),
        ],
    },
    {
        "slug": "seal-carving",
        "title": "中国篆刻",
        "chapter": "传统美术与工艺",
        "sub_chapter": "中国篆刻",
        "summary": "中国篆刻融合文字、书法、构图与刀法，是兼具实用性与艺术性的独特门类。",
        "body": "篆刻以印章为载体，却远不止于日常印记。它把汉字结构、书法线条和金石趣味结合在一起，通过方寸之间的布局形成独立的审美世界。篆刻作品看似小巧，却常常蕴含极强的节奏感和空间经营能力，因此被视作中国传统艺术中最能体现“以小见大”的门类之一。",
        "keywords": ["篆刻", "印章", "书法", "金石"],
        "qa": [
            ("中国篆刻为什么和书法关系密切？", "因为篆刻本质上离不开汉字。印面上的文字需要书法修养来支撑，而刀法又会进一步改变线条气质，所以一方好印，往往同时体现书法眼光、构图能力和刀法功底。"),
            ("篆刻的魅力体现在哪？", "它的魅力在于方寸之间的变化。很小的一块印面，可以通过字形疏密、线条粗细和留白关系，呈现非常丰富的精神气质，这种高度凝练的表达很有东方艺术特色。"),
        ],
    },
    {
        "slug": "longquan-celadon",
        "title": "龙泉青瓷传统烧制技艺",
        "chapter": "传统美术与工艺",
        "sub_chapter": "陶瓷技艺",
        "summary": "龙泉青瓷以温润如玉的釉色和器形审美著称，是中国陶瓷工艺的重要象征之一。",
        "body": "龙泉青瓷的迷人之处在于其釉色与器形的统一。匠人通过泥料选择、成型、修坯、施釉和烧制，追求青瓷独有的温润质感。看一件好的龙泉青瓷，往往能感受到一种含蓄、安静而持久的美，这种美并不张扬，却很能体现中国传统器物审美里“雅”和“净”的追求。",
        "keywords": ["龙泉青瓷", "青瓷", "陶瓷", "烧制技艺"],
        "qa": [
            ("龙泉青瓷为什么常被形容为温润如玉？", "因为它的釉色和质感给人一种柔和、含蓄、层次丰富的视觉体验，不是强烈发光的那种亮，而是像玉一样有内在光泽，所以常被称为温润如玉。"),
            ("青瓷烧制最关键的地方是什么？", "关键在于泥、釉、火三者的配合。原料差一点、施釉不稳或者火候控制失准，最后呈现出的釉色和器表质感都会明显不同，所以这项技艺非常依赖长期经验。"),
        ],
    },
    {
        "slug": "dragon-boat-festival",
        "title": "端午节",
        "chapter": "岁时节庆与民俗",
        "sub_chapter": "端午节",
        "summary": "端午节汇集竞渡、粽食、香囊、辟邪习俗等内容，是中国传统节俗体系中的重要节日。",
        "body": "端午节并不是单一活动，而是一整套节俗系统。不同地区会有赛龙舟、吃粽子、悬艾草、佩香囊、沐兰汤等多种习俗，这些习俗共同构成了端午节的文化面貌。它既与季节转换、卫生观念和群体记忆有关，也体现了中国传统社会通过节令组织家庭与社区生活的方式。",
        "keywords": ["端午节", "节俗", "龙舟", "粽子"],
        "qa": [
            ("端午节为什么不仅仅是吃粽子？", "因为粽子只是端午节最广为人知的一种表达。真正的端午文化还包括竞渡、辟邪、祈安、家庭团聚和社区活动等内容，它是一套完整的传统节俗，而不是单一道具。"),
            ("端午节的非遗价值体现在哪？", "它的价值在于节俗至今仍与现实生活紧密相连。无论是龙舟竞渡还是家庭包粽，很多传统都还在真实发生，所以端午节体现的是活态传承，而不只是历史记忆。"),
        ],
    },
    {
        "slug": "woodblock-new-year-print",
        "title": "中国木版年画",
        "chapter": "传统美术与工艺",
        "sub_chapter": "年画艺术",
        "summary": "木版年画以喜庆鲜明的视觉风格记录节俗、信仰与民间生活，是春节文化的重要图像记忆。",
        "body": "木版年画与中国春节生活有深厚联系。它通过刻版、套色和印制，把门神、吉祥娃娃、丰收场景和神话人物转化成家庭年节中的视觉符号。年画的价值不仅在图像好看，更在于它体现了民众对来年安康、丰收和吉庆的想象，因此是一种高度生活化的民间艺术。",
        "keywords": ["木版年画", "年画", "春节", "民间美术"],
        "qa": [
            ("木版年画为什么和春节关系这么紧密？", "因为年画本来就是年节视觉文化的一部分。贴年画、换门神、布置新春气氛，这些都和家庭迎新、祈福纳吉有关，所以它天然和春节生活连在一起。"),
            ("木版年画的艺术特点是什么？", "它通常色彩鲜明、构图饱满、主题直白热烈，强调一看就能感受到喜气和祝福。这种强烈而朴素的感染力，正是它在民间长期流传的重要原因。"),
        ],
    },
    {
        "slug": "tibetan-opera",
        "title": "藏戏",
        "chapter": "戏曲与表演艺术",
        "sub_chapter": "藏戏",
        "summary": "藏戏综合歌唱、舞蹈、叙事与宗教文化因素，是藏族传统表演艺术的重要代表。",
        "body": "藏戏具有鲜明的地域文化气质，常见面具、程式动作、长篇叙事和音乐表演交织在一起。它不是单纯的舞台娱乐，而是和节庆、社区生活、历史记忆密切相关。藏戏之所以珍贵，在于它保留了传统表演艺术与族群文化表达相结合的完整面貌，让观众在看戏的同时感受到一整套文化世界。",
        "keywords": ["藏戏", "藏族", "表演艺术", "面具"],
        "qa": [
            ("藏戏的独特魅力体现在哪里？", "藏戏最独特的地方在于它并不是单一唱戏，而是把歌舞、叙事、仪式感和社区参与结合起来。观众看到的不是一段单纯表演，而是一个完整文化场景。"),
            ("藏戏为什么常使用面具？", "面具不仅帮助塑造人物，也增强了表演的象征性和仪式感。它让角色身份更鲜明，同时形成了藏戏极具辨识度的舞台视觉风格。"),
        ],
    },
    {
        "slug": "cantonese-opera",
        "title": "粤剧",
        "chapter": "戏曲与表演艺术",
        "sub_chapter": "粤剧",
        "summary": "粤剧在岭南文化环境中形成独特风格，以唱做并重、节奏鲜明和舞台表现力强而广受喜爱。",
        "body": "粤剧长期活跃在岭南地区及海外华人社会中，是传播范围很广的一种中国地方戏曲。它吸收了多种戏曲养分，又形成了自己的唱腔表达、人物塑造和舞台节奏。粤剧既有传统折子戏的经典魅力，也能在现代剧场和当代传播环境中持续焕发活力，因此被视作兼具历史底蕴和现实传播力的戏曲艺术。",
        "keywords": ["粤剧", "岭南文化", "戏曲", "表演艺术"],
        "qa": [
            ("粤剧为什么能长期保持活力？", "因为粤剧既有深厚传统，又很重视与观众的连接。它在音乐、表演和舞台节奏上都比较鲜明，既能保留老戏韵味，也能不断适应新的传播方式，所以生命力很强。"),
            ("粤剧体现了怎样的地域文化气质？", "它体现了岭南文化中开放、灵动、讲究舞台感染力的一面。无论唱腔还是人物表达，粤剧都带有明显的地方审美特征，同时又能被更广泛的观众理解和接受。"),
        ],
    },
    {
        "slug": "xuan-paper",
        "title": "宣纸传统制作技艺",
        "chapter": "传统美术与工艺",
        "sub_chapter": "造纸技艺",
        "summary": "宣纸制作讲究原料、工序与纸性控制，是中国书画用纸传统中的重要技艺。",
        "body": "宣纸之所以珍贵，在于它不仅是一张纸，而是一种为书写与绘画服务的材料文明。匠人通过选料、蒸煮、漂洗、打浆、抄纸和晾晒等多道工序，逐步形成宣纸独有的吸墨、润墨和耐久特性。书画艺术之所以能呈现丰富的笔墨层次，背后离不开宣纸这种材料系统的长期发展。",
        "keywords": ["宣纸", "造纸", "书画", "传统工艺"],
        "qa": [
            ("宣纸为什么对中国书画这么重要？", "因为宣纸的纸性非常适合笔墨表现。它既能吸收墨色，又能保留层次变化，所以书法和水墨画中很多微妙效果，都要依靠宣纸才能充分呈现。"),
            ("宣纸制作技艺珍贵在哪里？", "珍贵之处在于它是一整套成熟工艺，而不是简单造纸。材料选择、工序次序和经验判断都会影响最终纸张性能，所以它代表的是长期积累下来的工艺智慧。"),
        ],
    },
    {
        "slug": "silk-weaving",
        "title": "中国蚕桑丝织技艺",
        "chapter": "传统美术与工艺",
        "sub_chapter": "丝织工艺",
        "summary": "中国蚕桑丝织技艺从养蚕、缫丝到织造构成完整体系，是中华丝绸文明的重要基础。",
        "body": "蚕桑丝织技艺并不是某一个单点技术，而是一整条从生产到织造的传统链路。它既包含农事经验，也包含纤维处理、染整和织造智慧。丝绸之所以能在中国传统生活与审美中占据重要位置，背后正是这种复合型技艺体系的长期支撑。看丝织技艺，也是在看中国如何把自然资源、生活需求和高级审美结合起来。",
        "keywords": ["蚕桑丝织", "丝绸", "织造", "传统工艺"],
        "qa": [
            ("中国蚕桑丝织技艺为什么重要？", "它重要在于不仅影响服饰和生活用品，也深刻影响了中国传统审美和工艺体系。丝绸文明背后不是一项孤立技术，而是一整套成熟的生产与艺术系统。"),
            ("蚕桑丝织技艺包含哪些环节？", "通常会涉及养蚕、缫丝、染整、织造等多个环节。正因为链路完整，所以它能体现古代中国在材料利用和工艺组织上的高水平。"),
        ],
    },
]


CATEGORY_STANDARD_QA = [
    (
        "中国非遗保护经历了哪些重要阶段？",
        "中国非遗保护大体经历了抢救记录、名录体系建设、法治化推进和活化传播四个阶段。早期重在普查与抢救，之后逐步建立分级名录与传承人制度，2011年《非遗法》实施后进入制度化保护，近年更强调数字化传播与创新转化。",
        "中国非遗保护阶段,非遗法,名录制度",
        "保护制度",
        "发展阶段",
    ),
    (
        "国家级非遗代表性项目大致有哪些门类？",
        "常见门类包括民间文学、传统音乐、传统舞蹈、传统戏剧、曲艺、传统体育游艺与杂技、传统美术、传统技艺、传统医药和民俗等。",
        "非遗门类,代表性项目,分类",
        "保护制度",
        "项目分类",
    ),
    (
        "为什么要保护非遗？",
        "非遗承载历史记忆、地方知识和生活方式。保护非遗不仅是保存技艺本身，也是在延续社区文化认同与代际传承能力。",
        "非遗价值,文化认同,传承",
        "保护制度",
        "保护意义",
    ),
]


def build_item_standard_qa(item: dict) -> list[tuple[str, str]]:
    title = item["title"]
    summary = item["summary"]
    chapter = item["chapter"]
    sub = item["sub_chapter"]
    return [
        (f"{title}属于哪一类非遗？", f"{title}通常归入“{chapter}”方向，细分可对应“{sub}”相关内容。"),
        (f"{title}最核心的文化价值是什么？", f"{title}的核心价值在于{summary}"),
        (f"第一次了解{title}，先看什么？", f"建议先把握它的历史背景、典型表现形式和当代传承方式，这三点最能快速建立对{title}的整体认识。"),
        (f"{title}为什么值得当代人关注？", f"因为{title}不仅是传统技艺或表演形式，也连接着地域记忆与生活智慧，对今天的文化认同仍有现实意义。"),
        (f"{title}在当代如何实现传承？", f"通常通过师徒教学、校园课程、展演展示、文旅融合和数字传播等方式推动{title}的持续传承。"),
        (f"{title}和其他非遗项目有什么共同点？", f"{title}与多数非遗项目一样，都强调活态传承，核心是“有人学、有人做、有人看、有人用”。"),
        (f"{title}适合怎样的体验方式？", f"可以从导览讲解、现场观演或工艺体验入手，再结合背景资料阅读，理解会更完整。"),
        (f"{title}的学习门槛高吗？", f"{title}通常需要长期练习与稳定训练，入门可先从基础认知和观察经典案例开始，再逐步实践。"),
        (f"如何向青少年介绍{title}？", f"可用“故事化背景+可视化示例+小任务体验”方式介绍{title}，更容易激发兴趣并形成记忆。"),
        (f"{title}在数字化传播中可以怎么做？", f"可通过短视频讲解、数字展陈、互动问答和线上课程等方式，让{title}更容易被公众理解和传播。"),
        (f"围绕{title}做文化活动，推荐什么主题？", f"推荐“历史脉络、技艺细节、代表作品、当代创新”四段式主题，便于形成完整活动内容。"),
        (f"{title}与地方文化有什么关系？", f"{title}往往与特定地域的语言、审美和生活习惯长期共生，是地方文化识别度的重要组成部分。"),
    ]


def build_standard_qa_records() -> list[dict]:
    records: list[dict] = []

    for question, answer, keywords, chapter, sub in CATEGORY_STANDARD_QA:
        records.append(
            {
                "question": question,
                "answer": answer,
                "qa_answer": answer,
                "keywords": keywords,
                "chapter": chapter,
                "sub_chapter": sub,
                "source": "heritage_standard_qa_v1",
                "status": "active",
            }
        )

    for item in HERITAGE_ITEMS:
        for q, a in build_item_standard_qa(item):
            records.append(
                {
                    "question": q,
                    "answer": a,
                    "qa_answer": a,
                    "keywords": ",".join(item["keywords"]),
                    "chapter": item["chapter"],
                    "sub_chapter": item["sub_chapter"],
                    "source": "heritage_standard_qa_v1",
                    "status": "active",
                }
            )
    return records


SVG_TEMPLATE = """<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='720' viewBox='0 0 1200 720'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='{c1}'/>
      <stop offset='100%' stop-color='{c2}'/>
    </linearGradient>
    <radialGradient id='glow' cx='50%' cy='40%' r='60%'>
      <stop offset='0%' stop-color='rgba(255,244,228,0.95)'/>
      <stop offset='100%' stop-color='rgba(255,244,228,0)'/>
    </radialGradient>
  </defs>
  <rect width='1200' height='720' rx='36' fill='url(#bg)'/>
  <circle cx='920' cy='170' r='210' fill='rgba(255,255,255,0.08)'/>
  <circle cx='1020' cy='540' r='180' fill='rgba(255,224,183,0.1)'/>
  <circle cx='850' cy='160' r='120' fill='url(#glow)'/>
  <rect x='82' y='92' width='190' height='44' rx='22' fill='rgba(255,248,238,0.16)'/>
  <text x='112' y='121' fill='#FFE3C0' font-size='24' font-family='Microsoft YaHei, PingFang SC, sans-serif' letter-spacing='2'>{chapter}</text>
  <text x='82' y='270' fill='#FFF8F0' font-size='76' font-weight='700' font-family='Microsoft YaHei, PingFang SC, sans-serif'>{title}</text>
  <text x='84' y='344' fill='rgba(255,244,233,0.92)' font-size='30' font-family='Microsoft YaHei, PingFang SC, sans-serif'>{subtitle}</text>
  <text x='84' y='430' fill='rgba(255,241,230,0.88)' font-size='28' font-family='Microsoft YaHei, PingFang SC, sans-serif'>{line1}</text>
  <text x='84' y='474' fill='rgba(255,241,230,0.88)' font-size='28' font-family='Microsoft YaHei, PingFang SC, sans-serif'>{line2}</text>
  <rect x='84' y='552' width='240' height='62' rx='31' fill='rgba(255,232,203,0.15)' stroke='rgba(255,235,208,0.18)'/>
  <text x='126' y='592' fill='#FFE7C8' font-size='28' font-family='Microsoft YaHei, PingFang SC, sans-serif'>中国非遗文化精选</text>
</svg>
"""


PALETTES = [
    ("#2C1713", "#8D2A1D"),
    ("#3A2016", "#AA4A2A"),
    ("#241612", "#A06334"),
    ("#2C2230", "#A15B4C"),
    ("#1F2430", "#8B5E3C"),
    ("#2E1B18", "#B46F43"),
]


def split_summary(summary: str) -> tuple[str, str]:
    text = summary.replace("，", "， ")
    half = max(10, len(text) // 2)
    pivot = text.find("，", half)
    if pivot == -1:
        pivot = half
    return text[: pivot + 1].strip(), text[pivot + 1 :].strip()


def write_cover(item: dict, index: int) -> str:
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    c1, c2 = PALETTES[index % len(PALETTES)]
    line1, line2 = split_summary(item["summary"])
    svg = SVG_TEMPLATE.format(
        c1=c1,
        c2=c2,
        chapter=item["chapter"],
        title=item["title"],
        subtitle=item["sub_chapter"],
        line1=line1[:30],
        line2=line2[:30],
    )
    path = COVERS_DIR / f"{item['slug']}.svg"
    path.write_text(svg, encoding="utf-8")
    return f"/static/covers/{item['slug']}.svg"


def reset_tables(db) -> None:
    db.query(LocalKnowledgeBase).delete()
    db.query(Content).delete()
    db.commit()


def import_contents(db) -> None:
    for index, item in enumerate(HERITAGE_ITEMS):
        cover_url = write_cover(item, index)
        db.add(
            Content(
                title=item["title"],
                cover_url=cover_url,
                content_type="article",
                summary=item["summary"],
                body=item["body"],
                chapter=item["chapter"],
                sub_chapter=item["sub_chapter"],
                status="published",
                created_by=-9,
            )
        )
    db.commit()


def import_knowledge_base(db) -> None:
    for item in HERITAGE_ITEMS:
        for question, answer in item["qa"]:
            db.add(
                LocalKnowledgeBase(
                    question=question,
                    answer=answer,
                    qa_answer=answer,
                    keywords=",".join(item["keywords"]),
                    chapter=item["chapter"],
                    sub_chapter=item["sub_chapter"],
                    source=SEED_SOURCE,
                    status="active",
                )
            )

    # 批量标准问答：用于覆盖更广泛的非遗问法，优先走本地知识库
    for qa in build_standard_qa_records():
        db.add(LocalKnowledgeBase(**qa))

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        reset_tables(db)
        import_contents(db)
        import_knowledge_base(db)
        qa_total = len(HERITAGE_ITEMS) * 2 + len(build_standard_qa_records())
        print(f"已导入 {len(HERITAGE_ITEMS)} 条非遗内容，{qa_total} 条知识库问答。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
