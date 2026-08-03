import requests, json, os
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from record_history import record_history

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
OUTPUT_PATH = "docs/data/trending.json"
TOP_N = 30

one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

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
    full_query = f"{query} created:>={one_week_ago}"
    params = {"q": full_query, "sort": "stars", "order": "desc", "per_page": 10}
    resp = session.get(url, headers=HEADERS, params=params)
    if resp.status_code == 200:
        return resp.json().get("items", [])
    else:
        print(f"Query failed: {query}, status {resp.status_code}")
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

sorted_repos = sorted(all_repos.values(), key=lambda x: x["stars"], reverse=True)[:TOP_N]

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(sorted_repos, f, indent=2, ensure_ascii=False)

print(f"✅ 保存了 {len(sorted_repos)} 个热门仓库到 {OUTPUT_PATH}")
record_history(sorted_repos, "docs/data/history.json")
