from sqlalchemy.orm import Session

from app.models.local_knowledge_base import LocalKnowledgeBase


HERITAGE_HINTS = (
    "非遗",
    "非物质文化遗产",
    "传统技艺",
    "戏曲",
    "民俗",
    "工艺",
    "传承",
    "昆曲",
    "京剧",
    "越剧",
    "黄梅戏",
    "剪纸",
    "皮影",
    "皮影戏",
    "刺绣",
    "苏绣",
    "湘绣",
    "蜀绣",
    "粤绣",
    "木版",
    "年画",
    "陶瓷",
    "云锦",
    "古琴",
    "古琴艺术",
    "粤剧",
    "藏戏",
    "端午",
    "端午节",
    "春节",
    "中秋",
    "中秋节",
    "清明",
    "清明节",
    "重阳",
    "重阳节",
    "七夕",
    "节气",
    "二十四节气",
    "书法",
    "中国书法",
    "篆刻",
    "中医针灸",
    "针灸",
    "太极拳",
    "太极",
    "武术",
    "围棋",
    "龙舟",
    "紫砂",
    "紫砂壶",
    "宜兴紫砂",
    "龙泉青瓷",
    "青瓷",
    "桑蚕丝织",
    "宣纸",
    "妈祖",
    "木版年画",
    "传统音乐",
    "南音",
    "传统医药",
    "中医药",
    "景泰蓝",
    "花丝镶嵌",
    "雕漆",
    "唐卡",
    "侗族大歌",
    "蒙古族长调",
    "花儿",
    "古建筑",
    "传统村落",
    "非遗法",
    "传承人",
    "人类非遗",
    "那达慕",
    "赛马",
    "摔跤",
    "传统体育",
    "传统节日",
    "岁时节庆",
    "四大名绣",
)

LOCAL_TOWN_HINTS = ()

ALIASES = {
    "非物质文化遗产": ["非遗"],
    "中国非物质文化遗产网": ["中国非遗网", "非遗网"],
    "《中华人民共和国非物质文化遗产法》": ["非遗法", "非物质文化遗产法"],
    "南京云锦织造技艺": ["南京云锦", "云锦"],
    "龙泉青瓷传统烧制技艺": ["龙泉青瓷", "青瓷"],
    "宣纸传统制作技艺": ["宣纸"],
    "中国剪纸": ["剪纸", "窗花"],
    "中国篆刻": ["篆刻"],
    "古琴艺术": ["古琴", "七弦琴"],
    "中国传统桑蚕丝织技艺": ["桑蚕丝织", "丝织技艺", "丝绸技艺"],
    "木版年画": ["年画"],
    "二十四节气": ["节气", "二十四节"],
    "妈祖信俗": ["妈祖"],
    "传承人研修培训计划": ["研修培训计划", "传承人培训计划"],
    "联合国教科文组织": ["联合国非遗", "国际非遗名录", "人类非遗", "UNESCO"],
    "苏绣": ["苏州刺绣", "苏州绣"],
    "湘绣": ["湖南刺绣", "湖南绣"],
    "蜀绣": ["四川刺绣", "川绣"],
    "粤绣": ["广东刺绣", "广绣", "潮绣"],
    "四大名绣": ["苏绣湘绣蜀绣粤绣", "四大刺绣"],
    "中医针灸": ["针灸", "针刺", "艾灸"],
    "太极拳": ["太极", "太极功", "太极武术"],
    "宜兴紫砂陶制作技艺": ["宜兴紫砂", "紫砂壶", "紫砂"],
    "皮影戏": ["皮影", "影戏"],
    "端午节": ["端午", "龙舟节", "五月节"],
    "中国书法": ["书法", "毛笔字"],
    "昆曲": ["昆剧", "昆腔", "水磨腔"],
    "京剧": ["国剧", "平剧", "京戏"],
    "越剧": ["绍兴戏", "越调"],
    "黄梅戏": ["黄梅调", "采茶戏"],
    "藏戏": ["藏族戏曲", "藏族传统戏剧"],
    "粤剧": ["广东大戏", "广府戏"],
    "二胡": ["胡琴", "南胡"],
    "古筝": ["筝", "秦筝", "汉筝"],
    "琵琶": ["琵琶弦乐"],
    "景泰蓝": ["掐丝珐琅", "珐琅彩"],
    "唐卡": ["藏族唐卡", "唐卡绘画"],
    "中国结": ["结绳", "盘长结"],
    "武当功夫": ["武当武术", "内家拳"],
    "少林功夫": ["少林武术", "少林拳", "外家拳"],
    "中国传统制茶技艺": ["制茶技艺", "茶道", "茶艺"],
}

