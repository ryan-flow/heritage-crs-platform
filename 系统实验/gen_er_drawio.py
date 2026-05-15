#!/usr/bin/env python3
"""生成draw.io格式的E-R图 .drawio 文件"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

OUTPUT = r"d:\桌面\毕业设计\论文正文\ER图-系统数据库.drawio"

mxfile = ET.Element("mxfile")
mxfile.set("host", "app.diagrams.net")
diagram = ET.SubElement(mxfile, "diagram")
diagram.set("name", "Page-1")
diagram.set("id", "er-diagram")

mxGraphModel = ET.SubElement(diagram, "mxGraphModel")
root = ET.SubElement(mxGraphModel, "root")
mxCell0 = ET.SubElement(root, "mxCell")
mxCell0.set("id", "0")

mxCell1 = ET.SubElement(root, "mxCell")
mxCell1.set("id", "1")
mxCell1.set("parent", "0")

uid = 2
def uid_gen():
    global uid
    u = str(uid)
    uid += 1
    return u

def add_entity(x, y, w, h, name, attrs, fill="#FFFFFF"):
    id_ = uid_gen()
    cell = ET.SubElement(root, "mxCell")
    cell.set("id", id_)
    cell.set("value", _build_entity_html(name, attrs))
    cell.set("style", f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#333333;strokeWidth=1.5;fontFamily=SimSun;fontSize=9;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;")
    mxGeo = ET.SubElement(cell, "mxGeometry")
    mxGeo.set("x", str(x))
    mxGeo.set("y", str(y))
    mxGeo.set("width", str(w))
    mxGeo.set("height", str(h))
    mxGeo.set("as", "geometry")
    return id_

def add_relation(x, y, name):
    id_ = uid_gen()
    cell = ET.SubElement(root, "mxCell")
    cell.set("id", id_)
    cell.set("value", name)
    cell.set("style", "rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#333333;strokeWidth=1.2;fontFamily=SimSun;fontSize=9;")
    mxGeo = ET.SubElement(cell, "mxGeometry")
    mxGeo.set("x", str(x))
    mxGeo.set("y", str(y))
    mxGeo.set("width", "70")
    mxGeo.set("height", "45")
    mxGeo.set("as", "geometry")
    return id_

def add_edge(src, tgt, label="", label_pos="center", style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;strokeColor=#666666;strokeWidth=1.0;fontFamily=Times New Roman;fontSize=10;"):
    id_ = uid_gen()
    cell = ET.SubElement(root, "mxCell")
    cell.set("id", id_)
    cell.set("edge", "1")
    cell.set("source", src)
    cell.set("target", tgt)
    if label:
        cell.set("value", label)
        cell.set(f"style", style + f";{label_pos}=1;labelBackgroundColor=none;")
    else:
        cell.set("style", style)
    mxGeo = ET.SubElement(cell, "mxGeometry")
    mxGeo.set("relative", "1")
    mxGeo.set("as", "geometry")
    return id_

def _build_entity_html(name, attrs):
    lines = [f'<b>{name}</b>']
    for a in attrs:
        lines.append(a)
    return "<br>".join(lines)

# ===== 实体定义 =====
user = add_entity(480, 200, 160, 220, "用户表",
    ["id (PK)", "openid", "nickname", "phone", "role", "is_active", "confidence_score", "score_explicit", "score_implicit", "score_dialogue", "preferred_heritage_types", "preferred_regions", "preferred_scene_types", "created_at"])

content = add_entity(80, 120, 150, 170, "内容表",
    ["id (PK)", "title", "cover_url", "content_type", "source_site", "summary", "body", "chapter", "sub_chapter", "quality_score", "review_status", "is_featured", "status", "published_at"])

activity = add_entity(80, 350, 140, 145, "活动表",
    ["id (PK)", "title", "cover_url", "location", "organizer", "start_time", "end_time", "max_participants", "description", "is_featured", "status"])

topic = add_entity(80, 550, 140, 125, "讨论话题",
    ["id (PK)", "title", "content", "like_count", "comment_count", "is_featured", "created_at"])

reclog = add_entity(880, 100, 155, 130, "推荐日志",
    ["id (PK)", "action", "target_type", "target_id", "source_scene", "explain_json", "created_at"])

qalog = add_entity(880, 280, 150, 125, "AI问答记录",
    ["id (PK)", "question", "answer", "source", "confidence", "created_at"])

crs = add_entity(880, 450, 140, 110, "CRS会话",
    ["id (PK)", "session_id", "mode", "turn_count", "asked_attributes", "context_summary"])

fav_content = add_entity(80, 720, 120, 60, "内容收藏",
    ["id (PK)", "user_id", "content_id", "created_at"])
reg_activity = add_entity(240, 720, 120, 60, "活动报名",
    ["id (PK)", "activity_id", "user_id", "status", "created_at"])
comment = add_entity(400, 720, 120, 55, "评论",
    ["id (PK)", "topic_id", "user_id", "content", "created_at"])
like_topic = add_entity(540, 720, 115, 50, "点赞",
    ["id (PK)", "topic_id", "user_id", "created_at"])
fav_topic = add_entity(675, 720, 115, 50, "话题收藏",
    ["id (PK)", "topic_id", "user_id", "created_at"])
ask_log = add_entity(820, 720, 135, 65, "CRS提问记录",
    ["id (PK)", "session_id", "ask_id", "attribute", "answer", "score_delta"])

# ===== 关系 =====
r_fav = add_relation(260, 160, "收藏")
r_reg = add_relation(260, 310, "报名")
r_post = add_relation(270, 500, "发帖")
r_cmt = add_relation(290, 560, "评论")
r_like = add_relation(320, 590, "点赞")
r_tfav = add_relation(340, 620, "收藏")
r_rec = add_relation(700, 165, "行为")
r_qa = add_relation(710, 265, "提问")
r_crs = add_relation(720, 380, "参与")
r_ask = add_relation(750, 520, "回答")

# ===== 连线 =====
add_edge(user, r_fav)
add_edge(r_fav, content, "M", "sourceLabel")
add_edge(content, r_fav, "N", "targetLabel")

add_edge(user, r_reg)
add_edge(r_reg, activity, "M", "sourceLabel")
add_edge(activity, r_reg, "N", "targetLabel")

add_edge(user, r_post)
add_edge(r_post, topic, "M", "sourceLabel")
add_edge(topic, r_post, "N", "targetLabel")

add_edge(user, r_rec)
add_edge(r_rec, reclog, "1", "sourceLabel")
add_edge(reclog, r_rec, "M", "targetLabel")

add_edge(user, r_qa)
add_edge(r_qa, qalog, "1", "sourceLabel")
add_edge(qalog, r_qa, "M", "targetLabel")

add_edge(user, r_crs)
add_edge(r_crs, crs, "1", "sourceLabel")
add_edge(crs, r_crs, "1", "targetLabel")

add_edge(user, r_ask)
add_edge(r_ask, ask_log, "1", "sourceLabel")
add_edge(ask_log, r_ask, "M", "targetLabel")

add_edge(topic, r_cmt)
add_edge(r_cmt, comment, "1", "sourceLabel")
add_edge(comment, r_cmt, "N", "targetLabel")

add_edge(topic, r_like)
add_edge(r_like, like_topic, "1", "sourceLabel")
add_edge(like_topic, r_like, "N", "targetLabel")

add_edge(topic, r_tfav)
add_edge(r_tfav, fav_topic, "1", "sourceLabel")
add_edge(fav_topic, r_tfav, "N", "targetLabel")

tree = minidom.parseString(ET.tostring(mxfile, encoding="unicode"))
pretty_xml = tree.toprettyxml(indent="  ")
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print(f".drawio文件已保存: {OUTPUT}")
print("请用draw.io打开此文件即可查看和编辑E-R图")
