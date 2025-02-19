import time
from utils.db import session
from dexscreener.dex_watching import (
    fetch_token_data, fetch_token_details, save_tokens, 
    save_token_details, analyze_market, parse_token_details
)
from dexscreener.models import Token


def watch_dexscreener():
    """Kode utama untuk mengambil dan menyimpan data token setiap 60 detik,
    menganalisis market mana token yang pump, rug pull dan mendeteksi kenaikan volume yang signifikan"""

    token_data = fetch_token_data()
    if token_data:
        save_tokens(token_data)

    token_list = session.query(Token.token_address).all()
    for token in token_list:
        print(f"Fetching token {token[0]}...")
        token_details = fetch_token_details(token[0])
        if token_details and token_details.get("pairs") is not None:
            for pair in token_details["pairs"]:
                parsed_data = parse_token_details(pair)
                if parsed_data:
                    save_token_details(parsed_data)

    analyze_market()