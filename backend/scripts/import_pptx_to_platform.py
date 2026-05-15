from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.activity import Activity
from app.models.content import Content
from app.models.discussion_comment import DiscussionComment
from app.models.discussion_extra import DiscussionFavorite, DiscussionTopicTag
from app.models.discussion_like import DiscussionLike
from app.models.discussion_topic import DiscussionTopic
from app.models.user import User

PDF_IMPORT_DIR = BASE_DIR / "storage" / "pdf_import"
PDF_IMAGE_DIR = BASE_DIR / "storage" / "pdf_assets"

CONTENT_CREATOR_ID = -121
ACTIVITY_ORGANIZER = "资料导入活动（PDF）"
TOPIC_NICKNAME = "资料整理员"
TOPIC_OPENID = "wx_pdf_importer"


def log(message: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def _safe_name(name: str) -> str:
    return re.sub(r"[^\w\-\u4e00-\u9fff]+", "_", name).strip("_") or "pdf"


def _title_summary(text: str) -> tuple[str, str, str]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if not lines:
        return "未命名内容", "", ""
    title = lines[0][:120]
    body_lines = lines[1:]
    summary = "；".join(body_lines[:2])[:220]
    body = "\n".join(lines)[:4500]
    return title, summary, body


def _detect_kind(text: str) -> str:
    activity_hits = sum(k in text for k in ["报名", "活动", "时间", "地点", "名额", "签到", "工作坊", "讲座", "研学"])
    topic_hits = sum(k in text for k in ["分享", "请教", "求助", "踩坑", "复盘", "讨论", "感受", "大家觉得"])

    if activity_hits >= 2:
        return "activity"
    if topic_hits >= 2:
        return "topic"
    return "content"


def _extract_pdf_text(pdf_path: Path) -> list[str]:
    try:
        pypdf = __import__("pypdf", fromlist=["PdfReader"])
        PdfReader = getattr(pypdf, "PdfReader")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("缺少 pypdf 依赖，请先安装 requirements.txt") from e

    log(f"开始提取文本：{pdf_path.name}")
    reader = PdfReader(str(pdf_path))
    page_texts: list[str] = []
    total = len(reader.pages)
    for idx, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        page_texts.append(text)
        if idx == 1 or idx == total or idx % 5 == 0:
            log(f"文本进度 {pdf_path.name}: {idx}/{total} 页")
    return page_texts


def _extract_pdf_images(pdf_path: Path) -> dict[int, list[str]]:
    """
    返回: {page_no(从1开始): ["/static/pdf_assets/xxx.png", ...]}
    """
    try:
        fitz = __import__("fitz")
    except Exception:
        log("未安装 PyMuPDF，跳过 PDF 图片提取，仅导入文本")
        return {}

    PDF_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    out: dict[int, list[str]] = {}
    stem = _safe_name(pdf_path.stem)
    total = len(doc)
    log(f"开始提取图片：{pdf_path.name}")

    try:
        for i, page in enumerate(doc, start=1):
            page_urls: list[str] = []
            images = page.get_images(full=True)
            for j, img in enumerate(images, start=1):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                out_name = f"{stem}_p{i}_{j}.png"
                out_path = PDF_IMAGE_DIR / out_name
                pix.save(str(out_path))
                pix = None
                page_urls.append(f"/static/pdf_assets/{out_name}")
            if page_urls:
                out[i] = page_urls
            if i == 1 or i == total or i % 5 == 0:
                log(f"图片进度 {pdf_path.name}: {i}/{total} 页，本页图片 {len(images)} 张")
    finally:
        doc.close()

    return out


def _ensure_topic_user(db: Session) -> User:
    u = db.query(User).filter(User.openid == TOPIC_OPENID).first()
    if u:
        return u
    u = User(openid=TOPIC_OPENID, nickname=TOPIC_NICKNAME, role="user", is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _clean_old_imports(db: Session) -> None:
    log("开始清理上次 PDF 导入数据")
    db.query(Content).filter(Content.created_by == CONTENT_CREATOR_ID).delete(synchronize_session=False)
    db.query(Activity).filter(Activity.organizer == ACTIVITY_ORGANIZER).delete(synchronize_session=False)

    bad_topics = db.query(DiscussionTopic).filter(DiscussionTopic.nickname == TOPIC_NICKNAME).all()
    bad_ids = [t.id for t in bad_topics]
    if bad_ids:
        db.query(DiscussionComment).filter(DiscussionComment.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionLike).filter(DiscussionLike.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionFavorite).filter(DiscussionFavorite.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionTopicTag).filter(DiscussionTopicTag.topic_id.in_(bad_ids)).delete(synchronize_session=False)
        db.query(DiscussionTopic).filter(DiscussionTopic.id.in_(bad_ids)).delete(synchronize_session=False)

    db.commit()
    log("清理完成")


def import_single_pdf(db: Session, pdf_path: Path, topic_user_id: int) -> dict:
    log(f"开始处理文件：{pdf_path.name}")
    page_texts = _extract_pdf_text(pdf_path)
    page_images = _extract_pdf_images(pdf_path)

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    created_content = 0
    created_activity = 0
    created_topic = 0
    total_pages = len(page_texts)

    for page_no, text in enumerate(page_texts, start=1):
        if page_no == 1 or page_no == total_pages or page_no % 5 == 0:
            log(f"入库进度 {pdf_path.name}: {page_no}/{total_pages} 页")

        if not text:
            log(f"第 {page_no} 页无可用文本，跳过")
            continue

        title, summary, body = _title_summary(text)
        image_urls = page_images.get(page_no, [])
        cover_url = image_urls[0] if image_urls else None
        kind = _detect_kind(text)

        if kind == "activity":
            st = now + timedelta(days=page_no)
            et = st + timedelta(hours=2)
            db.add(
                Activity(
                    title=title[:180],
                    cover_url=cover_url,
                    location="待公布（来自PDF资料）",
                    organizer=ACTIVITY_ORGANIZER,
                    start_time=st,
                    end_time=et,
                    max_participants=50,
                    description=body[:1200],
                    notes=f"来源：{pdf_path.name} 第{page_no}页",
                    status="open",
                    is_featured=(page_no % 8 == 0),
                )
            )
            created_activity += 1
        elif kind == "topic":
            db.add(
                DiscussionTopic(
                    user_id=topic_user_id,
                    nickname=TOPIC_NICKNAME,
                    title=title[:180],
                    content=body[:1800],
                    cover_url=cover_url,
                    image_urls=json.dumps(image_urls, ensure_ascii=False),
                    is_featured=False,
                    like_count=0,
                    favorite_count=0,
                    comment_count=0,
                )
            )
            created_topic += 1
        else:
            db.add(
                Content(
                    title=title[:180],
                    cover_url=cover_url,
                    content_type="article",
                    summary=(summary or body[:120])[:500],
                    body=f"{body}\n\n来源：{pdf_path.name} 第{page_no}页",
                    chapter="PDF导入",
                    sub_chapter=pdf_path.stem[:100],
                    is_featured=(page_no % 10 == 0),
                    status="published",
                    published_at=now - timedelta(hours=page_no),
                    created_by=CONTENT_CREATOR_ID,
                )
            )
            created_content += 1

        if page_no % 10 == 0:
            db.commit()
            log(f"已阶段性提交数据库：{pdf_path.name} 第 {page_no} 页")

    db.commit()
    log(
        f"文件完成：{pdf_path.name}，"
        f"content={created_content}, activity={created_activity}, topic={created_topic}"
    )
    return {
        "file": str(pdf_path),
        "contents": created_content,
        "activities": created_activity,
        "topics": created_topic,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="将PDF一键导入为内容/活动/帖子")
    parser.add_argument("--input", type=str, default=str(PDF_IMPORT_DIR), help="PDF目录")
    parser.add_argument("--clean", action="store_true", help="导入前清理上次导入数据")
    args = parser.parse_args()

    input_dir = Path(args.input)
    input_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(input_dir.glob("*.pdf"))

    if not files:
        log(f"未发现PDF文件，请把文件放到: {input_dir}")
        return

    log(f"检测到 {len(files)} 个 PDF 文件")
    db = SessionLocal()
    try:
        if args.clean:
            _clean_old_imports(db)

        user = _ensure_topic_user(db)
        totals = {"contents": 0, "activities": 0, "topics": 0}
        for index, f in enumerate(files, start=1):
            log(f"===== 文件 {index}/{len(files)}：{f.name} =====")
            result = import_single_pdf(db, f, user.id)
            totals["contents"] += result["contents"]
            totals["activities"] += result["activities"]
            totals["topics"] += result["topics"]

        log(
            "导入完成，总计："
            f"content={totals['contents']}, activity={totals['activities']}, topic={totals['topics']}"
        )
        log(f"图片输出目录：{PDF_IMAGE_DIR}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
