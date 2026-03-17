import telebot
import os
import sys

# Set your Bot Token here or use environment variable
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("Error: BOT_TOKEN not found!")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

def set_webhook(url):
    webhook_url = f"{url.rstrip('/')}/webhook"
    print(f"Setting webhook to: {webhook_url}")
    result = bot.set_webhook(url=webhook_url)
    if result:
        print("✅ Webhook muvaffaqiyatli saqlandi!")
    else:
        print("❌ Webhookni saqlashda xatolik!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python set_webhook.py <DEPLOYED_URL>")
        print("Example: python set_webhook.py https://telegram-versel-bot.up.railway.app")
    else:
        set_webhook(sys.argv[1])
