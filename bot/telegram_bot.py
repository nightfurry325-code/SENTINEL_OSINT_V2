"""bot/telegram_bot.py — Telegram bot interface for SENTINEL OSINT"""
import asyncio
from rich.console import Console

console = Console()

def start_bot(cfg, db):
    if not cfg.telegram_token:
        console.print("\n  [#ff3333]❌ TELEGRAM_BOT_TOKEN not set in .env[/]")
        console.print("  [#555555]Get a token from @BotFather on Telegram[/]\n")
        input("  Press ENTER to return...")
        return

    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    except ImportError:
        console.print("\n  [#ffaa00]⚠ python-telegram-bot not installed[/]")
        console.print("  [#555555]Run: pip install python-telegram-bot --break-system-packages[/]\n")
        input("  Press ENTER to return...")
        return

    console.print(f"\n  [bold #00ff9f]🤖 Starting SENTINEL Telegram Bot...[/]\n")
    asyncio.run(_run_bot(cfg, db))


async def _run_bot(cfg, db):
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    from modules.email_probe    import EmailProbe
    from modules.username_probe import UsernameProbe
    from modules.ip_probe       import IPProbe
    from modules.breach_probe   import BreachProbe
    from core.reporter          import Reporter

    WELCOME = (
        "⚡ *SENTINEL OSINT Bot*\n\n"
        "Intelligence commands:\n"
        "`/email target@example.com` — Email probe\n"
        "`/username johndoe` — Username OSINT\n"
        "`/ip 8.8.8.8` — IP/Domain intel\n"
        "`/breach email@example.com` — Breach check\n"
        "`/help` — Show this message\n\n"
        "_For authorized use only_"
    )

    async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(WELCOME, parse_mode="Markdown")

    async def cmd_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not ctx.args:
            await update.message.reply_text("Usage: /email target@example.com")
            return
        email = ctx.args[0]
        await update.message.reply_text(f"🔍 Scanning email: `{email}`...", parse_mode="Markdown")
        probe   = EmailProbe(cfg, db)
        results = await probe.scan(email)
        found   = results.get("found", [])
        total   = results.get("total_checked", 0)
        dur     = results.get("duration", 0)
        lines   = [f"📧 *Email Report:* `{email}`", f"✅ Found: *{len(found)}* / {total} ({dur}s)\n"]
        for item in found[:20]:
            lines.append(f"• [{item['name']}]({item['url']}) — {item['category']}")
        if len(found) > 20:
            lines.append(f"_...and {len(found)-20} more_")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)

    async def cmd_username(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not ctx.args:
            await update.message.reply_text("Usage: /username johndoe")
            return
        username = ctx.args[0]
        await update.message.reply_text(f"👤 Scanning username: `{username}`...", parse_mode="Markdown")
        probe   = UsernameProbe(cfg, db)
        results = await probe.scan(username)
        found   = results.get("found", [])
        lines   = [f"👤 *Username Report:* `{username}`", f"✅ Found: *{len(found)}*\n"]
        for item in found[:20]:
            lines.append(f"• [{item['name']}]({item['profile_url']}) — {item['category']}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)

    async def cmd_ip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not ctx.args:
            await update.message.reply_text("Usage: /ip 8.8.8.8 or /ip domain.com")
            return
        target  = ctx.args[0]
        await update.message.reply_text(f"🌐 Probing: `{target}`...", parse_mode="Markdown")
        probe   = IPProbe(cfg, db)
        results = await probe.scan(target)
        geo     = results.get("data", {}).get("Geolocation", {})
        shodan  = results.get("data", {}).get("Shodan (free)", {})
        lines   = [
            f"🌐 *IP Report:* `{target}`",
            f"🔎 Resolved: `{results.get('resolved_ip','')}`",
            f"🏳 Country: {geo.get('country','')} | City: {geo.get('city','')}",
            f"🏢 Org: {geo.get('org','')}",
            f"🕳 Open Ports: {shodan.get('open_ports','N/A')}",
            f"⚠ Vulns: {shodan.get('vulns','none')}",
        ]
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_breach(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not ctx.args:
            await update.message.reply_text("Usage: /breach email@example.com")
            return
        email   = ctx.args[0]
        await update.message.reply_text(f"🔓 Checking breaches for: `{email}`...", parse_mode="Markdown")
        probe   = BreachProbe(cfg, db)
        results = probe.scan(email)
        breaches = results.get("breaches", [])
        lines    = [f"🔓 *Breach Report:* `{email}`", f"⚠ Found in *{len(breaches)}* breach(es)\n"]
        for b in breaches[:10]:
            lines.append(f"• *{b.get('Name','')}* — {b.get('BreachDate','')} — {b.get('PwnCount',0):,} records")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(WELCOME, parse_mode="Markdown")

    app = Application.builder().token(cfg.telegram_token).build()
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("email",   cmd_email))
    app.add_handler(CommandHandler("username",cmd_username))
    app.add_handler(CommandHandler("ip",      cmd_ip))
    app.add_handler(CommandHandler("breach",  cmd_breach))
    app.add_handler(CommandHandler("help",    cmd_help))

    console.print("  [bold #00ff9f]✅ Bot running. Press Ctrl+C to stop.[/]\n")
    await app.run_polling(drop_pending_updates=True)
