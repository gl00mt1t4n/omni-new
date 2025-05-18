"""
woi_data.py - Definitions for WoI DB interaction and async PnL filtering.
"""

import asyncio
import datetime
import os
import sqlite3
import sys
import time
from typing import List, Dict, Optional

# ────────────────────────────────────────────────────────────────────
# Project imports
# ────────────────────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from raw_data import get_wallets_sorted_by_token_count
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.bullx import fetch_pnl_stats
# ────────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "woi.db")

# Async parameters (tweak as desired)
CONCURRENCY = 5
DELAY_BETWEEN_CALLS = 0.05  # seconds
MIN_THRESHOLD = 1_000       # USD threshold


# ────────────────────────────────────────────────────────────────────
# SQLite helpers
# ────────────────────────────────────────────────────────────────────
def connect_woi_db() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def initialize_woi_db() -> None:
    conn, cur = connect_woi_db()
    cur.execute("CREATE TABLE IF NOT EXISTS good_wallets (wallet TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def insert_wallet(wallet: str) -> None:
    conn, cur = connect_woi_db()
    try:
        cur.execute("INSERT INTO good_wallets (wallet) VALUES (?)", (wallet,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_all_wallets() -> List[str]:
    conn, cur = connect_woi_db()
    cur.execute("SELECT wallet FROM good_wallets")
    rows = cur.fetchall()
    conn.close()
    return [r["wallet"] for r in rows]


# ────────────────────────────────────────────────────────────────────
# Business logic
# ────────────────────────────────────────────────────────────────────
def is_wallet_active(stats: Dict) -> bool:
    """
    Return True iff:
      • realizedPnlUsd > 0
      • AND abs(realizedPnlUsd), abs(unrealizedPnlUsd),
        totalRevenueUsd, totalSpentUsd are all >= MIN_THRESHOLD.
    """
    if not stats:
        return False

    realized    = stats.get("realizedPnlUsd",    0.0)
    unrealized  = stats.get("unrealizedPnlUsd",  0.0)
    total_rev   = stats.get("totalRevenueUsd",   0.0)
    total_spent = stats.get("totalSpentUsd",     0.0)

    if realized <= 0:
        return False

    if (abs(realized)   < MIN_THRESHOLD or
        abs(unrealized) < MIN_THRESHOLD or
        total_rev       < MIN_THRESHOLD or
        total_spent     < MIN_THRESHOLD):
        return False

    return True


def pretty_elapsed(start: float) -> str:
    sec = int(time.perf_counter() - start)
    return str(datetime.timedelta(seconds=sec))


# ────────────────────────────────────────────────────────────────────
# Async validator + inserter with progress
# ────────────────────────────────────────────────────────────────────
async def _validate_and_insert(
    wallet: str,
    sem: asyncio.Semaphore,
    state: Dict[str, int],
    start: float
):
    async with sem:
        stats = await fetch_pnl_stats(wallet)

    state["processed"] += 1
    idx   = state["processed"]
    total = state["total"]
    elapsed = pretty_elapsed(start)

    if stats is None:
        print(f"[{idx:>5}/{total}] {elapsed} | Skipped (no data): {wallet}")
    elif is_wallet_active(stats):
        insert_wallet(wallet)
        print(f"[{idx:>5}/{total}] {elapsed} | Inserted wallet:     {wallet}")
    else:
        print(f"[{idx:>5}/{total}] {elapsed} | Skipped (inactive):  {wallet}")

    await asyncio.sleep(DELAY_BETWEEN_CALLS)


# ────────────────────────────────────────────────────────────────────
# Public async pipeline entrypoint
# ────────────────────────────────────────────────────────────────────
async def populate_filtered_woi(top_percent: int = 10) -> None:
    """
    1. Initializes woi.db.
    2. Fetches top_percent wallets from raw_data.
    3. Validates each via fetch_pnl_stats + is_wallet_active.
    4. Inserts only active wallets, skipping the rest.
    """
    initialize_woi_db()

    # Determine new candidates
    top_wallets = [w for w, _ in get_wallets_sorted_by_token_count(top_percent)]
    existing    = set(get_all_wallets())
    to_process  = [w for w in top_wallets if w not in existing]

    total = len(to_process)
    print(f"Validating {total} new wallets with concurrency={CONCURRENCY}")

    state = {"processed": 0, "total": total}
    sem   = asyncio.Semaphore(CONCURRENCY)
    start = time.perf_counter()

    # Launch validation tasks
    tasks = [
        _validate_and_insert(w, sem, state, start)
        for w in to_process
    ]
    await asyncio.gather(*tasks)

    print(f"Done in {pretty_elapsed(start)}")
