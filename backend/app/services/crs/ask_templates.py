"""ASK 提问模板

A系列(冷启动) → B系列(混合追问) → R系列(恢复模式)
"""

ASK_TEMPLATES = {
    "A01": {"attribute": "category", "prompt": "你最想了解哪类非物质文化遗产？", "options": ["传统工艺", "戏曲音乐", "民俗节俗", "饮食医药"], "score_delta": 25},
    "A02": {"attribute": "region", "prompt": "你更关注哪个地区的非遗？", "options": ["华东地区", "华南地区", "西南地区", "暂时跳过"], "score_delta": 20},
    "A03": {"attribute": "scene", "prompt": "你更偏好哪种体验方式？", "options": ["阅读了解", "线下体验", "社区交流"], "score_delta": 20},
    "A04": {"attribute": "level", "prompt": "你对非遗的了解程度？", "options": ["刚入门", "有一定了解", "比较熟悉"], "score_delta": 15},
    "A05": {"attribute": "category", "prompt": "下面哪个方向最吸引你？", "options": ["手工艺与技法", "戏曲与音乐", "节俗与信仰", "医药与饮食"], "score_delta": 20},
    "B01": {"attribute": "category", "prompt": "在这些推荐之外，你还有没有特别想深入的非遗类型？", "options": ["想看更多工艺类", "想了解戏曲类", "看看民俗方向", "暂时不用"], "score_delta": 15},
    "B02": {"attribute": "scene", "prompt": "我还可以帮你在其他方向找找看？", "options": ["推荐些线下活动", "找点社区讨论", "更多内容推荐", "不用了"], "score_delta": 10},
    "B03": {"attribute": "region", "prompt": "要不要看看其他地区的非遗项目？", "options": ["华东地区", "华南地区", "西南地区", "暂时不用"], "score_delta": 10},
    "B04": {"attribute": "category", "prompt": "要不要试试这个方向？", "options": ["好，试试看", "换一个方向", "保持现在的"], "score_delta": 10},
    "B05": {"attribute": "scene", "prompt": "你现在更想做什么？", "options": ["继续了解当前话题", "看看推荐内容", "找线下活动参加"], "score_delta": 10},
    "R01": {"attribute": "category", "prompt": "换个方向试试？你最想了解哪类非遗？", "options": ["传统工艺", "戏曲音乐", "民俗节俗", "饮食医药"], "score_delta": 20},
    "R02": {"attribute": "scene", "prompt": "我帮你重新找找方向吧？", "options": ["从内容科普开始", "找线下活动", "看看社区讨论"], "score_delta": 15},
    "R03": {"attribute": "category", "prompt": "不如我们先从热门方向开始？", "options": ["好，从热门开始", "我有特定方向", "随便推荐"], "score_delta": 15},
}

SKIP_ANSWERS = {"跳过", "暂时跳过", "暂时不用", "不用了"}

RECOMMEND_INTENT_TERMS = ["推荐", "适合", "先看", "先了解", "参加什么", "看什么", "怎么玩", "路线"]

CLARIFY_TERMS = ["想了解", "想看看", "随便", "不知道", "有什么", "怎么开始", "从哪开始"]
