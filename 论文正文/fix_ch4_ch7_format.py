from pathlib import Path
from lxml import etree
import re, random

base = Path(r'd:\桌面\毕业设计\论文正文')
xml_path = base / 'unpacked_thesis' / 'word' / 'document.xml'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'w14': 'http://schemas.microsoft.com/office/word/2010/wordml'}
W = '{%s}' % ns['w']
W14 = '{%s}' % ns['w14']

parser = etree.XMLParser(remove_blank_text=False)
root = etree.parse(str(xml_path), parser).getroot()
body = root.find('.//w:body', ns)

def txt(el):
    return ''.join(el.xpath('.//w:t/text()', namespaces=ns)).strip()

def norm(s):
    return re.sub(r'\s+', '', s)

def find_idx(title):
    t = norm(title)
    cur = list(body)
    for i, ch in enumerate(cur):
        if norm(txt(ch)) == t:
            return i
    raise ValueError(f'not found: {title}')

def make_rpr(font='宋体', sz='24', bold=False):
    rPr = etree.Element(W + 'rPr')
    etree.SubElement(rPr, W + 'rFonts', attrib={W + 'ascii': 'Times New Roman', W + 'hAnsi': 'Times New Roman', W + 'eastAsia': font})
    if bold:
        etree.SubElement(rPr, W + 'b')
    else:
        etree.SubElement(rPr, W + 'b', attrib={W + 'val': '0'})
    etree.SubElement(rPr, W + 'sz', attrib={W + 'val': sz})
    return rPr

def make_para(text, centered=False, bold=False, sz='24', indent=True):
    p = etree.Element(W + 'p', attrib={W14 + 'paraId': ''.join(random.choice('0123456789ABCDEF') for _ in range(8))})
    pPr = etree.SubElement(p, W + 'pPr')
    etree.SubElement(pPr, W + 'snapToGrid')
    etree.SubElement(pPr, W + 'spacing', attrib={W + 'beforeAutospacing': '0', W + 'after': '0', W + 'afterAutospacing': '0', W + 'line': '288', W + 'lineRule': 'auto'})
    etree.SubElement(pPr, W + 'ind', attrib={W + 'left': '0', W + 'leftChars': '0', W + 'right': '0', W + 'rightChars': '0', W + 'firstLine': '482' if indent else '0', W + 'firstLineChars': '0'})
    etree.SubElement(pPr, W + 'jc', attrib={W + 'val': 'center' if centered else 'both'})
    pPr.append(make_rpr('宋体', sz, bold))
    r = etree.SubElement(p, W + 'r')
    r.append(make_rpr('宋体', sz, bold))
    t = etree.SubElement(r, W + 't')
    t.text = text
    return p

# backup
backup = xml_path.with_suffix('.xml.bak_format_fix')
if not backup.exists():
    backup.write_text(xml_path.read_text(encoding='utf-8'), encoding='utf-8')

# remove markdown backticks in chapters 4-7
ranges = [
    ('4 系统设计', '5 系统实现'),
    ('5 系统实现', '6 系统测试与实验分析'),
    ('6 系统测试与实验分析', '7 结论与展望'),
    ('7 结论与展望', '参考文献'),
]
replaced_ticks = 0
for start, end in ranges:
    cur = list(body)
    s = find_idx(start)
    e = find_idx(end)
    for el in cur[s:e]:
        for t in el.xpath('.//w:t', namespaces=ns):
            if t.text and '`' in t.text:
                count = t.text.count('`')
                t.text = t.text.replace('`', '')
                replaced_ticks += count

# insert table lead-ins and captions
caption_map = {
    '5 系统实现': [
        ('如表5-1所示，本系统开发环境与工具配置如下。', '表5-1 开发环境'),
    ],
    '6 系统测试与实验分析': [
        ('如表6-1所示，系统测试硬件环境配置如下。', '表6-1 硬件环境'),
        ('如表6-2所示，系统测试软件环境配置如下。', '表6-2 软件环境'),
        ('如表6-3所示，内容展示与检索功能测试结果如下。', '表6-3 内容展示与检索功能测试'),
        ('如表6-4所示，推荐功能测试结果如下。', '表6-4 推荐功能测试'),
        ('如表6-5所示，AI数字人与CRS对话功能测试结果如下。', '表6-5 AI数字人与CRS对话功能测试'),
        ('如表6-6所示，活动、讨论与用户功能测试结果如下。', '表6-6 活动、讨论与用户功能测试'),
        ('如表6-7所示，推荐效果实验的对比策略如下。', '表6-7 推荐效果实验对比策略'),
        ('如表6-8所示，推荐效果实验结果如下。', '表6-8 推荐效果实验结果'),
        ('如表6-9所示，CRS冷启动实验策略设置如下。', '表6-9 CRS冷启动实验策略设置'),
        ('如表6-10所示，CRS冷启动实验结果如下。', '表6-10 CRS冷启动实验结果'),
        ('如表6-11所示，知识图谱增强实验配置如下。', '表6-11 知识图谱增强实验配置'),
        ('如表6-12所示，知识图谱增强实验结果如下。', '表6-12 知识图谱增强实验结果'),
    ],
}
inserted = 0
for chapter, captions in caption_map.items():
    cur = list(body)
    s = find_idx(chapter)
    next_title = '6 系统测试与实验分析' if chapter == '5 系统实现' else '7 结论与展望'
    if chapter == '6 系统测试与实验分析':
        next_title = '7 结论与展望'
    e = find_idx(next_title)
    tbl_positions = [i for i in range(s, e) if cur[i].tag == W + 'tbl']
    for idx, tbl_pos in enumerate(tbl_positions[:len(captions)]):
        lead, cap = captions[idx]
        # current table index may drift after insertions, recalc by locating original table object
        cur2 = list(body)
        target_tbl = cur[tbl_pos]
        pos = cur2.index(target_tbl)
        prev_text = txt(cur2[pos - 1]) if pos - 1 >= 0 else ''
        if '表' in prev_text and cap in prev_text:
            continue
        body.insert(pos, make_para(cap, centered=True, bold=False, sz='21', indent=False))
        body.insert(pos, make_para(lead, centered=False, bold=False, sz='24', indent=True))
        inserted += 2

etree.ElementTree(root).write(str(xml_path), encoding='UTF-8', xml_declaration=True, standalone=None)
print(f'removed_backticks={replaced_ticks}')
print(f'inserted_caption_paragraphs={inserted}')
