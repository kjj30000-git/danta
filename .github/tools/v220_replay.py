# 함수 설명: 새 프로세스/장외 모드에서만 실행하는 외부연결 없는 결정론적 회귀 fixture입니다.
def run_v220_off_hours_validation():
    if EXECUTION_MODE != 'RESEARCH' or AUTO_TRADE_ENABLED or USE_MOCK:
        raise RuntimeError('RESEARCH 전용 검증')
    if research_tick_worker_started or (v220_notify_thread and v220_notify_thread.is_alive()):
        raise RuntimeError('운영 worker가 없는 새 커널에서 검증하세요.')
    names = list(V220_STATE_GLOBALS) + ['v220_candidates','v220_signals','v220_outbox','v220_date','v220_halted',
        'v220_last_checkpoint','v220_fill_keys','v220_metrics','V220_STATE_FILE','PAPER_TRADE_FILE','websocket_manager',
        'enqueue_research_rows','log','send_telegram','start_entry_path_tracking','start_policy_shadow_tracking',
        'start_wide_snapshot_tracking','datetime','shutdown_requested','V220_SUMMARY_ENABLED',
        'entry_path_ids_by_code','post_exit_ids_by_code','policy_shadow_trackers','wide_snapshot_trackers',
        'live_positions','live_orders','PAPER_TRADE_ENABLED','AUTO_PAPER_ENTRY','WEBSOCKET_ENABLED',
        'PULLBACK_SUPPORT_ENABLED','PULLBACK_RECLAIM_ENABLED','PULLBACK_START_PCT','PULLBACK_BREAK_TOLERANCE_PCT',
        'PULLBACK_CANDIDATE_BARS','PULLBACK_CONFIRM_BARS','PULLBACK_RECOVERY_PCT','PULLBACK_RECLAIM_BARS',
        'PULLBACK_RECLAIM_BUFFER_PCT','PROGRAM_START','PROGRAM_END','V220_SUMMARY_TIMES']
    saved = {k: globals()[k] for k in names}
    results, rows, messages = [], [], []
    real_datetime = datetime

    # 함수 설명: runtime datetime 이름을 교체해 부모와 신규 함수를 동일 시계로 검증합니다.
    class Clock(real_datetime):
        moment = real_datetime(2026, 9, 22, 9, 5)
        @classmethod
        def now(cls, tz=None):
            return cls.fromtimestamp(cls.moment.timestamp(), tz)

    # 함수 설명: 외부 구독 없이 code당 한 번의 구독 의미를 재현합니다.
    class FakeWS:
        def __init__(self): self.codes = set(); self.removes = []
        def subscribe_stock(self, code, session=None): self.codes.add(code)
        def unsubscribe_stock(self, code): self.codes.discard(code); self.removes.append(code)
        def stop(self): pass

    # 함수 설명: 결과를 assertion과 함께 기록합니다.
    def check(condition, label):
        if not condition: raise AssertionError(label)
        results.append(label)

    # 함수 설명: 고정 입력의 정상 스캐너 후보를 반환합니다.
    def stock(code='999901', moment=None):
        moment = moment or Clock.now()
        return {'stock_code':code, 'stock_name':'검증종목', 'market':'KOSPI', 'current_price':100.0,
            'score':80, 'score_detail':{'trading_value':40}, 'actual_trading_value':30_000_000_000,
            'estimated_trading_value':30_000_000_000, 'trading_value_used':30_000_000_000,
            'trading_value_source':'ACTUAL','change_rate':7.0,'volume':500000,
            'day_high':100.,'high_gap':0.,'value_growth':1.5,'volume_growth':1.3,
            'watch_episode_id':'FIXTURE_EP','score_time':moment, '_score_evaluated_ts':moment.timestamp(),
            'scan_session':get_session_at(moment), 'decision_session':get_session_at(moment), 'decision_time':moment,
            'history_available_sec':90,'price_change_30s':.3,'price_change_60s':1.,'high_gap_change_60s':-.1}

    # 함수 설명: 독립 후보를 실제 부모 진입함수로 등록합니다.
    def candidate(code='999901'):
        st = stock(code); tid = open_paper_trade(st,'BASE')
        check(bool(tid), f'{code}: BASE actual function creates trade')
        return v220_candidates[code]

    # 함수 설명: 하나의 완결된 1분봉을 구성합니다.
    def bar(index, low=98., close=98.5, high=98.6, valid=True):
        return {'minute': Clock(2026,9,22,9,6)+timedelta(minutes=index), 'open':close,
            'high':high,'low':low,'close':close,'volume':100.,'tick_count':10,'valid':valid}

    # 함수 설명: 완료봉을 실제 상태머신에 입력합니다.
    def advance(c, b):
        Clock.moment=b['minute']+timedelta(minutes=1)
        v220_complete_bar(c,b,Clock.now())

    with tempfile.TemporaryDirectory(prefix='v220_offhours_') as temp:
        try:
            globals()['datetime']=Clock
            for k in V220_STATE_GLOBALS:
                globals()[k]=set() if isinstance(saved[k],set) else {}
            for k in ['entry_path_ids_by_code','post_exit_ids_by_code','policy_shadow_trackers',
                      'wide_snapshot_trackers','live_positions','live_orders']:
                globals()[k]={}
            globals().update(v220_candidates={}, v220_signals={m:{} for m in V220_MODES},v220_outbox={},
                v220_date='',v220_fill_keys=set(),v220_halted=False,v220_last_checkpoint=0.,shutdown_requested=False,
                v220_metrics={'ticks':0,'gaps':0,'bars':0,'invalid_bars':0,'save_failures':0},
                V220_STATE_FILE=str(Path(temp)/'state.json'),PAPER_TRADE_FILE=str(Path(temp)/'trades.csv'),
                websocket_manager=FakeWS(), log=lambda *a,**k:None,
                enqueue_research_rows=lambda file, batch, *a, **k: (rows.extend((file,dict(r)) for r in batch) or True),
                send_telegram=lambda text:(messages.append(text) or True),
                start_entry_path_tracking=lambda *a:None,start_policy_shadow_tracking=lambda *a:None,
                start_wide_snapshot_tracking=lambda *a:None,PAPER_TRADE_ENABLED=True,AUTO_PAPER_ENTRY=True,
                WEBSOCKET_ENABLED=True,V220_SUMMARY_ENABLED=True,PULLBACK_SUPPORT_ENABLED=True,
                PULLBACK_RECLAIM_ENABLED=True,PULLBACK_START_PCT=1.5,PULLBACK_BREAK_TOLERANCE_PCT=.3,
                PULLBACK_CANDIDATE_BARS=3,PULLBACK_CONFIRM_BARS=5,PULLBACK_RECOVERY_PCT=.4,
                PULLBACK_RECLAIM_BARS=5,PULLBACK_RECLAIM_BUFFER_PCT=.1,PROGRAM_START='08:00',PROGRAM_END='20:00',
                V220_SUMMARY_TIMES=['09:30','10:30','11:30','12:30','13:30','14:30','15:30'])
            v220_reset_day(Clock.now())
            c = candidate()
            base_tid = next(iter(paper_positions))
            check(len(paper_positions[base_tid]['strategies'])==169,'BASE 169-grid preserved')
            s=stock(); s['pre_entry_type']='FIRST_75_PASS'
            tid=open_paper_trade(s,'PRE_HISTORY',{'pre_entry_type':'FIRST_75_PASS'})
            check(bool(tid) and c['candidate_source']=='BOTH' and len(v220_candidates)==1,'BASE then FIRST -> BOTH single watcher')
            check(len(websocket_manager.codes)==1,'same code subscription idempotent')
            for mode in V220_OFF_MODES:
                check(open_paper_trade(stock('999902'),mode) is None,mode+' disabled at entry gate')
            check(open_paper_trade(stock('999902'),'PRE_HISTORY',{'pre_entry_type':'LATER_PASS'}) is None,'LATER disabled')
            s=stock('999903'); s['pre_entry_type']='FIRST_75_PASS'
            open_paper_trade(s,'PRE_HISTORY',{'pre_entry_type':'FIRST_75_PASS'})
            check(v220_candidates['999903']['candidate_source']=='FIRST_75_PASS','FIRST-only source')
            open_paper_trade(s,'BASE')
            check(v220_candidates['999903']['candidate_source']=='BOTH','FIRST then BASE -> BOTH')
            # 169/grid validation is atomic and selected rules remain unchanged.
            before=len(paper_positions)
            try:open_paper_trade(stock('999904'),'BASE',exit_strategies={})
            except ValueError:pass
            else:raise AssertionError('empty grid accepted')
            check(len(paper_positions)==before,'invalid grid leaves no half-position')
            # State: peak then exact pullback threshold, significant-low bar excluded from count.
            advance(c,bar(0,99.0,99.5,100.0))
            advance(c,bar(1,98.51,99.,99.1))
            check(c['low'] is None,'-1.49% is not pullback')
            advance(c,bar(2,98.5,98.6,98.7))
            check(c['state']=='PULLBACK' and c['support_count']==0,'-1.50% starts pullback with zero timer')
            advance(c,bar(3,98.5,98.6,98.7));advance(c,bar(4,98.5,98.6,98.7))
            check(c['state']=='PULLBACK','two completed bars insufficient')
            advance(c,bar(5,98.5,98.6,98.7))
            check(c['state']=='SUPPORT_CANDIDATE','three completed bars support candidate')
            advance(c,bar(6,98.5,98.6,98.7));advance(c,bar(7,98.5,98.5*1.0039,98.9))
            check(not c['pending'],'five bars +0.39% insufficient')
            advance(c,bar(8,98.5,98.5*1.004,98.9))
            check(set(c['pending'])=={V220_NEW_MODES[0]},'+0.40% SUPPORT only; no same-bar RECLAIM')
            check(len(paper_positions)==before,'waiting SUPPORT signal creates zero grids')
            signal=c['pending'][V220_NEW_MODES[0]]['signal_time']
            v220_fill_pending(c,98.95,Clock.now())
            check(not c['entered'],'signal instant cannot fill')
            Clock.moment += timedelta(seconds=1)
            v220_fill_pending(c,98.95,Clock.now())
            support_tid=c['entered'][V220_NEW_MODES[0]]
            check(len(paper_positions[support_tid]['strategies'])==169,'SUPPORT next tick creates 169')
            check(paper_positions[support_tid]['entry_price']==98.95 and paper_positions[support_tid]['signal_time']==signal,'signal/fill prices and times separated')
            advance(c,bar(9,98.6,98.9*1.0009,99.0))
            check(V220_NEW_MODES[1] not in c['pending'],'prior high +0.09% no RECLAIM')
            advance(c,bar(10,98.6,99.0*1.001,99.2))
            check(V220_NEW_MODES[1] in c['pending'],'prior five highs +0.10% RECLAIM')
            Clock.moment += timedelta(seconds=1); v220_fill_pending(c,99.11,Clock.now())
            reclaim_tid=c['entered'][V220_NEW_MODES[1]]
            check(len(paper_positions[reclaim_tid]['strategies'])==169,'RECLAIM 169 independent grid')
            check(paper_positions[support_tid]['support_episode_id']==paper_positions[reclaim_tid]['support_episode_id'],'SUPPORT/RECLAIM shared episode independent trade_id')
            before=len(paper_positions)
            advance(c,bar(11,98.6,99.4,99.5));Clock.moment+=timedelta(seconds=1);v220_fill_pending(c,99.4,Clock.now())
            check(len(paper_positions)==before,'daily new-strategy duplicate prevented')
            # Tolerance/reset/falling/recovery and new peak.
            d=candidate('999905')
            advance(d,bar(0,99.,99.,100.));advance(d,bar(1,98.,98.2,98.3))
            advance(d,bar(2,98.*.997,98.2,98.3))
            check(d['support_count']==1 and d['anchor']==98.,'exact -0.30% retest keeps anchor/timer')
            advance(d,bar(3,98.*.9969,98.1,98.3))
            check(d['support_count']==0,'beyond -0.30% resets timer')
            advance(d,bar(4,97.,97.2,97.4))
            for i in range(5,10):advance(d,bar(i,97.,97.5,97.6))
            check(V220_NEW_MODES[0] in d['pending'],'FALLING can later confirm support')
            advance(d,bar(10,98.,100.5,101.))
            check(d['state']=='PEAK' and not d['pending'] and d['low'] is None,'new high resets unentered episode and pending signal')
            # Watcher survives all parent trades closing.
            for tid in list(paper_position_ids_by_code.get(c['code'],set())):paper_positions.pop(tid,None)
            paper_position_ids_by_code.pop(c['code'],None)
            maybe_release_realtime(c['code'])
            check(c['code'] in websocket_manager.codes,'candidate subscription survives paper close')
            # OHLCV aggregation and partial/sequence gaps.
            Clock.moment=Clock(2026,9,22,10,0,30);e=candidate('999906')
            v220_on_tick(e['code'],100.,Clock(2026,9,22,10,0,31),{'15':'-10'},1)
            v220_on_tick(e['code'],101.,Clock(2026,9,22,10,1,1),{'15':'20'},2)
            check(v220_metrics['invalid_bars']>0,'registration partial minute is unavailable')
            v220_on_tick(e['code'],99.,Clock(2026,9,22,10,1,20),{'15':'-30'},3)
            v220_on_tick(e['code'],100.,Clock(2026,9,22,10,2,1),{'15':'5'},4)
            check(e['history'][-1]['volume']==50 and e['history'][-1]['high']==101. and e['history'][-1]['low']==99.,'all accepted ticks aggregate OHLC and absolute volume')
            v220_on_tick(e['code'],100.,Clock(2026,9,22,10,2,20),{'15':'5'},6)
            check(v220_metrics['gaps']==1 and not e['bar']['valid'],'queue sequence gap invalidates minute')
            # Summary includes only signals before each exact cutoff; no loop duplicates.
            v220_outbox.clear()
            v220_schedule_summaries(Clock(2026,9,22,15,30))
            check(len(v220_outbox)==7,'seven 09:30..15:30 summaries scheduled')
            v220_schedule_summaries(Clock(2026,9,22,15,30,45))
            check(len(v220_outbox)==7,'same-minute summary loop no duplicates')
            text=v220_summary_text(Clock(2026,9,22,9,30))
            check('검증종목(999901)' in text and '999906' not in text,'summary cutoff filters later signals')
            check('[FIRST 75 PASS]' in text and '1. ' in text,'summary section names and numbered rows')
            text=v220_alert_text({'stock_code':'999999','stock_name':'NA','score':None},'BASE',{})
            check(all(x in text for x in ['WATCH','HISTORY','30초 가격','60초 가격','60초 고점이격','N/A']),'N/A alert complete without formatting errors')
            check('총 169개 조합 동시추적' not in text and text.startswith('[BASE]'),'old grid banner removed; strategy prefix')
            check(all(len(p)<=3500 for p in v220_message_parts('가'*8000)),'long messages split within limit')
            check(v220_notify_once(),'outbox sender success')
            # Recovery uses exact tuple-key codec and marks data gaps.
            v220_checkpoint(True)
            expected_keys=set(paper_entered_today)
            expected_outbox=len(v220_outbox)
            check(v220_restore(Clock.now()),'same-day recovery success')
            check(paper_entered_today==expected_keys,'tuple entry keys survive JSON roundtrip')
            check(len(v220_outbox)==expected_outbox,'summary sent keys recover')
            check(not any(x['pending'] for x in v220_candidates.values()),'restart stale pending fills cancelled')
            c=v220_candidates['999901']
            check(V220_NEW_MODES[0] in c['entered'] and V220_NEW_MODES[1] in c['entered'],'restart new strategy daily limits persist')
            # Session boundary records explicit no-fill, no trade.
            c['pending'][V220_NEW_MODES[0]]={'signal_time':Clock(2026,9,22,15,29),'signal_detected_time':Clock(2026,9,22,15,29,59), 'signal_price':100.}
            before=len(paper_positions)
            v220_fill_pending(c,100.,Clock(2026,9,22,15,30))
            check(not c['pending'] and len(paper_positions)==before,'15:30 session boundary NO_FILL')
            check(any(r.get('event')=='NO_FILL_SESSION_END' for _,r in rows),'NO_FILL_SESSION_END ledger persisted')
            v220_reset_day(Clock(2026,9,23,8))
            check(not v220_candidates and not v220_outbox and not any(v220_signals.values()),'new day resets daily state')
            report={'status':'PASS','version':STRATEGY_VERSION,'checks':results,'check_count':len(results),
                'external_connections':0,'broker_orders':0,'captured_rows':len(rows)}
            print(json.dumps(report,ensure_ascii=False,indent=2))
            return report
        finally:
            globals().update(saved)
