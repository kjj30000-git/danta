#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ALLOWED_CHANGED_FUNCTIONS = {
    'open_paper_trade',
    'build_strategy_result_row',
    'validate_v21_opening_leader_config',
}
ALLOWED_NEW_FUNCTIONS = {
    '_validate_selected_exit_strategies',
    'run_off_hours_validation',
}


def load_code(path: Path) -> tuple[dict, list[str]]:
    nb = json.loads(path.read_text(encoding='utf-8'))
    cells = [
        ''.join(c.get('source', []))
        for c in nb.get('cells', [])
        if c.get('cell_type') == 'code'
    ]
    if len(cells) != 4:
        raise AssertionError(f'{path}: expected 4 code cells, found {len(cells)}')
    return nb, cells


def top_functions(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def top_assignments(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = target_name(target)
                if name:
                    result[name] = ast.dump(node.value, include_attributes=False)
        elif isinstance(node, ast.AnnAssign):
            name = target_name(node.target)
            if name:
                result[name] = ast.dump(node.value, include_attributes=False)
    return result


def duplicate_dict_keys(source: str) -> list[tuple[str, int]]:
    tree = ast.parse(source)
    failures = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        seen = set()
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, (str, int, float, bytes)):
                if key.value in seen:
                    failures.append((str(key.value), getattr(key, 'lineno', -1)))
                seen.add(key.value)
    return failures


def count_assignments(source: str, name: str) -> int:
    tree = ast.parse(source)
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            total += sum(isinstance(t, ast.Name) and t.id == name for t in node.targets)
        elif isinstance(node, ast.AnnAssign):
            total += int(isinstance(node.target, ast.Name) and node.target.id == name)
    return total


def forbidden_calls_in_function(source: str, function_name: str) -> list[str]:
    tree = ast.parse(source)
    forbidden = {
        'get_kiwoom_token', 'kiwoom_post', 'send_telegram', 'submit_stock_order',
        'start_websocket_manager', 'initialize_live_broker_state_with_retry',
        'requests', 'websockets',
    }
    fn = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == function_name
    )
    hits = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in forbidden:
            hits.append(node.func.id)
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id in forbidden:
                hits.append(f'{node.func.value.id}.{node.func.attr}')
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('parent', type=Path)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()

    _, parent_cells = load_code(args.parent)
    _, target_cells = load_code(args.target)
    p_settings, p_program, _, _ = parent_cells
    t_settings, t_program, _, _ = target_cells
    failures = []
    passes = []

    p_sa = top_assignments(p_settings)
    t_sa = top_assignments(t_settings)
    allowed_settings = {'PROGRAM_START', 'PROGRAM_END', 'OFF_HOURS_VALIDATION_MODE'}
    for name, dump in p_sa.items():
        if name in allowed_settings:
            continue
        if t_sa.get(name) != dump:
            failures.append(f'Cell1 unexpected assignment drift: {name}')
    if t_sa.get('PROGRAM_START') != ast.dump(ast.Constant('08:00'), include_attributes=False):
        failures.append('PROGRAM_START is not 08:00')
    if t_sa.get('PROGRAM_END') != ast.dump(ast.Constant('20:00'), include_attributes=False):
        failures.append('PROGRAM_END is not 20:00')
    if t_sa.get('OFF_HOURS_VALIDATION_MODE') != ast.dump(ast.Constant(False), include_attributes=False):
        failures.append('OFF_HOURS_VALIDATION_MODE is not False')
    passes.append('Cell1 strategy/risk constants unchanged except approved operating-hours additions')

    p_funcs = top_functions(p_program)
    t_funcs = top_functions(t_program)
    missing = sorted(set(p_funcs) - set(t_funcs))
    unexpected_new = sorted(set(t_funcs) - set(p_funcs) - ALLOWED_NEW_FUNCTIONS)
    if missing:
        failures.append('missing parent functions: ' + ', '.join(missing))
    if unexpected_new:
        failures.append('unexpected new functions: ' + ', '.join(unexpected_new))
    changed = []
    for name in sorted(set(p_funcs) & set(t_funcs)):
        if p_funcs[name] != t_funcs[name] and name not in ALLOWED_CHANGED_FUNCTIONS:
            changed.append(name)
    if changed:
        failures.append('unexpected changed functions: ' + ', '.join(changed))
    passes.append('All pre-existing strategy/order functions unchanged outside explicit allowlist')

    p_pa = top_assignments(p_program)
    t_pa = top_assignments(t_program)
    for name, dump in p_pa.items():
        if name in {'PROGRAM_START', 'PROGRAM_END'}:
            if name in t_pa:
                failures.append(f'duplicate top-level {name} still exists in program cell')
            continue
        if name == 'STRATEGY_VERSION' or name.endswith('_FILE'):
            continue
        if t_pa.get(name) != dump:
            failures.append(f'program top-level assignment drift: {name}')
    passes.append('Program constants unchanged except version/file outputs and removed duplicate hours')

    combined = '\n\n'.join(target_cells)
    if combined.count('import copy\n') != 1:
        failures.append('import copy count != 1')
    if count_assignments(combined, 'PROGRAM_START') != 1:
        failures.append('PROGRAM_START assignment count != 1')
    if count_assignments(combined, 'PROGRAM_END') != 1:
        failures.append('PROGRAM_END assignment count != 1')
    if duplicate_dict_keys(combined):
        failures.append('duplicate constant dict keys remain: ' + repr(duplicate_dict_keys(combined)[:20]))
    passes.append('Imports / single-source hours / duplicate dict key checks passed')

    tree = ast.parse(t_program)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'open_paper_trade')
    source_segment = ast.get_source_segment(t_program, fn) or ''
    selected_pos = source_segment.find('selected_exit_strategies = _validate_selected_exit_strategies(')
    register_pos = source_segment.find('paper_positions[trade_id] = p')
    entered_pos = source_segment.find('paper_entered_today.add(key)')
    loop_pos = source_segment.find('for name, rule in selected_exit_strategies.items():')
    if min(selected_pos, register_pos, entered_pos, loop_pos) < 0:
        failures.append('open_paper_trade required selected-grid markers missing')
    elif not (selected_pos < loop_pos < register_pos < entered_pos):
        failures.append('open_paper_trade selected-grid validation/registration ordering invalid')
    passes.append('Selected grid is validated/used before persistent paper state registration')

    hits = forbidden_calls_in_function(t_program, 'run_off_hours_validation')
    if hits:
        failures.append('off-hours replay has forbidden calls: ' + ', '.join(hits))
    required_literals = [
        '08:59:50', '09:00:05', '09:01:00', '09:04:59', '09:05:00',
        '09:15:00', '09:15:01', '14:30:00', '14:50:00', '15:00:00',
        '15:30:00', '15:40:00', '20:00:01',
    ]
    missing_times = [x for x in required_literals if x not in t_program]
    if missing_times:
        failures.append('off-hours required virtual times missing: ' + ', '.join(missing_times))
    passes.append('Off-hours replay is network/order-free and contains all required boundary times')

    for name, value_dump in t_pa.items():
        if not name.endswith('_FILE'):
            continue
        if '_v21.' in value_dump:
            failures.append(f'legacy v21 output suffix remains: {name}')
    passes.append('All top-level *_FILE outputs separated from v2.1 suffix')

    print('SECOND_REVIEW_V211')
    for item in passes:
        print('PASS:', item)
    if failures:
        for item in failures:
            print('FAIL:', item, file=sys.stderr)
        return 1
    print('SECOND_REVIEW_PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
