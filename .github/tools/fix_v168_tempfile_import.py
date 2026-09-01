#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

path = Path('.github/tools/build_v1_6_8.py')
text = path.read_text(encoding='utf-8')

old_guard = '    if "import tempfile" not in body:\n'
new_guard = '    if "\\nimport tempfile\\n" not in body:\n'
if old_guard in text:
    text = text.replace(old_guard, new_guard, 1)
elif new_guard not in text:
    raise SystemExit('tempfile guard not found')

# Correct the validation target: validate_output owns cells/full, not a local body variable.
wrong_validation = '    assert "\\nimport tempfile\\n" in body, "top-level tempfile import missing"\n'
right_validation = (
    '    assert "\\nimport tempfile\\n" in cell_source(cells[1]), '
    '"top-level tempfile import missing"\n'
)
if wrong_validation in text:
    text = text.replace(wrong_validation, right_validation, 1)
elif right_validation not in text:
    anchor = '    assert "LIVE_STATE_FILE_LOCK = threading.Lock()" in full\n'
    if anchor not in text:
        raise SystemExit('validation anchor not found')
    text = text.replace(anchor, right_validation + anchor, 1)

compile(text, str(path), 'exec')
path.write_text(text, encoding='utf-8')
print('verified top-level tempfile guard and corrected builder validation')
