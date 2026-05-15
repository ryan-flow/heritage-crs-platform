#!/usr/bin/env python3
"""7.4 冷启动效果实验

对比 CRS 引导 vs 无 CRS 引导的冷启动效果：
  1. 置信度随交互轮次的增长曲线
  2. 达到精准推荐模式所需交互轮次
  3. 偏好信息收集效率
"""

import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.recommendation_service import CRS_WEIGHT_EXPLICIT, CRS_WEIGHT_IMPLICIT, CRS_WEIGHT_DIALOGUE


def _simulate_crs_progression():
    """模拟有CRS引导的置信度增长过程"""
    rounds = []
    c_explicit = 0.0
    c_implicit = 0.0
    c_dialogue = 0.0

    steps = [
        {"round": 1, "action": "ask_category", "explicit_delta": 0.25, "dialogue_delta": 0.18, "implicit_delta": 0.02},
        {"round": 2, "action": "ask_region", "explicit_delta": 0.20, "dialogue_delta": 0.14, "implicit_delta": 0.03},
        {"round": 3, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.10},
        {"round": 4, "action": "ask_scene", "explicit_delta": 0.15, "dialogue_delta": 0.10, "implicit_delta": 0.02},
        {"round": 5, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.12},
        {"round": 6, "action": "ask_depth", "explicit_delta": 0.12, "dialogue_delta": 0.08, "implicit_delta": 0.03},
        {"round": 7, "action": "user_click", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.08},
        {"round": 8, "action": "recommend_feedback", "explicit_delta": 0.05, "dialogue_delta": 0.06, "implicit_delta": 0.04},
    ]

    for step in steps:
        c_explicit = min(1.0, c_explicit + step["explicit_delta"])
        c_implicit = min(1.0, c_implicit + step["implicit_delta"])
        c_dialogue = min(1.0, c_dialogue + step["dialogue_delta"])

        confidence = (
            CRS_WEIGHT_EXPLICIT * c_explicit
            + CRS_WEIGHT_IMPLICIT * c_implicit
            + CRS_WEIGHT_DIALOGUE * c_dialogue
        )

        if confidence < 0.35:
            mode = "cold_start"
        elif confidence < 0.60:
            mode = "mixed"
        else:
            mode = "precision"

        rounds.append({
            "round": step["round"],
            "action": step["action"],
            "s_explicit": round(c_explicit, 3),
            "s_implicit": round(c_implicit, 3),
            "s_dialogue": round(c_dialogue, 3),
            "confidence": round(confidence, 3),
            "mode": mode,
        })

    return rounds


def _simulate_no_crs_progression():
    """模拟无CRS引导的置信度增长过程（仅靠被动行为积累）"""
    rounds = []
    c_explicit = 0.0
    c_implicit = 0.0
    c_dialogue = 0.0

    steps = [
        {"round": 1, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.05},
        {"round": 2, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.06},
        {"round": 3, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.04},
        {"round": 4, "action": "user_click", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.07},
        {"round": 5, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.05},
        {"round": 6, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.04},
        {"round": 7, "action": "user_click", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.06},
        {"round": 8, "action": "user_browse", "explicit_delta": 0.00, "dialogue_delta": 0.00, "implicit_delta": 0.05},
    ]

    for step in steps:
        c_explicit = min(1.0, c_explicit + step["explicit_delta"])
        c_implicit = min(1.0, c_implicit + step["implicit_delta"])
        c_dialogue = min(1.0, c_dialogue + step["dialogue_delta"])

        confidence = (
            CRS_WEIGHT_EXPLICIT * c_explicit
            + CRS_WEIGHT_IMPLICIT * c_implicit
            + CRS_WEIGHT_DIALOGUE * c_dialogue
        )

        if confidence < 0.35:
            mode = "cold_start"
        elif confidence < 0.60:
            mode = "mixed"
        else:
            mode = "precision"

        rounds.append({
            "round": step["round"],
            "action": step["action"],
            "s_explicit": round(c_explicit, 3),
            "s_implicit": round(c_implicit, 3),
            "s_dialogue": round(c_dialogue, 3),
            "confidence": round(confidence, 3),
            "mode": mode,
        })

    return rounds


def run_experiment():
    crs_progression = _simulate_crs_progression()
    no_crs_progression = _simulate_no_crs_progression()

    crs_to_mixed = None
    crs_to_precision = None
    for r in crs_progression:
        if r["mode"] == "mixed" and crs_to_mixed is None:
            crs_to_mixed = r["round"]
        if r["mode"] == "precision" and crs_to_precision is None:
            crs_to_precision = r["round"]

    no_crs_to_mixed = None
    no_crs_to_precision = None
    for r in no_crs_progression:
        if r["mode"] == "mixed" and no_crs_to_mixed is None:
            no_crs_to_mixed = r["round"]
        if r["mode"] == "precision" and no_crs_to_precision is None:
            no_crs_to_precision = r["round"]

    crs_final = crs_progression[-1]["confidence"]
    no_crs_final = no_crs_progression[-1]["confidence"]

    return {
        "crs_guided": {
            "progression": crs_progression,
            "rounds_to_mixed": crs_to_mixed,
            "rounds_to_precision": crs_to_precision,
            "final_confidence": crs_final,
        },
        "no_crs": {
            "progression": no_crs_progression,
            "rounds_to_mixed": no_crs_to_mixed,
            "rounds_to_precision": no_crs_to_precision,
            "final_confidence": no_crs_final,
        },
        "comparison": {
            "confidence_improvement": round(crs_final - no_crs_final, 3),
            "speedup_to_mixed": round(no_crs_to_mixed / crs_to_mixed, 1) if crs_to_mixed and no_crs_to_mixed else None,
            "crs_reaches_precision": crs_to_precision is not None,
            "no_crs_reaches_precision": no_crs_to_precision is not None,
        },
        "weights": {
            "explicit": CRS_WEIGHT_EXPLICIT,
            "implicit": CRS_WEIGHT_IMPLICIT,
            "dialogue": CRS_WEIGHT_DIALOGUE,
        },
    }


if __name__ == "__main__":
    results = run_experiment()
    print(json.dumps(results, ensure_ascii=False, indent=2))
