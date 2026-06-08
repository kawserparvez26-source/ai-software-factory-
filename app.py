# app.py
import os
import logging
import io
from datetime import datetime
import telebot
from telebot import types
from flask import Flask, jsonify
import time
from math import ceil
from collections import defaultdict
import threading
# Existing imports placeholder... mofidy database import block to include new layers:
from database import (
    init_db, save_user, get_user_count, get_all_users,
    ban_user, unban_user, is_banned, get_banned_count,
    save_chat_memory, get_chat_memory, get_engine_metrics_report,
    activate_or_fetch_mining_node, calculate_realtime_mined_tokens # <── Add these two
)

import config
from database import (
    init_db, save_user, get_user_count, get_all_users,
    ban_user, unban_user, is_banned, get_banned_count,
    save_chat_memory, get_chat_memory, get_engine_metrics_report
)

from ai_engine import process_multimodal_request

# Initialize Logging and Platform Frameworks
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot(config.BOT_TOKEN)

# Initialize Storage Infrastructure
init_db()

# In-memory rate limiting database registries (100% Free & Fast)
USER_MESSAGE_TIMES = defaultdict(list)
BANNED_USERS = {}
SYSTEM_OPERATIONAL_STATE = True  

def check_spam_and_rate_limit(user_id: int) -> tuple:
    current_time = time.time()
    
    if user_id in BANNED_USERS:
        ban_expiry = BANNED_USERS[user_id]
        if current_time < ban_expiry:
            return True, int(ban_expiry - current_time)
        else:
            del BANNED_USERS[user_id]
            USER_MESSAGE_TIMES[user_id] = []

    msg_timestamps = USER_MESSAGE_TIMES[user_id]
    msg_timestamps = [t for t in msg_timestamps if current_time - t < 5]
    
    msg_timestamps.append(current_time)
    USER_MESSAGE_TIMES[user_id] = msg_timestamps
    
    if len(msg_timestamps) > 2:
        BANNED_USERS[user_id] = current_time + 900  
        return True, 900
        
    return False, 0

@app.route("/")
def home_endpoint():
    return jsonify({
        "application": config.BOT_NAME,
        "status": "synchronized",
        "version": config.VERSION
    }), 200

@app.route("/health")
def health_endpoint():
    return jsonify({"status": "healthy"}), 200

