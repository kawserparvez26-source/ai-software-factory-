# database.py
import sqlite3
import logging
import config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes and returns a connection to the SQLite database with thread-safe isolation."""
    conn = sqlite3.connect(config.DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes schema blueprints for both user profiles and system security blocks."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Master User Matrix Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Security Access Control Table (Ban Management)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                banned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
           # Smart Memory Layer: Conversational History Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
             # Performance & Failover Analytics Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_metrics (
                engine_name TEXT PRIMARY KEY,
                call_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0
            )
            """)
            
            # Populate baseline engine entries if they don't exist
            engines = ['Gemini', 'Groq', 'OpenRouter', 'TogetherAI']
            for engine in engines:
                cursor.execute("INSERT OR IGNORE INTO api_metrics (engine_name) VALUES (?)", (engine,))
                
            conn.commit()
            logger.info("📦 Database Engine initialized successfully with security nodes.")
    except Exception as e:
        logger.critical(f"Database Initialization Failure: {str(e)}")


def save_user(user) -> bool:
    """Inserts or dynamically synchronizes active Telegram profiles into the data warehouse."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO users (id, username, first_name)
            VALUES (?, ?, ?)
            """, (user.id, user.username, user.first_name))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to record profile telemetry for user {user.id}: {str(e)}")
        return False


def get_user_count() -> int:
    """Returns absolute aggregate volume of unique registered profiles."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"User analytics query failed: {str(e)}")
        return 0


def get_all_users() -> list:
    """Fetches full analytical records of user IDs for system-wide communication routing."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users")
            return [row['id'] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to extract historical user arrays: {str(e)}")
        return []


def ban_user(user_id: int) -> bool:
    """Restricts access authorization parameters for a specified user ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO banned_users (user_id) VALUES (?)", (user_id,))
            conn.commit()
            logger.warning(f"🚫 User ID {user_id} added to infrastructure isolation pool.")
            return True
    except Exception as e:
        logger.error(f"Security override failed for ban command on ID {user_id}: {str(e)}")
        return False


def unban_user(user_id: int) -> bool:
    """Restores administrative clearance parameters for a specified restricted user ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"✅ User ID {user_id} released from security restrictions.")
            return True
    except Exception as e:
        logger.error(f"Security override failed for unban command on ID {user_id}: {str(e)}")
        return False


def is_banned(user_id: int) -> bool:
    """Evaluates security authorization status dynamically for inbound operational calls."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Authorization status check failed for system reference {user_id}: {str(e)}")
        return False


def get_banned_count() -> int:
    """Returns historical metrics regarding banned connection blocks."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM banned_users")
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Banned analytics extraction failed: {str(e)}")
        return 0
def save_chat_memory(user_id: int, role: str, content: str):
    """Saves a single conversational exchange segment into the SQLite data storage framework."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO chat_memory (user_id, role, content)
            VALUES (?, ?, ?)
            """, (user_id, role, content))
            
            # Optimization: Keep only the last 20 messages per user to preserve local storage limits
            cursor.execute("""
            DELETE FROM chat_memory WHERE id NOT IN (
                SELECT id FROM chat_memory WHERE user_id = ? 
                ORDER BY timestamp DESC LIMIT 20
            ) AND user_id = ?
            """, (user_id, user_id))
            
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to commit runtime context trace for user {user_id}: {str(e)}")


def get_chat_memory(user_id: int, limit: int = 6) -> list:
    """Fetches historical dialogue logs for context payload rendering."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT role, content FROM chat_memory 
            WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT ?
            """, (user_id, limit))
            
            # Reverse order so messages flow chronologically (oldest to newest)
            rows = cursor.fetchall()
            memory_list = [{"role": row['role'], "content": row['content']} for row in rows]
            memory_list.reverse()
            return memory_list
    except Exception as e:
        logger.error(f"Failed to query local memory matrix for user {user_id}: {str(e)}")
        return []
def log_engine_metric(engine_name: str, success: bool):
    """Increments telemetry transaction flags for primary and fallback engines."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if success:
                cursor.execute("UPDATE api_metrics SET call_count = call_count + 1 WHERE engine_name = ?", (engine_name,))
            else:
                cursor.execute("UPDATE api_metrics SET fail_count = fail_count + 1 WHERE engine_name = ?", (engine_name,))
            conn.commit()
    except Exception as e:
        logger.error(f"Metrics logging transaction failed for {engine_name}: {str(e)}")


def get_engine_metrics_report() -> dict:
    """Retrieves computed structural analytics data frames for server admin review."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT engine_name, call_count, fail_count FROM api_metrics")
            rows = cursor.fetchall()
            return {row['engine_name']: {"calls": row['call_count'], "fails": row['fail_count']} for row in rows}
    except Exception as e:
        logger.error(f"Metrics fetch routine execution failed: {str(e)}")
        return {}
import sqlite3
import logging

