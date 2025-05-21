import sqlite3
import json
from datetime import datetime
import logging
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "raw_data.db")

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
        return None


def fetch_wallet_tokens(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        tokens = wallet["tokens_seen"]
        return tokens
    else:
        return None


def fetch_wallet_score(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        score = wallet["score"]
        return score
    else:
        return


def fetch_wallet_notes(address):
    wallet = fetch_wallet_all_info(address)
    if wallet:
        notes = wallet["notes"]
        return notes
    else:
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


def get_all_seen_token_addresses():
    conn, cursor = connect_db()
    cursor.execute("SELECT token_addresses_seen FROM wallets")
    rows = cursor.fetchall()
    conn.close()
    seen = set()
    for row in rows:
        addresses = json.loads(row["token_addresses_seen"] or "[]")
        seen.update(addresses)
    return seen


def insert_wallet(
    address, token_addresses=[], token_symbols=[], *, score=0.0, notes=""
):

    conn, cursor = connect_db()
    cursor.execute(
        """
        INSERT INTO wallets (wallet_address, token_addresses_seen,          
                   token_symbols_seen, score, notes)
        VALUES (?, ?, ?, ?, ?)
    """,
        (address, json.dumps(token_addresses), json.dumps(token_symbols), score, notes),
    )
    conn.commit()
    conn.close()


def add_or_update_wallet(address, token_mint, token_symbol=None, notes=""):
    conn, cursor = connect_db()
    cursor.execute(
        "SELECT token_addresses_seen, token_symbols_seen FROM wallets WHERE wallet_address = ?",
        (address,),
    )
    row = cursor.fetchone()

    if row:
        addresses = json.loads(row["token_addresses_seen"] or "[]")
        symbols = json.loads(row["token_symbols_seen"] or "[]")

        if token_mint not in addresses:
            addresses.append(token_mint)
            symbols.append(token_symbol or "UNKNOWN")
            cursor.execute(
                """
                UPDATE wallets
                SET token_addresses_seen = ?, token_symbols_seen = ?, notes = ?
                WHERE wallet_address = ?
            """,
                (json.dumps(addresses), json.dumps(symbols), notes, address),
            )
            print(
                f"Updated wallet: {address} | added token: {token_symbol or token_mint}"
            )
    else:
        insert_wallet(
            address, [token_mint], [token_symbol or "UNKNOWN"], score=0.0, notes=notes
        )
        print(f"Inserted wallet: {address} | token: {token_symbol or token_mint}")

    conn.commit()
    conn.close()


def update_wallet_score(address, new_score):
    conn, cursor = connect_db()
    cursor.execute(
        """
        UPDATE wallets
        SET score = ?
        WHERE wallet_address = ?
    """,
        (new_score, address),
    )
    conn.commit()
    conn.close()


def update_wallet_notes(address, notes):
    conn, cursor = connect_db()
    cursor.execute(
        """
        UPDATE wallets
        SET notes = ?
        WHERE wallet_address = ?
    """,
        (notes, address),
    )
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

    result = []
    for row in rows:
        result.append(
            {
                "wallet_address": row["wallet_address"],
                "token_addresses_seen": json.loads(row["token_addresses_seen"] or "[]"),
                "token_symbols_seen": json.loads(row["token_symbols_seen"] or "[]"),
                "score": row["score"],
                "notes": row["notes"],
            }
        )
    return result


def get_wallets_sorted_by_token_count(top_percent=10):
    conn, cursor = connect_db()
    cursor.execute("SELECT wallet_address, token_addresses_seen FROM wallets")
    rows = cursor.fetchall()
    conn.close()

    wallet_token_counts = [
        (row["wallet_address"], len(json.loads(row["token_addresses_seen"] or "[]")))
        for row in rows
    ]

    sorted_wallets = sorted(wallet_token_counts, key=lambda x: x[1], reverse=True)

    top_n = max(1, int(len(sorted_wallets) * (top_percent / 100)))
    return sorted_wallets[:top_n]


if __name__ == "__main__":
    print(fetch_wallet_tokens("wallet addy"))
    # placeholder as db is not populated yet.
