import time
from apscheduler.schedulers.background import BackgroundScheduler
from bot_instance import bot
from config import config, save_config
from logger import logger

scheduler = BackgroundScheduler()

def send_ad(force=False):
    cfg = config
    # Ads must ONLY fall into the destination_group (info receiver)
    target_id = cfg.get('destination_group')

    if not target_id:
        logger.warning("Ad system: No target group configured.")
        return

    if not force and not cfg.get('is_ad_active'):
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
    try:
        scheduler.remove_all_jobs()
        active = config.get('is_ad_active')
        interval = config.get('ad_interval_minutes', 0)
        
        if active and interval > 0:
            scheduler.add_job(send_ad, 'interval', minutes=interval, id='ad_job')
            logger.info(f"✅ Ad job rescheduled: every {interval} minutes.")
        else:
            logger.info("Ad job is currently DISABLED or interval is 0.")
    except Exception as e:
        logger.error(f"Error in reschedule_ads: {e}")

def start_ads():
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("Background ADS Scheduler started.")
        reschedule_ads()
    except Exception as e:
        logger.error(f"Failed to start ADS Scheduler: {e}")
