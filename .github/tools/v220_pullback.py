# v2.2.0 신규/ON — 독립 눌림 관찰, 완료봉 판정, 신호 원장과 복구.
# 이 파일은 빌드 시 본체에 삽입됩니다. 독립 실행 모듈이 아닙니다.
from functools import wraps
from statistics import median

V220_LOCK = threading.RLock()  # 연구 전용; WS/live 경로는 이 lock을 획득하지 않습니다.
V220_MODES = ('BASE', 'FIRST_75_PASS', 'PULLBACK_SUPPORT_ENTRY', 'PULLBACK_RECLAIM_ENTRY')
V220_NEW_MODES = V220_MODES[2:]
V220_OFF_MODES = {'LATER_PASS', 'CALM_FIRST_75', 'CALM_FIRST_75_PROTECT', 'CONFIRM',
    'LIVE_FILTER_SHADOW', 'SHADOW_SCORE_70_74', 'WIDE_HIGH_GAP_SHADOW',
    'PRE_FAIL_PULLBACK_SHADOW', 'NEW_EARLY_ACCEL_SHADOW', 'NEW_FIRST_PULLBACK_SHADOW',
    'NEW_WATCH_RECLAIM_SHADOW', 'OPENING_LEADER_DIRECT', 'OPENING_LEADER_RETEST',
    'OPENING_LEADER_RS', 'ORB_DIRECT', 'ORB_RETEST', 'ORB_RS_RETEST'}
V220_STATE_FILE = 'pullback_state_v220.json'
V220_MINUTE_FILE = 'pullback_candidate_1m_v220.csv'
V220_SIGNAL_FILE = 'pullback_signals_v220.csv'
V220_METRICS_FILE = 'pullback_metrics_v220.csv'
V220_META_COLUMNS = ['candidate_source', 'candidate_start_time', 'base_signal_time',
    'first75_signal_time', 'parent_trade_ids', 'support_episode_id', 'peak_time', 'peak_price',
    'pullback_start_time', 'pullback_depth_pct', 'support_low_time', 'support_low_price',
    'support_anchor_low', 'support_candidate_time', 'support_confirm_time', 'support_elapsed_min',
    'rebound_from_low_pct', 'higher_low', 'prior_5m_high', 'reclaim_threshold_price',
    'reclaim_signal_time', 'reclaim_volume_ratio', 'signal_time', 'signal_detected_time',
    'signal_price', 'fill_time', 'fill_price', 'signal_to_fill_sec', 'signal_to_fill_slippage_pct',
    'rule_version', 'data_status']
V220_SIGNAL_COLUMNS = ['date', 'version', 'event_id', 'event', 'strategy', 'trade_id',
    'stock_code', 'stock_name'] + V220_META_COLUMNS
V220_MINUTE_COLUMNS = ['date', 'version', 'stock_code', 'stock_name', 'minute',
    'open', 'high', 'low', 'close', 'volume', 'tick_count', 'current_state', 'running_high',
    'pullback_pct', 'raw_pullback_low', 'base_duration', 'base_high', 'base_low',
    'base_range_pct', 'support_retest_count', 'minute_aggregation_delay_ms'] + V220_META_COLUMNS
V220_STATE_GLOBALS = ('paper_positions', 'paper_position_ids_by_code', 'paper_entered_today',
    'paper_stock_entry_counts_today', 'paper_mode_entry_counts_today', 'paper_last_trade_id_by_mode',
    'paper_trade_registry', 'watch_states', 'watch_episode_states', 'watch_episode_counts',
    'pre_first_75_states', 'score_75_seen_today')
v220_candidates = {}
v220_signals = {m: {} for m in V220_MODES}
v220_outbox = {}
v220_tick_sequences = {}
v220_fill_keys = set()
v220_date = ''
v220_halted = False
v220_last_checkpoint = 0.0
v220_last_metrics = 0.0
v220_notify_stop = threading.Event()
v220_notify_thread = None
v220_metrics = {'ticks': 0, 'gaps': 0, 'bars': 0, 'invalid_bars': 0, 'save_failures': 0}

# 함수 설명: 연구 상태 수정만 직렬화하며 live/WS lock과 공유하지 않습니다.
def v220_serialized(fn):
    @wraps(fn)
    def locked(*args, **kwargs):
        with V220_LOCK:
            return fn(*args, **kwargs)
    return locked

# 함수 설명: tuple dictionary key를 포함한 연구 상태를 손실 없이 JSON 변환합니다.
def v220_pack(value):
    if isinstance(value, datetime): return {'t': 'dt', 'v': value.isoformat()}
    if isinstance(value, dict): return {'t': 'dict', 'v': [[v220_pack(k), v220_pack(v)] for k,v in list(value.items())]}
    if isinstance(value, (set, tuple, list)):
        return {'t': type(value).__name__, 'v': [v220_pack(v) for v in list(value)]}
    if isinstance(value, float) and not math.isfinite(value): return None
    return value

# 함수 설명: 저장된 타입과 날짜를 엄격히 복원하고 손상된 값은 예외로 처리합니다.
def v220_unpack(value):
    if not isinstance(value, dict): return value
    typ, raw = value['t'], value['v']
    if typ == 'dt': return datetime.fromisoformat(raw)
    if typ == 'dict': return {v220_unpack(k): v220_unpack(v) for k,v in raw}
    values = [v220_unpack(v) for v in raw]
    if typ == 'set': return set(values)
    if typ == 'tuple': return tuple(values)
    if typ == 'list': return values
    raise ValueError('unknown recovery type: ' + str(typ))

