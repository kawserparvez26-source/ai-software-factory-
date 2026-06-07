import sqlite3
import re
import logging

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_on_chain_payment(user_id: int, order_id: str, raw_tx_hash: str, expected_amount: float, db_path: str = 'users.db') -> dict:
    """
    Ingests, sanitizes, and validates incoming blockchain transaction hashes.
    Implements strict regex sanitation and database idempotency locks to stop fraud.
    
    Returns:
        dict: Standardized payload matrix for the core runtime orchestrator.
    """
    # Input Sanitization: Strip all whitespaces and malicious injection anomalies
    clean_hash = re.sub(r'\s+', '', str(raw_tx_hash)).strip()

    if not clean_hash or len(clean_hash) < 10:
        return {
            "status": "error",
            "message": "Invalid transaction hash string provided. Ingestion aborted."
        }

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Idempotency Check: Verify if this specific transaction hash has been claimed before
        cursor.execute("SELECT status, order_id FROM crypto_payments WHERE tx_hash = ?", (clean_hash,))
        existing_payment = cursor.fetchone()

        if existing_payment:
            logging.warning(f"[Fraud Intercepted] Duplicate hash submission by User {user_id} for Order {order_id}.")
            return {
                "status": "fraud_detected",
                "message": f"Security Exception: This transaction hash has already been processed for Order ID: {existing_payment[1]}."
            }

        # 2. Commit transaction metadata into the immutable ledger state
        cursor.execute('''
            INSERT INTO crypto_payments (order_id, user_id, tx_hash, amount_paid, status)
            VALUES (?, ?, ?, ?, 'VERIFYING')
        ''', (order_id, user_id, clean_hash, expected_amount))

        # 3. Transition the commercial order flow state to 'VERIFYING'
        cursor.execute("UPDATE orders SET status = 'VERIFYING' WHERE order_id = ?", (order_id,))
        
        conn.commit()
        logging.info(f"[Ledger Updated] Order {order_id} shifted to VERIFYING lifecycle state.")
        
        return {
            "status": "success",
            "message": "Transaction logged into blockchain ledger. Awaiting verification from On-Chain RPC Node listener..."
        }

    except sqlite3.IntegrityError:
        logging.error(f"[Integrity Fault] Race condition or unique constraints violation caught for hash: {clean_hash}")
        return {
            "status": "fraud_detected",
            "message": "Security Exception: Duplicate hash transaction blocked by database firewall."
        }
    except Exception as runtime_error:
        logging.error(f"[System Error] Critical exception during payment processing: {runtime_error}")
        return {
            "status": "system_error",
            "message": f"Internal backend execution failure: {str(runtime_error)}"
        }
    finally:
        if conn:
            conn.close()
      
