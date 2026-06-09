"""
SENTINEL OSINT - Username Intelligence Module
Sherlock-style username checker across 100+ platforms.
"""
import asyncio
import aiohttp
import random
import time
import re
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box
from core.config import cfg
from core.database import db
from core.banner import show_module_header, show_result_header

console = Console()

# ──────────────────────────────────────────────────────────────────
# PLATFORM DATABASE (100+ sites)
# ──────────────────────────────────────────────────────────────────
PLATFORMS: List[Dict] = [
    # ── Social ───────────────────────────────────────────────────
    {"name": "Twitter/X",      "category": "Social",      "url": "https://twitter.com/{u}",               "check": "status_200"},
    {"name": "Instagram",      "category": "Social",      "url": "https://www.instagram.com/{u}/",         "check": "status_200"},
    {"name": "Facebook",       "category": "Social",      "url": "https://www.facebook.com/{u}",           "check": "status_200"},
    {"name": "TikTok",         "category": "Social",      "url": "https://www.tiktok.com/@{u}",            "check": "status_200"},
    {"name": "Snapchat",       "category": "Social",      "url": "https://www.snapchat.com/add/{u}",       "check": "status_200"},
    {"name": "Pinterest",      "category": "Social",      "url": "https://www.pinterest.com/{u}/",         "check": "status_200"},
    {"name": "Tumblr",         "category": "Social",      "url": "https://{u}.tumblr.com/",                "check": "not_404"},
    {"name": "Reddit",         "category": "Social",      "url": "https://www.reddit.com/user/{u}",        "check": "status_200"},
    {"name": "VKontakte",      "category": "Social",      "url": "https://vk.com/{u}",                     "check": "status_200"},
    {"name": "OK.ru",          "category": "Social",      "url": "https://ok.ru/{u}",                      "check": "status_200"},
    {"name": "Telegram",       "category": "Social",      "url": "https://t.me/{u}",                       "check": "status_200"},
    {"name": "Signal",         "category": "Social",      "url": "https://signal.me/#p/{u}",               "check": "status_200"},
    {"name": "Mastodon",       "category": "Social",      "url": "https://mastodon.social/@{u}",           "check": "status_200"},
    {"name": "Minds",          "category": "Social",      "url": "https://www.minds.com/{u}",              "check": "status_200"},
    {"name": "MeWe",           "category": "Social",      "url": "https://mewe.com/i/{u}",                 "check": "status_200"},
    {"name": "Gab",            "category": "Social",      "url": "https://gab.com/{u}",                    "check": "status_200"},
    {"name": "Parler",         "category": "Social",      "url": "https://parler.com/profile/{u}/",        "check": "status_200"},
    {"name": "Gettr",          "category": "Social",      "url": "https://gettr.com/user/{u}",             "check": "status_200"},
    {"name": "Truth Social",   "category": "Social",      "url": "https://truthsocial.com/@{u}",           "check": "status_200"},
    {"name": "Clubhouse",      "category": "Social",      "url": "https://www.clubhouse.com/@{u}",         "check": "status_200"},
    {"name": "Ask.fm",         "category": "Social",      "url": "https://ask.fm/{u}",                     "check": "status_200"},
    {"name": "Badoo",          "category": "Social",      "url": "https://badoo.com/en/{u}",               "check": "status_200"},
    # ── Dev / Tech ────────────────────────────────────────────────
    {"name": "GitHub",         "category": "Dev",         "url": "https://github.com/{u}",                 "check": "status_200"},
    {"name": "GitLab",         "category": "Dev",         "url": "https://gitlab.com/{u}",                 "check": "status_200"},
    {"name": "Bitbucket",      "category": "Dev",         "url": "https://bitbucket.org/{u}",              "check": "status_200"},
    {"name": "SourceForge",    "category": "Dev",         "url": "https://sourceforge.net/u/{u}/",         "check": "status_200"},
    {"name": "CodePen",        "category": "Dev",         "url": "https://codepen.io/{u}",                 "check": "status_200"},
    {"name": "Replit",         "category": "Dev",         "url": "https://replit.com/@{u}",                "check": "status_200"},
    {"name": "HackerNews",     "category": "Dev",         "url": "https://news.ycombinator.com/user?id={u}","check": "status_200"},
    {"name": "Stack Overflow", "category": "Dev",         "url": "https://stackoverflow.com/users/name/{u}","check": "status_200"},
    {"name": "Kaggle",         "category": "Dev",         "url": "https://www.kaggle.com/{u}",             "check": "status_200"},
    {"name": "HackerEarth",    "category": "Dev",         "url": "https://www.hackerearth.com/@{u}",       "check": "status_200"},
    {"name": "LeetCode",       "category": "Dev",         "url": "https://leetcode.com/{u}/",              "check": "status_200"},
    {"name": "HackerRank",     "category": "Dev",         "url": "https://www.hackerrank.com/profile/{u}", "check": "status_200"},
    {"name": "Codeforces",     "category": "Dev",         "url": "https://codeforces.com/profile/{u}",     "check": "status_200"},
    {"name": "AtCoder",        "category": "Dev",         "url": "https://atcoder.jp/users/{u}",           "check": "status_200"},
    {"name": "TryHackMe",      "category": "Dev",         "url": "https://tryhackme.com/p/{u}",            "check": "status_200"},
    {"name": "HackTheBox",     "category": "Dev",         "url": "https://app.hackthebox.com/profile/{u}", "check": "status_200"},
    {"name": "Product Hunt",   "category": "Dev",         "url": "https://www.producthunt.com/@{u}",       "check": "status_200"},
    {"name": "AngelList",      "category": "Dev",         "url": "https://angel.co/u/{u}",                 "check": "status_200"},
    # ── Video / Streaming ─────────────────────────────────────────
    {"name": "YouTube",        "category": "Streaming",   "url": "https://www.youtube.com/@{u}",           "check": "status_200"},
    {"name": "Twitch",         "category": "Streaming",   "url": "https://www.twitch.tv/{u}",              "check": "status_200"},
    {"name": "Vimeo",          "category": "Streaming",   "url": "https://vimeo.com/{u}",                  "check": "status_200"},
    {"name": "Dailymotion",    "category": "Streaming",   "url": "https://www.dailymotion.com/{u}",        "check": "status_200"},
    {"name": "Rumble",         "category": "Streaming",   "url": "https://rumble.com/user/{u}",            "check": "status_200"},
    {"name": "Odysee",         "category": "Streaming",   "url": "https://odysee.com/@{u}",                "check": "status_200"},
    {"name": "BitChute",       "category": "Streaming",   "url": "https://www.bitchute.com/channel/{u}/",  "check": "status_200"},
    {"name": "Kick",           "category": "Streaming",   "url": "https://kick.com/{u}",                   "check": "status_200"},
    # ── Music ─────────────────────────────────────────────────────
    {"name": "Spotify",        "category": "Music",       "url": "https://open.spotify.com/user/{u}",      "check": "status_200"},
    {"name": "SoundCloud",     "category": "Music",       "url": "https://soundcloud.com/{u}",             "check": "status_200"},
    {"name": "Last.fm",        "category": "Music",       "url": "https://www.last.fm/user/{u}",           "check": "status_200"},
    {"name": "Bandcamp",       "category": "Music",       "url": "https://{u}.bandcamp.com/",              "check": "not_404"},
    {"name": "Mixcloud",       "category": "Music",       "url": "https://www.mixcloud.com/{u}/",          "check": "status_200"},
    # ── Photo / Design ────────────────────────────────────────────
    {"name": "Flickr",         "category": "Photo",       "url": "https://www.flickr.com/people/{u}/",     "check": "status_200"},
    {"name": "500px",          "category": "Photo",       "url": "https://500px.com/p/{u}",                "check": "status_200"},
    {"name": "Unsplash",       "category": "Photo",       "url": "https://unsplash.com/@{u}",              "check": "status_200"},
    {"name": "Behance",        "category": "Design",      "url": "https://www.behance.net/{u}",            "check": "status_200"},
    {"name": "DeviantArt",     "category": "Design",      "url": "https://www.deviantart.com/{u}",         "check": "status_200"},
    {"name": "Dribbble",       "category": "Design",      "url": "https://dribbble.com/{u}",               "check": "status_200"},
    {"name": "ArtStation",     "category": "Design",      "url": "https://www.artstation.com/{u}",         "check": "status_200"},
    {"name": "Figma",          "category": "Design",      "url": "https://www.figma.com/@{u}",             "check": "status_200"},
    # ── Blogging / Writing ────────────────────────────────────────
    {"name": "Medium",         "category": "Blogging",    "url": "https://medium.com/@{u}",                "check": "status_200"},
    {"name": "WordPress",      "category": "Blogging",    "url": "https://{u}.wordpress.com/",             "check": "not_404"},
    {"name": "Ghost",          "category": "Blogging",    "url": "https://{u}.ghost.io/",                  "check": "not_404"},
    {"name": "Substack",       "category": "Blogging",    "url": "https://{u}.substack.com/",              "check": "not_404"},
    {"name": "Wix",            "category": "Web",         "url": "https://{u}.wixsite.com/",               "check": "not_404"},
    # ── Q&A / Community ───────────────────────────────────────────
    {"name": "Quora",          "category": "Q&A",         "url": "https://www.quora.com/profile/{u}",      "check": "status_200"},
    {"name": "Wikipedia",      "category": "Wiki",        "url": "https://en.wikipedia.org/wiki/User:{u}", "check": "not_404"},
    {"name": "Fandom",         "category": "Wiki",        "url": "https://www.fandom.com/u/{u}",           "check": "status_200"},
    # ── eCommerce / Work ──────────────────────────────────────────
    {"name": "Etsy",           "category": "eCommerce",   "url": "https://www.etsy.com/people/{u}",        "check": "status_200"},
    {"name": "eBay",           "category": "eCommerce",   "url": "https://www.ebay.com/usr/{u}",           "check": "status_200"},
    {"name": "Fiverr",         "category": "Freelance",   "url": "https://www.fiverr.com/{u}",             "check": "status_200"},
    {"name": "Upwork",         "category": "Freelance",   "url": "https://www.upwork.com/freelancers/~{u}","check": "status_200"},
    {"name": "Freelancer",     "category": "Freelance",   "url": "https://www.freelancer.com/u/{u}",       "check": "status_200"},
    {"name": "Guru",           "category": "Freelance",   "url": "https://www.guru.com/freelancers/{u}/",  "check": "status_200"},
    {"name": "LinkedIn",       "category": "Professional","url": "https://www.linkedin.com/in/{u}",        "check": "status_200"},
    {"name": "Crunchbase",     "category": "Professional","url": "https://www.crunchbase.com/person/{u}",  "check": "status_200"},
    # ── Gaming ────────────────────────────────────────────────────
    {"name": "Steam",          "category": "Gaming",      "url": "https://steamcommunity.com/id/{u}",      "check": "status_200"},
    {"name": "Chess.com",      "category": "Gaming",      "url": "https://www.chess.com/member/{u}",       "check": "status_200"},
    {"name": "Lichess",        "category": "Gaming",      "url": "https://lichess.org/@/{u}",              "check": "status_200"},
    {"name": "Roblox",         "category": "Gaming",      "url": "https://www.roblox.com/user.aspx?username={u}","check": "status_200"},
    {"name": "NameMC",         "category": "Gaming",      "url": "https://namemc.com/profile/{u}",         "check": "status_200"},
    {"name": "MyAnimeList",    "category": "Anime",       "url": "https://myanimelist.net/profile/{u}",    "check": "status_200"},
    {"name": "AniList",        "category": "Anime",       "url": "https://anilist.co/user/{u}/",           "check": "status_200"},
    # ── Travel / Lifestyle ────────────────────────────────────────
    {"name": "Airbnb",         "category": "Travel",      "url": "https://www.airbnb.com/users/show/{u}",  "check": "status_200"},
    {"name": "TripAdvisor",    "category": "Travel",      "url": "https://www.tripadvisor.com/members/{u}","check": "status_200"},
    {"name": "AllTrails",      "category": "Fitness",     "url": "https://www.alltrails.com/members/{u}",  "check": "status_200"},
    {"name": "Strava",         "category": "Fitness",     "url": "https://www.strava.com/athletes/{u}",   "check": "status_200"},
    # ── Creator / Finance ─────────────────────────────────────────
    {"name": "Patreon",        "category": "Creator",     "url": "https://www.patreon.com/{u}",            "check": "status_200"},
    {"name": "Ko-fi",          "category": "Creator",     "url": "https://ko-fi.com/{u}",                  "check": "status_200"},
    {"name": "Buy Me Coffee",  "category": "Creator",     "url": "https://www.buymeacoffee.com/{u}",       "check": "status_200"},
    {"name": "Linktree",       "category": "Profile",     "url": "https://linktr.ee/{u}",                  "check": "status_200"},
    {"name": "About.me",       "category": "Profile",     "url": "https://about.me/{u}",                   "check": "status_200"},
    {"name": "Keybase",        "category": "Crypto",      "url": "https://keybase.io/{u}",                 "check": "status_200"},
    {"name": "Gravatar",       "category": "Profile",     "url": "https://en.gravatar.com/{u}",            "check": "status_200"},
    # ── NSFW / Adult (disabled by default) ────────────────────────
    # {"name": "OnlyFans",  "category": "Adult",  "url": "https://onlyfans.com/{u}", "check": "status_200"},
]

