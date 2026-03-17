from flask import Flask, request, abort
import telebot
from bot_instance import bot
import handlers # Ensure handlers are registered
import ads
from logger import logger
import os

app = Flask(__name__)

# Start the ad scheduler once on initialization
ads.start_ads()

@app.route('/')
def home():
    return "Bot is alive and listening for Webhooks!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram Webhook updates."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

if __name__ == "__main__":
    # Local development run
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)
