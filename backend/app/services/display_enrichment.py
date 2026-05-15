from __future__ import annotations

import re


def _clean_lines(text: str | None) -> list[str]:
    raw = (text or "").replace("\r", "\n")
    parts = [re.sub(r"\s+", " ", line).strip(" ·•-*\t") for line in raw.split("\n")]
    return [line for line in parts if line]


def _pick_sentences(text: str | None, limit: int = 3, max_len: int = 36) -> list[str]:
    if not text:
        return []
    normalized = re.sub(r"\s+", " ", text)
    chunks = re.split(r"[。！？!?；;\n]", normalized)
    results: list[str] = []
    for chunk in chunks:
        line = chunk.strip(" ，,、")
        if not line:
            continue
        if len(line) > max_len:
            line = line[:max_len].rstrip("，,、 ") + "…"
        results.append(line)
        if len(results) >= limit:
            break
    return results


def build_content_display(summary: str | None, body: str | None) -> dict:
    lines = _clean_lines(body)
    intro = summary or (lines[0] if lines else "")
    highlights = _pick_sentences(body or summary, limit=3, max_len=34)
    if len(highlights) < 3:
        for line in lines[:5]:
            short = line[:34].rstrip("，,、 ") + ("…" if len(line) > 34 else "")
            if short and short not in highlights:
                highlights.append(short)
            if len(highlights) >= 3:
                break
    reading_tips = []
    if highlights:
        reading_tips.append("先看摘要，再顺着图片理解重点")
    if len(lines) >= 4:
        reading_tips.append("正文较长，适合收藏后分段阅读")
    reading_tips.append("看完后可继续进入相关活动或帖子")
    return {
        "intro": intro[:140],
        "highlights": highlights[:3],
        "reading_tips": reading_tips[:3],
    }


def build_event_display(description: str | None, notes: str | None, location: str | None) -> dict:
    source = "\n".join([x for x in [description, notes] if x])
    highlights = _pick_sentences(source, limit=3, max_len=34)
    agenda = []
    if description:
        text = description
        if "导览" in text:
            agenda.append("项目导览")
        if "体验" in text:
            agenda.append("互动体验")
        if "答疑" in text or "交流" in text:
            agenda.append("现场答疑")
    if not agenda:
        agenda = ["到场签到", "内容讲解", "自由交流"]
    tips = []
    if location:
        tips.append(f"建议提前确认路线：{location}")
    tips.append("建议提前10-15分钟到场")
    tips.append("报名后可先看相关知识内容做准备")
    return {
        "highlights": highlights[:3],
        "agenda": agenda[:3],
        "tips": tips[:3],
    }


def build_topic_display(content: str | None) -> dict:
    highlights = _pick_sentences(content, limit=3, max_len=34)
    guide_questions = [
        "你最认同帖子的哪个判断？",
        "如果你也参加过类似活动，会补充什么？",
        "这条内容更适合新手还是已有基础的人？",
    ]
    tone = "经验分享"
    text = content or ""
    if any(k in text for k in ["请教", "想问", "求助", "有没有"]):
        tone = "提问求助"
    elif any(k in text for k in ["复盘", "总结", "感受", "分享"]):
        tone = "体验复盘"
    return {
        "highlights": highlights[:3],
        "guide_questions": guide_questions,
        "tone": tone,
    }
