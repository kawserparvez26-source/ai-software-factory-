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

        
