import requests, json, os
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from record_history import record_history

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
OUTPUT_PATH = "docs/data/trending.json"
HISTORY_PATH = "docs/data/history_weekly.json"
PER_DOMAIN = 10

one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
# 用于历史记录的日期（本周六的日期，方便统一）
today = datetime.now(timezone.utc)
this_saturday = today + timedelta(days=(5 - today.weekday() + 7) % 7)
date_key = this_saturday.strftime("%Y-%m-%d")

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
    top_domain = sorted(domain_repos.values(), key=lambda x: x["stars"], reverse=True)[:PER_DOMAIN]
    for repo in top_domain:
        rid = repo["id"]
        if rid not in all_repos:
            all_repos[rid] = repo

sorted_repos = sorted(all_repos.values(), key=lambda x: x["stars"], reverse=True)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(sorted_repos, f, indent=2, ensure_ascii=False)

print(f"✅ 本周热榜已保存 {len(sorted_repos)} 个仓库")

# ---------- 历史存档 ----------
history = {}
if os.path.exists(HISTORY_PATH):
    with open(HISTORY_PATH, "r") as f:
        try:
            history = json.load(f)
        except:
            pass
# 保存当前周
history[date_key] = sorted_repos
# 只保留最近 12 个条目
history = dict(sorted(history.items())[-12:])
with open(HISTORY_PATH, "w") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)
print(f"📅 历史周榜已更新，当前共 {len(history)} 周记录")

record_history(sorted_repos, "docs/data/history.json")