STOPWORDS = {
    "中国",
    "什么",
    "为什么",
    "如何",
    "怎么",
    "哪些",
    "哪个",
    "一个",
    "一种",
    "一下",
    "介绍",
    "说说",
    "请问",
    "请你",
    "我想",
    "想问",
    "一下子",
    "一下下",
    "有关",
    "关于",
    "这个",
    "那个",
    "它",
    "吗",
    "呢",
    "呀",
    "啊",
    "好吃",
    "好玩",
    "吃",
    "喝",
    "去",
    "来",
    "做",
    "看",
    "用",
    "有",
    "是",
    "在",
    "能",
    "会",
    "可以",
    "好吗",
    "好在",
    "难",
    "容易",
    "特点",
    "好处",
    "多",
    "少",
    "大",
    "小",
}

# 意图词映射：用户问题中的词 → KB中对应的语义关键词
INTENT_MAP = {
    # 制作/工艺类
    "怎么做": ["制作", "技艺", "工艺", "制作技艺"],
    "做的": ["制作", "技艺", "工艺"],
    "制作": ["制作", "技艺", "工艺"],
    "制法": ["制作", "技艺", "工艺"],
    "制作过程": ["制作", "技艺", "工艺", "步骤"],
    "怎么制作": ["制作", "技艺", "工艺"],
    "材料": ["材料", "原料", "工艺"],
    # 特点/特征类
    "特点": ["特色", "特点", "特征"],
    "特色": ["特色", "特点", "特征"],
    "特征": ["特色", "特点", "特征"],
    "艺术特点": ["特色", "特点", "特征", "艺术"],
    # 对比类（新增）
    "区别": ["区别", "不同", "差异", "对比"],
    "不同": ["区别", "不同", "差异", "对比"],
    "差异": ["区别", "不同", "差异", "对比"],
    "对比": ["区别", "不同", "差异", "对比"],
    "比较": ["区别", "不同", "差异", "对比"],
    "哪个好": ["区别", "不同", "对比", "代表"],
    "哪个更": ["区别", "不同", "对比"],
    "和.*有什么": ["区别", "不同", "差异"],
    # 时间/起源类（新增）
    "哪年": ["历史", "起源", "由来"],
    "什么时候": ["历史", "起源", "由来"],
    "起源": ["历史", "起源", "由来"],
    "怎么来的": ["历史", "起源", "由来"],
    "历史": ["历史", "起源", "发展", "由来"],
    "来源": ["历史", "起源", "由来"],
    "由来": ["历史", "起源", "由来"],
    "发展": ["历史", "起源", "发展"],
    "多少年": ["历史", "起源", "发展"],
    "始于": ["历史", "起源", "由来"],
    "发明": ["历史", "起源", "由来"],
    # 数量/范围类
    "种类": ["种类", "类型", "分类", "代表"],
    "哪些": ["代表", "种类", "项目"],
    "有几种": ["种类", "类型", "分类"],
    "多少种": ["种类", "类型", "分类"],
    "多少项": ["数量", "名录", "项目"],
    # 入门/学习类
    "入门": ["入门", "新手", "基础", "学习"],
    "怎么学": ["入门", "新手", "基础", "学习"],
    "如何学": ["入门", "新手", "基础", "学习"],
    "学习": ["入门", "新手", "基础", "学习"],
    "怎么参与": ["传承", "保护", "入门", "体验"],
    "如何参与": ["传承", "保护", "入门", "体验"],
    # 意义/价值类
    "意义": ["意义", "价值", "重要性", "作用"],
    "为什么重要": ["意义", "价值", "重要性"],
    "好处": ["价值", "好处", "养生", "功效"],
    "价值": ["意义", "价值", "重要性"],
    # 保护/传承类
    "保护": ["保护", "传承", "保存", "维护"],
    "传承": ["传承", "保护", "传承人"],
    "怎么保护": ["保护", "传承", "保存"],
    "申报": ["申报", "认定", "名录"],
    # 关系类（新增）
    "有什么关系": ["关系", "联系", "区别"],
    "是不是": ["区别", "关系", "联系"],
    "一回事": ["区别", "关系", "联系"],
}

