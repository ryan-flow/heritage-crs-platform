"""Fetch Pixabay images matching content titles, download and update DB.

Usage: python fix_content_covers_pixabay.py [--dry-run] [--limit N]
"""
import os, sys, json, time, sqlite3, ssl
from pathlib import Path
import urllib.request, urllib.parse

PIXABAY_KEY = "55468384-6826bf941c33f15394e137805"
DB = Path("d:/桌面/毕业设计/backend/heritage_platform.db")
COVERS_DIR = Path("d:/桌面/毕业设计/backend/storage/covers")
API_BASE = "https://pixabay.com/api/"

DRY_RUN = "--dry-run" in sys.argv
LIMIT = None
for i, a in enumerate(sys.argv):
    if a.startswith("--limit="):
        LIMIT = int(a.split("=")[1])

ctx = ssl.create_default_context()

def search_pixabay(query):
    """Search Pixabay for the best image matching the query."""
    # Remove quotes, clean up
    q = query.replace("'", "").replace('"', "").split("：")[0].split("，")[0]
    # Try Chinese + English keywords
    keywords = q.strip()
    if len(keywords) > 40:
        keywords = keywords[:40]

    params = urllib.parse.urlencode({
        "key": PIXABAY_KEY,
        "q": keywords,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "per_page": 3,
    })
    url = f"{API_BASE}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HeritageCRS/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read())
            hits = data.get("hits", [])
            if hits:
                return hits[0]["webformatURL"]  # ~640x360, good enough for covers
    except Exception as e:
        print(f"  Pixabay error: {e}")
    return None

def main():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Get all contents that use _1.jpg (AI-generated) or have no good cover
    c.execute("""
        SELECT id, title, cover_url
        FROM contents
        WHERE (cover_url LIKE '%_1.jpg' OR cover_url IS NULL OR cover_url = '')
        AND status = 'published'
        ORDER BY id
    """)
    items = c.fetchall()
    print(f"Found {len(items)} items to fix\n")

    if DRY_RUN:
        for i, (cid, title, cover) in enumerate(items):
            if LIMIT and i >= LIMIT: break
            print(f"  [{cid}] {title[:40]} → {cover}")
        print(f"\nDry-run: {len(items)} items (LIMIT={LIMIT})")
        conn.close()
        return

    success = 0
    failed = 0
    for i, (cid, title, _) in enumerate(items):
        if LIMIT and i >= LIMIT: break

        print(f"[{i+1}/{len(items)}] ID={cid}: {title[:50]}...", end=" ")
        sys.stdout.flush()

        img_url = search_pixabay(title)
        if not img_url:
            # Try just the first meaningful keyword
            first_word = title.split()[0] if title.split() else title
            if len(first_word) > 2:
                print(f"\n  Retry with '{first_word}'...", end=" ")
                sys.stdout.flush()
                img_url = search_pixabay(first_word)

        if img_url:
            # Download
            try:
                filename = f"pixabay_{cid}_{int(time.time())}.jpg"
                filepath = COVERS_DIR / filename
                req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
                    data = resp.read()
                    with open(str(filepath), 'wb') as f:
                        f.write(data)

                if len(data) > 5000:  # Real image
                    cover_path = f"/storage/covers/{filename}"
                    c.execute("UPDATE contents SET cover_url=? WHERE id=?", (cover_path, cid))
                    conn.commit()
                    print(f"OK ({len(data)//1024}KB)")
                    success += 1
                else:
                    filepath.unlink(missing_ok=True)
                    print("too small")
                    failed += 1
            except Exception as e:
                print(f"download failed: {e}")
                failed += 1
        else:
            print("no match")
            failed += 1

        time.sleep(0.5)  # Rate limit

    conn.close()
    print(f"\nDone: {success} OK, {failed} failed")

if __name__ == "__main__":
    main()
