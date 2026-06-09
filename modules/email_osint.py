"""
SENTINEL OSINT - Email Intelligence Module
Checks 50+ platforms for email registration.
"""
import asyncio
import aiohttp
import hashlib
import random
import time
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
# SITE DEFINITIONS
# Each site: name, category, url, method, params/data, headers,
#            found_indicator, not_found_indicator, reliability
# ──────────────────────────────────────────────────────────────────
SITES: List[Dict] = [
    # ── Social Media ─────────────────────────────────────────────
    {
        "name": "Twitter/X",
        "category": "Social",
        "url": "https://api.twitter.com/i/users/email_available.json",
        "method": "GET",
        "params": {"email": "{email}"},
        "headers": {"Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"},
        "found_if": {"body_contains": '"valid":false'},
        "not_found_if": {"body_contains": '"valid":true'},
        "reliability": "HIGH",
    },
    {
        "name": "Instagram",
        "category": "Social",
        "url": "https://www.instagram.com/accounts/web_create_ajax/attempt/",
        "method": "POST",
        "data": {"email": "{email}"},
        "headers": {"X-CSRFToken": "missing", "X-Instagram-AJAX": "1", "Content-Type": "application/x-www-form-urlencoded"},
        "found_if": {"body_contains": '"email_is_taken": true'},
        "not_found_if": {"body_contains": '"email_is_taken": false'},
        "reliability": "HIGH",
    },
    {
        "name": "Reddit",
        "category": "Social",
        "url": "https://www.reddit.com/api/check_username.json",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": "taken"},
        "not_found_if": {"body_contains": "available"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Pinterest",
        "category": "Social",
        "url": "https://www.pinterest.com/resource/EmailExistsResource/get/",
        "method": "GET",
        "params": {"source_url": "/", "data": '{{"options":{{"email":"{email}"}}}}'},
        "found_if": {"body_contains": '"data": true'},
        "not_found_if": {"body_contains": '"data": false'},
        "reliability": "HIGH",
    },
    {
        "name": "Tumblr",
        "category": "Social",
        "url": "https://www.tumblr.com/api/v2/user/accounts",
        "method": "GET",
        "params": {"email": "{email}"},
        "found_if": {"status": 200},
        "not_found_if": {"status": 401},
        "reliability": "MEDIUM",
    },
    {
        "name": "VKontakte",
        "category": "Social",
        "url": "https://vk.com/join",
        "method": "POST",
        "data": {"act": "email", "email": "{email}"},
        "found_if": {"body_contains": "already_registered"},
        "not_found_if": {"body_contains": "available"},
        "reliability": "MEDIUM",
    },
    {
        "name": "OK.ru",
        "category": "Social",
        "url": "https://ok.ru/dk",
        "method": "POST",
        "data": {"cmd": "AnonymousRegistration.checkEmail", "email": "{email}"},
        "found_if": {"body_contains": "USER_EXISTS"},
        "not_found_if": {"body_contains": "OK"},
        "reliability": "MEDIUM",
    },
    {
        "name": "TikTok",
        "category": "Social",
        "url": "https://www.tiktok.com/api/email/check/",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": '"email_status":1'},
        "not_found_if": {"body_contains": '"email_status":0'},
        "reliability": "MEDIUM",
    },
    {
        "name": "Badoo",
        "category": "Social",
        "url": "https://badoo.com/api/registered-email/",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": '"is_registered":true'},
        "not_found_if": {"body_contains": '"is_registered":false'},
        "reliability": "MEDIUM",
    },
    {
        "name": "Snapchat",
        "category": "Social",
        "url": "https://accounts.snapchat.com/accounts/get_username_suggestions",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": "email_taken"},
        "not_found_if": {"body_contains": "OK"},
        "reliability": "MEDIUM",
    },
    # ── Music / Entertainment ─────────────────────────────────────
    {
        "name": "Spotify",
        "category": "Music",
        "url": "https://spclient.wg.spotify.com/signup/public/v1/account",
        "method": "GET",
        "params": {"validate": "1", "email": "{email}"},
        "found_if": {"body_contains": '"emailExists":true'},
        "not_found_if": {"body_contains": '"emailExists":false'},
        "reliability": "HIGH",
    },
    {
        "name": "SoundCloud",
        "category": "Music",
        "url": "https://api-v2.soundcloud.com/users/email-lookup",
        "method": "GET",
        "params": {"client_id": "YUKXoArFcqrlFegpfGKspigRWsFooGlp", "email": "{email}"},
        "found_if": {"status": 200},
        "not_found_if": {"status": 404},
        "reliability": "HIGH",
    },
    {
        "name": "Last.fm",
        "category": "Music",
        "url": "https://www.last.fm/api/account/create",
        "method": "POST",
        "data": {"email": "{email}", "csrfmiddlewaretoken": "abcdef"},
        "found_if": {"body_contains": "already registered"},
        "not_found_if": {"body_contains": "success"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Deezer",
        "category": "Music",
        "url": "https://www.deezer.com/ajax/action.php",
        "method": "POST",
        "data": {"type": "check_email", "mail": "{email}"},
        "found_if": {"body_contains": '"error":false'},
        "not_found_if": {"body_contains": '"error":true'},
        "reliability": "MEDIUM",
    },
    # ── Tech / Dev ────────────────────────────────────────────────
    {
        "name": "GitHub",
        "category": "Dev",
        "url": "https://github.com/signup_check/email",
        "method": "POST",
        "data": {"value": "{email}", "authenticity_token": "fake"},
        "found_if": {"body_contains": "Email is already in use"},
        "not_found_if": {"body_contains": "Available"},
        "reliability": "HIGH",
    },
    {
        "name": "GitLab",
        "category": "Dev",
        "url": "https://gitlab.com/users/sign_up",
        "method": "POST",
        "data": {"user[email]": "{email}"},
        "found_if": {"body_contains": "has already been taken"},
        "not_found_if": {"body_contains": "success"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Gravatar",
        "category": "Profile",
        "url": "https://en.gravatar.com/{hash}.json",
        "method": "GET",
        "found_if": {"status": 200},
        "not_found_if": {"status": 404},
        "reliability": "HIGH",
        "use_md5": True,
    },
    {
        "name": "Firefox Accounts",
        "category": "Tech",
        "url": "https://api.accounts.firefox.com/v1/account/status",
        "method": "POST",
        "json_data": {"email": "{email}"},
        "found_if": {"body_contains": '"exists":true'},
        "not_found_if": {"body_contains": '"exists":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Proton Mail",
        "category": "Email",
        "url": "https://account.proton.me/api/core/v4/users/available",
        "method": "GET",
        "params": {"Email": "{email}", "ParseDomain": "1"},
        "found_if": {"body_contains": '"Code":12011'},
        "not_found_if": {"body_contains": '"Code":1000'},
        "reliability": "HIGH",
    },
    {
        "name": "Adobe",
        "category": "Creative",
        "url": "https://auth.services.adobe.com/en_US/index.html",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": "already in use"},
        "not_found_if": {"body_contains": "Sign up"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Dropbox",
        "category": "Cloud",
        "url": "https://www.dropbox.com/register",
        "method": "POST",
        "data": {"email": "{email}", "t": "IXmn0lLb4QVxBMdMYyq7mVBUiW72RZMa"},
        "found_if": {"body_contains": "already has an account"},
        "not_found_if": {"body_contains": "next"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Samsung",
        "category": "Tech",
        "url": "https://account.samsung.com/accounts/v1/USAID/signInGate",
        "method": "GET",
        "params": {"signInId": "{email}"},
        "found_if": {"body_contains": '"accountExists":true'},
        "not_found_if": {"body_contains": '"accountExists":false'},
        "reliability": "HIGH",
    },
    # ── eCommerce ─────────────────────────────────────────────────
    {
        "name": "eBay",
        "category": "eCommerce",
        "url": "https://reg.ebay.com/reg/CheckEmailAddress",
        "method": "GET",
        "params": {"emailAddress": "{email}"},
        "found_if": {"body_contains": '"registered":true'},
        "not_found_if": {"body_contains": '"registered":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Etsy",
        "category": "eCommerce",
        "url": "https://www.etsy.com/api/v3/ajax/email-available",
        "method": "GET",
        "params": {"email": "{email}"},
        "found_if": {"body_contains": '"exists":true'},
        "not_found_if": {"body_contains": '"exists":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Shopify",
        "category": "eCommerce",
        "url": "https://mystore.myshopify.com/account",
        "method": "POST",
        "data": {"form_type": "recover_customer_password", "email": "{email}"},
        "found_if": {"body_contains": "sent you an email"},
        "not_found_if": {"body_contains": "no account"},
        "reliability": "LOW",
    },
    # ── Entertainment / Streaming ──────────────────────────────────
    {
        "name": "Netflix",
        "category": "Streaming",
        "url": "https://www.netflix.com/api/shakti/mre/login",
        "method": "POST",
        "json_data": {"userLoginId": "{email}", "password": "SentinelOSINT#!", "flow": "websiteSignUp", "mode": "login", "action": "loginAction"},
        "found_if": {"body_contains": "password"},
        "not_found_if": {"body_contains": "member"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Twitch",
        "category": "Streaming",
        "url": "https://passport.twitch.tv/register",
        "method": "POST",
        "json_data": {"birthday": {"day": 1, "month": 1, "year": 1990}, "client_id": "kimne78kpu1blimcopherquawd0", "email": "{email}", "password": "TempPass123!", "username": "tempusrsentinel"},
        "found_if": {"body_contains": "email_taken"},
        "not_found_if": {"body_contains": "success"},
        "reliability": "HIGH",
    },
    {
        "name": "Vimeo",
        "category": "Streaming",
        "url": "https://vimeo.com/_signup/find_user",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": '"exists":true'},
        "not_found_if": {"body_contains": '"exists":false'},
        "reliability": "HIGH",
    },
    # ── Education / Learning ───────────────────────────────────────
    {
        "name": "Duolingo",
        "category": "Education",
        "url": "https://www.duolingo.com/2017-06-30/users",
        "method": "GET",
        "params": {"email": "{email}", "fields": "users{username}"},
        "found_if": {"body_contains": '"totalAvatarCount":1'},
        "not_found_if": {"body_contains": '"totalAvatarCount":0'},
        "reliability": "HIGH",
    },
    {
        "name": "Coursera",
        "category": "Education",
        "url": "https://www.coursera.org/api/rest/v1/user/exists",
        "method": "GET",
        "params": {"email": "{email}"},
        "found_if": {"body_contains": '"exists":true'},
        "not_found_if": {"body_contains": '"exists":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Udemy",
        "category": "Education",
        "url": "https://www.udemy.com/join/signup-popup/",
        "method": "POST",
        "data": {"email": "{email}", "csrfmiddlewaretoken": "fakecsfr123"},
        "found_if": {"body_contains": "already have an account"},
        "not_found_if": {"body_contains": "next"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Khan Academy",
        "category": "Education",
        "url": "https://www.khanacademy.org/api/internal/user/exists",
        "method": "GET",
        "params": {"identifier": "{email}"},
        "found_if": {"body_contains": '"exists":true'},
        "not_found_if": {"body_contains": '"exists":false'},
        "reliability": "HIGH",
    },
    # ── CMS / Blogging ─────────────────────────────────────────────
    {
        "name": "WordPress",
        "category": "CMS",
        "url": "https://public-api.wordpress.com/rest/v1.1/users/{email}/auth-options",
        "method": "GET",
        "found_if": {"status": 200},
        "not_found_if": {"status": 404},
        "reliability": "HIGH",
    },
    {
        "name": "Medium",
        "category": "Blogging",
        "url": "https://medium.com/m/account/authenticate",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": "susi"},
        "not_found_if": {"body_contains": "Sign Up"},
        "reliability": "LOW",
    },
    {
        "name": "Substack",
        "category": "Blogging",
        "url": "https://substack.com/api/v1/email/available",
        "method": "GET",
        "params": {"email": "{email}"},
        "found_if": {"body_contains": '"available":false'},
        "not_found_if": {"body_contains": '"available":true'},
        "reliability": "HIGH",
    },
    # ── Gaming ─────────────────────────────────────────────────────
    {
        "name": "Steam",
        "category": "Gaming",
        "url": "https://store.steampowered.com/join/checkavail/",
        "method": "POST",
        "data": {"email": "{email}", "captcha_text": "", "captchagid": "-1"},
        "found_if": {"body_contains": "already in use"},
        "not_found_if": {"body_contains": "available"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Chess.com",
        "category": "Gaming",
        "url": "https://www.chess.com/callback/email/unique",
        "method": "POST",
        "json_data": {"email": "{email}"},
        "found_if": {"body_contains": "taken"},
        "not_found_if": {"body_contains": "success"},
        "reliability": "HIGH",
    },
    # ── Travel ─────────────────────────────────────────────────────
    {
        "name": "Airbnb",
        "category": "Travel",
        "url": "https://www.airbnb.com/api/v3/RegisterPage/CheckEmail",
        "method": "POST",
        "json_data": {"email": "{email}"},
        "found_if": {"body_contains": '"registered":true'},
        "not_found_if": {"body_contains": '"registered":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Booking.com",
        "category": "Travel",
        "url": "https://account.booking.com/sign-in/verifyEmail",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": "exists"},
        "not_found_if": {"body_contains": "new"},
        "reliability": "MEDIUM",
    },
    # ── Design / Creative ──────────────────────────────────────────
    {
        "name": "Behance",
        "category": "Creative",
        "url": "https://www.behance.net/api/v2/users",
        "method": "GET",
        "params": {"q": "{email}"},
        "found_if": {"body_contains": '"users":[{'},
        "not_found_if": {"body_contains": '"users":[]'},
        "reliability": "MEDIUM",
    },
    {
        "name": "DeviantArt",
        "category": "Creative",
        "url": "https://www.deviantart.com/_napi/signup/check-user-availability",
        "method": "GET",
        "params": {"email": "{email}"},
        "found_if": {"body_contains": '"email_taken":true'},
        "not_found_if": {"body_contains": '"email_taken":false'},
        "reliability": "HIGH",
    },
    # ── Freelance / Work ──────────────────────────────────────────
    {
        "name": "Fiverr",
        "category": "Freelance",
        "url": "https://www.fiverr.com/validate_email",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": '"is_taken":true'},
        "not_found_if": {"body_contains": '"is_taken":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Freelancer",
        "category": "Freelance",
        "url": "https://www.freelancer.com/ajax/user/email-available.php",
        "method": "GET",
        "params": {"email": "{email}"},
        "found_if": {"body_contains": '"result":"not_available"'},
        "not_found_if": {"body_contains": '"result":"available"'},
        "reliability": "HIGH",
    },
    # ── Misc ──────────────────────────────────────────────────────
    {
        "name": "Imgur",
        "category": "Media",
        "url": "https://api.imgur.com/3/account/{email_url}",
        "method": "GET",
        "headers": {"Authorization": "Client-ID 546c25a59c58ad7"},
        "found_if": {"status": 200},
        "not_found_if": {"status": 404},
        "reliability": "LOW",
    },
    {
        "name": "Patreon",
        "category": "Creator",
        "url": "https://www.patreon.com/api/auth",
        "method": "POST",
        "json_data": {"data": {"type": "user", "attributes": {"email": "{email}", "password": "FakePass1!"}}, "included": []},
        "found_if": {"body_contains": "invalid_credentials"},
        "not_found_if": {"body_contains": "invalid_email"},
        "reliability": "HIGH",
    },
    {
        "name": "Quora",
        "category": "Q&A",
        "url": "https://www.quora.com/account/signup_with_email",
        "method": "POST",
        "data": {"email": "{email}"},
        "found_if": {"body_contains": "already_exists"},
        "not_found_if": {"body_contains": "success"},
        "reliability": "MEDIUM",
    },
    {
        "name": "Flickr",
        "category": "Photo",
        "url": "https://login.yahoo.com/?.tsrc=flickr",
        "method": "POST",
        "data": {"username": "{email}"},
        "found_if": {"body_contains": "signin"},
        "not_found_if": {"body_contains": "create_account"},
        "reliability": "LOW",
    },
    {
        "name": "Wix",
        "category": "Web Builder",
        "url": "https://www.wix.com/_api/iam/authentication/v1/report-email-used",
        "method": "POST",
        "json_data": {"email": "{email}"},
        "found_if": {"body_contains": '"emailUsed":true'},
        "not_found_if": {"body_contains": '"emailUsed":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Zoho",
        "category": "Productivity",
        "url": "https://accounts.zoho.com/emailverification",
        "method": "GET",
        "params": {"email": "{email}", "scope": "zohocontacts/contactapi"},
        "found_if": {"body_contains": '"exists":true'},
        "not_found_if": {"body_contains": '"exists":false'},
        "reliability": "HIGH",
    },
    {
        "name": "Skype",
        "category": "Comm",
        "url": "https://login.skype.com/login/oauth/microsoft",
        "method": "POST",
        "data": {"login": "{email}"},
        "found_if": {"body_contains": "ppsft"},
        "not_found_if": {"body_contains": "signup"},
        "reliability": "LOW",
    },
    {
        "name": "Roblox",
        "category": "Gaming",
        "url": "https://auth.roblox.com/v1/validators/email",
        "method": "GET",
        "params": {"emailAddress": "{email}"},
        "found_if": {"body_contains": '"isEmailValid":true'},
        "not_found_if": {"body_contains": '"isEmailValid":false'},
        "reliability": "MEDIUM",
    },
]

STATUS_FOUND     = "FOUND"
STATUS_NOT_FOUND = "NOT FOUND"
STATUS_ERROR     = "ERROR"
STATUS_UNKNOWN   = "UNKNOWN"

# ──────────────────────────────────────────────────────────────────
# ASYNC CHECKER
# ──────────────────────────────────────────────────────────────────
async def _check_site(session: aiohttp.ClientSession, site: dict, email: str) -> dict:
    """Check one site for email registration."""
    name = site["name"]
    result = {"site": name, "category": site["category"], "status": STATUS_UNKNOWN, "url": "", "reliability": site.get("reliability", "MEDIUM")}

    try:
        email_md5 = hashlib.md5(email.strip().lower().encode()).hexdigest()

        url = site["url"].replace("{email}", email).replace("{hash}", email_md5).replace("{email_url}", email.replace("@", "%40"))
        result["url"] = url

        method  = site.get("method", "GET")
        headers = {**{"User-Agent": random.choice(cfg.USER_AGENTS)}, **site.get("headers", {})}
        params  = {k: v.replace("{email}", email) for k, v in site.get("params", {}).items()}
        data    = {k: v.replace("{email}", email) for k, v in site.get("data", {}).items()}
        json_d  = site.get("json_data")
        if json_d:
            import json as _json
            json_str = _json.dumps(json_d).replace("{email}", email)
            json_d   = _json.loads(json_str)

        timeout = aiohttp.ClientTimeout(total=cfg.REQUEST_TIMEOUT)

        async with getattr(session, method.lower())(
            url, headers=headers, params=params or None,
            data=data or None, json=json_d,
            ssl=False, timeout=timeout, allow_redirects=True
        ) as resp:
            body   = await resp.text(errors="replace")
            status = resp.status

            found_if     = site.get("found_if", {})
            not_found_if = site.get("not_found_if", {})

            if "status" in found_if and status == found_if["status"]:
                result["status"] = STATUS_FOUND
            elif "status" in not_found_if and status == not_found_if["status"]:
                result["status"] = STATUS_NOT_FOUND
            elif "body_contains" in found_if and found_if["body_contains"] in body:
                result["status"] = STATUS_FOUND
            elif "body_contains" in not_found_if and not_found_if["body_contains"] in body:
                result["status"] = STATUS_NOT_FOUND
            else:
                result["status"] = STATUS_UNKNOWN

    except asyncio.TimeoutError:
        result["status"] = STATUS_ERROR
        result["error"]  = "Timeout"
    except Exception as e:
        result["status"] = STATUS_ERROR
        result["error"]  = str(e)[:60]

    return result


async def _check_all(email: str, sites: list) -> List[dict]:
    sem = asyncio.Semaphore(cfg.MAX_CONCURRENT)

    async def bounded(site):
        async with sem:
            return await _check_site(session, site, email)

    connector = aiohttp.TCPConnector(ssl=False, limit=cfg.MAX_CONCURRENT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [bounded(s) for s in sites]
        results = []
        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[bold yellow]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="green"),
            TextColumn("[dim]{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scanning {len(sites)} platforms...", total=len(tasks))
            for coro in asyncio.as_completed(tasks):
                r = await coro
                results.append(r)
                progress.advance(task)
        return results


# ──────────────────────────────────────────────────────────────────
# DISPLAY
# ──────────────────────────────────────────────────────────────────
def _display_results(email: str, results: List[dict]):
    found     = [r for r in results if r["status"] == STATUS_FOUND]
    not_found = [r for r in results if r["status"] == STATUS_NOT_FOUND]
    errors    = [r for r in results if r["status"] in (STATUS_ERROR, STATUS_UNKNOWN)]

    console.print(f"\n  [bold green]✔ FOUND[/bold green]      : [bold]{len(found)}[/bold]  sites")
    console.print(f"  [bold red]✘ NOT FOUND[/bold red] : [bold]{len(not_found)}[/bold]  sites")
    console.print(f"  [dim]⚠ ERRORS[/dim]      : [dim]{len(errors)}[/dim]  sites\n")

    if found:
        tbl = Table(
            title=f"[bold cyan]◈ REGISTERED ACCOUNTS — {email} ◈[/bold cyan]",
            box=box.DOUBLE_EDGE, border_style="cyan",
            show_lines=True, padding=(0, 1)
        )
        tbl.add_column("Platform",    style="bold white",  min_width=16)
        tbl.add_column("Category",    style="yellow",      min_width=12)
        tbl.add_column("Reliability", style="dim",         min_width=10)
        tbl.add_column("Status",      style="bold green",  min_width=10)
        tbl.add_column("Profile URL", style="cyan dim",    min_width=30)

        for r in sorted(found, key=lambda x: x["site"]):
            rel_color = {"HIGH": "green", "MEDIUM": "yellow", "LOW": "red"}.get(r.get("reliability", "LOW"), "dim")
            tbl.add_row(
                r["site"], r["category"],
                f"[{rel_color}]{r.get('reliability','?')}[/{rel_color}]",
                f"[bold green]● {STATUS_FOUND}[/bold green]",
                r.get("url", "")[:60]
            )
        console.print(tbl)

    if errors:
        console.print(f"\n  [dim]Errors/Unknown on {len(errors)} platform(s) — may be rate limited or endpoint changed.[/dim]")


# ──────────────────────────────────────────────────────────────────
# PUBLIC ENTRY
# ──────────────────────────────────────────────────────────────────
def run(email: str = None, from_scan_id: int = None):
    import questionary
    show_module_header("EMAIL INTELLIGENCE", "✉")

    if not email:
        email = questionary.text(
            "Enter target email:",
            style=questionary.Style([("question", "bold yellow"), ("answer", "cyan")])
        ).ask()
    if not email:
        return

    email = email.strip().lower()
    show_result_header("Email Intelligence", email)

    console.print(f"  [dim]Checking [bold]{len(SITES)}[/bold] platforms asynchronously...[/dim]\n")
    t0 = time.time()

    results = asyncio.run(_check_all(email, SITES))
    duration = time.time() - t0

    _display_results(email, results)
    console.print(f"\n  [dim]Completed in {duration:.2f}s[/dim]\n")

    # DB logging
    scan_id = db.log_scan("Email OSINT", email, {"total": len(results)}, duration)
    for r in results:
        if r["status"] == STATUS_FOUND:
            db.log_email_hit(scan_id, email, r["site"], r["category"], r["status"], r.get("url", ""))

    found_count = sum(1 for r in results if r["status"] == STATUS_FOUND)
    console.print(f"  [bold green]✔[/bold green] Scan saved to DB (ID: {scan_id}) — {found_count} accounts found\n")

    return results
