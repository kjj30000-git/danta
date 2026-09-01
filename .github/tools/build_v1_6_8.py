#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v1.6.8 builder — exact startmsg_fix base only

Purpose
-------
This script does NOT reconstruct the trading notebook from an older version.
It accepts only the actual v1.6.7 startmsg_fix notebook and patches the confirmed
v1.6.8 changes in place:

1) manual/external SELL realized-PnL ledger for auto-managed quantity only
2) live_state save race protection (dedicated lock + unique tmp + atomic replace + limited retry)
3) TP/SL trigger -> broker precheck -> SELL order -> fill timing instrumentation
4) exact 4-cell notebook organization with QUICK REFERENCE and final continuity cell

The original v1.6.7 strategy/research/order-engine blocks are preserved unless a
specific patch below explicitly targets them. If any expected marker is missing,
the build fails rather than guessing.

Usage
-----
    python build_v1_6_8_260901_from_startmsg_fix.py \
        013_260830_v1.6.7_startmsg_fix.ipynb

Platform-renamed duplicates such as startmsg_fix(8).ipynb are accepted as long as
content validation proves that the file is the exact startmsg_fix generation.

Outputs
-------
    014_260901_v1.6.8.ipynb
    stock_scanner_v1_6_8.py
    v1.6.8_build_report_260901.txt
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


CONTINUITY_MARKER = "# PROJECT CONTINUITY NOTES / DECISION HISTORY"
BASE_STEM_PREFIX = "013_260830_v1.6.7_startmsg_fix"

OUTPUT_FILE_MAP = {
    "scanner_signals_v167.csv": "scanner_signals_v168.csv",
    "paper_trades_v167.csv": "paper_trades_v168.csv",
    "paper_entry_decisions_v167.csv": "paper_entry_decisions_v168.csv",
    "paper_post_exit_v167.csv": "paper_post_exit_v168.csv",
    "paper_entry_path_v167.csv": "paper_entry_path_v168.csv",
    "scanner_system_v167.csv": "scanner_system_v168.csv",
    "live_trades_v167.csv": "live_trades_v168.csv",
    "live_orders_v167.csv": "live_orders_v168.csv",
    "live_state_v167.json": "live_state_v168.json",
}

RESEARCH_MARKERS = [
    "BASE",
    "PRE_HISTORY",
    "FIRST_75_PASS",
    "LATER_PASS",
    "CONFIRM",
    "LIVE_FILTER_SHADOW",
    "SHADOW_SCORE_70_74",
    "WATCH_SCORE",
    "MIN_SIGNAL_SCORE",
    "ENTRY_PATH",
    "POST_EXIT",
    "169",
]


def cell_source(cell: dict) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return str(src)


def source_lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def make_code_cell(text: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {},
        "outputs": [],
        "source": source_lines(text),
    }


def function_span(source: str, name: str) -> tuple[int, int]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node.lineno, node.end_lineno
    raise ValueError(f"function not found: {name}")


def get_function(source: str, name: str) -> str:
    start, end = function_span(source, name)
    lines = source.splitlines(keepends=True)
    return "".join(lines[start - 1:end])


def replace_function(source: str, name: str, replacement: str) -> str:
    start, end = function_span(source, name)
    lines = source.splitlines(keepends=True)
    repl = replacement.strip("\n") + "\n\n"
    return "".join(lines[: start - 1]) + repl + "".join(lines[end:])


def insert_before_function(source: str, name: str, block: str) -> str:
    start, _ = function_span(source, name)
    lines = source.splitlines(keepends=True)
    return (
        "".join(lines[: start - 1])
        + block.strip("\n")
        + "\n\n"
        + "".join(lines[start - 1 :])
    )


