import time
import asyncio
import cloudscraper
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Initialize scraper
scraper = cloudscraper.create_scraper()

# Load headers from .env
GMGN_HEADERS = json.loads(os.getenv("GMGN_HEADERS_JSON", "{}"))
HEADERS = GMGN_HEADERS

def get_base_params():
    return {
        "device_id": "8847efa1-b816-4997-a22c-b88f17e9c532",
        "client_id": "gmgn_web_20250517-1212-af09a36",
        "from_app": "gmgn",
        "app_ver": "20250517-1212-af09a36",
        "tz_name": "Asia/Calcutta",
        "tz_offset": "19800",
        "app_lang": "en-US",
        "fp_did": "3a81c4ac5b072160c4da0400dabab6da",
        "os": "web",
        "period": "7d",
        "_": str(time.time()),  #IMPORTANT: cache busting
    }

def _sync_fetch(endpoint_path: str, wallet: str) -> dict:
    """Synchronous call to GMGN API via cloudscraper."""
    url = f"https://gmgn.ai" + endpoint_path.format(wallet=wallet)
    params = get_base_params()

    try:
        response = scraper.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json().get("data", {})
    except Exception as e:
        print(f"Error fetching {wallet}: {e}")
        return {}


async def fetch_gmgn_data(endpoint_path: str, wallet: str) -> dict:
    """Async-compatible wrapper using to_thread for sync cloudscraper."""
    return await asyncio.to_thread(_sync_fetch, endpoint_path, wallet)


async def get_gmgn_risk(wallet: str) -> dict:
    """Fetches 'risk' flags (phishing behavior) from GMGN API."""
    data = await fetch_gmgn_data("/api/v1/wallet_stat/sol/{wallet}/7d", wallet)
    risk = data.get("risk", {})
    return {
        "didnt_buy_ratio": float(risk.get("no_buy_hold_ratio", 0.0)),
        "buy_sell_under_5s_ratio": float(risk.get("fast_tx_ratio", 0.0)),
        "sold_gt_bought_ratio": float(risk.get("sell_pass_buy_ratio", 0.0)),
    }


async def is_wallet_safe(wallet: str) -> bool:
    """
    Returns true if it passes phishing checks.
    didnt_buy_ratio < 10%
    buy_sell_under_5s_ratio	< 40%
    sold_gt_bought_ratio	< 10%
    """

    risk = await get_gmgn_risk(wallet)
    if not risk:
        print(f"No risk data found for {wallet}")
        return False
    
    if (
        risk["didnt_buy_ratio"] < 0.35 and
        risk["buy_sell_under_5s_ratio"] < 0.40 and
        risk["sold_gt_bought_ratio"] < 0.10
    ):
        return True

    print(f"Wallet {wallet} failed phishing filter:", risk)
    return False

# 🔹 Test one wallet
if __name__ == "__main__":
    async def main():
        wallet = "9VxJw5ngvTfv3SkBZnfn2bMk8H29QXMgA6MfGtuHkZhx"
        risk = await get_gmgn_risk(wallet)
        print("RISK:", risk)
        is_safe = await is_wallet_safe(wallet)
        print(f"Is wallet safe? {is_safe}")


    asyncio.run(main())
