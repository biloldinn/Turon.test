from flask import Flask, request, abort
import telebot
from bot_instance import bot
import handlers # Ensure handlers are registered
import ads
from logger import logger
import os

app = Flask(__name__)

# Webhook secret token for security (optional but recommended)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "my_secret_token")

@app.route('/')
def home():
    return "Bot is running with Webhook structure!"

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Handle Telegram Webhook updates."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

@app.route('/api/cron', methods=['GET'])
def cron_trigger():
    """Trigger ads externally (e.g. from Vercel Cron)."""
    ads.send_ad()
    return "Ads triggered successfully", 200

# For local testing only
def run_bot_polling():
    logger.info("Bot starting in polling mode for local test...")
    ads.start_ads()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    # In production (Render/Docker), we might still use the Flask app directly
    port = int(os.environ.get("PORT", 7860))
    # Note: On serverless like Vercel, we don't call app.run()
    app.run(host="0.0.0.0", port=port)
