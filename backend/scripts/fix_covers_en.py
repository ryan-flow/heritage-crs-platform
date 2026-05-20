"""
Fetch Pixabay images using English keywords (translated from Chinese titles).
Replaces ALL content covers with better-matched images.
"""
import json, sqlite3, os, sys, time, ssl, urllib.request, urllib.parse
from pathlib import Path

DRY_RUN = "--dry-run" in sys.argv

PIXABAY_KEY = "55468384-6826bf941c33f15394e137805"
DB = Path("d:/桌面/毕业设计/backend/heritage_platform.db")
COVERS_DIR = Path("d:/桌面/毕业设计/backend/storage/covers")
ctx = ssl.create_default_context()

# Chinese → English keyword mapping for heritage topics
TRANSLATE = {
    "昆曲": "Kunqu opera Chinese", "戏曲": "Chinese opera performance",
    "京剧": "Peking opera Beijing", "粤剧": "Cantonese opera",
    "藏戏": "Tibetan opera", "皮影": "shadow puppetry Chinese",
    "木偶戏": "puppet show Chinese", "剪纸": "paper cutting art",
    "云锦": "Chinese brocade silk fabric", "苏绣": "Suzhou embroidery",
    "刺绣": "Chinese embroidery", "陶瓷": "Chinese porcelain ceramic",
    "紫砂": "purple clay teapot Yixing", "青花瓷": "blue white porcelain",
    "景德镇": "Jingdezhen porcelain", "书法": "Chinese calligraphy",
    "国画": "Chinese ink painting", "中医": "traditional Chinese medicine",
    "针灸": "acupuncture treatment", "艾灸": "moxibustion Chinese medicine",
    "本草": "Chinese herbal medicine", "端午": "dragon boat festival",
    "春节": "Chinese New Year", "中秋": "Mid-Autumn festival",
    "节气": "24 solar terms China", "二十四节气": "solar terms China",
    "茶": "Chinese tea culture", "茶文化": "Chinese tea ceremony",
    "古琴": "guqin Chinese instrument", "古筝": "guzheng Chinese instrument",
    "琵琶": "pipa Chinese instrument", "二胡": "erhu Chinese instrument",
    "武术": "Chinese martial arts", "太极": "Tai Chi China",
    "太极拳": "Tai Chi martial art", "功夫": "Kung Fu China",
    "敦煌": "Dunhuang Mogao Grottoes", "壁画": "Chinese mural painting",
    "建筑": "Chinese architecture", "园林": "Chinese garden Suzhou",
    "灯彩": "Chinese lantern festival", "龙舟": "dragon boat race",
    "舞龙": "Chinese dragon dance", "舞狮": "Chinese lion dance",
    "年画": "Chinese New Year painting", "木版年画": "woodblock print Chinese",
    "漆器": "Chinese lacquerware", "玉雕": "Chinese jade carving",
    "木雕": "Chinese wood carving", "石雕": "Chinese stone carving",
    "竹编": "Chinese bamboo weaving", "编织": "Chinese weaving craft",
    "染织": "Chinese textile dyeing", "织锦": "Chinese brocade fabric",
    "唐卡": "Thangka Tibetan painting", "傩戏": "Nuo opera Chinese",
    "评弹": "Pingtan Chinese storytelling", "相声": "Chinese cross talk",
    "杂技": "Chinese acrobatics", "民歌": "Chinese folk song",
    "舞蹈": "Chinese folk dance", "汉服": "Hanfu Chinese clothing",
    "香道": "Chinese incense ceremony", "插花": "Chinese flower arrangement",
    "围棋": "Go board game China", "象棋": "Chinese chess",
    "造纸": "Chinese papermaking", "印刷": "Chinese printing",
    "火药": "gunpowder China", "指南针": "compass navigation China",
    "非遗": "intangible cultural heritage China",
    "传统文化": "traditional Chinese culture",
    "手工艺": "Chinese handicraft artisan",
    "入门": "beginner guide introduction",
    "攻略": "guide tips experience",
    "避坑": "tips advice experience",
    "踩坑": "experience lessons learned",
    "第一次": "first time beginner",
    "体验": "experience activity",
    "工坊": "workshop artisan craft",
    "公开": "open public event",
    "周末": "weekend activity event",
    "雅集": "elegant gathering Chinese",
    "导赏": "guided tour exhibition",
    "历史": "history ancient China",
    "传承": "inheritance tradition Chinese",
    "创新": "innovation modern Chinese",
    "手记": "notes documentary China",
    "走访": "field visit travel China",
    "难在哪": "challenge difficulty guide",
    "什么": "what how guide introduction",
    "了解": "learn understand guide",
    "全方位": "comprehensive complete guide",
    "进阶": "advanced guide next level",
    "指南": "guide tutorial how to",
    "流程": "step by step process",
    "区别": "difference comparison vs",
    "鉴赏": "appreciation art guide",
}

