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
    logger.info("Removed old webhook to switch to polling.")
except Exception as e:
    logger.error(f"Could not remove webhook: {e}")

# Health check endpoint for Railway monitoring
@app.route('/')
@app.route('/health')
def health_check():
    return "Bot is active and polling!", 200

def run_flask():
    """Run Flask in a background thread for health checks."""
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def main():
    # Start Flask health check server in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Health check server started in background.")

    # Run bot polling in the MAIN thread (this keeps the process alive)
    logger.info("Bot is now polling for messages...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    main()
