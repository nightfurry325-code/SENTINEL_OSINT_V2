"""modules/social_probe.py — Social media profile aggregator"""
import asyncio
import aiohttp
import re
from rich.console import Console

console = Console()

SOCIAL_APIS = {
    "Twitter/X":  {"url": "https://api.twitter.com/2/users/by/username/{}", "extract": ["name","description","public_metrics"]},
    "GitHub":     {"url": "https://api.github.com/users/{}", "extract": ["name","bio","public_repos","followers","location"]},
    "Reddit":     {"url": "https://www.reddit.com/user/{}/about.json", "extract": ["name","icon_img","link_karma","comment_karma","created_utc"]},
    "HackerNews": {"url": "https://hacker-news.firebaseio.com/v0/user/{}.json", "extract": ["about","karma","created","submitted"]},
    "PyPI":       {"url": "https://pypi.org/pypi/{}/json", "extract": ["info"]},
    "npm":        {"url": "https://registry.npmjs.org/~{}", "extract": []},
    "Gravatar":   {"url": "https://en.gravatar.com/{}.json", "extract": ["entry"]},
    "Keybase":    {"url": "https://keybase.io/_/api/1.0/user/lookup.json?username={}", "extract": ["them"]},
}

class SocialProbe:
    def __init__(self, cfg, db):
        self.cfg     = cfg
        self.db      = db
        self.timeout = aiohttp.ClientTimeout(total=cfg.timeout)

    async def scan(self, query: str) -> dict:
        profiles  = {}
        semaphore = asyncio.Semaphore(10)

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [
                self._fetch_profile(session, semaphore, platform, info, query)
                for platform, info in SOCIAL_APIS.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if r and not isinstance(r, Exception):
                profiles[r["platform"]] = r

        output = {
            "scan_type":   "social",
            "target":      query,
            "found_count": len(profiles),
            "profiles":    profiles,
        }
        self.db.save_scan("social", query, output)
        return output

    async def _fetch_profile(self, session, semaphore, platform, info, query):
        async with semaphore:
            try:
                url = info["url"].format(query)
                async with session.get(url, ssl=False) as r:
                    if r.status != 200:
                        return None
                    data = await r.json()
                return {
                    "platform": platform,
                    "url":      url,
                    "username": query,
                    "raw":      {k: data.get(k) for k in info.get("extract", []) if data.get(k)},
                    "bio":      str(data.get("bio") or data.get("description") or "")[:80],
                }
            except Exception:
                return None
