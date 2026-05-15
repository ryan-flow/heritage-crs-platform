#!/usr/bin/env python3
"""CRS算法循环优化与性能测试"""

import sys
import time
import random
from collections import defaultdict

sys.path.insert(0, '.')

# 原始实现模拟
def original_chapter_matching(combined_text: str, _INTEREST_TO_CHAPTERS: dict, _GENERIC_KWS: set):
    """原始实现：双重循环匹配"""
    matched_chapters = set()
    for kw, chapters in _INTEREST_TO_CHAPTERS.items():
        if kw in _GENERIC_KWS:
            continue
        if kw in combined_text:
            matched_chapters.update(chapters)
    return matched_chapters

# 进一步优化：使用预计算的反向索引
def build_reverse_index(_INTEREST_TO_CHAPTERS: dict, _GENERIC_KWS: set):
    """构建字符→关键词→章节的反向索引"""
    char_index = defaultdict(list)  # char -> list of (kw, chapters)
    for kw, chapters in _INTEREST_TO_CHAPTERS.items():
        if kw in _GENERIC_KWS:
            continue
        for c in kw:
            char_index[c].append((kw, chapters))
    return char_index

def optimized_chapter_matching(combined_text: str, char_index: dict):
    """优化实现：使用反向索引，避免全量遍历"""
    matched_chapters = set()
    processed_kws = set()
    
    for c in combined_text:
        if c in char_index:
            for kw, chapters in char_index[c]:
                if kw not in processed_kws:
                    processed_kws.add(kw)
                    if kw in combined_text:
                        matched_chapters.update(chapters)
    return matched_chapters

# 关键词属性检测优化
def original_attr_detection(combined_text: str):
    """原始实现：多次any()调用"""
    attr = "category"
    if any(kw in combined_text for kw in ["活动", "体验", "参加", "研学", "线下", "现场"]):
        attr = "scene"
    elif any(kw in combined_text for kw in ["华东", "华南", "华北", "西南", "地区", "地方", "省", "国际", "海外"]):
        attr = "region"
    elif any(kw in combined_text for kw in ["申报", "保护", "法律", "制度", "名录", "传承人", "政策"]):
        attr = "general"
    return attr

# 优化后：使用字典映射
_ATTR_KEYWORDS = {
    "scene": ["活动", "体验", "参加", "研学", "线下", "现场"],
    "region": ["华东", "华南", "华北", "西南", "地区", "地方", "省", "国际", "海外"],
    "general": ["申报", "保护", "法律", "制度", "名录", "传承人", "政策"],
}

def optimized_attr_detection(combined_text: str):
    """优化实现：单次遍历"""
    for attr, keywords in _ATTR_KEYWORDS.items():
        for kw in keywords:
            if kw in combined_text:
                return attr
    return "category"

