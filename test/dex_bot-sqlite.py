import requests
import sqlite3
import time
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import fnum, send_telegram_message

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
    url TEXT,
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

def fetch_token_data():
    """Mengambil daftar token terbaru dari API Dexscreener."""
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
        print("Error: Tidak dapat mengambil data token")
    except Exception as e:
        print(f"Fetch Token Error: {e}")
    return None

def fetch_token_details(token_address):
    """Mengambil data detail token dari API Dexscreener."""
    try:
        response = requests.get(DEX_API_URL + token_address)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Fetch Token Details Error ({token_address}): {e}")
    return None

def parse_tokens(token):
    """Parsing data token untuk kompatibilitas database"""
    try:
        timenow = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
        return {
            "token_address": token.get("tokenAddress", ""),
            "chain_id": token.get("chainId", ""),
            "url": token.get("url", ""),
            "icon": token.get("icon", ""),
            "description": token.get("description", "-"),
            "created_at": timenow,
        }
    except Exception as e:
        print(f"Parse Token Error: {e}")
        return None

def parse_token_details(token):
    """Parsing data token untuk kompatibilitas database"""
    try:
        timenow = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
        return {
            "chain_id": token.get("chainId", ""),
            "dex_id": token.get("dexId", ""),
            "url": token.get("url", ""),
            "pair_address": token.get("pairAddress", ""),
            "token_address": token.get("baseToken", {}).get("address", "-"),
            "name": token.get("baseToken", {}).get("name", "-"),
            "symbol": token.get("baseToken", {}).get("symbol", "-"),

            "priceUsd": float(token.get("priceUsd", 0)),
            "liquidityUsd": float(token.get("liquidity", {}).get("usd", 0)),
            "volume24h": float(token.get("volume", {}).get("h24", 0)),
            "priceChange24h": float(token.get("priceChange", {}).get("h24", 0)),
            "market_cap": float(token.get("marketCap", 0)),

            "created_at": timenow,
        }
    except Exception as e:
        print(f"Parse Token Error: {e}")
        return None

