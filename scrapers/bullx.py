import cloudscraper
import json
import requests
import time
import httpx
from typing import Dict, List, Optional, Union

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
HEADERS = {
        "authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjU5MWYxNWRlZTg0OTUzNjZjOTgyZTA1MTMzYmNhOGYyNDg5ZWFjNzIiLCJ0eXAiOiJKV1QifQ.eyJsb2dpblZhbGlkVGlsbCI6IjIwMjUtMDgtMTJUMTc6Mjg6MDUuOTU3WiIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9ic2ctdjIiLCJhdWQiOiJic2ctdjIiLCJhdXRoX3RpbWUiOjE3NDcyNDM2ODcsInVzZXJfaWQiOiIweGZmOTEzODY4NDQ0OTc1MDQ4Y2I1ZjI0MDRlZGQwMzc3NmFjNzA0YmIiLCJzdWIiOiIweGZmOTEzODY4NDQ0OTc1MDQ4Y2I1ZjI0MDRlZGQwMzc3NmFjNzA0YmIiLCJpYXQiOjE3NDczOTgxOTcsImV4cCI6MTc0NzQwMTc5NywiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6e30sInNpZ25faW5fcHJvdmlkZXIiOiJjdXN0b20ifX0.zgJnG0Z8ufcxaUYBcpz-stV57lSgYdiDhm1j0kqDdUEA5EYC-suAOTttPvuKaTfkYBx47uSdETcgS-c2T0bWqLoEMuCYfMkQ0vQLcnUcvlFbhFv-fYzcqI5g6-RXtshvgKJfNokTv0sJ3lVVaRfofuwbH1CjiDUyqJ2JxtE8-MgoNriZduceAgcdulWM069kyEqbVuPl4N7RPSTlu28re2nf1B5D8vkxBZe8kOGU6oH_bm2dN_0gFJuX8gnYmnLUQqxHUKmiNzZeqXesxHj3B42uCFbDtPrHi9KzMvBhaTw0orYzA5UIafLsnI_4gToEREjMRZWQ_2GMUk0db3nr0w",
        "x-cs-token": "Ji3XVbcEqURPut-CsB02o.a1a29087984f57992a9192ca81af88a13e7c685a1f89064bc06062eed359cc32",
        "origin": "https://neo.bullx.io",
        "referer": "https://neo.bullx.io/",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "accept": "application/json, text/plain, */*"
    }

COOKIES = {
        "bullx-session-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIweGZmOTEzODY4NDQ0OTc1MDQ4Y2I1ZjI0MDRlZGQwMzc3NmFjNzA0YmIiLCJzZXNzaW9uSWQiOiJKaTNYVmJjRXFVUlB1dC1Dc0IwMm8iLCJzdWJzY3JpcHRpb25QbGFuIjoiQkFTSUMiLCJoYXNoIjoiNmUzMGM5M2VjMGM4MmYxZjk4NzI4OTZjMjcyMzUyMTQyNzc3YjIyMTMzZDkwMzllZmEwZTllNzIwY2YxYzk5NiIsImlhdCI6MTc0NzI0MzY4NiwiZXhwIjoxNzU1MDE5Njg2fQ.NRW-qk8s9TLTjGYGeFigEq_54wgxnCnQHd_ibxZxWT4",
        "bullx-visitor-id": "0xff913868444975048cb5f2404edd03776ac704bb.631b0b4d39ffd6c22e67cda1f29897d1ef1ea07f5dce57339f1ce5c22d965d9f",
        "bullx-cs-token": "Ji3XVbcEqURPut-CsB02o.a1a29087984f57992a9192ca81af88a13e7c685a1f89064bc06062eed359cc32",
        "bullx-nonce-id": "3f2WFOBn87HBbQzgshVUA8WL9J01KB-DoL6rvP24VjlmYbxNYlCXRoFkoT6vz2KG"
    }


if __name__ == "__main__":
    import asyncio
    import json

    test_wallet = "H1UsuH1T32cKbdWpnkuYg5DCFfSgxDj4WMLD9jAZPJuB"

    async def main():
        stats = await fetch_pnl_stats(test_wallet)
        print(json.dumps(stats, indent=2))

    asyncio.run(main())
