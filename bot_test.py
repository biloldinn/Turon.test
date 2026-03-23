import telebot
import os
import sys
from dotenv import load_dotenv

# Set encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
TOKEN = os.environ.get('BOT_TOKEN')

def test_bot():
    if not TOKEN:
        print("ERROR: BOT_TOKEN not found in .env")
        return

    print(f"Connecting to Telegram with token: {TOKEN[:10]}...")
    bot = telebot.TeleBot(TOKEN)
    try:
        me = bot.get_me()
        print("SUCCESS! Bot is connected.")
        print(f"Bot Name: {me.first_name}")
        print(f"Bot Username: @{me.username}")
    except Exception as e:
        print(f"FAILED! Error: {e}")

if __name__ == "__main__":
    test_bot()
