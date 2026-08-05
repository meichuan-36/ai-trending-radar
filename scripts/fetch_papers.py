import requests, json, os

OUTPUT_PATH = "docs/data/papers_trending.json"
LIMIT = 20

url = "https://paperswithcode.com/api/v1/papers/"
params = {
    "ordering": "-github_stars",
    "page_size": LIMIT
}

try:
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 200:
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
    else:
        print(f"❌ Papers With Code API 错误：{resp.status_code}")
except Exception as e:
    print(f"❌ 抓取 Papers With Code 失败：{e}")
