"""Download a Kunqu image from Wikimedia Commons (no API key needed)."""
import os, urllib.request

OUT_DIR = r"d:\桌面\毕业设计\backend\storage\covers"
OUT_FILE = os.path.join(OUT_DIR, "kunqu_cover.jpg")

# Wikimedia Commons Kunqu images — direct download URLs (CC-licensed, free to use with attribution)
URLS = [
    # Kunqu - Dan (female role performer)
    "https://upload.wikimedia.org/wikipedia/commons/a/a5/Kunqu_-_Dan.jpg",
    # 昆曲 performer closeup
    "https://upload.wikimedia.org/wikipedia/commons/8/8b/%E6%98%86%E6%9B%B2.jpg",
    # Kunqu performance Taipei
    "https://upload.wikimedia.org/wikipedia/commons/7/7c/Kunqu_gosterisi_taipei.jpg",
]

for url in URLS:
    try:
        print(f"Trying: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'HeritageCRS/1.0 (educational project; image research)'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(OUT_FILE, 'wb') as f:
                f.write(data)
            size_kb = len(data) / 1024
            if size_kb > 10:  # Must be > 10KB to be a real image
                print(f"OK: {OUT_FILE} ({size_kb:.0f} KB)")
                break
            else:
                print(f"Too small ({size_kb:.0f} KB), trying next...")
    except Exception as e:
        print(f"Failed: {e}")
