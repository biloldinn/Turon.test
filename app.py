from flask import Flask, request, abort
import telebot
from bot_instance import bot
import handlers # Register all bot handlers
import ads
from logger import logger
import os
import time

app = Flask(__name__)

# Start ad scheduler
ads.start_ads()

# Auto-set webhook if WEBHOOK_URL is provided
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
if WEBHOOK_URL:
    logger.info(f"Setting webhook to {WEBHOOK_URL}/webhook...")
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    logger.info("Webhook set successfully.")
else:
    logger.warning("WEBHOOK_URL not found in environment. Skipping auto-webhook setup.")

@app.route('/')
@app.route('/health')
def health_check():
    """Health check endpoint for Railway/Platform monitoring."""
    logger.info("Health check accessed.")
    return "Bot is active and listening for Webhooks!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates via Webhook."""
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            logger.info(f"Webhook received: {json_string[:50]}...")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
        else:
            logger.warning(f"Unexpected Content-Type: {request.headers.get('content-type')}")
            abort(403)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return 'Internal Error', 500

if __name__ == "__main__":
    # Local dev port or Railway dynamic port
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
