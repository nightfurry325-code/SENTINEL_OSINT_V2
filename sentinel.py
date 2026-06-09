#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗                ║
║   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║                ║
║   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║                ║
║   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║                ║
║   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗           ║
║   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝           ║
║            Developer:by FERI × OSINT INTELLIGENCE FRAMEWORK v2.0             ║
║              [ Email · Username · Phone · IP · Breach · Social ]             ║
╚══════════════════════════════════════════════════════════════════════════════╝

SENTINEL OSINT — Advanced Open-Source Intelligence Framework
Author      : FERI (Sentinel Labs)
Version     : 2.0.0
License     : MIT
GitHub      : https://github.com/yourusername/sentinel-osint

Usage:
    python sentinel.py           → Interactive CLI
    python sentinel.py --help    → Command-line options
    python sentinel.py web       → Launch Web Dashboard
    python sentinel.py bot       → Start Telegram Bot
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich import box
import questionary
from questionary import Style

from core.banner import show_banner, show_module_header
from core.config import Config
from core.database import Database
from core.utils import validate_email, validate_ip, console_separator
from core.reporter import Reporter

console = Console()

SENTINEL_STYLE = Style([
    ('qmark',       'fg:#00ff9f bold'),
    ('question',    'fg:#ffffff bold'),
    ('answer',      'fg:#00ff9f bold'),
    ('pointer',     'fg:#00ff9f bold'),
    ('highlighted', 'fg:#00ff9f bold'),
    ('selected',    'fg:#00ff9f'),
    ('separator',   'fg:#333333'),
    ('instruction', 'fg:#666666'),
    ('text',        'fg:#cccccc'),
    ('disabled',    'fg:#444444 italic'),
])

MENU_ITEMS = [
    ("📧", "Email Intelligence",    "Probe 120+ platforms for registered accounts"),
    ("👤", "Username OSINT",        "Track username footprint across 100+ sites"),
    ("📱", "Phone Intelligence",    "Carrier lookup, region, OSINT aggregation"),
    ("🌐", "IP / Domain OSINT",     "Geolocation, WHOIS, DNS, threat intel"),
    ("🔓", "Breach Inspector",      "Check email/password breach exposure"),
    ("🕸️", "Social Profiler",       "Deep social media profile aggregator"),
    ("📊", "Reports & History",     "View, filter and export saved reports"),
    ("⚙️",  "Settings & API Keys",  "Configure proxies, keys, preferences"),
    ("🤖", "Telegram Bot Mode",     "Launch interactive bot interface"),
    ("❌", "Exit",                  ""),
]


def build_menu_choices():
    choices = []
    for icon, label, desc in MENU_ITEMS:
        if label == "Exit":
            choices.append(f"  {icon}  {label}")
        else:
            padded = f"{label:<25}"
            choices.append(f"  {icon}  {padded} → {desc}")
    return choices


# ──────────────────────────────── MAIN LOOP ──────────────────────────────────

def run():
    cfg   = Config()
    db    = Database(cfg)
    db.init()

    show_banner(cfg)

    while True:
        choices = build_menu_choices()
        answer  = questionary.select(
            "SELECT MODULE:",
            choices=choices,
            style=SENTINEL_STYLE,
            use_indicator=True,
        ).ask()

        if answer is None or "Exit" in answer:
            console.print("\n[bold #00ff9f]⚡ SENTINEL terminated. Stay vigilant.[/]\n")
            break
        elif "Email" in answer:
            email_menu(cfg, db)
        elif "Username" in answer:
            username_menu(cfg, db)
        elif "Phone" in answer:
            phone_menu(cfg, db)
        elif "IP" in answer:
            ip_menu(cfg, db)
        elif "Breach" in answer:
            breach_menu(cfg, db)
        elif "Social" in answer:
            social_menu(cfg, db)
        elif "Reports" in answer:
            reports_menu(cfg, db)
        elif "Settings" in answer:
            settings_menu(cfg)
        elif "Telegram" in answer:
            from bot.telegram_bot import start_bot
            start_bot(cfg, db)


