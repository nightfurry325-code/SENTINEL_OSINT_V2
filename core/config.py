"""core/config.py — Configuration manager"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
ENV_FILE = ROOT / ".env"
CFG_FILE = ROOT / "data" / "config.json"

load_dotenv(ENV_FILE)

class Config:
    DEFAULTS = {
        "timeout":        10,
        "max_workers":    20,
        "proxy":          "",
        "reports_dir":    str(ROOT / "reports"),
        "db_path":        str(ROOT / "data" / "sentinel.db"),
        "user_agent":     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "delay_between":  0.3,
    }

    def __init__(self):
        self._data = dict(self.DEFAULTS)
        self._load_file()

    def _load_file(self):
        CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if CFG_FILE.exists():
            try:
                with open(CFG_FILE) as f:
                    self._data.update(json.load(f))
            except Exception:
                pass

    def get(self, key, default=None):
        # ENV vars override JSON config (e.g. SENTINEL_TIMEOUT)
        env_key = f"SENTINEL_{key.upper()}"
        env_val = os.getenv(env_key)
        if env_val is not None:
            return env_val
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        with open(CFG_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def hibp_key(self):
        return os.getenv("HIBP_API_KEY", "")

    @property
    def ipinfo_key(self):
        return os.getenv("IPINFO_TOKEN", "")

    @property
    def numverify_key(self):
        return os.getenv("NUMVERIFY_KEY", "")

    @property
    def telegram_token(self):
        return os.getenv("TELEGRAM_BOT_TOKEN", "")

    @property
    def proxy(self):
        p = self.get("proxy", "")
        return {"http": p, "https": p} if p else None

    @property
    def timeout(self):
        return int(self.get("timeout", 10))

    @property
    def reports_dir(self):
        d = Path(self.get("reports_dir", str(ROOT / "reports")))
        d.mkdir(parents=True, exist_ok=True)
        return d
