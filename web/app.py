"""web/app.py — Flask web dashboard for SENTINEL OSINT"""
import asyncio
import json
from flask import Flask, render_template, request, jsonify
from pathlib import Path

ROOT = Path(__file__).parent.parent

def start_web(cfg, db):
    from rich.console import Console
    Console().print(f"\n  [bold #00ff9f]🌐 SENTINEL Web Dashboard starting...[/]")
    Console().print(f"  [#00aaff]Open: http://127.0.0.1:5000[/]\n")

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = "sentinel_osint_v2"

    @app.route("/")
    def index():
        scans = db.get_all_scans(limit=20)
        return render_template("dashboard.html", scans=scans)

    @app.route("/api/scan/email", methods=["POST"])
    def scan_email():
        from modules.email_probe import EmailProbe
        email   = request.json.get("email", "")
        probe   = EmailProbe(cfg, db)
        results = asyncio.run(probe.scan(email))
        return jsonify(results)

    @app.route("/api/scan/username", methods=["POST"])
    def scan_username():
        from modules.username_probe import UsernameProbe
        username = request.json.get("username", "")
        probe    = UsernameProbe(cfg, db)
        results  = asyncio.run(probe.scan(username))
        return jsonify(results)

    @app.route("/api/scan/ip", methods=["POST"])
    def scan_ip():
        from modules.ip_probe import IPProbe
        target  = request.json.get("target", "")
        probe   = IPProbe(cfg, db)
        results = asyncio.run(probe.scan(target))
        return jsonify(results)

    @app.route("/api/scan/breach", methods=["POST"])
    def scan_breach():
        from modules.breach_probe import BreachProbe
        email   = request.json.get("email", "")
        probe   = BreachProbe(cfg, db)
        results = probe.scan(email)
        return jsonify(results)

    @app.route("/api/history")
    def history():
        return jsonify(db.get_all_scans())

    app.run(host="0.0.0.0", port=5000, debug=False)
