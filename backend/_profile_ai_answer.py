import sys, time
sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.ai_qa_log import AIQALog
from app.services.knowledge_base import search_local_knowledge
from app.services.recommendation_service import calc_confidence, generate_recommendation_payload, generate_ai_recommend_cards
from app.services.ai_service import (
    _detect_vague_followup, _build_followup_context,
    _extract_kg_entity, _load_recent_history,
    _build_crs_aware_prompt, _build_recommend_context_for_ai,
    _ask_doubao_with_fallback, _ask_doubao_combined,
    _crs_decide, _get_or_create_session, _update_session_mode,
    ai_recommend_with_context,
)
from app.services.crs.session import get_or_create_session, update_session_mode
from app.services.knowledge_graph import kg_service

engine = create_engine(settings.sqlite_url)
db = sessionmaker(bind=engine)()
UID = 16
Q = "苏绣入门可以从哪些小件绣品开始了解"

timings = {}

t0 = time.time()
vague = _detect_vague_followup(Q, db, UID)
timings["vague_followup"] = time.time() - t0

t0 = time.time()
followup = _build_followup_context(Q, None)
timings["followup_context"] = time.time() - t0

rec_query = followup["topic"] if followup["is_followup"] else Q

t0 = time.time()
kb_result = search_local_knowledge(db, rec_query)
timings["kb_search"] = time.time() - t0
print(f"  KB: matched={kb_result['matched']}, conf={kb_result.get('confidence',0):.2f}")

t0 = time.time()
user = db.query(User).filter(User.id == UID).first()
timings["user_query"] = time.time() - t0

t0 = time.time()
crs_session = get_or_create_session(db, UID)
timings["crs_session"] = time.time() - t0

t0 = time.time()
conf_result = calc_confidence(db, UID)
timings["calc_confidence"] = time.time() - t0
print(f"  Confidence: mode={conf_result['mode']}, score={conf_result['confidence_score']:.1f}")

t0 = time.time()
rec_payload = generate_recommendation_payload(db, UID, context_text=rec_query, scene="ai")
timings["rec_payload"] = time.time() - t0

t0 = time.time()
strategy = _crs_decide(Q, conf_result, crs_session, rec_payload, kb_result, is_followup=followup["is_followup"])
timings["crs_decide"] = time.time() - t0

t0 = time.time()
cards = generate_ai_recommend_cards(db, UID, rec_query, rec_payload=rec_payload, prefer_hot=False)
timings["gen_cards"] = time.time() - t0

t0 = time.time()
history = _load_recent_history(db, UID, limit=3)
timings["load_history"] = time.time() - t0

t0 = time.time()
kg_entity = _extract_kg_entity(Q, rec_payload)
timings["kg_extract"] = time.time() - t0
print(f"  KG entity: {kg_entity}")

if kg_entity:
    t0 = time.time()
    kg_similar = kg_service.similar_entities(kg_entity, limit=3)
    timings["kg_similar"] = time.time() - t0

    t0 = time.time()
    kg_expand = kg_service.expand_recommendations(kg_entity, depth=2, limit=5)
    timings["kg_expand"] = time.time() - t0

    t0 = time.time()
    if kg_similar.get("items"):
        first = kg_similar["items"][0].get("entity", "")
        if first:
            kg_path = kg_service.shortest_path(kg_entity, first)
    timings["kg_path"] = time.time() - t0

t0 = time.time()
prompt = _build_crs_aware_prompt(conf_result["mode"], rec_payload, kb_result)
timings["build_prompt"] = time.time() - t0

t0 = time.time()
rec_ctx = _build_recommend_context_for_ai(cards, strategy, user_question=Q)
timings["build_rec_ctx"] = time.time() - t0

if cards and len(cards) > 1 and strategy.get("strategy") in ("intent_driven_rec", "precision", "mixed"):
    t0 = time.time()
    try:
        cards = ai_recommend_with_context(candidates=cards, question=Q, chat_history=history, strategy_name=strategy["strategy"])
    except:
        pass
    timings["ai_recommend"] = time.time() - t0
    print(f"  AI recommend: {timings.get('ai_recommend', 0):.2f}s")

t0 = time.time()
answer = _ask_doubao_with_fallback(question=Q, history=history, context=rec_ctx, system_prompt=prompt)
timings["doubao_call"] = time.time() - t0
print(f"  Doubao answer length: {len(answer or '')}")

print("\n" + "="*50)
print("耗时分析")
print("="*50)
total = sum(timings.values())
for k, v in sorted(timings.items(), key=lambda x: -x[1]):
    pct = v / total * 100
    bar = "█" * int(pct / 2)
    print(f"  {k:<20} {v:>6.2f}s  {pct:>5.1f}%  {bar}")
print(f"  {'TOTAL':<20} {total:>6.2f}s")

db.close()
