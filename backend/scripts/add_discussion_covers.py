#!/usr/bin/env python3
"""为讨论帖子从 Pixabay 匹配封面图，无匹配则删除"""

import sqlite3
import urllib.request
import urllib.parse
import json
import time
import os
import re
from pathlib import Path

PIXABAY_KEY = "55468384-6826bf941c33f15394e137805"
DB_PATH = r"D:\桌面\毕业设计\backend\heritage_platform.db"
COVER_DIR = Path(r"D:\桌面\毕业设计\backend\storage\covers")
COVER_DIR.mkdir(parents=True, exist_ok=True)

def search_pixabay(query, per_page=5):
    """搜索 Pixabay 并返回 hits"""
    params = urllib.parse.urlencode({
        "key": PIXABAY_KEY,
        "q": query,
        "lang": "zh",
        "per_page": per_page,
        "image_type": "photo",
        "safesearch": "true",
        "min_width": 800,
    })
    url = f"https://pixabay.com/api/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("hits", [])
    except Exception as e:
        print(f"  API ERROR: {e}")
        return []

def download_image(img_url, filename):
    """下载图片到 covers 目录"""
    filepath = COVER_DIR / filename
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            filepath.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"  DOWNLOAD ERROR: {e}")
        return False

def build_query(title, tags):
    """从标题和标签构建搜索词"""
    # 如果标题有乱码，用标签
    parts = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        parts.extend(tag_list[:2])

    # 尝试提取标题中可能的关键词
    try:
        clean_title = title.encode('latin-1').decode('utf-8', errors='replace')
    except:
        clean_title = title

    # 中国非遗相关默认加
    if not parts:
        parts = ["中国文化", "传统"]

    query = " ".join(parts) + " 中国"
    return query

def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # 获取所有没有封面的帖子
    cursor.execute('''
        SELECT dt.id, dt.title, GROUP_CONCAT(dtt.tag, ",") as tags
        FROM discussion_topics dt
        LEFT JOIN discussion_topic_tags dtt ON dt.id = dtt.topic_id
        WHERE dt.cover_url IS NULL OR dt.cover_url = ""
        GROUP BY dt.id
    ''')
    topics = cursor.fetchall()
    print(f"共 {len(topics)} 条帖子需要处理\n")

    success = 0
    failed = 0
    delete_ids = []

    for i, topic in enumerate(topics):
        topic_id = topic["id"]
        title = topic["title"]
        tags = topic["tags"] or ""

        # 尝试修复编码
        try:
            display_title = title.encode('latin-1').decode('utf-8')
        except:
            display_title = title[:40]

        query = build_query(title, tags)
        print(f"[{i+1}/{len(topics)}] ID={topic_id} | {display_title[:50]}")
        print(f"  搜索: {query}")

        hits = search_pixabay(query, per_page=5)
        if not hits:
            print(f"  => 无结果，标记删除")
            delete_ids.append(topic_id)
            failed += 1
            time.sleep(0.5)
            continue

        # 找到最佳匹配
        best = hits[0]
        img_url = best.get("largeImageURL") or best.get("webformatURL")
        if not img_url:
            delete_ids.append(topic_id)
            failed += 1
            continue

        # 生成文件名
        safe_name = f"discussion_{topic_id}_{best['id']}.jpg"
        if download_image(img_url, safe_name):
            cover_url = f"/storage/covers/{safe_name}"
            cursor.execute(
                "UPDATE discussion_topics SET cover_url = ? WHERE id = ?",
                (cover_url, topic_id)
            )
            db.commit()
            print(f"  => OK: {cover_url}")
            success += 1
        else:
            print(f"  => 下载失败，标记删除")
            delete_ids.append(topic_id)
            failed += 1

        # 速率限制
        time.sleep(0.6)

    # 删除无图片的帖子（级联删除关联数据）
    if delete_ids:
        print(f"\n=== 删除 {len(delete_ids)} 条无图片帖子 ===")
        placeholders = ",".join("?" * len(delete_ids))

        # 先删关联数据
        for rel_table in ["discussion_comments", "discussion_likes",
                          "discussion_favorites", "discussion_topic_tags"]:
            cursor.execute(
                f"DELETE FROM {rel_table} WHERE topic_id IN ({placeholders})",
                delete_ids
            )
            print(f"  {rel_table}: {cursor.rowcount} rows deleted")

        # 再删主表
        cursor.execute(
            f"DELETE FROM discussion_topics WHERE id IN ({placeholders})",
            delete_ids
        )
        print(f"  discussion_topics: {cursor.rowcount} rows deleted")
        db.commit()

    print(f"\n=== 完成 ===")
    print(f"成功: {success}")
    print(f"失败/删除: {failed}")
    print(f"剩余帖子: {len(topics) - len(delete_ids)}")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM discussion_topics")
    remaining = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM discussion_topics WHERE cover_url IS NOT NULL AND cover_url != ''"
    )
    with_img = cursor.fetchone()[0]
    print(f"数据库帖子总数: {remaining}, 有封面: {with_img}")

    db.close()

if __name__ == "__main__":
    main()
