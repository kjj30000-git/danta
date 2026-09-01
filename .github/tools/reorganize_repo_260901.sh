#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from pathlib import Path
replacements = {
    '.github/tools/compare_v168_variants.py': {
        'A = Path("code/releases/v1.6.8/014_260901_v1.6.8.ipynb")': 'A = Path("code/releases/014_260901_v1.6.8.ipynb")',
    },
    '.github/tools/inspect_v168_critical.py': {
        '("A_GITHUB", Path("code/releases/v1.6.8/014_260901_v1.6.8.ipynb"))': '("A_GITHUB", Path("code/releases/014_260901_v1.6.8.ipynb"))',
    },
    '.github/tools/run_v168_regressions.py': {
        '("A_GITHUB", Path("code/releases/v1.6.8/014_260901_v1.6.8.ipynb"), "test_v168_manual_sell_ledger_helpers")': '("A_GITHUB", Path("code/releases/014_260901_v1.6.8.ipynb"), "test_v168_manual_sell_ledger_helpers")',
    },
}
for file_name, mapping in replacements.items():
    path = Path(file_name)
    text = path.read_text(encoding='utf-8')
    for old, new in mapping.items():
        if old not in text:
            raise SystemExit(f'missing expected helper path marker in {file_name}: {old}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')
PY
git add .github/tools/compare_v168_variants.py .github/tools/inspect_v168_critical.py .github/tools/run_v168_regressions.py
