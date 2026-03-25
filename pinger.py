import time
import requests
import threading
from logger import logger
from config import WEBHOOK_URL

def ping_self():
    """Continuously pings the bot's own health endpoint to keep it awake on Render/Railway."""
    if not WEBHOOK_URL:
        logger.info("Pinger: WEBHOOK_URL not set. Skipping self-ping.")
        return

    # Extract the base URL (remove the /TOKEN part if present)
    base_url = WEBHOOK_URL.split('/8')[0].rstrip('/') # Rough split by token prefix if concatenated
    health_url = f"{WEBHOOK_URL.rstrip('/')}/health"
    
    logger.info(f"Pinger: Starting background pinger for {health_url}")
    
    while True:
        try:
            # Wait 10 minutes (Render sleeps after 15)
            time.sleep(600) 
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"Pinger: Self-ping successful! Status: {response.status_code}")
            else:
                logger.warning(f"Pinger: Self-ping returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Pinger: Self-ping failed: {e}")

def start_pinger():
    """Starts the pinger in a daemon thread."""
    if WEBHOOK_URL:
        pinger_thread = threading.Thread(target=ping_self, daemon=True)
        pinger_thread.start()
        logger.info("Pinger: Background thread initialized.")
    else:
        logger.warning("Pinger: Cannot start pinger without WEBHOOK_URL.")
