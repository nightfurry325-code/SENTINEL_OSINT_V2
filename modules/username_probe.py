"""modules/username_probe.py — Async username footprint probe (100+ sites)"""
import asyncio
import aiohttp
import json
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

console  = Console()
DATA_FILE = Path(__file__).parent.parent / "data" / "username_sites.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept":     "text/html,application/xhtml+xml,*/*;q=0.9",
}

class UsernameProbe:
    def __init__(self, cfg, db):
        self.cfg   = cfg
        self.db    = db
        self.sites = self._load_sites()
        self.timeout = aiohttp.ClientTimeout(total=cfg.timeout)

    def _load_sites(self):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]⚠ Could not load username_sites.json: {e}[/]")
            return {}

    async def scan(self, username: str) -> dict:
        cached = self.db.get_cached(f"username:{username}")
        if cached:
            console.print(f"\n  [#555555]↩ Loaded from cache[/]\n")
            return cached

        start = time.time()
        found = []
        not_found = []
        semaphore = asyncio.Semaphore(int(self.cfg.get("max_workers", 20)))
        connector = aiohttp.TCPConnector(ssl=False, limit=50)

        async with aiohttp.ClientSession(connector=connector, headers=HEADERS, timeout=self.timeout) as session:
            with Progress(
                SpinnerColumn(style="bold #ffaa00"),
                TextColumn("[bold #ffaa00]{task.description}"),
                BarColumn(bar_width=30, style="#333333", complete_style="#ffaa00"),
                TextColumn("[#555555]{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=console, transient=True,
            ) as progress:
                task = progress.add_task(
                    f"Scanning [bold #ffaa00]{username}[/] across {len(self.sites)} sites",
                    total=len(self.sites)
                )
                tasks = [
                    self._check(session, semaphore, key, site, username, progress, task)
                    for key, site in self.sites.items()
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                continue
            if r and r.get("found"):
                found.append(r)
            elif r:
                not_found.append(r)

        duration = round(time.time() - start, 2)
        output = {
            "scan_type":     "username",
            "target":        username,
            "found":         sorted(found,     key=lambda x: x["name"]),
            "not_found":     sorted(not_found, key=lambda x: x["name"]),
            "found_count":   len(found),
            "total_checked": len(self.sites),
            "duration":      duration,
        }
        self.db.set_cache(f"username:{username}", output, ttl_hours=12)
        self.db.save_scan("username", username, output)
        return output

    async def _check(self, session, semaphore, key, site, username, progress, task):
        async with semaphore:
            try:
                result = await self._probe(session, key, site, username)
                progress.advance(task)
                return result
            except Exception:
                progress.advance(task)
                return {"key": key, "name": site.get("name", key), "found": False}

    async def _probe(self, session, key, site, username):
        url        = site["url"].format(username)
        check_type = site.get("check_type", "status_code")

        async with session.get(url, allow_redirects=True, ssl=False) as resp:
            status = resp.status
            body   = await resp.text()

        found = False
        if check_type == "status_code":
            found = status == site.get("found_status", 200)
        elif check_type == "body_not_contains":
            not_found_text = site.get("not_found_text", "")
            found = not_found_text.lower() not in body.lower()
        elif check_type == "body_contains":
            found = site.get("found_text", "").lower() in body.lower()

        return {
            "key":         key,
            "name":        site.get("name", key),
            "url":         site.get("url", "").split("{")[0],
            "profile_url": url,
            "category":    site.get("category", "other"),
            "found":       found and status != 404,
            "status":      status,
        }
