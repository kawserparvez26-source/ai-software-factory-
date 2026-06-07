# bot.py
import threading
import logging
from app import app, bot

# Configure standard production logger node
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_flask_web_server():
    """
    Spins up the Flask web environment on port 10000.
    Required by free hosting platforms like Render to pass TCP health checks.
    """
    logger.info("🌐 Initializing Flask production listener interface...")
    # Render maps internal services to port 10000 by default
    app.run(host="0.0.0.0", port=10000, debug=False, use_reloader=False)


def run_telegram_bot_polling():
    """
    Establishes a continuous asynchronous non-blocking connection pool 
    with the Telegram API servers.
    """
    logger.info("🤖 AI Software Factory Gateway Core is now live and listening...")
    try:
        # infinity_polling automatically catches network dropped frames and reconnects
        bot.infinity_polling(timeout=20, long_polling_timeout=30)
    except Exception as e:
        logger.critical(f"Fatal network exception caught during polling sequence: {str(e)}")


if __name__ == "__main__":
    logger.info("🏭 Booting AI Automation Ecosystem Module...")
    
    # Allocating Web Server to a background worker thread to prevent thread blocking
    web_thread = threading.Thread(target=run_flask_web_server, daemon=True)
    web_thread.start()
    
    # Executing the Telegram listener engine on the main application loop
    run_telegram_bot_polling()
