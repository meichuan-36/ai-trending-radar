# Pull Request: fix(fetch): add headers, Content-Type checks and retry logic

This PR adds browser-like headers, Content-Type checks, retry logic with exponential backoff, and improved logging to scripts/fetch_papers.py to reduce failures when the Papers With Code API returns HTML (e.g., anti-bot pages) instead of JSON.

Changes:
- Add HEADERS with User-Agent, Accept, Referer, X-Requested-With
- Use requests.Session with urllib3 Retry via HTTPAdapter
- Check Content-Type before calling resp.json(), and print response preview on errors
- Add environment variables to tune retries, backoff, timeout, limit, and user-agent
- Keep existing fallback behavior of writing an empty list to the output path when fetch fails

How to test:
- Run locally: python scripts/fetch_papers.py
- Adjust retries/timeout via env vars, e.g.: FETCH_PAPERS_RETRIES=5 FETCH_PAPERS_TIMEOUT=60 python scripts/fetch_papers.py
