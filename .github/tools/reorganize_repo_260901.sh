#!/usr/bin/env bash
set -euo pipefail

# Repository structure reorganization for the day-trading project.
# This script only moves/renames repository artifacts and updates helper paths.
# It does NOT modify trading notebook contents.

mkdir -p \
  code/releases/v1.6.7 \
  code/releases/v1.6.8 \
  code/candidates/v1.6.8 \
  handoff/2026-09-01 \
  reports/build \
  reports/comparison \
  reports/regression \
  reports/inspection \
  data \
  .github/archive

# ---- release / candidate code -------------------------------------------------
git mv -- "013_260830_v1.6.7_startmsg_fix.ipynb" \
  "code/releases/v1.6.7/013_260830_v1.6.7_startmsg_fix.ipynb"

git mv -- "014_260901_v1.6.8.ipynb" \
  "code/releases/v1.6.8/014_260901_v1.6.8.ipynb"
git mv -- "014_260901_v1.6.8.txt" \
  "code/releases/v1.6.8/014_260901_v1.6.8.txt"
git mv -- "stock_scanner_v1_6_8.py" \
  "code/releases/v1.6.8/stock_scanner_v1_6_8.py"

git mv -- "014_260901_v1.6.8(새채팅).ipynb" \
  "code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb"

# ---- handoff ------------------------------------------------------------------
git mv -- "주식_단타_v1.6.7_to_v1.6.8_인수인계서_최종_260901.md" \
  "handoff/2026-09-01/v1.6.7_to_v1.6.8_인수인계서_최종.md"

# ---- reports: type-first, date-prefixed filenames -----------------------------
git mv -- "v1.6.8_build_report_260901.txt" \
  "reports/build/2026-09-01_v1.6.8_build.txt"
git mv -- "v1.6.8_comparison_report_260901.txt" \
  "reports/comparison/2026-09-01_v1.6.8_github_vs_새채팅.txt"
git mv -- "v1.6.8_regression_run_report_260901.txt" \
  "reports/regression/2026-09-01_v1.6.8_regression.txt"
git mv -- "v1.6.8_critical_implementation_extract_260901.txt" \
  "reports/inspection/2026-09-01_v1.6.8_critical_impl.txt"

# Temporary builder chunks are retained, but moved out of the repository root.
git mv -- ".v168_builder_parts" ".github/archive/v1.6.8_builder_parts"

# ---- update helper scripts to structured paths --------------------------------
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

# ---- workflows use explicit trigger files to avoid concurrent report commits ---
cat > .github/workflows/build_v168.yml <<'YAML'
name: Build v1.6.8 from exact v1.6.7 base

on:
  workflow_dispatch:
  push:
    paths:
      - '.github/triggers/build_v168.txt'

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout exact repository contents
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Build and validate v1.6.8
        run: |
          python .github/tools/build_v1_6_8.py \
            code/releases/v1.6.7/013_260830_v1.6.7_startmsg_fix.ipynb \
            --output-dir code/releases/v1.6.8
          mkdir -p reports/build
          mv code/releases/v1.6.8/v1.6.8_build_report_260901.txt \
            reports/build/2026-09-01_v1.6.8_build.txt
      - name: Verify requested outputs exist
        run: |
          test -s code/releases/v1.6.8/014_260901_v1.6.8.ipynb
          test -s code/releases/v1.6.8/014_260901_v1.6.8.txt
          test -s code/releases/v1.6.8/stock_scanner_v1_6_8.py
          test -s reports/build/2026-09-01_v1.6.8_build.txt
          python -m py_compile code/releases/v1.6.8/stock_scanner_v1_6_8.py
      - name: Commit generated outputs
        run: |
          git config user.name 'chatgpt-v168-builder'
          git config user.email 'chatgpt-v168-builder@users.noreply.github.com'
          git add code/releases/v1.6.8 reports/build/2026-09-01_v1.6.8_build.txt
          if git diff --cached --quiet; then
            echo 'No generated changes to commit.'
          else
            git commit -m 'Build v1.6.8 from exact startmsg_fix base'
            git push
          fi
YAML

cat > .github/workflows/compare_v168_variants.yml <<'YAML'
name: Compare v1.6.8 variants

on:
  workflow_dispatch:
  push:
    paths:
      - '.github/triggers/compare_v168.txt'

permissions:
  contents: write

jobs:
  compare:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python .github/tools/compare_v168_variants.py
      - name: Commit comparison report
        run: |
          git config user.name 'chatgpt-v168-compare'
          git config user.email 'chatgpt-v168-compare@users.noreply.github.com'
          git add reports/comparison/2026-09-01_v1.6.8_github_vs_새채팅.txt
          if git diff --cached --quiet; then
            echo 'No report changes.'
          else
            git commit -m 'Compare GitHub and 새채팅 v1.6.8 variants'
            git push
          fi
YAML

cat > .github/workflows/inspect_v168_critical.yml <<'YAML'
name: Inspect v1.6.8 critical implementations

on:
  workflow_dispatch:
  push:
    paths:
      - '.github/triggers/inspect_v168.txt'

permissions:
  contents: write

