import telebot
from bot_instance import bot
import handlers  # Register all bot handlers
import ads
import pinger
import logging
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
    # Render dynamic port
    port = int(os.environ.get("PORT", 8080))
    
    # Try multiple ways to get the public URL
    final_webhook_url = os.environ.get('RENDER_EXTERNAL_URL') or WEBHOOK_URL
    
    if final_webhook_url:
        logger.info(f"Setting up Webhook: {final_webhook_url}")
        try:
            bot.remove_webhook()
            webhook_full_url = f"{final_webhook_url.rstrip('/')}/{TOKEN}"
            bot.set_webhook(url=webhook_full_url, allowed_updates=['message', 'callback_query', 'channel_post'])
            logger.info("✅ Webhook configured.")
        except Exception as e:
            logger.error(f"Webhook setup failed: {e}. Bot might not receive messages but server is starting.")
    
    # ALWAYS start Flask server for Render health checks
    logger.info(f"Starting server on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
