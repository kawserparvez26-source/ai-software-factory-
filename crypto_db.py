import sqlite3
import logging

def create_crypto_ledger_tables(db_path: str = 'users.db'):
    """
    Initializes the secure SQL tables to prevent fraud and duplicate token claims.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Secure Ledger to guard against Replay Attacks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tx_hash TEXT UNIQUE NOT NULL, -- Strict cryptographic firewall against duplication
                amount REAL NOT NULL,
                status TEXT DEFAULT 'VERIFIED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logging.info("[Database] Crypto ledger tables verified and synchronized.")
    except Exception as db_error:
        logging.error(f"[Database Error] Table creation failed: {db_error}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_crypto_ledger_tables()
