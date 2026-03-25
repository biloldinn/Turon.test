import os
import json
from dotenv import load_dotenv
from logger import logger

load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN') or '8580639697:AAFPv5TYWiWFXFxaMYQWPN7JzCwMUMYkVIQ'
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('WEBHOOK_URL') or 'https://telegram-versel-bot.onrender.com'

if not TOKEN:
    # Use a safe logger message but don't hardcode a secret token here
    logger.error("BOT_TOKEN is missing from environment!")

# Admin IDs - supports multiple
admin_id_env = os.environ.get('ADMIN_ID') or os.environ.get('TELEGRAM_ADMIN_ID') or os.environ.get('ADMIN_IDS') or "7985206085"
ADMIN_IDS = [int(i.strip()) for i in admin_id_env.split(',') if i.strip().isdigit()]

# Add default admin IDs if not present
default_admins = [7985206085, 534958748, 1506545257]
for admin_id in default_admins:
    if admin_id not in ADMIN_IDS:
        ADMIN_IDS.append(admin_id)

ADMIN_IDS = list(set(ADMIN_IDS)) # Unique IDs only

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS are not set!")

CONFIG_FILE = 'bot_config.json'

DEFAULT_CONFIG = {
    "ad_text": os.environ.get('DEFAULT_AD_TEXT', "Sizning reklamangiz shu yerda bo'lishi mumkin!"),
    "ad_photo": os.environ.get('DEFAULT_AD_PHOTO', None),
    "ad_interval_minutes": int(os.environ.get('DEFAULT_AD_INTERVAL', 5)),
    "is_ad_active": os.environ.get('DEFAULT_AD_ACTIVE', 'false').lower() == 'true',
    "is_forwarding_active": os.environ.get('DEFAULT_FWD_ACTIVE', 'true').lower() == 'true',
    "source_group": os.environ.get('SOURCE_GROUP'),
    "destination_group": os.environ.get('DESTINATION_GROUP'),
    "ad_target_group": os.environ.get('AD_TARGET_GROUP')
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