# 함수 설명: 후보/진입원장/알림 예약을 atomic 저장하며 실패 시 신규 연구진입만 중단합니다.
@v220_serialized
def v220_checkpoint(force=False):
    global v220_last_checkpoint, v220_halted
    if not force and time.monotonic() - v220_last_checkpoint < RESEARCH_CHECKPOINT_INTERVAL_SEC:
        return True
    tmp = None
    try:
        payload = {'schema': 1, 'date': v220_date, 'candidates': v220_candidates,
                   'signals': v220_signals, 'outbox': v220_outbox, 'fill_keys': v220_fill_keys,
                   'research': {k: globals()[k] for k in V220_STATE_GLOBALS}}
        data = v220_pack(payload)
        path = Path(V220_STATE_FILE).resolve()
        fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, allow_nan=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path); tmp = None
        v220_last_checkpoint = time.monotonic()
        return True
    except Exception as exc:
        v220_halted = True
        v220_metrics['save_failures'] += 1
        log(f'[v2.2.0 연구 신규진입 중단] 상태저장 실패 / {exc}')
        return False
    finally:
        if tmp and os.path.exists(tmp): os.unlink(tmp)

# 함수 설명: 신규 날짜 원장을 초기화합니다. 기존 날짜 상태는 덮어쓰기 전에 정상 종료합니다.
@v220_serialized
def v220_reset_day(moment=None):
    global v220_date, v220_halted
    moment = moment or datetime.now()
    v220_date = moment.strftime('%Y-%m-%d')
    v220_candidates.clear(); v220_outbox.clear(); v220_fill_keys.clear()
    for mode in V220_MODES: v220_signals[mode] = {}
    v220_halted = False

# 함수 설명: 재시작 시 동일 날짜 원장/열린 grid를 복구하고 미관측 구간은 지지로 세지 않습니다.
@v220_serialized
def v220_restore(moment=None):
    global v220_date, v220_halted
    moment = moment or datetime.now()
    v220_reset_day(moment)
    path = Path(V220_STATE_FILE)
    if not path.exists():
        v220_recover_signal_ledger()
        return False
    try:
        payload = v220_unpack(json.loads(path.read_text(encoding='utf-8')))
        if payload['schema'] != 1: raise ValueError('unsupported schema')
        if payload['date'] != v220_date: return False
        v220_candidates.update(payload['candidates'])
        v220_signals.update(payload['signals']); v220_outbox.update(payload['outbox'])
        v220_fill_keys.update(payload.get('fill_keys', set()))
        for key in V220_STATE_GLOBALS: globals()[key] = payload['research'][key]
        # 이미 CSV에 확정 저장된 청산은 과거 checkpoint에서 다시 OPEN으로 부활시키지 않습니다.
        if Path(PAPER_TRADE_FILE).exists():
            with open(PAPER_TRADE_FILE, encoding='utf-8-sig', newline='') as f:
                for row in csv.DictReader(f):
                    p = paper_positions.get(row.get('trade_id'))
                    if p and row.get('strategy') in p['strategies']:
                        p['strategies'][row['strategy']].update(status='CLOSED', result=row.get('result'),
                            exit_price=safe_float(row.get('exit_price')), exit_time=datetime.fromisoformat(row['exit_time']))
        for tid, p in list(paper_positions.items()):
            p['recovery_status'] = 'RECOVERY_PARTIAL_PRICE_GAP'
            if all(s.get('status') == 'CLOSED' for s in p['strategies'].values()):
                paper_positions.pop(tid); paper_position_ids_by_code.get(p['stock_code'], set()).discard(tid)
        v220_recover_signal_ledger()
        for c in v220_candidates.values():
            v220_cancel_pending(c, 'NO_FILL_RESTART')
            c['bar'] = None; c['history'] = []; c['last_seq'] = None; c['next_bar_partial'] = True
            c['support_count'] = 0; c['confirmed_at'] = None; c['support_candidate_time'] = None
            c['state'] = 'PULLBACK' if c.get('low') else 'PEAK'
            c['data_status'] = 'RECOVERY_PARTIAL'
        for item in v220_outbox.values():
            if item['status'] == 'IN_FLIGHT': item['status'] = 'DELIVERY_UNKNOWN'
        log('[v2.2.0 복구] 당일 신호·grid 복구 / 미관측 구간 RECOVERY_PARTIAL / 알림 불명확 재전송 금지')
        return True
    except Exception as exc:
        v220_halted = True
        raise RuntimeError(f'v2.2.0 복구 실패: 상태파일을 보존하고 원인을 확인하세요: {exc}') from exc