# Configure structured logging for production auditing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_crypto_payment_system(db_path: str = 'users.db'):
    """
    Version 3.0: High-Concurrency Web3 Core Database Architecture.
    Initializes the immutable ledger tables required to process safe cryptographic transactions.
    Ensures strict schema integrity and idempotency using UNIQUE constraints.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Commercial layer table to track invoices and order lifecycles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price_usdt REAL NOT NULL,
                status TEXT DEFAULT 'PENDING', -- PENDING, VERIFYING, APPROVED, REJECTED
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Cryptographic ledger table to trap and prevent Replay Attacks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                tx_hash TEXT UNIQUE NOT NULL, -- Strict cryptographic firewall against duplication
                amount_paid REAL NOT NULL,
                crypto_currency TEXT DEFAULT 'USDT_TON',
                status TEXT DEFAULT 'VERIFYING',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        ''')

        conn.commit()
        logging.info("[Web3 Engine] Crypto Ledger Tables Initialized Successfully.")
        
    except sqlite3.Error as error:
        logging.error(f"[Database Error] Schema initialization failed: {error}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_crypto_payment_system()


 import sqlite3
from datetime import datetime

def init_mining_infrastructure():
    """
    Natively provisions the distributed Web3 AI mining ledger table
    and safe-guards it against database schema corruption.
    """
    conn = sqlite3.connect("crypto_factory.db")
    cursor = conn.cursor()
    
    # Creating an isolated sub-ledger for gamified user mining mechanics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_mining_nodes (
            user_id INTEGER PRIMARY KEY,
            mining_balance REAL DEFAULT 0.0,
            base_speed REAL DEFAULT 2.0,
            referral_speed_bonus REAL DEFAULT 0.0,
            last_checkpoint TEXT,
            referred_by INTEGER DEFAULT NULL,
            total_referrals INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def activate_or_fetch_mining_node(user_id: int, referrer_id: int = None) -> dict:
    """
    Idempotently registers a user into the H2O mining mesh.
    Awards welcome tokens and sets up the base 2x molecular speed bond.
    """
    init_mining_infrastructure()
    conn = sqlite3.connect("crypto_factory.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT mining_balance, base_speed, referral_speed_bonus, total_referrals, referred_by FROM user_mining_nodes WHERE user_id = ?", (user_id,))
    existing_node = cursor.fetchone()
    
    now_str = datetime.utcnow().isoformat()
    WELCOME_BONUS = 1000.0  # Instant Welcome Reward Tokens
    
    if not existing_node:
        # Check if a valid cross-referral link was used to initialize the bond
        valid_referrer = None
        if referrer_id and int(referrer_id) != user_id:
            cursor.execute("SELECT user_id FROM user_mining_nodes WHERE user_id = ?", (referrer_id,))
            if cursor.fetchone():
                valid_referrer = int(referrer_id)
        
        # Insert user node with Welcome Bonus and initial 2x core speed limits
        cursor.execute('''
            INSERT INTO user_mining_nodes (user_id, mining_balance, base_speed, last_checkpoint, referred_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, WELCOME_BONUS, 2.0, now_str, valid_referrer))
        
        if valid_referrer:
            # Atomic update: Increments referrer's network volume and appends +1x speed booster
            cursor.execute('''
                UPDATE user_mining_nodes 
                SET total_referrals = total_referrals + 1,
                    referral_speed_bonus = referral_speed_bonus + 1.0
                WHERE user_id = ?
            ''', (valid_referrer,))
            
        conn.commit()
        conn.close()
        return {
            "balance": WELCOME_BONUS,
            "total_speed": 2.0,
            "referrals": 0,
            "is_new": True
        }
    
    conn.close()
    return calculate_realtime_mined_tokens(user_id)

def calculate_realtime_mined_tokens(user_id: int) -> dict:
    """
    Executes the proof-of-time micro-inference matrix to calculate accrued tokens
    since the last claimed checkpoint based on total aggregated speed nodes.
    """
    conn = sqlite3.connect("crypto_factory.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT mining_balance, base_speed, referral_speed_bonus, last_checkpoint, total_referrals FROM user_mining_nodes WHERE user_id = ?", (user_id,))
    node = cursor.fetchone()
    
    if not node:
        conn.close()
        return {"balance": 0.0, "total_speed": 2.0, "referrals": 0}
    
    current_balance, base_speed, referral_bonus, last_checkpoint_str, total_referrals = node
    total_speed = base_speed + referral_bonus  # Total Speed = 2x Base + (1x * Friends)
    
    # Computing exact elapsed clock cycles (seconds passed)
    last_check = datetime.fromisoformat(last_checkpoint_str)
    elapsed_seconds = (datetime.utcnow() - last_check).total_seconds()
    
    # 0.001 tokens mined per unit of speed multiplier per second
    generated_tokens = elapsed_seconds * (total_speed * 0.001)
    new_balance = current_balance + generated_tokens
    
    # Persisting the updated ledger state
    now_str = datetime.utcnow().isoformat()
    cursor.execute('''
        UPDATE user_mining_nodes 
        SET mining_balance = ?, last_checkpoint = ? 
        WHERE user_id = ?
    ''', (new_balance, now_str, user_id))
    
    conn.commit()
    conn.close()
    
    return {
        "balance": round(new_balance, 3),
        "total_speed": total_speed,
        "referrals": total_referrals
    }
    
        
