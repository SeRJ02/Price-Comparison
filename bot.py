# bot.py — Main Telegram bot entry point

import os
import traceback
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from utils import detect_platform
from extractor import extract_product
from searcher import search_all_platforms
from matcher import match_all_platforms
from sheets import load_commission_sheet, get_commission
from formatter import format_full_message

# Module-level commission map — loaded at startup
commission_map = {}

START_MESSAGE = """👋 Welcome to EarnKaro Price Bot!

Send me any product link from:
- Amazon.in
- Flipkart
- Myntra
- Hamara Mall

I'll compare prices across all platforms and show your EarnKaro commission instantly."""


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(START_MESSAGE)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler — runs on every user message."""
    url = update.message.text.strip()

    # Step 1 — Validate it's a known platform URL
    try:
        platform = detect_platform(url)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please send a product link from Amazon, Flipkart, Myntra, or Hamara Mall."
        )
        return

    # Step 2 — Acknowledge immediately
    await update.message.reply_text("⏳ Searching across platforms, give me a moment...")

    try:
        # Step 3 — Extract product from source URL
        product = extract_product(url)

        if not product.get("name"):
            warnings = product.get("warnings", [])
            print(f"Extraction failed: {warnings}")
            await update.message.reply_text(
                "❌ Couldn't extract product details from that link. Please try a different one."
            )
            return

        # Step 4 — Search all other platforms
        search_results = search_all_platforms(product, skip_platform=platform)

        # Step 5 — Match and score
        matches = match_all_platforms(product, search_results)

        # Step 6 — Get commission
        commission = get_commission(product.get("category", ""), commission_map)

        # Step 7 — Format and send
        message = format_full_message(product, matches, commission)
        await update.message.reply_text(message)

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(
            "❌ Something went wrong. Please try again or send a different link."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Catch all unhandled exceptions."""
    print(f"Error: {context.error}")
    traceback.print_exc()


def main():
    """Load commission map, build bot, start polling."""
    global commission_map

    # Load .env file if present
    env_path = os.path.join(os.path.dirname(__file__) or ".", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set. Use the token setup cell or create a .env file.")
        return

    # Load commissions
    try:
        commission_map = load_commission_sheet()
        print(f"✅ Loaded {len(commission_map)} commission categories")
    except Exception as e:
        print(f"⚠️ Could not load commission sheet: {e}")
        print("   Bot will run without commission data.")

    request = HTTPXRequest(connection_pool_size=20, read_timeout=120, write_timeout=120, connect_timeout=30)
    app = Application.builder().token(token).request(request).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    threading.Thread(target=run_health_server, daemon=True).start()
    print("🤖 Bot is running... Send it a product link on Telegram")
    app.run_polling()


if __name__ == "__main__":
    main()
