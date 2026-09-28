#!/usr/bin/env python3
"""v2.3.1 부모 notebook에 v2.3.2 확정 변경만 국소 반영한다."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "code/releases/028_260928_v2.3.1.ipynb"
OUTPUT = ROOT / "code/releases/029_260929_v2.3.2.ipynb"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def as_source(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def main() -> None:
    notebook = json.loads(PARENT.read_text(encoding="utf-8"))
    result = copy.deepcopy(notebook)
    code_indices = [i for i, cell in enumerate(result["cells"]) if cell.get("cell_type") == "code"]
    if len(code_indices) != 5:
        raise RuntimeError(f"expected 5 code cells, found {len(code_indices)}")

    c0 = "".join(result["cells"][code_indices[0]]["source"])
    c1 = "".join(result["cells"][code_indices[1]]["source"])
    c3 = "".join(result["cells"][code_indices[3]]["source"])
    c4 = "".join(result["cells"][code_indices[4]]["source"])

    c0 = replace_once(c0, "# ★ v2.3.1 연구 운용 핵심 설정 — 실행 전 확인", "# ★ v2.3.2 연구 운용 핵심 설정 — 실행 전 확인", "cell0 title")
    c0 = replace_once(
        c0,
        'V220_SUMMARY_TIMES = ["09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30"]\n',
        'V220_SUMMARY_TIMES = ["09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30"]\n\n'
        '# v2.3.2 장기 보합 돌파 연구 — 첫 수집용 가설값\n'
        'PULLBACK_BALANCE_ENABLED = True\n'
        'BALANCE_OBSERVE_END = "15:30"\n'
        'BALANCE_ALERT_MIN_DURATION = 60\n'
        'BALANCE_MAX_RANGE_PCT = 1.50\n'
        'BALANCE_MAX_ABS_NET_CHANGE_PCT = 0.50\n'
        'BALANCE_MAX_ABS_SLOPE_PCT_PER_MIN = 0.010\n'
        'BALANCE_BREAKOUT_BUFFER_PCT = 0.10\n'
        'BALANCE_INVALIDATE_BUFFER_PCT = 0.20\n',
        "cell0 balance settings",
    )

    c1 = replace_once(c1, 'STRATEGY_VERSION = "v2.3.1"', 'STRATEGY_VERSION = "v2.3.2"', "strategy version")
    c1 = replace_once(
        c1,
        'assert STRATEGY_VERSION in {"v2.0", "v2.1", "v2.2.0", "v2.3.1"}',
        'assert STRATEGY_VERSION in {"v2.0", "v2.1", "v2.2.0", "v2.3.1", "v2.3.2"}',
        "startup version allowlist",
    )
    c1 = replace_once(
        c1,
        'assert STRATEGY_VERSION in {"v2.2.0", "v2.3.1"}',
        'assert STRATEGY_VERSION in {"v2.2.0", "v2.3.1", "v2.3.2"}',
        "opening leader version allowlist",
    )
    c1 = replace_once(c1, 'PAPER_TRADE_FILE = "paper_trades_v231.csv"', 'PAPER_TRADE_FILE = "paper_trades_v232.csv"', "paper file")
    if c1.count("V220_STATE_FILE = 'pullback_state_v231.json'") != 2:
        raise RuntimeError("state path: expected two parent definitions")
    c1 = c1.replace("V220_STATE_FILE = 'pullback_state_v231.json'", "V220_STATE_FILE = 'pullback_state_v232.json'", 1)
    c1 = replace_once(c1, "V220_STATE_FILE = 'pullback_state_v231.json'", "V220_STATE_FILE = 'pullback_state_v232.json'", "active state path")
    c1 = replace_once(c1, "V230_SNAPSHOT_FILE = 'pullback_snapshot_evaluations_v231.csv'", "V230_SNAPSHOT_FILE = 'pullback_snapshot_evaluations_v232.csv'", "expanded snapshot output")
    c1 = replace_once(
        c1,
        "V230_MODES = ('BASE', 'FIRST_75_PASS', 'PULLBACK_STRUCTURE_ENTRY',\n    'PULLBACK_SNAPSHOT_DIRECT', 'PULLBACK_SNAPSHOT_RECLAIM')\n",
        "V230_MODES = ('BASE', 'FIRST_75_PASS', 'PULLBACK_STRUCTURE_ENTRY',\n    'PULLBACK_SNAPSHOT_DIRECT', 'PULLBACK_SNAPSHOT_RECLAIM', 'PULLBACK_BALANCE_BREAKOUT')\n",
        "active modes",
    )
    c1 = replace_once(
        c1,
        "V230_SNAPSHOT_COLUMNS = ['date','version','stock_code','stock_name','candidate_source','support_episode_id',\n    'snapshot_horizon_min','scheduled_snapshot_time','actual_snapshot_time','snapshot_status','snapshot_decision',\n    'valid_l1_time','valid_l1_price','support_touch_count','higher_low_count','base_low','base_high','base_mid',\n    'base_range_pct','close_position_in_base','range_compression_ratio','descending_structure','distance_to_b_pct',\n    'volume_contraction_ratio','reclaim_volume_ratio','fixed_breakout_price_b','direct_signal_time',\n    'reclaim_signal_time','data_status','recovery_status','invalidated_later']\n",
        "V230_SNAPSHOT_COLUMNS = ['date','version','stock_code','stock_name','candidate_source','support_episode_id',\n    'snapshot_horizon_min','scheduled_snapshot_time','actual_snapshot_time','snapshot_status','snapshot_decision',\n    'valid_l1_time','valid_l1_price','support_touch_count','higher_low_count','base_low','base_high','base_mid',\n    'base_range_pct','close_position_in_base','range_compression_ratio','range_compression_unavailable_reason',\n    'descending_structure','distance_to_b_pct','volume_contraction_ratio','volume_contraction_unavailable_reason',\n    'reclaim_volume_ratio','reclaim_volume_unavailable_reason','balance_duration_min','balance_range_pct',\n    'balance_net_change_pct','trend_slope_pct_per_min','mean_abs_1m_return_pct','center_shift_pct',\n    'direction_efficiency_ratio','breakout_volume_ratio','fixed_breakout_price_b','direct_signal_time',\n    'reclaim_signal_time','data_status','recovery_status','invalidated_later']\n",
        "snapshot columns",
    )
    c1 = replace_once(
        c1,
        "    pos=((bar['close']-base_low)/(base_high-base_low) if base_high is not None and base_high>base_low else None)\n",
        "    pos=((bar['close']-base_low)/(base_high-base_low) if base_high is not None and base_high>base_low else None)\n    balance=v232_balance_features(hist,horizon)\n",
        "snapshot feature calculation",
    )
    c1 = replace_once(
        c1,
        "        'close_position_in_base':pos,'range_compression_ratio':None,'descending_structure':descending,\n        'distance_to_b_pct':((bar['close']/c['fixed_b']-1)*100 if c.get('fixed_b') else None),\n        'volume_contraction_ratio':None,'reclaim_volume_ratio':None,'fixed_breakout_price_b':c.get('fixed_b'),\n",
        "        'close_position_in_base':pos,'range_compression_ratio':balance.get('range_compression_ratio'),\n        'range_compression_unavailable_reason':balance.get('range_compression_unavailable_reason',''),\n        'descending_structure':descending,'distance_to_b_pct':((bar['close']/c['fixed_b']-1)*100 if c.get('fixed_b') else None),\n        'volume_contraction_ratio':balance.get('volume_contraction_ratio'),\n        'volume_contraction_unavailable_reason':balance.get('volume_contraction_unavailable_reason',''),\n        'reclaim_volume_ratio':balance.get('breakout_volume_ratio'),\n        'reclaim_volume_unavailable_reason':balance.get('breakout_volume_unavailable_reason',''),\n        **{k:balance.get(k) for k in ('balance_duration_min','balance_range_pct','balance_net_change_pct',\n            'trend_slope_pct_per_min','mean_abs_1m_return_pct','center_shift_pct','direction_efficiency_ratio','breakout_volume_ratio')},\n        'fixed_breakout_price_b':c.get('fixed_b'),\n",
        "snapshot populated features",
    )
    c1 = replace_once(
        c1,
        "    if decision=='READY':\n        c['snapshot_ready'][horizon]={'time':bar['minute']+timedelta(minutes=1),'b':c.get('fixed_b')}\n",
        "    if decision in {'READY','ENTRY_TIME_CLOSED'}:\n        c.setdefault('summary_snapshot_ready',{}).setdefault(horizon,bar['minute']+timedelta(minutes=1))\n    if decision=='READY':\n        c['snapshot_ready'][horizon]={'time':bar['minute']+timedelta(minutes=1),'b':c.get('fixed_b')}\n",
        "snapshot summary ready",
    )
    c1 = replace_once(
        c1,
        "    title=mode.replace('PULLBACK_','').replace('_ENTRY','')\n",
        "    title='장기 보합 돌파' if mode=='PULLBACK_BALANCE_BREAKOUT' else mode.replace('PULLBACK_','').replace('_ENTRY','')\n",
        "Korean balance entry title",
    )

    insertion_marker = "# ============================================================\n# 실행\n# ============================================================\n"
    v232_block = r'''# ============================================================
# v2.3.2 장기 보합 돌파·전략별 누적 알림 — 주문엔진과 독립
# ============================================================
V232_BALANCE_EVALUATION_FILE='pullback_balance_evaluations_v232.csv'
V232_BALANCE_EVENT_FILE='pullback_balance_events_v232.csv'
V232_BALANCE_MODE='PULLBACK_BALANCE_BREAKOUT'
V232_BALANCE_EVALUATION_COLUMNS=['date','version','stock_code','stock_name','candidate_source','evaluated_time',
    'snapshot_horizon_min','balance_duration_min','balance_range_pct','balance_net_change_pct','trend_slope_pct_per_min',
    'mean_abs_1m_return_pct','center_shift_pct','direction_efficiency_ratio','volume_contraction_ratio',
    'volume_contraction_unavailable_reason','range_compression_ratio','range_compression_unavailable_reason',
    'base_high','base_low','breakout_volume_ratio','breakout_volume_unavailable_reason','qualification','data_status']
V232_BALANCE_EVENT_COLUMNS=['date','version','event_id','event','box_id','stock_code','stock_name','event_time',
    'balance_duration_min','base_high','base_low','breakout_close','trade_id','reason']

# 함수 설명: 연속 완료봉만으로 보합·압축·거래량 feature와 계산 불가 사유를 만듭니다.
def v232_balance_features(bars,horizon):
    ordered=[b for b in bars if b.get('valid',True)]
    result={'balance_duration_min':len(ordered),'data_status':'OK'}
    if len(ordered)<horizon:
        result.update(data_status='INSUFFICIENT_DATA',range_compression_unavailable_reason='INSUFFICIENT_CURRENT_WINDOW',
            volume_contraction_unavailable_reason='INSUFFICIENT_CURRENT_WINDOW',breakout_volume_unavailable_reason='INSUFFICIENT_CURRENT_WINDOW')
        return result
    window=ordered[-horizon:]
    if any(b['minute']-a['minute']!=timedelta(minutes=1) for a,b in zip(window,window[1:])):
        result.update(data_status='NON_CONTIGUOUS_WINDOW',range_compression_unavailable_reason='NON_CONTIGUOUS_WINDOW',
            volume_contraction_unavailable_reason='NON_CONTIGUOUS_WINDOW',breakout_volume_unavailable_reason='NON_CONTIGUOUS_WINDOW')
        return result
    closes=[safe_float(b.get('close')) for b in window]; highs=[safe_float(b.get('high')) for b in window]
    lows=[safe_float(b.get('low')) for b in window]; returns=[(b/a-1)*100 for a,b in zip(closes,closes[1:]) if a>0]
    base_high=max(highs);base_low=min(lows);first=closes[0];last=closes[-1];n=len(closes);xm=(n-1)/2
    denom=sum((i-xm)**2 for i in range(n));slope=(sum((i-xm)*(v-sum(closes)/n) for i,v in enumerate(closes))/denom if denom else 0.)
    centers=[(safe_float(b.get('high'))+safe_float(b.get('low')))/2 for b in window]
    path=sum(abs(x) for x in returns);net=(last/first-1)*100 if first else None
    result.update(balance_duration_min=horizon,balance_range_pct=(base_high/base_low-1)*100 if base_low else None,
        balance_net_change_pct=net,trend_slope_pct_per_min=slope/first*100 if first else None,
        mean_abs_1m_return_pct=sum(abs(x) for x in returns)/len(returns) if returns else 0.,
        center_shift_pct=(centers[-1]/centers[0]-1)*100 if centers[0] else None,
        direction_efficiency_ratio=(abs(net)/path if net is not None and path else 0.),base_high=base_high,base_low=base_low)
    volumes=[b.get('volume') for b in window]
    if all(v is not None for v in volumes) and any(safe_float(v)>0 for v in volumes):
        half=max(1,horizon//2);left=[safe_float(v) for v in volumes[:half]];right=[safe_float(v) for v in volumes[-half:]]
        baseline=sum(left)/len(left);result['volume_contraction_ratio']=sum(right)/len(right)/baseline if baseline else None
        prior=[safe_float(v) for v in volumes[:-1] if safe_float(v)>0];base_volume=median(prior) if prior else None
        result['breakout_volume_ratio']=safe_float(volumes[-1])/base_volume if base_volume else None
        result['volume_contraction_unavailable_reason']='' if result.get('volume_contraction_ratio') is not None else 'ZERO_BASE_VOLUME'
        result['breakout_volume_unavailable_reason']='' if result.get('breakout_volume_ratio') is not None else 'ZERO_BASE_VOLUME'
    else:
        result['volume_contraction_ratio']=None;result['breakout_volume_ratio']=None
        result['volume_contraction_unavailable_reason']='VOLUME_MISSING';result['breakout_volume_unavailable_reason']='VOLUME_MISSING'
    if len(ordered)>=horizon*2:
        previous=ordered[-horizon*2:-horizon];ph=max(safe_float(b.get('high')) for b in previous);pl=min(safe_float(b.get('low')) for b in previous)
        previous_range=(ph/pl-1)*100 if pl else None
        result['range_compression_ratio']=result['balance_range_pct']/previous_range if previous_range else None
        result['range_compression_unavailable_reason']='' if result.get('range_compression_ratio') is not None else 'ZERO_PRIOR_RANGE'
    else:
        result['range_compression_ratio']=None;result['range_compression_unavailable_reason']='INSUFFICIENT_PRIOR_WINDOW'
    return result

# 함수 설명: 보합 가설값 충족 여부를 미래정보 없이 판정합니다.
def v232_balance_qualifies(feature):
    return (feature.get('data_status')=='OK' and feature.get('balance_duration_min',0)>=BALANCE_ALERT_MIN_DURATION
        and feature.get('balance_range_pct') is not None and feature['balance_range_pct']<=BALANCE_MAX_RANGE_PCT
        and feature.get('balance_net_change_pct') is not None and abs(feature['balance_net_change_pct'])<=BALANCE_MAX_ABS_NET_CHANGE_PCT
        and feature.get('trend_slope_pct_per_min') is not None and abs(feature['trend_slope_pct_per_min'])<=BALANCE_MAX_ABS_SLOPE_PCT_PER_MIN)

# 함수 설명: 보합 상태 사건을 원장과 당일 누적목록에 각각 한 번 기록합니다.
def v232_balance_event(c,event,when,feature=None,reason='',trade_id=''):
    feature=feature or {};box=c.get('balance_box') or {};box_id=box.get('box_id','')
    suffix=f':{feature.get("balance_duration_min","")}' if event=='BASE_MATURE' else ''
    event_id=f'{v220_date}:{c["code"]}:{box_id}:{event}{suffix}'
    if event_id in c.setdefault('balance_event_ids',set()):return True
    row={'date':v220_date,'version':STRATEGY_VERSION,'event_id':event_id,'event':event,'box_id':box_id,
        'stock_code':c['code'],'stock_name':c['stock'].get('stock_name',c['code']),'event_time':_csv_datetime(when),
        'balance_duration_min':feature.get('balance_duration_min',box.get('duration_min','')),'base_high':box.get('base_high',''),
        'base_low':box.get('base_low',''),'breakout_close':feature.get('breakout_close',''),'trade_id':trade_id,'reason':reason}
    if not v231_write_ledger(V232_BALANCE_EVENT_FILE,row,V232_BALANCE_EVENT_COLUMNS):v231_halt('BALANCE_EVENT_WRITE_UNAVAILABLE',c,when);return False
    c['balance_event_ids'].add(event_id)
    if event in {'BASE_READY','BASE_BREAKOUT'}:
        kind='보합완성' if event=='BASE_READY' else '보합돌파'
        key=(c['code'],kind);c.setdefault('balance_summary_events',{}).setdefault(key,{'time':when,'name':c['stock'].get('stock_name',c['code']),'duration':feature.get('balance_duration_min',box.get('duration_min',0))})
    return True

# 함수 설명: 유효 완료봉마다 8개 시간축 feature를 저장하고 보합 박스 상태를 전이합니다.
def v232_evaluate_balance(c,bar,detected):
    when=bar['minute']+timedelta(minutes=1);v230_ensure_candidate_schema(c)
    if when.strftime('%H:%M')>BALANCE_OBSERVE_END:return
    history=list(c.get('history',[]))
    if not history or history[-1].get('minute')!=bar.get('minute'):history.append(copy.deepcopy(bar))
    if not bar.get('valid',True):
        if c.get('balance_box'):v232_balance_event(c,'BASE_EXPIRED',when,reason=bar.get('invalid_reason','INVALID_BAR'))
        c['balance_box']=None;c['balance_breakout_watch']=None;return
    features={}
    for horizon in PULLBACK_SNAPSHOT_HORIZONS_MIN:
        feature=v232_balance_features(history,horizon);feature['qualification']='READY' if v232_balance_qualifies(feature) else 'WATCH'
        row={k:'' for k in V232_BALANCE_EVALUATION_COLUMNS};row.update(date=v220_date,version=STRATEGY_VERSION,stock_code=c['code'],
            stock_name=c['stock'].get('stock_name',c['code']),candidate_source=c.get('candidate_source',''),evaluated_time=_csv_datetime(when),
            snapshot_horizon_min=horizon,**feature)
        if not v231_write_ledger(V232_BALANCE_EVALUATION_FILE,row,V232_BALANCE_EVALUATION_COLUMNS):v231_halt('BALANCE_EVALUATION_WRITE_UNAVAILABLE',c,when);return
        features[horizon]=feature
    qualified=[(h,f) for h,f in features.items() if v232_balance_qualifies(f)]
    box=c.get('balance_box')
    if box is None and qualified:
        horizon,feature=max(qualified,key=lambda x:x[0]);c['balance_box_seq']=c.get('balance_box_seq',0)+1
        c['balance_box']={'box_id':f'{v220_date}:{c["code"]}:{c["balance_box_seq"]}','base_high':feature['base_high'],'base_low':feature['base_low'],
            'duration_min':horizon,'ready_time':when,'breakout_done':False};c['balance_breakout_watch']=None
        v232_balance_event(c,'BASE_READY',when,feature)
        box=c['balance_box']
    elif box is not None and qualified:
        horizon,feature=max(qualified,key=lambda x:x[0])
        if horizon>box.get('duration_min',0):box['duration_min']=horizon;v232_balance_event(c,'BASE_MATURE',when,feature)
    if box is None:return
    if bar['close']<box['base_low']*(1-BALANCE_INVALIDATE_BUFFER_PCT/100)-1e-9:
        v232_balance_event(c,'BASE_EXPIRED',when,reason='LOW_BREAK');c['balance_box']=None;c['balance_breakout_watch']=None;return
    watch=c.get('balance_breakout_watch')
    if watch and bar['minute']>watch['bar_minute']:
        c['balance_breakout_watch']=None
        if bar['close']+1e-9>=box['base_high'] and not box.get('breakout_done') and when.strftime('%H:%M')<PULLBACK_NEW_ENTRY_END:
            key=(c['code'],V232_BALANCE_MODE,box['box_id'])
            meta={'entry_mode':V232_BALANCE_MODE,'signal_time':when,'signal_detected_time':detected,'signal_price':bar['close'],
                'support_episode_id':box['box_id'],'balance_box_id':box['box_id'],'balance_duration_min':box['duration_min'],'base_high':box['base_high'],'base_low':box['base_low']}
            if key not in c['pending'] and key not in v220_fill_keys and v220_emit(c,V232_BALANCE_MODE,'SIGNAL',meta):
                c['pending'][key]=meta;v220_signals[V232_BALANCE_MODE].setdefault(c['code'],{'time':when,'name':c['stock'].get('stock_name',c['code']),'trade_id':''})
                box['breakout_done']=True;v232_balance_event(c,'BASE_BREAKOUT',when,dict(meta,breakout_close=bar['close']));v220_checkpoint(True)
    threshold=v230_ceil_to_valid_tick(box['base_high']*(1+BALANCE_BREAKOUT_BUFFER_PCT/100))
    if not box.get('breakout_done') and c.get('balance_breakout_watch') is None and bar['close']>=threshold:
        c['balance_breakout_watch']={'bar_minute':bar['minute'],'close':bar['close']};v232_balance_event(c,'BREAKOUT_WATCH',when,{'breakout_close':bar['close']})

# 함수 설명: 부모 완료봉 상태기계를 그대로 실행한 뒤 보합 연구만 후속 평가합니다.
v231_complete_bar_for_v232=v220_complete_bar
def v220_complete_bar(c,bar,detected):
    v231_complete_bar_for_v232(c,bar,detected)
    v232_evaluate_balance(c,bar,detected)

# 함수 설명: balance 원장까지 대조해 checkpoint 직전 장애에서도 동일 박스 재진입을 막습니다.
v231_recover_signal_ledger_for_v232=v220_recover_signal_ledger
def v220_recover_signal_ledger():
    v231_recover_signal_ledger_for_v232()
    signal_path=Path(V220_SIGNAL_FILE)
    if signal_path.exists():
        with signal_path.open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream):
                if row.get('date')!=v220_date or row.get('strategy')!=V232_BALANCE_MODE or row.get('event')!='FILL':continue
                box_id=row.get('support_episode_id','');v220_fill_keys.add((clean_stock_code(row.get('stock_code')),V232_BALANCE_MODE,box_id))
    event_path=Path(V232_BALANCE_EVENT_FILE)
    if event_path.exists():
        with event_path.open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream):
                if row.get('date')!=v220_date:continue
                code=clean_stock_code(row.get('stock_code'));c=v220_candidates.get(code)
                if c is None:continue
                c.setdefault('balance_event_ids',set()).add(row.get('event_id',''))
                if row.get('event') in {'BASE_READY','BASE_BREAKOUT'}:
                    kind='보합완성' if row['event']=='BASE_READY' else '보합돌파';when=datetime.fromisoformat(row['event_time'])
                    c.setdefault('balance_summary_events',{}).setdefault((code,kind),{'time':when,'name':row.get('stock_name',code),'duration':safe_int(row.get('balance_duration_min')) or 0})

# 함수 설명: 전략·SNAPSHOT 시간축·장기 보합을 각각 하나의 간단한 누적 말풍선으로 만듭니다.
def v220_summary_text(cutoff):
    buckets=[]
    for mode,title in [('BASE','BASE'),('FIRST_75_PASS','FIRST 75 PASS'),('PULLBACK_STRUCTURE_ENTRY','PULLBACK STRUCTURE ENTRY')]:
        entries=[(code,v['name'],v['time']) for code,v in v220_signals.get(mode,{}).items() if v['time']<=cutoff]
        buckets.append((mode,title,entries))
    for horizon in PULLBACK_SNAPSHOT_HORIZONS_MIN:
        entries=[]
        for code,c in v220_candidates.items():
            when=c.get('summary_snapshot_ready',{}).get(horizon)
            if when and when<=cutoff:entries.append((code,c['stock'].get('stock_name',code),when))
        buckets.append((f'SNAPSHOT_{horizon}',f'SNAPSHOT {horizon}분',entries))
    balance=[]
    for code,c in v220_candidates.items():
        for (_,kind),item in c.get('balance_summary_events',{}).items():
            if item['time']<=cutoff:balance.append((code,item['name'],item['time'],kind,item.get('duration',0)))
    messages=[]
    for slug,title,entries in buckets:
        entries=sorted(entries,key=lambda x:(x[2],x[0]));lines=[f'[{title}]']
        lines += [f'{i}. {name}({code}) - {when:%H:%M:%S}' for i,(code,name,when) in enumerate(entries,1)] or ['없음']
        messages.append((slug,'\n'.join(lines)))
    balance.sort(key=lambda x:(x[2],x[0],x[3]));lines=['[장기 보합 돌파]']
    lines += [f'{i}. {name}({code}) - '+(f'{duration}분 보합완성' if kind=='보합완성' else '보합돌파')+f' - {when:%H:%M:%S}' for i,(code,name,when,kind,duration) in enumerate(balance,1)] or ['없음']
    messages.append(('BALANCE','\n'.join(lines)))
    return messages

# 함수 설명: 같은 채팅방에 전략별 말풍선을 영속 분리 예약합니다.
@v220_serialized
def v220_schedule_summaries(now=None):
    now=now or datetime.now()
    if not V220_SUMMARY_ENABLED or now.strftime('%Y-%m-%d')!=v220_date:return
    changed=False
    for hhmm in V220_SUMMARY_TIMES:
        cutoff=datetime.combine(now.date(),_hhmm_time(hhmm))
        if now<cutoff:continue
        for slug,message in v220_summary_text(cutoff):
            key=f'SUMMARY:{v220_date}:{hhmm}:{slug}'
            if key not in v220_outbox:v220_outbox[key]={'parts':v220_message_parts(message),'status':'PENDING','next_part':0};changed=True
    if changed:v220_checkpoint(True)

# 함수 설명: 세션 종료 시 열린 보합 박스를 원장에 무효화하고 상태를 checkpoint합니다.
v231_maintenance_for_v232=v220_maintenance
def v220_maintenance(now=None,ending=False):
    now=now or datetime.now();v231_maintenance_for_v232(now,ending)
    if ending or now.strftime('%H:%M')>=BALANCE_OBSERVE_END:
        changed=False
        for c in v220_candidates.values():
            if c.get('balance_box'):
                v232_balance_event(c,'BASE_EXPIRED',now,reason='SESSION_END');c['balance_box']=None;c['balance_breakout_watch']=None;changed=True
        if changed:v220_checkpoint(True)

# 함수 설명: v2.3.2 신규 원장과 RESEARCH 전용 안전설정을 함께 검증합니다.
v231_validate_v220_config_for_v232=validate_v220_config
def validate_v220_config():
    v231_validate_v220_config_for_v232()
    if STRATEGY_VERSION!='v2.3.2' or EXECUTION_MODE!='RESEARCH' or AUTO_TRADE_ENABLED or USE_MOCK:raise ValueError('v2.3.2는 RESEARCH 전용입니다.')
    if V220_SUMMARY_TIMES!=['09:30','10:00','10:30','11:00','11:30','12:00','12:30','13:00','13:30','14:00','14:30','15:00','15:30']:raise ValueError('30분 누적시각을 확인하세요.')
    if not (BALANCE_ALERT_MIN_DURATION==60 and BALANCE_OBSERVE_END=='15:30' and PULLBACK_NEW_ENTRY_END=='15:10'):raise ValueError('보합 시간경계를 확인하세요.')
    if V232_BALANCE_MODE not in V230_NEW_MODES or len(PULLBACK_EXIT_STRATEGIES)!=63:raise ValueError('보합 63-grid 연결을 확인하세요.')
    return True

# 함수 설명: v2.3.2 필수 신규 원장을 빈 스키마로 먼저 생성합니다.
v231_initialize_ledgers_for_v232=v231_initialize_ledgers
def v231_initialize_ledgers():
    v231_initialize_ledgers_for_v232()
    for path,columns in [(V232_BALANCE_EVALUATION_FILE,V232_BALANCE_EVALUATION_COLUMNS),(V232_BALANCE_EVENT_FILE,V232_BALANCE_EVENT_COLUMNS)]:
        if not v231_write_ledger(path,None,columns):raise RuntimeError(f'필수 원장 생성 실패: {path}')

v220_signals.setdefault(V232_BALANCE_MODE,{})
'''
    c1 = replace_once(c1, insertion_marker, v232_block + "\n" + insertion_marker, "v232 implementation insertion")

    c3 += r'''

# v2.3.2 QUICK REFERENCE (append-only)
# - PULLBACK_BALANCE_BREAKOUT(장기 보합 돌파): 60분 이상, 폭 1.50% 이하, 순변화율 ±0.50% 이하,
#   기울기 ±0.010%/분 이하인 완료 1분봉 보합 박스를 고정합니다.
# - 완료봉 종가가 상단 +0.10%를 넘고 다음 완료봉도 상단 이상이면 다음 정상 tick에서 63-grid 가상체결합니다.
# - 하단 -0.20%, 부분봉·gap·재접속 첫 봉·15:30 세션 종료는 보합 박스를 무효화합니다.
# - 누적 Telegram은 같은 채팅방에서 BASE → FIRST 75 PASS → STRUCTURE → SNAPSHOT 30~240분 →
#   장기 보합 돌파 순서의 별도 말풍선이며 09:30~15:30 매 30분 당일 누적입니다.
'''
    c4 += r'''

# 2026-09-28 (월) — v2.3.2 장기 보합 돌파·알림 분리
# - 부모 028_260928_v2.3.1.ipynb 전체를 직접 보존하고 신규 보합 상태기계와 누적 알림만 국소 추가.
# - 기존 8개 SNAPSHOT, STRUCTURE, BASE/FIRST_75, ETF, 169/63-grid와 주문엔진은 의미 변경 없음.
# - 60분 이상 장기 보합 박스 완성, 상단 +0.10% 종가돌파, 다음 완료봉 상단 유지 뒤 첫 정상 tick 가상체결.
# - 신규 원장은 pullback_balance_evaluations_v232.csv / pullback_balance_events_v232.csv,
#   paper_trades_v232.csv entry_mode=PULLBACK_BALANCE_BREAKOUT이며 실제·키움 모의 주문과 연결하지 않음.
# - 전략별·SNAPSHOT 시간축별 누적 Telegram을 같은 채팅방의 별도 말풍선으로 30분마다 발송.
# - 기본 EXECUTION_MODE=RESEARCH, AUTO_TRADE_ENABLED=False, USE_MOCK=False, 실제·모의 주문 0건.
'''

    result["cells"][code_indices[0]]["source"] = as_source(c0)
    result["cells"][code_indices[1]]["source"] = as_source(c1)
    result["cells"][code_indices[3]]["source"] = as_source(c3)
    result["cells"][code_indices[4]]["source"] = as_source(c4)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
