import sqlite3
import json
from datetime import datetime

DB_PATH = "omni.db"

# Returns sqlite3 connection and cursor object (basic initialization)
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor

# row[0] is address, row[1] = tokens_seen, row[2] = last_seen, row[3] = score, row[4] = notes
# Row factory has been set which means I can access by row name, above is just for reference
def fetch_wallet_all_info(address):
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM wallets WHERE wallet_address = ?", (address,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row
    else:
        print("No wallet found")
        return

def fetch_wallet_tokens(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        tokens = wallet["tokens_seen"]
        return tokens
    else:
        print("Row does not exist, wallet not found")
        return

def fetch_wallet_last_active(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        last_active = wallet["last_active"]
        return last_active
    else:
        print("Row does not exist, wallet not found")
        return

def fetch_wallet_score(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        score = wallet["score"]
        return score
    else:
        print("Row does not exist, wallet not found")
        return
        
def fetch_wallet_notes(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        notes = wallet["notes"]
        return notes
    else:
        print("Row does not exist, wallet not found")
        return

def list_all_wallets():
    conn, cursor = connect_db()
    cursor.execute("SELECT wallet_address FROM wallets")
    rows = cursor.fetchall()
    conn.close()
    return [row["wallet_address"] for row in rows]

def delete_wallet(address):
    conn, cursor = connect_db()
    cursor.execute("DELETE FROM wallets WHERE wallet_address = ?", (address,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print(fetch_wallet_tokens("your_wallet_address_here"))


