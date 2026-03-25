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

    health_url = f"{WEBHOOK_URL.rstrip('/')}/health"
    logger.info(f"Pinger: Starting background pinger for {health_url}")
    
    # Wait a few seconds for the server to actually start
    time.sleep(10)
    
    while True:
        try:
            response = requests.get(health_url, timeout=10)
            logger.info(f"Pinger: Self-ping status: {response.status_code}")
            # Wait 5 minutes
            time.sleep(300) 
        except Exception as e:
            logger.error(f"Pinger: Self-ping failed: {e}")
            time.sleep(60) # Wait a minute before retry if failed

def start_pinger():
    """Starts the pinger in a daemon thread."""
    if WEBHOOK_URL:
        pinger_thread = threading.Thread(target=ping_self, daemon=True)
        pinger_thread.start()
        logger.info("Pinger: Background thread initialized.")
