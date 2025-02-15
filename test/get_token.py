import requests
import json

# API URLs
API_URL_1 = "https://api.dexscreener.com/token-profiles/latest/v1"
API_URL_2 = "https://api.dexscreener.com/latest/dex/tokens/Dw6docEkKZn9kDVAzkppcE1jWe9tK9LAtCsmSqdEYvbU"

# Fetch data from API 1
response_1 = requests.get(API_URL_1)
if response_1.status_code == 200:
    data_1 = response_1.json()
    with open("api_response_1.json", "w", encoding="utf-8") as f:
        json.dump(data_1, f, indent=4)
    print("Data from API 1 saved successfully.")
else:
    print("Failed to fetch data from API 1:", response_1.status_code)

# Fetch data from API 2
response_2 = requests.get(API_URL_2)
if response_2.status_code == 200:
    data_2 = response_2.json()
    with open("api_response_2.json", "w", encoding="utf-8") as f:
        json.dump(data_2, f, indent=4)
    print("Data from API 2 saved successfully.")
else:
    print("Failed to fetch data from API 2:", response_2.status_code)
