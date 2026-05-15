"""CRS 对话推荐系统

ASK-REC 状态机：冷启动提问 → 混合推荐 → 精准推荐
三维置信度驱动模式切换：explicit(40%) + implicit(35%) + dialogue(25%)
"""

from app.services.crs.ask_templates import ASK_TEMPLATES, SKIP_ANSWERS, RECOMMEND_INTENT_TERMS
from app.services.crs.mappings import (
    OPTION_TO_PREFERENCE, KG_ENTITY_TO_CATEGORY, KB_CHAPTER_TO_PREFERENCE,
    QUESTION_HERITAGE_MAP, QUESTION_SCENE_MAP, QUESTION_REGION_MAP,
    lookup_option_preference, lookup_kg_entity_category,
    lookup_kb_chapter_preference, lookup_question_preferences,
)
from app.services.crs.constants import (
    VAGUE_FOLLOWUP_MAX_LEN, HISTORY_TRUNCATE_LEN, AI_DIALOG_SCORE_DELTA,
    SPECIFIC_TERMS, CONTENT_CHAPTERS, SESSION_TIMEOUT_MINUTES,
)
from app.services.crs.preference import (
    append_preference, apply_answer_to_preference,
    sync_kg_entity_to_preference, sync_kb_chapter_to_preference,
    sync_question_to_preferences, auto_create_ask_log,
)
from app.services.crs.decision import crs_decide, select_cold_start_ask, select_mixed_ask, generate_ask_transition
from app.services.crs.questions import fetch_kb_questions, generate_recommended_questions, rewrite_suggestions
from app.services.crs.session import get_or_create_session, update_session_mode, process_ask_answer
