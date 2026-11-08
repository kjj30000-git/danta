"""v2.3.4 isolated notebook, order, and actual balance-ledger checks."""
import csv

import ast
import json
import os
import socket
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASES = ROOT / 'code/releases'
FILENAME = '031_261109_v2.3.4.ipynb'
SOURCES = [''.join(c['source']) for c in json.loads((RELEASES / FILENAME).read_text())['cells']]
PARENT = [''.join(c['source']) for c in json.loads((RELEASES / '030_260930_v2.3.3.ipynb').read_text())['cells']]


def forbid_network(*args, **kwargs):
    raise AssertionError('Network disabled for fixture')


socket.socket.connect = forbid_network
socket.socket.connect_ex = forbid_network


def load():
    Path('.env').write_text('KIWOOM_APP_KEY=test\nKIWOOM_SECRET_KEY=test\nTELEGRAM_BOT_TOKEN=test\nTELEGRAM_PERSONAL_CHAT_ID=123\n')
    mod = {'__name__': 'isolated_fixture'}
    for i in (0, 1):
        exec(compile(SOURCES[i], f'cell{i+1}', 'exec'), mod)
    mod['log'] = lambda *a, **kw: None
    return mod


def cold_start(m):
    class TokenBoundary(BaseException):
        pass

    def token():
        assert m['EXECUTION_MODE'] == 'RESEARCH'
        assert not m['USE_MOCK'] and not m['AUTO_TRADE_ENABLED']
        raise TokenBoundary()

    names = ('start_research_writer', 'start_research_safety_workers', 'start_live_exit_dispatcher',
             'start_live_exit_watchdog', 'start_research_compute_worker', 'start_live_state_flusher',
             'get_kiwoom_token')
    originals = {name: m[name] for name in names}
    m.update({name: lambda: None for name in names})
    m['get_kiwoom_token'] = token
    try:
        m['run_scanner']()
    except TokenBoundary:
        print('PASS cold startup through token boundary')
    else:
        raise AssertionError('Token boundary not reached')
    finally:
        m.update(originals)