def to_english(title: str) -> str:
    """Translate Chinese title to English search keywords."""
    terms = []
    for zh, en in TRANSLATE.items():
        if zh in title and en not in terms:
            terms.append(en)
    if terms:
        # Take top 3 most specific matches
        return " ".join(terms[:3])
    # Fallback: use first meaningful characters
    # Remove quotes and punctuation
    clean = title.replace("'", "").replace('"', "").replace("：", " ").replace("，", " ")
    words = clean.split()
    # Just use first few words
    kw = " ".join(words[:3])
    return f"{kw} China cultural"


def search_pixabay(query: str) -> str | None:
    params = urllib.parse.urlencode({
        "key": PIXABAY_KEY, "q": query.strip(),
        "image_type": "photo", "orientation": "horizontal",
        "safesearch": "true",
    })
    url = f"https://pixabay.com/api/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HeritageCRS/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            hits = json.loads(resp.read()).get("hits", [])
            if hits:
                return hits[0]["webformatURL"]
    except Exception as e:
        print(f"  Search error: {e}")
    return None


def main():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Get ALL published contents
    c.execute("SELECT id, title, cover_url FROM contents WHERE status='published' ORDER BY id")
    items = c.fetchall()
    print(f"Total published contents: {len(items)}\n")

    fixed = 0
    failed = 0
    for i, (cid, title, old_cover) in enumerate(items):
        print(f"[{i+1}/{len(items)}] ID={cid}: {title[:40]}...", end=" ")
        sys.stdout.flush()

        eng = to_english(title)
        print(f"→ '{eng[:50]}'", end=" ")
        sys.stdout.flush()

        img_url = search_pixabay(eng)
        if not img_url:
            # Try even simpler: just the main topic word
            simple = eng.split()[:3]
            simple = [w for w in simple if w not in ("Chinese", "China", "guide", "art")]
            if simple:
                img_url = search_pixabay(" ".join(simple))

        if img_url:
            try:
                filename = f"pixabay_{cid}_{int(time.time())}.jpg"
                filepath = COVERS_DIR / filename
                req2 = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=20, context=ctx) as resp2:
                    data = resp2.read()
                if len(data) > 5000:
                    filepath.write_bytes(data)
                    cover_path = f"/storage/covers/{filename}"
                    c.execute("UPDATE contents SET cover_url=? WHERE id=?", (cover_path, cid))
                    conn.commit()
                    print(f"✅ {len(data)//1024}KB")
                    fixed += 1
                else:
                    print("⚠️ too small")
                    failed += 1
            except Exception as e:
                print(f"❌ download: {e}")
                failed += 1
        else:
            print("❌ no match")
            failed += 1

        time.sleep(0.6)  # Rate limit

    conn.close()
    print(f"\nDone: {fixed} fixed, {failed} failed (out of {len(items)})")


if __name__ == "__main__":
    main()
