import time
import asyncio
import cloudscraper
from dotenv import load_dotenv
import os
import json
import threading
import random

load_dotenv()
scraper = cloudscraper.create_scraper()
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
        "_": str(time.time()),  # IMPORTANT: cache busting
    }
    p.update(extra)
    return p


async def fetch_gmgn_data(
    endpoint_path: str, wallet: str, params_override: dict | None = None
) -> dict:
    return await asyncio.to_thread(_sync_fetch, endpoint_path, wallet, params_override)


async def get_gmgn_risk(wallet: str) -> dict:
    """
    Return phishing-risk ratios.
    If API gives no data → return empty dict so caller treats wallet as unsafe.
    """
    data = await fetch_gmgn_data("/api/v1/wallet_stat/sol/{wallet}/7d", wallet)

    if not data:  # network failure or non-json
        return {}
    risk = data.get("risk") or {}  # protect against None
    return {
        "didnt_buy_ratio": float(risk.get("no_buy_hold_ratio", 0.0)),
        "buy_sell_under_5s_ratio": float(risk.get("fast_tx_ratio", 0.0)),
        "sold_gt_bought_ratio": float(risk.get("sell_pass_buy_ratio", 0.0)),
    }


async def is_wallet_safe(wallet: str) -> bool:
    """
    Returns true if it passes phishing checks.
    didnt_buy_ratio < 60%
    buy_sell_under_5s_ratio	< 40%
    sold_gt_bought_ratio	< 10%
    """

    risk = await get_gmgn_risk(wallet)
    if not risk:
        print(f"[INFO] No risk data returned for wallet: {wallet}")
        return False

    if (
        risk["didnt_buy_ratio"] < 0.6
        and risk["buy_sell_under_5s_ratio"] < 0.40
        and risk["sold_gt_bought_ratio"] < 0.10
    ):
        return True

    print(
        f"[WARN] Wallet {wallet} did not pass phishing risk checks. Risk metrics: {risk}"
    )
    return False


async def get_wallet_holdings(
    # default is for in order of total profit, descending
    wallet: str,
    limit: int = 50,
    orderby: str = "total_profit",
    direction: str = "desc",
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
        tx30d="true",
    )
    data = await fetch_gmgn_data(
        "/api/v1/wallet_holdings/sol/{wallet}", wallet, params_override=params
    )
    return data.get("holdings", [])


# ─── Adaptive global rate-limiter ────────────────────────────────────────────
TARGET_QPS = 4.0  # start goal: 4 requests / second  (0.25 s delay)
MIN_DELAY = 0.10  # never below 100 ms
MAX_DELAY = 1.00  # never above 1 s   (can still rise via back-off)
ADJUST_FACTOR = 1.15  # how aggressively to slow/speed
SUCCESS_WINDOW = 50  # successes needed before speeding back up

_lock = threading.Lock()
_next_time = 0.0
_delay = 1.0 / TARGET_QPS
_success = 0  # rolling counter

REQUEST_DELAY = 0.2
_lock = threading.Lock()
_next_allowed = 0.0


def _wait_slot():
    global _next_allowed
    with _lock:
        now = time.time()
        if now < _next_allowed:
            time.sleep(_next_allowed - now)
        _next_allowed = time.time() + REQUEST_DELAY


# ──────────────────────────────────────────────────────────────────────────────


def _sync_fetch(
    endpoint_path: str, wallet: str, params_override: dict | None = None
) -> dict:
    """
    Guaranteed-return version: will loop forever until GMGN
    replies with data (code == 0).  NO wallet is ever skipped.
    """
    url = "https://gmgn.ai" + endpoint_path.format(wallet=wallet)
    params = params_override or get_base_params()
    attempt = 0

    while True:
        attempt += 1
        _wait_slot()

        try:
            resp = scraper.get(url, headers=HEADERS, params=params)
            if resp.status_code == 429:
                # hard rate-limit: sleep a bit longer and retry
                sleep_for = 3 + random.uniform(0, 2)  # 3-5 s
                print(
                    f"[WARN] Received HTTP 429 for wallet {wallet} (attempt {attempt}). Retrying in {sleep_for:.1f} seconds."
                )
                time.sleep(sleep_for)
                continue

            resp.raise_for_status()

            payload = resp.json()
            if payload.get("code", 0) != 0:
                # gmgn sometimes returns code!=0 when wallet not cached yet
                sleep_for = 2 + random.uniform(0, 1)
                print(
                    f"[INFO] GMGN API returned non-zero code for wallet {wallet}. Retrying in {sleep_for:.1f} seconds. Response code: {payload.get('code')}"
                )

                time.sleep(sleep_for)
                continue

            return payload.get("data", {})

        except (json.JSONDecodeError, ValueError):
            print(
                f"[ERROR] Failed to parse JSON response for wallet {wallet}. Retrying in 2 seconds."
            )
        except Exception as e:
            print(
                f"[ERROR] Exception encountered while fetching data for wallet {wallet}: {e}. Retrying in 5 seconds."
            )


async def get_gmgn_big_wins(
    wallet: str, min_profit_usd: float = 5_000, min_roi: float = 0.69, top_n: int = 3
) -> dict:
    """
    Uses server-sorted /wallet_holdings so we only inspect the first `limit`.
    """
    holdings = await get_wallet_holdings(wallet, limit=50)

    winners = [
        {
            "symbol": h["token"]["symbol"],
            "profit_usd": float(h["total_profit"]),
            "roi": float(h["total_profit_pnl"]),
        }
        for h in holdings
        if float(h.get("total_profit", 0)) >= min_profit_usd
        and float(h.get("total_profit_pnl", 0)) >= min_roi
    ]

    return {"has_big_wins": len(winners) >= top_n, "winners": winners[:top_n]}


# 🔹 Test one wallet
if __name__ == "__main__":

    async def main():
        wallet = "9VxJw5ngvTfv3SkBZnfn2bMk8H29QXMgA6MfGtuHkZhx"
        risk = await get_gmgn_risk(wallet)
        print("RISK:", risk)
        is_safe = await is_wallet_safe(wallet)
        print(f"[RESULT] Wallet {wallet} safety check passed: {is_safe}")

    async def demo():
        wallet = "3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE"
        res = await get_gmgn_big_wins(wallet)
        print(f"[RESULT] High-performing tokens for wallet {wallet}: {res}")

    asyncio.run(demo())

    asyncio.run(main())
