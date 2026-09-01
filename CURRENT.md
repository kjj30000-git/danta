# CURRENT PROJECT STATE

## Current validated release
- Version: **v1.6.8**
- Path: `code/releases/014_260901_v1.6.8.ipynb`
- Default live mode: `AUTO_TRADE_ENABLED = False`
- Status: **validated by syntax/static checks and isolated regression helpers**

## Direct base / lineage
- Direct base: `code/releases/013_260830_v1.6.7_startmsg_fix.ipynb`
- Base SHA-256: `60afbcdd826607a62a23ddf57637d9bafb395a1a3f1e4fe001efb23289c78972`
- Principle: preserve the latest validated code and apply only the required minimum/local changes.

## v1.6.8 final validation
- 4 code cells / final Continuity cell
- `PROJECT CONTINUITY PRINCIPLE` appears before dated Decision History
- top-level `import tempfile` present for atomic live-state save
- `test_v166_core_logic`: PASS
- `test_v166_live_order_safety`: PASS
- `test_v167_order_engine_safety`: PASS
- `test_v168_manual_sell_ledger_helpers`: PASS
- Build/static validation: PASS
- Actual Kiwoom broker live-order test: **NOT performed**

## Independent review candidate
- `code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb`
- Role: independent comparison / dissenting review only; it does not gate the GitHub release.

## Release convention
- `code/releases/` contains **final/base `.ipynb` notebooks directly**.
- Do not create release `.txt` or `.py` copies unless explicitly requested.

## Latest handoff
- `handoff/2026-09-01/v1.6.7_to_v1.6.8_인수인계서_최종.md`

## Data convention
Daily scanner/live CSV files go under:

`data/YYYY-MM-DD/vX.Y.Z/`

Example:

`data/2026-09-02/v1.6.8/`