# 함수 설명: 신규 연구진입 gate를 중앙에서 확인해 OFF 전략과 중복 신규진입을 차단합니다.
def v220_entry_allowed(stock, mode, meta=None):
    label = 'FIRST_75_PASS' if mode == 'PRE_HISTORY' and (meta or {}).get('pre_entry_type', stock.get('pre_entry_type')) == 'FIRST_75_PASS' else mode
    if mode == 'PRE_HISTORY' and label != 'FIRST_75_PASS': return False
    if label in V220_OFF_MODES: return False
    if label in V220_MODES and (shutdown_requested or v220_halted): return False
    if label in V220_NEW_MODES:
        if EXECUTION_MODE != 'RESEARCH' or AUTO_TRADE_ENABLED or USE_MOCK: return False
        c = v220_candidates.get(clean_stock_code(stock.get('stock_code')), {})
        if label in c.get('entered', {}) or (clean_stock_code(stock.get('stock_code')), label) in v220_fill_keys: return False
    return True

# 함수 설명: 신호·체결 메타를 고정 스키마로 저장하고 누락 시 신규 연구진입을 중단합니다.
def v220_emit(c, mode, event, meta, trade_id=''):
    global v220_halted
    row = {'date': v220_date, 'version': STRATEGY_VERSION, 'event_id': f'{v220_date}:{c["code"]}:{mode}:{meta.get("support_episode_id", "")}:{meta.get("signal_time", "")}:{event}',
           'event': event, 'strategy': mode, 'trade_id': trade_id,
           'stock_code': c['code'], 'stock_name': c['stock']['stock_name']}
    row.update({k: _csv_datetime(meta.get(k, '')) if isinstance(meta.get(k), datetime) else meta.get(k, '') for k in V220_META_COLUMNS})
    if not enqueue_research_rows(V220_SIGNAL_FILE, [row], 'P1', V220_SIGNAL_COLUMNS, 'V220_SIGNAL'):
        v220_halted = True
        log('[v2.2.0 연구 신규진입 중단] 신호 원장 queue 저장 실패')

# 함수 설명: 기존 전략의 실제 생성 시점에 후보 등록·출처 승격·최초 신호 알림을 연결합니다.
@v220_serialized
def v220_on_legacy_entry(stock, mode, tid, meta=None):
    label = 'FIRST_75_PASS' if mode == 'PRE_HISTORY' and (meta or {}).get('pre_entry_type') == 'FIRST_75_PASS' else mode
    if label not in V220_MODES[:2]: return
    now = _stock_score_time(stock)
    if not v220_date: v220_reset_day(now)
    code = clean_stock_code(stock['stock_code'])
    c = v220_candidates.get(code)
    if c is None:
        c = {'code': code, 'stock': copy.deepcopy(stock), 'candidate_start_time': now,
             'sources': set(), 'parent_trade_ids': [], 'bar': None, 'history': [], 'last_seq': None,
             'state': 'CANDIDATE', 'high': None, 'peak_time': None, 'low': None, 'anchor': None,
             'low_time': None, 'pullback_start_time': None, 'support_count': 0, 'confirmed_at': None,
             'support_candidate_time': None, 'episode': 0, 'entered': {}, 'pending': {},
             'data_status': 'WARMUP', 'base_high': None, 'base_low': None, 'base_duration': 0,
             'support_retest_count': 0, 'reclaim_volume_ratio': None, 'prior_5m_high': None}
        v220_candidates[code] = c
    c['sources'].add(label)
    c['candidate_source'] = 'BOTH' if len(c['sources']) == 2 else label
    key = 'base_signal_time' if label == 'BASE' else 'first75_signal_time'
    c.setdefault(key, now)
    if tid not in c['parent_trade_ids']: c['parent_trade_ids'].append(tid)
    if code not in v220_signals[label]:
        v220_signals[label][code] = {'time': now, 'name': stock['stock_name'], 'trade_id': tid}
        v220_queue_alert(stock, label, {'signal_time': now, 'fill_time': paper_positions[tid]['entry_time'], 'fill_price': paper_positions[tid]['entry_price']})
    v220_checkpoint(True)

# 함수 설명: 현재 후보의 판정근거 snapshot을 만들어 이후 가격으로 덮어쓰지 않습니다.
def v220_meta(c, bar, detected):
    low = c.get('low')
    return {'candidate_source': c['candidate_source'], 'candidate_start_time': c['candidate_start_time'],
        'base_signal_time': c.get('base_signal_time', ''), 'first75_signal_time': c.get('first75_signal_time', ''),
        'parent_trade_ids': '|'.join(c['parent_trade_ids']), 'support_episode_id': f'{v220_date}:{c["code"]}:{c["episode"]}',
        'peak_time': c.get('peak_time'), 'peak_price': c.get('high'), 'pullback_start_time': c.get('pullback_start_time'),
        'pullback_depth_pct': (low / c['high'] - 1) * 100 if low and c.get('high') else None,
        'support_low_time': c.get('low_time'), 'support_low_price': low, 'support_anchor_low': c.get('anchor'),
        'support_candidate_time': c.get('support_candidate_time'), 'support_confirm_time': c.get('confirmed_at'),
        'support_elapsed_min': c['support_count'], 'rebound_from_low_pct': (bar['close']/low-1)*100 if low else None,
        'higher_low': c.get('higher_low'), 'prior_5m_high': c.get('prior_5m_high'),
        'reclaim_threshold_price': c['prior_5m_high']*(1+PULLBACK_RECLAIM_BUFFER_PCT/100) if c.get('prior_5m_high') else None,
        'reclaim_signal_time': c.get('reclaim_signal_time'), 'reclaim_volume_ratio': c.get('reclaim_volume_ratio'),
        'signal_time': bar['minute'] + timedelta(minutes=1), 'signal_detected_time': detected,
        'signal_price': bar['close'], 'rule_version': PULLBACK_RULE_VERSION, 'data_status': c['data_status']}

