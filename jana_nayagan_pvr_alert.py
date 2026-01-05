from seleniumbase import Driver
import time
from datetime import datetime
import requests
import os
import re

# ========= CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8362460080:AAH_UOmqzTUsuFD-aLq4bGTLOFpGA7Mf10M")
CHAT_ID = os.getenv("CHAT_ID", "6560835378") 

TARGET_DATE = "20260109" # Jan 9, 2026
CHECK_INTERVAL = 180     # 3 minutes

# Exact URL for Bengaluru + Jana Nayagan + Date
# Updated based on user input
# Exact URL for Bengaluru + Jana Nayagan + Date
# Updated based on user input
URL = f"https://in.bookmyshow.com/movies/bengaluru/jana-nayagan/buytickets/ET00430817/{TARGET_DATE}"

PLATFORMS = {
    "BookMyShow": URL
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.json().get("ok"):
            print("🚀 ALERT SENT TO YOUR TELEGRAM!")
        else:
            print(f"❌ Telegram Error: {r.json().get('description')}")
    except:
        print("❌ Network error connecting to Telegram.")

def monitor_cinemas():
    # UC=True is mandatory for BMS/District in 2026
    driver = Driver(uc=True, headless=True)
    try:
        all_found = []
        for name, url in PLATFORMS.items():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking {name}...")
            driver.get(url)
            time.sleep(10) # Give time for JS to render
            
            # Robust Text Scanning (Fixes CSS selector issues)
            try:
                body_text = driver.find_element("tag name", "body").text
            except:
                print(f"⚠️ Could not read body text for {name}")
                continue

            lines = body_text.splitlines()
            current_venue = None
            
            # Regex for 6 AM - 7:59 AM patterns
            # Matches 6:30 AM, 06:45 AM, 7:00 AM, etc.
            time_pattern = re.compile(r'\b(0?6|0?7|0?8):\d{2}\s?AM') 

            for line in lines:
                line = line.strip().upper()
                if not line: continue
                
                # 1. Identify Venue
                if "PVR" in line or "INOX" in line:
                    current_venue = line
                
                # 2. Identify Morning Shows (6 AM - 8 AM)
                elif current_venue and "AM" in line:
                    # Check if it matches our specific morning hours
                    if time_pattern.search(line):
                         all_found.append(f"<b>{name}</b>: {current_venue} at {line}")

        return list(set(all_found)) # Remove duplicates
    except Exception as e:
        print(f"⚠️ Scrape Error: {e}")
        return []
    finally:
        driver.quit()

# ========= MAIN LOOP =========
print(f"🔥 Watching PVR/INOX ONLY for Jan 9th (6AM-8AM)...")

while True:
    matches = monitor_cinemas()
    if matches:
        msg = (
            f"<b>🚨 JANA NAYAGAN PVR/INOX FAN SHOWS!</b>\n\n"
            + "\n".join(matches) + 
            f"\n\n<a href='{URL}'>BOOK NOW</a>"
        )
        send_telegram(msg)
        # break # Uncomment this if you only want ONE phone call/alert
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No PVR/INOX morning shows on {TARGET_DATE} yet.")
    
    time.sleep(CHECK_INTERVAL)