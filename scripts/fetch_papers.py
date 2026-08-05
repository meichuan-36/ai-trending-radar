import requests, json, os, sys

OUTPUT_PATH = "docs/data/papers_trending.json"
LIMIT = 20

url = "https://paperswithcode.com/api/v1/papers/"
params = {
    "ordering": "-github_stars",
    "page_size": LIMIT
}

# Use browser-like headers to avoid being served an HTML page instead of JSON
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

try:
    resp = requests.get(url, params=params, timeout=30, headers=HEADERS)
    print(f"HTTP 状态码: {resp.status_code}")
    # 打印响应前1000个字符，用于调试（如果很大只看前面）
    text_preview = resp.text[:1000] if resp.text else "[空响应]"
    print(f"响应预览: {text_preview}")

    if resp.status_code != 200:
        print(f"❌ Papers With Code API 返回非 200 状态码，内容：{resp.text[:500]}")
        sys.exit(1)

    # 如果服务器没有返回 JSON 的 content-type，额外提示
    ctype = resp.headers.get("Content-Type", "")
    if "application/json" not in ctype.lower():
        # 尝试解析为 JSON，但如果失败，则抛出更明确的错误
        try:
            data = resp.json()
        except Exception:
            raise ValueError(f"响应的 Content-Type 不是 JSON: {ctype}. 服务器返回了 HTML 或其它内容，可能被屏蔽或需要不同的 headers.")
    else:
        data = resp.json()

    papers = data.get("results", [])
    simplified = []
    for p in papers:
        simplified.append({
            "id": str(p.get("id")),
            "name": p.get("title", "Unknown"),
            "url": p.get("url_abs") or f"https://paperswithcode.com/paper/{p.get('id')}",
            "description": (p.get("abstract") or "")[:200],
            "stars": p.get("github_stars", 0) or 0,
            "language": "Paper",
            "topics": [t.get("name") for t in p.get("tasks", [])],
            "domain": "PapersWithCode"
        })

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(simplified, f, indent=2, ensure_ascii=False)
    print(f"✅ Papers With Code 热点论文已保存 {len(simplified)} 篇")

except Exception as e:
    # 更明确地打印出引发错误的类型/信息和部分响应体，方便调试
    print(f"❌ 抓取 Papers With Code 失败：{e}")
    try:
        # 如果 resp 可用，打印 content-type 和前 1000 字符帮助诊断
        if 'resp' in locals():
            print(f"响应 Content-Type: {resp.headers.get('Content-Type')}")
            print(f"响应（前 1000 字符）:\n{resp.text[:1000]}")
    except Exception:
        pass
    # 创建一个空数组占位，防止网站加载失败
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)
    print(f"⚠️ 已生成空数组占位文件 {OUTPUT_PATH}")
