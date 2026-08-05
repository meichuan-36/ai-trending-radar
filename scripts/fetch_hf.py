import requests, json, os
from datetime import datetime, timezone

OUTPUT_PATH = "docs/data/hf_trending.json"
LIMIT = 20

url = "https://huggingface.co/api/models"
params = {
    "sort": "downloads",
    "direction": "-1",
    "limit": LIMIT,
    "full": "true"
}

try:
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 200:
        models = resp.json()
        simplified = []
        for m in models:
            simplified.append({
                "id": m.get("modelId"),
                "name": m.get("modelId"),
                "url": f"https://huggingface.co/{m.get('modelId')}",
                "description": m.get("pipeline_tag", "Model"),
                "stars": m.get("downloads", 0),
                "language": m.get("pipeline_tag", "N/A"),
                "topics": m.get("tags", []),
                "domain": "HuggingFace"
            })
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(simplified, f, indent=2, ensure_ascii=False)
        print(f"✅ Hugging Face 热门模型已保存 {len(simplified)} 个")
    else:
        print(f"❌ Hugging Face API 错误：{resp.status_code}")
except Exception as e:
    print(f"❌ 抓取 Hugging Face 失败：{e}")