# ──────────────────────────────── EMAIL MENU ─────────────────────────────────

def email_menu(cfg, db):
    show_module_header("📧 EMAIL INTELLIGENCE", "#00aaff")

    email = questionary.text(
        "Target email address:",
        style=SENTINEL_STYLE,
        validate=lambda v: True if "@" in v else "Enter a valid email address",
    ).ask()
    if not email:
        return

    scan_options = questionary.checkbox(
        "Scan configuration:",
        choices=[
            questionary.Choice("🔍  Full platform scan (120+ sites)",   checked=True),
            questionary.Choice("⚡  Async mode (faster, parallel)",     checked=True),
            questionary.Choice("💾  Cache results to SQLite",           checked=True),
            questionary.Choice("🔄  Bypass cached results (re-scan)",  checked=False),
            questionary.Choice("📄  Auto-generate HTML report",        checked=False),
            questionary.Choice("📊  Export JSON report",               checked=False),
            questionary.Choice("📋  Export CSV report",                checked=False),
        ],
        style=SENTINEL_STYLE,
    ).ask()
    if not scan_options:
        return

    from modules.email_probe import EmailProbe
    probe   = EmailProbe(cfg, db)
    results = asyncio.run(probe.scan(email, options=scan_options))

    reporter = Reporter(cfg)
    reporter.display_email_results(results)

    if any("HTML" in o for o in scan_options):
        path = reporter.export_html(results, f"email_{email.replace('@','_at_')}")
        console.print(f"\n[bold #00ff9f]📄 HTML report → {path}[/]")
    if any("JSON" in o for o in scan_options):
        path = reporter.export_json(results, f"email_{email.replace('@','_at_')}")
        console.print(f"[bold #00ff9f]📊 JSON report → {path}[/]")
    if any("CSV" in o for o in scan_options):
        path = reporter.export_csv(results, f"email_{email.replace('@','_at_')}")
        console.print(f"[bold #00ff9f]📋 CSV report  → {path}[/]")

    input("\n  Press ENTER to return to main menu...")


# ─────────────────────────────── USERNAME MENU ───────────────────────────────

def username_menu(cfg, db):
    show_module_header("👤 USERNAME OSINT", "#ff9f00")

    username = questionary.text(
        "Target username:",
        style=SENTINEL_STYLE,
        validate=lambda v: True if len(v.strip()) > 0 else "Enter a username",
    ).ask()
    if not username:
        return

    from modules.username_probe import UsernameProbe
    probe   = UsernameProbe(cfg, db)
    results = asyncio.run(probe.scan(username.strip()))

    reporter = Reporter(cfg)
    reporter.display_username_results(results)

    export = questionary.confirm("Export report?", style=SENTINEL_STYLE).ask()
    if export:
        fmt = questionary.select("Format:", choices=["HTML", "JSON", "CSV"],
                                 style=SENTINEL_STYLE).ask()
        if fmt == "HTML":
            reporter.export_html(results, f"username_{username}")
        elif fmt == "JSON":
            reporter.export_json(results, f"username_{username}")
        else:
            reporter.export_csv(results, f"username_{username}")

    input("\n  Press ENTER to return...")


# ──────────────────────────────── PHONE MENU ─────────────────────────────────

def phone_menu(cfg, db):
    show_module_header("📱 PHONE INTELLIGENCE", "#ff00aa")

    phone = questionary.text(
        "Target phone number (E.164 format, e.g. +628123456789):",
        style=SENTINEL_STYLE,
        validate=lambda v: True if v.startswith("+") else "Include country code (+62...)",
    ).ask()
    if not phone:
        return

    from modules.phone_probe import PhoneProbe
    probe   = PhoneProbe(cfg, db)
    results = probe.scan(phone.strip())

    reporter = Reporter(cfg)
    reporter.display_phone_results(results)
    input("\n  Press ENTER to return...")


