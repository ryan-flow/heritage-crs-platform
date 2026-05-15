from pathlib import Path
from lxml import etree
from copy import deepcopy
import re, random

base=Path(r'd:\桌面\毕业设计\论文正文')
xml_path=base/'unpacked_thesis'/'word'/'document.xml'
chapters=[
 ('第一章-绪论.md','1 绪论','2 相关技术与理论基础'),
 ('../第二章-相关技术与理论基础.md','2 相关技术与理论基础','3 系统分析'),
 ('第三章-系统分析.md','3 系统分析','4 系统设计'),
 ('第四章-系统设计.md','4 系统设计','5 系统实现'),
 ('第五章-系统实现.md','5 系统实现','6 系统测试与实验分析'),
 ('第六章-系统测试.md','6 系统测试与实验分析','7 结论与展望'),
 ('第七章-结论与展望.md','7 结论与展望','参考文献'),
]

title_updates={
}

ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','w14':'http://schemas.microsoft.com/office/word/2010/wordml'}
W='{%s}'%ns['w']; W14='{%s}'%ns['w14']
parser=etree.XMLParser(remove_blank_text=False)
root=etree.parse(str(xml_path),parser).getroot()
body=root.find('.//w:body',ns)
children=list(body)


def texts(el):
    return ''.join(el.xpath('.//w:t/text()',namespaces=ns)).strip()

def norm(s):
    return re.sub(r'\s+','',s)

def find_idx(title):
    t=norm(title)
    cur=list(body)
    for i,ch in enumerate(cur):
        if norm(texts(ch))==t:
            return i
    raise ValueError(f'not found: {title}')

def replace_para_text(el,new_text):
    ts=el.xpath('.//w:t',namespaces=ns)
    if not ts:
        return
    ts[0].text=new_text
    for extra in ts[1:]:
        extra.text=''

def make_rpr(font='宋体',sz='24',bold=False):
    rPr=etree.Element(W+'rPr')
    etree.SubElement(rPr,W+'rFonts',attrib={W+'ascii':'Times New Roman',W+'hAnsi':'Times New Roman',W+'eastAsia':font})
    if bold: etree.SubElement(rPr,W+'b')
    else: etree.SubElement(rPr,W+'b',attrib={W+'val':'0'})
    etree.SubElement(rPr,W+'sz',attrib={W+'val':sz})
    return rPr

def p_with_text(text,kind='body'):
    p=etree.Element(W+'p',attrib={W14+'paraId':''.join(random.choice('0123456789ABCDEF') for _ in range(8))})
    pPr=etree.SubElement(p,W+'pPr')
    etree.SubElement(pPr,W+'snapToGrid')
    if kind=='body':
        etree.SubElement(pPr,W+'spacing',attrib={W+'beforeAutospacing':'0',W+'after':'0',W+'afterAutospacing':'0',W+'line':'288',W+'lineRule':'auto'})
        etree.SubElement(pPr,W+'ind',attrib={W+'left':'0',W+'leftChars':'0',W+'right':'0',W+'rightChars':'0',W+'firstLine':'482',W+'firstLineChars':'0'})
        etree.SubElement(pPr,W+'jc',attrib={W+'val':'both'})
        pPr.append(make_rpr('宋体','24',False))
        r=etree.SubElement(p,W+'r'); r.append(make_rpr('宋体','24',False)); t=etree.SubElement(r,W+'t'); t.text=text
        return p
    level='1' if kind=='h2' else '2'
    sz='30' if kind=='h2' else '28'
    etree.SubElement(pPr,W+'spacing',attrib={W+'before':'260',W+'beforeAutospacing':'0',W+'after':'260',W+'afterAutospacing':'0',W+'line':'416',W+'lineRule':'auto'})
    etree.SubElement(pPr,W+'ind',attrib={W+'left':'0',W+'leftChars':'0',W+'right':'0',W+'rightChars':'0',W+'firstLine':'0',W+'firstLineChars':'0'})
    etree.SubElement(pPr,W+'jc',attrib={W+'val':'left'})
    etree.SubElement(pPr,W+'outlineLvl',attrib={W+'val':level})
    pPr.append(make_rpr('黑体',sz,True))
    r=etree.SubElement(p,W+'r'); r.append(make_rpr('黑体',sz,True)); t=etree.SubElement(r,W+'t'); t.text=text
    return p

