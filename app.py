import telebot
from bot_instance import bot
import handlers  # Register all bot handlers
import ads
import pinger
from logger import logger
import os
from flask import Flask, request
from config import TOKEN, WEBHOOK_URL

app = Flask(__name__)

# Start background systems
ads.start_ads()
pinger.start_pinger()

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
    # On Render, Railway, etc., 'PORT' is set automatically.
    port = int(os.environ.get("PORT", 8080))
    is_cloud = os.environ.get('PORT') or os.environ.get('RENDER') or os.environ.get('RAILWAY_STATIC_URL')
    
    if is_cloud and WEBHOOK_URL:
        logger.info(f"Cloud environment detected (Render/Railway). Using Webhook strategy.")
        try:
            # Construct full URL: https://your-domain.render.com/TOKEN
            # Ensure the webhook_url from environment is used
            bot.remove_webhook()
            webhook_full_url = f"{WEBHOOK_URL.rstrip('/')}/{TOKEN}"
            
            logger.info(f"Setting webhook to: {webhook_full_url}")
            if bot.set_webhook(url=webhook_full_url, allowed_updates=['message', 'callback_query', 'channel_post']):
                logger.info("✅ Webhook set successfully.")
            else:
                logger.error("❌ Failed to set webhook.")
            
            # Start Flask server
            logger.info(f"Starting Webhook server on port {port}...")
            # For Render/Railway, we must listen on 0.0.0.0
            app.run(host="0.0.0.0", port=port)
            
        except Exception as e:
            logger.error(f"Critical error in Webhook setup: {e}. Attempting Polling fallback...")
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
    else:
        # Local development or no WEBHOOK_URL - use Polling
        logger.info("Local environment detected (or WEBHOOK_URL missing). Starting Polling...")
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True, logger_level=logging.INFO)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")

if __name__ == "__main__":
    main()