# 非遗产话题硬拦截词（日常生活/天气等无关话题）
OFF_TOPIC_INDICATORS = {
    "天气", "气温", "下雨", "晴天", "吃饭", "吃什么", "今天吃",
    "电影", "游戏", "打球", "上班", "工资", "放假", "旅游攻略",
    "股票", "房价", "外卖", "打车", "快递",
}


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _normalize(text: str) -> str:
    return (
        text.strip()
        .replace("：", " ")
        .replace("，", " ")
        .replace("。", " ")
        .replace("？", " ")
        .replace("！", " ")
        .replace("、", " ")
        .replace("（", " ")
        .replace("）", " ")
        .replace("《", " ")
        .replace("》", " ")
        .replace("\u201c", " ")
        .replace("\u201d", " ")
        .replace("-", " ")
        .replace("/", " ")
        .lower()
    )


def _expand_aliases(text: str) -> str:
    expanded = [text]
    for canonical, alias_list in ALIASES.items():
        if canonical in text:
            expanded.extend(alias_list)
        for alias in alias_list:
            if alias in text:
                expanded.append(canonical)
                expanded.extend(a for a in alias_list if a != alias)
    return " ".join(dict.fromkeys(expanded))


def _extract_entities(text: str) -> list[str]:
    """从文本中抽取已知非遗实体（基于HERITAGE_HINTS + ALIASES）。

    利用实体词表做最长匹配，解决中文无空格分词的问题。
    "什么是昆曲" → ["昆曲"]
    "紫砂壶怎么做的" → ["紫砂壶", "紫砂", "宜兴紫砂"]
    """
    _all_entities = set(HERITAGE_HINTS)
    for canonical, alias_list in ALIASES.items():
        _all_entities.add(canonical)
        _all_entities.update(alias_list)
    # 按长度降序排列，优先匹配长实体
    sorted_entities = sorted(_all_entities, key=len, reverse=True)
    found = []
    for entity in sorted_entities:
        if entity in text:
            found.append(entity)
    return found


# 实体上位词映射：苏绣→刺绣、湘绣→刺绣、蜀绣→刺绣、粤绣→刺绣 等
_ENTITY_BROADER = {
    "苏绣": "刺绣", "苏州刺绣": "刺绣",
    "湘绣": "刺绣", "湖南刺绣": "刺绣",
    "蜀绣": "刺绣", "四川刺绣": "刺绣",
    "粤绣": "刺绣", "广东刺绣": "刺绣",
    "紫砂壶": "紫砂", "宜兴紫砂": "紫砂",
    "太极": "太极拳",
    "端午": "端午节",
    "节气": "二十四节气",
    "书法": "中国书法",
    "篆刻": "中国篆刻",
    "剪纸": "中国剪纸",
    "年画": "木版年画",
    "古琴": "古琴艺术",
    "妈祖": "妈祖信俗",
    "云锦": "南京云锦织造技艺",
    "青瓷": "龙泉青瓷传统烧制技艺",
    "针灸": "中医针灸",
    "皮影": "皮影戏",
    "中秋": "中秋节",
    "清明": "清明节",
    "重阳": "重阳节",
    "龙舟": "赛龙舟",
    "武术": "中国武术",
}


def _expand_with_broader(tokens: list[str]) -> list[str]:
    """将token列表中的实体词扩展上位概念。

    苏绣 → [苏绣, 刺绣]（如果苏绣在_ENTITY_BROADER中）
    这样"苏绣有什么特点"能命中keywords含"刺绣"的KB条目。
    """
    expanded = list(tokens)
    for token in tokens:
        if token in _ENTITY_BROADER:
            broader = _ENTITY_BROADER[token]
            if broader not in expanded:
                expanded.append(broader)
    return expanded


def _extract_core_tokens(text: str) -> list[str]:
    """提取核心token用于匹配（v3 改进版）。

    策略：
    1. 实体词表抽取（解决中文无空格分词）
    2. 实体上位词扩展（苏绣→刺绣）
    3. alias展开后的分词（≥2字，非停用词）
    4. 对≥3字的分词生成3字子串（有限，不再生成2字垃圾）
    """
    # 实体抽取 + 上位词扩展
    entities = _expand_with_broader(_extract_entities(text))

    # 分词token
    norm = _normalize(_expand_aliases(text))
    raw_parts = [part for part in norm.split() if len(part) >= 2 and part not in STOPWORDS]
    parts = list(dict.fromkeys(raw_parts))

    # 3字子串（有限，仅对≥4字的分词）
    substrings = []
    for part in parts:
        if len(part) <= 3:
            continue
        for idx in range(0, len(part) - 2):
            piece = part[idx : idx + 3]
            if piece not in STOPWORDS and len(piece) == 3:
                substrings.append(piece)

    return list(dict.fromkeys(entities + parts + substrings))


