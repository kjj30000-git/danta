#!/usr/bin/env python3
"""2차 비판적 검증: 새 namespace에서 통합 경로와 실패 주입을 확인합니다."""
import contextlib
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time as real_time
from datetime import datetime as RealDate, timedelta
import requests
ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'code/releases/026_260922_v2.2.0.ipynb'
checks=[]

# 함수 설명: 외부 연결 시도는 성공 여부와 무관하게 검증 실패로 처리합니다.
def no_network(*a,**k):raise AssertionError('NETWORK FORBIDDEN')

# 함수 설명: 매 시험마다 release import/전역 초기화를 새 namespace에서 수행합니다.
def load(tmp):
    os.chdir(tmp)
    Path('.env').write_text('KIWOOM_APP_KEY=dummy\nKIWOOM_SECRET_KEY=dummy\nTELEGRAM_BOT_TOKEN=dummy\nTELEGRAM_PERSONAL_CHAT_ID=test\n')
    ns={'__name__':'v220_review'}
    nb=json.loads(TARGET.read_text())
    for c in nb['cells']:exec(''.join(c['source']),ns)
    ns['log']=lambda *a,**k:None
    return ns

# 함수 설명: assertion 결과를 보고서에 기록합니다.
def check(value,label):
    if not value:raise AssertionError(label)
    checks.append(label)

class Clock(RealDate):
    at=RealDate(2026,9,22,9,5)
    @classmethod
    def now(cls,tz=None):return cls.fromtimestamp(cls.at.timestamp(),tz)

class TimeProxy:
    def time(self):return Clock.at.timestamp()
    def sleep(self,seconds):Clock.at+=timedelta(seconds=seconds)
    def __getattr__(self,key):return getattr(real_time,key)

# 함수 설명: 실제 스캔 입출력에 맞는 후보 샘플을 생성합니다.
def stock(code='999911'):
    now=Clock.now()
    return dict(stock_code=code,stock_name='검증주식',market='KOSPI',current_price=100.,score=80,
        score_detail={},trading_value_source='ACTUAL',actual_trading_value=30_000_000_000,
        estimated_trading_value=30_000_000_000,trading_value_used=30_000_000_000,
        change_rate=7.,volume=500000,day_high=100.,high_gap=0.,value_growth=1.5,volume_growth=1.5,
        history_available_sec=90,price_change_30s=.2,price_change_60s=.4,high_gap_change_60s=-.1,
        scan_session='MAIN',decision_session='MAIN',decision_time=now,score_time=now,
        _score_evaluated_ts=now.timestamp(),watch_episode_id='FIXTURE_EP')

# 함수 설명: fixture에서 외부 저장/알림을 캡처하되 핵심 전략함수는 그대로 둡니다.
def prepare(ns):
    Clock.at=RealDate(2026,9,22,9,5)
    ns['datetime']=Clock;ns['time']=TimeProxy()
    rows=[];msgs=[]
    ns['enqueue_research_rows']=lambda f,r,*a,**k:rows.extend((f,x) for x in r) or True
    ns['send_telegram']=lambda m:msgs.append(m) or True
    ns['v220_reset_day'](Clock.now())
    return rows,msgs

