# 答辩教程文稿：CRS 对话推荐算法与代码对应关系

## 一、CRS 系统总体架构

```
用户输入问题
     │
     ▼
┌─────────────────────────────────────────────┐
│  ai_answer()  主入口                         │
│  文件: app/services/ai_service.py            │
│                                              │
│  ① 偏好同步（问题→画像、KB→画像、KG→画像）   │
│  ② calc_confidence() → 三维置信度            │
│  ③ crs_decide() → ASK-REC策略决策            │
│  ④ _generate_answer() → 五级回退生成回答      │
│  ⑤ 组装结果（策略+推荐卡片+KG+推荐问题）      │
└─────────────────────────────────────────────┘
     │
     ▼
  返回前端: answer + recommend_cards + strategy + kg_*
```

## 二、三维置信度模型

### 2.1 公式

```
C = 0.40 × S_explicit + 0.35 × S_implicit + 0.25 × S_dialogue
```

### 2.2 代码对应

| 维度 | 代码位置 | 计算逻辑 |
|------|---------|---------|
| S_explicit | `recommendation_service.py:1222` `_calc_explicit_score()` | heritage每词+30(上限60) + scene每词+20(上限40) + region每词+20(上限40) + ASK回答每条+10(上限30) |
| S_implicit | `recommendation_service.py` `calc_implicit_score()` | 浏览+5(上限40) + 报名+15(上限30) + 互动+8(上限30) + ASK激励+7(上限20) + AI对话+5(上限20) |
| S_dialogue | `recommendation_service.py` `_calc_dialogue_score()` | AI提问+4(上限40) + ASK有效回答+12(上限60) |

### 2.3 模式切换阈值

```python
# recommendation_service.py:1103-1104
CRS_THRESHOLD_COLD = 28    # C < 28 → cold_start
CRS_THRESHOLD_MIXED = 62   # 28 ≤ C < 62 → mixed; C ≥ 62 → precision
```

| 置信度范围 | 模式 | 含义 |
|-----------|------|------|
| C < 28 | cold_start | 系统不了解用户，需要主动提问 |
| 28 ≤ C < 62 | mixed | 部分了解，边推荐边追问 |
| C ≥ 62 | precision | 充分了解，精准推荐 |

### 2.4 置信度提升路径（答辩演示重点）

| 操作 | 对C的贡献 | 代码入口 |
|------|----------|---------|
| 回答1次ASK问题 | +9.45分 | `session.py:process_ask_answer()` → `preference.py:apply_answer_to_preference()` |
| AI对话1次 | +2.75分 | `ai_service.py:ai_answer()` → `preference.py:sync_question_to_preferences()` |
| 设置1个heritage偏好 | +12分 | `preference.py:append_preference()` |
| KB命中反哺画像 | +12分 | `preference.py:sync_kb_chapter_to_preference()` |
| KG实体反哺画像 | +12分 | `preference.py:sync_kg_entity_to_preference()` |

## 三、ASK-REC 五策略决策

### 3.1 决策流程图

```
用户问题 q
     │
     ├─ is_followup=True? ──→ intent_driven_rec（追问意图，直接推荐）
     │
     ├─ q含"推荐/适合/先看"? ──→ intent_driven_rec（主动求推荐）
     │
     ├─ turn≥3 且 C<28? ──→ recovery_ask（恢复性提问）
     │
     ├─ mode=cold_start 且 偶数轮? ──→ mixed（穿插推荐）
     │
     ├─ mode=cold_start? ──→ cold_start_ask（冷启动提问）
     │
     ├─ mode=mixed? ──→ mixed（混合推荐+追问）
     │
     └─ mode=precision? ──→ precision（精准推荐）
```

### 3.2 代码对应

```python
# decision.py:26-72  crs_decide()
def crs_decide(question, confidence_result, session, rec_payload, kb_result, is_followup):
    c = confidence_result["confidence_score"]
    mode = confidence_result["mode"]
    turn_count = session.turn_count

    if is_followup:                    → intent_driven_rec
    if "推荐" in q:                    → intent_driven_rec
    if turn>=3 and c<28:              → recovery_ask
    if mode=="cold_start" and 偶数轮:  → mixed（穿插）
    if mode=="cold_start":            → cold_start_ask
    if mode=="mixed":                 → mixed
    if mode=="precision":             → precision
```