jobs:
  inspect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python .github/tools/inspect_v168_critical.py
      - name: Commit inspection report
        run: |
          git config user.name 'chatgpt-v168-inspect'
          git config user.email 'chatgpt-v168-inspect@users.noreply.github.com'
          git add reports/inspection/2026-09-01_v1.6.8_critical_impl.txt
          if git diff --cached --quiet; then
            echo 'No report changes.'
          else
            git commit -m 'Inspect critical v1.6.8 implementation differences'
            git push
          fi
YAML

cat > .github/workflows/run_v168_regressions.yml <<'YAML'
name: Run v1.6.8 regressions

on:
  workflow_dispatch:
  push:
    paths:
      - '.github/triggers/regression_v168.txt'

permissions:
  contents: write

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install runtime imports
        run: pip install requests pandas websockets
      - name: Run embedded regression helpers only
        run: python .github/tools/run_v168_regressions.py
      - name: Commit regression report
        run: |
          git config user.name 'chatgpt-v168-regression'
          git config user.email 'chatgpt-v168-regression@users.noreply.github.com'
          git add reports/regression/2026-09-01_v1.6.8_regression.txt
          if git diff --cached --quiet; then
            echo 'No report changes.'
          else
            git commit -m 'Run embedded v1.6.8 regression helpers'
            git push
          fi
YAML

# ---- project index files -------------------------------------------------------
cat > CURRENT.md <<'MD'
# CURRENT PROJECT STATE

## Current validated base
- Version: **v1.6.7 startmsg_fix**
- Path: `code/releases/v1.6.7/013_260830_v1.6.7_startmsg_fix.ipynb`

## v1.6.8 status
- GitHub-built candidate: `code/releases/v1.6.8/014_260901_v1.6.8.ipynb`
- Independent new-chat candidate: `code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb`
- Status: **final review / supplementation pending**
- Next work:
  1. resolve the legacy live-order safety regression difference,
  2. place `PROJECT CONTINUITY PRINCIPLE` at the top of the final continuity cell,
  3. strengthen v1.6.8 regression coverage,
  4. revalidate before declaring v1.6.8 the current validated release.

## Latest handoff
- `handoff/2026-09-01/v1.6.7_to_v1.6.8_인수인계서_최종.md`

## Data convention
Daily scanner/live CSV files go under:

`data/YYYY-MM-DD/vX.Y.Z/`

Example:

`data/2026-09-02/v1.6.8/`
MD

cat > README.md <<'MD'
# danta — 주식 단타 자동매매 프로젝트

이 저장소는 **코드 원본·검증 후보·인수인계·자동검증 보고서·장별 CSV 결과**를 분리해서 관리합니다.

## 폴더 구조

- `CURRENT.md` — 현재 검증 기준본과 다음 작업
- `code/releases/` — 버전별 기준/릴리스 코드
- `code/candidates/` — 비교·독립검증용 후보 코드
- `handoff/` — 날짜별 인수인계서
- `reports/build/` — 빌드 검증 보고서
- `reports/comparison/` — 코드 비교 보고서
- `reports/regression/` — 회귀테스트 결과
- `reports/inspection/` — 핵심 구현 점검 보고서
- `data/` — 날짜별 장 결과 CSV
- `.github/` — 자동 빌드/비교/검증 도구와 workflow

## 일일 CSV 업로드 규칙

장 종료 후 그날 생성된 CSV는 아래처럼 날짜와 실행 버전을 묶어 올립니다.

```text
data/
└─ YYYY-MM-DD/
   └─ vX.Y.Z/
      ├─ scanner_signals_*.csv
      ├─ scanner_system_*.csv
      ├─ paper_entry_decisions_*.csv
      ├─ paper_entry_path_*.csv
      ├─ paper_post_exit_*.csv
      ├─ paper_trades_*.csv
      ├─ live_orders_*.csv
      └─ live_trades_*.csv
```

파일이 없는 종류는 억지로 만들 필요가 없습니다.

## 운영 원칙

최신 검증 코드 전체를 보존하고, 필요한 변경점만 최소 수정·통합한 뒤 새 전체본을 생성합니다.
프로젝트 채팅은 설계·결정·리뷰의 본체로 사용하고, GitHub는 실제 코드/데이터 원본의 본체로 사용합니다.
MD

cat > data/README.md <<'MD'
# Daily CSV Data

장 종료 후 CSV를 `data/YYYY-MM-DD/vX.Y.Z/` 아래에 업로드합니다.

예: `data/2026-09-02/v1.6.8/`

가능하면 해당 날짜에 생성된 scanner / paper / live CSV를 한 폴더에 함께 올립니다.
MD

# Final sanity check: expected top-level source files must be gone.
for f in \
  "013_260830_v1.6.7_startmsg_fix.ipynb" \
  "014_260901_v1.6.8.ipynb" \
  "014_260901_v1.6.8.txt" \
  "014_260901_v1.6.8(새채팅).ipynb" \
  "stock_scanner_v1_6_8.py" \
  "v1.6.8_build_report_260901.txt" \
  "v1.6.8_comparison_report_260901.txt" \
  "v1.6.8_regression_run_report_260901.txt" \
  "v1.6.8_critical_implementation_extract_260901.txt"; do
  if [[ -e "$f" ]]; then
    echo "Unexpected root artifact remains: $f" >&2
    exit 1
  fi
done

git add -A
git status --short
