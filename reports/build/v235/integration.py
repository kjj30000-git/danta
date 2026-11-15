# 함수 설명: 부모와 새 포지션/후보가 필요한 시세를 해지로 삭제하지 않습니다.
def v235_keep_ticks(code):
    if code in live_positions or paper_position_ids_by_code.get(code) or entry_path_ids_by_code.get(code) or post_exit_ids_by_code.get(code):
        return True
    if code in v220_candidates or v234_needs_ticks(code):
        return True
    if v235_engine:
        with V235_LOCK:
            c = v235_engine.s['candidates'].get(code)
            return bool(c and (c['active'] or v235_engine.protected(code)))
    return False

# 함수 설명: 서버 해지 ACK 뒤에만 로컬 구독 슬롯을 회수합니다.
async def v235_remove_confirmed(manager, item, code):
    if await manager._remove_item(item):
        with manager.lock:
            manager.desired_items.get(code,set()).discard(item)

# 함수 설명: 종료 시 raw 이벤트를 배출하고 남은 공백을 명시합니다.
def v235_drain():
    deadline = time.monotonic() + RESEARCH_FLUSH_TIMEOUT_SEC
    while v235_queue.unfinished_tasks and time.monotonic() < deadline:
        time.sleep(.02)
    if v235_queue.unfinished_tasks and v235_engine:
        with V235_LOCK:
            v235_engine.halted=True
            v235_engine.emit('events','SHUTDOWN_BACKLOG',datetime.now(),'',dict(backlog=v235_queue.unfinished_tasks))
            v235_engine.commit()

v235_reference_futures = {}

# 함수 설명: 실제 구독관리자를 통해 top20을 등록하고 부모관찰과 수용량을 공유합니다.
def v235_sync_subscriptions():
    if websocket_manager is None or v235_engine is None:
        return
    for c in sorted(v235_engine.s['candidates'].values(), key=lambda x:(not v235_engine.protected(x['code']),x.get('rank',999),x['code'])):
        if c['active'] or v235_engine.protected(c['code']):
            v235_subscribe_krx(websocket_manager,c['code'])
        elif not v235_engine.protected(c['code']):
            manager=websocket_manager
            with manager.lock:
                item=c['code']
                if item in manager.desired_items.get(item,set()) and item not in manager.v235_removing and manager.logged_in and manager.loop is not None:
                    manager.v235_removing.add(item)
                    asyncio.run_coroutine_threadsafe(v235_remove_confirmed(manager,item,item),manager.loop)

# 함수 설명: 개장참조 조회는 신호 경로와 분리된 읽기 전용 worker에서 1회 수행합니다.
def v235_reference_query(code, day):
    try:
        row = kiwoom_post('/api/dostk/chart','ka10080',dict(stk_cd=code,tic_scope='1',upd_stkpc_tp='0',base_dt=day.replace('-','')),
                          priority=API_PRIORITY_OTHER,request_class='OPENING_REFERENCE_READONLY')
        v235_enqueue('REFERENCE',code,datetime.now(),row)
    except Exception as exc:
        v235_enqueue('REFERENCE',code,datetime.now(),{'error':type(exc).__name__})

# 함수 설명: 09:05 이후에만 완결된 개장 참조봉 조회를 스케줄합니다.
def v235_schedule_references(now):
    if not v234_between(now,'09:07','10:00') or not v235_engine:
        return
    for c in v235_engine.s['candidates'].values():
        key=(v235_engine.day,c['code'],now.minute)
        if c['active'] and c['b_status'] in ('WAIT_RANGE','WAIT_REFERENCE') and (key not in v235_reference_futures or v235_reference_futures[key].done()):
            v235_reference_futures[key]=v234_index_executor.submit(v235_reference_query,c['code'],v235_engine.day)

# 함수 설명: 부모 SOR 구독은 유지하고 A/B에는 별도 KRX 체결·호가 pair만 추가합니다.
def v235_subscribe_krx(manager, code):
    with manager.lock:
        items=manager.desired_items.setdefault(code,set())
        if code in items:
            return True
        if not v235_subscription_admit(manager,code,['0B','0D']):
            return False
        items.add(code)
    if manager.logged_in and manager.loop is not None:
        asyncio.run_coroutine_threadsafe(manager._register_item(code),manager.loop)
    return True

# 함수 설명: 인증경계가 지난 뒤 공개 분류자료만 비동기로 가져옵니다.
def v235_launch_master():
    global v235_master_future
    v235_master_future=v234_index_executor.submit(v235_fetch_master,datetime.now().date().isoformat())

