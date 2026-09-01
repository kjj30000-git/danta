# CURRENT PROJECT STATE

## Current validated base
- Version: **v1.6.7 startmsg_fix**
- Path: `code/releases/013_260830_v1.6.7_startmsg_fix.ipynb`

## v1.6.8 status
- GitHub-built candidate: `code/releases/014_260901_v1.6.8.ipynb`
- Independent new-chat candidate: `code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb`
- Status: **final review / supplementation pending**
- Next work:
  1. resolve the legacy live-order safety regression difference,
  2. place `PROJECT CONTINUITY PRINCIPLE` at the top of the final continuity cell,
  3. strengthen v1.6.8 regression coverage,
  4. revalidate before declaring v1.6.8 the current validated release.

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
