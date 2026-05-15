# -*- coding: utf-8 -*-
"""Rebuild activities with balanced category distribution."""
import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.core.database import SessionLocal
from app.models.activity import Activity

ACTIVITY_PLAN = [
    # 传统工艺 (12)
    ("云锦织造体验工坊", "传统工艺"),
    ("龙泉青瓷烧制开放日", "传统工艺"),
    ("宣纸制作技艺观摩", "传统工艺"),
    ("雕版印刷体验课", "传统工艺"),
    ("苏绣针法入门体验", "传统工艺"),
    ("景泰蓝珐琅工艺体验", "传统工艺"),
    ("紫砂壶手作体验", "传统工艺"),
    ("蜡染方巾设计工坊", "传统工艺"),
    ("非遗工艺市集", "传统工艺"),
    ("传统酿造技艺展览", "传统工艺"),
    ("泥人彩塑体验课", "传统工艺"),
    ("陶瓷拉坯体验工坊", "传统工艺"),

    # 戏曲与表演艺术 (12)
    ("昆曲折子戏导赏", "戏曲与表演艺术"),
    ("京剧脸谱绘制体验", "戏曲与表演艺术"),
    ("粤剧身段入门体验", "戏曲与表演艺术"),
    ("藏戏面具彩绘工坊", "戏曲与表演艺术"),
    ("皮影戏制作与操纵体验", "戏曲与表演艺术"),
    ("评弹名家说书夜", "戏曲与表演艺术"),
    ("秦腔经典唱段导赏", "戏曲与表演艺术"),
    ("川剧变脸后台探秘", "戏曲与表演艺术"),
    ("黄梅戏经典唱段学唱", "戏曲与表演艺术"),
    ("越剧才子佳人赏析", "戏曲与表演艺术"),
    ("梨园戏艺术沙龙", "戏曲与表演艺术"),
    ("花鼓戏表演体验夜", "戏曲与表演艺术"),

    # 岁时节庆与民俗 (12)
    ("端午龙舟体验日", "岁时节庆与民俗"),
    ("春节年俗体验展", "岁时节庆与民俗"),
    ("二十四节气生活讲座", "岁时节庆与民俗"),
    ("中秋诗词赏月夜", "岁时节庆与民俗"),
    ("清明踏青非遗体验", "岁时节庆与民俗"),
    ("元宵灯会猜灯谜", "岁时节庆与民俗"),
    ("重阳登高赏菊会", "岁时节庆与民俗"),
    ("妈祖信俗文化展", "岁时节庆与民俗"),
    ("火把节篝火狂欢夜", "岁时节庆与民俗"),
    ("那达慕体育竞技观摩", "岁时节庆与民俗"),
    ("七夕女红手作体验", "岁时节庆与民俗"),
    ("冬至年俗美食工坊", "岁时节庆与民俗"),

    # 传统美术 (12)
    ("中国剪纸入门工坊", "传统美术"),
    ("木版年画印制体验", "传统美术"),
    ("篆刻艺术体验课", "传统美术"),
    ("书法入门体验日", "传统美术"),
    ("唐卡绘制基础工坊", "传统美术"),
    ("刺绣技法体验课", "传统美术"),
    ("内画壶技艺展示", "传统美术"),
    ("杨柳青年画印制体验", "传统美术"),
    ("泥塑人物塑造工坊", "传统美术"),
    ("烙画艺术体验", "传统美术"),
    ("瓷板画绘制体验", "传统美术"),
    ("敦煌壁画临摹体验", "传统美术"),

    # 传统音乐 (10)
    ("古琴雅集入门体验", "传统音乐"),
    ("南音古乐赏析夜", "传统音乐"),
    ("古筝名曲演奏会", "传统音乐"),
    ("江南丝竹雅集", "传统音乐"),
    ("西安鼓乐展演", "传统音乐"),
    ("侗族大歌合唱体验", "传统音乐"),
    ("呼麦喉音工作坊", "传统音乐"),
    ("笛箫合奏雅集", "传统音乐"),
    ("二胡名曲音乐会", "传统音乐"),
    ("昆曲清唱雅会", "传统音乐"),

    # 传统医药 (8)
    ("中医针灸体验讲座", "传统医药"),
    ("中药炮制技艺展示", "传统医药"),
    ("藏医药文化体验", "传统医药"),
    ("中医养生功法体验", "传统医药"),
    ("中医诊法体验日", "传统医药"),
    ("传统膏方展示体验", "传统医药"),
    ("壮医特色疗法体验", "传统医药"),
    ("中医正骨技法展示", "传统医药"),

    # 传承实践 (8)
    ("非遗进校园经验分享会", "传承实践"),
    ("非遗研学导师培训", "传承实践"),
    ("乡村振兴非遗论坛", "传承实践"),
    ("非遗与文旅融合论坛", "传承实践"),
    ("博物馆非遗教育研讨会", "传承实践"),
    ("非遗传承人对谈", "传承实践"),
    ("社区非遗活动策划工坊", "传承实践"),
    ("非遗文创设计大赛", "传承实践"),

    # 保护制度 (6)
    ("非遗法实施十周年论坛", "保护制度"),
    ("国家级非遗名录解读", "保护制度"),
    ("传承人培养经验分享", "保护制度"),
    ("非遗数字化保护论坛", "保护制度"),
    ("非遗生产性保护论坛", "保护制度"),
    ("非遗整体性保护研讨会", "保护制度"),
]