def is_subscribed_to_channel(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(config.CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Membership subscription check failed for {user_id}: {str(e)}")
        return False

def get_verified_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_help = types.InlineKeyboardButton("📚 Help Guide", callback_data="ui_help")
    btn_about = types.InlineKeyboardButton("ℹ️ System Info", callback_data="ui_about")
    btn_support = types.InlineKeyboardButton("👨‍💻 Support", callback_data="ui_support")
    markup.row(btn_help, btn_about)
    markup.row(btn_support)
    return markup

# ====================================================================
# HANDLER: MOLECULAR START COMMAND WITH DEEP-LINK DECODING LAYER
# ====================================================================
@bot.message_handler(commands=['start'])
def handle_start_and_referral_ingress(message):
    """
    Intercepts user activation intents, parses the atomic referral tracking codes,
    and provisions the initial cloud mining allocations.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Anonymous Node"
    chat_id = message.chat.id
    
    if is_banned(user_id):
        bot.send_message(chat_id, "🚫 Your node has been blacklisted from the sovereign mesh.")
        return
        
    save_user(user_id, username)
    
    # Parsing deep-link codes (e.g., /start ref_12345)
    command_args = message.text.split()
    detected_referrer = None
    if len(command_args) > 1 and command_args[1].startswith("ref_"):
        try:
            detected_referrer = int(command_args[1].replace("ref_", ""))
        except ValueError:
            pass
            
    # Activating the user's personal cloud engine node with Welcome Bonus (1000 Tokens) & 2x Base Speed
    mining_data = activate_or_fetch_mining_node(user_id, detected_referrer)
    
    welcome_msg = (
        f"🛸 *Welcome to the Sovereign AI Software Factory Core!*\n\n"
        f"💎 *Welcome Bonus Received:* `1,000.000 FACTORY Tokens`\n"
        f"⚡ *Autonomous Baseline Speed Active:* `{mining_data['total_speed']}x Multiplier`\n\n"
        f"⛏️ Your decentralized cloud miner is now eternally active in the background. "
        f"Type `/mine` to access your dynamic ledger dashboard or `/frenz` to scale your network bond!"
    )
    
    bot.send_message(chat_id, welcome_msg, parse_mode="Markdown")
    
    
    if is_banned(user.id):
        bot.reply_to(message, "🚫 Access Denied! Your node identifier is blacklisted by administration.")
        return

    if not is_subscribed_to_channel(user.id):
        markup = types.InlineKeyboardMarkup()
        btn_join = types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{config.CHANNEL_USERNAME.replace('@', '')}")
        btn_verify = types.InlineKeyboardButton("✅ Verify Membership", callback_data="verify_subscription")
        markup.row(btn_join)
        markup.row(btn_verify)
        
        bot.send_message(
            message.chat.id,
            f"🔒 Access Restricted!\n\nTo unlock {config.BOT_NAME}, you must:\n1️⃣ Join our official channel.\n2️⃣ Click the verify button below.",
            reply_markup=markup
        )
        return

    save_user(user)
    bot.send_message(
        message.chat.id,
        f"🤖 *{config.BOT_NAME}* — Version {config.VERSION}\n\n🚀 Welcome to the automation gateway. System operational and listening.",
        parse_mode="Markdown",
        reply_markup=get_verified_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_interface_callbacks(call):
    user_id = call.from_user.id

    if call.data == "verify_subscription":
        if is_subscribed_to_channel(user_id):
            bot.answer_callback_query(call.id, "✅ Verification Complete!", show_alert=False)
            save_user(call.from_user)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                f"🤖 *{config.BOT_NAME}* initialized.\n\nVerification successful. System is ready.",
                parse_mode="Markdown",
                reply_markup=get_verified_main_keyboard()
            )
        else:
            bot.answer_callback_query(call.id, "❌ Verification Failed. Please join the channel first.", show_alert=True)

    elif call.data == "ui_help":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📚 Use the `/help` command to view the comprehensive systems operations catalog.")

    elif call.data == "ui_about":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"🤖 *{config.BOT_NAME}*\nFramework Core: Multimodal LLM\nBuild Version: {config.VERSION}\nLead Architect: KAWSER PARVEZ", parse_mode="Markdown")

    elif call.data == "ui_support":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📩 To log an administrative ticket, please format your message as follows:\n`/support Your message content here`")
            
    # Admin Interface Callbacks Telemetry Routing Fix
    elif call.data == "admin_stats":
        if call.from_user.id == config.ADMIN_ID:
            bot.answer_callback_query(call.id)
            call.message.from_user.id = call.from_user.id
            handle_admin_dashboard_metrics(call.message)
        else:
            bot.answer_callback_query(call.id, "🚫 Unauthorized Access!", show_alert=True)

    elif call.data == "admin_logs":
        if call.from_user.id == config.ADMIN_ID:
            bot.answer_callback_query(call.id)
            call.message.from_user.id = call.from_user.id
            handle_admin_live_log_stream(call.message)
        else:
            bot.answer_callback_query(call.id, "🚫 Unauthorized Access!", show_alert=True)

    elif call.data == "admin_backup":
        if call.from_user.id == config.ADMIN_ID:
            bot.answer_callback_query(call.id)
            call.message.from_user.id = call.from_user.id
            handle_admin_database_backup(call.message)
        else:
            bot.answer_callback_query(call.id, "🚫 Unauthorized Access!", show_alert=True)

@bot.message_handler(commands=['help'])
def handle_help_catalog(message):
    if is_banned(message.from_user.id): return
    is_admin = (message.from_user.id == config.ADMIN_ID)
    catalog = (
        f"📚 *{config.BOT_NAME} Operations Manual*\n\n"
        "`/start` - Reboot System Connection\n"
        "`/help` - Open System Catalog\n"
        "`/support` <text> - Send Admin Ticket\n"
    )
    if is_admin:
        catalog += (
            "\n⚡ *Administrative Access Subsystem*\n"
            "`/stats` - Pull Analytical Repository\n"
            "`/broadcast` <text> - Deploy Global Node Transmission\n"
            "`/ban` <user_id> - Suspend Network Access\n"
            "`/unban` <user_id> - Restore Network Access\n"
            "`/maintenance` <on/off> - Toggle Maintenance State\n"
            "`/audit` <user_id> - Interrogate Terminal Node\n"
            "`/setkey` <engine> <key> - Hot-swap API Tokens\n"
            "`/logs` - Operational System Diagnostics\n"
            "`/backup` - Export Physical Schema State\n"
        )
    bot.reply_to(message, catalog, parse_mode="Markdown")


# ====================================================================
# HANDLER: DECENTRALIZED REAL-TIME MINING LEDGER TERMINAL (/mine)
# ====================================================================
@bot.message_handler(commands=['mine'])
def render_live_mining_terminal(message):
    """
    Fetches elapsed computational loops, auto-updates balance states,
    and returns an actionable summary card to the active terminal node.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if is_banned(user_id): return
    
    # Calculate accumulated tokens dynamically on terminal invocation
    stats = calculate_realtime_mined_tokens(user_id)
    
    mining_layout = (
        f"⛏️ *Sovereign AI Autonomous Cloud Miner* ⛏️\n\n"
        f"💰 *Current Ledger Balance:* `{stats['balance']} FACTORY`\n"
        f"⚡ *Calculated Processing Speed:* `{stats['total_speed']}x Multiplier`\n"
        f"👥 *Network Connected Nodes:* `{stats['referrals']} Referrals`\n\n"
        f"📈 _Status: Operational. The baseline 2x power is scaling dynamically "
        f"with every new particle connection injected into your network layer._"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="🔄 Sync & Claim Checkpoint", callback_data="refresh_mining_stats"))
    
    bot.send_message(chat_id, mining_layout, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_mining_stats")
def trigger_terminal_refresh(call):
    """
    Callback wrapper to allow users to force checkpoint state updates synchronously.
    """
    user_id = call.from_user.id
    stats = calculate_realtime_mined_tokens(user_id)
    
    updated_layout = (
        f"⛏️ *Sovereign AI Autonomous Cloud Miner* ⛏️\n\n"
        f"💰 *Current Ledger Balance:* `{stats['balance']} FACTORY`\n"
        f"⚡ *Calculated Processing Speed:* `{stats['total_speed']}x Multiplier`\n"
        f"👥 *Network Connected Nodes:* `{stats['referrals']} Referrals`\n\n"
        f"⏳ _Last Sync Checkpoint: Just Now (UTC)_"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="🔄 Sync & Claim Checkpoint", callback_data="refresh_mining_stats"))
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=updated_layout,
            parse_mode="Markdown",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id, text="🚀 Ledger synchronized successfully!")
    except Exception:
        bot.answer_callback_query(call.id)

