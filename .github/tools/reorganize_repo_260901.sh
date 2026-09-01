#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from pathlib import Path
replacements = {
    '.github/tools/compare_v168_variants.py': {
        'A = Path("014_260901_v1.6.8.ipynb")': 'A = Path("code/releases/v1.6.8/014_260901_v1.6.8.ipynb")',
        'B = Path("014_260901_v1.6.8(새채팅).ipynb")': 'B = Path("code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb")',
        'OUT = Path("v1.6.8_comparison_report_260901.txt")': 'OUT = Path("reports/comparison/2026-09-01_v1.6.8_github_vs_새채팅.txt")',
    },
    '.github/tools/inspect_v168_critical.py': {
        '("A_GITHUB", Path("014_260901_v1.6.8.ipynb"))': '("A_GITHUB", Path("code/releases/v1.6.8/014_260901_v1.6.8.ipynb"))',
        '("B_NEWCHAT", Path("014_260901_v1.6.8(새채팅).ipynb"))': '("B_NEWCHAT", Path("code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb"))',
        'Path("v1.6.8_critical_implementation_extract_260901.txt")': 'Path("reports/inspection/2026-09-01_v1.6.8_critical_impl.txt")',
    },
    '.github/tools/run_v168_regressions.py': {
        '("A_GITHUB", Path("014_260901_v1.6.8.ipynb"), "test_v168_manual_sell_ledger_helpers")': '("A_GITHUB", Path("code/releases/v1.6.8/014_260901_v1.6.8.ipynb"), "test_v168_manual_sell_ledger_helpers")',
        '("B_NEWCHAT", Path("014_260901_v1.6.8(새채팅).ipynb"), "test_v168_live_ledger_and_timing")': '("B_NEWCHAT", Path("code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb"), "test_v168_live_ledger_and_timing")',
        'OUT = Path("v1.6.8_regression_run_report_260901.txt")': 'OUT = Path("reports/regression/2026-09-01_v1.6.8_regression.txt")',
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
