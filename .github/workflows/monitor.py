import os
import hashlib
import requests
from bs4 import BeautifulSoup


# --- CONFIGURATION ---
TARGET_URL = "http://woodslandingenergy.com/"
HASH_FILE = "site_hash.txt"


# Provide either or both Webhook URLs (leave empty string "" if not using)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
# TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
# TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"


def get_page_hash(url):
    """Fetches the web page, cleans non-content elements, and calculates SHA-256 hash."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return None


    # Parse HTML and strip non-visible elements (scripts, styles, tracking metadata)
    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "meta", "noscript", "header", "footer"]):
        element.decompose()


    # Extract clean text visible to the user
    clean_text = soup.get_text(separator=" ", strip=True)


    # Hash the extracted text content
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()


def send_alert(message):
    """Sends notification to Discord and/or Telegram."""
    # Discord Alert
    if DISCORD_WEBHOOK_URL and DISCORD_WEBHOOK_URL != "YOUR_DISCORD_WEBHOOK_URL_HERE":
        payload = {"content": f"🔔 **Website Change Detected!**\n{message}\n{TARGET_URL}"}
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            print("Discord notification sent.")
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")


    # Telegram Alert
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID and TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🔔 Website Change Detected!\n{message}\n{TARGET_URL}"
        }
        try:
            requests.post(tg_url, json=payload, timeout=10)
            print("Telegram notification sent.")
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")


def check_site():
    current_hash = get_page_hash(TARGET_URL)
    if not current_hash:
        return


    # Check if we have a recorded baseline hash
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()
        
        if current_hash != previous_hash:
            print("Change detected on the site!")
            send_alert("The Woods Landing Energy project website content has been updated.")
            
            # Save the new hash as the current baseline
            with open(HASH_FILE, "w") as f:
                f.write(current_hash)
        else:
            print("No changes detected.")
    else:
        # First-time run: Store the baseline hash
        print("First run detected. Saving baseline snapshot.")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)


if __name__ == "__main__":
    check_site()