ORGANIZERS = [
    "市文化馆非遗部", "城南社区文化站", "青年非遗志愿团",
    "非遗体验合作社", "公共文化服务中心", "在地工艺研究社",
    "非遗保护中心", "各区文化馆",
]
LOCATIONS = [
    "市文化馆二层体验教室", "老城街区公共空间", "非遗体验馆A区",
    "社区文化活动中心", "滨河展演空间", "城市书房多功能厅",
    "各区文化馆展厅", "市民活动中心",
]

PALETTES = [
    ("#261611", "#8D2A1D"), ("#1E2230", "#7D5A3D"),
    ("#2B1F30", "#A44E34"), ("#1D2A2F", "#7C633E"),
    ("#2E1B18", "#B26C42"),
]

random.seed(20260413)


def make_cover(idx: int, chapter: str, title: str) -> str:
    c1, c2 = random.choice(PALETTES)
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='720' viewBox='0 0 1200 720'>
  <defs><linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
    <stop offset='0%' stop-color='{c1}'/><stop offset='100%' stop-color='{c2}'/>
  </linearGradient></defs>
  <rect width='1200' height='720' fill='url(#bg)' rx='34'/>
  <circle cx='920' cy='140' r='200' fill='rgba(255,255,255,0.08)'/>
  <text x='86' y='122' fill='#FFE4C0' font-size='28' font-family='Microsoft YaHei'>{chapter}</text>
  <text x='86' y='268' fill='#FFF8F0' font-size='56' font-weight='700' font-family='Microsoft YaHei'>活动{idx+1:02d}</text>
  <text x='86' y='336' fill='rgba(255,241,230,0.9)' font-size='26' font-family='Microsoft YaHei'>{title[:20]}</text>
</svg>"""
    cover_dir = BASE_DIR / "storage" / "covers"
    cover_dir.mkdir(parents=True, exist_ok=True)
    path = cover_dir / f"activity_{idx+1:03d}.svg"
    path.write_text(svg, encoding="utf-8")
    return f"/static/covers/activity_{idx+1:03d}.svg"


def main():
    db = SessionLocal()
    try:
        db.query(Activity).delete()
        db.commit()
        print("Cleared all activities")

        base = datetime.now().replace(minute=0, second=0, microsecond=0)
        for idx, (title, chapter) in enumerate(ACTIVITY_PLAN):
            organizer = random.choice(ORGANIZERS)
            location = random.choice(LOCATIONS) + "·" + chapter + "专区"
            # 每月分配3-4个活动，覆盖未来6个月
            month_offset = (idx // 10) % 6
            slot = idx % 10
            start = base.replace(day=1) + timedelta(days=month_offset * 30 + slot * 3 + 3, hours=9 + (slot % 6))
            end = start + timedelta(hours=2 + (slot % 2))
            cover = make_cover(idx, chapter, title)

            a = Activity(
                title=title,
                cover_url=cover,
                location=location,
                organizer=organizer,
                start_time=start,
                end_time=end,
                max_participants=25 + (idx % 6) * 10,
                description=f"本场活动聚焦{chapter}，设置导览+体验+答疑三个环节，适合不同人群参与。",
                notes="请提前15分钟到场；名额有限，请确认时间后报名。",
                status="open" if idx % 10 != 9 else "closed",
                is_featured=(idx < 8),
            )
            db.add(a)

        db.commit()
        print(f"Created {len(ACTIVITY_PLAN)} activities")

        from sqlalchemy import func
        dist = db.query(Activity.category, func.count(Activity.id)).order_by(
            func.count(Activity.id).desc()
        ).all() if hasattr(Activity, 'category') else None

        print("\nDone. Activities rebuilt.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
