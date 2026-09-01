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

# The v1.6.8 generated program should not retain the old v1.6.7 title comment.
func_marker = 'def patch_settings_and_globals(body: str) -> str:\n'
header_patch = (
    '    body = replace_once(\n'
    '        body,\n'
    '        "# 단타 자동 스크리너 v1.6.7\\n",\n'
    '        "# 단타 자동 스크리너 v1.6.8\\n",\n'
    '        "program header version",\n'
    '    )\n'
)
if header_patch not in text:
    if func_marker not in text:
        raise SystemExit('patch_settings_and_globals marker not found')
    text = text.replace(func_marker, func_marker + header_patch, 1)

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

header_validation = (
    '    assert "# 단타 자동 스크리너 v1.6.8" in cell_source(cells[1]), '
    '"program header version mismatch"\n'
)
if header_validation not in text:
    if right_validation not in text:
        raise SystemExit('tempfile validation marker not found')
    text = text.replace(right_validation, right_validation + header_validation, 1)

compile(text, str(path), 'exec')
path.write_text(text, encoding='utf-8')
print('verified tempfile import and normalized v1.6.8 program header')