# ────────────────────────────── IP / DOMAIN MENU ─────────────────────────────

def ip_menu(cfg, db):
    show_module_header("🌐 IP / DOMAIN OSINT", "#aa00ff")

    target = questionary.text(
        "Target IP address or domain:",
        style=SENTINEL_STYLE,
    ).ask()
    if not target:
        return

    from modules.ip_probe import IPProbe
    probe   = IPProbe(cfg, db)
    results = asyncio.run(probe.scan(target.strip()))

    reporter = Reporter(cfg)
    reporter.display_ip_results(results)
    input("\n  Press ENTER to return...")


# ──────────────────────────────── BREACH MENU ────────────────────────────────

def breach_menu(cfg, db):
    show_module_header("🔓 BREACH INSPECTOR", "#ff3333")

    email = questionary.text(
        "Email to check for breaches:",
        style=SENTINEL_STYLE,
        validate=lambda v: True if "@" in v else "Enter a valid email",
    ).ask()
    if not email:
        return

    from modules.breach_probe import BreachProbe
    probe   = BreachProbe(cfg, db)
    results = probe.scan(email.strip())

    reporter = Reporter(cfg)
    reporter.display_breach_results(results)
    input("\n  Press ENTER to return...")


# ──────────────────────────────── SOCIAL MENU ────────────────────────────────

def social_menu(cfg, db):
    show_module_header("🕸️  SOCIAL PROFILER", "#00ffff")

    console.print("[#666666]  Aggregate social footprint from multiple vectors\n[/]")
    query = questionary.text(
        "Full name or username to profile:",
        style=SENTINEL_STYLE,
    ).ask()
    if not query:
        return

    from modules.social_probe import SocialProbe
    probe   = SocialProbe(cfg, db)
    results = asyncio.run(probe.scan(query.strip()))

    reporter = Reporter(cfg)
    reporter.display_social_results(results)
    input("\n  Press ENTER to return...")


# ─────────────────────────────── REPORTS MENU ────────────────────────────────

def reports_menu(cfg, db):
    show_module_header("📊 REPORTS & HISTORY", "#ffff00")

    rows = db.get_all_scans()
    if not rows:
        console.print("\n[#666666]  No saved scans found.[/]\n")
        input("  Press ENTER...")
        return

    table = Table(box=box.SIMPLE_HEAD, border_style="#333333",
                  header_style="bold #00ff9f")
    table.add_column("ID",       style="#666666", width=4)
    table.add_column("Type",     style="#00aaff", width=12)
    table.add_column("Target",   style="#ffffff", width=30)
    table.add_column("Found",    style="#00ff9f", width=6)
    table.add_column("Date",     style="#888888", width=20)

    for row in rows:
        table.add_row(str(row["id"]), row["scan_type"], row["target"],
                      str(row["found_count"]), row["created_at"])

    console.print(table)

    action = questionary.select(
        "Action:",
        choices=["Re-export a report", "Delete a scan", "Back"],
        style=SENTINEL_STYLE,
    ).ask()

    if action == "Re-export a report":
        scan_id = questionary.text("Enter scan ID:", style=SENTINEL_STYLE).ask()
        scan    = db.get_scan_by_id(int(scan_id))
        if scan:
            reporter = Reporter(cfg)
            path = reporter.export_from_db(scan)
            console.print(f"\n[bold #00ff9f]✅ Exported → {path}[/]")
    elif action == "Delete a scan":
        scan_id = questionary.text("Enter scan ID to delete:", style=SENTINEL_STYLE).ask()
        db.delete_scan(int(scan_id))
        console.print("\n[bold #ff3333]🗑  Scan deleted.[/]")

    input("\n  Press ENTER to return...")


# ─────────────────────────────── SETTINGS MENU ───────────────────────────────

