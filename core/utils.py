"""core/utils.py — Shared utility helpers"""
import re
import ipaddress
from rich.console import Console

console = Console()

def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def validate_ip(target: str) -> bool:
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False

def validate_domain(target: str) -> bool:
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, target))

def console_separator(char="─", width=70, color="#333333"):
    console.print(f"[{color}]{char * width}[/]")

def mask_email(email: str) -> str:
    parts = email.split("@")
    if len(parts) != 2:
        return email
    name, domain = parts
    masked = name[:2] + "*" * (len(name) - 2) if len(name) > 2 else name
    return f"{masked}@{domain}"

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\.]', '_', name)

def truncate(text: str, length: int = 60) -> str:
    return text if len(text) <= length else text[:length - 3] + "..."

CATEGORIES = {
    "social":      "#00aaff",
    "tech":        "#00ff9f",
    "finance":     "#ffaa00",
    "gaming":      "#aa00ff",
    "dating":      "#ff00aa",
    "streaming":   "#ff5500",
    "shopping":    "#ffff00",
    "news":        "#aaaaaa",
    "forum":       "#888888",
    "other":       "#555555",
}

def category_color(cat: str) -> str:
    return CATEGORIES.get(cat.lower(), "#555555")
