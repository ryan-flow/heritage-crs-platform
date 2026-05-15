import re
import html
import httpx


def search_web_brief(question: str, max_items: int = 3) -> str:
    """
    使用公开搜索结果摘要做轻量联网检索。
    仅提取标题/摘要，不抓取全文，避免超时。
    """
    query = question.strip()
    if not query:
        return ""

    url = "https://html.duckduckgo.com/html/"
    params = {"q": f"中国非遗 {query}"}

    with httpx.Client(timeout=12.0, follow_redirects=True) as client:
        resp = client.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        text = resp.text

    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', text, flags=re.S)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', text, flags=re.S)

    merged: list[str] = []
    for i in range(min(max_items, max(len(titles), len(snippets)))):
        t = html.unescape(re.sub(r"<.*?>", "", titles[i] if i < len(titles) else "")).strip()
        s = html.unescape(re.sub(r"<.*?>", "", snippets[i] if i < len(snippets) else "")).strip()
        if t and s:
            merged.append(f"{t}：{s}")
        elif t:
            merged.append(t)
        elif s:
            merged.append(s)

    if not merged:
        return ""

    return "；".join(merged)
