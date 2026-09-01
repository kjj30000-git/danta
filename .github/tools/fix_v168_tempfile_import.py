#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

path = Path('.github/tools/build_v1_6_8.py')
text = path.read_text(encoding='utf-8')

old = '    if "import tempfile" not in body:\n'
new = '    if "\\nimport tempfile\\n" not in body:\n'
if old not in text:
    raise SystemExit('expected tempfile guard not found')
text = text.replace(old, new, 1)

# Make the builder itself reject a generated notebook that only has a local
# test import rather than the required top-level program import.
anchor = '    assert "LIVE_STATE_FILE_LOCK = threading.Lock()" in full\n'
insert = (
    '    assert "\\nimport tempfile\\n" in body, "top-level tempfile import missing"\n'
    '    assert "LIVE_STATE_FILE_LOCK = threading.Lock()" in full\n'
)
if anchor not in text:
    raise SystemExit('validation anchor not found')
text = text.replace(anchor, insert, 1)

compile(text, str(path), 'exec')
path.write_text(text, encoding='utf-8')
print('fixed top-level tempfile import guard and validation')