# 함수 설명: SUPPORT/RECLAIM을 일간 신호원장에 등록하고 다음 수신가격을 기다립니다.
def v220_signal(c, mode, bar, detected):
    if mode in c['entered'] or (c['code'], mode) in v220_fill_keys or mode in c['pending'] or v220_halted: return
    enabled = PULLBACK_SUPPORT_ENABLED if mode == V220_NEW_MODES[0] else PULLBACK_RECLAIM_ENABLED
    if not enabled: return
    meta = v220_meta(c, bar, detected)
    c['pending'][mode] = meta
    v220_signals[mode].setdefault(c['code'], {'time': meta['signal_time'], 'name': c['stock']['stock_name'], 'trade_id': ''})
    v220_emit(c, mode, 'SIGNAL', meta)
    v220_checkpoint(True)

# 함수 설명: 신호 후 체결 가능한 가격이 없거나 지지가 무효화되면 미체결 사유를 보존합니다.
def v220_cancel_pending(c, reason):
    for mode, meta in list(c['pending'].items()):
        v220_emit(c, mode, reason, meta)
        v220_queue_alert(c['stock'], mode, dict(meta, fill_status=reason))
    c['pending'].clear()

# 함수 설명: 완료봉만 사용해 지지 상태를 전이하고 현재봉을 직전 고점 계산에서 제외합니다.
def v220_complete_bar(c, bar, detected):
    v220_metrics['bars'] += 1
    previous = c['history']
    contiguous = not previous or bar['minute'] - previous[-1]['minute'] == timedelta(minutes=1)
    valid = bar.get('valid', True) and contiguous
    if not valid:
        v220_metrics['invalid_bars'] += 1
        v220_cancel_pending(c, 'NO_FILL_DATA_GAP')
        c['support_count'] = 0; c['confirmed_at'] = None; c['support_candidate_time'] = None
        c['state'] = 'PULLBACK' if c['low'] else 'PEAK'
        c['history'] = []; c['data_status'] = 'DATA_UNAVAILABLE'
    else:
        c['data_status'] = 'OK'
        # 현재봉의 high 뒤에 low가 발생했는지 OHLC만으로 알 수 없으므로,
        # 새로운 고점 봉에서는 PEAK만 갱신하고 다음 완료봉부터 눌림을 평가합니다.
        new_peak = c['high'] is None or bar['high'] > c['high']
        if new_peak:
            c['high'] = bar['high']; c['peak_time'] = bar['minute']
            if not c['entered']:
                v220_cancel_pending(c, 'NO_FILL_NEW_PEAK')
                c.update(low=None, anchor=None, support_count=0, confirmed_at=None,
                    support_candidate_time=None, state='PEAK', pullback_start_time=None,
                    base_duration=0, base_high=None, base_low=None, support_retest_count=0)
        if not new_peak or c['entered']:
            if c['low'] is None and bar['low'] <= c['high'] * (1-PULLBACK_START_PCT/100) + 1e-9:
                c['episode'] += 1
                c.update(low=bar['low'], anchor=bar['low'], low_time=bar['minute'],
                    pullback_start_time=bar['minute'], state='PULLBACK', support_count=0)
            elif c['low'] is not None:
                if bar['low'] < c['low']:
                    c['low'] = bar['low']; c['low_time'] = bar['minute']
                if bar['low'] < c['anchor'] * (1-PULLBACK_BREAK_TOLERANCE_PCT/100) - 1e-9:
                    v220_cancel_pending(c, 'NO_FILL_SUPPORT_BREAK')
                    c.update(anchor=bar['low'], support_count=0, confirmed_at=None,
                        support_candidate_time=None, state='PULLBACK', base_duration=0,
                        base_high=None, base_low=None, support_retest_count=0)
                else:
                    c['support_count'] += 1
                    c['higher_low'] = bool(previous and bar['low'] > previous[-1]['low'])
                    if bar['low'] <= c['anchor']: c['support_retest_count'] += 1
                    if c['support_count'] >= PULLBACK_CANDIDATE_BARS and c['confirmed_at'] is None:
                        c['state'] = 'SUPPORT_CANDIDATE'
                        if c['support_candidate_time'] is None: c['support_candidate_time'] = bar['minute'] + timedelta(minutes=1)
                    confirmed_before = c['confirmed_at'] is not None
                    if (not confirmed_before and c['support_count'] >= PULLBACK_CONFIRM_BARS
                            and bar['close'] >= c['low']*(1+PULLBACK_RECOVERY_PCT/100)-1e-9):
                        c['confirmed_at'] = bar['minute'] + timedelta(minutes=1)
                        c['state'] = 'SUPPORT_CONFIRMED'
                        v220_signal(c, V220_NEW_MODES[0], bar, detected)
                    if confirmed_before:
                        c['state'] = 'PULLBACK_BASE'; c['base_duration'] += 1
                        c['base_high'] = max(c['base_high'] or bar['high'], bar['high'])
                        c['base_low'] = min(c['base_low'] or bar['low'], bar['low'])
                        lookback = previous[-PULLBACK_RECLAIM_BARS:]
                        c['prior_5m_high'] = max(x['high'] for x in lookback) if len(lookback) == PULLBACK_RECLAIM_BARS else None
                        volumes = [b['volume'] for b in previous[-10:] if b.get('volume') is not None]
                        denom = median(volumes) if len(volumes) == 10 else None
                        c['reclaim_volume_ratio'] = bar['volume']/denom if denom and bar.get('volume') is not None else None
                        if c['prior_5m_high'] and bar['close'] >= c['prior_5m_high']*(1+PULLBACK_RECLAIM_BUFFER_PCT/100)-1e-9:
                            c['state'] = 'RECLAIM_CONFIRMED'; c['reclaim_signal_time'] = bar['minute'] + timedelta(minutes=1)
                            v220_signal(c, V220_NEW_MODES[1], bar, detected)
    meta = v220_meta(c, bar, detected)
    row = {'date': v220_date, 'version': STRATEGY_VERSION, 'stock_code': c['code'],
        'stock_name': c['stock']['stock_name'], **{k: bar.get(k) for k in ('minute','open','high','low','close','volume','tick_count')},
        'current_state': c['state'], 'running_high': c['high'], 'raw_pullback_low': c['low'],
        'pullback_pct': (bar['low']/c['high']-1)*100 if c['high'] else None,
        'base_duration': c['base_duration'], 'base_high': c['base_high'], 'base_low': c['base_low'],
        'base_range_pct': (c['base_high']/c['base_low']-1)*100 if c['base_low'] else None,
        'support_retest_count': c['support_retest_count'],
        'minute_aggregation_delay_ms': max(0, (detected-meta['signal_time']).total_seconds()*1000), **meta}
    row = {k: _csv_datetime(v) if isinstance(v, datetime) else v for k,v in row.items()}
    if not enqueue_research_rows(V220_MINUTE_FILE, [row], 'P1', V220_MINUTE_COLUMNS, 'V220_1M'):
        c['data_status'] = 'WRITE_UNAVAILABLE'
        v220_cancel_pending(c, 'NO_FILL_WRITE_UNAVAILABLE')
        c['support_count'] = 0; c['confirmed_at'] = None; c['history'] = []
    elif valid:
        c['history'].append(bar); c['history'] = c['history'][-11:]

