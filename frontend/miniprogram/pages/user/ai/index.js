const { request } = require("../../../utils/request");
const digitalHuman = require("../../../utils/digital-human");

const DEFAULT_QUESTIONS = [
  "第一次接触非遗，适合先从什么体验项目开始？",
  "昆曲适合新手从哪里入门？",
  "云锦为什么会让人觉得工艺门槛很高？",
  "端午节为什么不只是吃粽子这么简单？",
  "古琴为什么常被看作适合静心聆听的艺术？",
  "非遗进校园为什么不是简单办活动？",
  "非遗和旅游融合为什么越来越常见？",
  "为什么很多非遗项目既强调保护也强调创新转化？",
  "二十四节气为什么和日常生活关系这么近？",
  "皮影戏为什么会被很多人认为特别有故事感？",
  "为什么非遗保护不能只靠展览？",
  "中国书法为什么也属于非遗范畴？",
  "苏绣和湘绣在风格上有什么不同？",
  "中医针灸为什么能入选联合国非遗名录？",
  "剪纸艺术为什么能流传这么久？",
  "太极拳作为非遗有什么特别的文化价值？",
  "侗族大歌为什么被称为无指挥合唱的奇迹？",
  "景德镇的制瓷工艺是怎么传承到今天的？",
  "京剧脸谱的颜色分别代表什么含义？",
  "川剧变脸到底是怎么做到的？"
];

/** 按CRS模式分层的推荐问题池 */
const CRS_MODE_QUESTIONS = {
  /* 冷启动阶段：广谱入门 + 4大类别引导（帮助快速积累对话分数） */
  cold_start: [
    "第一次接触非遗，从哪类开始比较容易上手？",
    "传统工艺类和戏曲音乐类，哪个更适合零基础体验？",
    "有什么适合周末去现场感受的非遗活动？",
    "非遗和普通手艺最大的区别在哪里？",
    "中国有多少项非遗被列入了联合国名录？",
    "皮影戏、木偶戏、布袋戏，这些有什么不同？",
    "二十四节气除了指导农事，还有什么文化意义？",
    "剪纸艺术为什么几乎每个地区都有不同风格？",
    "为什么说昆曲是'百戏之祖'？",
    "传统手工艺为什么值得现在重新关注？",
    "想带小朋友了解非遗，从哪个方向切入比较好？",
    "非遗传承人是怎么培养出来的？"
  ],
  /* 混合阶段：深入追问 + 跨类别探索 + 体验引导 */
  mixed: [
    "云锦和苏绣，哪种工艺更值得深入看？",
    "古琴和古筝在听感上有什么本质区别？",
    "京剧和昆曲的表演风格差异在哪？",
    "端午节在不同地区有什么不同的庆祝方式？",
    "非遗传承中'活态传承'是什么意思？",
    "有没有适合自己动手体验的非遗项目？",
    "中医里的经络理论和非遗有什么关系？",
    "花灯制作属于哪一类非遗？入门难度如何？",
    "非遗进校园活动一般会包含哪些内容？",
    "如果想系统地了解一个非遗类别，推荐什么顺序？",
    "非遗和乡村振兴是怎么结合的？",
    "现在最热门的非遗体验活动有哪些？"
  ],
  /* 精准阶段：深度话题 + 小众发现 + 行动导向 */
  precision: [
    "景德镇的柴窑和气窑烧出来的瓷器差别在哪？",
    "侗族大歌的演唱技巧为什么很难用乐谱记录？",
    "蜀锦的挑花结本工艺具体是怎么操作的？",
    "中医针灸和艾灸在传承路线上有什么不同？",
    "皮影戏的雕刻刀法对最终演出效果有多大影响？",
    "非遗文创产品为什么经常被说'不够原汁原味'？",
    "有哪些冷门但非常值得了解的非遗项目？",
    "非遗保护中的'生产性保护'是什么概念？",
    "如何判断一场非遗演出的质量好不好？",
    "数字化技术对非遗保护带来了什么改变？"
  ]
};

const KEYWORD_FOLLOWUP_MAP = [
  {
    keyword: "皮影",
    questions: [
      "皮影戏适合从哪些代表作品入门？",
      "现在哪里还能看到皮影戏现场表演？",
      "皮影戏和木偶戏有什么区别？",
      "如果想现场体验皮影戏，先看什么最容易入门？"
    ]
  },
  {
    keyword: "昆曲",
    questions: [
      "昆曲适合先听哪几段经典唱段？",
      "第一次看昆曲演出，最值得注意什么？",
      "昆曲和京剧在观演体验上有什么差别？",
      "如果想线下体验昆曲，应该优先选讲座还是演出？"
    ]
  },
  {
    keyword: "云锦",
    questions: [
      "云锦最值得先了解的工艺步骤是什么？",
      "云锦和普通织锦最大的区别在哪里？",
      "看云锦时怎样才算看懂门道？",
      "如果想深入了解云锦，可以先看内容还是先看展览？"
    ]
  },
  {
    keyword: "古琴",
    questions: [
      "古琴适合从哪些代表曲目开始听？",
      "古琴为什么会给人特别静心的感觉？",
      "古琴和古筝在听感上有什么差别？",
      "如果想体验古琴，先听讲解还是先听完整曲子更合适？"
    ]
  },
  {
    keyword: "端午",
    questions: [
      "除了吃粽子，端午还有哪些核心习俗值得了解？",
      "端午背后的文化象征可以怎么理解？",
      "端午习俗为什么会因地区不同而变化？",
      "如果想做端午主题活动，适合先选哪类体验项目？"
    ]
  },
  {
    keyword: "书法",
    questions: [
      "书法作为非遗，最适合从哪种字体开始认识？",
      "书法欣赏时可以先看哪些基本线索？",
      "书法为什么也被纳入非遗保护？",
      "如果是初学者，先看名作还是先了解工具更合适？"
    ]
  },
  {
    keyword: "苏绣",
    questions: [
      "苏绣和湘绣最大的风格差异在哪？",
      "苏绣的双面绣工艺为什么被认为是最难的？",
      "想近距离看苏绣作品，推荐去哪里？",
      "苏绣入门可以从哪些小件绣品开始了解？"
    ]
  },
  {
    keyword: "京剧",
    questions: [
      "京剧脸谱的颜色分别代表什么含义？",
      "京剧的四大行当分别有什么特点？",
      "第一次看京剧，选哪出戏最容易看进去？",
      "京剧的唱腔体系和其他戏曲有什么不同？"
    ]
  },
  {
    keyword: "中医",
    questions: [
      "中医针灸为什么能入选联合国非遗名录？",
      "中医的望闻问切和现代医学诊断有什么互补？",
      "有没有适合普通人体验的中医养生方法？",
      "中药材炮制工艺本身也是非遗吗？"
    ]
  },
  {
    keyword: "剪纸",
    questions: [
      "剪纸艺术为什么能流传这么久？",
      "中国南北方剪纸风格有什么明显不同？",
      "想学剪纸，从什么基本技法开始练？",
      "剪纸在现代设计中是怎么被应用的？"
    ]
  },
  {
    keyword: "陶瓷",
    questions: [
      "景德镇为什么被称为瓷都？",
      "青花瓷的制作流程包含哪些关键步骤？",
      "古代陶瓷工艺是怎么传承到今天的？",
      "现代陶艺和传统制瓷工艺最大的区别是什么？"
    ]
  },
  {
    keyword: "太极",
    questions: [
      "太极拳作为非遗有什么特别的文化价值？",
      "太极拳的不同流派之间差异大吗？",
      "太极的养生效果从现代科学角度怎么解释？",
      "学太极拳零基础可以从哪里开始？"
    ]
  },
  {
    keyword: "非遗",
    questions: [
      "非遗和普通传统文化项目有什么区别？",
      "中国目前有多少项世界级非遗？",
      "非遗传承人需要满足什么条件？",
      "为什么非遗保护越来越受到重视？"
    ]
  }
];

