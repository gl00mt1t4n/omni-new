import sqlite3
import os
import sys
import time
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from raw_data import get_wallets_sorted_by_token_count
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.bullx import fetch_pnl_stats
from concurrent.futures import ThreadPoolExecutor, as_completed



DB_PATH = os.path.join(os.path.dirname(__file__), "woi.db")

def connect_woi_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor

def initialize_woi_db():
    conn, cursor = connect_woi_db()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS good_wallets (
            wallet TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def insert_wallet(wallet_address: str):
    conn, cursor = connect_woi_db()
    try:
        cursor.execute("INSERT INTO good_wallets (wallet) VALUES (?)", (wallet_address,))
        conn.commit()
        print(f"Inserted {wallet_address} into woi.db")
    except sqlite3.IntegrityError:

        pass
    finally:
        conn.close()

def get_all_wallets():
    conn, cursor = connect_woi_db()
    cursor.execute("SELECT wallet FROM good_wallets")
    rows = cursor.fetchall()
    conn.close()
    return [row["wallet"] for row in rows]

def populate_woi_from_raw(top_percent=10):
    initialize_woi_db()

    top_wallets = [wallet for wallet, _ in get_wallets_sorted_by_token_count(top_percent=top_percent)]
    existing = set(get_all_wallets())
    new_wallets = [w for w in top_wallets if w not in existing]

    for wallet in new_wallets:
        insert_wallet(wallet)

    print(f"{len(new_wallets)} new wallets added to woi.db")

    remove_inactive_wallets_serial()

def remove_inactive_wallets_serial():
    print("Modifying:", DB_PATH)
    wallets = get_all_wallets()
    conn, cursor = connect_woi_db()
    skipped = 0
    removed = 0

    for i, wallet in enumerate(wallets, 1):
        try:
            stats = fetch_pnl_stats(wallet)
            time.sleep(0.2)

            if not stats:
                print(f"⏭️ Skipped: {wallet}")
                skipped += 1
                continue

            wins = stats.get("wins", 0)
            realized = stats.get("realizedPnlUsd", 0)

            if wins == 0 and realized == 0:
                cursor.execute("DELETE FROM good_wallets WHERE wallet = ?", (wallet,))
                print(f"🗑️ Removed inactive wallet: {wallet}")
                removed += 1

        except Exception as e:
            print(f"⏭️ Skipped: {wallet} — due to error: {e}")
            skipped += 1

        if i % 100 == 0:
            print(f"🔄 Processed {i}/{len(wallets)} wallets...")

    conn.commit()
    conn.close()
    print(f"✅ Pruning done — Removed: {removed}, Skipped: {skipped}")

if __name__ == "__main__":
    # initialize_woi_db()
    # print("woi.db has been initialized.")
    populate_woi_from_raw()
