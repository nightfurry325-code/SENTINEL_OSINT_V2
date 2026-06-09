"""modules/email_probe.py — Async email-to-accounts probe (120+ platforms)"""
import asyncio
import aiohttp
import json
import re
import time
import hashlib
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

console = Console()
DATA_FILE = Path(__file__).parent.parent / "data" / "email_services.json"

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control":   "no-cache",
}


class EmailProbe:
    def __init__(self, cfg, db):
        self.cfg      = cfg
        self.db       = db
        self.services = self._load_services()
        self.timeout  = aiohttp.ClientTimeout(total=cfg.timeout)

    def _load_services(self) -> dict:
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]⚠ Could not load email_services.json: {e}[/]")
            return {}

    async def scan(self, email: str, options: list = None) -> dict:
        options      = options or []
        use_cache    = any("Cache" in o for o in options)
        bypass_cache = any("Bypass" in o for o in options)

        # Check DB cache first
        if use_cache and not bypass_cache:
            cached = self.db.get_cached(f"email:{email}")
            if cached:
                console.print(f"\n  [#555555]↩ Loaded from cache ({len(cached.get('found',[]))} found)[/]\n")
                return cached

        start    = time.time()
        found    = []
        not_fnd  = []
        errors   = []
        semaphore = asyncio.Semaphore(int(self.cfg.get("max_workers", 20)))

        connector = aiohttp.TCPConnector(ssl=False, limit=50)
        async with aiohttp.ClientSession(
            connector=connector,
            headers=HEADERS,
            timeout=self.timeout,
        ) as session:
            with Progress(
                SpinnerColumn(style="bold #00ff9f"),
                TextColumn("[bold #00aaff]{task.description}"),
                BarColumn(bar_width=30, style="#333333", complete_style="#00ff9f"),
                TextColumn("[#555555]{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    f"Probing {len(self.services)} platforms for [bold #00aaff]{email}[/]",
                    total=len(self.services)
                )

                tasks = [
                    self._check_service(session, semaphore, svc_key, svc_data, email, progress, task)
                    for svc_key, svc_data in self.services.items()
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                errors.append(str(r))
            elif r and r.get("found"):
                found.append(r)
            elif r:
                not_fnd.append(r)

        duration = round(time.time() - start, 2)
        output   = {
            "scan_type":     "email",
            "target":        email,
            "found":         sorted(found,    key=lambda x: x["name"]),
            "not_found":     sorted(not_fnd,  key=lambda x: x["name"]),
            "errors":        errors,
            "found_count":   len(found),
            "total_checked": len(self.services),
            "duration":      duration,
        }

        if use_cache:
            self.db.set_cache(f"email:{email}", output, ttl_hours=24)
        self.db.save_scan("email", email, output)

        return output

    async def _check_service(self, session, semaphore, key, svc, email, progress, task):
        async with semaphore:
            try:
                result = await self._probe(session, key, svc, email)
                if progress:
                    progress.advance(task)
                return result
            except Exception as e:
                if progress:
                    progress.advance(task)
                return {"key": key, "name": svc.get("name", key), "found": False, "error": str(e)}

    async def _probe(self, session, key: str, svc: dict, email: str) -> dict:
        endpoint   = svc.get("endpoint", "")
        method     = svc.get("method", "GET").upper()
        check_type = svc.get("check_type", "body_contains")
        indicator  = svc.get("found_indicator", "")

        # Build endpoint
        email_user = email.split("@")[0]
        email_hash = hashlib.md5(email.lower().encode()).hexdigest()
        endpoint   = endpoint.replace("{email}", email)\
                              .replace("{email_user}", email_user)\
                              .replace("{email_hash}", email_hash)

        # Substitute in params/data/json
        def sub(obj):
            if isinstance(obj, dict):
                return {k: v.replace("{email}", email).replace("{email_user}", email_user)
                        if isinstance(v, str) else v for k, v in obj.items()}
            return obj

        params  = sub(svc.get("params", {})) or None
        data    = sub(svc.get("data",   {})) or None
        json_b  = sub(svc.get("json",   {})) or None

        async with session.request(
            method,
            endpoint,
            params=params,
            data=data,
            json=json_b if json_b else None,
            allow_redirects=True,
            ssl=False,
        ) as resp:
            body        = await resp.text()
            status_code = resp.status
            found       = False

            if check_type == "status_code":
                found = str(status_code) == indicator
            elif check_type == "body_contains":
                found = bool(re.search(indicator, body, re.IGNORECASE))
            elif check_type == "body_not_contains":
                found = not bool(re.search(indicator, body, re.IGNORECASE))
            elif check_type == "json_field":
                try:
                    data_j = json.loads(body)
                    field  = svc.get("field", "")
                    found  = str(data_j.get(field, "")).lower() == indicator.lower()
                except Exception:
                    found = False
            elif check_type == "json_key":
                found = indicator in body
            elif check_type == "json_error":
                found = bool(re.search(indicator, body, re.IGNORECASE))

        return {
            "key":         key,
            "name":        svc.get("name", key),
            "url":         svc.get("url", ""),
            "category":    svc.get("category", "other"),
            "method":      svc.get("method", "GET"),
            "profile_url": svc.get("url", "") + "/" + email.split("@")[0],
            "found":       found,
            "status":      status_code,
        }
