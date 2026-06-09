 #  💠SENTINEL OSINT

> **Advanced Open-Source Intelligence Framework**  
> Email · Username · Phone · IP/Domain · Breach · Social

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Platforms](https://img.shields.io/badge/Email%20Sites-120%2B-00ff9f?style=flat-square)]()
[![Username](https://img.shields.io/badge/Username%20Sites-100%2B-ffaa00?style=flat-square)]()
[![Termux](https://img.shields.io/badge/Termux-Compatible-purple?style=flat-square)]()

---

## 📋 Summary

SENTINEL OSINT is a professional-grade intelligence gathering framework. Given an email address, username, phone number, IP, or domain — it probes hundreds of platforms, APIs, and data sources to build a comprehensive intelligence profile.

Built for security researchers, OSINT analysts, and penetration testers.

---

## 🚀 Features

| Module | Description | Sources |
|--------|-------------|---------|
| 📧 **Email Intelligence** | Check email across registered accounts | 120+ platforms |
| 👤 **Username OSINT** | Track username footprint | 100+ sites |
| 📱 **Phone Intelligence** | Carrier, country, line type | NumVerify + heuristics |
| 🌐 **IP / Domain OSINT** | GeoIP, WHOIS, DNS, Shodan, Threat Intel | 5+ APIs |
| 🔓 **Breach Inspector** | Data breach + paste exposure | HaveIBeenPwned |
| 🕸️ **Social Profiler** | Profile aggregation from public APIs | GitHub, Reddit, HN + more |
| 📊 **Report Engine** | HTML, JSON, CSV export | Built-in |
| 🤖 **Telegram Bot** | Full bot interface | python-telegram-bot |
| 🌐 **Web Dashboard** | Flask-based local UI | Built-in |

---

## ⚡ Quick Start (Termux / Android)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/sentinel-osint.git
cd sentinel-osint

# 2. Install
bash install.sh

# 3. Configure (optional but recommended)
nano .env

# 4. Run
python sentinel.py
```

---

## 🖥️ Usage

```bash
# Interactive CLI (recommended)
python sentinel.py

# Web dashboard
python sentinel.py web

# Telegram bot
python sentinel.py bot

# Direct CLI scan
python sentinel.py --email target@example.com
python sentinel.py --username johndoe
python sentinel.py --ip 8.8.8.8
python sentinel.py --phone +628123456789

# With output format
python sentinel.py --email target@example.com --output html
```

---

## 📁 Project Structure

```
sentinel-osint/
├── sentinel.py              # Main entry point (CLI)
├── install.sh               # One-step installer
├── requirements.txt
├── .env.example
│
├── core/
│   ├── banner.py            # ASCII art & headers
│   ├── config.py            # Config manager (.env + JSON)
│   ├── database.py          # SQLite persistence
│   ├── reporter.py          # HTML/JSON/CSV export engine
│   └── utils.py             # Shared utilities
│
├── modules/
│   ├── email_probe.py       # Async email checker (120+ sites)
│   ├── username_probe.py    # Async username checker (100+ sites)
│   ├── phone_probe.py       # Phone intelligence
│   ├── ip_probe.py          # IP/Domain OSINT
│   ├── breach_probe.py      # Breach inspector
│   └── social_probe.py      # Social aggregator
│
├── data/
│   ├── email_services.json  # 120+ email check definitions
│   ├── username_sites.json  # 100+ username site definitions
│   └── sentinel.db          # SQLite database (auto-created)
│
├── web/
│   └── app.py               # Flask web dashboard
│
├── bot/
│   └── telegram_bot.py      # Telegram bot
│
└── reports/                 # Auto-generated reports (HTML/JSON/CSV)
```

---

## ⚙️ API Keys (Optional)

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [HaveIBeenPwned](https://haveibeenpwned.com/API/Key) | Breach checking | Paid key required |
| [IPInfo](https://ipinfo.io) | Geolocation | 50k req/month |
| [NumVerify](https://numverify.com) | Phone validation | 100 req/month |

Add keys to `.env` — the tool works without them but with reduced accuracy.

---

## 📊 Sample Output

```
╭─────────────────────────────────────────────────────────────────────╮
│  📧 EMAIL INTELLIGENCE REPORT                                       │
│  Target: target@gmail.com   Found: 47   Checked: 120   Duration: 8s │
╰─────────────────────────────────────────────────────────────────────╯

  Platform          Category     URL                         Status
  ───────────────────────────────────────────────────────────────────
  Discord           social       https://discord.com         ✅ FOUND
  GitHub            tech         https://github.com          ✅ FOUND
  Google            tech         https://google.com          ✅ FOUND
  Instagram         social       https://instagram.com       ✅ FOUND
  LinkedIn          social       https://linkedin.com        ✅ FOUND
  Netflix           streaming    https://netflix.com         ✅ FOUND
  Spotify           streaming    https://spotify.com         ✅ FOUND
  Steam             gaming       https://steampowered.com    ✅ FOUND
  ...
```

---

## ⚠️ Legal Disclaimer

This tool is intended **for authorized security research and OSINT purposes only**. Users are responsible for ensuring compliance with applicable laws and platform terms of service. The developer assumes no liability for misuse.

---

## 📄 License

MIT License — See [LICENSE](LICENSE)

---

*SENTINEL OSINT — Intelligence. Precision. Speed.*