def definitions(s):
    return {node.name for node in ast.parse(s).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def fixture(m):
    assert all(definitions(before) <= definitions(after) for before, after in zip(PARENT, SOURCES))
    assert SOURCES[2] == PARENT[2]
    assert SOURCES[3].startswith(PARENT[3]) and SOURCES[4].startswith(PARENT[4])
    assert not m['AUTO_TRADE_ENABLED'] and not m['USE_MOCK']
    assert m['run_v231_off_hours_validation']()
    assert m['test_v1713_order_safety']()
    dt, td = m['datetime'], m['timedelta']
    class Clock(dt):
        moment = dt(2026, 11, 9, 9)
        @classmethod
        def now(cls, *args):
            return cls.moment

    m['datetime'] = Clock
    now = Clock(2026, 11, 9, 9, 3, 30)
    Clock.moment = now
    m['v220_reset_day'](now)
    m['v234_start'](now)
    sample = dict(stock_code='999001', stock_name='A', market='KOSPI', change_rank=1,
                  current_price=100, estimated_trading_value=10000000)
    m['v234_register'](sample, now)
    m['v234_register'](dict(sample, stock_code='999002'), now.replace(minute=14, second=59))
    m['v234_register'](dict(sample, stock_code='999003'), now.replace(minute=15, second=0))
    assert set(m['v234_candidates']) == {'999001', '999002'}
    for i, (minute, price) in enumerate(((3, 200), (4, 100), (5, 99), (6, 98),
                                          (7, 101), (8, 102), (8, 103)), 1):
        Clock.moment = Clock(2026, 11, 9, 9, minute, 30 if i == 1 else 1 if i == 7 else 0)
        if i == 6:
            m['v234_index_tick']('001', {'20': '090800', '10': '110', '16': '100'},
                                Clock.moment + td(seconds=2))
        m['v234_tick']('999001', price, Clock.moment, {'20': Clock.moment.strftime('%H%M%S'), '16': '90'}, i)
    db = m['v234_db']
    assert db.execute("select count(*) from events where kind='FILL'").fetchone() == (1,)
    c = m['v234_candidates']['999001']
    assert c['status'] == 'FILLED' and c['signal']['market']['KOSPI']['status'] == 'MISSING'
    print('PASS 09:15 boundary, partial high exclusion, future received index exclusion, next tick fill')
    m['v234_start'](Clock.moment)
    m['v234_maintenance'](Clock(2026, 11, 9, 15, 21), False)
    assert m['v234_db'].execute("select count(*) from events where kind='FILL'").fetchone() == (1,)
    assert m['v234_db'].execute("select count(*) from events where kind='EXIT'").fetchone() == (1,)
    print('PASS restart after committed fill and cutoff idempotence')


def replay(m):
    dt = m['datetime']
    day = dt(2026, 11, 9, 9)
    m['v220_reset_day'](day)
    m['v234_start'](day)
    db = m['v234_db']
    template = dict(stock_code='990001', stock_name='bad', market='KOSPI',
                    change_rank=1, current_price=100, estimated_trading_value=10000)
    now = day.replace(minute=5)
    m['v234_register'](template, now)
    m['v234_register'](dict(template, stock_code='990002', stock_name='good'), now)
    a, b = (m['v234_candidates'][code] for code in ('990001', '990002'))
    events = []
    for i in range(2):
        start = day.replace(minute=6+i)
        m['v234_complete'](a, dict(minute=start, valid=False, reason='SEQUENCE_GAP'),
                          start.replace(second=59), events)
    for i, price in enumerate([100, 99, 98, 101]):
        start = day.replace(minute=6+i)
        end = start.replace(minute=start.minute+1)
        m['v234_complete'](b, dict(minute=start, high=price, close=price, opening=99,
                                  valid=True), end, [])
    assert b['status'] == 'PENDING' and a['degraded'] and not m['v234_blocked']
    for i in range(2):
        start = day.replace(minute=11+i)
        m['v234_complete'](a, dict(minute=start, high=110, close=109, opening=100,
                                  valid=True), start, events)
    assert not a['degraded'] and a['high'] == 110
    # A 09:29 signal may not be filled by a 09:30 quote.
    b['signal']['detected'] = day.replace(minute=29, second=59)
    boundary = day.replace(minute=30)
    m['v234_tick'](b['code'], 103, boundary, {'20': '093000'}, 1)
    m['v234_maintenance'](boundary, False)
    assert m['v234_candidates'][b['code']]['status'] == 'NO_FILL'
    # A duplicate event with a conflicting payload must stop new entries.
    assert m['v234_commit'](a, [('X', 'FORCED', now, {'v': 1})])
    assert not m['v234_commit'](a, [('X', 'FORCED', now, {'v': 2})])
    assert m['v234_blocked']
    m['v234_register'](dict(template, stock_code='990003'), now)
    assert '990003' not in m['v234_candidates']
    assert db.execute("select count(*) from events where kind='FORCED'").fetchone() == (1,)
    # An ambiguous Telegram response becomes terminal.
    m['v220_outbox'].clear()
    m['v220_outbox']['review'] = dict(parts=['fixture'], status='PENDING', next_part=0)
    calls = []
    m['send_telegram'] = lambda s: calls.append(s) or False
    assert not m['v220_notify_once']()
    assert not m['v220_notify_once']()
    assert calls == ['fixture'] and m['v220_outbox']['review']['status'] == 'DELIVERY_UNKNOWN'
    print('PASS candidate isolation/recovery, cutoff no fill, shared ledger conflict and Telegram uncertainty')


def regression(m):
    def definitions(source):
        return {node.name: ast.dump(node) for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    parents, updated = definitions(PARENT[1]), definitions(SOURCES[1])
    selected = ('submit_stock_order', 'submit_live_exit', '_submit_live_exit_worker',
                'compute_broker_fill_delta', 'get_broker_positions', 'get_broker_pending_orders',
                'handle_order_execution', 'force_close_live_positions', 'maybe_open_live_trade')
    assert all(parents[k] == updated[k] for k in selected)

    # Cell 3 is independent and uses a controlled response for separate partial fills.
    ns = {'__name__': 'pnl_test'}
    body = ast.parse(SOURCES[2])
    assert isinstance(body.body[-1], ast.If)
    body.body.pop()
    exec(compile(body, 'pnl', 'exec'), ns)
    fills = [{'stk_cd': '005930', 'cntr_qty': qty, 'cntr_pric': px, 'ord_no': '10',
              'io_tp_nm': '매도'} for qty, px in [('2', '100'), ('3', '110')]]
    rows = ns['pnl_aggregate']('2026-11-09', fills, [], [], {}, set(), 'now')
    assert len(rows) == 1 and rows[0]['sell_qty'] == 5 and rows[0]['avg_sell_price'] == 106
    print('PASS order AST identity and independent PnL partial fill aggregation')


def scenario(m):
    dt = m['datetime']
    class Clock(dt):
        value = dt(2026, 11, 9, 9)
        @classmethod
        def now(cls, *args):
            return cls.value
    m['datetime'] = Clock
    m['v220_reset_day'](Clock.value)
    m['v234_start'](Clock.value)
    def stock(code, at):
        return dict(stock_code=code, stock_name='fixture', market='KOSPI', current_price=100,
                    score=80, score_detail={'trading_value':40}, actual_trading_value=30_000_000_000,
                    estimated_trading_value=30_000_000_000, trading_value_used=30_000_000_000,
                    trading_value_source='ACTUAL', change_rate=7, change_rank=1, volume=500000,
                    day_high=100, high_gap=0, value_growth=1.5, volume_growth=1.3,
                    watch_episode_id='EP', score_time=at, _score_evaluated_ts=at.timestamp(),
                    scan_session='MAIN', decision_session='MAIN', decision_time=at,
                    history_available_sec=90, price_change_30s=.3, price_change_60s=1.,
                    high_gap_change_60s=-.1)
    for i, t in enumerate(((9, 4, 59), (9, 5, 0), (9, 5, 1), (9, 29, 59), (9, 30, 0), (9, 30, 1), (13, 0, 0)), 1):
        at = Clock(2026, 11, 9, *t)
        Clock.value = at
        code = str(900000 + i)
        s = stock(code, at)
        m['v234_register'](s, Clock(2026, 11, 9, 9, 0))
        if i == 7:
            m['V234_RESTORE_LEGACY_GRID'] = True
        base = m['open_paper_trade'](s, 'BASE')
        first = m['open_paper_trade'](dict(s, pre_entry_type='FIRST_75_PASS'), 'PRE_HISTORY',
                                    {'pre_entry_type': 'FIRST_75_PASS'})
        assert base and first
        for tid in (base, first):
            assert len(m['paper_positions'][tid]['strategies']) == (169 if i == 7 else 1)
        policies = m['v234_candidates'][code]['policies']
        assert len(policies) == (2 if i in {2, 3, 4} else 0)
    assert not m['PULLBACK_STRUCTURE_ENABLED'] and not m['PULLBACK_SNAPSHOT_DIRECT_ENABLED']
    assert not m['PULLBACK_SNAPSHOT_RECLAIM_ENABLED'] and not m['ETF_INTRADAY_MOMENTUM_ENABLED']
    print('PASS comparison 09:05/09:30 ±1s, legacy full-day collection and restored 169 grid')

    Clock.value = Clock(2026, 11, 9, 15, 15)
    mode = m['V232_BALANCE_MODE']
    # Real entry factory and a stable storage key. Leave the checkpoint behind the journal.
    for code in ('990090', '990091'):
        s = stock(code, Clock.value)
        tid = m['open_paper_trade'](s, mode, exit_strategies={'T200_S125': m['PULLBACK_EXIT_STRATEGIES']['T200_S125']})
        assert tid
        p = m['paper_positions'][tid]
        assert m['v234_store_fill'](p, (code, mode, 'box'), Clock.value)
        if code == '990090':
            tick = Clock(2026, 11, 9, 15, 19, 59)
            assert m['v234_cutoff_quote'](p, 101, tick, tick)
            assert not m['v234_cutoff_quote'](p, 120, tick, tick.replace(minute=20, second=1))
        m['paper_positions'].pop(tid)
        m['paper_position_ids_by_code'].pop(code)
    m['v234_start'](Clock.value)
    assert all(m['paper_position_ids_by_code'].get(code) for code in ('990090', '990091'))
    Clock.value = Clock(2026, 11, 9, 15, 20, 1)
    m['v220_maintenance'](Clock.value)
    m['v220_maintenance'](Clock.value)
    with open('paper_cutoff_exits_v234.csv', encoding='utf-8-sig', newline='') as f:
        rows = {row['stock_code']: row for row in csv.DictReader(f)}
    assert rows['990090']['result'] == 'TIME_EXIT' and float(rows['990090']['exit_price']) == 101
    assert rows['990091']['result'] == 'EXIT_UNCONFIRMED' and not rows['990091']['gross_return_pct']
    assert len(rows) == 2
    print('PASS journal-ahead restart, pre-cutoff price only, missing price and no duplicate exit')


def fill_tick_provenance(m):
    dt = m['datetime']
    moment = dt(2026, 11, 9, 10, 0, 2)
    m['v220_reset_day'](moment)
    c = m['v230_create_candidate_state']({
        'code': '999091', 'stock': {'stock_code': '999091', 'stock_name': 'fixture'},
        'candidate_start_time': moment.replace(minute=59, hour=9),
        'candidate_source': 'BASE', 'sources': {'BASE'}, 'parent_trade_ids': [],
    })
    c.update(data_status='OK', v234_wire='100001')
    m['v220_candidates'][c['code']] = c
    used = []
    original = m['v220_fill_pending']
    m['v220_fill_pending'] = lambda candidate, price, received: used.append(candidate['v234_wire'])
    try:
        m['v220_on_tick'](c['code'], 100, moment, {'20': '100002'}, 1)
    finally:
        m['v220_fill_pending'] = original
    assert used == ['100002'], used
    print('PASS pending-fill receives the current tick exchange timestamp')


def historical(m):
    dt = m['datetime']
    day = dt(2026, 9, 29, 8)
    m['v220_reset_day'](day)
    path = ROOT / 'data/2.3.2(260929)/pullback_balance_events_v232.csv'
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 20
    m['V232_BALANCE_EVENT_FILE'] = str(path)
    for row in rows:
        code = row['stock_code']
        m['v220_candidates'].setdefault(code, m['v230_create_candidate_state'](
            {'code':code, 'stock':{'stock_code':code, 'stock_name':row['stock_name']},
             'candidate_start_time':day, 'candidate_source':'BASE', 'sources':{'BASE'}, 'parent_trade_ids':[]}))
    m['v220_recover_signal_ledger']()
    messages = dict(m['v220_summary_text'](day.replace(hour=15, minute=30)))
    assert '돌파완료' in messages['BALANCE'] and '삼화콘덴서' in messages['BALANCE']
    assert '보합' in messages['BALANCE'] and m['V234_MODE'] in messages
    assert len(messages) == len(set(messages))
    print('PASS actual 2026-09-29 balance ledger 20 events and 15:30 separate strategy summaries')



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Network-disabled v2.3.4 checks')
    parser.add_argument('stage', choices=('build', 'review', 'regression'))
    stage = parser.parse_args().stage
    checks = {'build': (cold_start, fixture), 'review': (replay,),
              'regression': (cold_start, fixture, replay, regression, scenario, fill_tick_provenance, historical)}
    old = Path.cwd()
    try:
        for check in checks[stage]:
            with tempfile.TemporaryDirectory() as temp:
                os.chdir(temp)
                check(load())
    finally:
        os.chdir(old)
