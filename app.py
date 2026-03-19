from flask import Flask, request, abort
import telebot
from bot_instance import bot
import handlers # Register all bot handlers
import ads
from logger import logger
import os
import threading

app = Flask(__name__)

# Start ad scheduler
ads.start_ads()

# Remove any existing webhook to ensure polling works
try:
    bot.remove_webhook()
    logger.info("Removed old webhook to switch to polling.")
except Exception as e:
    logger.error(f"Could not remove webhook: {e}")

def run_bot():
    logger.info("Bot is now polling for messages in the background...")
    bot.infinity_polling(skip_pending=True)

# Start polling in a background thread
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

@app.route('/')
@app.route('/health')
def health_check():
    """Health check endpoint for Railway/Platform monitoring."""
    logger.info("Health check accessed.")
    return "Bot is actively running in Local Polling mode (Background Thread)!", 200

if __name__ == "__main__":
    # Local dev port or Railway dynamic port
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
