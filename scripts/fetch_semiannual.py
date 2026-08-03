import requests, json, os, time
from datetime import datetime, timedelta, timezone
from collections import Counter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from record_history import record_history

TOKEN = os.getenv("GITHUB_TOKEN")
# include recommended Accept and API version headers
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}
if TOKEN:
    HEADERS["Authorization"] = f"token {TOKEN}"

OUTPUT_PATH = "docs/data/semiannual.json"
TOP_N = 20

six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")

queries = [
    "topic:comfyui",
    "topic:stable-diffusion",
    "topic:image-generation",
    "topic:blender",
    "ai+video+generation",
    "text-to-video",
    "animate-diffusion",
    "blender+addon",
    "blender+python",
    "diffusers",
    "controlnet",
    "ip-adapter",
    "lora",
    "prompt-engineering",
    "topic:huggingface",
    "topic:deep-learning",
    "topic:llm",
    "text-to-image",
    "image-to-video",
    "3d-generation",
    "nerf",
    "gaussian-splatting",
    "ai-art",
    "openai-api",
    "langchain",
    "autogen",
    "crewai",
    "rag",
    "embedding",
    "whisper",
    "tts",
    "voice-cloning",
    "diffusion-models",
    "segmentation",
    "inpainting",
    "super-resolution",
    "style-transfer",
    "ai-upscaler",
    "vlm",
    "multimodal",
]


def search_github(query):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    url = "https://api.github.com/search/repositories"
    full_query = f"{query} created:>={six_months_ago}"
    params = {"q": full_query, "sort": "stars", "order": "desc", "per_page": 10}
    try:
        resp = session.get(url, headers=HEADERS, params=params, timeout=30)
    except Exception as e:
        print(f"Request exception for {query}: {e}")
        return []

    if resp.status_code == 200:
        return resp.json().get("items", [])
    else:
        # diagnostic logging for failures (especially 403 / rate-limit)
        print(f"Query failed: {query}, status {resp.status_code}")
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        print("Response body:", body)
        # helpful headers
        rate_rem = resp.headers.get("X-RateLimit-Remaining")
        rate_reset = resp.headers.get("X-RateLimit-Reset")
        if rate_rem is not None:
            print(f"X-RateLimit-Remaining: {rate_rem}, X-RateLimit-Reset: {rate_reset}")
            if rate_rem == "0":
                print("Rate limit exhausted. Consider using a token with higher quota or spacing requests.")
        if resp.status_code == 403:
            if not TOKEN:
                print("Warning: No GITHUB_TOKEN provided. Set GITHUB_TOKEN (preferably using the built-in secrets.GITHUB_TOKEN in Actions) to avoid 403s.")
            else:
                print("403 received despite token. Token may lack scopes or you're hitting abuse/rate limits.")
        return []


all_repos = {}
for q in queries:
    for repo in search_github(q):
        rid = repo["id"]
        if rid not in all_repos:
            all_repos[rid] = {
                "id": repo["id"],
                "name": repo["full_name"],
                "url": repo["html_url"],
                "description": repo["description"],
                "stars": repo["stargazers_count"],
                "language": repo["language"],
                "created_at": repo["created_at"],
                "topics": repo.get("topics", [])
            }
    # small sleep to reduce chance of rate-limiting/abuse triggering
    time.sleep(0.2)

sorted_repos = sorted(all_repos.values(), key=lambda x: x["stars"], reverse=True)[:TOP_N]

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(sorted_repos, f, indent=2, ensure_ascii=False)

print(f"✅ 半年精选 Top20 已保存 {len(sorted_repos)} 个仓库到 {OUTPUT_PATH}")

# 生成半年总结
summary = {
    "total_repos": len(sorted_repos),
    "avg_stars": round(sum(r['stars'] for r in sorted_repos) / len(sorted_repos), 2) if sorted_repos else 0,
    "top_topics": Counter(t for r in sorted_repos for t in r.get('topics', [])).most_common(5),
    "languages": dict(Counter(r.get('language') for r in sorted_repos if r.get('language')).most_common(5))
}
with open("docs/data/summary.json", "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("✅ 半年总结已生成")

# 动态发现新话题
existing_set = set(queries)
all_topics = Counter()
for r in sorted_repos:
    for t in r.get('topics', []):
        all_topics[t] += 1
new_topics = [(t, c) for t, c in all_topics.most_common(20) if f"topic:{t}" not in existing_set and t not in existing_set]
with open("docs/data/emerging_topics.json", "w") as f:
    json.dump(new_topics, f, indent=2, ensure_ascii=False)
print(f"✅ 发现 {len(new_topics)} 个潜在新话题")

record_history(sorted_repos, "docs/data/history.json")