# 함수 설명: 신호 확정 뒤 다음 실제 수신 tick으로만 가상체결하고 같은 날 재진입을 막습니다.
def v220_fill_pending(c, price, now):
    for mode, meta in list(c['pending'].items()):
        if now <= meta['signal_detected_time']: continue
        signal_session = get_session_at(meta['signal_detected_time'])
        if (shutdown_requested or not (PROGRAM_START <= now.strftime('%H:%M') < PROGRAM_END)
                or get_session_at(now) == 'WAIT' or get_session_at(now) != signal_session):
            v220_cancel_pending(c, 'NO_FILL_SESSION_END'); return
        if v220_halted: return
        stock = copy.deepcopy(c['stock'])
        stock.update(current_price=meta['signal_price'], score_time=meta['signal_time'],
            _score_evaluated_ts=meta['signal_time'].timestamp(), decision_time=meta['signal_time'],
            scan_session=get_session_at(meta['signal_time']), watch_episode_id=meta['support_episode_id'])
        entry_meta = dict(meta, strategy_name=mode, strategy_family='PULLBACK', grid_family='LEGACY_169',
            strategy_status='신규/ON', fill_time=now, fill_price=price,
            signal_to_fill_sec=(now-meta['signal_time']).total_seconds(),
            signal_to_fill_slippage_pct=(price/meta['signal_price']-1)*100)
        tid = open_paper_trade(stock, mode, entry_meta, exit_strategies=EXIT_STRATEGIES,
            entry_slippage_pct=0.0, forced_entry_time=now, forced_entry_price=price)
        if not tid:
            v220_queue_alert(stock, mode, dict(entry_meta, fill_status='NO_FILL_ENTRY_REJECTED'))
            v220_emit(c, mode, 'NO_FILL_ENTRY_REJECTED', entry_meta)
            c['pending'].pop(mode, None); continue
        c['entered'][mode] = tid; c['pending'].pop(mode, None)
        v220_fill_keys.add((c['code'], mode))
        p = paper_positions[tid]
        p.update(last_price=price, max_price=price, min_price=price)
        v220_signals[mode][c['code']]['trade_id'] = tid
        v220_emit(c, mode, 'FILL', entry_meta, tid)
        v220_queue_alert(stock, mode, entry_meta)
        v220_checkpoint(True)

