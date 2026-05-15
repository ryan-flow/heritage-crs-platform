"""一次性导入全部KB数据（batch1~batch4），彻底重建KB"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.local_knowledge_base import LocalKnowledgeBase

# 各批次函数
from import_authoritative_heritage_kb import authoritative_kb_items
import import_authoritative_heritage_kb_batch2 as b2
import import_authoritative_heritage_kb_batch3 as b3
import import_authoritative_heritage_kb_batch4 as b4

db = SessionLocal()
try:
    # 清空旧KB
    db.query(LocalKnowledgeBase).delete()
    db.commit()
    print("KB已清空")

    # 每批次对应的source常量
    SOURCE_MAP = {
        1: "权威公开资料整理",
        2: "权威公开资料整理（第二批）",
        3: "权威公开资料整理（第三批）",
        4: "权威公开资料整理（第四批）",
    }

    batches = [
        (1, "batch1-权威基础认知(23条)", authoritative_kb_items()),
        (2, "batch2-权威非遗知识(15条)",  b2.batch2_items()),
        (3, "batch3-非遗入门与传播(19条)", b3.batch3_items()),
        (4, "batch4-非遗实践与数字化(14条)", b4.batch4_items()),
    ]

    total = 0
    for bid, name, items in batches:
        src = SOURCE_MAP[bid]
        for item in items:
            db.add(LocalKnowledgeBase(
                question=item['question'],
                answer=item['answer'],
                qa_answer=item['qa_answer'],
                keywords=item['keywords'],
                chapter=item['chapter'],
                sub_chapter=item['sub_chapter'],
                source=src,
                status='active',
            ))
        db.commit()
        print(f"  {name}: {len(items)}条")
        total += len(items)

    print(f"\nKB导入完成，共 {total} 条")

    # 验证
    total_in_db = db.query(LocalKnowledgeBase).count()
    print(f"DB总计: {total_in_db} 条")

    # 按chapter分布
    from sqlalchemy import func
    dist = db.query(
        LocalKnowledgeBase.chapter,
        func.count(LocalKnowledgeBase.id)
    ).group_by(LocalKnowledgeBase.chapter).order_by(func.count(LocalKnowledgeBase.id).desc()).all()
    print("\n按类别分布:")
    for ch, cnt in dist:
        print(f"  {ch}: {cnt}条")

finally:
    db.close()