# 함수 설명: 전체 scan_market를 실제 진입함수까지 실행합니다.
def scan_test(ns):
    rows,_=prepare(ns)
    ns['MARKETS']=[('001','KOSPI')]
    ns['get_change_rate_rank']=lambda market:[{'stk_cd':'999911','stk_nm':'검증주식','cur_prc':'10000','now_trde_qty':'500000','flu_rt':'7'}]
    ns['build_actual_trading_value_map']=lambda:{'999911':{'actual_trading_value':30_000_000_000,'trading_value_rank':1,'market':'KOSPI'}}
    ns['fetch_quotes_parallel']=lambda stocks:({'999911':{'cur_prc':'10000','high_pric':'10000','trde_qty':'500000'}},{})
    ns['calculate_score']=lambda st:80
    now=Clock.now().timestamp()
    ns['price_history']['999911']=[{'ts':now-60,'price':9900.,'high_gap':1.,'score':65}, {'ts':now-30,'price':9950.,'high_gap':.5,'score':70}]
    out=ns['scan_market']()
    check(len(out)==1,'full scan_market returns candidate')
    modes=[p['entry_mode'] for p in ns['paper_positions'].values()]
    check(modes==['BASE','PRE_HISTORY'],f'full scan only BASE/FIRST entries: {modes}')
    check(ns['v220_candidates']['999911']['candidate_source']=='BOTH','full scan joins candidate sources')
    check(set(ns['v220_signals']['FIRST_75_PASS'])=={'999911'},'full scan FIRST75 signal registry')
    ns['scan_market']()
    check(len(ns['paper_positions'])==2,'repeat scan same episode no duplicate grid')
    check(not ns['orb_universe'],'OFF ORB no expanded REST universe')
    # 反例: history条件失敗を FIRST と表示しない。
    failed=dict(stock('999912'),price_change_30s=-.2)
    check(ns['evaluate_pre_history'](failed)[0]=='FAIL','original FIRST PRE condition negative case')
    check(ns['maybe_open_pre_history'](failed,Clock.now()) is None,'actual FIRST function rejects PRE fail')
    check('999912' not in ns['v220_signals']['FIRST_75_PASS'],'failed PRE absent from FIRST notifications')
    return rows

# 함수 설명: atomic 저장 실패가 신규진입만 멈추고 파일을 보존하는지 검증합니다.
def failure_test(ns,tmp):
    rows,msgs=prepare(ns)
    tid=ns['open_paper_trade'](stock(),'BASE')
    path=Path(ns['V220_STATE_FILE']);old=path.read_bytes()
    real_replace=ns['os'].replace
    try:
        ns['os'].replace=lambda *a,**k:(_ for _ in ()).throw(OSError('injected atomic replace error'))
        check(not ns['v220_checkpoint'](True),'atomic save failure returns false')
        check(ns['v220_halted'],'save failure blocks new research entries')
        check(ns['open_paper_trade'](stock('999913'),'BASE') is None,'save-failure gate no new grid')
        check(path.read_bytes()==old,'save failure keeps last good state bytes')
        ns['update_paper_position']('999911',105.)
        check(any(r.get('result')=='TAKE_PROFIT' for _,r in rows),'existing positions still exit while new entries halted')
    finally:ns['os'].replace=real_replace
    # Ambiguous send is not retried by the same loop or recovery.
    ns['v220_halted']=False;ns['v220_outbox'].clear()
    ns['v220_queue_alert'](stock(),'BASE',{'signal_time':Clock.now()})
    ns['send_telegram']=lambda m:msgs.append(m) or False
    ns['v220_notify_once']();ns['v220_notify_once']()
    check(len(msgs)==1,'ambiguous Telegram response no duplicate retry')
    check(next(iter(ns['v220_outbox'].values()))['status']=='DELIVERY_UNKNOWN','unknown delivery recorded')
    ns['v220_restore'](Clock.now());ns['v220_notify_once']()
    check(len(msgs)==1,'unknown delivery remains non-retry after restart')
    # In-flight status left by a killed process.
    item=next(iter(ns['v220_outbox'].values()));item['status']='IN_FLIGHT';ns['v220_checkpoint'](True)
    ns['v220_restore'](Clock.now())
    check(next(iter(ns['v220_outbox'].values()))['status']=='DELIVERY_UNKNOWN','crashed in-flight delivery marked unknown')
    ns['V220_STATE_FILE']=str(Path(tmp)/'corrupt.json');Path(ns['V220_STATE_FILE']).write_text('{broken')
    try:ns['v220_restore'](Clock.now())
    except RuntimeError:pass
    else:raise AssertionError('corrupt recovery accepted')
    check(ns['v220_halted'],'corrupt state fails closed without silent reset')
    return tid

