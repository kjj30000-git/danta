from __future__ import annotations

import ast
import json
import re
import sys
from datetime import datetime, time as dt_time
from pathlib import Path

EXPECTED_NAME = "016_260904_v1.6.10.ipynb"


def _replace_first_top_level_function(src: str, name: str, replacement: str) -> str:
    pattern = rf"(?ms)^def {re.escape(name)}\([^\n]*\):\n.*?(?=^def |\Z)"
    matches = list(re.finditer(pattern, src))
    if not matches:
        raise RuntimeError(f"function not found: {name}")
    m = matches[0]
    return src[: m.start()] + replacement.rstrip() + "\n\n" + src[m.end() :]


def _cleanup_legacy_exact_locks(program: str) -> str:
    program = _replace_first_top_level_function(
        program,
        "validate_live_trading_config",
        '''def _validate_live_trading_config_v169_parent_snapshot_removed():
    """v1.6.9 exact-value 잠금은 v1.6.10에서 제거되었습니다."""
    return True''',
    )
    program = _replace_first_top_level_function(
        program,
        "test_v169_enhancements",
        '''def test_v169_enhancements():
    """호환 이름. v1.6.10 일반화 회귀검증으로 연결합니다."""
    return test_v1610_enhancements()''',
    )
    return program


def _static_validate(nb: dict) -> tuple[str, str]:
    cells = nb.get("cells", [])
    assert len(cells) == 4, f"expected 4 cells, got {len(cells)}"
    assert [c.get("id") for c in cells] == [
        "v1610-settings",
        "v1610-program",
        "v1610-quick-reference",
        "v1610-continuity",
    ]

    for i, cell in enumerate(cells):
        if cell.get("cell_type") == "code":
            compile("".join(cell.get("source", [])), f"cell-{i + 1}", "exec")
        assert cell.get("execution_count") is None
        assert cell.get("outputs") == []

    settings = "".join(cells[0]["source"])
    program = "".join(cells[1]["source"])
    quick = "".join(cells[2]["source"])
    continuity = "".join(cells[3]["source"])
    combined = settings + program + quick + continuity

    first_values = [
        "AUTO_TRADE_ENABLED = False",
        "LIVE_PROFIT_PROTECT_ENABLED = True",
        "LIVE_TRADE_AMOUNT_WON = 1_000_000",
        "LIVE_MAX_STOCKS = 5",
        "LIVE_TOTAL_BUDGET_WON = 6_000_000",
    ]
    positions = [settings.index(x) for x in first_values]
    assert positions == sorted(positions)

    required = first_values + [
        'STRATEGY_VERSION = "v1.6.10"',
        'POST_EXIT_REFERENCE_STRATEGY = "T250_S150"',
        'LIVE_POLICY_RESEARCH_FILE = "paper_policy_research_v1610.csv"',
        'LIVE_PAPER_COMPARISON_FILE = "live_paper_comparison_v1610.csv"',
        'LIVE_PERFORMANCE_FILE = "live_performance_v1610.csv"',
        'POLICY_FOLLOWUP_STATE_FILE = "policy_followup_state_v1610.json"',
        "PROFIT_PROTECT",
        "NOON_RECOVERY",
        "STARTUP_CONNECTIVITY_WAIT",
        "compute_broker_fill_delta",
        "request_entry_cancel_for_exit",
        "WIDE_HIGH_GAP_SHADOW_ENABLED",
        "PRE_FAIL_PULLBACK_SHADOW_ENABLED",
        "def test_v1610_enhancements():",
        "def is_live_entry_time_allowed",
        "def save_policy_followup_state",
        "def load_policy_followup_state",
        "def _append_live_paper_comparison",
        "def show_strategy_performance",
    ]
    for token in required:
        assert token in combined, token

    for token in [
        "scanner_signals_v1610.csv",
        "paper_trades_v1610.csv",
        "paper_entry_decisions_v1610.csv",
        "paper_post_exit_v1610.csv",
        "paper_entry_path_v1610.csv",
        "scanner_system_v1610.csv",
        "live_trades_v1610.csv",
        "live_orders_v1610.csv",
        "live_state_v1610.json",
    ]:
        assert token in program, token

    forbidden = [
        "LIVE_ENTRY_START <= now_hhmm <= LIVE_ENTRY_END",
        "if LIVE_TRADE_AMOUNT_WON != 3_000_000:",
        "if LIVE_TOTAL_BUDGET_WON != 18_000_000:",
        "if LIVE_MAX_STOCKS != 5:",
        "assert LIVE_TRADE_AMOUNT_WON == 3_000_000",
        "assert LIVE_TOTAL_BUDGET_WON == 18_000_000",
        "assert LIVE_DAILY_MAX_LOSS_WON == 300_000",
        'assert LIVE_STRATEGY == "T200_S150"',
    ]
    for token in forbidden:
        assert token not in program, token

    # Safety engine / research preservation markers from v1.6.9.
    preserved = [
        "compute_broker_fill_delta",
        "reconcile_managed_quantities",
        "get_broker_pending_orders",
        "get_broker_positions",
        "request_entry_cancel_for_exit",
        "pending_auto_sell_qty",
        "auto_managed_qty",
        "external_qty",
        "save_live_state",
        "LIVE_STATE_SAVE_LOCK",
        "WIDE_HIGH_GAP_SHADOW_ENABLED",
        "PRE_FAIL_PULLBACK_SHADOW_ENABLED",
        "PAPER_TP_LEVELS",
        "PAPER_SL_LEVELS",
        "EXIT_STRATEGIES",
    ]
    for token in preserved:
        assert token in program, token

    assert "v1.6.9" in continuity
    assert "09:30:00 미만" in quick
    assert "T250_S150" in quick
    return settings, program


