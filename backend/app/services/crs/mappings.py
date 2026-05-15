"""偏好映射字典

新增映射只需在此文件添加条目，其他模块通过 lookup 函数访问。
"""

OPTION_TO_PREFERENCE = {
    "传统工艺": ("preferred_heritage_types", "工艺"),
    "戏曲音乐": ("preferred_heritage_types", "戏曲"),
    "民俗节俗": ("preferred_heritage_types", "民俗"),
    "饮食医药": ("preferred_heritage_types", "医药"),
    "手工艺与技法": ("preferred_heritage_types", "工艺"),
    "戏曲与音乐": ("preferred_heritage_types", "戏曲"),
    "节俗与信仰": ("preferred_heritage_types", "民俗"),
    "医药与饮食": ("preferred_heritage_types", "医药"),
    "想看更多工艺类": ("preferred_heritage_types", "工艺"),
    "想了解戏曲类": ("preferred_heritage_types", "戏曲"),
    "看看民俗方向": ("preferred_heritage_types", "民俗"),
    "华东地区": ("preferred_regions", "华东"),
    "华南地区": ("preferred_regions", "华南"),
    "西南地区": ("preferred_regions", "西南"),
    "阅读了解": ("preferred_scene_types", "知识阅读"),
    "线下体验": ("preferred_scene_types", "活动体验"),
    "社区交流": ("preferred_scene_types", "论坛交流"),
    "推荐些线下活动": ("preferred_scene_types", "活动体验"),
    "找点社区讨论": ("preferred_scene_types", "论坛交流"),
    "更多内容推荐": ("preferred_scene_types", "知识阅读"),
    "继续了解当前话题": ("preferred_scene_types", "知识阅读"),
    "看看推荐内容": ("preferred_scene_types", "知识阅读"),
    "找线下活动参加": ("preferred_scene_types", "活动体验"),
    "从内容科普开始": ("preferred_scene_types", "知识阅读"),
    "找线下活动": ("preferred_scene_types", "活动体验"),
    "看看社区讨论": ("preferred_scene_types", "论坛交流"),
    "刚入门": (None, "beginner"),
    "有一定了解": (None, "intermediate"),
    "比较熟悉": (None, "advanced"),
}

KG_ENTITY_TO_CATEGORY = {
    "苏绣": "工艺", "蜀绣": "工艺", "湘绣": "工艺", "粤绣": "工艺",
    "南京云锦": "工艺", "宜兴紫砂陶制作技艺": "工艺", "龙泉青瓷烧制技艺": "工艺",
    "木版年画": "工艺", "中国剪纸": "工艺", "中国书法": "工艺",
    "昆曲": "戏曲", "京剧": "戏曲", "越剧": "戏曲", "黄梅戏": "戏曲", "古琴艺术": "戏曲",
    "皮影戏": "戏曲",
    "端午节": "民俗", "二十四节气": "民俗",
    "中医针灸": "医药",
    "太极拳": "工艺",
}

KB_CHAPTER_TO_PREFERENCE = {
    "传统工艺": "工艺", "传统美术": "传统美术",
    "戏曲与表演艺术": "戏曲", "传统音乐": "传统音乐",
    "岁时节庆与民俗": "民俗", "传统医药": "医药", "传统体育": "工艺",
    "非遗基础认知": None, "传承实践": None, "保护制度": None,
    "国际传播": None, "数字化体验": None,
}

QUESTION_HERITAGE_MAP = {
    "工艺": "工艺", "手工": "工艺", "绣": "工艺", "瓷": "工艺", "锦": "工艺",
    "紫砂": "工艺", "蜡染": "工艺", "剪纸": "工艺", "书法": "传统美术", "美术": "传统美术",
    "戏曲": "戏曲", "昆曲": "戏曲", "京剧": "戏曲", "皮影": "戏曲", "越剧": "戏曲",
    "音乐": "传统音乐", "古琴": "传统音乐", "南音": "传统音乐",
    "民俗": "民俗", "节俗": "民俗", "节气": "民俗", "端午": "民俗", "节庆": "民俗", "非遗": "民俗",
    "医药": "医药", "针灸": "医药", "中药": "医药",
    "体育": "工艺", "太极": "工艺", "武术": "工艺", "围棋": "工艺",
    "饮食": "医药", "酿造": "医药", "茶": "医药",
}

QUESTION_SCENE_MAP = {
    "线下体验": "线下体验", "体验活动": "线下体验", "动手": "线下体验",
    "自己动手": "线下体验", "参加": "线下体验", "工坊": "线下体验",
    "体验": "线下体验", "传习": "线下体验", "研学": "线下体验",
    "深度阅读": "知识阅读", "了解": "知识阅读", "阅读": "知识阅读",
    "科普": "知识阅读", "学习": "知识阅读", "入门": "知识阅读",
    "社区": "社区互动", "讨论": "社区互动", "话题": "社区互动",
    "论坛": "社区互动", "分享": "社区互动",
    "旅游": "文旅融合", "旅行": "文旅融合", "游玩": "文旅融合",
    "博物馆": "文旅融合", "展览": "文旅融合", "文创": "文旅融合",
    "数字化": "数字化体验", "VR": "数字化体验", "AI": "数字化体验",
    "短视频": "数字化体验", "直播": "数字化体验", "AR": "数字化体验",
    "校园": "校园教育", "教育": "校园教育", "学生": "校园教育",
}

QUESTION_REGION_MAP = {
    "华东": "华东", "华南": "华南", "西南": "西南", "华北": "华北",
    "西北": "西北", "东北": "东北", "华中": "华中",
    "广东": "华南", "广西": "华南", "海南": "华南", "福建": "华南",
    "湖南": "华中", "湖北": "华中", "河南": "华中",
    "浙江": "华东", "江苏": "华东", "上海": "华东", "安徽": "华东", "江西": "华东",
    "北京": "华北", "天津": "华北", "河北": "华北", "山东": "华北", "山西": "华北",
    "四川": "西南", "重庆": "西南", "云南": "西南", "贵州": "西南", "西藏": "西南",
    "陕西": "西北", "甘肃": "西北", "新疆": "西北", "宁夏": "西北", "青海": "西北",
    "辽宁": "东北", "吉林": "东北", "黑龙江": "东北",
    "粤": "华南", "藏": "西南", "蜀": "西南", "湘": "华中",
    "苏": "华东", "徽": "华东", "赣": "华东", "闽": "华南",
    "京": "华北", "晋": "华北", "鲁": "华北",
    "国际": "国际", "联合国": "国际", "海外": "国际",
    "全国": "全国",
}


def lookup_option_preference(answer_text: str) -> tuple[str | None, str] | None:
    return OPTION_TO_PREFERENCE.get(answer_text)


def lookup_kg_entity_category(entity: str) -> str | None:
    return KG_ENTITY_TO_CATEGORY.get(entity)


def lookup_kb_chapter_preference(chapter: str) -> str | None:
    return KB_CHAPTER_TO_PREFERENCE.get(chapter)


def lookup_question_preferences(question: str) -> dict[str, set[str]]:
    """从问题文本中提取三类偏好信号：heritage / scene / region"""
    q = (question or "").strip()
    return {
        "heritage": {v for k, v in QUESTION_HERITAGE_MAP.items() if k in q},
        "scene": {v for k, v in QUESTION_SCENE_MAP.items() if k in q},
        "region": {v for k, v in QUESTION_REGION_MAP.items() if k in q},
    }
