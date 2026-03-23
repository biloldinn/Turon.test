import os
import json
from dotenv import load_dotenv
from logger import logger

load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN') or '8580639697:AAFPv5TYWiWFXFxaMYQWPN7JzCwMUMYkVIQ'
# Admin IDs - supports multiple
admin_id_env = os.environ.get('ADMIN_ID') or os.environ.get('TELEGRAM_ADMIN_ID') or "7985206085"
ADMIN_IDS = [int(i.strip()) for i in admin_id_env.split(',') if i.strip().isdigit()]
# Add the second admin ID if not already present
if 1506545257 not in ADMIN_IDS:
    ADMIN_IDS.append(1506545257)

WEBHOOK_URL = os.environ.get('WEBHOOK_URL') or 'https://telegram-versel-bot-production.up.railway.app'

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS are not set!")

CONFIG_FILE = 'bot_config.json'

DEFAULT_CONFIG = {
    "ad_text": "Sizning reklamangiz shu yerda bo'lishi mumkin!",
    "ad_photo": None,
    "ad_interval_minutes": 5,
    "is_ad_active": False,
    "is_forwarding_active": True,
    "source_group": None,
    "destination_group": None,
    "ad_target_group": None
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("bot_config.json is empty. Using defaults.")
                    return DEFAULT_CONFIG.copy()
                data = json.loads(content)
                return {**DEFAULT_CONFIG, **data}
        except Exception as e:
            logger.error(f"Error loading config: {e}. Using defaults.")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

config = load_config()
