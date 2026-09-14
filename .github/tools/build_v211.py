#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PARENT_DEFAULT = Path('code/releases/023_260914_v2.1.ipynb')
TARGET_DEFAULT = Path('code/releases/024_260915_v2.1.1.ipynb')
REPORT_DEFAULT = Path('reports/validation/2026-09-14_v2.1.1_validation.md')


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_notebook(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def cell_source(cell: dict) -> str:
    src = cell.get('source', [])
    return ''.join(src) if isinstance(src, list) else str(src)


def set_cell_source(cell: dict, text: str) -> None:
    cell['source'] = text.splitlines(keepends=True)


def require_count(text: str, needle: str, expected: int, label: str) -> None:
    count = text.count(needle)
    if count != expected:
        raise RuntimeError(f'{label}: expected {expected}, found {count}: {needle!r}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require_count(text, old, 1, label)
    return text.replace(old, new, 1)


def patch_settings(source: str) -> str:
    source = source.replace('★ v2.1 연구 운용 핵심 설정', '★ v2.1.1 연구 운용 핵심 설정', 1)
    source = replace_once(
        source,
        'PROGRAM_START = "08:50"\nPROGRAM_END = "15:30"\n',
        'PROGRAM_START = "08:00"\nPROGRAM_END = "20:00"\nOFF_HOURS_VALIDATION_MODE = False\n',
        'Cell1 operating hours',
    )
    return source


def validate_grid_helper_text() -> str:
    return '''\n# 함수 설명: 가상매매에 전달된 TP/SL grid를 포지션 등록 전에 검증합니다.\ndef _validate_selected_exit_strategies(exit_strategies):\n    if not isinstance(exit_strategies, dict):\n        raise TypeError("exit_strategies는 dict여야 합니다.")\n    if not exit_strategies:\n        raise ValueError("exit_strategies는 비어 있을 수 없습니다.")\n\n    for strategy_name, rule in exit_strategies.items():\n        if not isinstance(strategy_name, str) or not strategy_name:\n            raise ValueError("exit_strategies의 전략명은 비어 있지 않은 문자열이어야 합니다.")\n        if not isinstance(rule, dict):\n            raise TypeError(f"{strategy_name}: rule은 dict여야 합니다.")\n        if "tp" not in rule or "sl" not in rule:\n            raise ValueError(f"{strategy_name}: tp/sl이 모두 필요합니다.")\n\n        tp = rule["tp"]\n        sl = rule["sl"]\n        if (\n            isinstance(tp, bool)\n            or isinstance(sl, bool)\n            or not isinstance(tp, (int, float))\n            or not isinstance(sl, (int, float))\n        ):\n            raise TypeError(f"{strategy_name}: tp/sl은 숫자형이어야 합니다.")\n\n    return exit_strategies\n\n'''


def off_hours_validation_text() -> str:
    return r'''
# ============================================================
# v2.1.1 장외 가상시계 replay
# - 실제 시각과 무관하게 시간경계/핵심 연구분기를 검증합니다.
# - token/REST/WebSocket/Telegram/broker 주문을 호출하지 않습니다.
# ============================================================

def run_off_hours_validation():
    if EXECUTION_MODE != "RESEARCH" or AUTO_TRADE_ENABLED or USE_MOCK:
        raise RuntimeError(
            "OFF_HOURS_VALIDATION_MODE는 RESEARCH / 실제·모의주문 OFF에서만 허용됩니다."
        )

    required_times = [
        "08:59:50", "09:00:05", "09:01:00", "09:04:59", "09:05:00",
        "09:15:00", "09:15:01", "14:30:00", "14:50:00", "15:00:00",
        "15:30:00", "15:40:00", "20:00:01",
    ]
    base_date = datetime(2026, 9, 15)
    moments = {
        label: datetime.combine(base_date.date(), datetime.strptime(label, "%H:%M:%S").time())
        for label in required_times
    }

    replay = {}
    for label, moment in moments.items():
        hhmm = moment.strftime("%H:%M")
        hhmmss = moment.strftime("%H:%M:%S")
        replay[label] = {
            "session": get_session_at(moment),
            "program_active": PROGRAM_START <= hhmm < PROGRAM_END,
            "opening_observe": (
                OPENING_LEADER_OBSERVE_START + ":00"
                <= hhmmss
                <= OPENING_LEADER_ENTRY_END + ":59"
            ),
            "opening_entry": (
                OPENING_LEADER_ENTRY_START + ":00"
                <= hhmmss
                <= OPENING_LEADER_ENTRY_END + ":00"
            ),
            "opening_range_sample": hhmmss <= "09:04:59",
            "etf_decision": hhmm in ETF_ENTRY_TIMES,
        }

    assert replay["08:59:50"]["opening_entry"] is False
    assert replay["09:00:05"]["opening_observe"] is True
    assert replay["09:01:00"]["opening_entry"] is True
    assert replay["09:04:59"]["opening_range_sample"] is True
    assert replay["09:05:00"]["opening_range_sample"] is False
    assert replay["09:15:00"]["opening_entry"] is True
    assert replay["09:15:01"]["opening_entry"] is False
    assert replay["14:30:00"]["etf_decision"] is True
    assert replay["14:50:00"]["etf_decision"] is True
    assert replay["15:00:00"]["etf_decision"] is True
    assert replay["15:30:00"]["session"] == "WAIT"
    assert replay["15:40:00"]["session"] == "NXT_AFTER"
    assert replay["20:00:01"]["program_active"] is False

    assert len(_validate_selected_exit_strategies(EXIT_STRATEGIES)) == 169
    assert len(_validate_selected_exit_strategies(NEW_STOCK_EXIT_STRATEGIES)) == 20
    assert len(_validate_selected_exit_strategies(ETF_EXIT_STRATEGIES)) == 16

    invalid_grid_failed = False
    try:
        _validate_selected_exit_strategies({})
    except ValueError:
        invalid_grid_failed = True
    assert invalid_grid_failed

    original_save_entry_decision = globals().get("save_entry_decision")
    captured_decisions = []
    globals()["save_entry_decision"] = (
        lambda stock, entry_mode, decision, reason="", extra=None:
        captured_decisions.append((entry_mode, decision, reason, dict(extra or {})))
    )
    try:
        moment = moments["09:05:00"]
        base_stock = {
            "stock_code": "999991",
            "stock_name": "VALIDATION_DIRECT",
            "market": "KOSPI",
            "current_price": 101.0,
            "change_rate": 7.0,
            "trading_value_source": "ACTUAL",
            "actual_trading_value": OPENING_LEADER_MIN_TRADING_VALUE_WON * 2,
            "price_change_60s": 1.0,
        }
        state = {
            "episode_id": "VALIDATION-OL-1",
            "first_seen_time": datetime(2026, 9, 15, 9, 0, 0),
            "current_rank": 1,
            "best_rank": 1,
            "in_top_n": True,
            "opening_low": 99.0,
            "entered_modes": set(),
        }
        reference = {
            "data_status": "OK",
            "reference_high": 100.0,
            "reference_high_source": "VALIDATION",
            "reference_high_cutoff_time": datetime(2026, 9, 15, 9, 4, 59),
        }
        checks, common_pass = _opening_leader_common_conditions(
            base_stock, state, reference, moment
        )
        assert common_pass and all(checks.values())

        direct_pass, _ = evaluate_opening_leader_direct(
            base_stock, state, reference, moment, {}, checks
        )
        assert direct_pass

        retest_state = dict(state)
        retest_state.update({
            "breakout_seen_at": datetime(2026, 9, 15, 9, 5, 0),
            "breakout_price": 100.2,
            "retest_seen_at": None,
            "reclaim_seen_at": None,
            "pullback_low": 100.0,
        })
        retest_stock = dict(base_stock)
        retest_stock["current_price"] = 100.0
        first_retest, _ = evaluate_opening_leader_retest(
            retest_stock,
            retest_state,
            reference,
            datetime(2026, 9, 15, 9, 5, 10),
            {},
            checks,
        )
        assert first_retest is False and retest_state.get("retest_seen_at") is not None

        retest_stock["current_price"] = 100.1
        retest_pass, _ = evaluate_opening_leader_retest(
            retest_stock,
            retest_state,
            reference,
            datetime(2026, 9, 15, 9, 5, 20),
            {},
            checks,
        )
        assert retest_pass

        rs_pass, _ = evaluate_opening_leader_rs(
            retest_stock, retest_state, True, OPENING_LEADER_RS_MIN_EXCESS_PCT + 0.10, {}, checks
        )
        assert rs_pass

        fail_stock = dict(base_stock)
        fail_stock["change_rate"] = OPENING_LEADER_ENTRY_MIN_CHANGE_PCT - 0.1
        fail_checks, fail_common = _opening_leader_common_conditions(
            fail_stock, state, reference, moment
        )
        assert not fail_common and fail_checks["condition_change_min_pass"] is False

        unavailable_ref = dict(reference)
        unavailable_ref["data_status"] = "DATA_UNAVAILABLE"
        unavailable_checks, unavailable_common = _opening_leader_common_conditions(
            base_stock, state, unavailable_ref, moment
        )
        assert not unavailable_common and unavailable_checks["condition_observation_pass"] is False

        rs_missing, _ = evaluate_opening_leader_rs(
            retest_stock, retest_state, True, None, {}, checks
        )
        assert rs_missing is False
    finally:
        if original_save_entry_decision is not None:
            globals()["save_entry_decision"] = original_save_entry_decision
        else:
            globals().pop("save_entry_decision", None)

    report = {
        "status": "PASS",
        "version": STRATEGY_VERSION,
        "program_hours": f"{PROGRAM_START}~{PROGRAM_END}",
        "grid_sizes": {
            "BASE": len(EXIT_STRATEGIES),
            "NEW_STOCK": len(NEW_STOCK_EXIT_STRATEGIES),
            "ETF": len(ETF_EXIT_STRATEGIES),
        },
        "virtual_times": replay,
        "opening_leader": {
            "DIRECT": "PASS",
            "RETEST": "PASS",
            "RS": "PASS",
            "COMMON_FAIL": "PASS",
            "DATA_UNAVAILABLE": "PASS",
        },
        "external_connections": 0,
        "broker_orders": 0,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return report

'''


def patch_open_paper_trade(source: str) -> str:
    helper = validate_grid_helper_text()
    marker = '# 함수 설명: `open_paper_trade` 관련 처리를 수행합니다.\ndef open_paper_trade('
    require_count(source, marker, 1, 'open_paper_trade marker')
    source = source.replace('# 함수 설명: `open_paper_trade` 관련 처리를 수행합니다.\n', helper + '# 함수 설명: `open_paper_trade` 관련 처리를 수행합니다.\n', 1)

    fn_start = source.index('def open_paper_trade(')
    next_marker = '\n\n\n# 함수 설명: 관련 추적 또는 작업을 시작합니다.\ndef start_wide_snapshot_tracking'
    fn_end = source.index(next_marker, fn_start)
    fn = source[fn_start:fn_end]

    fn = replace_once(
        fn,
        '    entry_meta = entry_meta or {}\n',
        '    selected_exit_strategies = _validate_selected_exit_strategies(\n'
        '        EXIT_STRATEGIES if exit_strategies is None else exit_strategies\n'
        '    )\n\n'
        '    entry_meta = entry_meta or {}\n',
        'selected grid definition',
    )
    fn = replace_once(
        fn,
        '    for name, rule in EXIT_STRATEGIES.items():\n',
        '    for name, rule in selected_exit_strategies.items():\n',
        'selected grid loop',
    )

    source = source[:fn_start] + fn + source[fn_end:]
    return source


def dedupe_build_strategy_result_rule_version(source: str) -> tuple[str, int]:
    start = source.index('def build_strategy_result_row(')
    end = source.index('\ndef save_strategy_results(', start)
    segment = source[start:end]
    line = '        "rule_version": position.get("rule_version", ""),\n'
    count = segment.count(line)
    removed = 0
    if count == 2:
        segment = segment.replace(line, '', 1)
        removed = 1
    elif count > 2:
        raise RuntimeError(f'build_strategy_result_row rule_version count unexpected: {count}')
    source = source[:start] + segment + source[end:]
    return source, removed


def patch_program(source: str) -> tuple[str, dict]:
    changes = {}

    if 'import copy\n' not in source:
        source = replace_once(source, 'import hashlib\n', 'import hashlib\nimport copy\n', 'copy import insertion')
    require_count(source, 'import copy\n', 1, 'copy import exact once')
    changes['copy_import'] = 1

    source = replace_once(source, 'STRATEGY_VERSION = "v2.1"\n', 'STRATEGY_VERSION = "v2.1.1"\n', 'strategy version')
    source = source.replace('assert STRATEGY_VERSION == "v2.1"', 'assert STRATEGY_VERSION == "v2.1.1"')

    duplicate_hours = 'PROGRAM_START = "08:00"\nPROGRAM_END   = "20:00"\n'
    require_count(source, duplicate_hours, 1, 'duplicate operating hours')
    source = source.replace(
        duplicate_hours,
        '# PROGRAM_START / PROGRAM_END는 Cell 1 사용자 설정만 사용합니다.\n',
        1,
    )
    changes['duplicate_hours_removed'] = 1

    source, suffix_count = re.subn(
        r'(_v21)(?=\.(?:csv|json|jsonl|txt)["\'])',
        '_v211',
        source,
    )
    if suffix_count < 5:
        raise RuntimeError(f'output suffix replacements too few: {suffix_count}')
    changes['output_suffix_replacements'] = suffix_count

    source = patch_open_paper_trade(source)
    changes['selected_grid_fix'] = 1

    source, deduped = dedupe_build_strategy_result_rule_version(source)
    changes['rule_version_duplicate_removed'] = deduped

    run_marker = '# ============================================================\n# 실행\n# ============================================================\n\nif __name__ == "__main__":\n    run_scanner()\n'
    require_count(source, run_marker, 1, 'main entry marker')
    source = source.replace(
        run_marker,
        off_hours_validation_text()
        + '# ============================================================\n# 실행\n# ============================================================\n\n'
        + 'if __name__ == "__main__":\n'
        + '    if OFF_HOURS_VALIDATION_MODE:\n'
        + '        run_off_hours_validation()\n'
        + '    else:\n'
        + '        run_scanner()\n',
        1,
    )
    changes['off_hours_replay'] = 1

    return source, changes


def patch_quick_reference(source: str) -> str:
    insertion = '''# [v2.1.1 운영시간 / 장외검증]\n# PROGRAM_START=08:00, PROGRAM_END=20:00은 Cell 1 한 곳에서만 정의합니다.\n# OFF_HOURS_VALIDATION_MODE=True는 RESEARCH 전용이며 외부연결 없이 가상시계 replay만 실행합니다.\n# 기본값은 반드시 False입니다.\n#\n'''
    marker = '# [AUTO_TRADE_ENABLED]\n'
    require_count(source, marker, 1, 'quick reference marker')
    return source.replace(marker, insertion + marker, 1)


def patch_continuity(source: str) -> str:
    note = '''\n# 2026-09-14 (월) — v2.1.1 복구 release\n# - v2.1은 copy import 누락, selected_exit_strategies 미정의/선택 grid 미적용, 운영시간 이중정의로 실행 금지.\n# - v2.1.1은 전략 조건을 변경하지 않고 위 P0 결함만 국소 복구.\n# - BASE 169 / 신규주식 20 / ETF 16 grid를 open_paper_trade 전달값 그대로 추적.\n# - PROGRAM_START/END는 Cell 1 단일 설정원(08:00~20:00). 본체 재정의 금지.\n# - OFF_HOURS_VALIDATION_MODE=False 기본. True일 때 RESEARCH 전용 무외부연결 가상시계 replay 실행.\n# - release 승인 전 compile/pyflakes/cold-start/replay/grid/negative-control/2차 비판적 리뷰를 모두 통과해야 함.\n'''
    if '2026-09-14 (월) — v2.1.1 복구 release' not in source:
        source += note
    return source


def duplicate_constant_dict_keys(source: str) -> list[tuple[str, int]]:
    tree = ast.parse(source)
    duplicates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        seen = {}
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, (str, int, float, bytes)):
                value = key.value
                if value in seen:
                    duplicates.append((str(value), getattr(key, 'lineno', -1)))
                else:
                    seen[value] = getattr(key, 'lineno', -1)
    return duplicates


def count_name_assignments(source: str, name: str) -> int:
    tree = ast.parse(source)
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == name:
                    count += 1
    return count


def run_static_validation(target: Path) -> list[str]:
    nb = load_notebook(target)
    code_cells = [cell_source(c) for c in nb.get('cells', []) if c.get('cell_type') == 'code']
    checks = []
    if len(code_cells) != 4:
        raise RuntimeError(f'expected 4 code cells, found {len(code_cells)}')
    for i, source in enumerate(code_cells, 1):
        compile(source, f'{target}#cell-{i}', 'exec')
    checks.append('4개 code cell 개별 compile PASS')
    combined = '\n\n'.join(code_cells)
    compile(combined, str(target), 'exec')
    checks.append('전체 code cell 결합 compile PASS')

    if combined.count('import copy\n') != 1:
        raise RuntimeError('import copy must appear exactly once')
    if 'selected_exit_strategies = _validate_selected_exit_strategies(' not in combined:
        raise RuntimeError('selected_exit_strategies definition missing')
    if 'for name, rule in selected_exit_strategies.items():' not in combined:
        raise RuntimeError('selected grid loop missing')
    checks.append('copy / selected_exit_strategies 정적 확인 PASS')

    if count_name_assignments(combined, 'PROGRAM_START') != 1 or count_name_assignments(combined, 'PROGRAM_END') != 1:
        raise RuntimeError('PROGRAM_START/END must each have exactly one assignment')
    checks.append('PROGRAM_START/END 단일 설정원 PASS')

    duplicates = duplicate_constant_dict_keys(combined)
    if duplicates:
        raise RuntimeError(f'duplicate constant dict keys remain: {duplicates[:20]}')
    checks.append('정적 duplicate dict key 0건 PASS')

    if 'OFF_HOURS_VALIDATION_MODE = False' not in code_cells[0]:
        raise RuntimeError('OFF_HOURS_VALIDATION_MODE default False missing')
    checks.append('장외검증 기본 OFF PASS')

    return checks


def make_cold_start_script(notebook_path: Path) -> str:
    return f'''\nimport json, os, tempfile, pathlib\nfrom datetime import datetime\n\nrepo = pathlib.Path.cwd()\nwith tempfile.TemporaryDirectory() as td:\n    td = pathlib.Path(td)\n    (td / ".env").write_text(\n        "KIWOOM_APP_KEY=dummy\\nKIWOOM_SECRET_KEY=dummy\\nTELEGRAM_BOT_TOKEN=dummy\\n"\n        "TELEGRAM_PERSONAL_CHAT_ID=\\nTELEGRAM_GROUP_CHAT_ID=\\n",\n        encoding="utf-8",\n    )\n    os.chdir(td)\n    nb = json.loads((repo / {str(notebook_path)!r}).read_text(encoding="utf-8"))\n    cells = ["".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "code"]\n    ns = {{"__name__": "v211_cold_start"}}\n    exec(cells[0], ns)\n    exec(cells[1], ns)\n\n    assert ns["STRATEGY_VERSION"] == "v2.1.1"\n    assert ns["EXECUTION_MODE"] == "RESEARCH"\n    assert ns["AUTO_TRADE_ENABLED"] is False\n    assert ns["USE_MOCK"] is False\n    assert ns["PROGRAM_START"] == "08:00" and ns["PROGRAM_END"] == "20:00"\n    assert ns["OFF_HOURS_VALIDATION_MODE"] is False\n    assert len(ns["EXIT_STRATEGIES"]) == 169\n    assert len(ns["NEW_STOCK_EXIT_STRATEGIES"]) == 20\n    assert len(ns["ETF_EXIT_STRATEGIES"]) == 16\n\n    forbidden = []\n    def bomb(name):\n        def _f(*args, **kwargs):\n            forbidden.append(name)\n            raise AssertionError("external call in off-hours replay: " + name)\n        return _f\n    for name in [\n        "get_kiwoom_token", "kiwoom_post", "send_telegram", "submit_stock_order",\n        "start_websocket_manager", "initialize_live_broker_state_with_retry"\n    ]:\n        if name in ns:\n            ns[name] = bomb(name)\n\n    replay = ns["run_off_hours_validation"]()\n    assert replay["status"] == "PASS"\n    assert replay["external_connections"] == 0\n    assert replay["broker_orders"] == 0\n    assert not forbidden\n\n    ns["PAPER_TRADE_ENABLED"] = True\n    ns["AUTO_PAPER_ENTRY"] = True\n    ns["ONE_ENTRY_PER_STOCK"] = True\n    ns["WEBSOCKET_ENABLED"] = False\n    ns["websocket_manager"] = None\n    ns["HISTORY_LOOKBACKS_SEC"] = []\n    ns["attach_session_decision_metrics"] = lambda stock, scan, when: (True, "OK")\n    ns["attach_pre_first_75_metrics"] = lambda *a, **k: None\n    ns["attach_entry_cost_metrics"] = lambda *a, **k: None\n    ns["start_entry_path_tracking"] = lambda *a, **k: None\n    ns["start_policy_shadow_tracking"] = lambda *a, **k: None\n    ns["start_wide_snapshot_tracking"] = lambda *a, **k: None\n    ns["log"] = lambda *a, **k: None\n    ns["get_session"] = lambda: "MAIN"\n    ns["_current_watch_episode_id"] = lambda code, stock=None: "VALIDATION_EPISODE"\n    ns["paper_entry_key"] = lambda code, mode, episode=None: (code, mode, episode)\n    ns["make_trade_id"] = lambda code, mode, episode=None: f"VALID-{{code}}-{{mode}}-{{episode}}"\n    ns["_commit_paper_reentry_metadata"] = lambda stock, mode, tid, meta: {{\n        "stock_entry_seq_today": 1, "mode_entry_seq_today": 1, "is_reentry": False,\n        "previous_same_mode_result": "", "previous_same_mode_trade_id": ""\n    }}\n\n    def base_stock(code):\n        return {{\n            "stock_code": code, "stock_name": code, "current_price": 10000.0,\n            "score": 80, "trading_value_source": "ACTUAL",\n            "actual_trading_value": 50_000_000_000,\n            "estimated_trading_value": 50_000_000_000,\n            "scan_session": "MAIN", "decision_session": "MAIN",\n            "decision_time": datetime(2026, 9, 15, 9, 5, 0),\n            "score_time": datetime(2026, 9, 15, 9, 5, 0),\n        }}\n\n    cases = [\n        ("999901", "BASE", None, 169),\n        ("999902", "OPENING_LEADER_DIRECT", ns["NEW_STOCK_EXIT_STRATEGIES"], 20),\n        ("999903", "ORB_DIRECT", ns["NEW_STOCK_EXIT_STRATEGIES"], 20),\n        ("999904", "ETF_LONG", ns["ETF_EXIT_STRATEGIES"], 16),\n    ]\n    for code, mode, grid, expected in cases:\n        tid = ns["open_paper_trade"](\n            base_stock(code), mode, exit_strategies=grid,\n            forced_entry_time=datetime(2026, 9, 15, 9, 5, 0),\n            forced_entry_price=10000.0,\n        )\n        assert tid\n        assert len(ns["paper_positions"][tid]["strategies"]) == expected\n\n    before_positions = dict(ns["paper_positions"])\n    before_entered = set(ns["paper_entered_today"])\n    try:\n        ns["open_paper_trade"](base_stock("999905"), "INVALID", exit_strategies={{}})\n    except ValueError:\n        pass\n    else:\n        raise AssertionError("empty grid must fail")\n    assert ns["paper_positions"] == before_positions\n    assert ns["paper_entered_today"] == before_entered\n\nprint("COLD_START_AND_REPLAY_PASS")\n'''


def run_cold_start(target: Path) -> str:
    script = make_cold_start_script(target)
    with tempfile.NamedTemporaryFile('w', suffix='.py', encoding='utf-8', delete=False) as f:
        f.write(script)
        temp_path = Path(f.name)
    try:
        result = subprocess.run(
            [sys.executable, str(temp_path)],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
    finally:
        temp_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(
            'cold-start failed\nSTDOUT:\n' + result.stdout + '\nSTDERR:\n' + result.stderr
        )
    return result.stdout.strip()


def run_negative_controls(target: Path) -> list[str]:
    nb = load_notebook(target)
    results = []

    bad_copy = copy.deepcopy(nb)
    program = next(c for c in bad_copy['cells'] if c.get('id') == 'v169-program')
    src = cell_source(program).replace('import copy\n', '', 1)
    set_cell_source(program, src)
    combined = '\n\n'.join(cell_source(c) for c in bad_copy['cells'] if c.get('cell_type') == 'code')
    names = {n.id for n in ast.walk(ast.parse(combined)) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    imported = set()
    for n in ast.walk(ast.parse(combined)):
        if isinstance(n, ast.Import):
            imported.update(alias.asname or alias.name.split('.')[0] for alias in n.names)
        elif isinstance(n, ast.ImportFrom):
            imported.update(alias.asname or alias.name for alias in n.names)
    if 'copy' not in names or 'copy' in imported:
        raise RuntimeError('negative control copy did not create expected missing import condition')
    results.append('negative-control: import copy 제거 결함 재현 PASS')

    bad_selected = copy.deepcopy(nb)
    program = next(c for c in bad_selected['cells'] if c.get('id') == 'v169-program')
    src = cell_source(program)
    block = (
        '    selected_exit_strategies = _validate_selected_exit_strategies(\n'
        '        EXIT_STRATEGIES if exit_strategies is None else exit_strategies\n'
        '    )\n\n'
    )
    require_count(src, block, 1, 'negative selected block')
    src = src.replace(block, '', 1)
    if 'for name, rule in selected_exit_strategies.items():' not in src:
        raise RuntimeError('negative selected loop unexpectedly absent')
    results.append('negative-control: selected_exit_strategies 정의 제거 결함 재현 PASS')

    return results


def write_report(report_path: Path, parent_sha: str, final_sha: str, changes: dict, checks: list[str], cold: str, negatives: list[str]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '# v2.1.1 작성·검증 보고서',
        '',
        '- 작성일: 2026-09-14 (월)',
        '- 실행 예정일: 2026-09-15 (화)',
        '- 부모: `code/releases/023_260914_v2.1.ipynb`',
        '- 최종: `code/releases/024_260915_v2.1.1.ipynb`',
        '- 전략 조건 변경: **없음**',
        '- 실제·모의 broker 주문 호출: **0건**',
        '',
        '## 해시',
        '',
        f'- 부모 SHA-256: `{parent_sha}`',
        f'- 최종 SHA-256: `{final_sha}`',
        '',
        '## 국소 변경',
        '',
    ]
    for key, value in changes.items():
        lines.append(f'- {key}: {value}')
    lines += ['', '## 1차 검증', '']
    lines += [f'- {x}' for x in checks]
    lines += [f'- cold-start / off-hours replay: `{cold}`']
    lines += [f'- {x}' for x in negatives]
    lines += [
        '', '## 2차 비판적 리뷰', '',
        '- 테스트 namespace가 `copy`를 선행 제공하지 않도록 별도 프로세스 cold-start로 재검증.',
        '- `PROGRAM_START/PROGRAM_END` AST assignment 수를 각각 1개로 강제.',
        '- 선택 grid 검증을 포지션/entered set/tracker/WS 구독보다 먼저 수행하여 invalid grid 원자성 확인.',
        '- OFF_HOURS replay 중 token/REST/WebSocket/Telegram/broker 함수는 bomb stub으로 차단해 호출 0건 확인.',
        '- 09:15:00 허용 / 09:15:01 차단, 09:04:59 opening-range 표본 / 09:05:00 이후 판정 경계 확인.',
        '- BASE 169 / OPENING_LEADER 20 / ORB 20 / ETF 16 strategy 실제 생성 수 확인.',
        '- v2.1의 전략 임계값·점수·OPENING_LEADER/ORB/ETF 조건·주문엔진 로직은 변경하지 않음.',
        '', '## 남은 실시장 위험', '',
        '- 정적·장외 fixture 검증은 실제 09:00 키움 데이터 품질, 네트워크 지연, WebSocket 체결 품질을 재현하지 못함.',
        '- 2026-09-15 장중 첫 실행은 `EXECUTION_MODE="RESEARCH"`, `OFF_HOURS_VALIDATION_MODE=False`로만 진행.',
    ]
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def build(parent: Path, target: Path, report: Path) -> None:
    nb = load_notebook(parent)
    code_cells = [c for c in nb.get('cells', []) if c.get('cell_type') == 'code']
    if len(code_cells) != 4:
        raise RuntimeError(f'parent must have 4 code cells, found {len(code_cells)}')
    ids = [c.get('id') for c in code_cells]
    expected_ids = ['v169-settings', 'v169-program', 'v169-quick-reference']
    for required in expected_ids:
        if required not in ids:
            raise RuntimeError(f'missing expected cell id: {required}')

    parent_sha = sha256_path(parent)

    settings = next(c for c in code_cells if c.get('id') == 'v169-settings')
    program = next(c for c in code_cells if c.get('id') == 'v169-program')
    quick = next(c for c in code_cells if c.get('id') == 'v169-quick-reference')
    continuity = code_cells[-1]

    set_cell_source(settings, patch_settings(cell_source(settings)))
    patched_program, changes = patch_program(cell_source(program))
    set_cell_source(program, patched_program)
    set_cell_source(quick, patch_quick_reference(cell_source(quick)))
    set_cell_source(continuity, patch_continuity(cell_source(continuity)))

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write('\n')

    checks = run_static_validation(target)
    final_sha = sha256_path(target)
    cold = run_cold_start(target)
    negatives = run_negative_controls(target)
    write_report(report, parent_sha, final_sha, changes, checks, cold, negatives)

    print(f'BUILT {target}')
    print(f'PARENT_SHA256={parent_sha}')
    print(f'FINAL_SHA256={final_sha}')
    print(f'REPORT={report}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, default=PARENT_DEFAULT)
    parser.add_argument('--target', type=Path, default=TARGET_DEFAULT)
    parser.add_argument('--report', type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args()
    build(args.parent, args.target, args.report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
