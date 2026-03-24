import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

def check_status():
    url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
    response = requests.get(url).json()
    if response.get('ok'):
        print(f"Webhook Info: {response['result']}")
    else:
        print("Failed to get webhook info.")

if __name__ == "__main__":
    check_status()
