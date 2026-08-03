import requests, json, os
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from record_history import record_history

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
OUTPUT_PATH = "docs/data/trending.json"
PER_DOMAIN = 10   # 每个领域保留数量

one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

# 领域分组（你可以自由增删改）
domains = {
    "ComfyUI": ["topic:comfyui", "comfyui", "comfyui-workflow"],
    "Stable Diffusion": ["topic:stable-diffusion", "stable-diffusion-webui", "sd-webui"],
    "图像生成": ["topic:image-generation", "text-to-image", "image-generation", "diffusers"],
    "Blender": ["topic:blender", "blender", "blender-addon", "blender-python"],
    "视频生成": ["ai+video+generation", "text-to-video", "animate-diffusion", "video-diffusion"],
    "ControlNet": ["controlnet", "controlnet-aux"],
    "LoRA/微调": ["lora", "finetune", "ip-adapter", "textual-inversion"],
    "提示词工程": ["prompt-engineering", "prompt-generator", "prompt-optimizer"],
    "大语言模型": ["topic:llm", "langchain", "autogen", "crewai", "rag", "embedding"],
    "音频/语音": ["whisper", "tts", "voice-cloning", "audio-generation"],
    "3D/NeRF": ["3d-generation", "nerf", "gaussian-splatting"],
    "其他AI工具": ["topic:huggingface", "topic:deep-learning", "ai-art", "openai-api", "super-resolution", "style-transfer", "vlm", "multimodal"]
}

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
# 按领域抓取
for domain_name, queries in domains.items():
    domain_repos = {}
    for q in queries:
        for repo in search_github(q):
            rid = repo["id"]
            if rid not in domain_repos:
                domain_repos[rid] = {
                    "id": repo["id"],
                    "name": repo["full_name"],
                    "url": repo["html_url"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "language": repo["language"],
                    "created_at": repo["created_at"],
                    "topics": repo.get("topics", []),
                    "domain": domain_name
                }
    # 该领域内按星标排序，取前 PER_DOMAIN
    top_domain = sorted(domain_repos.values(), key=lambda x: x["stars"], reverse=True)[:PER_DOMAIN]
    for repo in top_domain:
        rid = repo["id"]
        if rid not in all_repos:
            all_repos[rid] = repo

# 总体按星标排序（保证整体热度顺序，但每个领域已有代表）
sorted_repos = sorted(all_repos.values(), key=lambda x: x["stars"], reverse=True)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(sorted_repos, f, indent=2, ensure_ascii=False)

print(f"✅ 保存了 {len(sorted_repos)} 个热门仓库（覆盖 {len(domains)} 个领域）到 {OUTPUT_PATH}")
record_history(sorted_repos, "docs/data/history.json")
