import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.defined_fi import get_trending_token_info
from scrapers.helius_utils import get_token_accounts_rpc
from data.raw_data import add_or_update_wallet, get_all_seen_token_addresses
from data.raw_data import add_or_update_wallet
from scrapers.bullx import fetch_pnl_stats  


def process_token(contract: dict): 
    mint = contract.get("address")
    symbol = contract.get("symbol", "UNKNOWN")

    if not mint:
        print(f"Skipping token {contract}: {symbol} with no address")
        return
    
    print(f"\n Processing {symbol} ({mint})")

    holders = get_token_accounts_rpc(mint)
    print(f"Found {len(holders)} holders for token {symbol}")

    for holder in holders:
        wallet = holder.get("owner")
        if wallet:
            add_or_update_wallet(wallet, mint, token_symbol=symbol)

def process_trending_tokens():
    trending_contracts = get_trending_token_info()
    seen_tokens = get_all_seen_token_addresses()
    print(f"Skipping already seen tokens: {len(seen_tokens)} total\n")

    for contract in trending_contracts:
        mint = contract.get("address")
        if mint in seen_tokens:
            print(f"⏭   Skipping {contract.get('symbol', 'UNKNOWN')} ({mint}) — already processed")
            continue

        process_token(contract)

if __name__ == "__main__":
    # Example: Any test token with address + symbol
    """ test_token = {
        "address": "A8YHuvQBMAxXoZAZE72FyC8B7jKHo8RJyByXRRffpump",
        "symbol": "XBT"
    }
    process_token([test_token])
    """
    process_trending_tokens()