#!/usr/bin/env python3
"""v2.3.2 1차 빌드·행동·회귀 검증."""

import ast
import copy
import csv
import json
import os
import socket
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NB = ROOT / "code/releases/029_260929_v2.3.2.ipynb"
PARENT = ROOT / "code/releases/028_260928_v2.3.1.ipynb"


def deny(*args, **kwargs):
    raise AssertionError("external connection")


socket.socket.connect = deny
socket.create_connection = deny
notebook = json.loads(NB.read_text(encoding="utf-8"))
cells = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
checks = []


def check(condition, label):
    assert condition, label
    checks.append(label)


with tempfile.TemporaryDirectory(prefix="v232_first_") as td:
    os.chdir(td)
    Path(".env").write_text(
        "KIWOOM_APP_KEY=x\nKIWOOM_SECRET_KEY=x\nTELEGRAM_BOT_TOKEN=x\nTELEGRAM_PERSONAL_CHAT_ID=x\n",
        encoding="utf-8",
    )
    g = {"__name__": "release_test"}
    for source in cells[:2]:
        exec(compile(source, "release", "exec"), g)

    check(g["validate_v220_config"](), "v2.3.2 config")
    check(g["EXECUTION_MODE"] == "RESEARCH" and not g["AUTO_TRADE_ENABLED"] and not g["USE_MOCK"], "research zero-order defaults")
    check(len(g["EXIT_STRATEGIES"]) == 169 and len(g["PULLBACK_EXIT_STRATEGIES"]) == 63, "169/63 grids")
    check(g["PULLBACK_SNAPSHOT_HORIZONS_MIN"] == [30, 60, 90, 120, 150, 180, 210, 240], "eight snapshots preserved")

    # 실제 원장 생성·헤더 검증.
    g["v220_reset_day"](datetime(2026, 9, 29, 9, 0))
    g["v231_initialize_ledgers"]()
    for path, columns in [
        (g["V232_BALANCE_EVALUATION_FILE"], g["V232_BALANCE_EVALUATION_COLUMNS"]),
        (g["V232_BALANCE_EVENT_FILE"], g["V232_BALANCE_EVENT_COLUMNS"]),
    ]:
        with open(path, encoding="utf-8-sig", newline="") as stream:
            check(next(csv.reader(stream)) == columns, f"ledger header {path}")

    rows = []
    original_write = g["v231_write_ledger"]
    g["v231_write_ledger"] = lambda path, row, columns: (rows.append((path, copy.deepcopy(row))) or True)
    g["v220_checkpoint"] = lambda force=False: True
    g["v220_emit"] = lambda *args, **kwargs: True

    def scenario(code, name, ready_time, horizon, breakout_time, low, high):
        original_min_duration = g["BALANCE_ALERT_MIN_DURATION"]
        if horizon == 90:
            g["BALANCE_ALERT_MIN_DURATION"] = 90
        start = ready_time - timedelta(minutes=horizon)
        stock = {"stock_code": code, "stock_name": name, "score": 80, "current_price": (low + high) / 2,
                 "trading_value_source": "ACTUAL", "actual_trading_value": 1, "estimated_trading_value": 1}
        c = g["v230_create_candidate_state"]({"code": code, "stock": stock, "candidate_start_time": start,
            "sources": {"BASE"}, "parent_trade_ids": [], "candidate_source": "BASE"})
        c["needs_partial_bar"] = False
        g["v220_candidates"][code] = c
        center = (low + high) / 2
        for i in range(horizon):
            minute = start + timedelta(minutes=i)
            if horizon == 90:
                close = low + 500 + (high - low - 500) * i / 59 if i < 60 else high - (high - center) * (i - 59) / 30
            else:
                close = center
            bar = {"minute": minute, "open": close, "high": max(close, high if i % 17 == 0 else close),
                   "low": min(close, low if i % 19 == 0 else close), "close": close, "volume": 100 + i % 3,
                   "tick_count": 5, "valid": True}
            c["history"].append(copy.deepcopy(bar))
            g["v232_evaluate_balance"](c, bar, minute + timedelta(minutes=1))
        ready = [r for p, r in rows if p == g["V232_BALANCE_EVENT_FILE"] and r and r["stock_code"] == code and r["event"] == "BASE_READY"]
        if not ready or datetime.fromisoformat(ready[0]["event_time"]) != ready_time:
            print("READY_DIAGNOSTIC", code, [r["event_time"] for r in ready], g["v232_balance_features"](c["history"], horizon))
        check(ready and datetime.fromisoformat(ready[0]["event_time"]) == ready_time, f"{name} ready exact")
        g["BALANCE_ALERT_MIN_DURATION"] = original_min_duration
        # 준비와 돌파 사이의 평탄한 완료봉.
        minute = ready_time
        while minute < breakout_time - timedelta(minutes=2):
            bar = {"minute": minute, "open": center, "high": center, "low": center, "close": center,
                   "volume": 100, "tick_count": 5, "valid": True}
            c["history"].append(copy.deepcopy(bar));g["v232_evaluate_balance"](c, bar, minute + timedelta(minutes=1));minute += timedelta(minutes=1)
        watch_minute = breakout_time - timedelta(minutes=2)
        watch_close = high * 1.003
        watch = {"minute": watch_minute, "open": center, "high": watch_close, "low": center, "close": watch_close,
                 "volume": 180, "tick_count": 5, "valid": True}
        c["history"].append(copy.deepcopy(watch));g["v232_evaluate_balance"](c, watch, watch_minute + timedelta(minutes=1))
        hold_minute = breakout_time - timedelta(minutes=1)
        hold = {"minute": hold_minute, "open": high, "high": high, "low": high, "close": high,
                "volume": 150, "tick_count": 5, "valid": True}
        c["history"].append(copy.deepcopy(hold));g["v232_evaluate_balance"](c, hold, breakout_time)
        events = [r for p, r in rows if p == g["V232_BALANCE_EVENT_FILE"] and r and r["stock_code"] == code and r["event"] == "BASE_BREAKOUT"]
        if not events or datetime.fromisoformat(events[0]["event_time"]) != breakout_time:
            print("BREAKOUT_DIAGNOSTIC", code, [r["event_time"] for r in events], c.get("balance_box"), c.get("balance_breakout_watch"))
        check(events and datetime.fromisoformat(events[0]["event_time"]) == breakout_time, f"{name} breakout exact")
        check(any(k[1] == g["V232_BALANCE_MODE"] for k in c["pending"]), f"{name} balance pending")
        g["v220_fill_pending"](c, high, breakout_time + timedelta(seconds=1))
        balance_trades = [tid for key, tid in c["entered"].items() if isinstance(key, tuple) and key[1] == g["V232_BALANCE_MODE"]]
        check(balance_trades and len(g["paper_positions"][balance_trades[0]]["strategies"]) == 63, f"{name} balance 63-grid fill")
        return c

    g["v220_reset_day"](datetime(2026, 9, 28, 9, 0))
    oci = scenario("010060", "OCI홀딩스", datetime(2026, 9, 28, 11, 57), 90, datetime(2026, 9, 28, 12, 27), 226000, 229000)
    korea = scenario("007810", "코리아써키트", datetime(2026, 9, 28, 13, 1), 60, datetime(2026, 9, 28, 13, 28), 14000, 14120)
    immune = scenario("424870", "이뮨온시아", datetime(2026, 9, 28, 14, 21), 60, datetime(2026, 9, 28, 14, 43), 10000, 10100)

    feature = g["v232_balance_features"](oci["history"], 60)
    check(feature["volume_contraction_ratio"] is not None and feature["breakout_volume_ratio"] is not None, "volume ratios populated")
    check("range_compression_unavailable_reason" in feature, "feature unavailable reason explicit")

    # 전략별/시간축별 말풍선과 영속 중복키.
    cutoff = datetime(2026, 9, 28, 15, 30)
    messages = g["v220_summary_text"](cutoff)
    check(len(messages) == 12, "3 strategy + 8 snapshot + balance bubbles")
    check([x[0] for x in messages[:3]] == ["BASE", "FIRST_75_PASS", "PULLBACK_STRUCTURE_ENTRY"], "summary strategy order")
    check([x[0] for x in messages[3:11]] == [f"SNAPSHOT_{h}" for h in g["PULLBACK_SNAPSHOT_HORIZONS_MIN"]], "snapshot ascending order")
    balance_text = messages[-1][1]
    check(balance_text.startswith("[장기 보합 돌파]") and "90분 보합완성" in balance_text and "보합돌파" in balance_text, "Korean balance bubble")
    g["v220_outbox"].clear();g["v220_schedule_summaries"](cutoff)
    check(len(g["v220_outbox"]) == 13 * 12, "13 cutoffs split into 12 bubbles")
    before = len(g["v220_outbox"]);g["v220_schedule_summaries"](cutoff + timedelta(seconds=30))
    check(len(g["v220_outbox"]) == before, "summary restart/loop duplicate suppression")

    # 부분봉·gap과 15:10 신규진입 경계.
    c = korea;c["balance_box"] = {"box_id": "x", "base_high": 100, "base_low": 99, "duration_min": 60, "breakout_done": False}
    invalid = {"minute": datetime(2026, 9, 28, 14, 0), "open": 100, "high": 100, "low": 100, "close": 100,
               "volume": 1, "tick_count": 1, "valid": False, "invalid_reason": "SEQUENCE_GAP"}
    g["v232_evaluate_balance"](c, invalid, invalid["minute"] + timedelta(minutes=1))
    check(c["balance_box"] is None, "gap invalidates balance box")
    check(not any("kt1000" in source for source in cells[2:3]), "independent pnl cell has no order API")
    g["v231_write_ledger"] = original_write

parent_source = "".join("".join(c["source"]) for c in json.loads(PARENT.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code")
child_source = "".join(cells)
parent_defs = {x.name: x for x in ast.parse(parent_source).body if isinstance(x, (ast.FunctionDef, ast.ClassDef))}
child_defs = {x.name: x for x in ast.parse(child_source).body if isinstance(x, (ast.FunctionDef, ast.ClassDef))}
check(set(parent_defs) <= set(child_defs), "all parent top-level definitions preserved")
broker_keys = [k for k in parent_defs if any(t in k for t in ("broker", "submit_live", "submit_stock", "exit_worker", "safe_rest", "live_order", "live_position")) and not k.startswith("run_")]
check(all(ast.dump(parent_defs[k], include_attributes=False) == ast.dump(child_defs[k], include_attributes=False) for k in broker_keys), "order/broker functions unchanged")

print(json.dumps({"status": "PASS", "checks": checks, "check_count": len(checks),
                  "parent_definitions": len(parent_defs), "order_broker_definitions": len(broker_keys),
                  "external_connections": 0, "broker_orders": 0}, ensure_ascii=False, indent=2))
