import os
import json
from dotenv import load_dotenv
from logger import logger

load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN') or '8580639697:AAFPv5TYWiWFXFxaMYQWPN7JzCwMUMYkVIQ'
WEBHOOK_URL = os.environ.get('WEBHOOK_URL') or 'https://telegram-versel-bot-production.up.railway.app'
ADMIN_IDS = [7985206085, 534958748, 1506545257] # Original, User, and New Admin
# Plus any from environment
env_admins = os.environ.get('ADMIN_IDS') or os.environ.get('ADMIN_ID')
if env_admins:
    for a in str(env_admins).split(','):
        try: ADMIN_IDS.append(int(a.strip()))
        except: pass
ADMIN_IDS = list(set(ADMIN_IDS)) # Unique IDs only

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
