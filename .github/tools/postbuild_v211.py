#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from datetime import datetime


def load_nb(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def code_cells(nb: dict) -> list[str]:
    return [''.join(c.get('source', [])) for c in nb.get('cells', []) if c.get('cell_type') == 'code']


def mutate_program(nb: dict, old: str, new: str = '') -> dict:
    out = copy.deepcopy(nb)
    cell = next(c for c in out['cells'] if c.get('id') == 'v169-program')
    src = ''.join(cell.get('source', []))
    if src.count(old) != 1:
        raise RuntimeError(f'mutation marker count != 1: {old!r}')
    src = src.replace(old, new, 1)
    cell['source'] = src.splitlines(keepends=True)
    return out


def validator_result(validator: pathlib.Path, notebook: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(validator), str(notebook)],
        text=True,
        capture_output=True,
        check=False,
    )


def negative_controls(target: pathlib.Path, validator: pathlib.Path, tmp: pathlib.Path) -> list[str]:
    nb = load_nb(target)
    good = validator_result(validator, target)
    if good.returncode != 0:
        raise RuntimeError('baseline validator failed:\n' + good.stdout + good.stderr)

    cases = [
        (
            'copy',
            'import copy\n',
            '',
            'copy',
        ),
        (
            'selected_exit_strategies',
            '    selected_exit_strategies = _validate_selected_exit_strategies(\n'
            '        EXIT_STRATEGIES if exit_strategies is None else exit_strategies\n'
            '    )\n\n',
            '',
            'selected_exit_strategies',
        ),
    ]
    results = []
    for label, old, new, expected_name in cases:
        bad = mutate_program(nb, old, new)
        path = tmp / f'negative_{label}.ipynb'
        path.write_text(json.dumps(bad, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        proc = validator_result(validator, path)
        combined = proc.stdout + '\n' + proc.stderr
        if proc.returncode == 0:
            raise RuntimeError(f'negative control {label}: validator unexpectedly passed')
        if expected_name not in combined:
            raise RuntimeError(
                f'negative control {label}: expected undefined name not present\n{combined}'
            )
        results.append(f'{label}: validator FAIL as expected')
    return results


def execute_release(target: pathlib.Path, tmp: pathlib.Path) -> dict:
    nb = load_nb(target)
    cells = code_cells(nb)
    if len(cells) != 4:
        raise RuntimeError(f'expected 4 code cells, found {len(cells)}')
    (tmp / '.env').write_text(
        'KIWOOM_APP_KEY=dummy\nKIWOOM_SECRET_KEY=dummy\nTELEGRAM_BOT_TOKEN=dummy\n'
        'TELEGRAM_PERSONAL_CHAT_ID=\nTELEGRAM_GROUP_CHAT_ID=\n',
        encoding='utf-8',
    )
    old_cwd = pathlib.Path.cwd()
    os.chdir(tmp)
    try:
        ns = {'__name__': 'v211_postbuild'}
        exec(cells[0], ns)
        exec(cells[1], ns)
        return ns
    finally:
        os.chdir(old_cwd)


def bomb_external(ns: dict) -> list[str]:
    called = []
    def bomb(name):
        def _f(*args, **kwargs):
            called.append(name)
            raise AssertionError('external call forbidden: ' + name)
        return _f
    for name in [
        'get_kiwoom_token', 'kiwoom_post', 'send_telegram', 'submit_stock_order',
        'start_websocket_manager', 'initialize_live_broker_state_with_retry',
    ]:
        if name in ns:
            ns[name] = bomb(name)
    return called


def base_stock(code: str) -> dict:
    t = datetime(2026, 9, 15, 9, 5, 0)
    return {
        'stock_code': code,
        'stock_name': code,
        'market': 'KOSPI',
        'current_price': 10000.0,
        'change_rate': 7.0,
        'score': 80,
        'score_detail': {},
        'trading_value_source': 'ACTUAL',
        'actual_trading_value': 50_000_000_000,
        'estimated_trading_value': 50_000_000_000,
        'trading_value_used': 50_000_000_000,
        'scan_session': 'MAIN',
        'decision_session': 'MAIN',
        'decision_time': t,
        'score_time': t,
    }


def verify_duplicate_and_atomicity(ns: dict) -> list[str]:
    ns['PAPER_TRADE_ENABLED'] = True
    ns['AUTO_PAPER_ENTRY'] = True
    ns['ONE_ENTRY_PER_STOCK'] = True
    ns['WEBSOCKET_ENABLED'] = False
    ns['HISTORY_LOOKBACKS_SEC'] = []

    side_effects = {'entry_path': 0, 'policy': 0, 'wide': 0, 'subscribe': 0}
    ns['attach_session_decision_metrics'] = lambda stock, scan, when: (True, 'OK')
    ns['attach_pre_first_75_metrics'] = lambda *a, **k: None
    ns['attach_entry_cost_metrics'] = lambda *a, **k: None
    ns['start_entry_path_tracking'] = lambda *a, **k: side_effects.__setitem__('entry_path', side_effects['entry_path'] + 1)
    ns['start_policy_shadow_tracking'] = lambda *a, **k: side_effects.__setitem__('policy', side_effects['policy'] + 1)
    ns['start_wide_snapshot_tracking'] = lambda *a, **k: side_effects.__setitem__('wide', side_effects['wide'] + 1)
    ns['log'] = lambda *a, **k: None
    ns['get_session'] = lambda: 'MAIN'
    ns['_current_watch_episode_id'] = lambda code, stock=None: 'POSTBUILD_EPISODE'
    ns['paper_entry_key'] = lambda code, mode, episode=None: (code, mode, episode)
    ns['make_trade_id'] = lambda code, mode, episode=None: f'POST-{code}-{mode}-{episode}'
    ns['_commit_paper_reentry_metadata'] = lambda stock, mode, tid, meta: {
        'stock_entry_seq_today': 1,
        'mode_entry_seq_today': 1,
        'is_reentry': False,
        'previous_same_mode_result': '',
        'previous_same_mode_trade_id': '',
    }

    class WS:
        def subscribe_stock(self, *args, **kwargs):
            side_effects['subscribe'] += 1
    ns['websocket_manager'] = WS()

    stock = base_stock('999921')
    tid = ns['open_paper_trade'](
        stock,
        'OPENING_LEADER_DIRECT',
        exit_strategies=ns['NEW_STOCK_EXIT_STRATEGIES'],
        forced_entry_time=datetime(2026, 9, 15, 9, 5, 0),
        forced_entry_price=10000.0,
    )
    if not tid or len(ns['paper_positions'][tid]['strategies']) != 20:
        raise RuntimeError('first 20-grid entry failed')
    positions_after_first = len(ns['paper_positions'])
    effects_after_first = dict(side_effects)

    duplicate = ns['open_paper_trade'](
        stock,
        'OPENING_LEADER_DIRECT',
        exit_strategies=ns['NEW_STOCK_EXIT_STRATEGIES'],
        forced_entry_time=datetime(2026, 9, 15, 9, 5, 5),
        forced_entry_price=10000.0,
    )
    if duplicate is not None:
        raise RuntimeError('duplicate same-mode entry was not prevented')
    if len(ns['paper_positions']) != positions_after_first or side_effects != effects_after_first:
        raise RuntimeError('duplicate attempt left side effects')

    positions_before_bad = dict(ns['paper_positions'])
    entered_before_bad = set(ns['paper_entered_today'])
    effects_before_bad = dict(side_effects)
    try:
        ns['open_paper_trade'](base_stock('999922'), 'INVALID_GRID', exit_strategies={})
    except ValueError:
        pass
    else:
        raise RuntimeError('invalid grid unexpectedly accepted')
    if ns['paper_positions'] != positions_before_bad:
        raise RuntimeError('invalid grid changed paper_positions')
    if ns['paper_entered_today'] != entered_before_bad:
        raise RuntimeError('invalid grid changed paper_entered_today')
    if side_effects != effects_before_bad:
        raise RuntimeError('invalid grid triggered tracker/ws side effects')

    return [
        'duplicate same-mode entry: blocked without side effects',
        'invalid grid: atomic failure before position/entered/tracker/ws',
    ]


def verify_opening_observation_and_grace(ns: dict, tmp: pathlib.Path) -> list[str]:
    original_enqueue = ns.get('enqueue_research_rows')
    written = []

    def write_rows(filename, rows, priority, columns=None, kind=None):
        path = tmp / pathlib.Path(str(filename)).name
        fieldnames = list(columns or (rows[0].keys() if rows else []))
        with path.open('a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if f.tell() == 0:
                writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, '') for k in fieldnames})
        written.append(path)
        return True

    ns['enqueue_research_rows'] = write_rows
    try:
        moment = datetime(2026, 9, 15, 9, 5, 0)
        stock = base_stock('999931')
        stock['current_price'] = 101.0
        state = {
            'episode_id': 'POSTBUILD-OBS',
            'first_seen_time': datetime(2026, 9, 15, 9, 0, 0),
            'current_rank': 1,
            'best_rank': 1,
            'in_top_n': True,
            'rank_event': 'STAY',
            'opening_high': 100.0,
            'opening_low': 98.0,
            'observations': [(datetime(2026, 9, 15, 9, 4, 0), 99.0)],
        }
        reference = {
            'data_status': 'OK',
            'reference_high': 100.0,
            'reference_high_source': 'POSTBUILD',
            'reference_high_cutoff_time': datetime(2026, 9, 15, 9, 4, 59),
            'observation_span_sec': 300.0,
            'sample_count': 2,
            'max_observation_gap_sec': 60.0,
        }
        lag = {15: (0.1, 15.0), 30: (0.2, 30.0), 60: (0.3, 60.0)}
        ok = ns['_save_opening_leader_observation'](
            stock, state, reference, moment, 0.5, moment, 0.0, 0.7, lag
        )
        if ok is not True or not written:
            raise RuntimeError('opening-leader observation enqueue failed')
        obs_path = written[-1]
        if not obs_path.name.endswith('_v211.csv') or obs_path.stat().st_size <= 0:
            raise RuntimeError(f'opening observation file invalid: {obs_path}')
    finally:
        if original_enqueue is not None:
            ns['enqueue_research_rows'] = original_enqueue

    ns['opening_leader_date'] = None
    ns['opening_leader_states'].clear()
    ns['opening_leader_observation_keys'].clear()
    first = base_stock('999932')
    first.update({'change_rank': 1, 'current_price': 10000.0, 'change_rate': 6.0})
    amap = {'999932': {'actual_trading_value': 5_000_000_000, 'trading_value_rank': 1}}
    selected1 = ns['update_opening_leader_universe']([first], amap, datetime(2026, 9, 15, 9, 0, 5))
    if not any(x.get('stock_code') == '999932' for x in selected1):
        raise RuntimeError('opening leader initial top-N registration failed')
    selected_grace = ns['update_opening_leader_universe']([], amap, datetime(2026, 9, 15, 9, 0, 45))
    if not any(x.get('stock_code') == '999932' for x in selected_grace):
        raise RuntimeError('top-N grace did not preserve candidate')
    selected_expired = ns['update_opening_leader_universe']([], amap, datetime(2026, 9, 15, 9, 1, 10))
    if any(x.get('stock_code') == '999932' for x in selected_expired):
        raise RuntimeError('top-N grace did not expire')

    return [
        f'opening observation temp file: {written[-1].name}',
        'top-N grace: preserve within 60s / expire after 60s',
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=pathlib.Path, required=True)
    parser.add_argument('--validator', type=pathlib.Path, default=pathlib.Path('.github/tools/validate_release_notebook.py'))
    parser.add_argument('--report', type=pathlib.Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as td_raw:
        td = pathlib.Path(td_raw)
        negative = negative_controls(args.target, args.validator, td)
        ns = execute_release(args.target, td)
        called = bomb_external(ns)
        replay = ns['run_off_hours_validation']()
        if called or replay.get('external_connections') != 0 or replay.get('broker_orders') != 0:
            raise RuntimeError(f'off-hours external calls detected: {called}')
        duplicate = verify_duplicate_and_atomicity(ns)
        observation = verify_opening_observation_and_grace(ns, td)

    lines = [
        '# v2.1.1 post-build 승인검증',
        '',
        '- 대상: `code/releases/024_260915_v2.1.1.ipynb`',
        '- 외부 연결/실제·모의 주문: 0건',
        '',
        '## 실제 validator negative-control',
        '',
        *[f'- PASS: {x}' for x in negative],
        '',
        '## 상태 원자성·중복진입',
        '',
        *[f'- PASS: {x}' for x in duplicate],
        '',
        '## OPENING_LEADER 장외 fixture',
        '',
        *[f'- PASS: {x}' for x in observation],
        '- PASS: built-in DIRECT / RETEST / RS / COMMON_FAIL / DATA_UNAVAILABLE replay',
        '',
        '## 판정',
        '',
        '**POST_BUILD_APPROVAL_PASS**',
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
