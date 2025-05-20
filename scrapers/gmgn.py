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

def get_base_params(**extra) -> dict:
    p = {
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
    p.update(extra)
    return p

async def fetch_gmgn_data(endpoint_path: str, wallet: str, params_override: dict | None = None) -> dict:
    return await asyncio.to_thread(_sync_fetch, endpoint_path, wallet, params_override)


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

async def get_wallet_holdings( # this is for in order of total profit, descending
    wallet: str,
    limit: int = 50,
    orderby: str = "total_profit",
    direction: str = "desc"
) -> list[dict]:
    """
    Returns the 'holdings' array already sorted by GMGN backend.

    Showsmall=True, sellout=True, tx30d=True replicate the UI query.
    """
    params = get_base_params(
        limit=str(limit),
        orderby=orderby,
        direction=direction,
        showsmall="true",
        sellout="true",
        tx30d="true"
    )
    data = await fetch_gmgn_data(
        "/api/v1/wallet_holdings/sol/{wallet}", wallet, params_override=params
    )
    return data.get("holdings", [])

# ─── KEEP **ONE** GOOD VERSION ONLY ────────────────────────────────────────────
def _sync_fetch(endpoint_path: str,
                wallet: str,
                params_override: dict | None = None) -> dict:
    """
    Low-level synchronous call to GMGN API via cloudscraper.
    """
    url    = f"https://gmgn.ai" + endpoint_path.format(wallet=wallet)
    params = params_override or get_base_params()

    try:
        resp = scraper.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        return resp.json().get("data", {})
    except Exception as e:
        print(f"❌ Error fetching {wallet}: {e}")
        return {}
# ───────────────────────────────────────────────────────────────────────────────


async def get_gmgn_big_wins(
    wallet: str,
    min_profit_usd: float = 1_000,
    min_roi: float = 1.0,
    top_n: int = 3
) -> dict:
    """
    Uses server-sorted /wallet_holdings so we only inspect the first `limit`.
    """
    holdings = await get_wallet_holdings(wallet, limit=50)

    winners = [
        {
            "symbol": h["token"]["symbol"],
            "profit_usd": float(h["total_profit"]),
            "roi": float(h["total_profit_pnl"])
        }
        for h in holdings
        if float(h.get("total_profit", 0)) >= min_profit_usd
        and float(h.get("total_profit_pnl", 0)) >= min_roi
    ]

    return {
        "has_big_wins": len(winners) >= top_n,
        "winners": winners[:top_n]
    }

# 🔹 Test one wallet
if __name__ == "__main__":
    async def main():
        wallet = "9VxJw5ngvTfv3SkBZnfn2bMk8H29QXMgA6MfGtuHkZhx"
        risk = await get_gmgn_risk(wallet)
        print("RISK:", risk)
        is_safe = await is_wallet_safe(wallet)
        print(f"Is wallet safe? {is_safe}")

    async def demo():
        wallet = "3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE"
        res = await get_gmgn_big_wins(wallet)
        print(res)
    asyncio.run(demo())


    asyncio.run(main())