def _behavioral_validate(settings: str, program: str) -> None:
    ns = {"datetime": datetime, "dt_time": dt_time}
    exec(compile(settings, "settings", "exec"), ns)
    ns["EXIT_STRATEGIES"] = {"T250_S150": {"tp": 2.5, "sl": -1.5}}

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except Exception:
            return default

    ns["safe_float"] = safe_float

    needed = {
        "_parse_hhmm",
        "is_live_entry_time_allowed",
        "_logical_live_config_check",
        "validate_live_trading_config",
        "_ensure_v1610_position_fields",
        "_current_gross_return_pct",
        "_evaluate_v1610_live_exit_state",
    }
    tree = ast.parse(program)
    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in needed
    ]
    found = {node.name for node in selected}
    assert needed <= found, f"missing pure functions: {needed - found}"
    exec(compile(ast.Module(body=selected, type_ignores=[]), "pure-v1610", "exec"), ns)

    allowed = ns["is_live_entry_time_allowed"]
    assert not allowed(datetime(2026, 9, 4, 9, 4, 59))
    assert allowed(datetime(2026, 9, 4, 9, 5, 0))
    assert allowed(datetime(2026, 9, 4, 9, 29, 59, 999000))
    assert not allowed(datetime(2026, 9, 4, 9, 30, 0))
    assert not allowed(datetime(2026, 9, 4, 9, 30, 42))

    keys = [
        "LIVE_TRADE_AMOUNT_WON",
        "LIVE_MAX_STOCKS",
        "LIVE_MAX_TRADES_PER_DAY",
        "LIVE_MAX_CONCURRENT_POSITIONS",
        "LIVE_TOTAL_BUDGET_WON",
        "LIVE_DAILY_MAX_LOSS_WON",
    ]
    original = {k: ns[k] for k in keys}
    for amount, stocks, total in [
        (1_000_000, 5, 6_000_000),
        (2_000_000, 3, 7_000_000),
    ]:
        ns["LIVE_TRADE_AMOUNT_WON"] = amount
        ns["LIVE_MAX_STOCKS"] = stocks
        ns["LIVE_MAX_TRADES_PER_DAY"] = stocks
        ns["LIVE_MAX_CONCURRENT_POSITIONS"] = stocks
        ns["LIVE_TOTAL_BUDGET_WON"] = total
        ns["LIVE_DAILY_MAX_LOSS_WON"] = 100_000
        assert ns["validate_live_trading_config"]() is True

    for amount, stocks, total, loss in [
        (0, 5, 6_000_000, 100_000),
        (1_000_000, 0, 6_000_000, 100_000),
        (1_000_000, 2.5, 6_000_000, 100_000),
        (2_000_000, 3, 1_000_000, 100_000),
        (1_000_000, 5, 6_000_000, 0),
    ]:
        ns["LIVE_TRADE_AMOUNT_WON"] = amount
        ns["LIVE_MAX_STOCKS"] = stocks
        ns["LIVE_MAX_TRADES_PER_DAY"] = stocks
        ns["LIVE_MAX_CONCURRENT_POSITIONS"] = stocks
        ns["LIVE_TOTAL_BUDGET_WON"] = total
        ns["LIVE_DAILY_MAX_LOSS_WON"] = loss
        try:
            ns["validate_live_trading_config"]()
            raise AssertionError(("invalid config accepted", amount, stocks, total, loss))
        except ValueError:
            pass
    ns.update(original)

    def position():
        return {
            "avg_entry_price": 10_000.0,
            "target_price": 10_250.0,
            "stop_price": 9_850.0,
            "status": "OPEN",
            "entry_complete": True,
            "auto_managed_qty": 1,
        }

    evaluate = ns["_evaluate_v1610_live_exit_state"]

    p = position()
    reason, _, _ = evaluate(p, 10_100, datetime(2026, 9, 4, 10, 0))
    assert reason is None and p["profit_protect_armed"] is True
    reason, _, _ = evaluate(p, 10_040, datetime(2026, 9, 4, 10, 1))
    assert reason == "PROFIT_PROTECT"

    p = position()
    evaluate(p, 10_099, datetime(2026, 9, 4, 11, 0))
    reason, _, _ = evaluate(p, 10_040, datetime(2026, 9, 4, 12, 0))
    assert reason == "NOON_RECOVERY"

    p = position()
    evaluate(p, 10_099, datetime(2026, 9, 4, 11, 0))
    reason, _, _ = evaluate(p, 9_970, datetime(2026, 9, 4, 12, 0))
    assert reason is None and p["noon_recovery_waiting"] is True
    reason, _, _ = evaluate(p, 10_040, datetime(2026, 9, 4, 13, 0))
    assert reason == "NOON_RECOVERY"

    # Once NOON_RECOVERY_WAIT is set, an afternoon jump is still NOON_RECOVERY, not reclassified.
    p = position()
    evaluate(p, 10_050, datetime(2026, 9, 4, 11, 0))
    reason, _, _ = evaluate(p, 9_970, datetime(2026, 9, 4, 12, 0))
    assert reason is None and p["noon_recovery_waiting"] is True
    reason, _, _ = evaluate(p, 10_120, datetime(2026, 9, 4, 13, 0))
    assert reason == "NOON_RECOVERY"

    p = position()
    evaluate(p, 10_100, datetime(2026, 9, 4, 11, 0))
    reason, _, _ = evaluate(p, 10_050, datetime(2026, 9, 4, 12, 0))
    assert reason is None and p["noon_recovery_eligible"] is False

    p = position()
    p["profit_protect_armed"] = True
    p["max_return_pct"] = 1.25
    reason, _, _ = evaluate(p, 10_250, datetime(2026, 9, 4, 10, 5))
    assert reason == "TAKE_PROFIT"

    p = position()
    p["profit_protect_armed"] = True
    p["max_return_pct"] = 1.25
    reason, _, _ = evaluate(p, 9_850, datetime(2026, 9, 4, 10, 5))
    assert reason == "STOP_LOSS"

    # Restart-like restored armed state.
    p = position()
    p["profit_protect_armed"] = True
    p["max_return_pct"] = 1.25
    reason, _, _ = evaluate(p, 10_040, datetime(2026, 9, 4, 10, 5))
    assert reason == "PROFIT_PROTECT"

    # PROTECT OFF keeps arm state for research but does not emit actual protect reason.
    ns["LIVE_PROFIT_PROTECT_ENABLED"] = False
    p = position()
    reason, _, _ = evaluate(p, 10_100, datetime(2026, 9, 4, 10, 0))
    assert reason is None and p["profit_protect_armed"] is True
    reason, _, _ = evaluate(p, 10_040, datetime(2026, 9, 4, 10, 1))
    assert reason is None


def validate_and_rewrite(path: Path) -> None:
    if path.name != EXPECTED_NAME:
        raise SystemExit(f"expected {EXPECTED_NAME}, got {path.name}")
    nb = json.loads(path.read_text(encoding="utf-8"))
    program = "".join(nb["cells"][1]["source"])
    program = _cleanup_legacy_exact_locks(program)
    compile(program, "v1610-program-postprocessed", "exec")
    nb["cells"][1]["source"] = program.splitlines(keepends=True)
    for cell in nb["cells"]:
        cell["execution_count"] = None
        cell["outputs"] = []
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")

    # Re-read exactly what was written.
    final_nb = json.loads(path.read_text(encoding="utf-8"))
    settings, final_program = _static_validate(final_nb)
    _behavioral_validate(settings, final_program)
    print("V1610_STATIC_VALIDATION_OK")
    print("V1610_BEHAVIORAL_REGRESSION_OK")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_v1_6_10.py 016_260904_v1.6.10.ipynb")
    validate_and_rewrite(Path(sys.argv[1]))
