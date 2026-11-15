# v2.3.5 opportunity engine. Embedded into the program cell by build_v235.py.
# No broker/order API is referenced by this engine.
import zipfile
import statistics

V235_A = 'OPENING_FLOW_CONTINUATION'
V235_B = 'OPENING_FAILED_BREAKDOWN_RECLAIM'
V235_NAMES = {V235_A: '장초반 수급 지속', V235_B: '초반 하락 실패 후 회복'}
V235_LOCK = threading.RLock()
v235_engine = None
v235_queue = queue.Queue(maxsize=20000)
v235_drops = set()
v235_thread = None
v235_master_future = None
v235_summary_keys = set()

# 함수 설명: ISO 시각을 읽고 로컬 운영시각은 KST인지 별도로 강제합니다.
def v235_dt(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value

# 함수 설명: 유한 숫자만 허용하며 결측을 0으로 바꾸지 않습니다.
def v235_num(value):
    try:
        result = float(str(value).replace(',', ''))
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None

# 함수 설명: 보통주 가격대별 다음/직전 유효 호가를 경계까지 계산합니다.
def v235_tick_price(price, direction=1):
    levels = ((2000, 1), (5000, 5), (20000, 10), (50000, 50),
              (200000, 100), (500000, 500), (float('inf'), 1000))
    p = int(price)
    for limit, step in levels:
        if p < limit:
            break
    if direction > 0:
        return (p // step + 1) * step
    for limit, step in levels:
        if p - 1 < limit:
            return ((p - 1) // step) * step

# 함수 설명: 상태와 이벤트가 같은 SQLite transaction에서 확정되는 내부 연구 원장입니다.
class Opportunity235:
    # 함수 설명: 실험 설정을 검증하고 일자별 상태·미결거래·구독·알림을 복원합니다.
    def __init__(self, path, now, config=None):
        self.config = copy.deepcopy(config or V235_CONFIG)
        self.path = str(path)
        self.halted = False
        self.db = sqlite3.connect(self.path, timeout=2, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS state(day TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY, day TEXT, stream TEXT, kind TEXT, at TEXT, code TEXT, payload TEXT)')
        if self.db.execute('PRAGMA quick_check').fetchone() != ('ok',):
            raise RuntimeError('opportunity ledger integrity')
        self.day = now.date().isoformat()
        record = self.db.execute('SELECT payload FROM state WHERE day=?', (self.day,)).fetchone()
        self.s = json.loads(record[0]) if record else dict(candidates={}, accounts={}, indexes={}, master={}, subscriptions={}, outbox={}, serial=0)
        for policy in ('UNFILTERED', 'INDEX_UP'):
            for delay in (0, 1, 3, 5):
                key = policy + ('' if not delay else '_DELAY_' + str(delay))
                self.s['accounts'].setdefault(key, dict(cash=self.config['capital'], reserved=0., count=0, used=[], trades={}, policy=policy, delay=delay))
        old = self.s.get('config')
        if old is not None and old != self.config:
            raise RuntimeError('Frozen experiment config changed; new experiment required')
        self.s['config'] = self.config
        self.db.execute('CREATE TABLE IF NOT EXISTS master(day TEXT, code TEXT, payload TEXT, PRIMARY KEY(day,code))')
        self.master = {code:json.loads(raw) for code,raw in self.db.execute('SELECT code,payload FROM master WHERE day=?',(self.day,))}
        self.indexes = {}
        for raw, in self.db.execute("SELECT payload FROM journal WHERE day=? AND kind='INDEX' ORDER BY id",(self.day,)):
            row=json.loads(raw)
            self.indexes.setdefault(row['item'],[]).append(row)
        self.s.pop('master',None)
        self.s.pop('indexes',None)
        self.events = []
        self.last_received = None
        self.last_export = 0.
        for c in self.s['candidates'].values():
            self.gap(c, now, 'RESTART_PARTIAL')
        for sub in self.s['subscriptions'].values():
            if sub['status'] != 'REMOVED':
                sub['status'] = 'RECONNECT_PENDING'
        self.emit('events', 'START', now, '', {'restored': bool(record), 'mode': 'RESEARCH'})
        self.commit()
        self.registry(now)

    # 함수 설명: 실험 정의와 데이터 계약을 원자 JSON에 고정합니다.
    def registry(self, now):
        path = Path(self.path).with_name('opportunity_registry_v235.json')
        payload = dict(version='v2.3.5', experiment_id=self.config['experiment_id'], config=self.config,
                       parent_sha256='70baaf1f4d86b5e0e1eda4c42c00b07066b5aba943f4d336be253e738ca21499',
                       first_started_at=now.isoformat(), target_date='2026-12-15', profitability='UNVERIFIED',
                       contracts={'0B': 'official 13 cumulative shares,14 million KRW,20 HHmmss,290=2',
                                  '0D': 'official 21 HHmmss,41 ask,51 bid,61 ask_qty,71 bid_qty',
                                  '0J': 'official 20 time,10 price,16 MAIN open; no synthesized time',
                                  'classification': 'KIS official public master group/preferred/SPAC fields; missing blocks entry',
                                  'minute_backfill': 'ka10080 KRX tic_scope=1 upd_stkpc_tp=0; exactly five completed opening labels required; response time before decision; two distinct completed raw KRX OHLCV overlap matches required before reference use'})
        if path.exists():
            previous = json.loads(path.read_text(encoding='utf-8'))
            if previous['config'] != self.config:
                raise RuntimeError('registry mismatch')
            return
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, path)

    # 함수 설명: 공유 구독의 상태와 수용량을 확인하여 요청을 처리합니다.
    def emit(self, stream, kind, at, code, payload):
        c = self.s['candidates'].get(code, {})
        row = dict(version='v2.3.5', experiment_id=self.config['experiment_id'], rule_id=self.config['rule_id'],
                   cost_model_id='quote_plus_0p24_estimated', date=self.day, market=c.get('market', ''),
                   stock_code=code, candidate_id=c.get('id', ''), segment_id=c.get('segment', ''),
                   )
        row.update(copy.deepcopy(payload))
        self.events.append((self.day, stream, kind, at.isoformat(), code, json.dumps(row, ensure_ascii=False, allow_nan=False)))

    # 함수 설명: DB 불변식을 검사하고 상태·자금·이벤트를 한 번에 저장, 실패 시 신규만 차단합니다.
    def commit(self):
        try:
            self.invariants()
            raw = json.dumps(self.s, ensure_ascii=False, allow_nan=False)
            with self.db:
                self.db.executemany('INSERT INTO journal(day,stream,kind,at,code,payload) VALUES(?,?,?,?,?,?)', self.events)
                self.db.execute('INSERT OR REPLACE INTO state VALUES(?,?)', (self.day, raw))
            self.events.clear()
        except Exception:
            self.halted = True
            raise

    # 함수 설명: 정책별 현금·예약·보유·횟수 보존과 동일종목·수량 중복을 자동 검증합니다.
    def invariants(self):
        for a in self.s['accounts'].values():
            active = [t for t in a['trades'].values() if t['status'] in ('PENDING', 'OPEN', 'EXIT_PENDING', 'EXIT_UNCONFIRMED')]
            assert a['cash'] >= -1e-5 and a['reserved'] >= -1e-5 and a['reserved'] <= a['cash'] + 1e-5
            assert len(active) <= self.config['max_slots']
            assert a['count'] <= self.config['max_daily'] and len(a['used']) == a['count'] == len(set(a['used']))
            assert len({t['code'] for t in active}) == len(active)
            assert abs(a['reserved'] - sum(t['reserve'] for t in active)) < 1e-4
            assert all(0 <= t['sold'] <= t['qty'] <= t['target'] for t in a['trades'].values())
            invested = sum(t['buy_amount'] - t['sell_amount'] + t['cost'] for t in a['trades'].values())
            assert abs(a['cash'] + invested - self.config['capital']) < 1e-3

    # 함수 설명: 입출력 이벤트를 단일 순서로 처리하고 원시 수신시각과 실제 검출시각을 분리합니다.
    def process(self, kind, code, received, data, detected=None):
        detected = detected or datetime.now()
        if received.date().isoformat() != self.day:
            return
        if kind in ('TRADE','QUOTE','INDEX') and not isinstance(data,dict):
            self.emit('events','INPUT_DATA_UNAVAILABLE',received,code,dict(kind=kind,raw=data))
            if code in self.s['candidates']:
                self.gap(self.s['candidates'][code],received,'INVALID_INPUT_TYPE')
            self.commit()
            return
        if kind == 'RANK':
            self.rank(data, received, detected)
        elif kind == 'MASTER':
            with self.db:
                self.db.executemany('INSERT OR REPLACE INTO master VALUES(?,?,?)',[(self.day,code,json.dumps(row,ensure_ascii=False)) for code,row in data.items()])
            self.master = data
            for c in self.s['candidates'].values():
                product=self.master.get(c['code'])
                if product and not product['ordinary'] and not self.protected(c['code']):
                    c['active']=False
                    c['excluded_product']=True
            self.emit('universe', 'MASTER_READY', received, '', {'count': len(data)})
        elif kind == 'SUBSCRIPTION':
            self.s['subscriptions'][data['item']] = dict(data)
            c = self.s['candidates'].get(code)
            if c is not None and data['item']==code:
                c['subscription_ok'] = data['status'] == 'ACK' and set(data['types']) >= {'0B','0D'}
            self.emit('universe', 'SUBSCRIPTION', received, code, data)
        elif kind == 'REFERENCE':
            self.reference(code, data, received, detected)
        elif kind == 'INDEX':
            self.index(code, data, received)
        elif kind == 'TRADE':
            self.tick(code, data, received, detected)
        elif kind == 'QUOTE':
            self.quote(code, data, received, detected)
        elif kind == 'GAP':
            for c in self.s['candidates'].values():
                if not code or c['code'] == code:
                    self.gap(c, received, data.get('reason', 'STREAM_GAP'))
        elif kind == 'MAINTAIN':
            self.maintain(detected, data.get('ending', False))
        self.commit()

    # 함수 설명: 0J의 수신 당시 값을 저장하며 미래·역행 시세를 의사결정에 사용하지 않습니다.
    def index(self, code, values, received):
        q = v234_wire_time(values.get('20'), received)
        p, opening = v235_num(values.get('10')), v235_num(values.get('16'))
        if code not in V234_INDEX_CODES or q is None or p is None or not p:
            self.emit('events', 'INDEX_UNAVAILABLE', received, '', {'item': code, 'raw': values})
            return
        h = self.indexes.setdefault(code, [])
        if h and q < v235_dt(h[-1]['quote_at']):
            return
        row = dict(quote_at=q.isoformat(), received_at=received.isoformat(), price=abs(p),
                   opening=abs(opening) if opening else None, source='0J')
        h.append(row)
        self.indexes[code] = h[-24000:]
        self.emit('events', 'INDEX', received, '', dict(item=code, **row))

    # 함수 설명: 판단시점 t를 기준으로 1/5분 과거 앵커·시가·상대강도·결측 사유를 계산합니다.
    def context(self, at, c, price):
        result = {}
        for code, market in V234_INDEX_CODES.items():
            eligible = [x for x in self.indexes.get(code, []) if v235_dt(x['quote_at']) <= v235_dt(x['received_at']) <= at
                        and v235_dt(x['quote_at']).date() == at.date()]
            current = max(eligible, key=lambda x: (x['quote_at'], x['received_at']), default=None)
            if current is None:
                result[market] = dict(status='INDEX_MISSING')
                continue
            row = copy.deepcopy(current)
            age = (at - v235_dt(current['quote_at'])).total_seconds()
            row.update(age_sec=age, status='OK' if age <= self.config['rank_age'] else 'INDEX_STALE')
            opening = next((x for x in eligible if x.get('opening')), None)
            row['open_received_at'] = opening['received_at'] if opening else None
            row['from_open_pct'] = (current['price'] / opening['opening'] - 1) * 100 if opening and row['status'] == 'OK' else None
            if not opening:
                row['open_status'] = 'MARKET_OPEN_MISSING'
            for sec in (60, 300):
                anchor = at - timedelta(seconds=sec)
                lag = max((x for x in eligible if v235_dt(x['quote_at']) <= anchor),
                          key=lambda x: (x['quote_at'], x['received_at']), default=None)
                row['change_' + str(sec // 60) + 'm_pct'] = ((current['price'] / lag['price'] - 1) * 100
                     if row['status'] == 'OK' and lag and (anchor - v235_dt(lag['quote_at'])).total_seconds() <= 15 else None)
                row['anchor_' + str(sec)] = lag['quote_at'] if lag else None
            result[market] = row
        own = result.get(c.get('market'), {})
        opening = c.get('main_open') if c.get('main_open_at') and v235_dt(c['main_open_at']) <= at else None
        ret = own.get('from_open_pct')
        result['stock_open'] = opening
        result['stock_open_source'] = c.get('main_open_source')
        result['stock_open_received_at'] = c.get('main_open_at')
        result['relative_strength_pp'] = ((price / opening - 1) * 100 - ret if opening and ret is not None else None)
        result['relative_strength_status'] = ('STOCK_OPEN_MISSING' if not opening else 'MARKET_OPEN_OR_INDEX_MISSING' if ret is None else 'OK')
        five = own.get('change_5m_pct')
        result['index_decision'] = ('DATA_UNAVAILABLE' if ret is None or five is None else 'PASS' if ret >= 0 and five > 0 else 'FAIL')
        return result

    # 함수 설명: 순위 원본을 전부 기록하고 현재 순위·실거래대금·20개 관찰 우선순위를 고정합니다.
    def rank(self, packet, received, detected):
        market = packet['market']
        normalized = []
        for rank, raw in enumerate(packet['rows'], 1):
            try:
                if not isinstance(raw,dict):
                    raise ValueError('RANK_ROW_NOT_OBJECT')
                stock = normalize_change_row(raw, market, rank)
            except (ValueError,TypeError,KeyError,AttributeError) as exc:
                self.emit('universe','RANK_ROW_UNAVAILABLE',received,'',dict(raw=raw,rank=rank,market=market,reason=type(exc).__name__))
                continue
            code = stock['stock_code']
            normalized.append(stock)
            self.emit('universe', 'RANK_RAW', received, code, dict(raw=raw, rank=rank, market=market, source='ka10027', received_at=received.isoformat()))
        current = {x['stock_code']: x for x in normalized if x['change_rank'] <= self.config['top_n']}
        for c in self.s['candidates'].values():
            if c['market'] != market:
                continue
            if c['code'] not in current:
                c['in_rank'] = False
                c.setdefault('outside_at', received.isoformat())
            else:
                c.pop('outside_at', None)
        for s in sorted(current.values(), key=lambda x: (x['change_rank'], -float(x.get('actual_trading_value') or 0), market, x['stock_code'])):
            code = s['stock_code']
            product=self.master.get(code)
            if product and not product['ordinary']:
                self.emit('universe','EXCLUDED_PRODUCT',received,code,{'product':product})
                continue
            c = self.s['candidates'].get(code)
            if c is None:
                if not v234_between(received, '09:00', '09:15') or s['change_rate'] < self.config['observe_pct']:
                    continue
                c = dict(id=self.day + ':' + code, code=code, name=s['stock_name'], market=market,
                         segment=0, registered=received.isoformat(), active=False, bars=[], bar=None,
                         volume=0., value=0., b_status='WAIT_RANGE', b_count=0, used_signals=[],
                         main_open=None, main_open_at=None, main_open_source=None)
                self.s['candidates'][code] = c
            c.update(rank=s['change_rank'], rank_at=received.isoformat(), in_rank=True,
                     change=s['change_rate'], change_at=received.isoformat())
        eligible = sorted((c for c in self.s['candidates'].values() if not c.get('excluded_product') and c.get('in_rank') and self.fresh(c.get('rank_at'), detected, self.config['rank_age'])),
                          key=lambda c: (c['rank'], -c.get('actual_value', 0), c['market'], c['code']))
        allowed = {c['code'] for c in eligible[:self.config['max_candidates']]}
        for c in self.s['candidates'].values():
            if c['active'] and not self.protected(c['code']) and c.get('outside_at') and (received-v235_dt(c['outside_at'])).total_seconds()>=30:
                c['active']=False
                self.gap(c,received,'RANK_EXIT')
                self.emit('universe','RELEASE_ELIGIBLE',received,c['code'],{})
        for c in sorted(self.s['candidates'].values(),key=lambda x:(x.get('rank',999),-x.get('actual_value',0),x['market'],x['code'])):
            if c['code'] in allowed and not c['active']:
                if sum(x['active'] for x in self.s['candidates'].values()) >= self.config['max_candidates']:
                    self.emit('universe','NO_ACTIVE_SLOT',received,c['code'],{})
                    continue
                c['active'] = True
                self.gap(c, received, 'NEW_SEGMENT')
                c['segment_start'] = received.isoformat()
                self.emit('universe', 'SELECTED', received, c['code'], {'context': self.context(detected, c, 0)})
            if c['active'] and not self.protected(c['code']) and c.get('outside_at') and (received - v235_dt(c['outside_at'])).total_seconds() >= 30:
                c['active'] = False
                self.gap(c, received, 'RANK_EXIT')
                self.emit('universe', 'RELEASE_ELIGIBLE', received, c['code'], {})

    # 함수 설명: 입력 시각이 같은 날의 과거이며 신선한지 확인합니다.
    def fresh(self, stamp, at, limit):
        return bool(stamp and v235_dt(stamp).date() == at.date() and 0 <= (at - v235_dt(stamp)).total_seconds() <= limit)

    # 함수 설명: 보유·예약·첫 이탈 사건과 체결후 관찰에 필요한 구독을 보호합니다.
    def protected(self, code):
        c = self.s['candidates'].get(code, {})
        return c.get('b_status') == 'BREAK' or any(t['code'] == code and (t['status'] in ('PENDING', 'OPEN', 'EXIT_PENDING', 'EXIT_UNCONFIRMED') or t['qty'] and len(t['horizons'])<3)
                        for a in self.s['accounts'].values() for t in a['trades'].values())

    # 함수 설명: 관측 공백은 새 VWAP 구간으로 격리하고 당일 최초 사건·신호키는 유지합니다.
    def gap(self, c, at, reason):
        if reason in ('RECONNECT','RESTART_PARTIAL'):
            c['subscription_ok']=False
        if at.time() >= _hhmm_time('09:05') and reason != 'NEW_SEGMENT':
            c['post05_gap'] = True
        c['segment'] += 1
        c.update(bars=[], bar=None, volume=0., value=0., last_cum=None, last_quote=None, first_partial=True)
        if c.get('b_status') == 'BREAK':
            c['b_status'] = 'EVENT_TERMINATED_GAP'
        elif c.get('b_status') in ('WAIT_RANGE','WAIT_REFERENCE','READY') and at.time() >= _hhmm_time('09:05'):
            c['b_status'] = 'OPENING_RANGE_INCOMPLETE'
        self.emit('events', 'GAP', at, c['code'], {'reason': reason})
        if reason not in ('NEW_SEGMENT','RANK_EXIT') and not c.get('notice_degraded'):
            c['notice_degraded']=True
            key=c['id']+':FAULT:'+str(c['segment'])
            self.s['outbox'].setdefault(key,dict(status='PENDING',text=f"⚠️ 연구 시세 장애 {c['code']}\n• {reason} / 해당 후보 평가 격리\n연구용 가상진입 / 실제주문 없음"))

    # 함수 설명: 신호 시점의 보통주·순위·유동성·구독 자격을 재검사합니다.
    def common(self, c, at):
        reasons = []
        master = self.master.get(c['code'])
        if not master or master.get('market') != c['market'] or master.get('day') != self.day:
            reasons.append('PRODUCT_CLASSIFICATION_UNAVAILABLE')
        elif not master['ordinary']:
            reasons.append('EXCLUDED_PRODUCT')
        if not c.get('in_rank') or c.get('rank', 999) > self.config['top_n']:
            reasons.append('RANK_OUTSIDE')
        for field in ('rank_at', 'change_at', 'value_at'):
            if not self.fresh(c.get(field), at, self.config['rank_age']):
                reasons.append('STALE_OR_MISSING_' + field.upper())
        if not self.config['entry_min_pct'] <= c.get('change', -999) <= self.config['entry_max_pct']:
            reasons.append('CHANGE_OUTSIDE')
        if c.get('actual_value', 0) < self.config['min_value']:
            reasons.append('ACTUAL_VALUE_INSUFFICIENT')
        if not c.get('subscription_ok', False):
            reasons.append('SUBSCRIPTION_UNCONFIRMED')
        return reasons

    # 함수 설명: 실제 누적량 증분으로 정상 체결·분봉·VWAP을 갱신합니다.
    def tick(self, code, values, received, detected):
        c = self.s['candidates'].get(code)
        if not c or not c['active']:
            return
        self.emit('quotes', 'TRADE_RAW', received, code, dict(raw=values, received_at=received.isoformat()))
        q = v234_wire_time(values.get('20'), received)
        p, cum = v235_num(values.get('10')), v235_num(values.get('13'))
        if q is None or p is None or not p or cum is None or cum < 0 or str(values.get('290')) != '2' or values.get('v235_item', code) != code:
            self.gap(c, received, 'TRADE_FIELD_OR_SESSION_UNAVAILABLE')
            return
        p = abs(p)
        previous = c.get('last_cum')
        if c.get('last_quote') and q < v235_dt(c['last_quote']):
            self.gap(c, received, 'REVERSE_TIME')
            return
        if previous is not None and cum <= previous:
            if cum < previous:
                self.gap(c, received, 'CUMULATIVE_VOLUME_REVERSED')
            return
        delta = cum - previous if previous is not None else 0
        single = v235_num(values.get('15'))
        if previous is not None and (single is None or abs(single) != delta):
            self.gap(c, received, 'MISSING_OR_DUPLICATED_TRADES')
            delta = 0
        if previous is None and q.time() == _hhmm_time('09:00') and received == q and single is not None and abs(single) == cum:
            delta = abs(single)
        c.update(last_cum=cum, last_quote=q.isoformat(), last_received=received.isoformat())
        if '12' in values and v235_num(values['12']) is not None:
            c.update(change=v235_num(values['12']), change_at=received.isoformat())
        if '14' in values and v235_num(values['14']) is not None:
            c.update(actual_value=abs(v235_num(values['14'])) * 1_000_000, value_at=received.isoformat(), value_source='0B:14 million KRW')
        opening = v235_num(values.get('16'))
        if opening and not c.get('main_open'):
            c.update(main_open=abs(opening), main_open_at=received.isoformat(), main_open_source='0B:16:KRX:MAIN')
        minute = q.replace(second=0, microsecond=0)
        bar = c['bar']
        if bar and minute > v235_dt(bar['minute']):
            if minute != v235_dt(bar['minute']) + timedelta(minutes=1):
                self.gap(c, received, 'MISSING_MINUTE')
            else:
                self.complete(c, bar, received, detected)
            c['bar'] = None
        if c['bar'] is None:
            partial = c.pop('first_partial', True)
            # 完全な9:00:00受信以外は初回分を部分足とする。後から開始時刻を偽らない。
            if minute.time() == _hhmm_time('09:00') and q == minute and received == minute and delta > 0:
                partial = False
            c['bar'] = dict(minute=minute.isoformat(), open=p, high=p, low=p, close=p, volume=0., trade_value=0., valid=not partial)
            c['first_partial'] = False
        bar = c['bar']
        bar.update(high=max(bar['high'], p), low=min(bar['low'], p), close=p)
        bar['volume'] += delta
        bar['trade_value'] += p * delta
        if bar['valid']:
            c['volume'] += delta
            c['value'] += p * delta
        c['vwap'] = c['value'] / c['volume'] if c['volume'] > 0 else None

    # 함수 설명: 판정 전에 받은 KRX 완료5봉만 초기범위에 연결하고 관측공백·소급신호를 차단합니다.
    def reference(self, code, packet, received, detected):
        c = self.s['candidates'].get(code)
        if not c or c['b_status'] not in ('WAIT_RANGE','WAIT_REFERENCE'):
            return
        self.emit('events','REFERENCE_RAW',received,code,packet)
        rows = packet.get('stk_min_pole_chart_qry', [])
        wanted = {received.replace(hour=9,minute=m,second=0,microsecond=0).strftime('%Y%m%d%H%M%S') for m in range(5)}
        opening = [r for r in rows if str(r.get('cntr_tm')) in wanted]
        early_start = v235_dt(c.get('segment_start', c['registered'])) <= received.replace(hour=9,minute=5,second=0,microsecond=0)
        checks=c.get('reference_check_bars',[])
        by_time={str(r.get('cntr_tm')):r for r in rows}
        matches=0
        shapes=set()
        for bar in checks:
            row=by_time.get(v235_dt(bar['minute']).strftime('%Y%m%d%H%M%S'))
            if row and all(v235_num(row.get(field)) is not None and abs(v235_num(row[field]))==bar[k] for k,field in [('open','open_pric'),('high','high_pric'),('low','low_pric'),('close','cur_prc'),('volume','trde_qty')]):
                matches+=1
                shapes.add(tuple(bar[k] for k in ('open','high','low','close','volume')))
        if len(checks)<2 or len(shapes)<2:
            self.emit('events','REFERENCE_CONTRACT_UNVERIFIED',detected,code,{'reason':'NEED_TWO_DISTINCT_COMPLETE_KRX_OVERLAPS'})
            return
        good = (matches>=2 and len(opening)==5 and len({r['cntr_tm'] for r in opening})==5 and early_start and not c.get('post05_gap')
                and received.time() >= _hhmm_time('09:05') and received <= detected and c.get('subscription_ok')
                and all(all(v235_num(r.get(k)) is not None and abs(v235_num(r[k]))>0 for k in ('low_pric','high_pric','open_pric','cur_prc','trde_qty')) for r in opening))
        if not good:
            c['b_status']='OPENING_RANGE_INCOMPLETE'
            self.emit('events','OPENING_RANGE_INCOMPLETE',detected,code,{'reason':'REFERENCE_OR_POST05_CONTINUITY'})
            return
        c.update(range_low=min(abs(v235_num(r['low_pric'])) for r in opening), range_ready_at=received.isoformat(),b_status='READY')
        self.emit('events','RANGE_READY',detected,code,{'low':c['range_low'],'source':'ka10080:KRX:unadjusted:two_raw_ohlcv_matches','range_ready_at':c['range_ready_at']})
        # 이전 완료봉은 최초 이탈 여부만 초기화. 과거 회복신호·체결은 생성하지 않습니다.
        for bar in c.pop('post05_waiting', []):
            if c['b_status']=='READY' and bar['close']<=v235_tick_price(c['range_low'],-1):
                c.update(b_status='BREAK',b_count=0,break_at=(v235_dt(bar['minute'])+timedelta(minutes=1)).isoformat(),break_low=bar['low'])
            elif c['b_status']=='BREAK':
                c['b_count']+=1
                if c['b_count']>=3:
                    c['b_status']='FIRST_EVENT_EXPIRED'

    # 함수 설명: 연속 유효 완료봉으로 A/B 조건과 평가 분모를 기록합니다.
    def complete(self, c, bar, received, detected):
        end = v235_dt(bar['minute']) + timedelta(minutes=1)
        valid = bar['valid'] and bar['volume'] > 0 and received >= end and detected >= received
        bar = dict(bar, valid=valid, received_at=received.isoformat(), detected_at=detected.isoformat())
        self.emit('events', 'BAR', detected, c['code'], {'bar': bar, 'vwap': c.get('vwap')})
        if not valid:
            if v235_dt(bar['minute']).time() >= _hhmm_time('09:05'):
                c['post05_gap']=True
                if c.get('b_status') in ('WAIT_RANGE','WAIT_REFERENCE','READY'):
                    c['b_status']='OPENING_RANGE_INCOMPLETE'
            if c.get('b_status') == 'BREAK':
                c['b_status'] = 'EVENT_TERMINATED_GAP'
            c['bars'] = []
            c.update(volume=0., value=0., vwap=None)
            for strategy,start,finish in ((V235_A,'09:02','09:10'),(V235_B,'09:05','10:00')):
                if v234_between(end,start,finish):
                    self.evaluation(c,detected,dict(strategy=strategy,status='DATA_UNAVAILABLE',reasons=['INVALID_BAR'],bar=bar))
            return
        if v235_dt(bar['minute']).time() >= _hhmm_time('09:05'):
            c.setdefault('reference_check_bars', []).append(copy.deepcopy(bar))
            c['reference_check_bars']=c['reference_check_bars'][-10:]
        prior = c['bars'][-1] if c['bars'] else None
        if prior and v235_dt(prior['minute']) + timedelta(minutes=1) != v235_dt(bar['minute']):
            c['bars'] = []
            prior = None
        if prior and c.get('notice_degraded'):
            c['notice_degraded']=False
            self.s['outbox'].setdefault(c['id']+':RECOVERY:'+str(c['segment']),dict(status='PENDING',text=f"🔬 연구 시세 복구 {c['code']}\n• 연속 완료봉 2개 확보\n연구용 가상진입 / 실제주문 없음"))
        c['bars'].append(bar)
        c['bars'] = c['bars'][-(5 if end.time() <= _hhmm_time('09:05') else 2):]
        if end.time() == _hhmm_time('09:05') and c['b_status'] == 'WAIT_RANGE':
            opening = [x for x in c['bars'] if _hhmm_time('09:00') <= v235_dt(x['minute']).time() < _hhmm_time('09:05')]
            if len(opening) == 5 and all(v235_dt(x['minute']).minute == i for i, x in enumerate(opening)):
                c.update(range_low=min(x['low'] for x in opening), range_ready_at=detected.isoformat(), b_status='READY')
                self.emit('events', 'RANGE_READY', detected, c['code'], {'low': c['range_low'], 'range_ready_at': c['range_ready_at']})
            else:
                c['b_status'] = 'WAIT_REFERENCE'
        if end.time() > _hhmm_time('09:05') and c['b_status'] in ('WAIT_RANGE','WAIT_REFERENCE'):
            c['b_status'] = 'WAIT_REFERENCE'
            c.setdefault('post05_waiting', []).append(bar)
        reasons = self.common(c, detected)
        data_reasons=[r for r in reasons if r.startswith('STALE_OR_MISSING_') or r in ('PRODUCT_CLASSIFICATION_UNAVAILABLE','SUBSCRIPTION_UNCONFIRMED')]
        vwap = c.get('vwap')
        a_time = all(v234_between(t, '09:02', '09:10') for t in (end, detected))
        a_registered = v234_between(v235_dt(c['registered']), '09:00', '09:10')
        if a_time and a_registered and V235_A in c['used_signals']:
            self.evaluation(c,detected,dict(strategy=V235_A,status='TERMINAL_ALREADY_SIGNALLED',reasons=[],bar=bar))
        if a_time and a_registered and V235_A not in c['used_signals']:
            ready = bool(prior and vwap and bar['close'] >= v235_tick_price(prior['high']) and bar['close'] > bar['open']
                         and prior['trade_value'] > 0 and bar['trade_value'] >= self.config['flow_ratio'] * prior['trade_value'] and bar['close'] > vwap)
            self.evaluation(c,detected,dict(strategy=V235_A, status='DATA_UNAVAILABLE' if data_reasons or not prior or not vwap else 'CONDITION_REJECT' if reasons else 'READY' if ready else 'NO_SETUP', reasons=reasons, bar=bar, previous=prior, vwap=vwap))
            if ready and not reasons:
                self.signal(c, V235_A, bar, detected)
        if c['b_status'] in ('READY', 'BREAK') and end.time() > _hhmm_time('09:05'):
            low = c['range_low']
            if c['b_status'] == 'READY' and bar['close'] <= v235_tick_price(low, -1):
                c.update(b_status='BREAK', b_count=0, break_at=end.isoformat(), break_low=bar['low'])
                self.emit('events', 'FIRST_BREAK', detected, c['code'], dict(low=low, bar=bar))
            elif c['b_status'] == 'BREAK':
                c['b_count'] += 1
                c['break_low'] = min(c['break_low'], bar['low'])
                recovered = bool(prior and vwap and bar['close'] >= v235_tick_price(low) and bar['close'] > prior['high'] and bar['close'] > vwap)
                btime = all(v234_between(t, '09:05', '10:00') for t in (end, detected))
                if c['b_count'] <= 3 and recovered and btime and not reasons and V235_B not in c['used_signals']:
                    self.signal(c, V235_B, bar, detected)
                    c['b_status'] = 'SIGNALLED'
                elif c['b_count'] >= 3:
                    c['b_status'] = 'FIRST_EVENT_EXPIRED'
        if all(v234_between(t, '09:05', '10:00') for t in (end, detected)):
            self.evaluation(c,detected,dict(strategy=V235_B, status='DATA_UNAVAILABLE' if data_reasons or c['b_status'] in ('OPENING_RANGE_INCOMPLETE','WAIT_REFERENCE','WAIT_RANGE') else 'CONDITION_REJECT' if reasons else c['b_status'], reasons=reasons, bar=bar))

    # 함수 설명: 후보×전략×판정분마다 평가 분모를 한 번만 기록합니다.
    def evaluation(self,c,at,payload):
        bar=payload.get('bar')
        end=v235_dt(bar['minute'])+timedelta(minutes=1) if bar else v235_dt(payload.get('evaluation_at',at.replace(second=0,microsecond=0)))
        key=payload['strategy']+':'+end.isoformat()
        if c.get('excluded_product'):
            return
        if payload['strategy'] in c['used_signals']:
            payload=dict(payload,status='TERMINAL_ALREADY_SIGNALLED',reasons=[])
        if c.get('excluded_product'):
            payload=dict(payload,status='EXCLUDED_PRODUCT',reasons=[])
        registered=v235_dt(c['registered'])
        earliest=registered.replace(second=0,microsecond=0)+timedelta(minutes=2 if registered==registered.replace(second=0,microsecond=0) else 3)
        if payload['strategy']==V235_A and end<earliest:
            payload=dict(payload,status='WARMUP',reasons=['TWO_COMPLETE_BARS_NOT_YET_POSSIBLE'])
        if payload['strategy']==V235_B and c['b_status'] in ('WAIT_RANGE','WAIT_REFERENCE') and end.time()<_hhmm_time('09:07'):
            payload=dict(payload,status='WARMUP_REFERENCE',reasons=['REFERENCE_CONTRACT_WARMUP'])
        if not c.get('in_rank') and payload['status']!='TERMINAL_ALREADY_SIGNALLED':
            payload=dict(payload,status='EXCLUDED_RANK',reasons=[])
        if key in c.setdefault('evaluation_keys',[]):
            return
        c['evaluation_keys'].append(key)
        self.emit('events','EVALUATION',at,c['code'],dict(payload,evaluation_at=end.isoformat()))

    # 함수 설명: 종목당 최초 적격 신호를 영구 소비하고 두 정책·지연 시나리오 예약을 독립 생성합니다.
    def signal(self, c, strategy, bar, at):
        if self.halted or shutdown_requested:
            return
        c['used_signals'].append(strategy)
        self.s['serial'] += 1
        sid = c['id'] + ':' + strategy + ':' + str(self.s['serial'])
        ctx = self.context(at, c, bar['close'])
        signal = dict(signal_id=sid, strategy=strategy, detected_at=at.isoformat(), signal_at=(v235_dt(bar['minute']) + timedelta(minutes=1)).isoformat(),
                      signal_price=bar['close'], context=ctx, rank=c['rank'], change=c['change'], actual_value=c['actual_value'],
                      as_of={k: c.get(k) for k in ('rank_at', 'change_at', 'value_at', 'main_open_at')}, vwap=c.get('vwap'), bar=bar)
        self.emit('events', 'SIGNAL', at, c['code'], signal)
        pair_key='PAIR:'+sid
        self.s['accounts'][pair_key]=dict(cash=self.config['capital'],reserved=0.,count=0,used=[],trades={},policy='UNFILTERED',delay=0)
        for key, a in self.s['accounts'].items():
            if key.startswith('PAIR:') and key!=pair_key:
                continue
            if a['policy'] == 'INDEX_UP' and ctx['index_decision'] != 'PASS':
                self.emit('portfolio', 'POLICY_SKIP', at, c['code'], dict(policy=key, signal_id=sid, reason=ctx['index_decision']))
                continue
            active = [t for t in a['trades'].values() if t['status'] in ('PENDING', 'OPEN', 'EXIT_PENDING', 'EXIT_UNCONFIRMED')]
            proposed=(at.isoformat(),strategy!=V235_A,c['code'])
            worst=max((t for t in active if not t['qty']),key=lambda t:(t['signal']['detected_at'],t['strategy']!=V235_A,t['code']),default=None)
            if worst and worst['signal']['detected_at']==at.isoformat() and proposed<(worst['signal']['detected_at'],worst['strategy']!=V235_A,worst['code']) and (len(active)>=self.config['max_slots'] or a['cash']-a['reserved']<self.config['per_stock'] or a['count']+sum(t['qty']==0 for t in active)>=self.config['max_daily']):
                self.cancel_pending(a,key,worst,at,'SIMULTANEOUS_PRIORITY')
                active=[t for t in active if t['id']!=worst['id']]
            reason = ('DAILY_LIMIT' if a['count'] + sum(t['qty'] == 0 for t in active) >= self.config['max_daily'] else
                      'SAME_STOCK' if c['code'] in a['used'] or any(t['code'] == c['code'] for t in active) else
                      'SLOT_LIMIT' if len(active) >= self.config['max_slots'] else
                      'BUDGET' if a['cash'] - a['reserved'] < 1 else None)
            if reason:
                self.emit('portfolio', 'REJECT', at, c['code'], dict(policy=key, signal_id=sid, reason=reason))
                continue
            reserve = min(self.config['per_stock'], a['cash'] - a['reserved'])
            end = at.replace(hour=9 if strategy == V235_A else 10, minute=10 if strategy == V235_A else 0, second=0, microsecond=0)
            deadline = min(at + timedelta(seconds=self.config['wait_sec']), end)
            tid = sid + ':' + key
            a['trades'][tid] = dict(code=c['code'], strategy=strategy, signal=signal, id=tid, status='PENDING', reserve=reserve,
                                   deadline=deadline.isoformat(), end=end.isoformat(), earliest=(at + timedelta(seconds=a['delay'])).isoformat(),
                                   target=0, qty=0, sold=0, buy_amount=0., sell_amount=0., cost=0., exit_reason=None, horizons=[], inventory={})
            a['reserved'] += reserve
            self.account_event(a, key, 'RESERVE', at, c['code'], tid)

    # 함수 설명: 정책별 자금 상태를 거래·신호키와 함께 기록합니다.
    def account_event(self, a, key, kind, at, code, tid, extra=None):
        self.emit('portfolio', kind, at, code, dict(policy=key, trade_id=tid, cash=a['cash'], reserved=a['reserved'],
                                                   count=a['count'], **(extra or {})))

    # 함수 설명: 0D 원시호가의 실제 시각·잔량·동일 snapshot 재사용을 검사하고 청산을 먼저 처리합니다.
    def quote(self, code, values, received, detected):
        c = self.s['candidates'].get(code)
        if c is None:
            return
        q = v234_wire_time(values.get('21'), received)
        ask, bid = v235_num(values.get('41')), v235_num(values.get('51'))
        aq, bq = v235_num(values.get('61')), v235_num(values.get('71'))
        self.emit('quotes', 'QUOTE_RAW', received, code, dict(raw=values, received_at=received.isoformat(), detected_at=detected.isoformat()))
        valid = (q is not None and values.get('v235_item', code) == code and all(x is not None and abs(x) > 0 for x in (ask, bid))
                 and aq is not None and bq is not None and aq >= 0 and bq >= 0 and self.fresh(q.isoformat(), detected, self.config['quote_age'])
                 and self.fresh(received.isoformat(), detected, self.config['quote_age']))
        if not valid:
            self.emit('events', 'QUOTE_UNAVAILABLE', detected, code, {'reason': 'QUOTE_FIELD_TIME_OR_SESSION'})
            return
        ask, bid = abs(ask), abs(bid)
        if bid > ask:
            self.emit('events', 'QUOTE_UNAVAILABLE', detected, code, {'reason': 'SPREAD_OR_CROSSED'})
            return
        signature = json.dumps([q.isoformat(), ask, bid, aq, bq])
        quote_id = hashlib.sha256((code + signature).encode()).hexdigest()[:24]
        # 相同秒・価格・残量はserver sequenceなしでは新規在庫と証明できないため再利用禁止。
        if c.get('quote_last_at') and q < v235_dt(c['quote_last_at']):
            return
        c['quote_last_at'] = q.isoformat()
        c['mark_bid']=bid
        c['mark_bid_at']=received.isoformat()
        for key, a in self.s['accounts'].items():
            for t in a['trades'].values():
                if t['code']==code and t.get('inventory_quote_at')!=q.isoformat():
                    t['inventory']={}
                    t['inventory_quote_at']=q.isoformat()
            trades = sorted((t for t in a['trades'].values() if t['code'] == code), key=lambda t: (t['signal']['detected_at'], t['strategy'] != V235_A, t['code']))
            for t in trades:
                if t['qty']:
                    self.path_quote(t,c,key,bid,quote_id,detected)
                if t['status'] in ('OPEN', 'EXIT_PENDING'):
                    self.exit_quote(a, key, t, c, bid, bq, quote_id, q, received, detected)
            for t in trades:
                if (ask - bid) / ((ask + bid) / 2) * 100 > self.config['spread_pct']:
                    continue
                if t['status'] not in ('PENDING', 'OPEN') or t['target'] and t['qty'] >= t['target']:
                    continue
                if detected >= v235_dt(t['deadline']) or q >= v235_dt(t['end']):
                    self.cancel_pending(a, key, t, detected, 'DEADLINE')
                    continue
                if received <= v235_dt(t['signal']['detected_at']) or q < v235_dt(t['signal']['detected_at']).replace(microsecond=0) or detected < v235_dt(t['earliest']):
                    continue
                if self.halted or shutdown_requested or self.common(c, detected):
                    self.cancel_pending(a, key, t, detected, 'ENTRY_RECHECK_FAILED')
                    continue
                invkey = quote_id + ':BUY'
                if invkey in t['inventory']:
                    continue
                t['inventory'][invkey] = True
                capacity = int(aq * self.config['depth_fraction'])
                if not t['target']:
                    t['target'] = min(int(t['reserve'] / ask), capacity)
                quantity = min(t['target'] - t['qty'], capacity, int(t['reserve'] / ask))
                if quantity < 1:
                    if not t['qty']:
                        self.cancel_pending(a, key, t, detected, 'NO_FILL_QTY')
                    continue
                first = not t['qty']
                t['qty'] += quantity
                amount = quantity * ask
                t['buy_amount'] += amount
                a['cash'] -= amount
                a['reserved'] -= amount
                t['reserve'] -= amount
                t['status'] = 'OPEN'
                if first:
                    a['count'] += 1
                    a['used'].append(code)
                    t['first_fill_at'] = detected.isoformat()
                    t['due_at'] = (detected + timedelta(seconds=self.config['hold_a_sec'] if t['strategy'] == V235_A else self.config['hold_b_sec'])).isoformat()
                t['avg_entry'] = t['buy_amount'] / t['qty']
                t['last_fill_at'] = detected.isoformat()
                self.emit('events', 'FILL', detected, code, dict(policy=key, trade_id=t['id'], signal_id=t['signal']['signal_id'], strategy=t['strategy'],
                          price=ask, qty=quantity, total_qty=t['qty'], quote_id=quote_id, quote_at=q.isoformat(), received_at=received.isoformat(),
                          latency_sec=(detected - v235_dt(t['signal']['detected_at'])).total_seconds(), context=self.context(detected, c, ask)))
                self.account_event(a, key, 'FILL', detected, code, t['id'])
                if t['qty'] >= t['target']:
                    self.release(a, t)
                if key == 'UNFILTERED' and first:
                    self.notice(t, '가상진입', detected, ask)
            self.mark_account(a,key,detected)

    # 함수 설명: 모든 미결수량의 신선한 매도호가로 자금곡선·낙폭을 표시합니다.
    def mark_account(self,a,key,at):
        equity=a['cash']
        for t in a['trades'].values():
            remaining=t['qty']-t['sold']
            if remaining<=0:
                continue
            c=self.s['candidates'][t['code']]
            if not self.fresh(c.get('mark_bid_at'),at,self.config['quote_age']):
                a['mark_missing_count']=a.get('mark_missing_count',0)+1
                return
            equity+=remaining*c['mark_bid']-remaining*t['avg_entry']*self.config['cost_pct']/100
        a['equity_peak']=max(a.get('equity_peak',self.config['capital']),equity)
        a['drawdown_pct']=max(a.get('drawdown_pct',0),(a['equity_peak']-equity)/self.config['capital']*100)
        a['equity']=equity
        self.account_event(a,key,'MARK',at,'','',{'equity':equity,'drawdown_pct':a['drawdown_pct']})

    # 함수 설명: 미체결 예약자금만 해제하고 체결된 수량은 유지합니다.
    def release(self, a, t):
        a['reserved'] -= t['reserve']
        t['reserve'] = 0.

    # 함수 설명: 미체결·부분체결 잔량을 구분하고 예약을 해제합니다.
    def cancel_pending(self, a, key, t, at, reason):
        self.release(a, t)
        t['status'] = 'OPEN' if t['qty'] else 'NO_FILL'
        if not t['qty']:
            t['target'] = 0
        self.emit('events', 'NO_FILL' if not t['qty'] else 'PARTIAL_ENTRY_CANCEL', at, t['code'],
                  dict(policy=key, strategy=t['strategy'], trade_id=t['id'], reason=reason, remaining=max(0, t['target'] - t['qty'])))
        self.account_event(a, key, 'RELEASE', at, t['code'], t['id'])

    # 함수 설명: 매도가능호가를 기준으로 TP/SL/시간청산·부분청산·비용을 계산합니다.
    def exit_quote(self, a, key, t, c, bid, qty, quote_id, quote_at, received, at):
        due = v235_dt(t['due_at'])
        if at.time() > _hhmm_time('15:20') or quote_at.time() > _hhmm_time('15:20'):
            return
        ret = (bid / t['avg_entry'] - 1) * 100
        if t['status'] == 'OPEN':
            reason = ('TAKE_PROFIT' if ret >= self.config['tp_pct'] else 'STOP_LOSS' if ret <= self.config['sl_pct'] else 'TIME_EXIT' if at >= due and quote_at >= due else None)
            if reason:
                self.release(a, t)
                t.update(status='EXIT_PENDING', exit_reason=reason, exit_trigger_at=at.isoformat())
                self.emit('events', 'EXIT_PENDING', at, t['code'], dict(policy=key, trade_id=t['id'], reason=reason))
        if t['status'] != 'EXIT_PENDING' or quote_at < v235_dt(t['exit_trigger_at']).replace(microsecond=0):
            return
        invkey = quote_id + ':SELL'
        if invkey in t['inventory']:
            return
        t['inventory'][invkey] = True
        quantity = min(t['qty'] - t['sold'], int(qty * self.config['depth_fraction']))
        if quantity < 1:
            return
        amount = quantity * bid
        cost = t['avg_entry'] * quantity * self.config['cost_pct'] / 100
        t['sold'] += quantity
        t['sell_amount'] += amount
        t['cost'] += cost
        a['cash'] += amount - cost
        self.emit('events', 'EXIT_FILL', at, t['code'], dict(policy=key, trade_id=t['id'], strategy=t['strategy'],
                   qty=quantity, price=bid, quote_id=quote_id, quote_at=quote_at.isoformat(), received_at=received.isoformat(), reason=t['exit_reason'],
                   time_overshoot_sec=max(0., (at-due).total_seconds())))
        if t['sold'] == t['qty']:
            t['status'] = 'CLOSED'
            t['exit_at'] = at.isoformat()
            gross = (t['sell_amount'] / t['buy_amount'] - 1) * 100
            t.update(gross_pct=gross, net_pct=gross-self.config['cost_pct'], net_pnl=t['sell_amount']-t['buy_amount']-t['cost'])
            self.emit('events', 'EXIT', at, t['code'], dict(policy=key, trade_id=t['id'], strategy=t['strategy'], buy_amount=t['buy_amount'], index_decision=t['signal']['context']['index_decision'],
                      gross_pct=t['gross_pct'], net_pct=t['net_pct'], net_pnl=t['net_pnl'], break_even_cost_pct=gross,
                      cost_headroom_pct=t['net_pct'], stresses={str(s):t['net_pct']-s for s in (0.1,0.2,0.4)},
                      hold_sec=(at-v235_dt(t['first_fill_at'])).total_seconds(), reference_model='REFERENCE_gross_signal_to_exit_minus_0p24',
                      reference_net_pct=((t['sell_amount']/t['sold'])/t['signal']['signal_price']-1)*100-self.config['cost_pct']))
            if key == 'UNFILTERED':
                self.notice(t, '가상청산', at, bid)
        self.account_event(a, key, 'EXIT_FILL', at, t['code'], t['id'])

    # 함수 설명: 조기청산과 독립적으로 체결 후 1/3/5분 지수·가격을 관찰합니다.
    def path_quote(self,t,c,key,bid,quote_id,at):
        ret=(bid/t['avg_entry']-1)*100
        for horizon in (60, 180, 300):
            if horizon not in t['horizons'] and at >= v235_dt(t['first_fill_at']) + timedelta(seconds=horizon):
                t['horizons'].append(horizon)
                self.emit('events', 'PATH_' + str(horizon // 60), at, t['code'], dict(policy=key, trade_id=t['id'], return_pct=ret,
                          context=self.context(at, c, bid), quote_id=quote_id, overshoot_sec=(at-v235_dt(t['first_fill_at'])).total_seconds()-horizon))

    # 함수 설명: 주 정책의 가상체결·청산 알림을 영속 예약합니다.
    def notice(self, t, kind, at, price):
        key = t['id'] + ':' + kind
        name=self.s['candidates'][t['code']]['name']
        signal_at=v235_dt(t['signal']['signal_at'])
        detected_at=v235_dt(t['signal']['detected_at'])
        text=(f"🔬 {V235_NAMES[t['strategy']]} {kind}\n\n{name}\n종목코드 : {t['code']}\n\n"
              f"⏱ 시각\n- 신호 : {signal_at:%H:%M:%S}\n- 검출 : {detected_at:%H:%M:%S}\n- 체결 : {at:%H:%M:%S}\n\n"
              f"💰 가격\n- 신호가 : {t['signal']['signal_price']:,.0f}원\n- 가상체결가 : {price:,.0f}원\n\n"
              f"🎯 전략\n- TP +{self.config['tp_pct']:.2f}% / SL {self.config['sl_pct']:.2f}%\n"
              f"- 지수 : {t['signal']['context']['index_decision']}\n\n연구용 가상진입\n실제주문 없음")
        self.s['outbox'].setdefault(key, dict(status='PENDING', text=text))

    # 함수 설명: 미체결 만료·미확정 청산과 일별 평가를 점검합니다.
    def maintain(self, at, ending=False):
        for c in self.s['candidates'].values():
            end=at.replace(second=0,microsecond=0)-timedelta(minutes=1)
            for strategy,start,finish in ((V235_A,'09:02','09:10'),(V235_B,'09:05','10:00')):
                if v234_between(end,start,finish) and end>v235_dt(c['registered']) and (at-end).total_seconds()>=60:
                    self.evaluation(c,at,dict(strategy=strategy,status='DATA_UNAVAILABLE',reasons=['NO_COMPLETE_EVALUATION_AT_DEADLINE'],evaluation_at=end.isoformat()))
            if c.get('bar') and at >= v235_dt(c['bar']['minute']) + timedelta(minutes=2):
                self.gap(c, at, 'NO_TICK_MINUTE_GAP')
        for key, a in self.s['accounts'].items():
            for t in a['trades'].values():
                if t['reserve'] and at >= v235_dt(t['deadline']):
                    self.cancel_pending(a, key, t, at, 'WAIT_EXPIRED')
                if t['status'] == 'OPEN' and at >= v235_dt(t['due_at']):
                    t.update(status='EXIT_PENDING', exit_reason='TIME_EXIT', exit_trigger_at=t['due_at'])
                if (ending or at.time() >= _hhmm_time('15:20')) and t['status'] in ('PENDING','OPEN','EXIT_PENDING'):
                    self.release(a, t)
                    t['status'] = 'EXIT_UNCONFIRMED' if t['qty'] > t['sold'] else 'NO_FILL'
                    self.emit('events', t['status'], at, t['code'], dict(policy=key, trade_id=t['id'], strategy=t['strategy'], remaining=t['qty']-t['sold'], price=None))
        if ending or at.second == 0:
            self.daily(at)
            if ending or at.strftime('%H:%M')=='15:30':
                v235_scorecard(self,at)

    # 함수 설명: 공유 구독의 상태와 수용량을 확인하여 요청을 처리합니다.
    def daily(self, at):
        rows = self.db.execute("SELECT kind,payload FROM journal WHERE day=? AND stream='events' AND kind IN ('SIGNAL','EVALUATION')", (self.day,)).fetchall()
        for key, a in self.s['accounts'].items():
            if key.startswith('PAIR:'):
                continue
            for strategy in (V235_A, V235_B):
                trades = [t for t in a['trades'].values() if t['strategy'] == strategy]
                closed = [t for t in trades if t['status'] == 'CLOSED']
                nets = [t['net_pct'] for t in closed]
                pos = sum(x for x in nets if x > 0)
                neg = -sum(x for x in nets if x < 0)
                evals = [json.loads(p) for k,p in rows if k == 'EVALUATION' and json.loads(p)['strategy'] == strategy and json.loads(p)['status'] not in ('TERMINAL_ALREADY_SIGNALLED','EXCLUDED_PRODUCT','EXCLUDED_RANK','WARMUP','WARMUP_REFERENCE')]
                signals = sum(k == 'SIGNAL' and json.loads(p)['strategy'] == strategy for k,p in rows)
                n = len(nets)
                self.emit('daily', 'SCORECARD', at, '', dict(policy=key, strategy=strategy, signals=signals, entries=sum(t['qty'] > 0 for t in trades),
                         no_fill=sum(t['status']=='NO_FILL' for t in trades), unconfirmed=sum(t['status']=='EXIT_UNCONFIRMED' for t in trades),
                         evaluation_denominator=len(evals), unavailable=sum(e['status']=='DATA_UNAVAILABLE' for e in evals), closed=n,
                         mean_net_pct=statistics.mean(nets) if nets else None, median_net_pct=statistics.median(nets) if nets else None,
                         mean_gross_pct=statistics.mean([t['gross_pct'] for t in closed]) if closed else None, net_pf=pos/neg if neg else None,
                         break_even_cost_pct=statistics.mean([t['gross_pct'] for t in closed]) if closed else None,
                         cost_headroom_pct=statistics.mean(nets) if nets else None,
                         net_pnl=sum(t['net_pnl'] for t in closed), account_realized_return_pct=sum(x['sell_amount']-x.get('avg_entry',0)*x['sold']-x['cost'] for x in a['trades'].values())/self.config['capital']*100, strategy_contribution_pct=sum(x.get('net_pnl',0) for x in closed)/self.config['capital']*100,
                         decision='SAMPLE_INSUFFICIENT' if n else 'NO_EVALUABLE_SAMPLE', pnl_is_estimated=True))

    # 함수 설명: 별도 읽기 연결의 SQLite backup으로 일관 스냅샷을 만들고 전체 CSV를 대조합니다.
    def export(self):
        backup_path=Path(self.path).with_suffix('.backup.sqlite3')
        snapshot=sqlite3.connect(':memory:')
        try:
            with sqlite3.connect(self.path) as source:
                source.backup(snapshot)
            assert snapshot.execute('PRAGMA quick_check').fetchone()==('ok',)
            for stream in ('universe','events','quotes','portfolio','daily'):
                path=Path(self.path).with_name('opportunity_'+stream+'_v235.csv')
                records=snapshot.execute('SELECT id,day,stream,kind,at,code,payload FROM journal WHERE stream=? ORDER BY id',(stream,)).fetchall()
                tmp=path.with_suffix('.tmp')
                with tmp.open('w',encoding='utf-8-sig',newline='') as f:
                    writer=csv.writer(f)
                    writer.writerow(('event_id','date','stream','event','at','stock_code','details'))
                    writer.writerows(records)
                    f.flush();os.fsync(f.fileno())
                with tmp.open(encoding='utf-8-sig',newline='') as f:
                    check=list(csv.reader(f))[1:]
                assert check==[[str(x) for x in r] for r in records]
                os.replace(tmp,path)
            with sqlite3.connect(str(backup_path)) as target:
                snapshot.backup(target)
            return True
        except (OSError,sqlite3.Error,AssertionError):
            return False
        finally:
            snapshot.close()

# 함수 설명: 공식 고정폭 마스터에서 보통주·우선주·SPAC을 구분합니다.
def v235_parse_master(blob, market, day):
    schema = V235_MASTER_SCHEMAS[market]
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        name = 'kospi_code.mst' if market == 'KOSPI' else 'kosdaq_code.mst'
        text = archive.read(name).decode('cp949')
    result = {}
    for line in text.splitlines():
        width = sum(schema['widths'])
        if len(line) < width + 21:
            raise ValueError('master fixed-width schema mismatch')
        first, tail = line[:-width], line[-width:]
        code = first[:9].strip()
        if len(code) != 6:
            continue
        offset, fields = 0, []
        for w in schema['widths']:
            fields.append(tail[offset:offset+w].strip())
            offset += w
        group, preferred, spac = (fields[schema[k]] for k in ('group', 'preferred', 'spac'))
        if preferred not in ('0','1','2') or spac not in ('Y','N'):
            continue
        result[code] = dict(market=market, day=day, ordinary=group == 'ST' and preferred == '0' and spac == 'N',
                            group=group, preferred=preferred, spac=spac, source='KIS_PUBLIC_MASTER', sha256=hashlib.sha256(blob).hexdigest())
    return result

# 함수 설명: 로그인 없는 공식 분류자료를 받고 결측은 평가불가로 남깁니다.
def v235_fetch_master(day):
    result = {}
    for market, name in (('KOSPI','kospi'),('KOSDAQ','kosdaq')):
        try:
            response = requests.get('https://new.real.download.dws.co.kr/common/master/' + name + '_code.mst.zip', timeout=20)
            response.raise_for_status()
            result.update(v235_parse_master(response.content, market, day))
        except Exception as exc:
            log(f'[상품분류 평가불가] {market} {type(exc).__name__}')
    v235_enqueue('MASTER', '', datetime.now(), result)

# 함수 설명: 외부 시세를 유한 큐로 전달하고 누락은 후보별 gap으로 기록합니다.
def v235_enqueue(kind, code, received, data):
    try:
        v235_queue.put_nowait((kind, code, received, copy.deepcopy(data)))
    except queue.Full:
        v235_drops.add(code or '*')

# 함수 설명: 입력을 순서대로 처리하고 후보 오류와 공용 원장 오류를 분리합니다.
def v235_loop():
    while True:
        event = v235_queue.get()
        try:
            if event is None:
                return
            kind, code, received, data = event
            with V235_LOCK:
                now = datetime.now()
                if v235_engine is None:
                    continue
                for dropped in tuple(v235_drops):
                    v235_engine.process('GAP', '' if dropped == '*' else dropped, now, {'reason':'QUEUE_DROP'}, now)
                    v235_drops.discard(dropped)
                try:
                    v235_engine.process(kind, code, received, data, now)
                except (ValueError, TypeError, KeyError) as exc:
                    if code in v235_engine.s['candidates']:
                        v235_engine.gap(v235_engine.s['candidates'][code], now, 'CANDIDATE_ERROR:'+type(exc).__name__)
                        v235_engine.commit()
                    else:
                        raise
                if kind in ('RANK','MASTER'):
                    v235_sync_subscriptions()
        except Exception as exc:
            if v235_engine:
                v235_engine.halted = True
            log(f'[v235 원장/후보 오류] {type(exc).__name__}: {exc}')
        finally:
            v235_queue.task_done()

# 함수 설명: KST 운영시간을 확인하고 상태원장과 처리 worker를 시작합니다.
def v235_start(now):
    global v235_engine, v235_thread, v235_master_future
    if abs((datetime.now() - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() - 32400) > 60 and not OFF_HOURS_VALIDATION_MODE:
        raise RuntimeError('시스템 시간대를 Asia/Seoul(KST)로 설정하세요.')
    with V235_LOCK:
        v235_engine = Opportunity235('opportunity_state_v235.sqlite3', now)
    if v235_thread is None or not v235_thread.is_alive():
        v235_thread = threading.Thread(target=v235_loop, daemon=True, name='Opportunity235')
        v235_thread.start()


# 함수 설명: 주기 점검·CSV·전략별 알림 작업을 스케줄합니다.
def v235_maintenance(now, ending=False):
    if v235_engine is None:
        return
    with V235_LOCK:
        if v235_queue.unfinished_tasks:
            return
        v235_schedule_references(now)
        v235_engine.process('MAINTAIN', '', now, {'ending':ending}, now)
        if ending or time.monotonic()-v235_engine.last_export>=60:
            v235_schedule_export(ending)
        v235_schedule_notifications()
        hhmm = now.strftime('%H:%M')
        if hhmm in V220_SUMMARY_TIMES and hhmm not in v235_engine.s.setdefault('summaries', []):
            v235_engine.s['summaries'].append(hhmm)
            for strategy in (V235_A, V235_B):
                parts = []
                for policy in ('UNFILTERED','INDEX_UP'):
                    a = v235_engine.s['accounts'][policy]
                    trades = [t for t in a['trades'].values() if t['strategy']==strategy and t['qty']]
                    parts.append(f"• {policy}: 누적 가상체결 {len(trades)}건 / 완료 {sum(t['status']=='CLOSED' for t in trades)}건")
                v235_engine.s['outbox'][hhmm+strategy] = dict(status='PENDING', text=f"🔬 {V235_NAMES[strategy]} 누적 {hhmm}\n"+'\n'.join(parts)+'\n연구용 가상진입 / 실제주문 없음')
            v235_engine.commit()