def _extract_question_keywords(text: str) -> list[str]:
    """从问题中提取用于匹配question字段的关键词。

    组合：实体词（含上位词扩展）+ alias展开后的分词。
    """
    entities = _expand_with_broader(_extract_entities(text))
    norm = _normalize(_expand_aliases(text))
    raw_parts = [part for part in norm.split() if len(part) >= 2 and part not in STOPWORDS]
    return list(dict.fromkeys(entities + raw_parts))


def _is_off_topic(question: str) -> bool:
    """判断问题是否明显与非遗无关。"""
    q = question.strip()
    # 含非遗产话题指示词且不含任何遗产相关词
    has_off_topic = any(indicator in q for indicator in OFF_TOPIC_INDICATORS)
    if has_off_topic and not _contains_any(_expand_aliases(q), HERITAGE_HINTS):
        return True
    # 完全不含任何遗产相关词且问题很短（≤6字）
    if len(q) <= 6 and not _contains_any(_expand_aliases(q), HERITAGE_HINTS):
        return True
    return False


def search_local_knowledge(db: Session, question: str) -> dict:
    """
    优先检索本地知识库（v3 优化版）:

    核心优化：
    1. question字段权重大幅提升（vs answer字段降权），
       避免answer自由文本中的偶然命中导致错配
    2. _extract_core_tokens 不再生成2字子串，消除垃圾token污染
    3. 非遗产话题硬拦截，"今天吃什么"等不再误命中
    4. 多候选时question命中优先，answer仅做辅助验证
    5. 交叉验证更严格：核心实体必须在question或keywords中出现
    """
    q = question.strip()

    # ── 非遗产话题硬拦截 ──
    if _is_off_topic(q):
        return {"matched": False, "answer": "", "confidence": 0.0, "source": "local_knowledge_base"}

    records = db.query(LocalKnowledgeBase).filter(LocalKnowledgeBase.status == "active").all()

    q_text = _expand_aliases(q)
    q_norm = _normalize(q_text)
    q_core_tokens = _extract_core_tokens(q)     # 核心+3字子串
    q_qkw = _extract_question_keywords(q)       # 问题关键词（严格，无子串）
    q_windows = []
    for i in range(0, max(len(q_norm) - 3, 0)):
        w = q_norm[i : i + 4].strip()
        if len(w) >= 3:   # 窗口从2→3，减少短窗口噪声
            q_windows.append(w)

    q_is_heritage = _contains_any(q_text, HERITAGE_HINTS)
    q_mentions_local_town = _contains_any(q_text, LOCAL_TOWN_HINTS)

    # ── 收集候选记录（≥12分）──
    candidates = []
    for record in records:
        rq = record.question or ""
        rk = record.keywords or ""
        ra = record.answer or ""
        rqa = record.qa_answer or ""

        rq_text = _expand_aliases(rq)
        rk_text = _expand_aliases(rk)
        ra_text = _expand_aliases(ra)
        rqa_text = _expand_aliases(rqa)
        record_text = f"{rq_text} {rk_text} {ra_text} {rqa_text}"

        record_mentions_local_town = _contains_any(record_text, LOCAL_TOWN_HINTS)
        record_is_heritage = _contains_any(record_text, HERITAGE_HINTS)

        if record_mentions_local_town and not q_mentions_local_town:
            continue
        if q_is_heritage and not record_is_heritage:
            continue

        rq_norm = _normalize(rq_text)
        rk_norm = _normalize(rk_text)
        ra_norm = _normalize(ra_text)
        rqa_norm = _normalize(rqa_text)

        score = 0
        for intent_word, mapped_words in INTENT_MAP.items():
            if intent_word in q:
                for mw in mapped_words:
                    if mw in rq_norm or mw in rk_norm:
                        score += 5
                        break
        if q_norm and rq_norm and q_norm == rq_norm:
            score += 50
        if q_norm and (q_norm in rq_norm or q_norm in rk_norm):
            score += 20
        if rq and rq.replace("请介绍：", "") in q:
            score += 12
        if rq_norm.startswith(q_norm[: min(len(q_norm), 6)]) and len(q_norm) >= 4:
            score += 8
        for kw in q_qkw:
            if kw in rq_norm:
                score += 8
            if kw in rk_norm:
                score += 6
        for token in q_core_tokens:
            if token in rq_norm:
                score += 4
            if token in rk_norm:
                score += 4
            if token in rqa_norm:
                score += 2
            if token in ra_norm:
                score += 1
        for w in q_windows:
            if w in rq_norm:
                score += 3
            if w in rk_norm:
                score += 2
        if q_is_heritage and record_is_heritage:
            score += 3
        qkw_hits_in_question = sum(1 for kw in q_qkw if kw in rq_norm)
        qkw_hits_in_keywords = sum(1 for kw in q_qkw if kw in rk_norm)
        if qkw_hits_in_question >= 2:
            score += 10
        elif qkw_hits_in_question == 1:
            score += 3
        if qkw_hits_in_keywords >= 2:
            score += 6
        if qkw_hits_in_question == 0 and qkw_hits_in_keywords == 0:
            answer_only_hits = sum(
                1
                for token in q_core_tokens
                if token in ra_norm or token in rqa_norm
            )
            if answer_only_hits > 0:
                score = score // 3
        if q_norm and q_norm not in rq_norm and q_norm not in rk_norm and q_norm not in rqa_norm:
            if qkw_hits_in_question == 0 and qkw_hits_in_keywords == 0:
                score = max(0, score - 6)

        if score >= 12:
            candidates.append((score, record))

    # 按分数降序排列
    candidates.sort(key=lambda x: -x[0])

    if not candidates:
        return {"matched": False, "answer": "", "confidence": 0.0, "source": "local_knowledge_base"}

    # ── 交叉验证：遍历候选，找到通过验证的最佳候选 ──
    _all_known_entities = set(HERITAGE_HINTS)
    for canonical, alias_list in ALIASES.items():
        _all_known_entities.add(canonical)
        _all_known_entities.update(alias_list)
    _TOO_GENERIC = {"非遗", "非物质文化遗产", "传统技艺", "戏曲", "民俗", "工艺", "传承"}
    q_entity_hits = [e for e in _all_known_entities if e in q_text and e not in _TOO_GENERIC]

    best_validated = None
    best_validated_score = 0

    for cand_score, cand_record in candidates:
        entity_in_qk = True
        entity_in_answer = True
        if q_entity_hits:
            cand_qk_norm = _normalize(_expand_aliases(
                f"{cand_record.question or ''} {cand_record.keywords or ''}"
            ))
            cand_answer = cand_record.qa_answer or cand_record.answer or ""
            cand_answer_norm = _normalize(_expand_aliases(cand_answer))
            entity_in_qk = any(e in cand_qk_norm for e in q_entity_hits)
            entity_in_answer = any(e in cand_answer_norm or e in cand_answer for e in q_entity_hits)
            if not entity_in_qk and not entity_in_answer:
                continue   # 交叉验证失败，跳过此候选
            if not entity_in_qk and entity_in_answer:
                cand_score = cand_score // 2   # 实体仅出现在answer中，降分
        # 验证通过
        if cand_score > best_validated_score:
            best_validated_score = cand_score
            best_validated = cand_record

    if not best_validated:
        return {"matched": False, "answer": "", "confidence": 0.0, "source": "local_knowledge_base"}

    best = best_validated
    best_score = best_validated_score
    best_answer = best.qa_answer or best.answer

    # ── 置信度：基于命中质量 ──
    rq_norm_check = _normalize(_expand_aliases(best.question or ""))
    rk_norm_check = _normalize(_expand_aliases(best.keywords or ""))
    q_norm_check = _normalize(_expand_aliases(q))

    # 检查question/keywords的关键词命中数
    _qkw = _extract_question_keywords(q)
    _qk_hits_in_q = sum(1 for kw in _qkw if kw in rq_norm_check)
    _qk_hits_in_k = sum(1 for kw in _qkw if kw in rk_norm_check)

    if q_norm_check and q_norm_check in rq_norm_check:
        confidence = 0.95   # 精确/包含命中question
    elif q_norm_check and q_norm_check in rk_norm_check:
        confidence = 0.90   # 关键词精确命中
    elif _qk_hits_in_q >= 2:
        confidence = 0.85   # 多关键词命中question（新增档位）
    elif best_score >= 30:
        confidence = 0.80   # 高分强匹配
    elif best_score >= 20:
        confidence = 0.65   # 中等匹配（新增档位，替代原来0.50）
    else:
        confidence = 0.50   # 弱匹配

    return {
        "matched": True,
        "answer": best_answer,
        "confidence": confidence,
        "source": best.source or "local_knowledge_base",
        "chapter": best.chapter or "",
        "sub_chapter": best.sub_chapter or "",
        "keywords": best.keywords or "",
    }

    return {"matched": False, "answer": "", "confidence": 0.0, "source": "local_knowledge_base", "chapter": "", "sub_chapter": "", "keywords": ""}