const RECOMMENDED_QUESTION_POOL = DEFAULT_QUESTIONS;
const AI_RECOMMEND_STATE_KEY = "ai_recommend_state";
const AI_COLDSTART_WELCOME_ONCE_KEY = "ai_coldstart_welcome_once";
const MAX_MESSAGES = 20;

function truncateMessages(list) {
  return (Array.isArray(list) ? list : []).slice(-MAX_MESSAGES);
}

function normalizeQuestion(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

function uniqueQuestions(list) {
  const seen = new Set();
  return (Array.isArray(list) ? list : []).filter((item) => {
    const normalized = normalizeQuestion(item);
    if (!normalized || seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}

function shortenPresetLabel(text) {
  const raw = normalizeQuestion(text);
  if (!raw) return "";
  const simplified = raw
    .replace(/^如果继续深入看/, "继续了解")
    .replace(/^围绕这个方向，?/, "围绕这个方向")
    .replace(/^围绕这个方向帮我推荐/, "围绕这个方向推荐")
    .replace(/，下一步建议是什么[？?]?$/, "怎么继续？")
    .replace(/适合先从哪些代表内容入门[？?]?$/, "怎么入门？")
    .replace(/有没有更适合线下体验的方式[？?]?$/, "怎么线下体验？")
    .replace(/和相关项目相比，最值得先了解什么[？?]?$/, "先看什么？")
    .replace(/应该优先选讲座还是演出[？?]?$/, "先看讲座还是演出？")
    .replace(/先听讲解还是先听完整曲子更合适[？?]?$/, "先听讲解还是整曲？")
    .replace(/点击查看详情/g, "查看详情");
  return simplified.length > 18 ? `${simplified.slice(0, 18)}…` : simplified;
}

function buildPresetItems(list) {
  return uniqueQuestions(list).map((text) => ({
    text: normalizeQuestion(text),
    display: shortenPresetLabel(text)
  }));
}

function isGenericDirectiveQuestion(text) {
  const q = normalizeQuestion(text);
  if (!q) return true;
  return [
    "围绕这个方向推荐相关内容",
    "围绕这个方向",
    "继续追问",
    "能再详细说说吗",
    "怎么继续？",
    "怎么线下体验？",
    "先看什么最合适？"
  ].some((item) => q === item || q.indexOf(item) !== -1);
}

function getLastMeaningfulUserQuestion(history) {
  const list = (history || [])
    .filter((item) => item && item.role === "user" && item.text)
    .map((item) => String(item.text).trim())
    .filter(Boolean);
  for (let i = list.length - 1; i >= 0; i -= 1) {
    if (!isGenericDirectiveQuestion(list[i])) {
      return list[i];
    }
  }
  return list[list.length - 1] || "";
}

function getMatchedKeyword(question) {
  const q = normalizeQuestion(question);
  if (!q) return "";
  const matched = KEYWORD_FOLLOWUP_MAP.find((item) => q.indexOf(item.keyword) !== -1);
  return matched ? matched.keyword : "";
}

function deriveFollowupAnchor({ question = "", kgEntity = "", history = [], cards = [] } = {}) {
  const entity = normalizeQuestion(kgEntity);
  if (entity) return entity;

  const directKeyword = getMatchedKeyword(question);
  if (directKeyword) return directKeyword;

  const lastMeaningful = getLastMeaningfulUserQuestion(history);
  const historyKeyword = getMatchedKeyword(lastMeaningful);
  if (historyKeyword) return historyKeyword;

  const heritageTerm = (cards || [])
    .map((item) => item && item.explain && item.explain.display && item.explain.display.heritageTerms)
    .find((list) => Array.isArray(list) && list.length);
  if (heritageTerm && heritageTerm[0]) return normalizeQuestion(heritageTerm[0]);

  return normalizeQuestion(lastMeaningful || question || "");
}

function buildGenericFollowups(topic) {
  const subject = normalizeQuestion(topic).replace(/[？?。！!，,]/g, "").slice(0, 10);
  if (!subject) return [];
  return [
    `${subject}怎么入门？`,
    `${subject}先看什么最合适？`,
    `${subject}怎么线下体验？`,
    `${subject}下一步怎么继续？`,
    `${subject}有哪些代表内容？`,
    `${subject}和相关项目有什么区别？`,
    `${subject}有没有值得参加的活动？`,
    `${subject}有哪些容易忽略的细节？`
  ];
}

function shuffle(array) {
  const list = array.slice();
  for (let i = list.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [list[i], list[j]] = [list[j], list[i]];
  }
  return list;
}

function cardUrl(card) {
  if (!card) return "";
  if (card.type === "content") return `/pages/user/content/detail/index?id=${card.id}`;
  if (card.type === "event") return `/pages/user/activity/detail/index?id=${card.id}`;
  if (card.type === "topic") return `/pages/user/discussion/detail/index?id=${card.id}`;
  return "";
}

function extractRecentQuestions(history) {
  const list = (history || [])
    .filter((item) => item && item.role === "user" && item.text)
    .map((item) => String(item.text).trim())
    .filter(Boolean);
  return list.reverse().filter((text, idx, arr) => arr.indexOf(text) === idx).slice(0, 3);
}

function buildRecommendSummaryState(profileSummary) {
  const summary = (profileSummary && (profileSummary.summary_text || ((profileSummary.sources || []).join(" · ")))) || "";
  const sources = (profileSummary && profileSummary.sources) || [];
  return {
    recommendSummary: summary,
    recommendSummaryBrief: summary ? "基于当前问答 + 历史偏好" : "",
    recommendSummaryExpanded: false,
    recommendSummarySources: sources
  };
}

function buildPersistedRecommendState(data) {
  return {
    recommendCards: data.recommendCards || [],
    actionTasks: data.actionTasks || [],
    dialogueStrategy: data.dialogueStrategy || "",
    strategyNote: data.strategyNote || "",
    strategyDisplay: data.strategyDisplay || "",
    recommendPrefix: data.recommendPrefix || "",
    recommendSummary: data.recommendSummary || "",
    recommendSummaryBrief: data.recommendSummaryBrief || "",
    recommendSummarySources: data.recommendSummarySources || [],
    fixedCta: data.fixedCta || { show: false, contentId: null, eventId: null },
    kgEntity: data.kgEntity || "",
    kgPathText: data.kgPathText || "",
    kgSimilarNames: data.kgSimilarNames || [],
    kgExpandItems: data.kgExpandItems || [],
    currentFollowupAnchor: data.currentFollowupAnchor || ""
  };
}

function loadPersistedRecommendState() {
  const state = wx.getStorageSync(AI_RECOMMEND_STATE_KEY) || {};
  return buildPersistedRecommendState(state);
}

function buildActionTask(card, idx) {
  const actionMap = {
    content: {
      title: "先读 1 篇相关入门内容",
      desc: card.title || "从内容线索开始继续了解"
    },
    event: {
      title: "看看这个活动是否值得报名",
      desc: card.title || "顺着活动线索继续体验"
    },
    topic: {
      title: "去社区看看大家怎么讨论",
      desc: card.title || "从讨论中补足更多视角"
    }
  };
  const fallback = actionMap[card.type] || {
    title: "继续沿着这条线索探索",
    desc: card.title || "推荐继续探索"
  };
  return {
    id: `${card.type}-${card.id}-${idx}`,
    title: fallback.title,
    type: card.type,
    desc: card.reason || fallback.desc,
    metaTitle: card.title || "",
    done: false,
    recommended: idx === 0
  };
}

function buildRecommendPrefix(cards, strategy) {
  if (!cards || !cards.length) return "";
  const types = cards.map((item) => item.type);
  if (strategy === "ask_clarify") {
    return "看起来你还在收窄方向，我先把最值得继续看的线索排出来。";
  }
  if (types.includes("content") && types.includes("event")) {
    return "因为你刚才的问题已经有明确方向，我先帮你补了内容和活动两条继续探索路线。";
  }
  if (types.includes("topic")) {
    return "除了直接回答，我也补了社区里的讨论线索，方便你继续顺着看。";
  }
  return "看起来你更像想找入门路径，所以我先给你排了一条继续探索路线。";
}

function detectFollowupQuestions(lastQuestion, backendSuggestions) {
  const backend = uniqueQuestions(backendSuggestions || []);
  const question = normalizeQuestion(lastQuestion);
  const matched = KEYWORD_FOLLOWUP_MAP.find((item) => question.indexOf(item.keyword) !== -1);
  const keywordQuestions = matched ? uniqueQuestions(matched.questions || []) : [];
  const genericQuestions = buildGenericFollowups(question);

  if (backend.length) return backend.slice(0, 8);
  if (keywordQuestions.length) return keywordQuestions.slice(0, 8);
  if (question) return genericQuestions.slice(0, 8);
  return [];
}

function formatScore(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "0.00";
  return num.toFixed(2);
}

function cleanStringList(list) {
  return (Array.isArray(list) ? list : [])
    .map((item) => String(item || "").trim())
    .filter(Boolean);
}

function humanizeRelationText(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const map = {
    belongs_to: "属于同一非遗类别",
    "belongs to": "属于同一非遗类别",
    similar_to: "和你刚关注的方向相近",
    related_to: "和你刚提到的主题有关联",
    same_theme: "和当前主题一致"
  };
  return map[raw] || raw.replace(/_/g, " ");
}

function formatMatchDetailText(detail) {
  if (!detail || typeof detail !== "object") return "";
  const labelMap = {
    heritage: "主题相关",
    entity_recall: "实体命中",
    scene_weight: "场景匹配",
    quality: "内容质量",
    featured: "精选加权",
    novelty: "新鲜度",
    diversity_penalty: "重复惩罚"
  };
  const parts = Object.entries(detail)
    .map(([key, val]) => {
      const num = Number(val);
      if (!Number.isFinite(num)) return "";
      return `${labelMap[key] || key} ${formatScore(num)}`;
    })
    .filter(Boolean);
  return parts.join(" · ");
}

function normalizeRecommendExplain(explain) {
  const raw = explain || {};
  const strategyContext = raw.strategy_context || {};
  const kgContext = raw.kg_context || {};
  const sources = cleanStringList(strategyContext.sources);
  const heritageTerms = cleanStringList(strategyContext.heritage_terms);
  const similarEntities = cleanStringList(kgContext.similar_entities);
  const expandPath = String(kgContext.expand_path || raw.kg_path_text || "").trim();
  const kgReasonText = humanizeRelationText(kgContext.kg_reason || raw.kg_reason || "");
  const matchDetailText = formatMatchDetailText(raw.match_detail);

  return {
    ...raw,
    match_score_text: formatScore(raw.match_score),
    novelty_score_text: formatScore(raw.novelty_score),
    diversity_penalty_text: formatScore(raw.diversity_penalty),
    final_score_text: formatScore(raw.final_score),
    kg_score_text: formatScore(raw.kg_score),
    display: {
      matchDetailText,
      sources,
      heritageTerms,
      similarEntities,
      expandPath,
      kgReasonText
    }
  };
}

/** CRS模式 → 黑塔表情映射 */
function crsModeToMood(mode) {
  if (mode === "precision") return "confident";
  if (mode === "mixed") return "thinking";
  return "curious";
}

function _processRecommendPayload(payload) {
  const cards = (payload.recommend_cards || []).map((card) => ({
    ...card,
    explain: normalizeRecommendExplain(card.explain || {})
  }));
  const roundStrategyLabel = payload.strategy_display || (payload.strategy === 'precision' ? '精准推荐' : payload.strategy === 'mixed' ? '推荐+追问' : payload.strategy === 'intent_driven_rec' ? '主动推荐' : '智能推荐');
  const normalizedCards = cards.map((card) => ({
    ...card,
    explain: { ...(card.explain || {}), crs_mode_label: roundStrategyLabel }
  }));
  const recommendPayload = payload.recommend_payload || {};
  const summaryState = buildRecommendSummaryState(recommendPayload.profile_summary);
  const tasks = normalizedCards.slice(0, 3).map((card, idx) => buildActionTask(card, idx));
  const contentCard = normalizedCards.find((x) => x.type === "content");
  const eventCard = normalizedCards.find((x) => x.type === "event");
  const kgSimilarItems = (payload.kg_similar && payload.kg_similar.items) || [];
  const kgExpandItems = (payload.kg_expand && payload.kg_expand.items) || [];
  const kgPath = (payload.kg_path && payload.kg_path.path) || [];
  const kgPathText = kgPath
    .map((step) => (step.entity ? step.entity : step.relation ? `[${step.relation}]` : ""))
    .filter(Boolean)
    .join(" → ");
  const duplicatePath = (normalizedCards || []).some((item) => {
    const exp = item.explain || {};
    return exp.kg_path_text && kgPathText && exp.kg_path_text === kgPathText;
  });
  return {
    normalizedCards,
    tasks,
    summaryState,
    fixedCta: {
      show: !!(contentCard || eventCard),
      contentId: contentCard ? contentCard.id : null,
      eventId: eventCard ? eventCard.id : null
    },
    kgEntity: payload.kg_entity || "",
    kgPathText: duplicatePath ? "" : kgPathText,
    kgSimilarNames: kgSimilarItems.map((item) => item.entity).filter(Boolean).slice(0, 3),
    kgExpandItems: kgExpandItems.slice(0, 3),
    strategyDisplay: payload.strategy_display || "",
    dialogueStrategy: payload.strategy || "knowledge_answer",
    strategyNote: payload.strategy_note || "",
    recommendPrefix: payload.recommend_prefix || buildRecommendPrefix(cards, payload.strategy || "knowledge_answer")
  };
}

Page({
  behaviors: [digitalHuman],

  data: {
    question: "",
    sending: false,
    messages: [],
    typingIndex: -1,
    sourceTag: "",
    webSearching: false,
    waitingTip: "",
    rewriteSuggestions: [],
    recommendCards: [],
    explainExpandedMap: {},
    feedbackMap: {},
    actionTasks: [],
    dialogueStrategy: "",
    strategyNote: "",
    strategyDisplay: "",
    askPrompt: "",
    askOptions: [],
    askId: "",
    askAttribute: "",
    crsMode: "cold_start",
    crsConfidence: 0,
    crsConfidenceRaw: 0,
    crsSessionId: "",
    crsDimensions: {},
    crsDetailExpanded: false,
    askTimeline: [],   /* CRS决策时间线 */
    digitalHumanMood: "curious",
    scrollTop: 0,   /* scroll-top 自动滚底 */
    _scrollCounter: 0,
    modeCelebrating: false,
    celebrationMode: "",
    celebrationFading: false,
    fixedCta: {
      show: false,
      contentId: null,
      eventId: null
    },
    presets: [],
    presetMode: "default",
    presetTitle: "推荐发问",
    recentQuestions: [],
    recommendPrefix: "",
    selectedAskOption: "",
    recommendSummary: "",
    recommendSummaryBrief: "",
    recommendSummaryExpanded: false,
    recommendSummarySources: [],
    kgEntity: "",
    kgPathText: "",
    kgSimilarNames: [],
    kgExpandItems: [],
    currentFollowupAnchor: ""
  },

  syncDigitalHumanStage() {
    const speaking = this.data.digitalHumanSpeaking;
    const expanded = this.data.digitalHumanExpanded;
    const scene = this.data.digitalHumanScene || "ai";
    let bubble;
    if (speaking) {
      bubble = "正在讲解。";
    } else if (expanded) {
      bubble = "有问题随时问。";
    } else {
      bubble = "不懂就问。";
    }
    const visualState = speaking ? "speaking" : expanded ? "open" : "idle";
    this.setData({
      digitalHumanMood: crsModeToMood(this.data.crsMode),
      digitalHumanBubble: bubble,
      digitalHumanVisualState: visualState
    });
  },

  /** 滚动对话到底部 */
  _scrollChatToBottom() {
    const counter = (this.data._scrollCounter || 0) + 1;
    this.setData({ scrollTop: counter * 10000, _scrollCounter: counter });
  },

  onShow() {
    const history = wx.getStorageSync("ai_chat_history") || [];
    const session = wx.getStorageSync("session") || {};
    const persistedRecommendState = loadPersistedRecommendState();
    const lastUserQuestion = getLastMeaningfulUserQuestion(history) || "";
    this.setData({
      messages: truncateMessages(history),
      typingIndex: -1,
      sourceTag: this.data.sourceTag || "",
      rewriteSuggestions: this.data.rewriteSuggestions || [],
      recommendCards: (this.data.recommendCards && this.data.recommendCards.length ? this.data.recommendCards : persistedRecommendState.recommendCards) || [],
      actionTasks: (this.data.actionTasks && this.data.actionTasks.length ? this.data.actionTasks : persistedRecommendState.actionTasks) || [],
      dialogueStrategy: this.data.dialogueStrategy || persistedRecommendState.dialogueStrategy || "",
      strategyNote: this.data.strategyNote || persistedRecommendState.strategyNote || "",
      strategyDisplay: this.data.strategyDisplay || persistedRecommendState.strategyDisplay || "",
      askPrompt: this.data.askPrompt || "",
      askOptions: this.data.askOptions || [],
      askId: this.data.askId || "",
      askAttribute: this.data.askAttribute || "",
      feedbackMap: this.data.feedbackMap || {},
      crsMode: this.data.crsMode || "cold_start",
      crsConfidence: this.data.crsConfidence || 0,
      crsConfidenceRaw: this.data.crsConfidenceRaw || 0,
      crsSessionId: this.data.crsSessionId || "",
      crsDimensions: this.data.crsDimensions || {},
      digitalHumanMood: crsModeToMood(this.data.crsMode),
      fixedCta: this.data.fixedCta && this.data.fixedCta.show ? this.data.fixedCta : persistedRecommendState.fixedCta,
      recentQuestions: extractRecentQuestions(history),
      presetMode: history.length ? "followup" : "default",
      presetTitle: history.length ? "↳ 继续探索" : "推荐发问",
      recommendPrefix: this.data.recommendPrefix || persistedRecommendState.recommendPrefix || "",
      selectedAskOption: this.data.selectedAskOption || "",
      recommendSummary: this.data.recommendSummary || persistedRecommendState.recommendSummary || "",
      recommendSummaryBrief: this.data.recommendSummaryBrief || persistedRecommendState.recommendSummaryBrief || "",
      recommendSummaryExpanded: false,
      recommendSummarySources: (this.data.recommendSummarySources && this.data.recommendSummarySources.length ? this.data.recommendSummarySources : persistedRecommendState.recommendSummarySources) || [],
      kgEntity: this.data.kgEntity || persistedRecommendState.kgEntity || "",
      kgPathText: this.data.kgPathText || persistedRecommendState.kgPathText || "",
      kgSimilarNames: (this.data.kgSimilarNames && this.data.kgSimilarNames.length ? this.data.kgSimilarNames : persistedRecommendState.kgSimilarNames) || [],
      kgExpandItems: (this.data.kgExpandItems && this.data.kgExpandItems.length ? this.data.kgExpandItems : persistedRecommendState.kgExpandItems) || [],
      currentFollowupAnchor: this.data.currentFollowupAnchor || persistedRecommendState.currentFollowupAnchor || "",
      digitalHumanLiveCaption: "",
      digitalHumanCaptionVisible: false,
      digitalHumanCaptionProgress: 0
    });
    this.refreshPresets(true, { history, lastUserQuestion });
    this.initDigitalHuman("ai");
    this._loadCrsState();
    // 加载历史后滚到底部
    if (history.length) {
      setTimeout(() => this._scrollChatToBottom(), 100);
    }
  },

  async _loadCrsState() {
    const session = wx.getStorageSync("session") || {};
    if (!session.userId) return;
    try {
      const res = await request({
        url: "/ai/crs/state",
        method: "GET",
        data: { user_id: session.userId }
      });
      const data = (res && res.data) || {};
      const mode = data.mode || "cold_start";
      const confidence = data.stage_progress_percent || 0;
      const confidenceRaw = data.confidence_score_raw || data.confidence_score || 0;
      const turnCount = data.turn_count || 0;
      const lastAskAttr = data.last_ask_attribute || "";
      this.setData({
        crsMode: mode,
        crsConfidence: confidence,
        crsConfidenceRaw: confidenceRaw,
        crsSessionId: data.session_id || "",
        crsDimensions: data.dimensions || {},
        askTimeline: data.ask_timeline || [],
        digitalHumanMood: crsModeToMood(mode)
      });
      // 同步CRS模式到全局，FAB黑塔可读取
      const app = getApp();
      if (app && app.globalData) { app.globalData.crsMode = mode; }

      // 冷启动 + 无历史对话 → 自动触发首个ASK
      const history = this.data.messages || [];
      if (mode === "cold_start" && !history.length && turnCount === 0) {
        this._triggerColdStartAsk(data.session_id);
      }

      // 高模式但无推荐卡 → 静默补拉一次推荐区
      if ((mode === "mixed" || mode === "precision") && !(this.data.recommendCards || []).length) {
        this._ensureRecommendCardsFromState();
      }
    } catch (e) {
      // 静默失败，不影响页面
    }
  },

  async _ensureRecommendCardsFromState() {
    if (this.data.sending || this._recoveringRecommendCards) return;
    const session = wx.getStorageSync("session") || {};
    if (!session.userId) return;

    this._recoveringRecommendCards = true;
    try {
      const res = await request({
        url: "/ai/crs/state",
        method: "GET",
        data: { user_id: session.userId }
      });
      const data = (res && res.data) || {};
      const cards = (data.recommend_cards || []).map((card) => {
        const normalized = normalizeRecommendExplain(card.explain || {});
        return { ...card, explain: normalized };
      });
      if (!cards.length) return;

      const tasks = cards.slice(0, 3).map((card, idx) => buildActionTask(card, idx));
      const contentCard = cards.find((x) => x.type === "content");
      const eventCard = cards.find((x) => x.type === "event");
      this.setData({
        recommendCards: cards,
        actionTasks: tasks,
        fixedCta: {
          show: !!(contentCard || eventCard),
          contentId: contentCard ? contentCard.id : null,
          eventId: eventCard ? eventCard.id : null
        }
      });
      wx.setStorageSync(AI_RECOMMEND_STATE_KEY, buildPersistedRecommendState({
        ...this.data,
        recommendCards: cards,
        actionTasks: tasks,
        fixedCta: {
          show: !!(contentCard || eventCard),
          contentId: contentCard ? contentCard.id : null,
          eventId: eventCard ? eventCard.id : null
        }
      }));
    } catch (e) {
    } finally {
      this._recoveringRecommendCards = false;
    }
  },

  _triggerColdStartAsk(sessionId) {
    // 冷启动首次进入：自动弹出第一个ASK（A01 - 类目选择）
    const A01 = {
      attribute: "category",
      prompt: "你最想了解哪类非物质文化遗产？",
      options: ["传统工艺", "戏曲音乐", "民俗节俗", "饮食医药"]
    };
    this.setData({
      askPrompt: A01.prompt,
      askOptions: A01.options,
      askId: "A01",
      askAttribute: A01.attribute,
      dialogueStrategy: "cold_start_ask",
      strategyNote: "黑塔先了解你的兴趣方向，再缩小推荐范围。"
    });
    const session = wx.getStorageSync("session") || {};
    const onceKey = `${AI_COLDSTART_WELCOME_ONCE_KEY}_${session.userId || 'guest'}`;
    const greeted = wx.getStorageSync(onceKey);
    if (!greeted && this.narrateDigitalHumanText) {
      this.narrateDigitalHumanText("你好，我是黑塔。让我先了解一下你最感兴趣的方向吧。" + A01.prompt);
      wx.setStorageSync(onceKey, true);
    }
  },

  onHide() {
    this.clearTypingTimer(false);
    this.stopDigitalHumanCaptionTimer();
    if (this.digitalHumanAudio) {
      try {
        this.digitalHumanAudio.stop();
      } catch (e) {}
    }
    this.setData({
      digitalHumanSpeaking: false,
      digitalHumanCaptionVisible: false,
      digitalHumanLiveCaption: "",
      digitalHumanCaptionProgress: 0
    });
  },

  onUnload() {
    this.clearTypingTimer(false);
    this.stopDigitalHumanCaptionTimer();
    clearTimeout(this._celebrationTimer);
    if (this.digitalHumanAudio) {
      try { this.digitalHumanAudio.destroy(); } catch (e) {}
      this.digitalHumanAudio = null;
    }
  },

  askRandomPreset() {
    const presets = this.data.presets || [];
    if (!presets.length) return;
    const random = presets[Math.floor(Math.random() * presets.length)];
    this.sendQuestion(random.text || random);
  },

  focusQuestionInput() {
    this.setData({ question: "" });
  },

  onQuestionInput(e) {
    this.setData({ question: e.detail.value || "" });
  },

  usePreset(e) {
    const text = e.currentTarget.dataset.text || "";
    if (!text) return;
    this.setData({ question: text });
    this.sendQuestion();
  },

  refreshPresets(forceShuffle = false, options = {}) {
    const history = options.history || this.data.messages || [];
    const lastUserQuestion = options.lastUserQuestion || getLastMeaningfulUserQuestion(history) || "";
    const followupAnchor = normalizeQuestion(options.followupAnchor || this.data.currentFollowupAnchor || lastUserQuestion || "");
    const backendFollowups = uniqueQuestions(options.backendFollowups || []);
    const matched = KEYWORD_FOLLOWUP_MAP.find((item) => followupAnchor.indexOf(item.keyword) !== -1);
    const keywordFollowups = matched ? uniqueQuestions(matched.questions || []) : [];
    const meaningfulQuestionFollowups = followupAnchor ? buildGenericFollowups(followupAnchor) : [];
    const fallbackModePool = CRS_MODE_QUESTIONS[this.data.crsMode || "cold_start"] || CRS_MODE_QUESTIONS.cold_start;
    const followupSource = backendFollowups.length
      ? backendFollowups
      : keywordFollowups.length
        ? keywordFollowups
        : meaningfulQuestionFollowups.length
          ? meaningfulQuestionFollowups
          : fallbackModePool;
    const useFollowup = !!(history && history.length && followupSource && followupSource.length);

    /* 按CRS模式选择基础问题池 */
    const crsMode = this.data.crsMode || "cold_start";
    const modePool = CRS_MODE_QUESTIONS[crsMode] || CRS_MODE_QUESTIONS.cold_start;
    const pool = (useFollowup ? followupSource : modePool).slice();

    const cacheKey = useFollowup ? "ai_followup_question_state" : "ai_recommended_question_state";
    const state = wx.getStorageSync(cacheKey) || {};
    const current = (this.data.presets || []).map((item) => item.text || item);
    const recentlyUsed = Array.isArray(state.recentlyUsed) ? state.recentlyUsed.slice() : [];
    let queue = Array.isArray(state.queue) ? state.queue.slice() : [];

    const invalidQueue = !queue.length || queue.some((item) => !pool.includes(item));
    if (forceShuffle || invalidQueue) {
      queue = shuffle(pool.filter((item) => !recentlyUsed.includes(item)));
      if (!queue.length) queue = shuffle(pool);
    }

    let nextBatch = queue.slice(0, 4);
    queue = queue.slice(nextBatch.length);

    if (nextBatch.length < 4) {
      const refill = shuffle(pool.filter((item) => !nextBatch.includes(item) && !recentlyUsed.includes(item)));
      nextBatch = nextBatch.concat(refill.slice(0, 4 - nextBatch.length));
      queue = queue.concat(refill.slice(Math.max(0, 4 - nextBatch.length)));
    }

    if (nextBatch.length < 4) {
      const fallbackPool = shuffle(pool.filter((item) => !nextBatch.includes(item)));
      nextBatch = nextBatch.concat(fallbackPool.slice(0, 4 - nextBatch.length));
    }

    if (current.length && nextBatch.join("|") === current.join("|")) {
      const fallback = shuffle(pool.filter((item) => !current.includes(item) && !recentlyUsed.includes(item))).slice(0, 4);
      if (fallback.length) nextBatch = fallback;
    }

    const nextRecentlyUsed = uniqueQuestions([...(recentlyUsed || []), ...nextBatch]).slice(-8);
    const presetItems = buildPresetItems(nextBatch);

    this.setData({
      presets: presetItems,
      presetMode: useFollowup ? "followup" : "default",
      presetTitle: useFollowup ? "继续探索" : (options.isCrsRecommended ? "黑塔推荐" : "推荐发问")
    });
    wx.setStorageSync(cacheKey, { queue, recentlyUsed: nextRecentlyUsed });
  },

  refreshPresetQuestions() {
    // v2.1: 换一批时记录跳过信号，让后端知道用户对当前预设问题不感兴趣
    const session = wx.getStorageSync("session") || {};
    if (session.userId) {
      request({
        url: "/recommend/track",
        method: "POST",
        data: {
          user_id: session.userId,
          action: "expose",
          target_type: "topic",
          target_id: 0,
          source_scene: "ai_preset_skip"
        }
      }).catch(() => {});
    }
    this.refreshPresets(false);
  },

  async askPreset(e) {
    const text = e.currentTarget.dataset.text || "";
    if (!text || this.data.sending) return;
    await this.sendQuestion(text);
  },

  async sendQuestion(overrideQuestion) {
    const payloadInput = (overrideQuestion && typeof overrideQuestion === "object" && !overrideQuestion.detail)
      ? overrideQuestion
      : null;
    const candidate = typeof overrideQuestion === "string"
      ? overrideQuestion
      : payloadInput && typeof payloadInput.text === "string"
        ? payloadInput.text
        : (overrideQuestion && overrideQuestion.detail && typeof overrideQuestion.detail.value === "string")
          ? overrideQuestion.detail.value
          : this.data.question;
    const followupAnchor = normalizeQuestion((payloadInput && payloadInput.followupAnchor) || "");
    const q = String(candidate || "").trim();
    if (!q || this.data.sending) return;
    const session = wx.getStorageSync("session") || {};

    // 追问前保存当前推荐卡片（等新数据覆盖，不再清空，保留上下文连贯性）
    const prevCards = this.data.recommendCards || [];

    const nextMessages = this.data.messages.concat([{ role: "user", text: q, _id: "u" + Date.now() }]);
    const userMsgId = nextMessages[nextMessages.length - 1]._id;
    this.setData({
      sending: true,
      question: "",
      messages: nextMessages,
      webSearching: false,
      waitingTip: "正在整理本地知识库回答...",
      sourceTag: "",
      rewriteSuggestions: [],
      // v2.1: 不再清空recommendCards，等新数据覆盖，保留追问上下文
      // recommendCards: [],  // 删除这行
      actionTasks: [],
      dialogueStrategy: "",
      strategyNote: "",
      askPrompt: "",
      askOptions: [],
      recommendSummary: "",
      recommendSummaryBrief: "",
      recommendSummaryExpanded: false,
      recommendSummarySources: [],
      fixedCta: { show: false, contentId: null, eventId: null }
    });
    wx.setStorageSync("ai_chat_history", truncateMessages(nextMessages));
    this._scrollChatToBottom();

    const waitingTimer = setTimeout(() => {
      if (this.data.sending) {
        this.setData({
          webSearching: true,
          waitingTip: "黑塔正在思考中，稍等一下..."
        });
      }
    }, 1500);

    try {
      const res = await request({
        url: "/ai/chat",
        method: "POST",
        timeout: 60000,
        data: {
          question: q,
          user_id: session.userId || null,
          context_cards: prevCards.length > 0 ? prevCards : undefined
        }
      });
      const payload = (res && res.data) || {};
      const answer = payload.answer || "未获取到回答";
      const source = payload.source || "";
      const sourceTagMap = {
        local_kb: "本地知识库",
        kb_enhanced: "知识库+AI润色",
        web_search: "联网补充",
        web_enhanced: "联网+AI总结",
        doubao: "AI模型",
        fallback: "兜底回复"
      };
      const withAnswer = nextMessages.concat([{ role: "ai", text: answer, _id: "a" + Date.now() }]);
      const aiMsgId = withAnswer[withAnswer.length - 1]._id;
      const rec = _processRecommendPayload(payload);
      const recentQuestions = extractRecentQuestions(nextMessages);
      const recommendedQuestions = uniqueQuestions(payload.recommended_questions || []);
      const followupQuestions = recommendedQuestions.length
        ? recommendedQuestions
        : detectFollowupQuestions(q, payload.followup_questions || []);
      const nextFollowupAnchor = deriveFollowupAnchor({
        question: followupAnchor || q,
        kgEntity: rec.kgEntity,
        history: withAnswer,
        cards: rec.normalizedCards
      });
      const crsConfidence = payload.crs_confidence || {};
      const oldCrsMode = this.data.crsMode;
      const newCrsMode = payload.crs_mode || crsConfidence.mode || "cold_start";
      this.setData({
        messages: truncateMessages(withAnswer),
        typingIndex: -1,
        sourceTag: sourceTagMap[source] || "智能回答",
        webSearching: !!payload.searching_web,
        rewriteSuggestions: payload.rewrite_suggestions || [],
        recommendCards: rec.normalizedCards,
        recommendPrefix: rec.recommendPrefix,
        actionTasks: rec.tasks,
        explainExpandedMap: {},
        dialogueStrategy: rec.dialogueStrategy,
        strategyNote: rec.strategyNote,
        strategyDisplay: rec.strategyDisplay,
        askPrompt: payload.ask_prompt || "",
        askOptions: payload.ask_options || [],
        askId: payload.ask_id || "",
        askAttribute: payload.ask_attribute || "",
        crsMode: newCrsMode,
        crsConfidence: crsConfidence.confidence_score || 0,
        crsSessionId: payload.crs_session_id || "",
        crsDimensions: crsConfidence.dimensions || {},
        digitalHumanMood: crsModeToMood(newCrsMode),
        selectedAskOption: "",
        kgEntity: rec.kgEntity,
        kgPathText: rec.kgPathText,
        kgSimilarNames: rec.kgSimilarNames,
        kgExpandItems: rec.kgExpandItems,
        currentFollowupAnchor: nextFollowupAnchor,
        recentQuestions,
        ...rec.summaryState,
        fixedCta: rec.fixedCta
      });
      wx.setStorageSync(AI_RECOMMEND_STATE_KEY, buildPersistedRecommendState({
        ...this.data,
        recommendCards: rec.normalizedCards,
        actionTasks: rec.tasks,
        dialogueStrategy: rec.dialogueStrategy,
        strategyNote: rec.strategyNote,
        strategyDisplay: rec.strategyDisplay,
        recommendPrefix: rec.recommendPrefix,
        ...rec.summaryState,
        fixedCta: rec.fixedCta,
        kgEntity: rec.kgEntity,
        kgPathText: rec.kgPathText,
        kgSimilarNames: rec.kgSimilarNames,
        kgExpandItems: rec.kgExpandItems,
        currentFollowupAnchor: nextFollowupAnchor
      }));
      this._scrollChatToBottom();
      // 同步CRS模式到全局
      const _app = getApp();
      if (_app && _app.globalData) { _app.globalData.crsMode = newCrsMode; }
      // CRS v2.0.7：流式响应中也检测模式升级
      if (oldCrsMode !== newCrsMode) {
        this._triggerModeCelebration(newCrsMode);
        if (this.narrateDigitalHumanText) {
          const modeMsg = {
            mixed: "黑塔已经初步了解你的偏好了，接下来会边推荐边追问。",
            precision: "黑塔已经比较了解你了，接下来直接推荐最匹配你的内容！"
          };
          if (modeMsg[newCrsMode]) {
            setTimeout(() => this.narrateDigitalHumanText(modeMsg[newCrsMode]), 1500);
          }
        }
      }
      this.refreshPresets(true, {
        history: withAnswer,
        lastUserQuestion: q,
        followupAnchor: nextFollowupAnchor,
        followupQuestions,
        backendFollowups: payload.followup_questions || [],
        isCrsRecommended: !!(payload.recommended_questions && payload.recommended_questions.length)
      });
      wx.setStorageSync("ai_chat_history", truncateMessages(withAnswer));
      if (this.narrateDigitalHumanText) this.narrateDigitalHumanText(answer);
    } catch (e) {
      wx.showToast({ title: "提问失败", icon: "none" });
    } finally {
      clearTimeout(waitingTimer);
      this.setData({ sending: false, waitingTip: "" });
    }
  },

  applySuggestion(e) {
    const text = e.currentTarget.dataset.text || "";
    if (!text) return;
    const followupAnchor = text.indexOf("围绕这个方向") !== -1
      ? deriveFollowupAnchor({
          kgEntity: this.data.kgEntity,
          history: this.data.messages,
          cards: this.data.recommendCards
        })
      : "";
    this.sendQuestion({ text, followupAnchor });
  },

  toggleCrsDetail() {
    this.setData({ crsDetailExpanded: !this.data.crsDetailExpanded });
  },

  async applyAskOption(e) {
    const text = e.currentTarget.dataset.text || "";
    if (!text || this.data.sending) return;
    const askId = this.data.askId || "";
    const sessionId = this.data.crsSessionId || "";
    const session = wx.getStorageSync("session") || {};

    // 先把用户选择作为用户消息展示，避免黑塔回复排在前面
    const userMsgId = "u_ask_" + Date.now();
    const baseMessages = (this.data.messages || []).slice();
    baseMessages.push({ _id: userMsgId, role: "user", text: text });
    this.setData({
      sending: true,
      messages: truncateMessages(baseMessages),
      selectedAskOption: text,
      question: "",
      askId: "",
      askPrompt: "",
      askOptions: []
    });
    this._scrollChatToBottom();

    // CRS v2.0.6：语音确认选择
    if (this.narrateDigitalHumanText) {
      this.narrateDigitalHumanText("好的，你选了" + text);
    }

    // CRS v2.0：调后端提交ASK回答 → 更新偏好+置信度
    if (askId && sessionId && session.userId) {
      try {
        const res = await request({
          url: "/ai/crs/answer",
          method: "POST",
          data: {
            user_id: session.userId,
            session_id: sessionId,
            ask_id: askId,
            answer: text
          }
        });
        const data = (res && res.data) || {};
        this._lastCrsAnswerData = data;
        const oldMode = this.data.crsMode;
        const newMode = data.mode || this.data.crsMode;
        const askRec = _processRecommendPayload(data);
        this.setData({
          crsMode: newMode,
          crsConfidence: data.confidence_score || this.data.crsConfidence,
          crsDimensions: data.dimensions || this.data.crsDimensions,
          askTimeline: data.ask_timeline || this.data.askTimeline,
          digitalHumanMood: crsModeToMood(newMode),
          recommendCards: askRec.normalizedCards.length ? askRec.normalizedCards : this.data.recommendCards,
          recommendPrefix: askRec.normalizedCards.length ? askRec.recommendPrefix : this.data.recommendPrefix,
          actionTasks: askRec.normalizedCards.length ? askRec.tasks : this.data.actionTasks,
          strategyDisplay: askRec.strategyDisplay || this.data.strategyDisplay,
          dialogueStrategy: askRec.dialogueStrategy || this.data.dialogueStrategy,
          fixedCta: askRec.normalizedCards.length ? askRec.fixedCta : this.data.fixedCta
        });
        if (askRec.normalizedCards.length) {
          wx.setStorageSync(AI_RECOMMEND_STATE_KEY, buildPersistedRecommendState({
            ...this.data,
            recommendCards: askRec.normalizedCards,
            recommendPrefix: askRec.recommendPrefix,
            actionTasks: askRec.tasks,
            strategyDisplay: askRec.strategyDisplay || this.data.strategyDisplay,
            dialogueStrategy: askRec.dialogueStrategy || this.data.dialogueStrategy,
            fixedCta: askRec.fixedCta
          }));
        }
        // 过渡语：黑塔对ASK回答给出自然反馈
        const transitionMsg = data.transition_msg || "";
        if (transitionMsg) {
          const msgs = (this.data.messages || []).slice();
          const transId = "trans_" + Date.now();
          msgs.push({ _id: transId, role: "ai", text: transitionMsg, isTransition: true });
          this.setData({ messages: truncateMessages(msgs) });
          this._scrollChatToBottom();
        }
        // 同步CRS模式到全局
        const __app = getApp();
        if (__app && __app.globalData) { __app.globalData.crsMode = newMode; }
        // CRS v2.0.6：模式升级语音播报 + v2.0.7庆祝动效
        if (oldMode !== newMode) {
          this._triggerModeCelebration(newMode);
          if (this.narrateDigitalHumanText) {
            const modeMsg = {
              mixed: "黑塔已经初步了解你的偏好了，接下来会边推荐边追问，帮你找到更精准的方向。",
              precision: "黑塔已经比较了解你了，接下来直接推荐最匹配你的内容！"
            };
            if (modeMsg[newMode]) {
              setTimeout(() => this.narrateDigitalHumanText(modeMsg[newMode]), 1500);
            }
          }
        }
      } catch (e) {
        // 静默失败，继续走问答流程
      }
    }

    // v2.1优化：如果CRS answer已经返回了推荐卡片，不再调sendQuestion避免重复豆包调用
    // 只有当CRS answer没有返回推荐卡片时才需要sendQuestion生成AI回答
    const crsData = (this._lastCrsAnswerData) || {};
    const hasCrsCards = (crsData.recommend_cards || []).length > 0;
    const hasCrsTransition = !!(crsData.transition_msg || "");
    const msgs = this.data.messages || [];

    if (hasCrsCards && hasCrsTransition) {
      this.setData({ sending: false });
      this.refreshPresets(true, { history: msgs });
    } else {
      // 没有完整CRS响应，需要调AI生成回答
      setTimeout(() => {
        this.sendQuestion(text);
      }, 300);
    }
  },

  useRecentQuestion(e) {
    const text = e.currentTarget.dataset.text || "";
    if (!text) return;
    this.setData({ question: text });
  },

  toggleRecommendSummary() {
    // UI优化：推荐依据折叠切换
    if (!this.data.recommendSummary) return;
    this.setData({ recommendSummaryExpanded: !this.data.recommendSummaryExpanded });
  },

  toggleTaskDone(e) {
    // UI优化：行动清单整行点击反馈
    const idx = Number(e.currentTarget.dataset.index);
    const tasks = (this.data.actionTasks || []).slice();
    if (!tasks[idx]) return;
    tasks[idx].done = !tasks[idx].done;
    this.setData({ actionTasks: tasks });
  },

  toggleExplain(e) {
    const idx = Number(e.currentTarget.dataset.index);
    const map = { ...(this.data.explainExpandedMap || {}) };
    map[idx] = !map[idx];
    this.setData({ explainExpandedMap: map });
  },

  copyExplain(e) {
    const idx = Number(e.currentTarget.dataset.index);
    const card = (this.data.recommendCards || [])[idx];
    if (!card) return;
    const exp = card.explain || {};
    const md = exp.match_detail || {};
    const sc = exp.strategy_context || {};
    const kg = exp.kg_context || {};
    const lines = [
      `【L1 用户可读理由】${card.reason || ''}`,
      `【L2 系统依据】综合=${exp.final_score_text || '0.00'} 匹配=${exp.match_score_text || '0.00'} 新鲜=${exp.novelty_score_text || '0.00'} 已看=${exp.diversity_penalty_text || '0.00'}`,
      Object.keys(md).length ? `【L2 匹配依据】${Object.entries(md).map(([k,v]) => `${k}=${v}`).join(' ')}` : '',
      `【L3 策略上下文】推荐方式=${exp.crs_mode_label || '-'} 来源=${(sc.sources || []).join('/')} 兴趣=${(sc.heritage_terms || []).join('/')}`,
      kg.similar_entities ? `【L4 关联推荐】相似=${(kg.similar_entities || []).join('/')} 路径=${kg.expand_path || '-'} 原因=${kg.kg_reason || '-'}` : '',
    ];
    const text = lines.filter(Boolean).join('\n');
    wx.setClipboardData({ data: text, success: () => wx.showToast({ title: '解释已复制', icon: 'success' }) });
  },

  _stopDigitalHumanNarration() {
    if (this.digitalHumanAudio) {
      try {
        this.digitalHumanAudio.stop();
      } catch (e) {}
    }
    if (typeof this.stopDigitalHumanCaptionTimer === "function") {
      this.stopDigitalHumanCaptionTimer();
    }
    this.setData({
      digitalHumanSpeaking: false,
      digitalHumanCaptionVisible: false
    });
    if (typeof this.syncDigitalHumanStage === "function") {
      this.syncDigitalHumanStage();
    }
  },

  openRecommendCard(e) {
    const idx = Number(e.currentTarget.dataset.index);
    const card = (this.data.recommendCards || [])[idx];
    if (!card) return;
    const url = cardUrl(card);
    if (!url) return;

    const session = wx.getStorageSync("session") || {};
    request({
      url: "/recommend/track",
      method: "POST",
      data: {
        user_id: session.userId || null,
        action: "click",
        target_type: card.type === "topic" ? "topic" : card.type,
        target_id: card.id,
        source_scene: "ai_chat",
        explain: card.explain || {}
      }
    }).catch(() => {});

    wx.navigateTo({ url });
  },

  feedbackOverall(e) {
    const { type } = e.currentTarget.dataset;
    const feedbackMap = { like: "feedback_like", dislike: "feedback_dislike" };
    const action = feedbackMap[type];
    if (!action) return;

    // 更新本地反馈状态，防止重复点击
    this.setData({ "feedbackMap._overall": type });

    const session = wx.getStorageSync("session") || {};
    // 对每张推荐卡片都记录反馈
    const cards = this.data.recommendCards || [];
    cards.forEach((card) => {
      request({
        url: "/recommend/track",
        method: "POST",
        data: {
          user_id: session.userId || null,
          action: action,
          target_type: card.type === "topic" ? "topic" : card.type,
          target_id: card.id,
          source_scene: "ai_chat",
          explain: card.explain || {}
        }
      }).catch(() => {});
    });

    wx.showToast({
      title: type === "like" ? "感谢反馈" : "已记录，会改进推荐",
      icon: "none",
      duration: 1200
    });
  },

  toFixedContent() {
    const id = this.data.fixedCta && this.data.fixedCta.contentId;
    if (!id) return;
    wx.navigateTo({ url: `/pages/user/content/detail/index?id=${id}` });
  },

  toFixedEvent() {
    const id = this.data.fixedCta && this.data.fixedCta.eventId;
    if (!id) return;
    wx.navigateTo({ url: `/pages/user/activity/detail/index?id=${id}` });
  },

  clearHistory() {
    this.clearTypingTimer(true);
    wx.removeStorageSync("ai_chat_history");
    wx.removeStorageSync(AI_RECOMMEND_STATE_KEY);
    const session = wx.getStorageSync("session") || {};
    wx.removeStorageSync(`${AI_COLDSTART_WELCOME_ONCE_KEY}_${session.userId || 'guest'}`);
    this.setData({
      messages: [],
      typingIndex: -1,
      sourceTag: "",
      rewriteSuggestions: [],
      recommendCards: [],
      actionTasks: [],
      dialogueStrategy: "",
      strategyNote: "",
      askPrompt: "",
      askOptions: [],
      askId: "",
      askAttribute: "",
      feedbackMap: {},
      crsMode: "cold_start",
      crsConfidence: 0,
      crsSessionId: "",
      crsDimensions: {},
      digitalHumanMood: "curious",
      modeCelebrating: false,
      celebrationMode: "",
      celebrationFading: false,
      presetMode: "default",
      presetTitle: "推荐发问",
      recommendPrefix: "",
      selectedAskOption: "",
      recentQuestions: [],
      recommendSummary: "",
      recommendSummaryBrief: "",
      recommendSummaryExpanded: false,
      recommendSummarySources: [],
      kgEntity: "",
      kgPathText: "",
      kgSimilarNames: [],
      kgExpandItems: [],
      fixedCta: { show: false, contentId: null, eventId: null },
      digitalHumanLiveCaption: "",
      digitalHumanCaptionVisible: false,
      digitalHumanCaptionProgress: 0
    });
    this.refreshPresets(true, { history: [] });
    // 重置CRS会话
    if (session.userId) {
      request({
        url: "/ai/crs/reset",
        method: "POST",
        data: { user_id: session.userId }
      }).catch(() => {});
    }
  },

  onAvatarSpeakTap() {
    const messages = this.data.messages || [];
    const latestAiMessage = [...messages].reverse().find((item) => item && item.role === "ai" && item.text);
    if (latestAiMessage && latestAiMessage.text) {
      this.narrateDigitalHumanText(latestAiMessage.text);
      return;
    }
    this.speakDigitalHumanLatest();
  },

  speakCurrentMessage(e) {
    const text = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.text : "";
    if (!text) return;
    this.narrateDigitalHumanText(text);
  },

  clearTypingTimer(finalize = false) {
    if (this.typingTimer) {
      clearInterval(this.typingTimer);
      this.typingTimer = null;
    }
    if (finalize && this.pendingTypingState) {
      const { fullText, typingIndex } = this.pendingTypingState;
      if (this.data.messages[typingIndex]) {
        this.setData({ [`messages[${typingIndex}].text`]: fullText, typingIndex: -1 });
        var draft = (this.data.messages || []).slice();
        if (draft[typingIndex]) draft[typingIndex].text = fullText;
        wx.setStorageSync("ai_chat_history", truncateMessages(draft));
      }
      this.pendingTypingState = null;
    }
  },

  playTypewriter(fullText, typingIndex, autoNarrate = false) {
    this.clearTypingTimer(true);
    const text = String(fullText || "");
    if (!text) {
      this.pendingTypingState = null;
      this.setData({ typingIndex: -1 });
      return;
    }

    this.pendingTypingState = { fullText: text, typingIndex };
    let cursor = 0;
    let hasNarrated = false;
    const step = text.length > 120 ? 3 : text.length > 48 ? 2 : 1;

    this.typingTimer = setInterval(() => {
      cursor = Math.min(text.length, cursor + step);
      if (!this.data.messages[typingIndex]) {
        this.clearTypingTimer(false);
        this.pendingTypingState = null;
        this.setData({ typingIndex: -1 });
        return;
      }
      const currentText = text.slice(0, cursor);
      this.setData({ [`messages[${typingIndex}].text`]: currentText });
      if (autoNarrate && !hasNarrated && cursor >= Math.min(24, text.length)) {
        hasNarrated = true;
        if (this.narrateDigitalHumanText) this.narrateDigitalHumanText(text);
      }
      if (cursor >= text.length) {
        this.clearTypingTimer(false);
        this.pendingTypingState = null;
        this.setData({ typingIndex: -1 });
        var draft = (this.data.messages || []).slice();
        if (draft[typingIndex]) draft[typingIndex].text = text;
        wx.setStorageSync("ai_chat_history", truncateMessages(draft));
      }
    }, 28);
  },

  // CRS v2.0.7：模式升级庆祝动效
  _triggerModeCelebration(newMode) {
    if (!newMode || newMode === "cold_start") return;
    this.setData({
      modeCelebrating: true,
      celebrationMode: newMode
    });
    // 3秒后自动淡出关闭
    clearTimeout(this._celebrationTimer);
    this._celebrationTimer = setTimeout(() => {
      this._dismissCelebration();
    }, 3000);
  },

  _dismissCelebration() {
    // 添加淡出class → 动画结束再移除
    this.setData({ celebrationFading: true });
    setTimeout(() => {
      this.setData({ modeCelebrating: false, celebrationFading: false });
    }, 350);
  },

  _onCelebrationTap() {
    clearTimeout(this._celebrationTimer);
    this._dismissCelebration();
  }
});