# 함수 설명: 일별·종목 집중과 날짜군집 불확실성을 포함한 고정 실험 성과표를 작성합니다.
def v235_scorecard(engine, at):
    import random
    exits=[dict(json.loads(p),at=stamp) for stamp,p in engine.db.execute("SELECT at,payload FROM journal WHERE kind='EXIT' ORDER BY id")]
    evaluations_all=[json.loads(p) for p, in engine.db.execute("SELECT payload FROM journal WHERE kind='EVALUATION'")]
    evaluations=[r for r in evaluations_all if r['status'] not in ('TERMINAL_ALREADY_SIGNALLED','EXCLUDED_PRODUCT','EXCLUDED_RANK','WARMUP','WARMUP_REFERENCE')]
    fills=[json.loads(p) for p, in engine.db.execute("SELECT payload FROM journal WHERE kind='FILL' AND stream='events'")]
    archived=[json.loads(p) for p, in engine.db.execute('SELECT payload FROM state')]
    rows=[]
    for policy in ('UNFILTERED','INDEX_UP','UNFILTERED_DELAY_1','UNFILTERED_DELAY_3','UNFILTERED_DELAY_5','INDEX_UP_DELAY_1','INDEX_UP_DELAY_3','INDEX_UP_DELAY_5'):
        for strategy in (V235_A,V235_B,'ALL_SHARED'):
            selected=[r for r in exits if r['policy']==policy and (strategy=='ALL_SHARED' or r['strategy']==strategy)]
            nets=[r['net_pct'] for r in selected]
            by_day,by_stock={},{}
            for r in selected:
                by_day[r['date']]=by_day.get(r['date'],0)+r['net_pnl']
                by_stock[r['stock_code']]=by_stock.get(r['stock_code'],0)+r['net_pnl']
            total=sum(by_day.values());positive=sum(max(0,r['net_pnl']) for r in selected)
            pos=sum(max(0,r['net_pnl']) for r in selected);neg=-sum(min(0,r['net_pnl']) for r in selected)
            pf=pos/neg if neg else None
            eq=engine.config['capital'];peak=eq;dd=0.
            for r in selected:
                eq+=r['net_pnl'];peak=max(peak,eq);dd=max(dd,(peak-eq)/engine.config['capital']*100)
            daymeans={d:statistics.mean([r['net_pct'] for r in selected if r['date']==d]) for d in by_day}
            lcb=None
            if len(daymeans)>=2:
                rng=random.Random(261116)
                vals=list(daymeans.values())
                boot=sorted(statistics.mean(rng.choices(vals,k=len(vals))) for _ in range(2000))
                lcb=boot[99]
            ev=[r for r in evaluations if strategy=='ALL_SHARED' or r['strategy']==strategy]
            unavailable=sum(r['status']=='DATA_UNAVAILABLE' for r in ev)
            availability=1-unavailable/len(ev) if ev else None
            day_con=max(by_day.values(),default=0)/positive if positive else None
            stock_con=max(by_stock.values(),default=0)/positive if positive else None
            stress20=sum(r['net_pnl']-(r.get('buy_amount',0)*.002) for r in selected) if selected else None
            # EXIT explicitly includes actual buy amount; absent historical fields are unavailable, never zero-cost.
            if selected and any('buy_amount' not in r for r in selected):stress20=None
            normal_days=sum(sum(r['status']!='DATA_UNAVAILABLE' for r in ev if r['date']==day)/len([r for r in ev if r['date']==day])>=.95 for day in {r['date'] for r in ev})
            completed_ids={r['trade_id'] for r in selected}
            pending_ids={r['trade_id'] for r in fills if r['policy']==policy and (strategy=='ALL_SHARED' or r['strategy']==strategy)}-completed_ids
            historical_missing_marks=sum(state.get('accounts',{}).get(policy,{}).get('mark_missing_count',0) for state in archived)
            status='SAMPLE_INSUFFICIENT'
            if at.date().isoformat()>=engine.config['decision_date'] and not selected:status='DATA_INVALID' if not ev or not availability else 'SAMPLE_INSUFFICIENT'
            if normal_days>=engine.config['pass_min_days'] and len(selected)>=engine.config['pass_min_fills'] and len(by_stock)>=engine.config['pass_min_symbols']:
                mark_rows=[json.loads(p) for p, in engine.db.execute("SELECT payload FROM journal WHERE kind='MARK'") if json.loads(p).get('policy')==policy]
                marked_dd=max((r.get('drawdown_pct',0) for r in mark_rows),default=None)
                missing_marks=engine.s['accounts'][policy].get('mark_missing_count',0)
                status='PASS' if (not pending_ids and not historical_missing_marks and marked_dd is not None and marked_dd<=5 and not missing_marks and total>0 and pf is not None and pf>=1.2 and lcb is not None and lcb>0 and stress20 is not None and stress20>0
                    and total-max(by_day.values())>0 and total-max(by_stock.values())>0 and dd<=5 and availability is not None and availability>=.95
                    and day_con is not None and day_con<=.30 and stock_con is not None and stock_con<=.30) else 'FAIL_OR_ADDITIONAL_OBSERVATION'
            rows.append(dict(policy=policy,strategy=strategy,trades=len(selected),dates=len(by_day),symbols=len(by_stock),normal_days=normal_days,
                             mean_net_pct=statistics.mean(nets) if nets else None,median_net_pct=statistics.median(nets) if nets else None,
                             net_pf=pf,total_net_pnl=total,account_realized_return_pct=total/engine.config['capital']*100,
                             realized_drawdown_pct=dd,drawdown_limit='REALIZED_ONLY_OPEN_POSITIONS_UNCERTAIN',date_cluster_one_sided95_lcb_pct=lcb,
                             without_best_day_pnl=total-max(by_day.values(),default=0),without_best_stock_pnl=total-max(by_stock.values(),default=0),
                             best_day_positive_concentration=day_con,best_stock_positive_concentration=stock_con,stress20_pnl=stress20,
                             evaluations=len(ev),terminal_or_warmup_excluded=sum((strategy=='ALL_SHARED' or r['strategy']==strategy) and r['status'] in ('TERMINAL_ALREADY_SIGNALLED','EXCLUDED_PRODUCT','EXCLUDED_RANK','WARMUP','WARMUP_REFERENCE') for r in evaluations_all),unavailable=unavailable,availability=availability,unresolved_trade_ids=sorted(pending_ids),unresolved_count=len(pending_ids),decision=status,
                             uncertainty='date+symbol clusters; repeated weekly comparisons; no power guarantee; marked-equity drawdown also required'))
    # Pair comparisons are never added to shared account results.
    paired=[r for r in exits if r['policy'].startswith('PAIR:')]
    for decision in ('PASS','FAIL','DATA_UNAVAILABLE'):
        p=[r for r in paired if r.get('index_decision')==decision]
        rows.append(dict(policy='PAIRED_BEFORE_CAPITAL',strategy='ALL_SHARED',index_decision=decision,trades=len(p),
                         mean_net_pct=statistics.mean([r['net_pct'] for r in p]) if p else None,
                         net_pnl=sum(r['net_pnl'] for r in p),label='filter_kept' if decision=='PASS' else 'avoided_loss_and_missed_profit' if decision=='FAIL' else 'not_index_comparable'))
    engine.emit('daily','FIXED_EXPERIMENT_SCORECARD',at,'',{'rows':rows,'minimum_samples_are_not_power_guarantee':True})

