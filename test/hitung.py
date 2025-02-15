import requests
import sqlite3
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
from zoneinfo import ZoneInfo

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Dexscreener API Endpoint
API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
DEX_API_URL = "https://api.dexscreener.com/latest/dex/tokens/"

# Database Setup
db_conn = sqlite3.connect("dexscreener_data.db", check_same_thread=False)
cursor = db_conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT UNIQUE,
    chain_id TEXT,
    url TEXT,
    icon TEXT,
    description TEXT,
    created_at TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS token_details ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id TEXT,
    dex_id TEXT,
    token_address TEXT,
    pair_address TEXT,
    name TEXT,
    symbol TEXT,
    priceUsd REAL,
    liquidityUsd REAL,
    volume24h REAL,
    priceChange24h REAL,
    market_cap REAL,
    created_at TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (
    token_address TEXT PRIMARY KEY,
    last_priceUsd REAL,
    last_priceChange24h REAL,
    last_volume24h REAL,
    last_alert_type TEXT,
    last_alert_time TEXT,
    dex_id TEXT
)''')

cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_address ON token_details (token_address)') 
cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON token_details (created_at)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_address ON alerts (token_address)') 
db_conn.commit()

def should_send_alert(token, alert_type):
    """Cek apakah perlu mengirim notifikasi berdasarkan perubahan signifikan dan cooldown."""
    cursor.execute("SELECT last_priceUsd, last_priceChange24h, last_volume24h, last_alert_type, last_alert_time FROM alerts WHERE token_address = ?", 
                   (token["token_address"],))
    row = cursor.fetchone()

    if not row:
        # Jika belum ada di database, kirim notifikasi pertama kali
        cursor.execute('''INSERT INTO alerts (token_address, last_priceUsd, last_priceChange24h, last_volume24h, last_alert_type, last_alert_time, dex_id) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (token["token_address"], token["priceUsd"], token["priceChange24h"], token["volume24h"], alert_type, datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(), token["dex_id"]))
        db_conn.commit()
        return True

    last_price, last_change, last_volume, last_alert, last_alert_time = row

    # Hitung waktu sejak notifikasi terakhir
    last_alert_time = datetime.fromisoformat(last_alert_time)
    time_since_last_alert = datetime.now(ZoneInfo("Asia/Jakarta")) - last_alert_time
    cooldown_period = 3600  # Cooldown 1 jam (3600 detik)

    if time_since_last_alert.total_seconds() < cooldown_period:
        return False  # Masih dalam cooldown, tidak kirim notifikasi

    # Hitung perubahan
    price_change_diff = abs(token["priceChange24h"] - last_change)
    volume_change_ratio = token["volume24h"] / max(last_volume, 1)

    print(price_change_diff)

    # Jika terjadi perubahan signifikan, update database dan kirim notifikasi
    if alert_type == "pump" and price_change_diff > 20:  # Harga berubah lebih dari 20%
        update_alert(token, alert_type)
        return True
    elif alert_type == "rug_pull" and price_change_diff > 20:  # Harga berubah lebih dari 20%
        update_alert(token, alert_type)
        return True
    elif alert_type == "volume_spike" and volume_change_ratio > 2:  # Volume naik lebih dari 2x
        update_alert(token, alert_type)
        return True

    return False  # Tidak ada perubahan signifikan, tidak perlu kirim notifikasi

def update_alert(token, alert_type):
    """Update status alert di database"""
    # cursor.execute('''UPDATE alerts SET last_priceUsd = ?, last_priceChange24h = ?, last_volume24h = ?, last_alert_type = ?, last_alert_time = ?, dex_id = ?
    #                   WHERE token_address = ?''',
    #                (token["priceUsd"], token["priceChange24h"], token["volume24h"], alert_type, datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(), token["dex_id"], token["token_address"]))
    # db_conn.commit()
    print('update_alert()')

token_tes = {
    # 'id': 1,
    'chain_id': 'solana',
    'dex_id': 'raydium',
    'token_address': '2fGzUxrni6k7fFzydagpCiuoaGHw4ehTTP5aBSjEyfNj',
    'pair_address': '64VmdbBcpFNGhNg2aEpeBmuG8Bh7wu9Tcyt7f4av7Gca',
    'name': 'Kaito.AI',
    'symbol': 'Kaito',
    'priceUsd': 0.06929,
    'liquidityUsd': 740133.71,
    'volume24h': 389769.98,
    'priceChange24h': 4791470,
    'market_cap': 6929505242,
    'created_at': '2025-02-16T13:13:36.735040+07:00'
}

if should_send_alert(token_tes, 'pump'):
    print('send..')
else:
    print('no send..')