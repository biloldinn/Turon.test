import telebot
from bot_instance import bot
import handlers  # Register all bot handlers
import ads
from logger import logger
import os
from flask import Flask, request
from config import TOKEN, WEBHOOK_URL

app = Flask(__name__)

# Start ad scheduler
ads.start_ads()

# Webhook route
@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    """Receive updates from Telegram."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Forbidden", 403

# Health check endpoints
@app.route('/')
@app.route('/health')
def health_check():
    return "Bot is active (Webhook Strategy)!", 200

def main():
    # Detect if we should use Webhook or Polling
    # If we are on Railway or have a WEBHOOK_URL, use Webhook
    is_railway = os.environ.get('RAILWAY_STATIC_URL') or os.environ.get('PORT')
    
    if is_railway and WEBHOOK_URL:
        logger.info("Railway environment detected. Setting up Webhook...")
        try:
            bot.remove_webhook()
            # Construct full URL: https://domain.com/TOKEN
            webhook_full_url = f"{WEBHOOK_URL.rstrip('/')}/{TOKEN}"
            bot.set_webhook(url=webhook_full_url)
            logger.info(f"Webhook set successfully to: {webhook_full_url}")
            
            # Start Flask server (Main thread)
            port = int(os.environ.get("PORT", 8080))
            logger.info(f"Starting Webhook server on port {port}...")
            app.run(host="0.0.0.0", port=port)
        except Exception as e:
            logger.error(f"Webhook setup failed: {e}. Falling back to polling.")
            bot.infinity_polling(skip_pending=True)
    else:
        # Local development - use Polling
        logger.info("Local environment detected. Starting Polling...")
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")

if __name__ == "__main__":
    main()