# 性能测试
def run_performance_test():
    """CRS循环优化性能测试"""
    print("=" * 70)
    print("CRS算法循环优化性能测试")
    print("=" * 70)
    
    # 构建测试数据
    _INTEREST_TO_CHAPTERS = {
        "苏绣": ["传统工艺", "传统美术"],
        "昆曲": ["戏曲与表演艺术", "传统音乐"],
        "端午节": ["民俗与节俗"],
        "中医": ["传统医药"],
        "剪纸": ["传统工艺", "传统美术"],
        "书法": ["传统美术"],
        "古琴": ["传统音乐"],
        "太极": ["传统体育"],
        "云锦": ["传统工艺"],
        "皮影": ["戏曲与表演艺术"],
        "粤绣": ["传统工艺"],
        "蜀绣": ["传统工艺"],
        "湘绣": ["传统工艺"],
        "京剧": ["戏曲与表演艺术"],
        "越剧": ["戏曲与表演艺术"],
        "古筝": ["传统音乐"],
        "琵琶": ["传统音乐"],
        "南音": ["传统音乐"],
        "宣纸": ["传统工艺"],
        "紫砂": ["传统工艺"],
        "龙泉青瓷": ["传统工艺"],
        "景泰蓝": ["传统工艺"],
        "年画": ["传统美术"],
        "木版年画": ["传统美术"],
        "竹编": ["传统工艺"],
        "陶瓷": ["传统工艺"],
        "春节": ["民俗与节俗"],
        "清明": ["民俗与节俗"],
        "中秋": ["民俗与节俗"],
        "武术": ["传统体育"],
        "针灸": ["传统医药"],
        "唐卡": ["传统美术"],
        "热贡": ["传统美术"],
        "藏戏": ["戏曲与表演艺术"],
        "四大名绣": ["传统工艺"],
        "非遗传承人": ["民俗与节俗"],
        "联合国非遗": ["民俗与节俗"],
    }
    
    _GENERIC_KWS = {"非遗", "文化", "传统", "中国"}
    
    # 测试文本
    test_texts = [
        "苏绣有什么特点？",
        "我想了解昆曲的历史",
        "端午节有哪些习俗",
        "中医针灸的原理是什么",
        "推荐一些传统工艺相关的内容",
        "苏州的非遗项目有哪些",
        "我想参加线下体验活动",
        "华南地区的非遗文化",
        "非遗保护政策有哪些",
        "剪纸艺术的历史渊源",
    ]
    
    # 构建反向索引
    char_index = build_reverse_index(_INTEREST_TO_CHAPTERS, _GENERIC_KWS)
    
    # 测试章节匹配优化
    print("\n【测试1】章节匹配优化")
    print("-" * 50)
    
    # 预热
    for text in test_texts:
        original_chapter_matching(text, _INTEREST_TO_CHAPTERS, _GENERIC_KWS)
        optimized_chapter_matching(text, char_index)
    
    # 性能测试
    iterations = 10000
    
    start = time.time()
    for _ in range(iterations):
        for text in test_texts:
            original_chapter_matching(text, _INTEREST_TO_CHAPTERS, _GENERIC_KWS)
    t1 = time.time() - start
    
    start = time.time()
    for _ in range(iterations):
        for text in test_texts:
            optimized_chapter_matching(text, char_index)
    t2 = time.time() - start
    
    print("原始实现: {:.4f}s".format(t1))
    print("优化实现: {:.4f}s (提升 {:.1f}%)".format(t2, (1 - t2/t1) * 100))
    
    # 验证正确性
    print("\n【验证】结果一致性检查")
    all_match = True
    for text in test_texts:
        r1 = original_chapter_matching(text, _INTEREST_TO_CHAPTERS, _GENERIC_KWS)
        r2 = optimized_chapter_matching(text, char_index)
        if r1 != r2:
            print("  [FAIL] {}: {} != {}".format(text, r1, r2))
            all_match = False
        else:
            print("  [OK] {}".format(text))
    
    if all_match:
        print("  [OK] 所有测试用例结果一致")
    
    # 测试属性检测优化
    print("\n【测试2】属性检测优化")
    print("-" * 50)
    
    start = time.time()
    for _ in range(iterations):
        for text in test_texts:
            original_attr_detection(text)
    t1 = time.time() - start
    
    start = time.time()
    for _ in range(iterations):
        for text in test_texts:
            optimized_attr_detection(text)
    t2 = time.time() - start
    
    print("原始实现: {:.4f}s".format(t1))
    print("优化实现: {:.4f}s (提升 {:.1f}%)".format(t2, (1 - t2/t1) * 100))
    
    # 验证正确性
    print("\n【验证】属性检测结果")
    for text in test_texts:
        r1 = original_attr_detection(text)
        r2 = optimized_attr_detection(text)
        status = "[OK]" if r1 == r2 else "[FAIL]"
        print("  {} {} -> {}".format(status, text, r1))
    
    print("\n" + "=" * 70)
    print("测试完成!")

if __name__ == "__main__":
    run_performance_test()