def table_block(lines):
    rows=[]
    for ln in lines:
        cols=[c.strip() for c in ln.strip().strip('|').split('|')]
        if any(re.fullmatch(r':?-{3,}:?',c) for c in cols):
            continue
        rows.append(cols)
    if not rows: return []
    col_n=max(len(r) for r in rows)
    tbl=etree.Element(W+'tbl')
    tblPr=etree.SubElement(tbl,W+'tblPr')
    etree.SubElement(tblPr,W+'tblStyle',attrib={W+'val':'36'})
    etree.SubElement(tblPr,W+'tblW',attrib={W+'w':'0',W+'type':'auto'})
    etree.SubElement(tblPr,W+'jc',attrib={W+'val':'center'})
    etree.SubElement(tblPr,W+'tblLayout',attrib={W+'type':'autofit'})
    mar=etree.SubElement(tblPr,W+'tblCellMar')
    for side in ['top','left','bottom','right']:
        etree.SubElement(mar,W+side,attrib={W+'w':'108' if side in ['left','right'] else '0',W+'type':'dxa'})
    grid=etree.SubElement(tbl,W+'tblGrid')
    for _ in range(col_n): etree.SubElement(grid,W+'gridCol',attrib={W+'w':str(8312//col_n)})
    for ridx,row in enumerate(rows):
        tr=etree.SubElement(tbl,W+'tr')
        for cidx in range(col_n):
            tc=etree.SubElement(tr,W+'tc'); tcPr=etree.SubElement(tc,W+'tcPr'); etree.SubElement(tcPr,W+'tcW',attrib={W+'w':str(8312//col_n),W+'type':'dxa'})
            p=p_with_text(row[cidx] if cidx<len(row) else '', 'body')
            if ridx==0:
                r=p.find('.//w:r',ns)
                rpr=r.find('w:rPr',ns)
                b=rpr.find('w:b',ns)
                if b is not None: rpr.remove(b)
                rpr.insert(1,etree.Element(W+'b'))
            tc.append(p)
    return [tbl]

def md_to_nodes(path):
    lines=Path(path).read_text(encoding='utf-8').splitlines()
    nodes=[]; i=0
    while i<len(lines):
        ln=lines[i].rstrip()
        s=ln.strip()
        if not s: i+=1; continue
        if s.startswith('# '): i+=1; continue
        if s.startswith('## '): nodes.append(p_with_text(s[3:].strip(),'h2')); i+=1; continue
        if s.startswith('### '): nodes.append(p_with_text(s[4:].strip(),'h3')); i+=1; continue
        if s.startswith('|'):
            buf=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                buf.append(lines[i]); i+=1
            nodes.extend(table_block(buf)); continue
        para=[s]; i+=1
        while i<len(lines):
            t=lines[i].strip()
            if not t or t.startswith('#') or t.startswith('|'): break
            para.append(t); i+=1
        nodes.append(p_with_text(''.join(para),'body'))
    return nodes

backup=xml_path.with_suffix('.xml.bak_md_sync')
if not backup.exists():
    backup.write_text(xml_path.read_text(encoding='utf-8'),encoding='utf-8')

for md,start_t,next_t in reversed(chapters):
    children=list(body)
    orig_start = start_t
    for old_t, new_t in title_updates.items():
        if new_t == start_t:
            orig_start = old_t
            break
    orig_next = next_t
    for old_t, new_t in title_updates.items():
        if new_t == next_t:
            orig_next = old_t
            break
    s=find_idx(orig_start); n=find_idx(orig_next)
    start=children[s]
    to_remove=children[s+1:n]
    for el in to_remove: body.remove(el)
    insert_at=list(body).index(start)+1
    inserted=0
    for node in md_to_nodes(base/md):
        body.insert(insert_at,node); insert_at+=1; inserted+=1
    print(f'replaced {md}: {len(to_remove)} -> {inserted}')

for old_title,new_title in title_updates.items():
    idx=find_idx(old_title)
    replace_para_text(list(body)[idx],new_title)
    print(f'title updated: {old_title} -> {new_title}')

etree.ElementTree(root).write(str(xml_path),encoding='UTF-8',xml_declaration=True,standalone=None)
print('done')
