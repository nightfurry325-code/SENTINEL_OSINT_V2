#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#   SENTINEL OSINT v2.0.0 — Installer
#   Compatible: Termux (Android) / Ubuntu / Debian / macOS
# ═══════════════════════════════════════════════════════════════════

set -e

CYAN="\033[1;36m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

echo -e "${CYAN}"
echo "  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗"
echo "  ╚════╝  ██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║"
echo "    OSINT  █████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║"
echo "  ╚════╝  ██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║"
echo "          ███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗██████║"
echo "          ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝"
echo -e "${RESET}"
echo -e "${GREEN}  SENTINEL OSINT v2.0.0 — Installer${RESET}"
echo ""

# ── Detect environment ────────────────────────────────────────────
if [ -d "/data/data/com.termux" ]; then
    echo -e "${YELLOW}  📱 Detected: Termux (Android)${RESET}"
    ENV="termux"
else
    echo -e "${YELLOW}  🐧 Detected: Linux/macOS${RESET}"
    ENV="linux"
fi

# ── Python check ─────────────────────────────────────────────────
echo -e "\n${CYAN}[1/4] Checking Python...${RESET}"
python3 --version || { echo -e "${RED}  ❌ Python3 not found. Install it first.${RESET}"; exit 1; }
pip3 --version    || { echo -e "${RED}  ❌ pip3 not found.${RESET}"; exit 1; }
echo -e "${GREEN}  ✅ Python OK${RESET}"

# ── Install dependencies ─────────────────────────────────────────
echo -e "\n${CYAN}[2/4] Installing Python dependencies...${RESET}"
if [ "$ENV" = "termux" ]; then
    pip install -r requirements.txt --break-system-packages --quiet
else
    pip3 install -r requirements.txt --quiet
fi
echo -e "${GREEN}  ✅ Dependencies installed${RESET}"

# ── Create .env from template ────────────────────────────────────
echo -e "\n${CYAN}[3/4] Setting up configuration...${RESET}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}  ✅ .env created from template${RESET}"
    echo -e "${YELLOW}  ⚠  Edit .env to add API keys (optional but recommended)${RESET}"
else
    echo -e "${GREEN}  ✅ .env already exists${RESET}"
fi

# ── Create directories ───────────────────────────────────────────
mkdir -p reports data

# ── Permissions ──────────────────────────────────────────────────
echo -e "\n${CYAN}[4/4] Setting permissions...${RESET}"
chmod +x sentinel.py
echo -e "${GREEN}  ✅ Executable set${RESET}"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}  ✅ SENTINEL OSINT installed successfully!${RESET}"
echo ""
echo -e "  Start CLI:   ${GREEN}python sentinel.py${RESET}"
echo -e "  Web UI:      ${GREEN}python sentinel.py web${RESET}"
echo -e "  Telegram:    ${GREEN}python sentinel.py bot${RESET}"
echo -e "  Direct scan: ${GREEN}python sentinel.py --email test@example.com${RESET}"
echo -e "${GREEN}═══════════════════════════════════════════════════${RESET}"
echo ""
