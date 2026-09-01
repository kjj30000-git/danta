#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import hashlib
import json
from pathlib import Path

A = Path("code/releases/014_260901_v1.6.8.ipynb")
B = Path("code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb")
OUT = Path("reports/comparison/2026-09-01_v1.6.8_github_vs_새채팅.txt")


def load_nb(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def src(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else str(s)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def code_cells(nb):
    return [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]


def parse_ok(text):
    try:
        ast.parse(text)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def function_map(text):
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            block = "".join(lines[node.lineno-1:node.end_lineno])
            # AST dump ignores comments/most formatting, useful for semantic-ish comparison.
            norm = ast.dump(node, annotate_fields=True, include_attributes=False)
            out[node.name] = {
                "source": block,
                "source_sha": sha(block),
                "ast_sha": sha(norm),
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
            }
    return out


def simple_assignments(text):
    tree = ast.parse(text)
    out = {}
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            try:
                val = ast.literal_eval(node.value)
            except Exception:
                continue
            out[name] = val
    return out


def marker_checks(nb):
    cells = nb.get("cells", [])
    all_text = "\n".join(src(c) for c in cells)
    first = src(cells[0]) if cells else ""
    final = src(cells[-1]) if cells else ""
    quick = src(cells[2]) if len(cells) >= 3 else ""
    body = src(cells[1]) if len(cells) >= 2 else ""

    checks = {
        "exact_4_cells": len(cells) == 4,
        "all_4_code_cells": len(cells) == 4 and all(c.get("cell_type") == "code" for c in cells),
        "auto_trade_default_false": "AUTO_TRADE_ENABLED = False" in first,
        "strategy_v168": 'STRATEGY_VERSION = "v1.6.8"' in body,
        "first75_live": 'LIVE_ENTRY_MODE = "FIRST_75_PASS"' in first or 'LIVE_ENTRY_MODE = "FIRST_75_PASS"' in body,
        "t200_s150": 'LIVE_STRATEGY = "T200_S150"' in first or 'LIVE_STRATEGY = "T200_S150"' in body,
        "watch_score_60": "WATCH_SCORE = 60" in body,
        "signal_score_75": "MIN_SIGNAL_SCORE = 75" in body,
        "169_grid_guard": "len(EXIT_STRATEGIES) != 169" in body,
        "watch_episode": "WATCH Episode" in all_text or "watch_episode" in all_text,
        "entry_path": "ENTRY_PATH" in all_text,
        "post_exit": "POST_EXIT" in all_text,
        "live_filter_shadow": "LIVE_FILTER_SHADOW" in all_text,
        "shadow_70_74": "SHADOW_SCORE_70_74" in all_text,
        "live_state_lock": "LIVE_STATE_FILE_LOCK" in body,
        "unique_tmp": "tempfile.mkstemp" in body,
        "atomic_replace": "os.replace" in body,
        "save_retry": "LIVE_STATE_SAVE_RETRY_COUNT" in body,
        "external_order_progress": "external_sell_order_progress" in body,
        "external_fill_lots": "external_sell_fill_lots" in body,
        "external_track_helper": "_track_external_sell_execution" in body,
        "external_consume_helper": "_consume_external_sell_lots" in body,
        "external_pnl_helper": "_apply_external_auto_realized_pnl" in body,
        "timing_trigger": "exit_trigger_time" in body,
        "timing_precheck_start": "broker_precheck_start_time" in body,
        "timing_precheck_end": "broker_precheck_end_time" in body,
        "timing_precheck_sec": "broker_precheck_sec" in body,
        "timing_sell_order": "sell_order_time" in body,
        "timing_sell_fill": "sell_fill_time" in body,
        "timing_trigger_to_order": "trigger_to_order_sec" in body,
        "timing_order_to_fill": "order_to_fill_sec" in body,
        "timing_trigger_to_fill": "trigger_to_fill_sec" in body,
        "broker_positions_precheck": "get_broker_positions()" in body,
        "broker_pending_precheck": "get_broker_pending_orders()" in body,
        "v168_regression_helper": "test_v168_manual_sell_ledger_helpers" in body,
        "quick_reference_title": "QUICK REFERENCE" in quick,
        "quick_reference_mfe_mae": "MFE" in quick and "MAE" in quick,
        "continuity_final": "PROJECT CONTINUITY NOTES / DECISION HISTORY" in final,
        "continuity_principle": "PROJECT CONTINUITY PRINCIPLE" in final,
        "continuity_exact_base": "013_260830_v1.6.7_startmsg_fix.ipynb" in final,
        "continuity_not_manual_fix_base": "manual_pnl_fix" in final,
        "future_market_research": all(x in final for x in ["FIRST_75_PASS", "KOSPI", "KOSDAQ", "삼성전자", "SK하이닉스"]),
    }
    return checks


def compare():
    na = load_nb(A)
    nb = load_nb(B)
    ca = na.get("cells", [])
    cb = nb.get("cells", [])
    ac = code_cells(na)
    bc = code_cells(nb)

    lines = []
    p = lines.append
    p("v1.6.8 TWO-VARIANT COMPARISON — 2026-09-01")
    p("=" * 76)
    p(f"A GitHub-built : {A}")
    p(f"B 새채팅-built : {B}")
    p(f"A file SHA256  : {hashlib.sha256(A.read_bytes()).hexdigest()}")
    p(f"B file SHA256  : {hashlib.sha256(B.read_bytes()).hexdigest()}")
    p(f"Exact file same: {A.read_bytes() == B.read_bytes()}")
    p("")

    p("[1] NOTEBOOK STRUCTURE")
    p(f"A cells={len(ca)} / code_cells={len(ac)} / types={[c.get('cell_type') for c in ca]}")
    p(f"B cells={len(cb)} / code_cells={len(bc)} / types={[c.get('cell_type') for c in cb]}")
    for i in range(max(len(ca), len(cb))):
        ta = src(ca[i]) if i < len(ca) else ""
        tb = src(cb[i]) if i < len(cb) else ""
        p(f"cell{i+1}: A chars={len(ta):,}, B chars={len(tb):,}, source_equal={ta == tb}, A_sha={sha(ta)[:12]}, B_sha={sha(tb)[:12]}")
    p("")

    # Compile every code cell independently.
    p("[2] SYNTAX")
    for label, cells in [("A", ac), ("B", bc)]:
        for i, c in enumerate(cells, 1):
            ok, err = parse_ok(src(c))
            p(f"{label} code cell {i}: {'PASS' if ok else 'FAIL'} {err}")
    p("")

    # Core body function comparison assumes full program is cell 2 if present.
    body_a = src(ca[1]) if len(ca) > 1 else ""
    body_b = src(cb[1]) if len(cb) > 1 else ""
    fa = function_map(body_a)
    fb = function_map(body_b)
    names_a, names_b = set(fa), set(fb)
    only_a = sorted(names_a - names_b)
    only_b = sorted(names_b - names_a)
    common = sorted(names_a & names_b)
    changed_ast = [n for n in common if fa[n]["ast_sha"] != fb[n]["ast_sha"]]
    changed_source_only = [n for n in common if fa[n]["ast_sha"] == fb[n]["ast_sha"] and fa[n]["source_sha"] != fb[n]["source_sha"]]
    same_ast = [n for n in common if fa[n]["ast_sha"] == fb[n]["ast_sha"]]

    p("[3] FUNCTION-LEVEL COMPARISON (AST ignores comments/formatting)")
    p(f"A functions={len(fa)}, B functions={len(fb)}, common={len(common)}")
    p(f"Only A ({len(only_a)}): {', '.join(only_a) if only_a else '-'}")
    p(f"Only B ({len(only_b)}): {', '.join(only_b) if only_b else '-'}")
    p(f"Changed AST ({len(changed_ast)}): {', '.join(changed_ast) if changed_ast else '-'}")
    p(f"Same AST ({len(same_ast)}), of which source/comment/format-only differs ({len(changed_source_only)}): {', '.join(changed_source_only) if changed_source_only else '-'}")
    p("")

    # Focus on safety-critical functions.
    focus = [
        "save_live_state", "_normalize_live_position_state", "_sync_position_from_broker",
        "handle_external_order_event", "_submit_live_exit_worker", "handle_order_execution",
        "save_live_trade_result", "submit_live_exit", "compute_broker_fill_delta",
        "reconcile_managed_quantities", "can_open_live_trade", "submit_live_entry",
        "run_scanner", "test_v168_manual_sell_ledger_helpers",
    ]
    p("[4] SAFETY/ORDER-ENGINE FOCUS")
    for n in focus:
        a, b = fa.get(n), fb.get(n)
        if a and b:
            status = "SAME_AST" if a["ast_sha"] == b["ast_sha"] else "DIFFERENT_AST"
        elif a:
            status = "ONLY_A"
        elif b:
            status = "ONLY_B"
        else:
            status = "MISSING_BOTH"
        p(f"{n}: {status}")
    p("")

    # Simple top-level literal config differences.
    aa = simple_assignments(src(ca[0]) + "\n" + body_a) if ca else {}
    ab = simple_assignments(src(cb[0]) + "\n" + body_b) if cb else {}
    keys = sorted(set(aa) | set(ab))
    config_diff = [(k, aa.get(k, '<MISSING>'), ab.get(k, '<MISSING>')) for k in keys if aa.get(k, '<MISSING>') != ab.get(k, '<MISSING>')]
    p("[5] TOP-LEVEL LITERAL ASSIGNMENT DIFFERENCES")
    if not config_diff:
        p("None")
    else:
        for k, va, vb in config_diff:
            p(f"{k}: A={va!r} / B={vb!r}")
    p("")

    ma = marker_checks(na)
    mb = marker_checks(nb)
    p("[6] v1.6.8 REQUIREMENT CHECKLIST")
    p("requirement | A GitHub | B 새채팅")
    for k in ma:
        p(f"{k} | {'PASS' if ma[k] else 'FAIL'} | {'PASS' if mb[k] else 'FAIL'}")
    p("")

    # Overall classification.
    req_a = all(ma.values())
    req_b = all(mb.values())
    critical_focus_same = all(
        (fa.get(n) is not None and fb.get(n) is not None and fa[n]["ast_sha"] == fb[n]["ast_sha"])
        for n in [
            "compute_broker_fill_delta", "can_open_live_trade", "submit_live_entry"
        ]
        if n in fa or n in fb
    )
    p("[7] SUMMARY")
    p(f"A all checklist PASS: {req_a}")
    p(f"B all checklist PASS: {req_b}")
    p(f"Exact body source same: {body_a == body_b}")
    p(f"Function AST changes count: {len(changed_ast)}")
    p(f"Core preserved-function sample same: {critical_focus_same}")
    p("Interpretation rule: checklist PASS means required v1.6.8 features are present; it does NOT by itself prove two implementations are behaviorally identical. DIFFERENT_AST on order/sync/PnL functions requires manual review.")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    compare()