### 3.3 冷启动ASK选择顺序

```python
# decision.py:75-81  select_cold_start_ask()
A01(category) → A02(region) → A03(scene) → A04(level) → A05(category备选)
# 已问过的属性自动跳过，A05始终可选
```

## 四、偏好同步机制（4条路径）

### 4.1 偏好写入统一入口

所有偏好变更都经过 `preference.py:append_preference()`，自动去重。

### 4.2 四条偏好同步路径

| 路径 | 触发条件 | 代码位置 | 映射字典 |
|------|---------|---------|---------|
| ASK回答→偏好 | 用户点击ASK选项 | `preference.py:apply_answer_to_preference()` | `mappings.py:OPTION_TO_PREFERENCE` |
| 问题文本→偏好 | AI对话中用户提问 | `preference.py:sync_question_to_preferences()` | `mappings.py:QUESTION_*_MAP` |
| KB章节→偏好 | KB命中时反哺 | `preference.py:sync_kb_chapter_to_preference()` | `mappings.py:KB_CHAPTER_TO_PREFERENCE` |
| KG实体→偏好 | KG识别到实体 | `preference.py:sync_kg_entity_to_preference()` | `mappings.py:KG_ENTITY_TO_CATEGORY` |

### 4.3 映射字典示例

```python
# mappings.py
OPTION_TO_PREFERENCE = {
    "传统工艺": ("preferred_heritage_types", "工艺"),
    "华东地区": ("preferred_regions", "华东"),
    "线下体验": ("preferred_scene_types", "活动体验"),
    ...
}

KG_ENTITY_TO_CATEGORY = {
    "苏绣": "工艺", "昆曲": "戏曲", "端午节": "民俗", "中医针灸": "医药",
    ...
}

QUESTION_HERITAGE_MAP = {
    "工艺": "工艺", "绣": "工艺", "戏曲": "戏曲", "昆曲": "戏曲",
    "民俗": "民俗", "端午": "民俗", "医药": "医药", "针灸": "医药",
    ...
}
```

## 五、五级回答回退策略

### 5.1 回退层级

```
L1: KB高置信度命中 → 豆包润色(kb_enhanced, conf=0.92)
L2: KB低置信度命中 → 豆包参考回答(doubao, conf=0.78)
L3: KB未命中 → 豆包合并调用(回答+追问建议)(doubao, conf=0.75)
L4: 豆包失败 → 联网搜索+豆包总结(web_enhanced, conf=0.65)
L5: 全部失败 → 兜底回答(fallback, conf=0.25)
```

### 5.2 代码对应

```python
# ai_service.py:634  _generate_answer()
if kb_matched and kb_confidence >= 0.8:     → L1: kb_enhanced
elif kb_matched and kb_confidence >= 0.45:   → L2: doubao
else:
    combined = _ask_doubao_combined()        → L3: doubao
    if not answer:
        web_brief = search_web_brief()       → L4: web_enhanced
    if not answer:
        fallback = _build_recommend_fallback_answer()  → L5: fallback
```

## 六、知识图谱(KG)增强

### 6.1 KG在CRS中的角色

```
用户问题 → _extract_kg_entity() → 识别实体(如"苏绣")
    │
    ├─ kg_service.similar_entities() → 相似实体推荐(蜀绣/湘绣)
    ├─ kg_service.expand_recommendations() → 扩展推荐(深度2跳)
    ├─ kg_service.shortest_path() → 实体间路径解释
    │
    └─ _inject_kg_reason() → 将KG信息注入推荐卡片reason字段
```

### 6.2 代码对应