# ──────────────────────────────────────────────────────────────────
# ASYNC CHECKER
# ──────────────────────────────────────────────────────────────────
async def _check_platform(session: aiohttp.ClientSession, platform: dict, username: str) -> dict:
    result = {
        "site": platform["name"],
        "category": platform["category"],
        "found": False,
        "url": platform["url"].replace("{u}", username),
        "error": None,
    }
    try:
        headers = {"User-Agent": random.choice(cfg.USER_AGENTS)}
        timeout = aiohttp.ClientTimeout(total=cfg.REQUEST_TIMEOUT)
        check   = platform.get("check", "status_200")

        async with session.get(result["url"], headers=headers, ssl=False, timeout=timeout,
                               allow_redirects=True) as resp:
            if check == "status_200":
                result["found"] = (resp.status == 200)
            elif check == "not_404":
                result["found"] = (resp.status != 404)
            elif check == "body_contains":
                body = await resp.text(errors="replace")
                result["found"] = (platform.get("text", "") in body)

    except asyncio.TimeoutError:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:40]
    return result


async def _scan_all(username: str) -> List[dict]:
    sem = asyncio.Semaphore(cfg.MAX_CONCURRENT)

    async def bounded(p):
        async with sem:
            return await _check_platform(session, p, username)

    connector = aiohttp.TCPConnector(ssl=False, limit=cfg.MAX_CONCURRENT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [bounded(p) for p in PLATFORMS]
        results = []
        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[bold yellow]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="green"),
            TextColumn("[dim]{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task_p = progress.add_task(f"Scanning {len(PLATFORMS)} platforms...", total=len(tasks))
            for coro in asyncio.as_completed(tasks):
                r = await coro
                results.append(r)
                progress.advance(task_p)
        return results


def _display(username: str, results: List[dict]):
    found  = [r for r in results if r["found"]]
    errors = [r for r in results if r.get("error")]

    console.print(f"  [bold green]✔ FOUND[/bold green]  : [bold]{len(found)}[/bold] platforms")
    console.print(f"  [bold red]✘ MISS[/bold red]    : [bold]{len(results)-len(found)-len(errors)}[/bold] platforms")
    console.print(f"  [dim]⚠ ERRORS[/dim]  : [dim]{len(errors)}[/dim] platforms\n")

    if found:
        # Group by category
        cats = {}
        for r in found:
            cats.setdefault(r["category"], []).append(r)

        tbl = Table(
            title=f"[bold cyan]◈ USERNAME FOUND — @{username} ◈[/bold cyan]",
            box=box.DOUBLE_EDGE, border_style="cyan", show_lines=True, padding=(0, 1)
        )
        tbl.add_column("Platform",  style="bold white",  min_width=16)
        tbl.add_column("Category",  style="yellow",      min_width=12)
        tbl.add_column("Status",    style="bold green",  min_width=8)
        tbl.add_column("Profile URL", style="cyan dim",  min_width=40)

        for r in sorted(found, key=lambda x: x["category"]):
            tbl.add_row(r["site"], r["category"], "[bold green]● FOUND[/bold green]", r["url"])
        console.print(tbl)


def run(username: str = None):
    import questionary
    show_module_header("USERNAME INTELLIGENCE", "◉")

    if not username:
        username = questionary.text(
            "Enter target username:",
            style=questionary.Style([("question", "bold yellow"), ("answer", "cyan")])
        ).ask()
    if not username:
        return

    username = username.strip().lstrip("@")
    show_result_header("Username Intelligence", f"@{username}")

    console.print(f"  [dim]Scanning [bold]{len(PLATFORMS)}[/bold] platforms...[/dim]\n")
    t0 = time.time()

    results  = asyncio.run(_scan_all(username))
    duration = time.time() - t0

    _display(username, results)
    console.print(f"\n  [dim]Completed in {duration:.2f}s[/dim]\n")

    scan_id = db.log_scan("Username OSINT", username, {"found": sum(1 for r in results if r["found"])}, duration)
    for r in results:
        if r["found"]:
            db.log_username_hit(scan_id, username, r["site"], r["category"], r["url"])

    found = sum(1 for r in results if r["found"])
    console.print(f"  [bold green]✔[/bold green] Scan saved (ID: {scan_id}) — found on {found} platforms\n")
    return results
