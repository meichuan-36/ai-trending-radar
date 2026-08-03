import json, os
from datetime import datetime, timezone

def generate_rss(json_path="docs/data/trending.json", output_path="docs/feed.xml", title_prefix="本周热榜"):
    with open(json_path, "r") as f:
        repos = json.load(f)
    items_xml = ""
    for repo in repos:
        pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        items_xml += f"""
        <item>
            <title>{repo['name']} - 🌟 {repo['stars']}</title>
            <link>{repo['url']}</link>
            <description>{repo.get('description','')}</description>
            <pubDate>{pub_date}</pubDate>
            <guid>{repo['url']}</guid>
        </item>"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>AI 开源项目热榜</title>
    <link>https://meichuan-36.github.io/ai-trending-radar/</link>
    <description>{title_prefix} · 自动更新</description>
    <language>zh-cn</language>
    <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
    {items_xml}
</channel>
</rss>"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(rss)

if __name__ == "__main__":
    generate_rss()