# 함수 설명: 연구 worker에서 수신순서/누락을 검사하고 1분 OHLCV를 집계합니다.
@v220_serialized
def v220_on_tick(code, price, now, values=None, sequence=None):
    c = v220_candidates.get(code)
    if c is None or now.strftime('%Y-%m-%d') != v220_date or shutdown_requested: return
    if now < c['candidate_start_time']: return
    if not (PROGRAM_START <= now.strftime('%H:%M') < PROGRAM_END) or get_session_at(now) == 'WAIT':
        v220_cancel_pending(c, 'NO_FILL_SESSION_END'); return
    v220_metrics['ticks'] += 1
    gap = sequence is not None and c['last_seq'] is not None and sequence != c['last_seq'] + 1
    if sequence is not None and c['last_seq'] is not None and sequence <= c['last_seq']: return
    c['last_seq'] = sequence
    minute = now.replace(second=0, microsecond=0)
    bar = c['bar']
    if bar and minute < bar['minute']: return
    if gap:
        v220_metrics['gaps'] += 1
        v220_cancel_pending(c, 'NO_FILL_DATA_GAP')
        if bar: bar['valid'] = False
        c['support_count'] = 0; c['confirmed_at'] = None; c['support_candidate_time'] = None
        c['history'] = []; c['state'] = 'PULLBACK' if c['low'] else 'PEAK'
    # 이전 tick에서 확정한 신호만 체결: rollover tick으로 과거 종가 체결하지 않습니다.
    v220_fill_pending(c, price, now)
    values = values or {}
    raw_volume = values.get('15')
    volume = abs(safe_float(raw_volume)) if raw_volume not in (None, '') else None
    if bar and minute > bar['minute']:
        v220_complete_bar(c, bar, max(now, datetime.now()))
        bar = None
    if bar is None:
        partial = c.pop('next_bar_partial', False) or minute <= c['candidate_start_time'].replace(second=0, microsecond=0)
        c['bar'] = {'minute': minute, 'open': price, 'high': price, 'low': price,
            'close': price, 'volume': volume, 'tick_count': 1, 'valid': not partial and not gap}
    else:
        bar['high'] = max(bar['high'], price); bar['low'] = min(bar['low'], price); bar['close'] = price
        bar['volume'] = bar['volume'] + volume if volume is not None and bar['volume'] is not None else None
        bar['tick_count'] += 1
    v220_checkpoint()

# 함수 설명: N/A를 안전 표시하고 부모 후보 본문의 모든 정보 항목을 유지합니다.
def v220_fmt(value, spec='.2f', suffix=''):
    try:
        number = float(value)
        return format(number, spec) + suffix if math.isfinite(number) else 'N/A'
    except (TypeError, ValueError): return 'N/A'

# 함수 설명: 추가 REST 없이 기존 snapshot과 실제 판정 메타로 개별 메시지를 만듭니다.
def v220_alert_text(stock, mode, meta=None):
    meta = meta or {}
    f = v220_fmt
    def clock(value):
        return value.strftime('%H:%M:%S') if isinstance(value, datetime) else (str(value) if value else 'N/A')
    actual = safe_float(stock.get('actual_trading_value'))/100_000_000 if stock.get('actual_trading_value') not in (None, '') else None
    est = safe_float(stock.get('estimated_trading_value'))/100_000_000 if stock.get('estimated_trading_value') not in (None, '') else None
    lines = [f'[{mode}]', f'🚨 단타 후보 [{stock.get("decision_session", "N/A")}]',
        f'{stock.get("stock_name", "N/A")} ({stock.get("stock_code", "N/A")})',
        f'NXT : {nxt_eligibility_cache.get(stock.get("stock_code"), "N/A (미조회)")}',
        f'현재가 : {f(stock.get("current_price"), ",.0f", "원")}',
        f'등락률 : {f(stock.get("change_rate"), "+.2f", "%")}',
        f'거래량 : {f(stock.get("volume"), ",.0f", "주")}',
        f'실제 거래대금 : {f(actual, ",.1f", "억원")}', f'추정 거래대금 : {f(est, ",.1f", "억원")}',
        f'거래대금 구분 : {stock.get("trading_value_source", "N/A")}',
        f'당일고가 : {f(stock.get("day_high"), ",.0f", "원")}',
        f'고점대비 : {f(-safe_float(stock["high_gap"]) if stock.get("high_gap") is not None else None, ".2f", "%")}',
        f'거래대금 증가 : {f(stock.get("value_growth"), ".3f", "배")}',
        f'거래량 증가 : {f(stock.get("volume_growth"), ".3f", "배")}',
        f'점수 : {stock.get("score", "N/A")} / 100',
        f'점수 세부 : {stock.get("score_detail", {})}', f'WATCH : {WATCH_SCORE}점+',
        f'HISTORY : {f(stock.get("history_available_sec"), ".0f", "초")}',
        f'30초 가격 : {f(stock.get("price_change_30s"), "+.2f", "%")}',
        f'60초 가격 : {f(stock.get("price_change_60s"), "+.2f", "%")}',
        f'60초 고점이격 변화 : {f(stock.get("high_gap_change_60s"), "+.2f", "%p")}',
        f'운영모드 : {EXECUTION_MODE}', f'분류 : {"⭐ FOCUS 조건" if is_focus_signal(stock) else "일반 신호"}']
    if mode in V220_NEW_MODES:
        lines.insert(2, '※ 공통본문은 원본 후보 관측값 / 아래 판정값은 신규 신호 시점')
        labels = [('원본후보','candidate_source'), ('원본후보 발생시각','candidate_start_time'),
            ('고점','peak_price'), ('고점시각','peak_time'), ('눌림저점','support_low_price'),
            ('저점시각','support_low_time'), ('최대눌림','pullback_depth_pct'),
            ('저점대비 회복','rebound_from_low_pct'), ('지지 지속','support_elapsed_min'),
            ('Higher Low','higher_low'), ('직전 5분 고점','prior_5m_high'),
            ('Reclaim 기준가격','reclaim_threshold_price'), ('Reclaim 가격','signal_price'), ('거래량비','reclaim_volume_ratio')]
        lines += [f'{label} : {clock(meta.get(key))}' for label,key in labels]
        lines += [f'지지 허용범위 : {PULLBACK_BREAK_TOLERANCE_PCT:.2f}%',
            f'Reclaim 기준 : 직전 {PULLBACK_RECLAIM_BARS}분 고점 +{PULLBACK_RECLAIM_BUFFER_PCT:.2f}%',
            '진입판정 : ' + ('SUPPORT_CONFIRMED' if mode == V220_NEW_MODES[0] else 'RECLAIM_CONFIRMED')]
    lines += [f'신호시각 : {clock(meta.get("signal_time"))}', f'가상진입시각 : {clock(meta.get("fill_time"))}',
        f'가상진입가 : {f(meta.get("fill_price"), ",.2f", "원")}', f'체결상태 : {meta.get("fill_status", "FILLED")}']
    return '\n'.join(lines)

