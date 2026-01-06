from seleniumbase import Driver
import time
from datetime import datetime
import requests
import os
import re
import sys 
from twilio.rest import Client

# 1. Try Loading from Environment Variables (Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") 
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
MY_PHONE = os.getenv("MY_PHONE")

# 2. Try Loading from Local Config (Local Dev) -> Overwrites Env if present
try:
    import local_config
    BOT_TOKEN = local_config.BOT_TOKEN
    CHAT_ID = local_config.CHAT_ID
    TWILIO_SID = local_config.TWILIO_SID
    TWILIO_AUTH_TOKEN = local_config.TWILIO_AUTH_TOKEN
    TWILIO_FROM = local_config.TWILIO_FROM
    MY_PHONE = local_config.MY_PHONE
    print("✅ Loaded credentials from local_config.py")
except ImportError:
    pass # No local config, relying on Env Vars 

# 3. Sanitize Inputs (Remove accidental newlines/spaces)
if TWILIO_SID: TWILIO_SID = TWILIO_SID.strip()
if TWILIO_AUTH_TOKEN: TWILIO_AUTH_TOKEN = TWILIO_AUTH_TOKEN.strip()
if TWILIO_FROM: TWILIO_FROM = TWILIO_FROM.strip()
if MY_PHONE: MY_PHONE = MY_PHONE.strip()

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

def trigger_all_alerts(theaters_list):
    """Triggers Telegram Message AND Twilio Call"""
    print(f"🚨 TICKETS FOUND! Triggering all alerts for: {theaters_list}")
    
    # 1. TELEGRAM TEXT
    try:
        msg = (
            f"<b>🚨 JANA NAYAGAN LIVE!</b>\n\n"
            + "\n".join(theaters_list) + 
            f"\n\n<a href='{URL}'>BOOK NOW</a>"
        )
        url_tg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url_tg, data=payload, timeout=10)
        print("🚀 ALERT SENT TO YOUR TELEGRAM!")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

    # 2. TWILIO PHONE CALL
    if TWILIO_SID and TWILIO_AUTH_TOKEN and MY_PHONE:
        try:
            client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
            theater_text = " ".join([t.split(":")[0] for t in theaters_list]) # Just theater names for voice
            
            call = client.calls.create(
                twiml=f'<Response><Say voice="alice" loop="5">Attention! Jana Nayagan tickets are live at {theater_text}. Book now!</Say></Response>',
                to=MY_PHONE,
                from_=TWILIO_FROM
            )
            print(f"☎️  Twilio Call Initiated! SID: {call.sid}")
        except Exception as e:
            print(f"❌ Twilio Error: {e}")
    else:
        print("ℹ️ Twilio credentials missing. Skipping phone call.")

def monitor_cinemas():
    # UC=True is mandatory for BMS/District in 2026
    driver = None
    try:
        driver = Driver(uc=True, headless=True)
        
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
        if driver:
            try:
                driver.quit()
            except:
                pass

# ========= MAIN LOOP =========
print(f"🔥 Watching PVR/INOX ONLY for Jan 9th (6AM-8AM)...")

while True:
    try:
        matches = monitor_cinemas()
        if matches:
            trigger_all_alerts(matches)
            print("✅ Success! Alerts triggered. Exiting to prevent spam loop.")
            sys.exit() # Critical for phone calls - don't want to call 100 times in a row
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No PVR/INOX morning shows on {TARGET_DATE} yet.")
    except Exception as e:
        print(f"⚠️ Critical Error in Main Loop: {e}")
        print("🔄 Retrying in a few minutes...")
    
    time.sleep(CHECK_INTERVAL)