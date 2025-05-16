import sqlite3
import json
from datetime import datetime
import logging

""" logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
) """


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
        # logging.warning("Wallet not found")
        return None

def fetch_wallet_tokens(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        tokens = wallet["tokens_seen"]
        return tokens
    else:
        # logging.warning("Wallet not found")
        return None

def fetch_wallet_last_active(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        last_active = wallet["last_active"]
        return last_active
    else:
        logging.warning("Wallet not found")("Row does not exist, wallet not found")
        return

def fetch_wallet_score(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        score = wallet["score"]
        return score
    else:
        logging.warning("Wallet not found")("Row does not exist, wallet not found")
        return
        
def fetch_wallet_notes(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        notes = wallet["notes"]
        return notes
    else:
        logging.warning("Wallet not found")("Row does not exist, wallet not found")
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

# Wont be used directly, just to make it more modular
def insert_wallet(address, tokens_seen=[], score=0.0, notes=""):
    now = datetime.utcnow().isoformat()
    conn, cursor = connect_db()
    cursor.execute("""
        INSERT INTO wallets (wallet_address, tokens_seen, score, notes)
        VALUES (?, ?, ?, ?)
    """, (address, json.dumps(tokens_seen), score, notes))
    conn.commit()
    conn.close()

def add_or_update_wallet(address, token, notes=""):
    tokens = fetch_wallet_tokens(address)
    now = datetime.utcnow().isoformat()

    if tokens:
        token_list = json.loads(tokens)
        if token not in token_list:
            token_list.append(token)
            conn, cursor = connect_db()
            cursor.execute("""
                UPDATE wallets
                SET tokens_seen = ?, notes = ?
                WHERE wallet_address = ?
            """, (json.dumps(token_list), notes, address))
            logging.info(f"Updated wallet: {address} | token added: {token}")
            conn.commit()
            conn.close()
    else:
        insert_wallet(address, [token], notes=notes)
        print(f"Inserted new wallet: {address} | token: {token}")

def update_wallet_score(address, new_score):
    now = datetime.utcnow().isoformat()
    conn, cursor = connect_db()
    cursor.execute("""
        UPDATE wallets
        SET score = ?
        WHERE wallet_address = ?
    """, (new_score, address))
    conn.commit()
    conn.close()

def update_wallet_notes(address, notes):
    now = datetime.utcnow().isoformat()
    conn, cursor = connect_db()
    cursor.execute("""
        UPDATE wallets
        SET notes = ?
        WHERE wallet_address = ?
    """, (notes, now, address))
    conn.commit()
    conn.close()

def get_all_wallets_with_token(token):
    conn, cursor = connect_db()
    cursor.execute("SELECT wallet_address, tokens_seen FROM wallets")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        tokens = json.loads(row["tokens_seen"])
        if token in tokens:
            result.append(row["wallet_address"])
    return result

def export_all_wallets():
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM wallets")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    print(fetch_wallet_tokens("your_wallet_address_here"))
    # placeholder as db is not populated yet.


