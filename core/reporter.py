"""core/reporter.py — Multi-format report engine (terminal, HTML, JSON, CSV)"""
import json
import csv
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

class Reporter:
    def __init__(self, cfg):
        self.reports_dir = cfg.reports_dir
        self.timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ─────────────────────────── TERMINAL DISPLAY ────────────────────────────

    def display_email_results(self, results: dict):
        email   = results.get("target", "")
        found   = results.get("found",  [])
        not_found = results.get("not_found", [])
        errors  = results.get("errors", [])
        duration = results.get("duration", 0)

        console.print()
        console.print(Panel(
            f"[bold #ffffff]Target:[/] [#00aaff]{email}[/]   "
            f"[bold #00ff9f]Found: {len(found)}[/]   "
            f"[#ff3333]Not Found: {len(not_found)}[/]   "
            f"[#888888]Errors: {len(errors)}[/]   "
            f"[#555555]Duration: {duration:.1f}s[/]",
            title="[bold #00ff9f]📧 EMAIL INTELLIGENCE REPORT[/]",
            border_style="#333333", box=box.ROUNDED,
        ))
        console.print()

        if found:
            t = Table(box=box.SIMPLE_HEAD, border_style="#333333",
                      header_style="bold #00ff9f", show_footer=False)
            t.add_column("Platform",  style="#ffffff",  width=22)
            t.add_column("Category", style="#888888",  width=12)
            t.add_column("URL",       style="#00aaff",  width=40)
            t.add_column("Status",    style="#00ff9f",  width=10)
            t.add_column("Method",    style="#555555",  width=10)

            for item in sorted(found, key=lambda x: x["name"]):
                t.add_row(
                    item["name"],
                    item.get("category", "other"),
                    item.get("url", ""),
                    "✅ FOUND",
                    item.get("method", ""),
                )
            console.print(t)
        else:
            console.print("[#555555]  No registered accounts found.[/]\n")

    def display_username_results(self, results: dict):
        username  = results.get("target", "")
        found     = results.get("found", [])
        not_found = results.get("not_found", [])
        duration  = results.get("duration", 0)

        console.print()
        console.print(Panel(
            f"[bold #ffffff]Username:[/] [#ffaa00]{username}[/]   "
            f"[bold #00ff9f]Found: {len(found)}[/]   "
            f"[#ff3333]Not Found: {len(not_found)}[/]   "
            f"[#555555]{duration:.1f}s[/]",
            title="[bold #ffaa00]👤 USERNAME OSINT REPORT[/]",
            border_style="#333333", box=box.ROUNDED,
        ))
        console.print()

        if found:
            t = Table(box=box.SIMPLE_HEAD, border_style="#333333", header_style="bold #ffaa00")
            t.add_column("Platform",    style="#ffffff",  width=22)
            t.add_column("Category",   style="#888888",  width=12)
            t.add_column("Profile URL", style="#00aaff",  width=50)

            for item in sorted(found, key=lambda x: x["name"]):
                t.add_row(item["name"], item.get("category","other"), item.get("profile_url",""))
            console.print(t)

    def display_phone_results(self, results: dict):
        phone = results.get("target", "")
        data  = results.get("data", {})

        console.print()
        console.print(Panel(
            f"[bold #ffffff]Phone:[/] [#ff00aa]{phone}[/]",
            title="[bold #ff00aa]📱 PHONE INTELLIGENCE REPORT[/]",
            border_style="#333333", box=box.ROUNDED,
        ))
        console.print()

        t = Table(box=box.SIMPLE_HEAD, border_style="#333333", header_style="bold #ff00aa",
                  show_header=False)
        t.add_column("Field",  style="#888888", width=22)
        t.add_column("Value",  style="#ffffff",  width=40)

        for k, v in data.items():
            t.add_row(k.replace("_", " ").title(), str(v) if v else "[#555555]N/A[/]")
        console.print(t)

    def display_ip_results(self, results: dict):
        target = results.get("target", "")
        data   = results.get("data", {})

        console.print()
        console.print(Panel(
            f"[bold #ffffff]Target:[/] [#aa00ff]{target}[/]",
            title="[bold #aa00ff]🌐 IP / DOMAIN OSINT REPORT[/]",
            border_style="#333333", box=box.ROUNDED,
        ))
        console.print()

        for section, items in data.items():
            if not items:
                continue
            t = Table(title=f"[bold #aa00ff]{section}[/]", box=box.SIMPLE_HEAD,
                      border_style="#333333", show_header=False)
            t.add_column("Field", style="#888888", width=22)
            t.add_column("Value", style="#ffffff",  width=50)
            for k, v in items.items():
                t.add_row(k.replace("_", " ").title(), str(v) if v else "[#555555]N/A[/]")
            console.print(t)
            console.print()

    def display_breach_results(self, results: dict):
        email    = results.get("target", "")
        breaches = results.get("breaches", [])
        pastes   = results.get("pastes",   [])

        console.print()
        console.print(Panel(
            f"[bold #ffffff]Email:[/] [#ff3333]{email}[/]   "
            f"[bold #ff3333]Breaches: {len(breaches)}[/]   "
            f"[#ffaa00]Pastes: {len(pastes)}[/]",
            title="[bold #ff3333]🔓 BREACH INSPECTOR REPORT[/]",
            border_style="#ff3333", box=box.ROUNDED,
        ))
        console.print()

        if breaches:
            t = Table(box=box.SIMPLE_HEAD, border_style="#333333", header_style="bold #ff3333")
            t.add_column("Service",    style="#ffffff",  width=20)
            t.add_column("Date",       style="#888888",  width=12)
            t.add_column("Records",    style="#ffaa00",  width=12)
            t.add_column("Data Types", style="#aaaaaa",  width=40)
            for b in breaches:
                t.add_row(
                    b.get("Name",""),
                    b.get("BreachDate",""),
                    f"{b.get('PwnCount',0):,}",
                    ", ".join(b.get("DataClasses", [])[:4]),
                )
            console.print(t)
        else:
            console.print("[#555555]  No breach records found for this email.[/]\n")

    def display_social_results(self, results: dict):
        console.print()
        data = results.get("profiles", {})
        if not data:
            console.print("[#555555]  No social profiles found.[/]\n")
            return

        t = Table(box=box.SIMPLE_HEAD, border_style="#333333", header_style="bold #00ffff")
        t.add_column("Platform",  style="#ffffff",  width=18)
        t.add_column("Username",  style="#00ffff",  width=20)
        t.add_column("URL",       style="#00aaff",  width=50)
        t.add_column("Bio",       style="#888888",  width=30)

        for platform, info in data.items():
            t.add_row(platform, info.get("username",""), info.get("url",""),
                      info.get("bio","")[:30])
        console.print(t)

    # ─────────────────────────────── EXPORTS ─────────────────────────────────

    def _path(self, name: str, ext: str) -> Path:
        return self.reports_dir / f"{name}_{self.timestamp}.{ext}"

    def export_json(self, results: dict, name: str) -> str:
        path = self._path(name, "json")
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        return str(path)

    def export_csv(self, results: dict, name: str) -> str:
        path  = self._path(name, "csv")
        found = results.get("found", [])
        if found:
            with open(path, "w", newline="") as f:
                if found:
                    writer = csv.DictWriter(f, fieldnames=found[0].keys())
                    writer.writeheader()
                    writer.writerows(found)
        return str(path)

    def export_html(self, results: dict, name: str) -> str:
        path    = self._path(name, "html")
        target  = results.get("target", "")
        found   = results.get("found", [])
        scan_type = results.get("scan_type", "email")
        ts      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rows = ""
        for item in found:
            rows += f"""
            <tr>
                <td>{item.get('name','')}</td>
                <td><span class="badge badge-{item.get('category','other')}">{item.get('category','other')}</span></td>
                <td><a href="{item.get('url','')}#{item.get('profile_url','')}" target="_blank">{item.get('url','')}</a></td>
                <td><span class="found">✅ FOUND</span></td>
                <td>{item.get('method','')}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SENTINEL OSINT — {target}</title>
<style>
  :root{{--bg:#0a0a0f;--surface:#111118;--border:#1e1e2e;--accent:#00ff9f;--blue:#00aaff;--text:#e0e0e0;--muted:#555}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Courier New',monospace;padding:24px}}
  .header{{border-bottom:1px solid var(--border);padding-bottom:16px;margin-bottom:24px}}
  .title{{font-size:28px;color:var(--accent);font-weight:700;letter-spacing:2px}}
  .subtitle{{color:var(--muted);font-size:13px;margin-top:4px}}
  .stats{{display:flex;gap:24px;margin:20px 0;flex-wrap:wrap}}
  .stat{{background:var(--surface);border:1px solid var(--border);padding:12px 20px;border-radius:6px;text-align:center}}
  .stat .num{{font-size:28px;font-weight:700;color:var(--accent)}}
  .stat .lbl{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}}
  table{{width:100%;border-collapse:collapse;margin-top:16px}}
  th{{background:var(--surface);color:var(--accent);padding:10px 14px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid var(--border)}}
  td{{padding:9px 14px;border-bottom:1px solid var(--border);font-size:13px}}
  tr:hover td{{background:rgba(0,255,159,0.03)}}
  a{{color:var(--blue);text-decoration:none}}
  a:hover{{text-decoration:underline}}
  .found{{color:var(--accent)}}
  .badge{{padding:2px 8px;border-radius:3px;font-size:11px;text-transform:uppercase;letter-spacing:.5px}}
  .badge-social{{background:#00aaff22;color:#00aaff}}
  .badge-tech{{background:#00ff9f22;color:#00ff9f}}
  .badge-gaming{{background:#aa00ff22;color:#aa00ff}}
  .badge-dating{{background:#ff00aa22;color:#ff00aa}}
  .badge-finance{{background:#ffaa0022;color:#ffaa00}}
  .badge-streaming{{background:#ff550022;color:#ff5500}}
  .badge-other{{background:#55555522;color:#888}}
  .footer{{margin-top:32px;padding-top:16px;border-top:1px solid var(--border);color:var(--muted);font-size:11px;text-align:center}}
</style>
</head>
<body>
<div class="header">
  <div class="title">⚡ SENTINEL OSINT</div>
  <div class="subtitle">Intelligence Report — {scan_type.upper()} scan — Generated: {ts}</div>
</div>
<div class="stats">
  <div class="stat"><div class="num">{len(found)}</div><div class="lbl">Accounts Found</div></div>
  <div class="stat"><div class="num">{results.get('total_checked',0)}</div><div class="lbl">Sites Checked</div></div>
  <div class="stat"><div class="num">{results.get('duration',0):.1f}s</div><div class="lbl">Scan Duration</div></div>
  <div class="stat"><div class="num">{target}</div><div class="lbl">Target</div></div>
</div>
<table>
  <thead><tr><th>Platform</th><th>Category</th><th>URL</th><th>Status</th><th>Method</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
<div class="footer">SENTINEL OSINT v2.0.0 — For authorized intelligence gathering only</div>
</body></html>"""

        with open(path, "w") as f:
            f.write(html)
        return str(path)

    def export_from_db(self, scan: dict) -> str:
        results = json.loads(scan.get("results", "{}"))
        name    = f"{scan['scan_type']}_{scan['target'].replace('@','_at_')}"
        return self.export_html(results, name)
