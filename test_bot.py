import sys
import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.environ.get("BOT_TOKEN")
if token:
    res = requests.get(f"https://api.telegram.org/bot{token}/getMe")
    print(res.json())
else:
    print("NO TOKEN")
