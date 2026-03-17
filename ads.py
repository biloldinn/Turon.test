import time
from apscheduler.schedulers.background import BackgroundScheduler
from bot_instance import bot
from config import config, save_config
from logger import logger

scheduler = BackgroundScheduler()

def send_ad():
    cfg = config
    target_id = cfg.get('ad_target_group')
    
    # If ad_target_group is not set, use destination_group as a single target
    if not target_id:
        target_id = cfg.get('destination_group')

    if not cfg.get('is_ad_active') or not target_id:
        logger.warning("Ad system active but no target group configured.")
        return

    try:
        # Send to only ONE target_id
        if cfg.get('ad_photo'):
            bot.send_photo(target_id, cfg['ad_photo'], caption=cfg.get('ad_text'), parse_mode='HTML')
        elif cfg.get('ad_text'):
            bot.send_message(target_id, cfg['ad_text'], parse_mode='HTML')
        logger.info(f"Ad sent successfully to {target_id}")
    except Exception as e:
        logger.error(f"Failed to send ad: {e}")

def reschedule_ads():
    scheduler.remove_all_jobs()
    if config.get('is_ad_active') and config.get('ad_interval_minutes', 0) > 0:
        scheduler.add_job(send_ad, 'interval', minutes=config['ad_interval_minutes'], id='ad_job')
        logger.info(f"Ad job scheduled every {config['ad_interval_minutes']} minutes")

def start_ads():
    if not scheduler.running:
        scheduler.start()
    reschedule_ads()
