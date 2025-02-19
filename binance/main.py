import requests
from utils.telegram import send_telegram_message
from utils.db import session
from binance.models import BncAlert

def watch_binance():
    """send notif if 24h priceChangePercent > 30%"""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    
    try:
        print("Fetching binance api...")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            for ticker in data:
                symbol = ticker["symbol"]
                price_change_percent = float(ticker["priceChangePercent"])

                # Cek jika perubahan harga lebih dari 30%
                if price_change_percent > 30: 
                    message = (
                        f"🚀 *ALERT: Lonjakan Harga {symbol}* 🚀\n"
                        f"📈 Perubahan Harga: {price_change_percent:.2f}%\n"
                        f"💰 Harga Terakhir: {ticker['lastPrice']}\n"
                        f"📊 Harga Tertinggi: {ticker['highPrice']}\n"
                        f"📉 Harga Terendah: {ticker['lowPrice']}\n"
                        f"🔄 Volume: {ticker['volume']}"
                    )
                    send_telegram_message(message)

                # Send setup alert
                setup_symbol = session.query(BncAlert).filter_by(symbol=symbol).first()
                if setup_symbol:
                        last_price = float(ticker['lastPrice'])

                        if last_price >= setup_symbol.higher:
                            message = (
                                f"🚀 *ALERT: {symbol} menyentuh higher {setup_symbol.higher}* 🚀\n"
                                f"📈 Harga Saat Ini: {last_price}\n"
                            )
                            send_telegram_message(message)
                        elif last_price <= setup_symbol.lower:
                            message = (
                                f"🚀 *ALERT: {symbol} menyentuh lower {setup_symbol.lower}* 🚀\n"
                                f"📈 Harga Saat Ini: {last_price}\n"
                            )
                            send_telegram_message(message)

        else:
            print(f"Error Fetching Data: {response.status_code}")
    
    except Exception as e:
        print(f"Request Error: {e}")
