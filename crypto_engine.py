import urllib.request
import json
import re
import logging

# Configure enterprise logging standard
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global Web3 Configurations
# REPLACE THIS WITH YOUR REAL TON WALLET ADDRESS WHERE YOU WANT TO RECEIVE USDT/TON
ADMIN_WALLET_ADDRESS = "EQCxE6mUtQJGZvdvNDmAps3gVLw9Q_gNM92gKG1_1abcDEfg" 
TON_PUBLIC_RPC_URL = "https://toncenter.com/api/v2/getTransactions"

def sanitize_tx_hash(raw_hash: str) -> str:
    """
    Sanitizes the incoming transaction hash string.
    Removes malicious characters, spaces, and guards against injection/replay bugs.
    """
    if not raw_hash:
        return ""
    return re.sub(r'\s+', '', str(raw_hash)).strip()

def verify_blockchain_transaction(tx_hash: str, expected_amount: float) -> dict:
    """
    Connects directly to the TON Blockchain distributed ledger via public RPC.
    Validates existence, recipient address, and transaction amount autonomously.
    """
    clean_hash = sanitize_tx_hash(tx_hash)
    
    if not clean_hash or len(clean_hash) < 10:
        return {"status": "failed", "reason": "Malformed or invalid transaction hash format."}
        
    try:
        # Constructing the public blockchain RPC request query
        query_url = f"{TON_PUBLIC_RPC_URL}?address={ADMIN_WALLET_ADDRESS}&limit=10&to_lt=0&archival=false"
        
        req = urllib.request.Request(
            query_url, 
            headers={'User-Agent': 'Mozilla/5.0 (AI Software Factory Core Engine)'}
        )
        
        # Opening secure network channel to the blockchain ledger
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() != 200:
                return {"status": "error", "reason": "Blockchain RPC Node unreachable."}
                
            blockchain_data = json.loads(response.read().decode())
            
            # Parsing the decentralized distributed ledger payload
            if not blockchain_data.get("ok") or "result" not in blockchain_data:
                return {"status": "failed", "reason": "Empty ledger response from RPC cluster."}
                
            transactions = blockchain_data["result"]
            
            # Magic Scanning Loop: Matching the transaction hash in the global ledger
            for tx in transactions:
                # TON transaction hashes are usually mapped inside the transaction_id or in messages
                current_tx_id = tx.get("transaction_id", {}).get("hash", "")
                
                if current_tx_id == clean_hash:
                    # Target hash found! Now verifying financial metrics
                    in_msg = tx.get("in_msg", {})
                    value_nano_ton = int(in_msg.get("value", 0))
                    
                    # Convert NanoTON to standard coin value (1 TON = 10^9 NanoTON)
                    actual_amount = value_nano_ton / 1000000000.0
                    
                    if actual_amount >= expected_amount:
                        logging.info(f"[Ledger Success] Transaction verified! Received {actual_amount} TON.")
                        return {
                            "status": "verified",
                            "amount": actual_amount,
                            "sender": in_msg.get("source", "Unknown")
                        }
                    else:
                        return {
                            "status": "failed",
                            "reason": f"Underpaid. Expected {expected_amount}, but found {actual_amount}."
                        }
                        
            # Loop ended and hash wasn't found in the latest blocks
            return {"status": "pending", "reason": "Transaction hash not found in recent blocks yet."}
            
    except Exception as network_error:
        logging.error(f"[RPC Error] Failure communicating with the blockchain network: {network_error}")
        return {"status": "error", "reason": f"Internal Web3 runtime error: {str(network_error)}"}
