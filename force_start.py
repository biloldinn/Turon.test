import time
import subprocess
import sys

def run_bot():
    while True:
        print("Starting bot (app.py)...")
        # Run app.py and wait for it to finish (it will likely crash with 409)
        process = subprocess.Popen([sys.executable, "app.py"])
        process.wait()
        
        print("Bot stopped/crashed. Retrying in 2 seconds...")
        time.sleep(2)

if __name__ == "__main__":
    run_bot()
