# === COLAB CELL: Telegram Token Setup (Task 8.1) ===
# Run this cell to securely enter your bot token

import os
from getpass import getpass

token = getpass("Enter your TELEGRAM_BOT_TOKEN: ")
os.environ["TELEGRAM_BOT_TOKEN"] = token
print("Token saved ✅")


# === COLAB CELL: Start Bot (Task 8.5) ===
# Run this cell LAST — it blocks while the bot is polling

from sheets import load_commission_sheet
from bot import main

main()
