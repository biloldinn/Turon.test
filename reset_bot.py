import os
import telebot
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

def reset_bot():
    print("Resetting bot webhook and polling...")
    try:
        # Set a dummy webhook to break any polling
        bot.set_webhook(url="https://localhost/this-is-a-test-to-break-polling")
        print("Webhook set successfully.")
        import time
        time.sleep(2)
        # Remove the webhook
        bot.remove_webhook()
        print("Webhook removed successfully.")
        time.sleep(2)
    except Exception as e:
        print(f"Error resetting bot: {e}")

if __name__ == "__main__":
    reset_bot()
