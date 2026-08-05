import requests, json, os, sys, logging, time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Configuration
OUTPUT_PATH = "docs/data/papers_trending.json"
LIMIT = int(os.getenv("FETCH_PAPERS_LIMIT", "20"))
URL = "https://paperswithcode.com/api/v1/papers/"
PARAMS = {
    "ordering": "-github_stars",
    "page_size": LIMIT
}

# Browser-like headers to reduce chance of being served HTML
HEADERS = {
    "User-Agent": os.getenv("FETCH_PAPERS_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://paperswithcode.com/",
    "X-Requested-With": "XMLHttpRequest",
}

# Retry / timeout config (tunable via env)
RETRIES = int(os.getenv("FETCH_PAPERS_RETRIES", "3"))
BACKOFF_FACTOR = float(os.getenv("FETCH_PAPERS_BACKOFF", "0.5"))
STATUS_FORCELIST = [429, 500, 502, 503, 504]
TIMEOUT = int(os.getenv("FETCH_PAPERS_TIMEOUT", "30"))

# Logging
logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_session(retries=RETRIES, backoff=BACKOFF_FACTOR):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=STATUS_FORCELIST,
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch():
    session = get_session()

    try:
        logger.info(f"请求 URL: %s, params: %s", URL, PARAMS)
        resp = session.get(URL, params=PARAMS, timeout=TIMEOUT, headers=HEADERS)
        logger.info("HTTP 状态码: %s", resp.status_code)

        # 打印响应前 2000 字符，方便 CI 日志中排查
        text_preview = resp.text[:2000] if resp.text else "[空响应]"
        logger.debug("响应预览: %s", text_preview)

        if resp.status_code != 200:
            # 打印部分响应体帮助诊断
            logger.error("❌ Papers With Code API 返回非 200 状态码：%s", resp.status_code)
            logger.error("响应前 1000 字：\n%s", resp.text[:1000])
            raise RuntimeError(f"非 200 状态码: {resp.status_code}")

        ctype = resp.headers.get("Content-Type", "")
        logger.info("响应 Content-Type: %s", ctype)

        # 如果 content-type 看起来不是 JSON，尝试解析并给出更明确的错误
        if "application/json" not in ctype.lower():
            try:
                data = resp.json()
            except Exception:
                raise ValueError(f"响应的 Content-Type 不是 JSON: {ctype}. 服务器可能返回 HTML（反爬/验证码），响应前 2000 字: {text_preview}")
        else:
            data = resp.json()

        papers = data.get("results", []) if isinstance(data, dict) else []
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
        logger.info("✅ Papers With Code 热点论文已保存 %s 篇", len(simplified))

    except Exception as e:
        logger.error("❌ 抓取 Papers With Code 失败：%s", e)
        try:
            if 'resp' in locals():
                logger.error("响应 Content-Type: %s", resp.headers.get('Content-Type'))
                logger.error("响应（前 2000 字）:\n%s", resp.text[:2000])
        except Exception:
            pass
        # 创建一个空数组占位，防止网站加载失败
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        logger.warning("⚠️ 已生成空数组占位文件 %s", OUTPUT_PATH)


if __name__ == "__main__":
    # Allow quick retries when running locally for debugging
    attempt = 0
    while True:
        try:
            attempt += 1
            fetch()
            break
        except Exception as exc:
            if attempt >= max(1, RETRIES):
                logger.error("达到最大重试次数 (%s)，停止。最后错误：%s", RETRIES, exc)
                sys.exit(1)
            sleep_for = BACKOFF_FACTOR * (2 ** (attempt - 1))
            logger.info("第 %s 次尝试失败，%s 秒后重试...", attempt, sleep_for)
            time.sleep(sleep_for)
