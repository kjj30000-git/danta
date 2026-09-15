#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


PARENT_DEFAULT = Path("code/releases/024_260915_v2.1.1.ipynb")
TARGET_DEFAULT = Path("code/releases/025_260916_v2.1.2.ipynb")


def source(cell: dict) -> str:
    value = cell.get("source", [])
    return "".join(value) if isinstance(value, list) else str(value)


def set_source(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_program(text: str) -> str:
    text = replace_once(
        text,
        'STRATEGY_VERSION = "v2.1.1"',
        'STRATEGY_VERSION = "v2.1.2"',
        "strategy version",
    )
    text = text.replace("_v211.", "_v212.").replace("_v211\"", "_v212\"")
    text = replace_once(
        text,
        'assert STRATEGY_VERSION == "v2.1.1"',
        'assert STRATEGY_VERSION == "v2.1.2"',
        "startup version assertion",
    )

    old_gate = '''    stock["pre_entry_type"] = pre_entry_type

    extra = {
'''
    new_gate = '''    stock["pre_entry_type"] = pre_entry_type

    # v2.1.2: FIRST/LATER 설정을 실제 신규 paper 진입 생성에 각각 연결합니다.
    research_enabled = (
        (pre_entry_type == "FIRST_75_PASS" and FIRST_75_RESEARCH_ENABLED)
        or (pre_entry_type == "LATER_PASS" and LATER_PASS_RESEARCH_ENABLED)
    )
    entry_allowed = ok and research_enabled
    decision_reason = (
        reason
        if (not ok or research_enabled)
        else f"{pre_entry_type}_RESEARCH_DISABLED"
    )

    extra = {
'''
    text = replace_once(text, old_gate, new_gate, "FIRST/LATER research gate")
    text = replace_once(
        text,
        '''        "ENTER" if ok else "SKIP",
        reason,
        extra
''',
        '''        "ENTER" if entry_allowed else "SKIP",
        decision_reason,
        extra
''',
        "PRE_HISTORY decision gate",
    )
    text = replace_once(
        text,
        '''    if not ok:
        return None

    paper_trade_id = open_paper_trade(
''',
        '''    if not entry_allowed:
        return None

    paper_trade_id = open_paper_trade(
''',
        "PRE_HISTORY open gate",
    )

    old_dispatch = '''        # 2) PRE_HISTORY: 전략조건은 그대로, 최초/나중 통과만 구분
        if FIRST_75_RESEARCH_ENABLED:
            maybe_open_pre_history(stock, signal_time)
'''
    new_dispatch = '''        # 2) PRE_HISTORY: 전략조건은 그대로, FIRST/LATER 설정을 독립 적용
        pre_history_trade_id = None
        if FIRST_75_RESEARCH_ENABLED or LATER_PASS_RESEARCH_ENABLED:
            pre_history_trade_id = maybe_open_pre_history(stock, signal_time)
'''
    text = replace_once(text, old_dispatch, new_dispatch, "PRE_HISTORY dispatch")
    text = replace_once(
        text,
        "        maybe_open_calm_first_75(stock)\n",
        "        maybe_open_calm_first_75(stock, pre_history_trade_id)\n",
        "CALM parent dispatch",
    )
    text = replace_once(
        text,
        "def maybe_open_calm_first_75(stock):\n",
        "def maybe_open_calm_first_75(stock, parent_pre_trade_id=None):\n",
        "CALM signature",
    )
    text = replace_once(
        text,
        '''    is_first = isinstance(first_time, datetime) and abs((signal_time-first_time).total_seconds()) < .001
    p30 = stock.get("price_change_30s"); p60 = stock.get("price_change_60s")
''',
        '''    is_first = isinstance(first_time, datetime) and abs((signal_time-first_time).total_seconds()) < .001
    is_confirmed_first = (
        bool(parent_pre_trade_id)
        and stock.get("pre_entry_type") == "FIRST_75_PASS"
        and is_first
    )
    p30 = stock.get("price_change_30s"); p60 = stock.get("price_change_60s")
''',
        "CALM confirmed FIRST parent",
    )
    text = replace_once(
        text,
        "    passed = (is_first and available and CALM_30S_MIN_PCT <= safe_float(p30) <= CALM_30S_MAX_PCT\n",
        "    passed = (is_confirmed_first and available and CALM_30S_MIN_PCT <= safe_float(p30) <= CALM_30S_MAX_PCT\n",
        "CALM pass parent condition",
    )
    text = replace_once(
        text,
        '''    raw = {"condition_first_75": is_first, "condition_history_available": available,
           "condition_30s_pass": available and CALM_30S_MIN_PCT <= safe_float(p30) <= CALM_30S_MAX_PCT,
''',
        '''    raw = {"condition_first_75": is_first,
           "condition_confirmed_first_75_pass": is_confirmed_first,
           "parent_pre_trade_id": parent_pre_trade_id or "",
           "parent_pre_entry_type": stock.get("pre_entry_type", ""),
           "condition_history_available": available,
           "condition_30s_pass": available and CALM_30S_MIN_PCT <= safe_float(p30) <= CALM_30S_MAX_PCT,
''',
        "CALM parent metadata",
    )
    return text


def build(parent: Path, target: Path) -> None:
    notebook = json.loads(parent.read_text(encoding="utf-8"))
    if len(notebook.get("cells", [])) != 4:
        raise RuntimeError("parent notebook must have exactly four cells")

    result = copy.deepcopy(notebook)
    cell0 = source(result["cells"][0]).replace(
        "★ v2.1.1 연구 운용 핵심 설정", "★ v2.1.2 연구 운용 핵심 설정", 1
    )
    cell1 = patch_program(source(result["cells"][1]))
    cell2 = source(result["cells"][2])
    cell3 = source(result["cells"][3])
    continuity = '''

# 2026-09-15 (화) — v2.1.2 FIRST_75 계통 최소복구
# - 부모는 v2.1.1이며 v1.7.1.3은 FIRST/LATER 판정 의미 비교에만 사용.
# - FIRST_75_PASS와 LATER_PASS의 연구 ON/OFF를 신규 paper 진입 생성에 독립 연결.
# - CALM_FIRST_75 / PROTECT는 같은 신호에서 확정·생성된 FIRST_75_PASS의 파생전략으로 제한.
# - OPENING_LEADER·ORB·ETF·주문엔진·운영시간·169/20/16 grid 조건은 변경하지 않음.
# - 기본 EXECUTION_MODE=RESEARCH, OFF_HOURS_VALIDATION_MODE=False, 실제·모의주문 0건 유지.
'''

    set_source(result["cells"][0], cell0)
    set_source(result["cells"][1], cell1)
    set_source(result["cells"][2], cell2)
    set_source(result["cells"][3], cell3.rstrip() + continuity)
    for cell in result["cells"]:
        cell["execution_count"] = None
        cell["outputs"] = []

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, default=PARENT_DEFAULT)
    parser.add_argument("--target", type=Path, default=TARGET_DEFAULT)
    args = parser.parse_args()
    build(args.parent, args.target)
    print(args.target)


if __name__ == "__main__":
    main()
