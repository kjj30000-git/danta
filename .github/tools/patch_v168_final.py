#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final v1.6.8 supplementation patcher.

Edits the reproducible builder only. The normal build workflow then regenerates
014_260901_v1.6.8.ipynb from the exact v1.6.7 startmsg_fix base.

Production trading logic is not changed here. This patch only:
1) isolates the legacy live-order safety helper from the broker precheck,
2) strengthens the offline v1.6.8 regression helper,
3) places PROJECT CONTINUITY PRINCIPLE at the top of the final continuity cell.
"""

from __future__ import annotations

import ast
from pathlib import Path

BUILDER = Path('.github/tools/build_v1_6_8.py')


def assignment_span(source: str, name: str):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.lineno, node.end_lineno, ast.literal_eval(node.value)
    raise ValueError(f'assignment not found: {name}')


def replace_assignment(source: str, name: str, replacement: str) -> str:
    start, end, _ = assignment_span(source, name)
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:start-1]) + replacement.rstrip() + '\n\n' + ''.join(lines[end:])


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f'{label}: expected 1 marker, found {count}')
    return source.replace(old, new, 1)


ENHANCED_TEST = r'''def test_v168_manual_sell_ledger_helpers():
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


BUILDER_HELPERS = r'''
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
'''


def main():
    source = BUILDER.read_text(encoding='utf-8')

    # Idempotency guard.
    if 'def place_continuity_principle(continuity):' in source:
        print('builder already supplemented')
        return

    # Replace the offline helper embedded in generated notebooks.
    source = replace_assignment(
        source,
        'TEST_V168',
        "TEST_V168 = r'''\n" + ENHANCED_TEST.rstrip() + "\n'''",
    )

    # Split old DECISION_APPEND into permanent principle + dated append.
    _, _, decision = assignment_span(source, 'DECISION_APPEND')
    p_marker = '# ============================================================\n# PROJECT CONTINUITY PRINCIPLE\n# ============================================================'
    h_marker = '# 2026-08-31 (월)'
    p_start = decision.find(p_marker)
    h_start = decision.find(h_marker)
    if p_start < 0 or h_start < 0 or h_start <= p_start:
        raise ValueError('could not split continuity principle/history')
    principle = decision[p_start:h_start].rstrip()
    history = decision[h_start:].rstrip()
    replacement = (
        "CONTINUITY_PRINCIPLE = r'''\n" + principle + "\n'''\n\n"
        "DECISION_APPEND = r'''\n" + history + "\n'''"
    )
    source = replace_assignment(source, 'DECISION_APPEND', replacement)

    # Add builder helper functions before validate_base.
    marker = '\ndef validate_base(path: Path, nb: dict)'
    source = replace_once(
        source,
        marker,
        '\n' + BUILDER_HELPERS.strip('\n') + '\n\n\ndef validate_base(path: Path, nb: dict)',
        'insert final supplementation helpers',
    )

    # Apply test-harness patch during build.
    source = replace_once(
        source,
        '    body = patch_settings_and_globals(body)\n',
        '    body = patch_settings_and_globals(body)\n    body = patch_v166_safety_test_for_broker_precheck(body)\n',
        'call v166 safety test patch',
    )

    # Place principle before dated history, then append 8/31+ dates.
    old_cont = '    continuity = continuity.rstrip() + "\\n" + DECISION_APPEND.rstrip() + "\\n"\n'
    new_cont = (
        '    continuity = place_continuity_principle(continuity)\n'
        '    continuity = continuity.rstrip() + "\\n" + DECISION_APPEND.rstrip() + "\\n"\n'
    )
    source = replace_once(source, old_cont, new_cont, 'continuity principle placement')

    # Strengthen static builder validation: principle must precede dated history and test mock must exist.
    old_val = (
        '    assert "PROJECT CONTINUITY PRINCIPLE" in cell_source(cells[3])\n'
        '    assert "2026-09-01 (화)" in cell_source(cells[3])\n'
        '    messages.append("PASS: continuity principle + 2026-09-01 decision history appended")\n'
    )
    new_val = (
        '    continuity_text = cell_source(cells[3])\n'
        '    assert "PROJECT CONTINUITY PRINCIPLE" in continuity_text\n'
        '    assert "# DECISION HISTORY" in continuity_text\n'
        '    assert "2026-09-01 (화)" in continuity_text\n'
        '    first_dated = continuity_text.find("# 2026-")\n'
        '    principle_at = continuity_text.find("# PROJECT CONTINUITY PRINCIPLE")\n'
        '    assert principle_at >= 0 and first_dated >= 0 and principle_at < first_dated\n'
        '    assert "verify_pre_buy_account_clear = lambda code" in full\n'
        '    assert "누적체결/배분/live_state/청산시간 강화 회귀" in full\n'
        '    messages.append("PASS: continuity principle first + isolated broker-precheck test + strengthened v1.6.8 regression")\n'
    )
    source = replace_once(source, old_val, new_val, 'strengthen final validation')

    # Compile patched builder before replacing it.
    compile(source, str(BUILDER), 'exec')
    BUILDER.write_text(source, encoding='utf-8')
    print('patched builder for final v1.6.8 supplementation')


if __name__ == '__main__':
    main()
