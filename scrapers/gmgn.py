import requests
import browser_cookie3
import json

def fetch_wallet_stats(wallet_address: str, period: str = "7d") -> dict:
    url = f"https://gmgn.ai/api/v1/wallet_stat/sol/{wallet_address}/{period}"
    
    params = {
        "device_id": "8847efa1-b816-4997-a22c-b88f17e9c532",
        "client_id": "gmgn_web_20250516-1125-5ada892",
        "from_app": "gmgn",
        "app_ver": "20250516-1125-5ada892",
        "tz_name": "Asia/Calcutta",
        "tz_offset": 19800,
        "app_lang": "en-US",
        "fp_did": "3a81c4ac5b072160c4da0400dabab6da",
        "os": "web",
        "period": period
    }

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "referer": f"https://gmgn.ai/sol/address/{wallet_address}",
        "accept": "application/json, text/plain, */*"
    }

    try:
        # Load cookies from your Chrome or Vivaldi session
        cookies = browser_cookie3.chrome(domain_name="gmgn.ai")  # or .vivaldi if needed

        res = requests.get(url, headers=headers, params=params, cookies=cookies)
        res.raise_for_status()
        data = res.json()

        if data.get("code") != 0:
            print("⚠️ API returned error code.")
            return {}

        return data.get("data", {})
    
    except Exception as e:
        print(f"❌ Error fetching gmgn data: {e}")
        return {}

if __name__ == "__main__":
    wallet = "HFqp6ErWHY6Uzhj8rFyjYuDya2mXUpYEk8VW75K9PSiY"
    stats = fetch_wallet_stats(wallet)
    print(json.dumps(stats, indent=2))