def settings_menu(cfg):
    show_module_header("⚙️  SETTINGS & CONFIGURATION", "#888888")

    opts = questionary.select(
        "Configure:",
        choices=[
            "🔑  API Keys (HaveIBeenPwned, NumVerify, IPInfo)",
            "🌍  Proxy settings",
            "⏱   Scan timeout & rate limits",
            "📁  Reports output directory",
            "🗑   Clear all cached data",
            "🔙  Back",
        ],
        style=SENTINEL_STYLE,
    ).ask()

    if opts and "API Keys" in opts:
        console.print("\n[#666666]  Edit .env file with your API keys:\n[/]")
        console.print(f"[#00ff9f]  nano {ROOT}/.env[/]")
    elif opts and "Proxy" in opts:
        proxy = questionary.text(
            "HTTP proxy (e.g. http://127.0.0.1:8080) or leave blank to disable:",
            style=SENTINEL_STYLE,
        ).ask()
        cfg.set("proxy", proxy or "")
        console.print("[bold #00ff9f]  ✅ Proxy updated[/]")
    elif opts and "timeout" in opts:
        timeout = questionary.text("Timeout in seconds (default 10):", style=SENTINEL_STYLE).ask()
        cfg.set("timeout", timeout or "10")
    elif opts and "Clear" in opts:
        confirm = questionary.confirm("Are you sure? This clears ALL cached data.", style=SENTINEL_STYLE).ask()
        if confirm:
            db_path = ROOT / "data" / "sentinel.db"
            if db_path.exists():
                db_path.unlink()
                console.print("[bold #00ff9f]  ✅ Cache cleared[/]")

    input("\n  Press ENTER to return...")


# ──────────────────────────────── ARGPARSE ───────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="SENTINEL OSINT — Advanced Intelligence Framework",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("mode", nargs="?", default="cli",
                        choices=["cli", "web", "bot"],
                        help="Launch mode: cli (default), web, bot")
    parser.add_argument("--email",    help="Direct email scan (non-interactive)")
    parser.add_argument("--username", help="Direct username scan")
    parser.add_argument("--ip",       help="Direct IP/domain scan")
    parser.add_argument("--phone",    help="Direct phone scan")
    parser.add_argument("--output",   default="json",
                        choices=["json", "html", "csv"],
                        help="Output format for direct mode")
    parser.add_argument("--version",  action="version", version="SENTINEL OSINT v2.0.0")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg  = Config()
    db   = Database(cfg)
    db.init()

    if args.mode == "web":
        from web.app import start_web
        start_web(cfg, db)

    elif args.mode == "bot":
        from bot.telegram_bot import start_bot
        start_bot(cfg, db)

    elif args.email:
        from modules.email_probe import EmailProbe
        probe   = EmailProbe(cfg, db)
        results = asyncio.run(probe.scan(args.email))
        reporter = Reporter(cfg)
        reporter.display_email_results(results)
        if args.output == "html":
            reporter.export_html(results, f"email_{args.email.replace('@','_at_')}")
        elif args.output == "json":
            reporter.export_json(results, f"email_{args.email.replace('@','_at_')}")
        elif args.output == "csv":
            reporter.export_csv(results, f"email_{args.email.replace('@','_at_')}")

    elif args.username:
        from modules.username_probe import UsernameProbe
        probe   = UsernameProbe(cfg, db)
        results = asyncio.run(probe.scan(args.username))
        Reporter(cfg).display_username_results(results)

    elif args.ip:
        from modules.ip_probe import IPProbe
        probe   = IPProbe(cfg, db)
        results = asyncio.run(probe.scan(args.ip))
        Reporter(cfg).display_ip_results(results)

    elif args.phone:
        from modules.phone_probe import PhoneProbe
        probe   = PhoneProbe(cfg, db)
        results = probe.scan(args.phone)
        Reporter(cfg).display_phone_results(results)

    else:
        run()