# 함수 설명: Telegram 제한을 넘지 않도록 줄 경계로 분할합니다.
def v220_message_parts(text, limit=3500):
    parts, buf = [], ''
    for line in text.splitlines():
        while len(line) > limit:
            if buf: parts.append(buf); buf = ''
            parts.append(line[:limit]); line = line[limit:]
        if len(buf)+len(line)+1 > limit:
            parts.append(buf); buf = ''
        buf += ('\n' if buf else '') + line
    if buf: parts.append(buf)
    return parts

# 함수 설명: 개별 전략 알림을 네트워크와 분리된 outbox에 예약합니다.
def v220_queue_alert(stock, mode, meta):
    key = f'ENTRY:{v220_date}:{mode}:{stock["stock_code"]}:{meta.get("signal_time")}'
    v220_outbox.setdefault(key, {'parts': v220_message_parts(v220_alert_text(stock, mode, meta)),
        'status': 'PENDING', 'next_part': 0})

# 함수 설명: 매시 30분 기준 당시까지의 최초 신호만 정렬한 누적목록을 만듭니다.
def v220_summary_text(cutoff):
    lines = [f'📋 전략별 누적 후보 — {cutoff:%H:%M} 기준']
    for mode in V220_MODES:
        lines += ['', '[' + mode.replace('_', ' ') + ']']
        entries = [(code, v) for code,v in v220_signals[mode].items() if v['time'] <= cutoff]
        entries.sort(key=lambda x: (x[1]['time'], x[0]))
        lines += [f'{i}. {v["name"]}({code}) - {v["time"]:%H:%M:%S}' for i,(code,v) in enumerate(entries,1)] or ['없음']
    return '\n'.join(lines + ['', f'기준시각 : {cutoff:%Y-%m-%d %H:%M}', '※ 당일 누적 / 전략별 동일종목 1회 표시'])

# 함수 설명: 현재까지 도래한 기준시각을 영속 키로 예약해 loop와 재시작 중복을 막습니다.
@v220_serialized
def v220_schedule_summaries(now=None):
    now = now or datetime.now()
    if not V220_SUMMARY_ENABLED or now.strftime('%Y-%m-%d') != v220_date: return
    changed = False
    for hhmm in V220_SUMMARY_TIMES:
        cutoff = datetime.combine(now.date(), _hhmm_time(hhmm))
        key = f'SUMMARY:{v220_date}:{hhmm}'
        if now >= cutoff and key not in v220_outbox:
            v220_outbox[key] = {'parts': v220_message_parts(v220_summary_text(cutoff)), 'status': 'PENDING', 'next_part': 0}
            changed = True
    if changed: v220_checkpoint(True)

# 함수 설명: 저장된 알림만 전송하며 응답 불명확은 자동 재전송하지 않습니다.
def v220_notify_once():
    with V220_LOCK:
        entry = next(((k,v) for k,v in v220_outbox.items() if v['status'] == 'PENDING'), None)
        if entry is None: return False
        key, item = entry; item['status'] = 'IN_FLIGHT'
        if not v220_checkpoint(True): return False
        part = item['parts'][item['next_part']]
    try: ok = send_telegram(part)
    except Exception as exc:
        ok = False; log(f'[v2.2.0 Telegram 실패] {exc}')
    with V220_LOCK:
        if v220_outbox.get(key) is not item: return False
        if ok:
            item['next_part'] += 1
            item['status'] = 'SENT' if item['next_part'] == len(item['parts']) else 'PENDING'
        else: item['status'] = 'DELIVERY_UNKNOWN'
        v220_checkpoint(True)
    return ok

# 함수 설명: 저우선 알림 worker에서만 HTTP 발송합니다.
def v220_notify_loop():
    while not v220_notify_stop.wait(0.2):
        try: v220_notify_once()
        except Exception as exc: log(f'[v2.2.0 알림 worker 격리] {exc}')

# 함수 설명: 복구 후보 구독 및 알림 worker를 한 번만 시작합니다.
def v220_start():
    global v220_notify_thread
    with V220_LOCK:
        codes = set(v220_candidates) | set(paper_position_ids_by_code)
    if websocket_manager is not None:
        for code in codes: websocket_manager.subscribe_stock(code, get_session())
    v220_notify_stop.clear()
    if not v220_notify_thread or not v220_notify_thread.is_alive():
        v220_notify_thread = threading.Thread(target=v220_notify_loop, name='ResearchTelegram220', daemon=True)
        v220_notify_thread.start()

