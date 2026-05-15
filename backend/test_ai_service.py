#!/usr/bin/env python3
"""AI服务优化效果测试脚本"""

import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.ai_service import ai_answer

# 创建测试数据库连接
engine = create_engine(settings.sqlite_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_ai_answer():
    """测试AI问答功能"""
    db = SessionLocal()
    
    test_cases = [
        "什么是非遗？",
        "苏绣有什么特点？",
        "推荐一些传统工艺相关的内容",
        "端午节的习俗有哪些？",
        "昆曲适合新手从哪里入门？",
    ]
    
    print("=" * 60)
    print("AI对话测试 - 优化效果验证")
    print("=" * 60)
    print()
    
    success_count = 0
    fail_count = 0
    
    for i, question in enumerate(test_cases, 1):
        print(f"[{i}] 问题: {question}")
        try:
            result = ai_answer(db, question, user_id=1)
            
            # 提取关键信息
            answer = result.get("answer", "")
            source = result.get("source", "")
            confidence = result.get("confidence", 0)
            recommend_cards = result.get("recommend_cards", [])
            followup_questions = result.get("followup_questions", [])
            
            print("   回答: %s..." % answer[:100] if len(answer) > 100 else "   回答: %s" % answer)
            print("   来源: %s" % source)
            print("   置信度: %.2f" % confidence)
            print("   推荐卡片数: %d" % len(recommend_cards))
            if followup_questions:
                print("   追问建议: %s" % ", ".join(followup_questions[:3]))
            
            print("   [OK]")
            success_count += 1
            
        except Exception as e:
            print("   [FAIL]: %s" % str(e)[:100])
            fail_count += 1
        print()
    
    db.close()
    print("=" * 60)
    print("测试完成! 成功: %d, 失败: %d" % (success_count, fail_count))

if __name__ == "__main__":
    test_ai_answer()