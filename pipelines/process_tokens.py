import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.defined_fi import get_trending_token_info
from scrapers.helius_utils import get_token_accounts_rpc
from data.raw_data import add_or_update_wallet, get_all_seen_token_addresses
from scrapers.bullx import fetch_pnl_stats


# Set this flag to False if we want to include tokens with >200k holders
SKIP_LARGE_HOLDER_TOKENS = True


def process_token(contract: dict):
    mint = contract.get("address")
    symbol = contract.get("symbol", "UNKNOWN")

    if not mint:
        print(f"[WARN] Skipping token without address: {symbol} — {contract}")
        return

    print(f"\n[INFO] Processing token: {symbol} ({mint})")

    holders = get_token_accounts_rpc(mint)
    holder_count = len(holders)
    print(f"[INFO] Retrieved {holder_count} holders for token {symbol}")

    if SKIP_LARGE_HOLDER_TOKENS and holder_count > 200_000:
        print(f"[SKIP] {symbol} has too many holders ({holder_count}) — skipping")
        return

    for holder in holders:
        wallet = holder.get("owner")
        if wallet:
            add_or_update_wallet(wallet, mint, token_symbol=symbol)


def process_trending_tokens():
    trending_contracts = get_trending_token_info()
    seen_tokens = get_all_seen_token_addresses()
    print(f"[INFO] Skipping previously seen tokens. Total seen: {len(seen_tokens)}\n")

    for contract in trending_contracts:
        mint = contract.get("address")
        if mint in seen_tokens:
            print(
                f"[SKIP] Token already processed: {contract.get('symbol', 'UNKNOWN')} ({mint})"
            )
            continue

        process_token(contract)


if __name__ == "__main__":
    # Toggle the below to True if you want to include large-holder tokens
    # SKIP_LARGE_HOLDER_TOKENS = False

    process_trending_tokens()
