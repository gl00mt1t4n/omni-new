import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.defined_fi import get_trending_token_info
from scrapers.helius_utils import get_token_accounts_rpc
from db import add_or_update_wallet

def process_token(contracts: list[dict]):
    for contract in contracts:
        mint = contract.get("address")
        symbol = contract.get("symbol", "UNKNOWN")

        if not mint:
            print(f"Skipping token {contract}: {symbol} with no address")
            continue
    
        print(f"\n Processing {symbol} ({mint})")

        holders = get_token_accounts_rpc(mint)
        print(f"Found {len(holders)} holders for token {symbol}")

        for holder in holders:
            wallet = holder.get("owner")
            if wallet:
                add_or_update_wallet(wallet, mint)

def process_trending_tokens():
    trending_contracts = get_trending_token_info()
    for contract in trending_contracts:
        process_token(contract)

if __name__ == "__main__":
    # Example: Polycule (PCULE) on Solana
    test_token = {
        "address": "J27UYHX5oeaG1YbUGQc8BmJySXDjNWChdGB2Pi2TMDAq",
        "symbol": "PCULE"
    }

    process_token([test_token])