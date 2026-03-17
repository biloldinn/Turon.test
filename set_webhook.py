import telebot
import os
import sys
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("Error: BOT_TOKEN not found in .env")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

def set_webhook(url):
    webhook_url = f"{url.rstrip('/')}/api/webhook"
    print(f"Setting webhook to: {webhook_url}")
    result = bot.set_webhook(url=webhook_url)
    if result:
        print("✅ Webhook successfully set!")
    else:
        print("❌ Failed to set webhook.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python set_webhook.py <YOUR_DEPLOYED_URL>")
        print("Example: python set_webhook.py https://my-bot.vercel.app")
    else:
        set_webhook(sys.argv[1])
