from pathlib import Path
from lxml import etree
import re

xml_path=Path(r'd:\桌面\毕业设计\论文正文\unpacked_thesis\word\document.xml')
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{%s}'%ns['w']
root=etree.parse(str(xml_path)).getroot()
body=root.find('.//w:body',ns)
children=list(body)

def text(el):
    return ''.join(el.xpath('.//w:t/text()',namespaces=ns)).strip()

def find_exact(title):
    t=re.sub(r'\s+','',title)
    for i,ch in enumerate(children):
        if re.sub(r'\s+','',text(ch))==t:
            return i
    return -1

ranges=[
 ('第四章', '4 系统设计', '5 系统实现'),
 ('第五章', '5 系统实现', '6 系统测试与实验分析'),
 ('第六章', '6 系统测试与实验分析', '7 结论与展望'),
 ('第七章', '7 结论与展望', '参考文献'),
]
for name,start,end in ranges:
    s=find_exact(start); e=find_exact(end)
    seg=children[s:e]
    p_count=sum(1 for x in seg if x.tag==W+'p')
    tbl_count=sum(1 for x in seg if x.tag==W+'tbl')
    draw_count=len([1 for x in seg if x.xpath('.//*[local-name()="drawing"]')])
    figure_caption=sum(1 for x in seg if x.tag==W+'p' and re.search(r'^(图\d+|如图\d+|图\s*\d+)', text(x)))
    table_caption=sum(1 for x in seg if x.tag==W+'p' and re.search(r'^(表\d+|如表\d+|表\s*\d+)', text(x)))
    md_ticks=sum(1 for x in seg if '`' in text(x) or '|' in text(x))
    print(f'[{name}] p={p_count} tbl={tbl_count} drawing={draw_count} figcap={figure_caption} tblcap={table_caption} md_markers={md_ticks}')
    for x in seg:
        tx=text(x)
        if ('`' in tx or ('|' in tx and len(tx)<300)) and tx:
            print('  marker:', tx[:180])
