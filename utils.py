import requests
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message, disable_web_page_preview = False):
    """Mengirim pesan ke Telegram jika ada token baru atau perubahan signifikan."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": disable_web_page_preview}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")


def fnum(number):
    """
    Mengubah angka menjadi format yang lebih manusiawi dengan suffix k, M, B, dll.
    
    Contoh:
    - 1000 → 1k
    - 1_500_000 → 1.5M
    - 2_000_000_000 → 2B
    """
    if not isinstance(number, (int, float)):
        return number 
    
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"  # Miliar
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"  # Juta
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"  # Ribu
    else:
        return str(number)