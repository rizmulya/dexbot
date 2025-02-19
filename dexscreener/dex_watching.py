import requests
from datetime import datetime
from utils.db import session
from dexscreener.models import Token, TokenDetail, Alert
from sqlalchemy.exc import IntegrityError
import pandas as pd
from utils.telegram import send_telegram_message
from utils.format import fnum

API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
DEX_API_URL = "https://api.dexscreener.com/latest/dex/tokens/"

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
        return {
            "token_address": token.get("tokenAddress", ""),
            "chain_id": token.get("chainId", ""),
            "url": token.get("url", ""),
            "icon": token.get("icon", ""),
            "description": token.get("description", "-"),
            "created_at": datetime.now(),
        }
    except Exception as e:
        print(f"Parse Token Error: {e}")
        return None

def parse_token_details(token):
    """Parsing data token untuk kompatibilitas database"""
    try:
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
            "created_at": datetime.now(),
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
            token_record = Token(**parsed_token)
            session.add(token_record)
            session.commit()
            new_tokens.append(parsed_token)
        except IntegrityError:
            session.rollback()
            continue
        except Exception as e:
            session.rollback()
            print(f"Save Token Error: {e}")
        finally:
            session.close()

def save_token_details(data):
    """Menyimpan data harga dan volume token ke database."""
    try:
        token_detail_record = TokenDetail(**data)
        session.add(token_detail_record)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Save Token Details Error: {e}")
    finally:
        session.close()

def should_send_alert(token, alert_type):
    """Cek apakah perlu mengirim notifikasi berdasarkan perubahan signifikan dan cooldown."""
    alert_record = session.query(Alert).filter_by(token_address=token["token_address"]).first()

    if not alert_record:
        # Jika belum ada di database, kirim notifikasi pertama kali
        alert_record = Alert(
            token_address=token["token_address"],
            last_priceUsd=token["priceUsd"],
            last_priceChange24h=token["priceChange24h"],
            last_volume24h=token["volume24h"],
            last_alert_type=alert_type,
            last_alert_time=datetime.now(),
            dex_id=token["dex_id"]
        )
        session.add(alert_record)
        session.commit()
        session.close()
        return True

    # Hitung waktu sejak notifikasi terakhir
    time_since_last_alert = datetime.now() - alert_record.last_alert_time
    cooldown_period = 3600  # Cooldown 1 jam (3600 detik)

    if time_since_last_alert.total_seconds() < cooldown_period:
        return False  # Masih dalam cooldown, tidak kirim notifikasi

    # Hitung perubahan
    price_change_diff = abs(token["priceChange24h"] - alert_record.last_priceChange24h)
    volume_change_ratio = token["volume24h"] / max(alert_record.last_volume24h, 1)

    # Jika terjadi perubahan signifikan, update database dan kirim notifikasi
    if alert_type == "pump" and price_change_diff > 50:  # Harga berubah lebih dari 50%
        update_alert(token, alert_type)
        return True
    elif alert_type == "rug_pull" and price_change_diff > 50:  # Harga berubah lebih dari 50%
        update_alert(token, alert_type)
        return True
    elif alert_type == "volume_spike" and volume_change_ratio > 2:  # Volume naik lebih dari 2x
        update_alert(token, alert_type)
        return True

    return False  # Tidak ada perubahan signifikan, tidak perlu kirim notifikasi

def update_alert(token, alert_type):
    """Update status alert di database"""
    alert_record = session.query(Alert).filter_by(token_address=token["token_address"]).first()
    if alert_record:
        alert_record.last_priceUsd = token["priceUsd"]
        alert_record.last_priceChange24h = token["priceChange24h"]
        alert_record.last_volume24h = token["volume24h"]
        alert_record.last_alert_type = alert_type
        alert_record.last_alert_time = datetime.now()
        alert_record.dex_id = token["dex_id"]
        session.commit()
        session.close()

def analyze_market():
    """Menganalisis tren pasar seperti Pump, Rug Pull, dan Volume Spike."""
    try:
        df = pd.read_sql_query("SELECT * FROM dex_token_details ORDER BY created_at DESC LIMIT 200", session.bind)

        # Deteksi PUMP (kenaikan harga >100% dalam 24 jam, volume tinggi)
        pump_tokens = df[(df["priceChange24h"] > 100) & (df["volume24h"] > 100000)]
        
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