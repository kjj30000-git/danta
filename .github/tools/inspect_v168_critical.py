#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast, json
from pathlib import Path

FILES = [
    ("A_GITHUB", Path("code/releases/014_260902_v1.6.8.ipynb")),
    ("B_NEWCHAT", Path("code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb")),
]
TARGETS = [
    "save_live_state",
    "_normalize_live_position_state",
    "_normalize_external_order_state",
    "_track_external_sell_execution",
    "_consume_external_sell_lots",
    "_apply_external_auto_realized_pnl",
    "_sync_position_from_broker",
    "handle_external_order_event",
    "save_live_trade_result",
    "_submit_live_exit_worker",
    "handle_order_execution",
    "test_v166_live_order_safety",
    "test_v168_manual_sell_ledger_helpers",
    "test_v168_live_ledger_and_timing",
]


def src(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else str(s)


def funcs(text):
    t=ast.parse(text); lines=text.splitlines(keepends=True); out={}
    for n in t.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            out[n.name]="".join(lines[n.lineno-1:n.end_lineno])
    return out


def keylines(text):
    keys=[
        "LIVE_STATE_FILE_LOCK","tmp","tempfile","replace","retry","requested_qty","unfilled_qty",
        "broker_filled_qty","delta_qty","911","external","auto_managed_qty","live_daily_realized_pnl",
        "save_live_trade_result","MANUAL_INTERVENTION_REQUIRED","pending_sell","cancel","broker_precheck",
        "sell_order_time","sell_fill_time","trigger_to_order_sec","order_to_fill_sec","trigger_to_fill_sec",
        "get_broker_positions","get_broker_pending_orders","submit_stock_order","live_entered_today",
        "maybe_open_live_trade","AUTO_TRADE_ENABLED","calls","already","이미 실제진입/주문시도",
    ]
    rows=[]
    for i,line in enumerate(text.splitlines(),1):
        if any(k.lower() in line.lower() for k in keys):
            rows.append(f"{i:04d}: {line}")
    return rows

out=[]
for label,path in FILES:
    nb=json.loads(path.read_text(encoding="utf-8-sig"))
    body=src(nb["cells"][1])
    fm=funcs(body)
    out.append("="*100)
    out.append(f"{label}: {path}")
    out.append("="*100)
    for name in TARGETS:
        if name not in fm:
            continue
        text=fm[name]
        out.append(f"\n### {name} (chars={len(text)})")
        for line in keylines(text):
            out.append(line)

Path("reports/inspection/2026-09-01_v1.6.8_critical_impl.txt").write_text("\n".join(out)+"\n",encoding="utf-8")
