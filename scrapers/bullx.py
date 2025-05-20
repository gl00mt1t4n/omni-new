import cloudscraper
import json
import requests
import time
import httpx
from typing import Dict, List, Optional, Union
import os
from dotenv import load_dotenv

load_dotenv()

BULLX_HEADERS = json.loads(os.getenv("BULLX_HEADERS_JSON", "{}"))
BULLX_COOKIES = json.loads(os.getenv("BULLX_COOKIES_JSON", "{}"))
HEADERS = BULLX_HEADERS
COOKIES = BULLX_COOKIES

async def fetch_pnl_stats(wallet: str) -> Optional[Dict]:
    """
    Fetch pnlStats for one wallet. Returns the stats dict on success, or None on any error.
    """
    url = "https://api-neo.bullx.io/v2/api/getPortfolioV3"
    payload = {
        "name": "getPortfolioV3",
        "data": {
            "walletAddresses": [wallet],
            "chainIds": [1399811149, 728126428],
            "fetchMostProfitablePositions": True,
            "mostProfitablePositionsFilters": {
                "chainIds": [1399811149, 728126428],
                "walletAddresses": [wallet],
            },
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.post(url, headers=HEADERS, cookies=COOKIES, json=payload)
            resp.raise_for_status()
            return resp.json().get("pnlStats", {})
        except Exception:
            return None



if __name__ == "__main__":
    import asyncio
    import json

    test_wallet = "H1UsuH1T32cKbdWpnkuYg5DCFfSgxDj4WMLD9jAZPJuB"

    async def main():
        stats = await fetch_pnl_stats(test_wallet)
        print(json.dumps(stats, indent=2))

    asyncio.run(main())
