#!/usr/bin/env python3
"""测试豆包API连接"""

import sys
sys.path.insert(0, '.')

from app.services.doubao_client import ask_doubao

def test_doubao_api():
    """测试豆包API是否正常工作"""
    print("=" * 60)
    print("豆包API连接测试")
    print("=" * 60)
    
    test_questions = [
        "你好，介绍一下你自己",
        "什么是非物质文化遗产？",
        "苏绣有什么特点？",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i}] 问题: {question}")
        try:
            answer = ask_doubao(question, max_tokens=200)
            print(f"回答: {answer[:150]}..." if len(answer) > 150 else f"回答: {answer}")
            print("✓ 成功")
        except Exception as e:
            print(f"✗ 失败: {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("测试完成!")

if __name__ == "__main__":
    test_doubao_api()