"""
woi_data.py
===========

Maintains the `woi.db` database of “wallets of interest” (WoI):

1.  Builds the WoI list from the top-token wallets in `raw_data.db`.
2.  Queries Bullx (`scrapers.bullx.fetch_pnl_stats`) to obtain P&L metrics.
3.  Removes wallets whose activity falls below a configurable threshold.

The script is network-bound; five worker threads process the wallets in
parallel, sleeping 0.1 s between calls to respect remote rate limits.
Progress is printed every wallet.
"""

from __future__ import annotations

import datetime
import os
import sqlite3
import sys
import threading
import time
from queue import Queue

# ────────────────────────────────────────────────────────────────────
# Project imports
# ────────────────────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from raw_data import delete_wallet, get_wallets_sorted_by_token_count

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.bullx import fetch_pnl_stats

# ────────────────────────────────────────────────────────────────────
# SQLite helpers
# ────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "woi.db")


def connect_woi_db() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()


def initialize_woi_db() -> None:
    conn, cur = connect_woi_db()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS good_wallets (wallet TEXT PRIMARY KEY)"
    )
    conn.commit()
    conn.close()


def insert_wallet(wallet_addr: str) -> None:
    conn, cur = connect_woi_db()
    try:
        cur.execute("INSERT INTO good_wallets (wallet) VALUES (?)", (wallet_addr,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_all_wallets() -> list[str]:
    conn, cur = connect_woi_db()
    cur.execute("SELECT wallet FROM good_wallets")
    rows = cur.fetchall()
    conn.close()
    return [row["wallet"] for row in rows]


# ────────────────────────────────────────────────────────────────────
# Worker parameters
# ────────────────────────────────────────────────────────────────────
NUM_WORKERS = 5
DELAY_BETWEEN_CALLS = 0.1  # seconds
PROGRESS_EVERY = 1         # print progress every wallet
MIN_THRESHOLD = 1_000      # USD threshold for all four metrics

wallet_queue: Queue[str] = Queue()
lock = threading.Lock()

processed = 0          # updated by workers under lock
total_wallets = 0      # set once in main
start_time = 0.0       # perf_counter timestamp


# ────────────────────────────────────────────────────────────────────
# Helper functions
# ────────────────────────────────────────────────────────────────────
def pretty_elapsed() -> str:
    seconds = int(time.perf_counter() - start_time)
    return str(datetime.timedelta(seconds=seconds))


def is_wallet_bad(stats: dict) -> bool:
    """
    Return True when *any* activity metrics are below MIN_THRESHOLD.

    Parameters
    ----------
    stats  The dict returned by Bullx (`pnlStats`).

    Notes
    -----
    For pnl numbers we apply abs(); realised losses count the same
    as realised gains for threshold purposes.
    """
    if not stats:
        return False  # unknown activity → keep

    realized     = abs(stats.get("realizedPnlUsd",    0.0))
    unrealized   = abs(stats.get("unrealizedPnlUsd",  0.0))
    total_rev    = stats.get("totalRevenueUsd",       0.0)
    total_spent  = stats.get("totalSpentUsd",         0.0)

    return (
        realized     < MIN_THRESHOLD or
        unrealized   < MIN_THRESHOLD or
        total_rev    < MIN_THRESHOLD or
        total_spent  < MIN_THRESHOLD
    )


# ────────────────────────────────────────────────────────────────────
# Worker thread
# ────────────────────────────────────────────────────────────────────
def worker() -> None:
    """
    Process wallets one by one, single‐shot fetch.  
    On failure, log and move on; on success, prune if below threshold.
    """
    global processed

    while True:
        wallet = wallet_queue.get()
        if wallet is None:
            break

        try:
            stats = fetch_pnl_stats(wallet)
        except Exception as exc:
            print(f"Failed to fetch stats for {wallet}: {exc}. Moving on.")
            # Progress update below still applies
        else:
            if stats:
                if is_wallet_bad(stats):
                    with lock:
                        delete_wallet(wallet)
                        print(f"Removed wallet: {wallet}")
                else:
                    print(f"Kept wallet:    {wallet}")
            else:
                print(f"No stats for {wallet}: keeping by default")

        # Progress counter & display
        with lock:
            processed += 1
            if processed % PROGRESS_EVERY == 0 or processed == total_wallets:
                print(
                    f"[ {processed:>5} / {total_wallets} ]  "
                    f"{pretty_elapsed():>8}  |  wallet {wallet}"
                )

        time.sleep(DELAY_BETWEEN_CALLS)
        wallet_queue.task_done()



# ────────────────────────────────────────────────────────────────────
# Core routines
# ────────────────────────────────────────────────────────────────────
def remove_inactive_wallets_threaded() -> None:
    global total_wallets, start_time

    wallets = get_all_wallets()
    total_wallets = len(wallets)
    print(f"Scanning {total_wallets} wallets with {NUM_WORKERS} workers…")

    start_time = time.perf_counter()

    for w in wallets:
        wallet_queue.put(w)

    threads = [threading.Thread(target=worker) for _ in range(NUM_WORKERS)]
    for t in threads:
        t.start()

    wallet_queue.join()

    for _ in threads:
        wallet_queue.put(None)
    for t in threads:
        t.join()

    print(f"Completed in {pretty_elapsed()}")


def populate_woi_from_raw(top_percent: int = 10) -> None:
    """
    1. Take the top‐token wallets from raw_data.db.
    2. Merge into woi.db (deduplicating).
    3. Prune inactive wallets.
    """
    initialize_woi_db()

    top_wallets = [
        w for w, _ in get_wallets_sorted_by_token_count(top_percent=top_percent)
    ]
    existing = set(get_all_wallets())
    new_wallets = [w for w in top_wallets if w not in existing]

    for wallet in new_wallets:
        insert_wallet(wallet)

    print(f"{len(new_wallets)} new wallets added to woi.db")
    remove_inactive_wallets_threaded()


# ────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    populate_woi_from_raw()