| 功能 | 代码位置 | 说明 |
|------|---------|------|
| 实体识别 | `ai_service.py:_extract_kg_entity()` | 从KG_ENTITY_HINTS列表匹配 |
| 相似推荐 | `knowledge_graph.py:KnowledgeGraphService.similar_entities()` | 基于图谱边关系 |
| 扩展推荐 | `knowledge_graph.py:KnowledgeGraphService.expand_recommendations()` | BFS多跳遍历 |
| 路径解释 | `knowledge_graph.py:KnowledgeGraphService.shortest_path()` | Dijkstra最短路径 |
| KG→偏好 | `preference.py:sync_kg_entity_to_preference()` | 实体→类目→偏好字段 |
| KG缓存 | `knowledge_graph.py:_similar_cache/_expand_cache/_path_cache` | 避免重复查询 |

## 七、CRS模块文件结构

```
app/services/crs/
├── __init__.py          # 公共接口导出（25行）
├── constants.py         # 常量：阈值、术语列表、章节（29行）
├── mappings.py          # 6个映射字典 + 4个lookup函数（95行）
├── ask_templates.py     # ASK提问模板(13套) + 跳过答案 + 意图词（27行）
├── preference.py        # 偏好同步4条路径 + auto_create_ask_log（148行）
├── decision.py          # 五策略决策 + ASK选择 + 过渡语生成（141行）
├── session.py           # 会话管理 + ASK回答处理（97行）
└── questions.py         # 推荐问题生成 + 章节匹配 + 属性检测（377行）

app/services/
├── ai_service.py        # AI问答主入口 + 五级回退 + KG增强（~900行）
├── recommendation_service.py  # 推荐引擎 + 置信度计算（~1300行）
└── knowledge_graph.py   # 知识图谱服务 + 缓存（~230行）
```

## 八、答辩演示路径（5轮对话）

| 轮次 | 输入 | 演示点 | 预期输出 |
|------|------|--------|---------|
| R1 | 昆曲为什么被称为百戏之祖 | KB命中+KG实体识别 | source=kb_enhanced, kg_entity=昆曲 |
| R2 | 苏绣有什么特点 | KG实体+偏好同步 | kg_entity=苏绣, heritage写入"工艺" |
| R3 | 推荐一些传统工艺的内容 | 意图驱动推荐策略 | strategy=intent_driven_rec |
| R4 | 有没有线下体验活动 | 场景偏好检测 | scene写入"线下体验" |
| R5 | 端午节为什么属于活态非遗 | 跨类目KB+KG | kg_entity=端午节, chapter=民俗 |

## 九、关键数据流图

```
用户提问 "苏绣有什么特点"
    │
    ├─① search_local_knowledge("苏绣有什么特点")
    │     → KB命中(conf=0.85), chapter="传统工艺"
    │
    ├─② _extract_kg_entity("苏绣有什么特点", rec_payload)
    │     → kg_entity="苏绣"
    │
    ├─③ sync_question_to_preferences(user, "苏绣有什么特点")
    │     → QUESTION_HERITAGE_MAP["绣"]="工艺" → preferred_heritage_types += ["工艺"]
    │
    ├─④ sync_kb_chapter_to_preference(user, "传统工艺")
    │     → KB_CHAPTER_TO_PREFERENCE["传统工艺"]="工艺" → preferred_heritage_types += ["工艺"]
    │
    ├─⑤ sync_kg_entity_to_preference(user, "苏绣")
    │     → KG_ENTITY_TO_CATEGORY["苏绣"]="工艺" → preferred_heritage_types += ["工艺"]
    │
    ├─⑥ calc_confidence(db, user_id)
    │     → S_explicit=60, S_implicit=20, S_dialogue=30
    │     → C = 0.4×60 + 0.35×20 + 0.25×30 = 38.5 → mode=mixed
    │
    ├─⑦ crs_decide(q, confidence, session, rec_payload, kb_result)
    │     → strategy=mixed, ask_id=B01
    │
    ├─⑧ kg_service.similar_entities("苏绣", limit=3)
    │     → ["蜀绣", "湘绣", "南京云锦"]
    │
    ├─⑨ _generate_answer(q, kb_result, ...)
    │     → L1: KB高置信度命中 → 豆包润色 → source=kb_enhanced
    │
    └─⑩ 返回结果
          answer="苏绣以针法精细著称..."
          recommend_cards=[苏绣针法图解, ...]
          kg_entity="苏绣", kg_similar=[蜀绣,湘绣]
          strategy="mixed", crs_mode="mixed"
```
