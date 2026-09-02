# CURRENT PROJECT STATE

## Current validated release
- Version: **v1.6.9**
- Path: `code/releases/015_260903_v1.6.9.ipynb`
- Intended execution date: **2026-09-03**
- Default live mode: `AUTO_TRADE_ENABLED = False`
- Status: **validated by syntax/static checks and isolated regression helpers**

## Direct base / lineage
- Direct base: `code/releases/014_260902_v1.6.8.ipynb`
- Base SHA-256: `a0ba5fac45dd7180562cefbed1068affc33604f1d5ea8e0eb31fcb114a82b9e1`
- Principle: preserve the latest validated code and apply only the required minimum/local changes.

## v1.6.9 final validation
- 4 code cells / final Continuity cell
- Notebook cell syntax compilation: PASS
- v1.6.8 protected execution functions AST equivalence: PASS
- `test_v166_core_logic`: PASS
- `test_v166_episode_mode_reentry`: PASS
- `test_v166_live_order_safety`: PASS
- `test_v167_order_engine_safety`: PASS
- `test_v168_manual_sell_ledger_helpers`: PASS
- `test_v169_handoff_changes`: PASS
- Actual Kiwoom broker live-order test: **NOT performed**

## Independent review candidate
- `code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb`
- Role: independent comparison / dissenting review only; it does not gate the GitHub release.

## Release convention
- `code/releases/` contains **final/base `.ipynb` notebooks directly**.
- Release filename date is the **intended execution date**.
- Do not create release `.txt` or `.py` copies unless explicitly requested.

## Latest handoff
- `handoff/2026-09-02/v1.6.8_to_v1.6.9_인수인계서_최종.md`

## v1.6.9 integrated changes
- Live amount per stock: **3,000,000 KRW**
- Total live budget safety cap: **18,000,000 KRW**
- Daily max loss: **300,000 KRW**
- Preserve FIRST_75_PASS / 09:05~09:30 / T200_S150 / max 5 stocks / same stock once per day
- BUY latency/slippage instrumentation
- Research-only `WIDE_HIGH_GAP_SHADOW` and `PRE_FAIL_PULLBACK_SHADOW`

## Data convention
Scanner / paper / live CSV files and live-state JSON files go under:

`data/X.Y.Z(YYMMDD[, YYMMDD...])/`

Examples:

- `data/1.6.7(260831, 260901)/`
- `data/1.6.8(260902)/`

Execution-result folders must be stored under `data/`, not at the repository root.
