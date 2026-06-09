"""modules/breach_probe.py — Data breach inspector (HIBP + extras)"""
import requests
import hashlib
from rich.console import Console

console = Console()

class BreachProbe:
    def __init__(self, cfg, db):
        self.cfg  = cfg
        self.db   = db
        self.headers = {
            "User-Agent":  "SENTINEL-OSINT-v2",
            "hibp-api-key": cfg.hibp_key,
        }

    def scan(self, email: str) -> dict:
        breaches = self._hibp_breaches(email)
        pastes   = self._hibp_pastes(email)
        pwned    = self._pwned_password_count(email)

        result = {
            "scan_type":   "breach",
            "target":      email,
            "found_count": len(breaches),
            "breaches":    breaches,
            "pastes":      pastes,
            "pwned_count": pwned,
        }
        self.db.save_scan("breach", email, result)
        return result

    def _hibp_breaches(self, email: str) -> list:
        if not self.cfg.hibp_key:
            return self._demo_breaches(email)
        try:
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers=self.headers,
                params={"truncateResponse": "false"},
                timeout=self.cfg.timeout,
            )
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return []
        except Exception as e:
            console.print(f"[yellow]⚠ HIBP error: {e}[/]")
        return []

    def _hibp_pastes(self, email: str) -> list:
        if not self.cfg.hibp_key:
            return []
        try:
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/pasteaccount/{email}",
                headers=self.headers,
                timeout=self.cfg.timeout,
            )
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    def _pwned_password_count(self, email: str) -> str:
        """Check how many times email domain appears in password lists (k-anonymity)"""
        try:
            sha1  = hashlib.sha1(email.encode()).hexdigest().upper()
            prefix, suffix = sha1[:5], sha1[5:]
            r = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                timeout=self.cfg.timeout,
            )
            lines = r.text.splitlines()
            for line in lines:
                h, count = line.split(":")
                if h == suffix:
                    return int(count)
            return 0
        except Exception:
            return "N/A"

    def _demo_breaches(self, email: str) -> list:
        """Return info message when no API key configured"""
        console.print("\n  [#ffaa00]⚠  HIBP API key not set. Add HIBP_API_KEY to .env[/]")
        console.print("  [#555555]Get your free key at: https://haveibeenpwned.com/API/Key[/]\n")
        return []