# ====================================================================
# HANDLER: H2O MOLECULAR VIRAL REFERRAL BRIDGE CONTROLLER (/frenz)
# ====================================================================
@bot.message_handler(commands=['frenz'])
def display_referral_extraction_bridge(message):
    """
    Extracts the user node ID, creates a dynamic sub-routing link string,
    and returns a tailored recruitment dispatch grid.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if is_banned(user_id): return
    
    stats = calculate_realtime_mined_tokens(user_id)
    bot_info = bot.get_me()
    
    # Constructing the unique atomic referral matrix string
    personal_invite_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    frenz_payload = (
        f"👥 *Sovereign $H_2O$ Viral Referral Network* 👥\n\n"
        f"🔗 *Your Unique Molecular Invitation Link:*\n"
        f"`{personal_invite_link}`\n\n"
        f"🧬 *Current Network Connections:* `{stats['referrals']} Friends`\n"
        f"⚡ *Aggregated Multiplier Bonus:* `+{stats['total_speed'] - 2.0}x Power`\n\n"
        f"🎁 *Rule Matrix:* Invite your friends right now! Each successful node injection "
        f"awards them `1,000 Welcome Tokens` instantly and unlocks an extra *+1x speed booster* permanently for your factory layout!"
    )
    
    bot.send_message(chat_id, frenz_payload, parse_mode="Markdown")
    
    
@bot.message_handler(commands=['admin', 'panel'])
def handle_admin_panel_command(message):
    user_id = message.from_user.id
    if user_id != config.ADMIN_ID:
        bot.reply_to(
            message, 
            f"❌ *Access Denied!*\n\nYou are not registered as the System Administrator.\nYour Actual Telegram ID: `{user_id}`\n\n*Fix:* Copy this ID and update the `ADMIN_ID` field in your `.env` file.", 
            parse_mode="Markdown"
        )
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_stats = types.InlineKeyboardButton("📊 System Stats", callback_data="admin_stats")
    btn_logs = types.InlineKeyboardButton("📋 System Logs", callback_data="admin_logs")
    btn_backup = types.InlineKeyboardButton("💾 DB Backup", callback_data="admin_backup")
    markup.add(btn_stats, btn_logs, btn_backup)

    bot.reply_to(
        message, 
        "⚡ *AI SOFTWARE FACTORY — ADMINISTRATIVE CONTROL PANEL*\n\nSelect an infrastructure operations module from the gateway control layer below:", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

@bot.message_handler(commands=['stats', 'dashboard'])
def handle_admin_dashboard_metrics(message):
    if message.from_user.id != config.ADMIN_ID:
        bot.reply_to(
            message, 
            f"❌ *Access Denied!*\nYour Telegram ID: `{message.from_user.id}` is unauthorized.", 
            parse_mode="Markdown"
        )
        return
            
    try:
        total_users = get_user_count()
        banned_users = get_banned_count()
        metrics = get_engine_metrics_report()
        
        metrics_ui = ""
        if metrics:
            for engine, data in metrics.items():
                metrics_ui += f" ├ 🟢 *{engine}* ── Calls: `{data.get('calls', 0)}` | Fails: `{data.get('fails', 0)}`\n"
        else:
            metrics_ui = " ├ ⚠️ No LLM telemetry engine logs found.\n"
            
        dashboard_text = (
            f"📊 *SYSTEM ADMINISTRATIVE MANAGEMENT CONTROL*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 *User Subsystem Infrastructure*\n"
            f" ├ Registered Users: `{total_users}`\n"
            f" └ Blacklisted Nodes: `{banned_users}`\n\n"
            f"🎛️ *LLM Core Gateway Telemetry Logs*\n"
            f"{metrics_ui}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥️ *Subsystem State:* `Operational // Nominal`"
        )
        
        bot.reply_to(message, dashboard_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to generate dashboard statistics metrics: {str(e)}")
        bot.reply_to(message, "⚠️ `System Error:` Failed to compile operational metrics logs database.")
        

@bot.message_handler(commands=['broadcast'])
def handle_admin_broadcast(message):
    if message.from_user.id != config.ADMIN_ID:
        return
    
    payload = message.text.replace("/broadcast", "").strip()
    if not payload:
        bot.reply_to(message, "⚠️ Usage: `/broadcast <your message>`", parse_mode="Markdown")
        return

    users = get_all_users()
    if not users:
        bot.reply_to(message, "⚠️ Broadcast aborted: No registered terminals discovered in database memory.")
        return

    status_msg = bot.reply_to(message, "⚡ *Deploying global node transmission... Please wait.*", parse_mode="Markdown")
    
    delivery_count = 0
    failed_count = 0
    
    for user in users:
        target_id = user[0] if isinstance(user, (tuple, list)) else (user.user_id if hasattr(user, 'user_id') else user)
        try:
            bot.send_message(target_id, payload)
            delivery_count += 1
            time.sleep(0.05)
        except Exception:
            failed_count += 1
            continue

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        text=f"✅ *Global Node Broadcast Completed.*\n\n🚀 Delivered: `{delivery_count}` terminals.\n❌ Failed/Blocked: `{failed_count}` terminals.",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['ban'])
def handle_admin_ban_override(message):
    if message.from_user.id != config.ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        ban_user(target_id)
        bot.reply_to(message, f"🚫 Access parameters suspended for ID: {target_id}")
    except Exception:
        bot.reply_to(message, "⚠️ Syntax: `/ban <user_id>`")

@bot.message_handler(commands=['unban'])
def handle_admin_unban_override(message):
    if message.from_user.id != config.ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        unban_user(target_id)
        bot.reply_to(message, f"✅ System privileges restored for ID: {target_id}")
    except Exception:
        bot.reply_to(message, "⚠️ Syntax: `/unban <user_id>`")

@bot.message_handler(commands=['maintenance'])
def handle_admin_maintenance_toggle(message):
    if message.from_user.id != config.ADMIN_ID:
        return
    
    global SYSTEM_OPERATIONAL_STATE
    command_args = message.text.replace("/maintenance", "").strip().lower()
    
    if command_args == "on":
        SYSTEM_OPERATIONAL_STATE = False
        bot.reply_to(message, "⚙️ *Subsystem Alert:* Maintenance mode has been ACTIVATED. Standard inbound traffic is now locked down.", parse_mode="Markdown")
    elif command_args == "off":
        SYSTEM_OPERATIONAL_STATE = True
        bot.reply_to(message, "🚀 *Subsystem Alert:* Maintenance mode has been DEACTIVATED. Global node pathways are now fully operational.", parse_mode="Markdown")
    else:
        current_status = "Nominal / Open" if SYSTEM_OPERATIONAL_STATE else "Under Maintenance / Restricted"
        bot.reply_to(message, f"📊 *System State:* `{current_status}`\n\n💡 Syntax: `/maintenance on` or `/maintenance off`", parse_mode="Markdown")

@bot.message_handler(commands=['audit'])
def handle_admin_user_audit(message):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    try:
        target_id = int(message.text.split()[1])
        is_user_banned = is_banned(target_id) or (target_id in BANNED_USERS)
        chat_history = get_chat_memory(target_id, limit=3)
        
        history_snippet = ""
        if chat_history:
            for log in chat_history:
                role_label = "👤 User" if log.get('role') == 'user' else "🤖 AI"
                history_snippet += f" ├ *{role_label}:* {log.get('content')[:50]}...\n"
        else:
            history_snippet = " ├ No transaction history found.\n"

        audit_report = (
            f"🔍 *CORE SUBSYSTEM INTERROGATION REPORT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 Targeted Node ID: `{target_id}`\n"
            f"⚡ Network Authorization: {'🚫 BLACKLISTED' if is_user_banned else '✅ VERIFIED'}\n\n"
            f"📜 *Recent Conversation Telemetry (Last 3 Records):*\n"
            f"{history_snippet}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, audit_report, parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "⚠️ *Syntax Error:* Please specify a valid connection string. Usage: `/audit <user_id>`", parse_mode="Markdown")
        
@bot.message_handler(commands=['support'])
def handle_support_ticket(message):
    if is_banned(message.from_user.id): return
    payload = message.text.replace("/support", "").strip()
    if not payload:
        bot.reply_to(message, "⚠️ Syntax: `/support <your message>`")
        return

    bot.send_message(
        config.ADMIN_ID,
        f"📩 *Inbound Support Telemetry*\n\n👤 Profile: {message.from_user.first_name}\n🆔 Connection ID: `{message.from_user.id}`\n\n💬 Payload:\n{payload}",
        parse_mode="Markdown"
    )
    bot.reply_to(message, "✅ Telemetry package successfully dispatched to the Operations Center.")

@bot.message_handler(commands=['setkey'])
def handle_admin_api_key_rotation(message):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ *Syntax:* `/setkey <GEMINI|GROQ|OPENROUTER> <new_api_key>`", parse_mode="Markdown")
            return
            
        target_engine = parts[1].upper()
        new_key = parts[2].strip()
        
        if target_engine == "GEMINI":
            config.GEMINI_API_KEY = new_key
        elif target_engine == "GROQ":
            config.GROQ_API_KEY = new_key
        else:
            bot.reply_to(message, "❌ *Rotation Failed:* Unsupported gateway engine specified.")
            return
            
        bot.reply_to(message, f"🔑 *Encryption Gateway Updated:* Dynamic runtime hot-swap complete for `{target_engine}` engine core.", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"API key runtime rotation exception: {str(e)}")
        bot.reply_to(message, "⚠️ `Runtime Error:` Key rotation pipeline encountered an exception.")

@bot.message_handler(commands=['logs'])
def handle_admin_live_log_stream(message):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    try:
        nominal_memory_status = "Nominal" if len(USER_MESSAGE_TIMES) < 500 else "High Traffic Memory Consumption"
        
        system_diagnostics = (
            f"🖥️ *CORE RUNTIME SYSTEM DIAGNOSTICS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Timestamp: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            f"🎛️ Memory Buffers Stack: `{len(USER_MESSAGE_TIMES)} active connections`\n"
            f"📦 Limiter Cool-downs: `{len(BANNED_USERS)} terminals flagged`\n"
            f"🛡️ Core Health Status: `{nominal_memory_status}`\n"
            f"⚡ Thread Allocation: `Active Pool // Non-blocking`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, system_diagnostics, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Failed to parse framework engine state: {str(e)}")

@bot.message_handler(commands=['backup'])
def handle_admin_database_backup(message):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    try:
        db_path = config.DB_NAME
        if os.path.exists(db_path):
            with open(db_path, 'rb') as db_file:
                bot.send_document(
                    message.chat.id, 
                    db_file, 
                    caption=f"📦 *Automated Infrastructure Backup Complete*\n📅 Database Snapshot: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
                    parse_mode="Markdown"
                )
        else:
            bot.reply_to(message, "❌ *Backup Error:* Target binary file footprint could not be located on this cluster allocation.")
    except Exception as e:
        logger.error(f"Critical data repository backup sequence terminated: {str(e)}")
        bot.reply_to(message, "⚠️ `Critical Storage Error:` Automated synchronization pipeline failed to export target schema.")

# =======================================================
#  ➕ CORE SYSTEM: MULTIMODAL MESSAGE PROCESSING (UPDATED V2.0)
# =======================================================

@bot.message_handler(content_types=['text', 'photo', 'voice', 'audio'])
def handle_inbound_multimodal_stream(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if is_banned(user_id):
        bot.send_message(chat_id, "🚫 Access Denied! Your node identifier is blacklisted by administration.")
        return

    if not SYSTEM_OPERATIONAL_STATE and user_id != config.ADMIN_ID:
        bot.send_message(chat_id, "⚙️ *System Maintenance Underway:*\n\nOur computational cores are receiving upgrades. Standard pathways are temporarily locked. Please try again shortly.", parse_mode="Markdown")
        return

    is_spamming, cooling_period = check_spam_and_rate_limit(user_id)
    if is_spamming and user_id != config.ADMIN_ID:
        bot.send_message(chat_id, f"⚠️ *Rate Limit Exceeded:*\n\nBreach in baseline threshold detected. Network cooldown forced. Remaining suspension: `{cooling_period}s`.", parse_mode="Markdown")
        return

    if not is_subscribed_to_channel(user_id) and user_id != config.ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        btn_join = types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{config.CHANNEL_USERNAME.replace('@', '')}")
        btn_verify = types.InlineKeyboardButton("✅ Verify Membership", callback_data="verify_subscription")
        markup.row(btn_join)
        markup.row(btn_verify)
        bot.send_message(chat_id, "🔒 *Access Restricted!*\n\nTo continue utilizing AI processing pipelines, you must join our official network core.", parse_mode="Markdown", reply_markup=markup)
        return

    processing_notice = bot.reply_to(message, "🧠 *Thinking... Please wait.*", parse_mode="Markdown")

    try:
        user_prompt = message.text if message.content_type == 'text' else (message.caption or "")
        media_bytes = None
        mime = None

        if message.content_type == 'photo':
            if not user_prompt:
                user_prompt = "Analyze this image in detail."
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_binary = bot.download_file(file_info.file_path)
            media_bytes = io.BytesIO(downloaded_binary).getvalue()
            mime = "image/jpeg"

        elif message.content_type in ['voice', 'audio']:
            if not user_prompt:
                user_prompt = "Listen to this audio record carefully and reply intelligently."
            file_id = message.voice.file_id if message.content_type == 'voice' else message.audio.file_id
            file_info = bot.get_file(file_id)
            downloaded_binary = bot.download_file(file_info.file_path)
            media_bytes = io.BytesIO(downloaded_binary).getvalue()
            mime = message.voice.mime_type if message.content_type == 'voice' else message.audio.mime_type

        context_history = get_chat_memory(user_id, limit=10)

        ai_response = process_multimodal_request(
            prompt_text=user_prompt,
            mime_type=mime,
            media_data=media_bytes,
            chat_history=context_history
        )

        save_chat_memory(user_id, "user", user_prompt if user_prompt else "[Sent Media File]")
        save_chat_memory(user_id, "model", ai_response)

        try:
            bot.delete_message(chat_id, processing_notice.message_id)
        except Exception: pass
        
        if len(ai_response) > 4000:
            for x in range(0, len(ai_response), 4000):
                bot.send_message(chat_id, ai_response[x:x+4000], parse_mode="Markdown")
        else:
            bot.send_message(chat_id, ai_response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Multimodal Engine Execution Exception for client {user_id}: {str(e)}")
        try:
            bot.delete_message(chat_id, processing_notice.message_id)
        except Exception: pass
        bot.send_message(chat_id, "⚠️ *Gateway Processing Exception:*\n\nThe computational LLM cluster failed to resolve this stream. Try restructuring your payload context.", parse_mode="Markdown")

def run_bot():
    logger.info("⚡ Synchronizing with Telegram API Network...")
    try:
        bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.critical(f"Bot engine crashed unexpectedly: {str(e)}")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
