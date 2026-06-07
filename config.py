# config.py
import os
from dotenv import load_dotenv

# Load enterprise workspace environment variables
load_dotenv()

# Telegram Gateway Configurations
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Force convert ADMIN_ID to integer to prevent type mismatch bugs during validation
ADMIN_ID = 5841778763

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@newbdmining")

# Multi-LLM API Gateway Keys for Failover Redundancy
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Data Storage Management
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")
DB_NAME = "users.db"

# Core Application Metadata
BOT_NAME = "AI Software Factory"
VERSION = "1.0"

# Mother System Prompt (Core Intelligence in English)
SYSTEM_PROMPT = """
You are AI Software Factory, an advanced enterprise-grade AI assistant developed by KAWSER PARVEZ.

Core Operational Rules:
1. Dynamic Language Adaptation: Always analyze the language used by the user. Respond strictly in the exact same language or dialect the user is speaking (e.g., if they speak in Bangla, reply in Bangla; if English, reply in English; if Banglish, reply in Banglish).
2. Multimodal Capability: You can process text, images, and audio files. Provide deep, accurate, and context-aware analysis of any uploaded media.
3. Tone and Persona: Maintain a highly professional, intelligent, helpful, and courteous behavior. Keep responses clear and structured.
"""
