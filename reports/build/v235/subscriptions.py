# Shared WS subscription admission/ACK helper (all groups use this one conservative budget).
# 함수 설명: 주문·기존보유·A/B 대기사건을 포함한 수용량을 item/type 단위로 계산합니다.
def v235_subscription_admit(manager, item, types, remove=False):
    with manager.lock:
        pairs = {(i,t) for i, ts in manager.v235_desired.items() for t in ts}
        desired = {(item,t) for t in types}
        priority=v235_subscription_priority(item)
        limit=V235_CONFIG['subscription_limit']-(V235_CONFIG['protected_subscription_reserve'] if priority>=3 and not desired<=pairs else 0)
        if not remove and len(pairs | desired) + 2 + int(AUTO_TRADE_ENABLED) > limit:
            v235_enqueue('SUBSCRIPTION', clean_stock_code(item), datetime.now(), dict(item=item, types=types, status='NO_CAPACITY'))
            return False
        if remove:
            manager.v235_desired.pop(item, None)
        else:
            manager.v235_desired[item] = set(types)
        return True

# 함수 설명: 원장 ACK/거절/해지 상태를 시세 후보에 연결합니다.
def v235_subscription_event(item, types, status, response=None):
    v235_enqueue('SUBSCRIPTION', clean_stock_code(item), datetime.now(), dict(item=item, types=list(types), status=status, response=response))

# 함수 설명: LOGIN 뒤 수신 loop를 막지 않는 별도 task에서 지수와 종목을 재등록합니다.
async def v235_bootstrap(manager):
    try:
        v235_restore_subscription_targets(manager)
        if AUTO_TRADE_ENABLED:
            await manager._register_order_stream()
        await manager._paced_reg_send({'trnm':'REG','grp_no':WEBSOCKET_GROUP_NO,'refresh':'1',
                                       'data':[{'item':list(V234_INDEX_CODES),'type':['0J']}]})
        await manager._reregister_all()
    except Exception as exc:
        log(f'[공용 구독 재등록 중단] {type(exc).__name__}')

# 함수 설명: 기존보유·가상보유·청산대기는 관찰용 예약용량보다 우선합니다.
def v235_subscription_priority(item):
    code=clean_stock_code(item)
    if code in live_positions:
        return 0
    if paper_position_ids_by_code.get(code):
        return 1
    engine=v235_engine
    if engine is not None:
        for account in tuple(engine.s['accounts'].values()):
            for trade in tuple(account['trades'].values()):
                if trade['code']==code and trade['qty']>trade['sold']:
                    return 1
        c=engine.s['candidates'].get(code,{})
        if c.get('b_status')=='BREAK' or any(t['code']==code and t['status']=='PENDING' for a in tuple(engine.s['accounts'].values()) for t in tuple(a['trades'].values())):
            return 2
        c=engine.s['candidates'].get(code)
        if c and c['active']:
            return 3
    return 4

# 함수 설명: 새 프로세스의 빈 desired 집합을 복원보유부터 재구성합니다.
def v235_restore_subscription_targets(manager):
    targets=set()
    for code in set(live_positions)|set(paper_position_ids_by_code):
        targets.add(realtime_item_code(code,'MAIN'))
    for code in tuple(v234_candidates):
        if v234_needs_ticks(code):
            targets.add(realtime_item_code(code,'MAIN'))
    if v235_engine:
        for c in tuple(v235_engine.s['candidates'].values()):
            if c['active'] or v235_engine.protected(c['code']):
                targets.add(c['code'])
    for item in sorted(targets,key=lambda i:(v235_subscription_priority(i),i)):
        types=['0B'] if '_' in item else ['0B','0D']
        if v235_subscription_admit(manager,item,types):
            with manager.lock:
                manager.desired_items.setdefault(clean_stock_code(item),set()).add(item)
