import telebot
from bot_instance import bot
import handlers  # Register all bot handlers
import ads
from logger import logger
import os
import threading
from flask import Flask

app = Flask(__name__)

# Start ad scheduler
ads.start_ads()

# Remove any existing webhook to ensure polling works
try:
    bot.remove_webhook()
    logger.info("Successfully removed old webhook format.")
except Exception as e:
    logger.error(f"Could not remove webhook: {e}")

# Health check endpoint for Render/Railway monitoring
@app.route('/')
@app.route('/health')
def health_check():
    return "Bot is active (Polling Strategy)!", 200

def run_flask():
    """Run Flask in a background thread for health checks."""
    # Use port 8080 or port from env (Render uses dynamic ports)
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Health check server starting on port {port}...")
    try:
        app.run(host="0.0.0.0", port=port, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

def main():
    # Start Flask health check server in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Log the number of handlers for debugging
    handler_count = len(bot.message_handlers)
    logger.info(f"Bot starting with {handler_count} handlers registered.")

    # Run bot polling in the MAIN thread
    logger.info("Bot is now entering infinity polling mode...")
    try:
        bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Bot polling crashed: {e}")

if __name__ == "__main__":
    main()
