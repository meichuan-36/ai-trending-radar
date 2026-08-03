import json, os
from datetime import datetime, timezone

def record_history(data, output_path="docs/data/history.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    history = {}
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            try:
                history = json.load(f)
            except:
                pass
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for repo in data:
        rid = str(repo.get("id"))
        stars = repo.get("stars", 0)
        if rid not in history:
            history[rid] = []
        if history[rid] and history[rid][-1][0] == today:
            continue
        history[rid].append([today, stars])
    with open(output_path, "w") as f:
        json.dump(history, f, indent=2)