# 함수 설명: 장 경계에서 미체결 신호와 완료봉을 기록하고 후보 구독을 유지/해제합니다.
@v220_serialized
def v220_maintenance(now=None, ending=False):
    now = now or datetime.now()
    v220_schedule_summaries(now)
    for c in v220_candidates.values():
        bar = c.get('bar')
        if (ending or get_session_at(now) == 'WAIT') and bar:
            if now >= bar['minute'] + timedelta(minutes=1): v220_complete_bar(c, bar, now)
            c['bar'] = None
        if ending or get_session_at(now) == 'WAIT': v220_cancel_pending(c, 'NO_FILL_SESSION_END')
    if ending: v220_checkpoint(True)
    else: v220_checkpoint()
    v220_record_metrics(now)

# 함수 설명: 새 전략 설정과 기존 보존 grid를 실행 전에 확인합니다.
def validate_v220_config():
    if EXECUTION_MODE != 'RESEARCH' or AUTO_TRADE_ENABLED or USE_MOCK:
        raise ValueError('v2.2.0은 RESEARCH 전용입니다. 실제·모의주문 승인이 없습니다.')
    if not WEBSOCKET_ENABLED and not OFF_HOURS_VALIDATION_MODE:
        raise ValueError('눌림 1분봉 수집에는 WebSocket이 필요합니다.')
    if not (0 < PULLBACK_START_PCT and 0 < PULLBACK_BREAK_TOLERANCE_PCT and 0 < PULLBACK_RECOVERY_PCT
            and 0 < PULLBACK_CANDIDATE_BARS < PULLBACK_CONFIRM_BARS and PULLBACK_RECLAIM_BARS > 0):
        raise ValueError('눌림 파라미터 범위를 확인하세요.')
    if len(EXIT_STRATEGIES) != 169: raise ValueError('169-grid가 필요합니다.')
    _validate_selected_exit_strategies(EXIT_STRATEGIES)
    return True

# 함수 설명: 종료 시 신규 tick을 막은 뒤 연구 queue drain과 알림 worker 종료를 확인합니다.
def v220_quiesce():
    if websocket_manager is not None: websocket_manager.stop()
    deadline = time.monotonic() + RESEARCH_FLUSH_TIMEOUT_SEC
    while research_tick_queue.unfinished_tasks and time.monotonic() < deadline:
        time.sleep(0.02)
    if research_tick_queue.unfinished_tasks:
        log(f'[v2.2.0 종료 연구잔여] {research_tick_queue.unfinished_tasks} ticks / RECOVERY_PARTIAL')
    v220_notify_stop.set()
    if v220_notify_thread: v220_notify_thread.join(HTTP_TIMEOUT + 1)


# 함수 설명: 후보/grid 수와 queue/분봉 처리지연을 낮은 빈도로 기록합니다.
@v220_serialized
def v220_record_metrics(now=None):
    global v220_last_metrics
    now = now or datetime.now()
    if time.monotonic() - v220_last_metrics < RESEARCH_LOAD_SUMMARY_INTERVAL_SEC: return
    v220_last_metrics = time.monotonic()
    row = {'datetime': _csv_datetime(now), 'version': STRATEGY_VERSION,
           'candidate_count': len(v220_candidates),
           'open_strategy_count': sum(sum(s.get('status') == 'OPEN' for s in p['strategies'].values()) for p in paper_positions.values()),
           'tick_queue_backlog': research_tick_queue.qsize(), 'writer_queue_backlog': research_write_queue.qsize(),
           'pending_notifications': sum(v['status']=='PENDING' for v in v220_outbox.values()),
           'unknown_notifications': sum(v['status']=='DELIVERY_UNKNOWN' for v in v220_outbox.values()),
           'halted': v220_halted, **v220_metrics}
    enqueue_research_rows(V220_METRICS_FILE, [row], 'P2', list(row), 'V220_METRICS')


# 함수 설명: WebSocket 재접속 경계를 sequence 공백으로 표시해 누락봉 지지판정을 막습니다.
def v220_mark_stream_gap():
    for code in list(v220_tick_sequences):
        v220_tick_sequences[code] += 1


# 함수 설명: checkpoint보다 먼저 저장된 신호/FILL 원장도 대조해 재시작 중복진입을 막습니다.
def v220_recover_signal_ledger():
    path = Path(V220_SIGNAL_FILE)
    if not path.exists(): return
    with path.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            if row.get('date') != v220_date or row.get('strategy') not in V220_NEW_MODES: continue
            code, mode = clean_stock_code(row['stock_code']), row['strategy']
            if row.get('signal_time'):
                stamp = datetime.fromisoformat(row['signal_time'])
                old = v220_signals[mode].get(code)
                if old is None or stamp < old['time']:
                    v220_signals[mode][code] = {'time': stamp, 'name': row.get('stock_name',code), 'trade_id': row.get('trade_id','')}
            if row.get('event') == 'FILL':
                v220_fill_keys.add((code, mode))
                c = v220_candidates.get(code)
                if c: c['entered'][mode] = row.get('trade_id','RECOVERED_FILL')
                if row.get('trade_id') not in paper_trade_registry:
                    log(f'[RECOVERY_PARTIAL] {code}/{mode}: FILL 원장은 있으나 grid checkpoint 없음; 재진입 차단')
