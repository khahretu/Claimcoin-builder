import sys, traceback
sys.path.insert(0, '.')
from bot import process_zip_file
import tempfile, zipfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    zip_path = tmpdir / 'test.zip'
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('page1.html', '<html><head><title>Test</title></head><body>Hello</body></html>')
        zf.writestr('subdir/page2.htm', '<html><head><title>Page2</title></head><body>Hi</body></html>')
    try:
        result = process_zip_file(zip_path, 'EXO_test123')
        print('Result:', result)
        assert result['success'] == True, f"success not True: {result['success']}"
        assert result['injected_files'] == 2, f"injected_files not 2: {result['injected_files']}"
        assert result['output_path'] is not None, f"output_path is None: {result['output_path']}"
    except AssertionError as e:
        print(f'AssertionError: {e}')
        traceback.print_exc()
