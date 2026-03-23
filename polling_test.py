import telebot
import os
import sys
import threading
import time
from dotenv import load_dotenv

# Set encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
TOKEN = os.environ.get('BOT_TOKEN')

def test_polling():
    if not TOKEN:
        print("ERROR: BOT_TOKEN not found in .env")
        return

    print("Checking for polling conflicts...")
    bot = telebot.TeleBot(TOKEN)
    
    # Try removing webhook first (standard procedure)
    bot.remove_webhook()
    time.sleep(1)

    try:
        # Start a thread to stop polling after 10 seconds
        def stop_polling():
            time.sleep(10)
            print("\nTest completed: Stopping polling...")
            bot.stop_polling()
            
        threading.Thread(target=stop_polling, daemon=True).start()
        
        print("Bot is now polling (10s)... If you see a 409 error, another instance is running.")
        bot.infinity_polling(skip_pending=True)
        print("Polling finished without immediate conflict.")

    except Exception as e:
        if "409" in str(e):
            print(f"\nCONFLICT ERROR (409): Another instance is still running! {e}")
        else:
            print(f"\nERROR: {e}")

if __name__ == "__main__":
    test_polling()
