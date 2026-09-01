#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

changes = {
    Path('.github/tools/build_v1_6_8.py'): [
        ('014_260901_v1.6.8.ipynb', '014_260902_v1.6.8.ipynb'),
        ('014_260901_v1.6.8.txt', '014_260902_v1.6.8.txt'),
    ],
    Path('.github/tools/compare_v168_variants.py'): [
        ('code/releases/014_260901_v1.6.8.ipynb', 'code/releases/014_260902_v1.6.8.ipynb'),
    ],
}

for path, replacements in changes.items():
    text = path.read_text(encoding='utf-8')
    before = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != before:
        compile(text, str(path), 'exec') if path.suffix == '.py' else None
        path.write_text(text, encoding='utf-8')
        print(f'updated: {path}')
    else:
        print(f'no change: {path}')