v235_io_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='v235-export')
v235_notify_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='v235-notify')
v235_export_future=None
v235_notify_future=None

# 함수 설명: 동일 snapshot export를 한 번만 수행하며 원시입력 처리를 막지 않습니다.
def v235_schedule_export(ending=False):
    global v235_export_future
    if v235_export_future is not None and not v235_export_future.done():
        return
    if v235_export_future is not None:
        ok=v235_export_future.result()
        v235_engine.emit('events','EXPORT_OK' if ok else 'EXPORT_FAILED',datetime.now(),'',{})
        v235_engine.commit()
    v235_export_future=v235_io_executor.submit(v235_engine.export)
    v235_engine.last_export=time.monotonic()

# 함수 설명: 발송예약은 영속 저장하고 Telegram 응답대기는 잠금 밖에서 수행합니다.
def v235_send_pending():
    while True:
        with V235_LOCK:
            pending=next(((k,r) for k,r in v235_engine.s['outbox'].items() if r['status']=='PENDING'),None)
            if pending is None:
                return
            key,row=pending
            row['status']='DELIVERY_UNKNOWN'
            v235_engine.commit()
            text=row['text']
        success=send_telegram(text)
        with V235_LOCK:
            v235_engine.s['outbox'][key]['status']='SENT' if success else 'DELIVERY_UNKNOWN'
            v235_engine.commit()

# 함수 설명: 외부발송 중에는 다음 발송 worker를 중복 생성하지 않습니다.
def v235_schedule_notifications():
    global v235_notify_future
    if v235_notify_future is None or v235_notify_future.done():
        if any(r['status']=='PENDING' for r in v235_engine.s['outbox'].values()):
            v235_notify_future=v235_notify_executor.submit(v235_send_pending)

# 함수 설명: 최종 export를 시세 drain 뒤 실행해 종료 원장과 CSV를 일치시킵니다.
def v235_finalize():
    v235_drain()
    if v235_export_future is not None:
        v235_export_future.result(timeout=RESEARCH_FLUSH_TIMEOUT_SEC)
    with V235_LOCK:
        if v235_engine:
            v235_engine.process('MAINTAIN','',datetime.now(),{'ending':True},datetime.now())
    if v235_engine and not v235_engine.export():
        log('[v235 종료 CSV 대조 실패] DB 보존 / 다음 실행에서 재export')