def save_tokens(data):
    """Menyimpan token baru ke database dan mengirim notifikasi jika ada token baru."""
    new_tokens = []
    for token in data:
        parsed_token = parse_tokens(token)
        if not parsed_token:
            continue
        
        try:
            cursor.execute('''INSERT INTO tokens (token_address, chain_id, url, icon, description, created_at)
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (parsed_token["token_address"], parsed_token["chain_id"], parsed_token["url"],
                            parsed_token["icon"], parsed_token["description"], parsed_token["created_at"]))
            db_conn.commit()
            new_tokens.append(parsed_token)
        except sqlite3.IntegrityError:
            continue  # Jika token sudah ada, lewati
        except Exception as e:
            print(f"Save Token Error: {e}")

    # if new_tokens:
    #     message = "*🚀 Token Baru Terdeteksi:*\n"
    #     for token in new_tokens:
    #         message += f"\n- [{token['token_address']}]({token['url']})\n"
    #     send_telegram_message(message)

def save_token_details(data):
    """Menyimpan data harga dan volume token ke database."""
    try:
        cursor.execute('''INSERT INTO token_details (chain_id, dex_id, url, token_address, pair_address, name, symbol, priceUsd, liquidityUsd, volume24h, priceChange24h, market_cap, created_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (data["chain_id"], data["dex_id"], data["url"], data["token_address"], data["pair_address"],
                        data["name"], data["symbol"], data["priceUsd"], data["liquidityUsd"],
                        data["volume24h"], data["priceChange24h"], data["market_cap"], data["created_at"]))
        db_conn.commit()
    except Exception as e:
        print(f"Save Token Details Error: {e}")

"""
ALERTS
"""
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
    cursor.execute('''UPDATE alerts SET last_priceUsd = ?, last_priceChange24h = ?, last_volume24h = ?, last_alert_type = ?, last_alert_time = ?, dex_id = ?
                      WHERE token_address = ?''',
                   (token["priceUsd"], token["priceChange24h"], token["volume24h"], alert_type, datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(), token["dex_id"], token["token_address"]))
    db_conn.commit()
"""
END ALERTS
"""

def analyze_market():
    """Menganalisis tren pasar seperti Pump, Rug Pull, dan Volume Spike."""
    try:
        df = pd.read_sql_query("SELECT * FROM token_details ORDER BY created_at DESC LIMIT 200", db_conn)

        # Deteksi PUMP (kenaikan harga >50% dalam 24 jam, volume tinggi)
        pump_tokens = df[(df["priceChange24h"] > 50) & (df["volume24h"] > 100000)]
        
        # Deteksi RUG PULL (penurunan harga >90%, likuiditas sangat rendah)
        rug_pull_tokens = df[(df["priceChange24h"] < -90) & (df["liquidityUsd"] < 5000)]

        # Deteksi VOLUME SPIKE (kenaikan volume > 500% dalam 24 jam)
        df["prev_volume"] = df["volume24h"].shift(1)
        volume_spike_tokens = df[(df["prev_volume"] > 0) & (df["volume24h"] > df["prev_volume"] * 5)]

        # Kirim notifikasi jika ada kejadian signifikan 
        for _, row in pump_tokens.iterrows():
            token = row.to_dict()
            if should_send_alert(token, "pump"):
                message = f"""
🚀 *Pump Detected!*

🔹 *Name:* [{token['name']} ({token['symbol']})]({token['url']})  
🔹 *Market Cap:* ${fnum(token['market_cap'])}  
🔹 *24H Change:* {fnum(token['priceChange24h'])}%  
🔹 *Price:* ${fnum(token['priceUsd'])}  
🔹 *DEX:* {token['dex_id']}
"""
                send_telegram_message(message, True)

        for _, row in rug_pull_tokens.iterrows():
            token = row.to_dict()
            if should_send_alert(token, "rug_pull"):
                message = f"""
*💀 Rug Pull Detected:*

🔹 *Name:* [{token['name']} ({token['symbol']})]({token['url']})  
🔹 *Market Cap:* ${fnum(token['market_cap'])}  
🔹 *24H Change:* {fnum(token['priceChange24h'])}%  
🔹 *Price:* ${fnum(token['priceUsd'])}  
🔹 *DEX:* {token['dex_id']}
"""
                send_telegram_message(message, True)

        for _, row in volume_spike_tokens.iterrows():
            token = row.to_dict()
            if should_send_alert(token, "volume_spike"):
                message = f"""
*📈 Volume Spike Detected:*

🔹 *Name:* [{token['name']} ({token['symbol']})]({token['url']})
🔹 *MCap:* ${fnum(token['market_cap'])}
🔹 *24H Vol:* {fnum(token['volume24h'])}%
🔹 *Liquidity:* ${fnum(token['liquidityUsd'])}
🔹 *Dex:* {token['dex_id']}
"""
                send_telegram_message(message, True)
    except Exception as e:
        print(f"Analyze Market Error: {e}")

def main():
    """Loop utama untuk mengambil dan menyimpan data token setiap 60 detik."""
    i = 1
    while True:
        try:
            token_data = fetch_token_data()
            if token_data:
                save_tokens(token_data)

            cursor.execute("SELECT token_address FROM tokens")
            token_list = [row[0] for row in cursor.fetchall()]
            
            for token in token_list:
                token_details = fetch_token_details(token)
                if token_details and "pairs" in token_details:
                    for pair in token_details["pairs"]:
                        parsed_data = parse_token_details(pair)
                        if parsed_data:
                            save_token_details(parsed_data)

            analyze_market()
        except Exception as e:
            print(f"Main Loop Error: {e}")
        
        print(i)
        i += 1
        time.sleep(60)

if __name__ == "__main__":
    main()
