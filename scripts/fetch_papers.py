import requests, json, os, sys

OUTPUT_PATH = "docs/data/papers_trending.json"
LIMIT = 20

url = "https://paperswithcode.com/api/v1/papers/"
params = {
    "ordering": "-github_stars",
    "page_size": LIMIT
}

try:
    resp = requests.get(url, params=params, timeout=30)
    print(f"HTTP 状态码: {resp.status_code}")
    # 打印响应前200个字符，用于调试
    text_preview = resp.text[:200] if resp.text else "[空响应]"
    print(f"响应预览: {text_preview}")

    if resp.status_code != 200:
        print(f"❌ Papers With Code API 返回非 200 状态码，内容：{resp.text[:500]}")
        sys.exit(1)

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
    print(f"❌ 抓取 Papers With Code 失败：{e}")
    # 创建一个空数组占位，防止网站加载失败
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)
    print(f"⚠️ 已生成空数组占位文件 {OUTPUT_PATH}")
