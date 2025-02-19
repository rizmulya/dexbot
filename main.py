from dexscreener.main import watch_dexscreener
from binance.main import watch_binance
import time

if __name__ == "__main__":
    i = 1
    while True:
        try:
            # watch_binance()
            watch_dexscreener()
        except Exception as e:
            print(f"Main Loop Error: {e}")
        
        print(i)
        i += 1
        time.sleep(60)