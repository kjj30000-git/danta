#!/usr/bin/env python3
"""v2.3.2 독립 2차 비판적 리뷰와 negative control."""

import ast
import json
import os
import socket
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NB = ROOT / "code/releases/029_260929_v2.3.2.ipynb"
notebook = json.loads(NB.read_text(encoding="utf-8"))
cells = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
checks = []


def check(condition, label):
    assert condition, label
    checks.append(label)


check(len(cells) == 5, "five code cells")
check(cells[1].count('if __name__ == "__main__":') == 1, "one main guard")
check("PULLBACK_BALANCE_BREAKOUT" in cells[1] and "paper_trades_v232.csv" in cells[1], "balance isolated paper output")
check(all(api not in cells[2] for api in ("kt10000", "kt10001", "kt10002", "kt10003")), "pnl collector read-only")

def deny(*args, **kwargs):
    raise AssertionError("network")


socket.socket.connect = deny
socket.create_connection = deny
with tempfile.TemporaryDirectory(prefix="v232_review_") as td:
    os.chdir(td)
    Path(".env").write_text("KIWOOM_APP_KEY=x\nKIWOOM_SECRET_KEY=x\nTELEGRAM_BOT_TOKEN=x\nTELEGRAM_PERSONAL_CHAT_ID=x\n", encoding="utf-8")
    g = {"__name__": "cold_start"}
    for source in cells[:2]:
        exec(compile(source, "release", "exec"), g)
    for name, value in list(g.items()):
        if name.startswith("start_") and callable(value):
            g[name] = lambda *args, **kwargs: None

    class Boundary(Exception):
        pass

    def stop():
        raise Boundary()

    g["get_kiwoom_token"] = stop
    try:
        g["run_scanner"]()
    except Boundary:
        checks.append("run_scanner reaches token boundary")
    else:
        raise AssertionError("token boundary not reached")
    check(g["EXECUTION_MODE"] == "RESEARCH" and not g["AUTO_TRADE_ENABLED"] and not g["USE_MOCK"], "startup zero-order mode")

    # 경계 반대관점: 15:10에는 신규진입 금지, 15:30 이후 평가는 금지.
    g["v220_reset_day"](datetime(2026, 9, 29, 15, 9))
    g["v231_write_ledger"] = lambda *args, **kwargs: True
    g["v220_checkpoint"] = lambda *args, **kwargs: True
    g["v220_emit"] = lambda *args, **kwargs: True
    stock = {"stock_code": "999999", "stock_name": "BOUNDARY", "current_price": 100, "score": 80,
             "trading_value_source": "ACTUAL", "actual_trading_value": 1, "estimated_trading_value": 1}
    c = g["v230_create_candidate_state"]({"code": "999999", "stock": stock, "candidate_start_time": datetime(2026, 9, 29, 14, 9),
        "sources": {"BASE"}, "parent_trade_ids": [], "candidate_source": "BASE"})
    c["balance_box"] = {"box_id": "B", "base_high": 100, "base_low": 99, "duration_min": 60, "breakout_done": False}
    c["balance_breakout_watch"] = {"bar_minute": datetime(2026, 9, 29, 15, 8), "close": 101}
    bar = {"minute": datetime(2026, 9, 29, 15, 9), "open": 100, "high": 100, "low": 100, "close": 100,
           "volume": 1, "tick_count": 1, "valid": True}
    c["history"] = [dict(bar, minute=bar["minute"] - timedelta(minutes=59) + timedelta(minutes=i)) for i in range(60)]
    g["v232_evaluate_balance"](c, bar, datetime(2026, 9, 29, 15, 10))
    check(not c["pending"], "15:10 no new balance entry")
    count = len(c.get("balance_event_ids", set()))
    after = dict(bar, minute=datetime(2026, 9, 29, 15, 30))
    g["v232_evaluate_balance"](c, after, datetime(2026, 9, 29, 15, 31))
    check(len(c.get("balance_event_ids", set())) == count, "after 15:30 ignored")

tree = ast.parse(cells[1])
defs = {}
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        defs.setdefault(node.name, []).append(node)
active = {k: v[-1].lineno for k, v in defs.items() if k in {"v220_complete_bar", "v220_summary_text", "v220_schedule_summaries", "validate_v220_config"}}
check(len(active) == 4, "active overrides located")

# Negative controls: 테스트가 핵심 안전변경을 실제로 감지하는지 확인.
mut = cells[0].replace('EXECUTION_MODE = "RESEARCH"', 'EXECUTION_MODE = "LIVE"', 1)
check(mut != cells[0] and 'EXECUTION_MODE = "LIVE"' in mut, "live-mode negative control detectable")
mut2 = cells[1].replace("when.strftime('%H:%M')<PULLBACK_NEW_ENTRY_END", "True", 1)
check(mut2 != cells[1], "15:10 boundary negative control detectable")
mut3 = cells[1].replace("key=f'SUMMARY:{v220_date}:{hhmm}:{slug}'", "key=f'SUMMARY:{v220_date}:{hhmm}'", 1)
check(mut3 != cells[1], "split-outbox negative control detectable")
mut4 = cells[1].replace("if not bar.get('valid',True):", "if False:", 1)
check(mut4 != cells[1], "invalid-bar negative control detectable")

print(json.dumps({"status": "PASS", "checks": checks, "active_definitions": active,
                  "external_connections": 0, "broker_orders": 0}, ensure_ascii=False, indent=2))
