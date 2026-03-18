import time
import telebot
from bot_instance import bot
import handlers
import ads
from logger import logger

# Ensure handlers are registered
# handlers.register_handlers() is already called at the end of handlers.py

def main():
    logger.info("Starting bot in LOCAL POLLING mode...")
    
    # Start the ad scheduler
    ads.start_ads()
    
    # We must remove webhook before polling
    bot.remove_webhook()
    time.sleep(1)
    
    try:
        logger.info("Bot is now polling for messages...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.error(f"Polling error: {e}")

if __name__ == "__main__":
    main()