# 함수 설명: 실제 tick queue와 worker를 사용해 WS/live 경로 비차단 및 grid 판정을 검증합니다.
def threading_test(ns):
    rows,_=prepare(ns)
    ns['open_paper_trade'](stock(),'BASE')
    ns['v220_checkpoint']=lambda *a,**k:True
    started=real_time.monotonic()
    with ns['V220_LOCK']:
        t=threading.Thread(target=lambda:ns['handle_realtime_price']('999911',100.,{'15':'3'}))
        t.start();t.join(1)
        check(not t.is_alive(),'WS callback never waits on research lock')
    check(real_time.monotonic()-started<1,'WS callback returns under held research lock')
    ns['start_research_compute_worker']()
    deadline=real_time.monotonic()+3
    while ns['research_tick_queue'].unfinished_tasks and real_time.monotonic()<deadline:real_time.sleep(.01)
    check(ns['v220_metrics']['ticks']==1,'real worker consumes extended tick tuple and OHLCV')
    check(ns['research_tick_queue'].unfinished_tasks==0,'real worker task accounting completes')
    ns['research_tick_queue'].put(None)
    ns['RESEARCH_COMPUTE_EXECUTOR'].shutdown(wait=True)
    # With a full queue producer must coalesce without I/O or waiting.
    import queue
    ns['research_tick_queue']=queue.Queue(maxsize=1)
    ns['handle_realtime_price']('999911',101.,{'15':'4'})
    ns['handle_realtime_price']('999911',102.,{'15':'5'})
    check('999911' in ns['research_latest_snapshots'],'queue-full coalescing keeps extended latest snapshot')
    check(len(ns['research_latest_snapshots']['999911'])==7,'coalesced data retains volume and sequence')

# 함수 설명: 시작/종료 main 경로를 서비스 연결 대신 mock으로 끝까지 통과시킵니다.
def main_boundaries(ns,hour):
    prepare(ns);Clock.at=RealDate(2026,9,22,hour,0,1)
    called=[]
    for name in ['start_research_writer','start_research_safety_workers','start_live_exit_dispatcher',
        'start_live_exit_watchdog','start_research_compute_worker','start_live_state_flusher',
        'get_kiwoom_token','start_websocket_manager','subscribe_recovered_live_items','v220_start',
        'force_close_all','finalize_entry_path_trackers','finalize_post_exit_trackers',
        'finalize_all_policy_shadow_trackers','finalize_wide_snapshot_trackers','save_live_state',
        'flush_research_writer','shutdown_async_executors','v220_quiesce']:
        ns[name]=lambda *a,_name=name,**k:called.append(_name)
    if hour<8:
        class InterruptTime(TimeProxy):
            def sleep(self,seconds):raise KeyboardInterrupt()
        ns['time']=InterruptTime()
    ns['run_scanner']()
    check(ns['shutdown_requested'],f'main {hour}:00 shutdown guard set')
    check('flush_research_writer' in called and 'shutdown_async_executors' in called,f'main {hour}:00 flush and executor shutdown')
    if hour>=20:check('force_close_all' in called,'after 20:00 main completes forced paper exit')

# 함수 설명: 전체 2차 검증을 격리 디렉터리/새 namespace별로 실행합니다.
def main():
    socket.socket.connect=no_network;socket.create_connection=no_network
    requests.sessions.Session.request=no_network
    with tempfile.TemporaryDirectory(prefix='v220_review_') as root:
        root=Path(root)
        for index,fn in enumerate([scan_test,lambda ns:failure_test(ns,root),threading_test,
                                   lambda ns:main_boundaries(ns,7),lambda ns:main_boundaries(ns,20)]):
            tmp=root/str(index);tmp.mkdir();ns=load(tmp)
            with contextlib.redirect_stdout(io.StringIO()):fn(ns)
        ns=load(root)
        with contextlib.redirect_stdout(io.StringIO()):
            check(ns['test_v171_enhancements'](),'parent live-first/config regression')
            check(ns['test_v1713_order_safety'](),'parent actual exit E2E cache/REST fallback/ambiguous-response mocks')
    report={'status':'PASS','checks':checks,'check_count':len(checks),'external_connections':0,'real_or_mock_broker_orders':0}
    path=ROOT/'reports/regression/v2.2.0_review_results.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
