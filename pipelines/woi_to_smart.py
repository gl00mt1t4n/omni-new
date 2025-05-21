"""
pipelines/woi_to_smart.py
─────────────────────────
• Pull wallet list from woi.db          (table: wallets)
• For each wallet:
      – phishing-safe?      (scrapers.gmgn.is_wallet_safe)
      – has big wins?       (scrapers.gmgn.get_gmgn_big_wins)
• Insert/update rows in smart.db (table: smart_wallets)

Run:
    python -m pipelines.woi_to_smart  [--concurrency 30]
"""

import asyncio
import sqlite3
import time
import argparse
from pathlib import Path
import sys, pathlib
import threading
from datetime import timedelta
import random

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

# ─── import gmgn helpers ──────────────────────────────────────────────────────
from scrapers.gmgn import (
    is_wallet_safe,
    get_gmgn_big_wins,
    get_gmgn_risk,
)

# ─── file paths ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
WOI_DB = ROOT / "data" / "woi.db"
SMART_DB = ROOT / "data" / "smart.db"

# ─── sqlite helpers ───────────────────────────────────────────────────────────
def init_smart_db() -> sqlite3.Connection:
    conn = sqlite3.connect(SMART_DB)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS smart_wallets (
            wallet TEXT PRIMARY KEY,
            didnt_buy REAL,
            fast_tx  REAL,
            sold_gt  REAL,
            win1_sym TEXT, win1_usd REAL, win1_roi REAL,
            win2_sym TEXT, win2_usd REAL, win2_roi REAL,
            win3_sym TEXT, win3_usd REAL, win3_roi REAL,
            updated_at INTEGER
        )
        """
    )
    conn.commit()
    return conn


def load_all_wallets() -> list[str]:
    conn = sqlite3.connect(WOI_DB)
    cur = conn.cursor()
    try:
        cur.execute("SELECT wallet FROM good_wallets")
        rows = cur.fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


# ─── per-wallet async processing ──────────────────────────────────────────────
async def analyse_wallet(wallet: str):
    """Return dict to insert, or None if wallet is not smart."""
    if not await is_wallet_safe(wallet):
        return None

    big = await get_gmgn_big_wins(wallet)
    if not big["has_big_wins"]:
        return None

    risk = await get_gmgn_risk(wallet)

    # pad winners to 3 slots
    winners = big["winners"] + [{}] * (3 - len(big["winners"]))

    row = {
        "wallet": wallet,
        "didnt_buy": risk["didnt_buy_ratio"],
        "fast_tx": risk["buy_sell_under_5s_ratio"],
        "sold_gt": risk["sold_gt_bought_ratio"],
        "wins": winners,
        "ts": int(time.time()),
    }
    return row


def upsert_row(conn: sqlite3.Connection, row: dict):
    w = row["wins"]
    conn.execute(
        """
        INSERT INTO smart_wallets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(wallet) DO UPDATE SET
            didnt_buy=excluded.didnt_buy,
            fast_tx =excluded.fast_tx,
            sold_gt =excluded.sold_gt,
            win1_sym=excluded.win1_sym, win1_usd=excluded.win1_usd, win1_roi=excluded.win1_roi,
            win2_sym=excluded.win2_sym, win2_usd=excluded.win2_usd, win2_roi=excluded.win2_roi,
            win3_sym=excluded.win3_sym, win3_usd=excluded.win3_usd, win3_roi=excluded.win3_roi,
            updated_at=excluded.updated_at
        """,
        (
            row["wallet"],
            row["didnt_buy"],
            row["fast_tx"],
            row["sold_gt"],
            w[0].get("symbol"),
            w[0].get("profit_usd"),
            w[0].get("roi"),
            w[1].get("symbol"),
            w[1].get("profit_usd"),
            w[1].get("roi"),
            w[2].get("symbol"),
            w[2].get("profit_usd"),
            w[2].get("roi"),
            row["ts"],
        ),
    )


# ─── main pipeline ────────────────────────────────────────────────────────────
async def main(concurrency: int = 30):
    wallets = load_all_wallets()
    total = len(wallets)
    print(f"[INFO] Starting analysis for {total} wallets from woi.db")

    sem = asyncio.Semaphore(concurrency)
    conn = init_smart_db()

    start_time = time.time()  # 👆 start-timestamp holder

    async def worker(idx_wallet):
        idx, w = idx_wallet
        async with sem:
            row = await analyse_wallet(w)
            elapsed = time.time() - start_time
            hhmmss = str(timedelta(seconds=int(elapsed)))

            if row:
                upsert_row(conn, row)
                print(
                    f"[SUCCESS] [{idx+1}/{total}] Wallet {w} processed successfully | Elapsed: {hhmmss}"
                )
            else:
                print(
                    f"[SKIP] [{idx+1}/{total}] Wallet {w} did not meet criteria | Elapsed: {hhmmss}"
                )

    # enumerate so each worker knows its sequence #
    await asyncio.gather(*(worker(pair) for pair in enumerate(wallets)))

    conn.commit()
    conn.close()

    runtime = str(timedelta(seconds=int(time.time() - start_time)))
    print(f"[INFO] Pipeline completed in {runtime}. Output written to data/smart.db")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=30)
    args = parser.parse_args()
    asyncio.run(main(concurrency=args.concurrency))