def replace_once(text: str, old: str, new: str, description: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(
            f"patch failed: {description}; expected exactly 1 occurrence, found {count}"
        )
    return text.replace(old, new, 1)


def require(text: str, needle: str, description: str) -> None:
    if needle not in text:
        raise ValueError(f"base validation failed: {description}; missing {needle!r}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


NORMALIZE_POSITION_V168 = r'''
def _normalize_live_position_state(position):
    if not isinstance(position, dict):
        return {}

    legacy_qty = safe_int(position.get("qty", 0))
    auto_qty = safe_int(position.get("auto_managed_qty", legacy_qty))
    position["auto_managed_qty"] = max(0, auto_qty)
    position["qty"] = position["auto_managed_qty"]  # legacy compatibility mirror
    position.setdefault("initial_qty", position["auto_managed_qty"])
    position.setdefault("external_qty", 0)
    position.setdefault("broker_held_qty", "")
    position.setdefault("broker_sellable_qty", "")
    position.setdefault("broker_avg_price", "")
    position.setdefault("broker_updated_at", "")
    position.setdefault("pending_auto_buy_qty", 0)
    position.setdefault("pending_auto_sell_qty", 0)
    position.setdefault("entry_seq", "")
    position.setdefault("exit_trigger_reason", "")
    position.setdefault("exit_trigger_time", "")
    position.setdefault("exit_trigger_price", "")

    # v1.6.8: 외부/수동 SELL은 프로그램 자동주문 원장과 분리하여
    # 주문번호별 requested-unfilled 누적체결량에서 delta만 관리합니다.
    position.setdefault("external_sell_order_progress", {})
    position.setdefault("external_sell_fill_lots", [])

    # v1.6.8: 청산 단계별 지연 계측. 기존 필드는 그대로 보존합니다.
    position.setdefault("broker_precheck_start_time", "")
    position.setdefault("broker_precheck_end_time", "")
    position.setdefault("broker_precheck_sec", "")
    position.setdefault("sell_order_time", position.get("live_exit_order_time", ""))
    position.setdefault("sell_fill_time", position.get("live_exit_fill_time", ""))
    position.setdefault("trigger_to_order_sec", "")
    position.setdefault("order_to_fill_sec", "")
    position.setdefault("trigger_to_fill_sec", "")

    return position
'''


SAVE_LIVE_STATE_V168 = r'''
def save_live_state():
    """
    실제 자동매매 상태를 원자적으로 JSON 저장합니다.

    v1.6.8:
    - LIVE_STATE_FILE_LOCK으로 동일 프로세스 내 동시 save를 직렬화
    - 매 저장마다 고유 tmp 파일 사용
    - os.replace() atomic replace 유지
    - Windows 일시적 파일 점유를 고려해 짧은 제한적 retry
    - 단발성 저장실패만으로 SAFE HALT하지 않음
    """

    if not AUTO_TRADE_ENABLED:
        return

    last_error = None

    # state snapshot 자체는 기존 STATE_LOCK 보호를 그대로 유지합니다.
    with STATE_LOCK:
        state = {
            "trade_date": current_trade_date,
            "live_orders": live_orders,
            "live_positions": live_positions,
            "live_entered_today": live_entered_today,
            "live_processed_fill_ids": live_processed_fill_ids,
            "live_trade_count": live_trade_count,
            "live_daily_realized_pnl": live_daily_realized_pnl,
            "live_trading_halted": live_trading_halted,
            "live_system_halt_reason": live_system_halt_reason,
            "live_recovery_mode": live_recovery_mode,
            "live_blocked_codes": live_blocked_codes,
            "live_execution_issue_codes": live_execution_issue_codes,
            "broker_balances": broker_balances,
            "broker_startup_holdings": broker_startup_holdings,
        }
        safe_state = _json_safe(state)

    with LIVE_STATE_FILE_LOCK:
        for attempt in range(1, LIVE_STATE_SAVE_RETRY_COUNT + 1):
            tmp_file = None
            try:
                base_dir = os.path.dirname(os.path.abspath(LIVE_STATE_FILE)) or "."
                base_name = os.path.basename(LIVE_STATE_FILE)
                fd, tmp_file = tempfile.mkstemp(
                    prefix=f".{base_name}.",
                    suffix=".tmp",
                    dir=base_dir,
                    text=True,
                )
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(safe_state, f, ensure_ascii=False, indent=2)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass

                os.replace(tmp_file, LIVE_STATE_FILE)
                tmp_file = None
                return

            except Exception as e:
                last_error = e
                if tmp_file:
                    try:
                        os.remove(tmp_file)
                    except Exception:
                        pass

                if attempt < LIVE_STATE_SAVE_RETRY_COUNT:
                    time.sleep(LIVE_STATE_SAVE_RETRY_DELAY_SEC)

    log(
        f"[실전상태 저장 오류] {last_error} / "
        f"{LIVE_STATE_SAVE_RETRY_COUNT}회 시도 후 실패"
    )
'''


EXTERNAL_PNL_HELPERS_V168 = r'''
def _elapsed_seconds_v168(start, end):
    if isinstance(start, datetime) and isinstance(end, datetime):
        return max(0.0, round((end - start).total_seconds(), 6))
    return ""


def _track_external_sell_execution(position, values):
    """
    v1.6.8 외부 SELL 누적체결 원장.

    broker_filled_qty = requested_qty - unfilled_qty
    delta_qty = broker_filled_qty - prev_filled_qty

    FID 911은 참고용이며 이벤트마다 단순 누적하지 않습니다.
    """
    if not isinstance(position, dict) or not isinstance(values, dict):
        return {
            "requested_qty": 0,
            "broker_filled_qty": 0,
            "delta_qty": 0,
            "unfilled_qty": 0,
            "fill_price": 0.0,
            "fill_no": "",
            "order_no": "",
            "quantity_known": False,
        }

    _normalize_live_position_state(position)

    order_no = str(values.get("9203", "")).strip()
    fill_no = str(values.get("909", "")).strip()
    requested_from_event = max(0, safe_int(values.get("900", 0)))
    unfilled_qty = max(0, safe_int(values.get("902", 0)))
    fill_price = abs_price(values.get("910", 0))

    progress_map = position.setdefault("external_sell_order_progress", {})
    progress = progress_map.setdefault(order_no, {
        "requested_qty": 0,
        "filled_qty": 0,
        "processed_fill_nos": [],
        "last_unfilled_qty": "",
        "updated_at": "",
    })

    requested_qty = requested_from_event or max(
        0, safe_int(progress.get("requested_qty", 0))
    )
    prev_filled_qty = max(0, safe_int(progress.get("filled_qty", 0)))

    if requested_qty <= 0:
        # 정확한 주문수량이 없는 이벤트에서는 체결량을 추정하지 않습니다.
        progress["last_unfilled_qty"] = unfilled_qty
        progress["updated_at"] = datetime.now()
        return {
            "requested_qty": 0,
            "broker_filled_qty": prev_filled_qty,
            "delta_qty": 0,
            "unfilled_qty": unfilled_qty,
            "fill_price": fill_price,
            "fill_no": fill_no,
            "order_no": order_no,
            "quantity_known": False,
        }

    requested_qty = max(requested_qty, prev_filled_qty)
    progress["requested_qty"] = requested_qty

    raw_broker_filled = requested_qty - unfilled_qty
    broker_filled_qty = min(requested_qty, max(0, raw_broker_filled))

    if broker_filled_qty < prev_filled_qty:
        # stale/out-of-order 이벤트는 재누적하지 않습니다.
        delta_qty = 0
        broker_filled_qty = prev_filled_qty
    else:
        delta_qty = broker_filled_qty - prev_filled_qty

    progress["filled_qty"] = broker_filled_qty
    progress["last_unfilled_qty"] = unfilled_qty
    progress["updated_at"] = datetime.now()

    if fill_no:
        processed = list(progress.get("processed_fill_nos", []))
        if fill_no not in processed:
            processed.append(fill_no)
        progress["processed_fill_nos"] = processed[-100:]

    if delta_qty > 0 and fill_price > 0:
        position.setdefault("external_sell_fill_lots", []).append({
            "order_no": order_no,
            "fill_no": fill_no,
            "qty_total": delta_qty,
            "qty_remaining": delta_qty,
            "price": fill_price,
            "fill_time": datetime.now(),
        })

    return {
        "requested_qty": requested_qty,
        "broker_filled_qty": broker_filled_qty,
        "delta_qty": delta_qty,
        "unfilled_qty": unfilled_qty,
        "fill_price": fill_price,
        "fill_no": fill_no,
        "order_no": order_no,
        "quantity_known": True,
    }


def _consume_external_sell_lots(position, qty):
    """외부 SELL 체결 lot을 시간순으로 qty만큼 소비합니다."""
    qty = max(0, safe_int(qty))
    if qty <= 0 or not isinstance(position, dict):
        return 0, 0.0, None, []

    lots = position.setdefault("external_sell_fill_lots", [])
    need = qty
    used = 0
    amount = 0.0
    last_fill_time = None
    order_nos = []

    for lot in lots:
        if need <= 0:
            break

        remaining = max(0, safe_int(lot.get("qty_remaining", 0)))
        price = safe_float(lot.get("price", 0))
        if remaining <= 0 or price <= 0:
            continue

        take = min(need, remaining)
        lot["qty_remaining"] = remaining - take
        used += take
        amount += price * take
        need -= take

        order_no = str(lot.get("order_no", "")).strip()
        if order_no and order_no not in order_nos:
            order_nos.append(order_no)

        ft = lot.get("fill_time")
        if isinstance(ft, datetime):
            last_fill_time = ft

    position["external_sell_fill_lots"] = [
        lot for lot in lots
        if safe_int(lot.get("qty_remaining", 0)) > 0
    ]

    return used, amount, last_fill_time, order_nos


def _apply_external_auto_realized_pnl(
    position_snapshot,
    exit_qty,
    exit_amount,
    exit_time,
    result,
    external_order_nos=None,
):
    """
    수동매도로 실제 감소한 auto_managed_qty만 gross 실현손익에 반영합니다.
    프로그램 실제 평균체결가(avg_entry_price)를 진입원가로 사용합니다.
    """
    global live_daily_realized_pnl
    global live_trading_halted
    global live_system_halt_reason

    exit_qty = max(0, safe_int(exit_qty))
    exit_amount = safe_float(exit_amount, 0)
    if exit_qty <= 0 or exit_amount <= 0:
        return None

    exit_price = exit_amount / exit_qty
    fill_time = exit_time if isinstance(exit_time, datetime) else datetime.now()
    order_nos = [
        str(x).strip() for x in (external_order_nos or []) if str(x).strip()
    ]
    external_order_no = ",".join(dict.fromkeys(order_nos))

    p = dict(position_snapshot)
    p["exit_filled_qty"] = exit_qty
    p["auto_managed_qty_before_exit"] = exit_qty
    p["external_auto_exit_qty"] = exit_qty
    p["external_exit_price"] = exit_price
    p["external_order_no"] = external_order_no
    p["external_fill_time"] = fill_time
    p["exit_order_no"] = external_order_no
    p["exit_reason"] = result
    p["exit_trigger_reason"] = result

    # 수동매도는 전략 TP/SL trigger가 아니므로 외부 체결시각을 기준으로 기록하되,
    # 자동청산 지연통계와 섞이지 않도록 broker_precheck 계측은 비워둡니다.
    p["exit_trigger_time"] = fill_time
    p["exit_trigger_price"] = exit_price
    p["live_exit_order_time"] = fill_time
    p["sell_order_time"] = fill_time
    p["live_exit_fill_time"] = fill_time
    p["sell_fill_time"] = fill_time
    p["trigger_to_order_sec"] = 0.0
    p["order_to_fill_sec"] = 0.0
    p["trigger_to_fill_sec"] = 0.0

    pnl, ret = save_live_trade_result(p, exit_price, result)

    with STATE_LOCK:
        live_daily_realized_pnl += pnl
        if (
            LIVE_DAILY_MAX_LOSS_WON > 0
            and live_daily_realized_pnl <= -LIVE_DAILY_MAX_LOSS_WON
        ):
            live_trading_halted = True
            live_system_halt_reason = "DAILY_LOSS_LIMIT"

    save_live_order_event({
        "event": "EXTERNAL_REALIZED_PNL",
        "side": "SELL",
        "stock_code": p.get("stock_code", ""),
        "stock_name": p.get("stock_name", ""),
        "order_no": external_order_no,
        "requested_qty": exit_qty,
        "broker_filled_qty": exit_qty,
        "delta_qty": exit_qty,
        "fill_price": exit_price,
        "reason": result,
        "auto_managed_qty": exit_qty,
        "external_auto_exit_qty": exit_qty,
        "external_exit_price": exit_price,
        "external_order_no": external_order_no,
        "external_fill_time": _csv_datetime(fill_time),
    })
    save_live_state()

    return {
        "qty": exit_qty,
        "exit_price": exit_price,
        "pnl": pnl,
        "ret": ret,
        "result": result,
    }
'''


SYNC_POSITION_V168 = r'''
def _sync_position_from_broker(code, balance, source="PERIODIC", external_event=False):
    """broker 총보유를 auto/external 원장에 반영합니다."""

    code = clean_stock_code(code)
    full_external_exit = False
    changed = False
    unresolved_external_auto_qty = 0
    external_realized_payload = None

    pending_buy = bool(_pending_internal_buy_for_code(code))
    pending_sell = bool(_pending_internal_sell_for_code(code))

    # 자동 주문 체결 직후 broker 잔고 반영이 늦을 수 있으므로,
    # 내부 BUY/SELL이 진행 중이거나 AUTO_*_FILL 직후 sync에서는
    # broker 수량을 원장에 덮어쓰지 않고 검증값만 저장합니다.
    defer_quantity_reconcile = (
        pending_buy
        or pending_sell
        or (not external_event and source in ["AUTO_BUY_FILL", "AUTO_SELL_FILL"])
    )

    with STATE_LOCK:
        p = live_positions.get(code)
        if not p:
            return {"exists": False}

        _normalize_live_position_state(p)

        has_external_sell_lots = any(
            safe_int(lot.get("qty_remaining", 0)) > 0
            for lot in p.get("external_sell_fill_lots", [])
            if isinstance(lot, dict)
        )
        external_reconcile = external_event or has_external_sell_lots

        old_auto = safe_int(p.get("auto_managed_qty", 0))
        old_external = safe_int(p.get("external_qty", 0))
        held = safe_int((balance or {}).get("held_qty", 0))
        sellable = (balance or {}).get("sellable_qty", 0 if held == 0 else None)
        broker_avg = (balance or {}).get("avg_price", "")

        p["broker_held_qty"] = held
        p["broker_sellable_qty"] = "" if sellable is None else sellable
        p["broker_avg_price"] = broker_avg
        p["broker_updated_at"] = datetime.now()

        expected = old_auto + old_external
        if held != expected and not defer_quantity_reconcile:
            new_auto, new_external = reconcile_managed_quantities(
                old_auto, old_external, held
            )

            # 감소분 배분은 기존 합의대로 external_qty -> auto_managed_qty 순서.
            external_qty_reduced = max(0, old_external - new_external)
            auto_qty_reduced = max(0, old_auto - new_auto)
            position_snapshot = dict(p)

            if external_reconcile and (external_qty_reduced > 0 or auto_qty_reduced > 0):
                if external_qty_reduced > 0:
                    _consume_external_sell_lots(p, external_qty_reduced)

                if auto_qty_reduced > 0:
                    used_qty, used_amount, used_time, used_order_nos = (
                        _consume_external_sell_lots(p, auto_qty_reduced)
                    )
                    unresolved_external_auto_qty = max(
                        0, auto_qty_reduced - used_qty
                    )

                    if used_qty > 0:
                        external_realized_payload = {
                            "position_snapshot": position_snapshot,
                            "exit_qty": used_qty,
                            "exit_amount": used_amount,
                            "exit_time": used_time,
                            "result": (
                                "EXTERNAL_EXIT"
                                if new_auto == 0
                                else "EXTERNAL_PARTIAL_EXIT"
                            ),
                            "external_order_nos": used_order_nos,
                        }

            p["auto_managed_qty"] = new_auto
            p["qty"] = new_auto
            p["external_qty"] = new_external
            changed = True

            save_live_order_event({
                "event": "BROKER_POSITION_RECONCILED",
                "stock_code": code,
                "stock_name": p.get("stock_name", ""),
                "reason": source,
                "broker_held_qty": held,
                "broker_sellable_qty": "" if sellable is None else sellable,
                "broker_avg_price": broker_avg,
                "auto_managed_qty": new_auto,
                "external_qty": new_external,
            })

            if held == 0 and old_auto > 0 and not pending_sell:
                full_external_exit = True

        p["pending_auto_buy_qty"] = sum(
            max(
                0,
                safe_int(o.get("requested_qty", 0))
                - safe_int(o.get("filled_qty", 0)),
            )
            for o in live_orders.values()
            if clean_stock_code(o.get("stock_code", "")) == code
            and o.get("side") == "BUY"
            and o.get("status") in ["SUBMITTED", "PARTIAL", "CANCEL_PENDING"]
        )
        p["pending_auto_sell_qty"] = sum(
            max(
                0,
                safe_int(o.get("requested_qty", 0))
                - safe_int(o.get("filled_qty", 0)),
            )
            for o in live_orders.values()
            if clean_stock_code(o.get("stock_code", "")) == code
            and o.get("side") == "SELL"
            and o.get("status") in ["SUBMITTED", "PARTIAL", "ORDER_STATUS_UNKNOWN"]
        )

        if external_reconcile and pending_sell:
            p["status"] = "MANUAL_INTERVENTION_REQUIRED"
            live_blocked_codes[code] = {
                "reason": "MANUAL_INTERVENTION_REQUIRED",
                "detail": "자동매도 주문 중 수동개입 감지",
                "time": datetime.now(),
            }
        elif (
            external_reconcile
            and not full_external_exit
            and safe_int(p.get("auto_managed_qty", 0)) > 0
        ):
            p["status"] = "OPEN"
            current_block = live_blocked_codes.get(code, {})
            if current_block.get("reason") == "EXTERNAL_ORDER_DETECTED":
                live_blocked_codes.pop(code, None)

        result = {
            "exists": True,
            "old_auto": old_auto,
            "old_external": old_external,
            "held": held,
            "new_auto": safe_int(p.get("auto_managed_qty", 0)),
            "new_external": safe_int(p.get("external_qty", 0)),
            "sellable": sellable,
            "changed": changed,
            "full_external_exit": full_external_exit,
            "pending_buy": pending_buy,
            "pending_sell": pending_sell,
            "deferred": defer_quantity_reconcile,
            "stock_name": p.get("stock_name", code),
            "entry_seq": p.get("entry_seq", ""),
        }

    # CSV/Telegram I/O는 STATE_LOCK 밖에서 처리합니다.
    realized = None
    if external_realized_payload:
        realized = _apply_external_auto_realized_pnl(**external_realized_payload)

    if unresolved_external_auto_qty > 0:
        with STATE_LOCK:
            live_execution_issue_codes.add(code)
            live_blocked_codes[code] = {
                "reason": "EXTERNAL_PNL_UNRESOLVED",
                "detail": (
                    f"자동관리 감소 {unresolved_external_auto_qty}주 체결가 lot 확인불가"
                ),
                "time": datetime.now(),
            }

        save_live_order_event({
            "event": "EXTERNAL_PNL_UNRESOLVED",
            "side": "SELL",
            "stock_code": code,
            "stock_name": result.get("stock_name", code),
            "reason": source,
            "error": (
                f"수동매도로 자동관리 {unresolved_external_auto_qty}주 감소했으나 "
                "실제 외부 체결가 lot 부족"
            ),
            "auto_managed_qty": result.get("new_auto", 0),
            "external_qty": result.get("new_external", 0),
        })

        send_telegram(
            "🚨 수동매도 손익 확인 필요\n"
            f"{result['stock_name']} ({code})\n"
            f"자동관리 감소 {unresolved_external_auto_qty}주의 실제 외부 체결가를 "
            "원장에서 확인하지 못했습니다.\n"
            "해당 종목 추가 자동주문을 차단하고 계좌/체결내역 확인이 필요합니다."
        )

    if full_external_exit and unresolved_external_auto_qty == 0:
        # 손익을 먼저 기록한 뒤 v1.6.7의 기존 외부청산 확정/포지션 제거 사용.
        _finalize_external_exit(code, source=source)
    else:
        # 불완전 체결가를 임의 추정해 포지션을 조용히 닫지 않습니다.
        save_live_state()

    if realized:
        action_text = "전량" if realized.get("result") == "EXTERNAL_EXIT" else "부분"
        send_telegram(
            "🏁 자동관리 물량 수동청산 손익 반영\n"
            f"{result['stock_name']} ({code})\n"
            f"구분 : {action_text} 수동청산\n"
            f"반영수량 : {realized['qty']}주\n"
            f"외부체결가 : {realized['exit_price']:,.0f}원\n"
            f"수익률(비용전) : {realized['ret']:+.2f}%\n"
            f"손익(비용전) : {realized['pnl']:+,.0f}원\n"
            f"오늘 누적(비용전) : {live_daily_realized_pnl:+,.0f}원"
        )

    return result
'''


HANDLE_EXTERNAL_V168 = r'''
def handle_external_order_event(values):
    """
    프로그램 주문번호가 아닌 사용자/외부 주문.

    - 프로그램과 무관한 다른 종목 개인매매는 자동포지션/손익/진입카운트에 편입하지 않음.
    - 자동관리 종목의 외부 SELL만 requested-unfilled 누적체결 원장에 기록.
    - 자동관리 종목의 외부 BUY는 기존 정책대로 external_qty 동기화 대상으로만 처리.
    """
    if not isinstance(values, dict):
        return

    code = clean_stock_code(values.get("9001", ""))
    ord_no = str(values.get("9203", "")).strip()
    side = _parse_event_side(values)
    status_text = str(values.get("913", ""))

    if not code or not side:
        return

    tracking = {
        "requested_qty": max(0, safe_int(values.get("900", 0))),
        "broker_filled_qty": "",
        "delta_qty": "",
        "unfilled_qty": max(0, safe_int(values.get("902", 0))),
        "fill_price": abs_price(values.get("910", 0)),
        "fill_no": str(values.get("909", "")).strip(),
        "order_no": ord_no,
        "quantity_known": False,
    }

    with STATE_LOCK:
        managed = code in live_positions

        if side == "BUY":
            # 사용자가 직접 산 종목은 실제 자동진입 대상에서 제외하는 기존 정책 유지.
            broker_startup_holdings.add(code)

        if not managed:
            # 다른 개인매매는 live 손익/카운트/포지션에 영향 없음.
            return

        p = live_positions.get(code)
        _normalize_live_position_state(p)
        stock_name = p.get("stock_name", code)

        if side == "SELL":
            tracking = _track_external_sell_execution(p, values)

        p["status"] = "EXTERNAL_ORDER_DETECTED"
        live_blocked_codes[code] = {
            "reason": "EXTERNAL_ORDER_DETECTED",
            "detail": f"외부 {side} 주문 {ord_no}",
            "time": datetime.now(),
        }

    save_live_order_event({
        "event": "EXTERNAL_ORDER_DETECTED",
        "side": side,
        "stock_code": code,
        "stock_name": stock_name,
        "order_no": ord_no,
        "fill_no": tracking.get("fill_no", ""),
        "requested_qty": tracking.get("requested_qty", ""),
        "broker_filled_qty": tracking.get("broker_filled_qty", ""),
        "delta_qty": tracking.get("delta_qty", ""),
        "unfilled_qty": tracking.get("unfilled_qty", ""),
        "fill_price": tracking.get("fill_price", ""),
        "broker_status": status_text,
        "reason": "EXTERNAL_ORDER_DETECTED",
    })

    save_live_state()

    # broker 잔고를 기준으로 external_qty -> auto_managed_qty 순서로 실제 감소분 확정.
    schedule_broker_sync(
        code,
        reason="EXTERNAL_ORDER_DETECTED",
        external_event=True,
    )
'''


QUICK_REFERENCE_CELL = r'''
# ============================================================
# 변수 / 용어 QUICK REFERENCE
# ============================================================
#
# [AUTO_TRADE_ENABLED]
# False = 가상연구만 실행 / 실제 주문 없음
# True  = 기존 가상연구 전체 + FIRST_75_PASS 실제주문 검토
# v1.6.8 전달본 기본값은 반드시 False.
#
# [WATCH_SCORE / MIN_SIGNAL_SCORE]
# WATCH_SCORE=60 : 진입 기준이 아니라 사전 관찰 시작선.
# MIN_SIGNAL_SCORE=75 : 75점 이상이 실제 신호/연구 진입 자격선.
#
# [WATCH Episode]
# 종목이 WATCH_SCORE 이상으로 올라온 뒤 조건에서 이탈하기 전까지의 연속 관찰 구간.
# 조건에서 정상 이탈 후 다시 올라오면 새 Episode가 시작될 수 있음.
# 실제매매는 동일 종목 하루 1회 정책을 별도로 유지.
#
# [BASE]
# 75점 이상 최초 신호를 가장 넓게 보는 기준 연구군.
#
# [PRE_HISTORY]
# 75점 이상 시점에 과거 가격 HISTORY가 충분하고,
# 직전 30초/60초 상승 + 60초 high_gap 감소 조건을 보는 연구군.
#
# [FIRST_75_PASS]
# 해당 WATCH Episode에서 최초 75점 도달 시 PRE_HISTORY까지 PASS한 신호.
# v1.6.8 실제매매는 이 신호만 사용.
#
# [LATER_PASS]
# 최초 75점에서는 PRE_HISTORY를 통과하지 못했지만 이후 정상 스캔에서 통과한 연구군.
# 실제매매에는 사용하지 않음.
#
# [CONFIRM]
# 최초 75점 신호 이후 다음 정상 스캔에서 추가 상승을 확인하는 연구군.
# 실제매매에는 사용하지 않음.
#
# [price_change_30s / price_change_60s]
# 현재 판정시점 가격이 약 30초/60초 전 가격보다 몇 % 변했는지.
# 양수면 해당 기간 가격 상승.
#
# [history_available_sec]
# 현재 종목에 대해 프로그램이 실제 확보한 rolling 가격 HISTORY 길이(초).
# PRE_HISTORY_MIN_SEC보다 짧으면 조건 실패가 아니라 DATA_UNAVAILABLE로 구분.
#
# [day_high / high_gap / high_gap_change_60s]
# day_high = 당일 고가
# high_gap = 당일 고가 대비 현재가의 이격률(%). 작을수록 고점에 가까움.
# high_gap_change_60s = 현재 high_gap - 약 60초 전 high_gap.
# 음수면 최근 60초 동안 고점에 가까워진 방향.
#
# [MAX_HIGH_GAP / LIVE_MAX_HIGH_GAP / 연구 high_gap<=0.25]
# MAX_HIGH_GAP = 스캐너/점수 체계의 넓은 고점이격 기준.
# LIVE_MAX_HIGH_GAP = LIVE_FILTER_SHADOW 연구용 기준이며 실제 FIRST_75_PASS 주문필터 아님.
# high_gap<=0.25 등 더 좁은 값은 사후 연구분석 조건이며 v1.6.8 실제 진입조건으로 구현하지 않음.
#
# [ENTRY_PATH]
# 진입 후 30/60/120/180/300초 가격경로를 독립 추적하는 연구자료.
# price_change_30s/60s는 진입 '전' 방향성이고 ENTRY_PATH는 진입 '후' 경로라는 차이.
#
# [MFE / MAE]
# MFE = 진입 후 가장 유리했던 최대 수익구간.
# MAE = 진입 후 가장 불리했던 최대 손실구간.
#
# [TP / SL / TIME_EXIT / T200_S150]
# TP = Take Profit(익절), SL = Stop Loss(손절), TIME_EXIT = 시간청산.
# T200_S150 = TP +2.00%, SL -1.50%.
#
# [SHADOW / LIVE_FILTER_SHADOW / SHADOW_SCORE_70_74]
# 실제 주문 없이 조건 성능만 비교하는 연구군.
# LIVE_FILTER_SHADOW = 실제 운용시간/고점조건을 재현하는 연구용 Shadow.
# SHADOW_SCORE_70_74 = 75점 직전 70~74점 구간 연구.
#
# [POST_EXIT]
# 기준전략 T200_S150 청산 후 5/10/30분 가격을 추가 추적하는 연구자료.
#
# [v1.6.8 청산 지연 필드]
# exit_trigger_time         = TP/SL/TIME_EXIT가 처음 발생한 시각
# broker_precheck_start_time= SELL 전 broker 보유/매도가능/미체결 조회 시작
# broker_precheck_end_time  = 위 안전조회 종료
# broker_precheck_sec       = broker 사전조회 소요시간
# sell_order_time           = 실제 SELL 주문 REST 응답/주문번호 확인 시각
# sell_fill_time            = SELL 체결 완료 시각
# trigger_to_order_sec      = trigger -> 주문제출 완료
# order_to_fill_sec         = 주문 -> 체결
# trigger_to_fill_sec       = trigger -> 체결 전체
# ============================================================
'''


CONTINUITY_PRINCIPLE = r'''
# ============================================================
# PROJECT CONTINUITY PRINCIPLE
# ============================================================
# 최신 검증 코드 전체를 보존하고 필요한 변경점만 최소 수정/통합한 뒤 전체본 제공.
# 기존 최신 검증 코드를 엎어서 재작성하지 않는다.
#
'''

DECISION_APPEND = r'''
# 2026-08-31 (월)
# - v1.6.8 전체코드는 반드시 013_260830_v1.6.7_startmsg_fix.ipynb를 직접 base로 한다.
# - 013_260831_v1.6.7_manual_pnl_fix.ipynb는 임시 실험본이므로 base로 사용하지 않는다.
# - 실제 진입전략은 FIRST_75_PASS only / MAIN 09:05~09:30 / 종목당 100만원 / 하루 5종목 /
#   동일종목 실제 1회 / T200_S150(+2.00/-1.50)를 유지한다.
# - 가상연구 BASE/PRE_HISTORY/FIRST_75_PASS/LATER_PASS/CONFIRM/LIVE_FILTER_SHADOW/
#   SHADOW_SCORE_70_74, WATCH Episode, ENTRY_PATH, POST_EXIT, 169 TP/SL grid는 유지한다.
#
# 2026-09-01 (화)
# - 비에이치 실전에서 STOP_LOSS trigger 09:28:22.220 -> SELL order 09:28:34.736 ->
#   fill 09:28:34.790, trigger-to-fill 약 12.57초를 확인했다.
# - SELL 전 broker positions + pending/sellable 안전검증은 제거하지 않는다.
#   안전을 유지한 상태에서 trigger/precheck/order/fill 단계별 시간을 계측한다.
# - live_state_v167.json.tmp Permission denied 경쟁 가능성을 확인했다.
#   v1.6.8에서는 전용 lock + 고유 tmp + atomic os.replace + 제한적 retry로 보완하며,
#   단발성 state 저장 실패만으로 SAFE HALT하지 않는다.
# - 수동/외부 SELL 손익은 broker requested_qty-unfilled_qty 누적체결량의 delta만 사용한다.
#   FID 911을 매 이벤트마다 증분처럼 누적하지 않는다.
# - 수동매도로 broker held가 감소하면 external_qty를 먼저 차감하고 그 다음 auto_managed_qty를 차감한다.
#   실제 감소한 auto_managed_qty만 프로그램의 live 실현손익/일손실 한도에 반영한다.
# - 프로그램과 무관한 개인매매는 live 손익/진입카운트에 편입하지 않는다.
# - 자동 SELL 진행 중 수동개입이 감지되어도 사용자 주문을 자동취소하지 않으며,
#   추가 주문을 차단하고 broker 동기화로 상태를 확정해 이중손익을 막는다.
#
# [향후 연구 후보 - v1.6.8 필터/수집 기능 아님]
# - FIRST_75_PASS 발생 건수와 성과가 장초반 시장상태와 관련되는지 향후 검증한다.
# - 후보 시장상태: KOSPI/KOSDAQ 장초반 등락률, 시장 상승확산도, 전체 거래활성도,
#   삼성전자·SK하이닉스 장초반 추세.
# - 위 항목은 v1.6.8 실제진입 필터나 신규 데이터수집 기능으로 구현하지 않는다.
# ============================================================
'''



def patch_settings_and_globals(body: str) -> str:
    body = replace_once(
        body,
        "# 단타 자동 스크리너 v1.6.7\n",
        "# 단타 자동 스크리너 v1.6.8\n",
        "program header version",
    )
    if "\nimport tempfile\n" not in body:
        body = replace_once(body, "import threading\n", "import threading\nimport tempfile\n", "add tempfile import")
    lock_anchor = "LIVE_CSV_LOCK = threading.Lock()\n"
    require(body, lock_anchor, "existing LIVE_CSV_LOCK")
    addition = (
        lock_anchor
        + "\n# v1.6.8 live_state 저장 전용 lock / 제한적 retry\n"
        + "LIVE_STATE_FILE_LOCK = threading.Lock()\n"
        + "LIVE_STATE_SAVE_RETRY_COUNT = 3\n"
        + "LIVE_STATE_SAVE_RETRY_DELAY_SEC = 0.05\n"
    )
    body = body.replace(lock_anchor, addition, 1)
    return body


def patch_live_order_columns(body: str) -> str:
    old = '''    "signal_time", "signal_price", "live_order_time", "entry_seq",\n]'''
    new = '''    "signal_time", "signal_price", "live_order_time", "entry_seq",\n    "broker_precheck_start_time", "broker_precheck_end_time", "broker_precheck_sec",\n    "sell_order_time", "sell_fill_time",\n    "trigger_to_order_sec", "order_to_fill_sec", "trigger_to_fill_sec",\n    "external_auto_exit_qty", "external_exit_price",\n    "external_order_no", "external_fill_time",\n]'''
    return replace_once(body, old, new, "extend LIVE_ORDER_COLUMNS")


def patch_live_trade_result(body: str) -> str:
    fn = get_function(body, "save_live_trade_result")
    old_calc = '''    trigger_time = position.get("exit_trigger_time", "")\n    fill_time = position.get("live_exit_fill_time", datetime.now())\n    trigger_to_fill_sec = ""\n    if isinstance(trigger_time, datetime) and isinstance(fill_time, datetime):\n        trigger_to_fill_sec = max(0.0, (fill_time - trigger_time).total_seconds())\n'''
    new_calc = '''    trigger_time = position.get("exit_trigger_time", "")\n    order_time = position.get("sell_order_time", position.get("live_exit_order_time", ""))\n    fill_time = position.get("sell_fill_time", position.get("live_exit_fill_time", datetime.now()))\n\n    trigger_to_order_sec = position.get("trigger_to_order_sec", "")\n    if trigger_to_order_sec in ["", None]:\n        trigger_to_order_sec = _elapsed_seconds_v168(trigger_time, order_time)\n\n    order_to_fill_sec = position.get("order_to_fill_sec", "")\n    if order_to_fill_sec in ["", None]:\n        order_to_fill_sec = _elapsed_seconds_v168(order_time, fill_time)\n\n    trigger_to_fill_sec = position.get("trigger_to_fill_sec", "")\n    if trigger_to_fill_sec in ["", None]:\n        trigger_to_fill_sec = _elapsed_seconds_v168(trigger_time, fill_time)\n'''
    if old_calc not in fn:
        raise ValueError("save_live_trade_result trigger timing block changed unexpectedly")
    fn = fn.replace(old_calc, new_calc, 1)
    old_key = '''        "sell_order_time": _csv_datetime(position.get("live_exit_order_time", "")),\n'''
    if old_key not in fn:
        raise ValueError("save_live_trade_result sell_order_time row marker not found")
    new_key = '''        "sell_order_time": _csv_datetime(order_time),\n        "broker_precheck_start_time": _csv_datetime(position.get("broker_precheck_start_time", "")),\n        "broker_precheck_end_time": _csv_datetime(position.get("broker_precheck_end_time", "")),\n        "broker_precheck_sec": position.get("broker_precheck_sec", ""),\n        "sell_fill_time": _csv_datetime(fill_time),\n        "trigger_to_order_sec": trigger_to_order_sec,\n        "order_to_fill_sec": order_to_fill_sec,\n'''
    fn = fn.replace(old_key, new_key, 1)
    old_exit_order = '''        "exit_order_no": position.get("exit_order_no", ""),\n'''
    if old_exit_order not in fn:
        raise ValueError("save_live_trade_result exit_order_no marker not found")
    new_exit_order = '''        "exit_order_no": position.get("exit_order_no", ""),\n        "external_auto_exit_qty": position.get("external_auto_exit_qty", ""),\n        "external_exit_price": position.get("external_exit_price", ""),\n        "external_order_no": position.get("external_order_no", ""),\n        "external_fill_time": _csv_datetime(position.get("external_fill_time", "")),\n'''
    fn = fn.replace(old_exit_order, new_exit_order, 1)
    return replace_function(body, "save_live_trade_result", fn)


def patch_exit_worker(body: str) -> str:
    fn = get_function(body, "_submit_live_exit_worker")
    old = '''    try:\n        with BROKER_SYNC_LOCK:\n            positions = get_broker_positions()\n            pending = get_broker_pending_orders()\n            _update_broker_balance_cache(positions)\n'''
    new = '''    broker_precheck_start_time = datetime.now()\n    with STATE_LOCK:\n        p = live_positions.get(code)\n        if p:\n            p["broker_precheck_start_time"] = broker_precheck_start_time\n\n    try:\n        with BROKER_SYNC_LOCK:\n            positions = get_broker_positions()\n            pending = get_broker_pending_orders()\n            _update_broker_balance_cache(positions)\n'''
    if old not in fn:
        raise ValueError("_submit_live_exit_worker broker precheck block changed unexpectedly")
    fn = fn.replace(old, new, 1)
    old = '''    balance = positions.get(code, {\n'''
    new = '''    broker_precheck_end_time = datetime.now()\n    broker_precheck_sec = _elapsed_seconds_v168(\n        broker_precheck_start_time, broker_precheck_end_time\n    )\n    with STATE_LOCK:\n        p = live_positions.get(code)\n        if p:\n            p["broker_precheck_end_time"] = broker_precheck_end_time\n            p["broker_precheck_sec"] = broker_precheck_sec\n    save_live_state()\n\n    balance = positions.get(code, {\n'''
    if old not in fn:
        raise ValueError("_submit_live_exit_worker balance marker not found")
    fn = fn.replace(old, new, 1)
    old = '''        ord_no = str(response.get("ord_no", "")).strip()\n\n        with STATE_LOCK:\n'''
    new = '''        ord_no = str(response.get("ord_no", "")).strip()\n        sell_order_time = datetime.now()\n\n        with STATE_LOCK:\n'''
    if old not in fn:
        raise ValueError("_submit_live_exit_worker order number marker not found")
    fn = fn.replace(old, new, 1)
    old = '''            p["live_exit_order_time"] = datetime.now()\n'''
    new = '''            p["live_exit_order_time"] = sell_order_time\n            p["sell_order_time"] = sell_order_time\n            p["trigger_to_order_sec"] = _elapsed_seconds_v168(\n                p.get("exit_trigger_time", ""), sell_order_time\n            )\n'''
    if old not in fn:
        raise ValueError("_submit_live_exit_worker live_exit_order_time marker not found")
    fn = fn.replace(old, new, 1)
    old = '''                "entry_seq": entry_seq,\n            })\n'''
    new = '''                "entry_seq": entry_seq,\n                "broker_precheck_start_time": broker_precheck_start_time,\n                "broker_precheck_end_time": broker_precheck_end_time,\n                "broker_precheck_sec": broker_precheck_sec,\n                "sell_order_time": sell_order_time,\n                "trigger_to_order_sec": _elapsed_seconds_v168(\n                    p.get("exit_trigger_time", ""), sell_order_time\n                ),\n            })\n'''
    if old not in fn:
        raise ValueError("_submit_live_exit_worker SELL order dict marker not found")
    fn = fn.replace(old, new, 1)
    return replace_function(body, "_submit_live_exit_worker", fn)


def patch_sell_fill_timing(body: str) -> str:
    fn = get_function(body, "handle_order_execution")
    old = '''                p["live_exit_fill_time"] = datetime.now()\n                p["exit_filled_qty"] = broker_filled_qty\n'''
    new = '''                sell_fill_time = datetime.now()\n                p["live_exit_fill_time"] = sell_fill_time\n                p["sell_fill_time"] = sell_fill_time\n                p["order_to_fill_sec"] = _elapsed_seconds_v168(\n                    p.get("sell_order_time", p.get("live_exit_order_time", "")),\n                    sell_fill_time,\n                )\n                p["trigger_to_fill_sec"] = _elapsed_seconds_v168(\n                    p.get("exit_trigger_time", ""), sell_fill_time\n                )\n                p["exit_filled_qty"] = broker_filled_qty\n'''
    if old not in fn:
        raise ValueError("handle_order_execution SELL final fill marker not found")
    fn = fn.replace(old, new, 1)
    return replace_function(body, "handle_order_execution", fn)


def patch_order_event_timing(body: str) -> str:
    fn = get_function(body, "handle_order_execution")
    old = '''        "entry_seq": order.get("entry_seq", ""),\n    })\n\n    if side == "BUY":\n'''
    new = '''        "entry_seq": order.get("entry_seq", ""),\n        "broker_precheck_start_time": _csv_datetime(order.get("broker_precheck_start_time", "")),\n        "broker_precheck_end_time": _csv_datetime(order.get("broker_precheck_end_time", "")),\n        "broker_precheck_sec": order.get("broker_precheck_sec", ""),\n        "sell_order_time": _csv_datetime(order.get("sell_order_time", "")),\n        "trigger_to_order_sec": order.get("trigger_to_order_sec", ""),\n    })\n\n    if side == "BUY":\n'''
    if old not in fn:
        raise ValueError("handle_order_execution FILL event marker not found")
    fn = fn.replace(old, new, 1)
    return replace_function(body, "handle_order_execution", fn)


TEST_V168 = r'''
def test_v168_manual_sell_ledger_helpers():
    """broker 호출 없이 v1.6.8 누적체결/배분/저장경합/청산시간을 검증합니다."""
    global AUTO_TRADE_ENABLED, LIVE_STATE_FILE

    # 1) 외부 SELL requested=50 / cumulative 20 -> 50 -> duplicate 50.
    p = _normalize_live_position_state({
        "stock_code": "999998",
        "stock_name": "v168테스트",
        "qty": 100,
        "auto_managed_qty": 100,
        "external_qty": 20,
        "avg_entry_price": 10000,
    })
    a = _track_external_sell_execution(p, {
        "9203": "EXT001", "909": "F1", "900": "50", "902": "30",
        "910": "10100", "911": "20",
    })
    assert a["broker_filled_qty"] == 20 and a["delta_qty"] == 20
    b = _track_external_sell_execution(p, {
        "9203": "EXT001", "909": "F2", "900": "50", "902": "0",
        "910": "10200", "911": "50",
    })
    assert b["broker_filled_qty"] == 50 and b["delta_qty"] == 30
    c = _track_external_sell_execution(p, {
        "9203": "EXT001", "909": "F2", "900": "50", "902": "0",
        "910": "10200", "911": "50",
    })
    assert c["broker_filled_qty"] == 50 and c["delta_qty"] == 0

    # 주문수량 FID 900이 없는 신규 외부주문은 911로 추정하지 않습니다.
    unknown = _normalize_live_position_state({"qty": 8, "auto_managed_qty": 8})
    u = _track_external_sell_execution(unknown, {
        "9203": "EXT_UNKNOWN", "909": "FU", "900": "0", "902": "0",
        "910": "10000", "911": "8",
    })
    assert u["quantity_known"] is False and u["delta_qty"] == 0

    # 2) 기존 내부 BUY/SELL 누적체결 delta 회귀.
    buy1 = compute_broker_fill_delta(107, 97, 0)
    buy2 = compute_broker_fill_delta(107, 0, buy1[0])
    buy_dup = compute_broker_fill_delta(107, 0, buy2[0])
    assert buy1 == (10, 10)
    assert buy2 == (107, 97)
    assert buy_dup == (107, 0)

    sell1 = compute_broker_fill_delta(71, 25, 0)
    sell2 = compute_broker_fill_delta(71, 0, sell1[0])
    assert sell1 == (46, 46)
    assert sell2 == (71, 25)

    # 3) broker 보유 감소는 external -> auto 순서.
    new_auto, new_external = reconcile_managed_quantities(100, 20, 70)
    assert new_external == 0 and new_auto == 70

    # 위 외부 SELL lot 50주도 20주(external) + 30주(auto) 순서로 정확히 소비됩니다.
    used_ext, amount_ext, _, _ = _consume_external_sell_lots(p, 20)
    used_auto, amount_auto, _, _ = _consume_external_sell_lots(p, 30)
    assert used_ext == 20 and abs(amount_ext - 202000) < 0.001
    assert used_auto == 30 and abs(amount_auto - 306000) < 0.001
    assert not p.get("external_sell_fill_lots")

    # 4) 자동매도 중 수동개입 경로는 기존 자동 SELL 취소가 아니라 추가주문 차단/동기화입니다.
    import inspect
    sync_src = inspect.getsource(_sync_position_from_broker)
    external_src = inspect.getsource(handle_external_order_event)
    assert "pending_sell" in sync_src
    assert "MANUAL_INTERVENTION_REQUIRED" in (sync_src + external_src)
    assert "cancel_stock_order" not in sync_src

    # 5) live_state 동시 저장: 전용 lock + unique tmp + atomic replace 결과가 정상 JSON이어야 합니다.
    old_auto = AUTO_TRADE_ENABLED
    old_state_file = LIVE_STATE_FILE
    try:
        with tempfile.TemporaryDirectory() as td:
            LIVE_STATE_FILE = os.path.join(td, "live_state_v168_test.json")
            AUTO_TRADE_ENABLED = True
            errors = []

            def _writer():
                try:
                    for _ in range(5):
                        save_live_state()
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=_writer) for _ in range(6)]
            for th in threads:
                th.start()
            for th in threads:
                th.join()
            assert not errors
            with open(LIVE_STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert isinstance(saved, dict) and "live_positions" in saved
    finally:
        AUTO_TRADE_ENABLED = old_auto
        LIVE_STATE_FILE = old_state_file

    # 6) 비에이치 실전 사례 기준 청산 단계 시간 산술.
    trigger = datetime(2026, 9, 1, 9, 28, 22, 220000)
    order = datetime(2026, 9, 1, 9, 28, 34, 736000)
    fill = datetime(2026, 9, 1, 9, 28, 34, 790000)
    assert abs(_elapsed_seconds_v168(trigger, order) - 12.516) < 0.001
    assert abs(_elapsed_seconds_v168(order, fill) - 0.054) < 0.001
    assert abs(_elapsed_seconds_v168(trigger, fill) - 12.57) < 0.001

    print("✅ v1.6.8 누적체결/배분/live_state/청산시간 강화 회귀 테스트 통과")
    return True
'''



def patch_v166_safety_test_for_broker_precheck(body):
    """v1.6.6 helper가 v1.6.7의 실제 broker precheck를 호출하지 않도록 test harness만 보정."""
    src = get_function(body, "test_v166_live_order_safety")
    if "global verify_pre_buy_account_clear" not in src:
        src = replace_once(
            src,
            "    global replay_unmatched_order_events\n",
            "    global replay_unmatched_order_events\n    global verify_pre_buy_account_clear\n",
            "v166 safety global broker-precheck mock",
        )
        src = replace_once(
            src,
            '        "replay_unmatched_order_events": replay_unmatched_order_events,\n',
            '        "replay_unmatched_order_events": replay_unmatched_order_events,\n'
            '        "verify_pre_buy_account_clear": verify_pre_buy_account_clear,\n',
            "v166 safety broker-precheck backup",
        )
        src = replace_once(
            src,
            "        replay_unmatched_order_events = lambda order_no: None\n",
            "        replay_unmatched_order_events = lambda order_no: None\n"
            "        verify_pre_buy_account_clear = lambda code, stock_name=\"\": (True, \"TEST_OK\")\n",
            "v166 safety broker-precheck mock",
        )
        src = replace_once(
            src,
            '        replay_unmatched_order_events = backups["replay_unmatched_order_events"]\n',
            '        replay_unmatched_order_events = backups["replay_unmatched_order_events"]\n'
            '        verify_pre_buy_account_clear = backups["verify_pre_buy_account_clear"]\n',
            "v166 safety broker-precheck restore",
        )
    return replace_function(body, "test_v166_live_order_safety", src)


def place_continuity_principle(continuity):
    """영구 원칙을 날짜별 Decision History보다 앞, 마지막 셀 최상단에 둡니다."""
    marker = CONTINUITY_MARKER
    if marker not in continuity:
        raise ValueError("continuity header missing")
    if "PROJECT CONTINUITY PRINCIPLE" in continuity:
        raise ValueError("base continuity unexpectedly already contains principle")

    marker_pos = continuity.index(marker)
    closing_sep = continuity.find("# ============================================================", marker_pos + len(marker))
    if closing_sep < 0:
        raise ValueError("continuity header closing separator missing")
    header_end = continuity.find("\n", closing_sep)
    header_end = len(continuity) if header_end < 0 else header_end + 1

    prefix = continuity[:header_end].rstrip() + "\n#\n"
    history = continuity[header_end:].lstrip("\n")
    return (
        prefix
        + CONTINUITY_PRINCIPLE.strip("\n")
        + "\n#\n# ============================================================\n"
        + "# DECISION HISTORY\n"
        + "# ============================================================\n#\n"
        + history
    )


def validate_base(path: Path, nb: dict) -> tuple[str, str, str, int]:
    name = path.name
    if "manual_pnl_fix" in name:
        raise ValueError("manual_pnl_fix is explicitly forbidden as a v1.6.8 base")
    if not name.startswith(BASE_STEM_PREFIX):
        raise ValueError(f"wrong base filename: {name}; expected prefix {BASE_STEM_PREFIX!r}")
    cells = nb.get("cells", [])
    if not cells:
        raise ValueError("notebook has no cells")
    code_cells = [c for c in cells if c.get("cell_type") == "code"]
    if not code_cells:
        raise ValueError("notebook has no code cells")
    settings = cell_source(code_cells[0])
    body_with_history = "\n\n".join(cell_source(c) for c in code_cells[1:])
    full = settings + "\n\n" + body_with_history
    require(settings, "★ 실제매매 설정 - 실행 전 반드시 확인", "top settings cell")
    if "AUTO_TRADE_ENABLED = False" not in settings and "AUTO_TRADE_ENABLED = True" not in settings:
        raise ValueError("base validation failed: AUTO_TRADE_ENABLED setting missing")
    require(settings, 'LIVE_ENTRY_MODE = "FIRST_75_PASS"', "FIRST-only live entry")
    require(settings, 'LIVE_ENTRY_START = "09:05"', "live start 09:05")
    require(settings, 'LIVE_ENTRY_END   = "09:30"', "live end 09:30")
    require(settings, "LIVE_TRADE_AMOUNT_WON = 1_000_000", "1M per stock")
    require(settings, "LIVE_MAX_STOCKS = 5", "max five stocks")
    require(settings, 'LIVE_STRATEGY = "T200_S150"', "T200_S150 live strategy")
    require(body_with_history, 'STRATEGY_VERSION = "v1.6.7"', "v1.6.7 version")
    require(body_with_history, "def compute_broker_fill_delta", "cumulative fill-delta engine")
    require(body_with_history, "def _normalize_live_position_state", "position normalization")
    require(body_with_history, "def _sync_position_from_broker", "broker reconciliation")
    require(body_with_history, "def handle_external_order_event", "external order handler")
    require(body_with_history, "def _submit_live_exit_worker", "safe broker-precheck exit worker")
    require(body_with_history, "def save_live_state", "live state persistence")
    require(body_with_history, "def test_v167_order_engine_safety", "v1.6.7 regression test")
    require(body_with_history, CONTINUITY_MARKER, "continuity marker")
    require(body_with_history, "live_exit_fill_time", "existing exit timing")
    require(body_with_history, "BROKER_SYNC_LOCK", "broker sync safety lock")
    for marker in RESEARCH_MARKERS:
        require(full, marker, f"research marker {marker}")
    continuity_start = body_with_history.find(CONTINUITY_MARKER)
    if continuity_start < 0:
        raise ValueError("continuity marker not found")
    body = body_with_history[:continuity_start].rstrip() + "\n"
    continuity = body_with_history[continuity_start:].rstrip() + "\n"
    return settings, body, continuity, len(cells)


def transform(nb: dict, path: Path) -> tuple[dict, str]:
    settings, body, continuity, original_cell_count = validate_base(path, nb)
    body = body.replace('STRATEGY_VERSION = "v1.6.7"', 'STRATEGY_VERSION = "v1.6.8"', 1)
    body = body.replace('assert STRATEGY_VERSION == "v1.6.7"', 'assert STRATEGY_VERSION == "v1.6.8"', 1)
    for old, new in OUTPUT_FILE_MAP.items():
        body = body.replace(old, new)
    if "AUTO_TRADE_ENABLED = True" in settings:
        settings = settings.replace("AUTO_TRADE_ENABLED = True", "AUTO_TRADE_ENABLED = False", 1)
    settings = settings.replace(
        "# v1.6.7 1차 실전검증은 PRE_HISTORY + FIRST_75_PASS만 허용",
        "# v1.6.8도 PRE_HISTORY + FIRST_75_PASS만 실제진입 허용",
    )
    body = body.replace(
        'log("v1.6.7 = broker 수량검증 / 수동매매 분리 / 종료 즉시 주문차단")',
        'log("v1.6.8 = v1.6.7 안전장치 유지 / 수동매도 손익·상태저장·청산계측 보완")',
    )
    body = patch_settings_and_globals(body)
    body = patch_v166_safety_test_for_broker_precheck(body)
    body = patch_live_order_columns(body)
    body = replace_function(body, "_normalize_live_position_state", NORMALIZE_POSITION_V168)
    body = replace_function(body, "save_live_state", SAVE_LIVE_STATE_V168)
    body = insert_before_function(body, "_sync_position_from_broker", EXTERNAL_PNL_HELPERS_V168)
    body = replace_function(body, "_sync_position_from_broker", SYNC_POSITION_V168)
    body = replace_function(body, "handle_external_order_event", HANDLE_EXTERNAL_V168)
    body = patch_exit_worker(body)
    body = patch_order_event_timing(body)
    body = patch_sell_fill_timing(body)
    body = patch_live_trade_result(body)
    body = insert_before_function(body, "run_scanner", TEST_V168)
    forbidden = [
        'LIVE_ENTRY_START = "09:00"', 'LIVE_ENTRY_END   = "10:00"',
        'LIVE_ENTRY_END   = "10:30"', "LIVE_TRADE_AMOUNT_WON = 2_000_000",
        'LIVE_ENTRY_MODE = "LATER_PASS"',
    ]
    for bad in forbidden:
        if bad in settings:
            raise ValueError(f"forbidden live strategy change detected: {bad}")
    continuity = place_continuity_principle(continuity)
    continuity = continuity.rstrip() + "\n" + DECISION_APPEND.rstrip() + "\n"
    out = copy.deepcopy(nb)
    out["cells"] = [
        make_code_cell(settings.rstrip() + "\n", "v168-settings"),
        make_code_cell(body.rstrip() + "\n", "v168-program"),
        make_code_cell(QUICK_REFERENCE_CELL.rstrip() + "\n", "v168-quickref"),
        make_code_cell(continuity.rstrip() + "\n", "v168-continuity"),
    ]
    return out, str(original_cell_count)


def validate_output(nb: dict) -> list[str]:
    messages = []
    cells = nb.get("cells", [])
    assert len(cells) == 4, f"expected exactly 4 cells, got {len(cells)}"
    assert all(c.get("cell_type") == "code" for c in cells)
    assert "★ 실제매매 설정 - 실행 전 반드시 확인" in cell_source(cells[0])
    assert "AUTO_TRADE_ENABLED = False" in cell_source(cells[0])
    assert "import requests" not in cell_source(cells[0])
    assert "변수 / 용어 QUICK REFERENCE" in cell_source(cells[2])
    assert CONTINUITY_MARKER in cell_source(cells[3])
    assert CONTINUITY_MARKER not in cell_source(cells[1])
    messages.append("PASS: exact 4-code-cell notebook structure; continuity is final cell")
    for idx, cell in enumerate(cells, start=1):
        compile(cell_source(cell), f"v168_cell_{idx}", "exec")
    messages.append("PASS: all four notebook cells compile independently")
    full = "\n\n".join(cell_source(c) for c in cells)
    assert 'STRATEGY_VERSION = "v1.6.8"' in full
    assert "AUTO_TRADE_ENABLED = False" in full
    assert 'LIVE_ENTRY_MODE = "FIRST_75_PASS"' in full
    assert 'LIVE_ENTRY_START = "09:05"' in full
    assert 'LIVE_ENTRY_END   = "09:30"' in full
    assert "LIVE_TRADE_AMOUNT_WON = 1_000_000" in full
    assert "LIVE_MAX_STOCKS = 5" in full
    assert 'LIVE_STRATEGY = "T200_S150"' in full
    messages.append("PASS: live strategy unchanged; AUTO_TRADE default remains False")
    for marker in RESEARCH_MARKERS:
        assert marker in full, marker
    messages.append("PASS: research-system marker regression preserved")
    assert "\nimport tempfile\n" in cell_source(cells[1]), "top-level tempfile import missing"
    assert "# 단타 자동 스크리너 v1.6.8" in cell_source(cells[1]), "program header version mismatch"
    assert "LIVE_STATE_FILE_LOCK = threading.Lock()" in full
    assert "tempfile.mkstemp" in full
    assert "os.replace(tmp_file, LIVE_STATE_FILE)" in full
    assert "LIVE_STATE_SAVE_RETRY_COUNT = 3" in full
    messages.append("PASS: live_state dedicated lock + unique tmp + atomic replace + limited retry")
    assert "external_sell_order_progress" in full
    assert "external_sell_fill_lots" in full
    assert "requested_qty - unfilled_qty" in full
    assert "EXTERNAL_REALIZED_PNL" in full
    assert "EXTERNAL_PARTIAL_EXIT" in full
    messages.append("PASS: external SELL cumulative-delta/manual realized-PnL ledger present")
    for marker in [
        "broker_precheck_start_time", "broker_precheck_end_time", "broker_precheck_sec",
        "sell_order_time", "sell_fill_time", "trigger_to_order_sec", "order_to_fill_sec",
        "trigger_to_fill_sec",
    ]:
        assert marker in full, marker
    messages.append("PASS: exit trigger -> precheck -> order -> fill timing fields present")
    assert "get_broker_positions()" in full
    assert "get_broker_pending_orders()" in full
    assert "broker_sellable_qty" in full
    assert "BROKER_SYNC_LOCK" in full
    messages.append("PASS: broker sellable/precheck safety path preserved")
    continuity_text = cell_source(cells[3])
    assert "PROJECT CONTINUITY PRINCIPLE" in continuity_text
    assert "# DECISION HISTORY" in continuity_text
    assert "2026-09-01 (화)" in continuity_text
    first_dated = continuity_text.find("# 2026-")
    principle_at = continuity_text.find("# PROJECT CONTINUITY PRINCIPLE")
    assert principle_at >= 0 and first_dated >= 0 and principle_at < first_dated
    assert "verify_pre_buy_account_clear = lambda code" in full
    assert "누적체결/배분/live_state/청산시간 강화 회귀" in full
    messages.append("PASS: continuity principle first + isolated broker-precheck test + strengthened v1.6.8 regression")
    compile(full, "stock_scanner_v1_6_8.py", "exec")
    messages.append("PASS: concatenated .py source compiles")
    return messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path, help="013_260830_v1.6.7_startmsg_fix*.ipynb")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    base = args.base.resolve()
    if not base.exists():
        raise FileNotFoundError(base)
    out_dir = (args.output_dir or base.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    with base.open("r", encoding="utf-8") as f:
        nb = json.load(f)
    output_nb, original_cell_count = transform(nb, base)
    messages = validate_output(output_nb)
    ipynb_path = out_dir / "014_260901_v1.6.8.ipynb"
    txt_path = out_dir / "014_260901_v1.6.8.txt"
    py_path = out_dir / "stock_scanner_v1_6_8.py"
    report_path = out_dir / "v1.6.8_build_report_260901.txt"
    notebook_json = json.dumps(output_nb, ensure_ascii=False, indent=1) + "\n"
    ipynb_path.write_text(notebook_json, encoding="utf-8")
    txt_path.write_text(notebook_json, encoding="utf-8")
    full_py = "\n\n".join(cell_source(c) for c in output_nb["cells"])
    py_path.write_text(full_py, encoding="utf-8")
    compile(py_path.read_text(encoding="utf-8"), str(py_path), "exec")
    report = [
        "v1.6.8 BUILD REPORT — 2026-09-01", "=" * 60,
        f"base: {base}", f"base_sha256: {sha256_file(base)}",
        f"original_notebook_cells: {original_cell_count}",
        f"output_notebook: {ipynb_path}", f"output_text_copy: {txt_path}",
        f"output_python: {py_path}", "",
    ]
    report.extend(messages)
    report.extend([
        "", "Runtime note:", "- Broker/API live execution is NOT performed by this builder.",
        "- The generated notebook includes test_v168_manual_sell_ledger_helpers()",
        "  in addition to the preserved v1.6.7 order-engine regression tests.",
        "- AUTO_TRADE_ENABLED remains False in the generated first cell.",
    ])
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
