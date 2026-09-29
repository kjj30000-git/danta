import json,ast,datetime,tempfile,pathlib,os,copy
from datetime import timedelta
root=pathlib.Path(__file__).resolve().parents[2]
n=json.load(open(root/'code/releases/030_260930_v2.3.3.ipynb'))
p=json.load(open(root/'code/releases/029_260929_v2.3.2.ipynb'))
for i in range(5):
 a=ast.parse(''.join(n['cells'][i]['source']));b=ast.parse(''.join(p['cells'][i]['source']))
 old=[x.name for x in b.body if isinstance(x,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))]
 new=[x.name for x in a.body if isinstance(x,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))]
 assert all(x in new for x in old),(i,set(old)-set(new))
print('parent defs preserved')
# Do not execute program main, broker calls, or notebook 5th independent broker read cell.
tmp=tempfile.TemporaryDirectory(); old=os.getcwd();os.chdir(tmp.name);pathlib.Path('.env').write_text('KIWOOM_APP_KEY=TEST\nKIWOOM_SECRET_KEY=TEST\nTELEGRAM_BOT_TOKEN=TEST\nTELEGRAM_PERSONAL_CHAT_ID=TEST\n')
g={'__name__':'v233_test'}
for i in (0,1): exec(compile(''.join(n['cells'][i]['source']),f'cell{i}','exec'),g)
assert g['EXECUTION_MODE']=='RESEARCH' and not g['AUTO_TRADE_ENABLED'] and not g['USE_MOCK']
assert g['validate_v220_config']()
D=datetime.datetime; base=D(2026,9,30,10,0); c={'code':'999901','stock':{'stock_name':'TEST'},'balance_box':{'box_id':'b1','base_start_time':D(2026,9,30,9,0),'base_ready_time':base,'initial_ready_duration_min':60,'duration_min':60,'base_high':100,'base_low':99,'sent_milestones':set()},'balance_event_ids':set()}
g['v220_date']='2026-09-30'
g['v231_write_ledger']=lambda *a:True;g['v220_checkpoint']=lambda *a:True;g['v220_outbox'].clear()
f=lambda d:{'balance_duration_min':d}
assert g['v232_balance_event'](c,'BASE_READY',base,f(60))
assert g['v232_balance_event'](c,'BASE_MATURE',base+timedelta(minutes=30),f(90))
assert g['v233_box_at'](c,'b1',base+timedelta(minutes=15))['minutes']==75
assert len([k for k in g['v220_outbox'] if k.startswith('BALANCE_MILESTONE')])==2
assert g['v232_balance_event'](c,'BREAKOUT_WATCH',base+timedelta(minutes=31))
assert g['v233_box_at'](c,'b1',base+timedelta(minutes=31))['status']=='돌파대기'
assert g['v232_balance_event'](c,'BREAKOUT_RESET',base+timedelta(minutes=32))
assert g['v233_box_at'](c,'b1',base+timedelta(minutes=32))['status']=='활성'
assert g['v232_balance_event'](c,'BREAKOUT_WATCH',base+timedelta(minutes=33))
assert g['v232_balance_event'](c,'BASE_BREAKOUT',base+timedelta(minutes=34))
assert g['v232_balance_event'](c,'BASE_EXPIRED',base+timedelta(minutes=35),reason='SESSION_END')
assert c['balance_box']['terminal_status']=='BASE_BREAKOUT'
assert g['v233_box_at'](c,'b1',base+timedelta(minutes=20))['status']=='활성'
assert g['v233_box_at'](c,'b1',base+timedelta(minutes=40))['minutes']==94
print('boundary / milestone / watch / terminal PASS; broker calls 0')
# Actual 2026-09-29 event ledger replay, distinct from synthetic fixtures.
import csv
rows=list(csv.DictReader(open(root/'data/2.3.2(260929)/pullback_balance_events_v232.csv',encoding='utf-8-sig')))
actual={}
for row in rows:
 code=row['stock_code'];x=actual.setdefault(code,{'code':code,'stock':{'stock_name':row['stock_name']},'balance_box_events':{},'balance_summary_events':{}})
 when=D.fromisoformat(row['event_time']);event=row['event'];duration=int(row['balance_duration_min'])
 x['balance_box_events'].setdefault(row['box_id'],[]).append({'event':event,'time':when,'reason':row['reason'],'duration':duration,'start':None,'initial':None})
 if event in ('BASE_READY','BASE_BREAKOUT'):
  kind='보합완성' if event=='BASE_READY' else '보합돌파'
  x['balance_summary_events'].setdefault((code,kind),{'time':when,'name':row['stock_name'],'duration':duration})
han=actual['042700'];ids=list(han['balance_box_events'])
assert len(ids)==2
assert g['v233_box_at'](han,ids[0],D(2026,9,29,12,0))['status']=='돌파완료'
assert g['v233_box_at'](han,ids[0],D(2026,9,29,15,30))['status']=='돌파완료'
assert g['v233_box_at'](han,ids[1],D(2026,9,29,14,0))['minutes']==64
assert g['v233_box_at'](actual['001820'],next(iter(actual['001820']['balance_box_events'])),D(2026,9,29,12,0))['minutes']==98
print('actual 2026-09-29 event ledger replay PASS / 20 events')
# Default start path to token boundary, no network or background workers.
class TokenBoundary(Exception):pass
for key in ('start_research_writer','start_research_safety_workers','start_live_exit_dispatcher','start_live_exit_watchdog','start_research_compute_worker','start_live_state_flusher'):
 g[key]=lambda:None
g['v231_initialize_ledgers']=lambda:True
g['v220_restore']=lambda *a:True
g['get_kiwoom_token']=lambda:(_ for _ in ()).throw(TokenBoundary())
g['log']=lambda *a,**kw:None
try:g['run_scanner']()
except TokenBoundary:pass
else:raise AssertionError('token boundary not reached')
print('clean-process start to token boundary PASS / network, broker, Telegram 0')
# Parent's offline tick path in an isolated temporary output directory.
for key in ('v231_initialize_ledgers','v220_restore','log'):
 pass
# The v231 replay calls only research tick processing and creates no broker order.
g['v231_initialize_ledgers']=g['v231_initialize_ledgers_for_v232']
assert g['run_v231_off_hours_validation']()
print('parent tick replay PASS / broker orders 0')
# Full completed-bar path with constant prices; ready60, then 90 and 120 exactly once.
g['v220_date']='2026-09-30';g['v220_outbox'].clear();g['v220_halted']=False
flat={'code':'999902','stock':{'stock_name':'FLAT','stock_code':'999902'},'candidate_start_time':D(2026,9,30,9,0),'pending':{}}
for i in range(120):
 minute=D(2026,9,30,9,0)+timedelta(minutes=i)
 bar={'minute':minute,'open':10000,'high':10000,'low':10000,'close':10000,'volume':100,'valid':True}
 flat.setdefault('history',[]).append(bar)
 g['v232_evaluate_balance'](flat,bar,minute+timedelta(minutes=1))
assert flat['balance_box']['initial_ready_duration_min']==60
assert flat['balance_box']['sent_milestones']=={60,90,120},flat['balance_box']['sent_milestones']
assert len([k for k in g['v220_outbox'] if k.startswith('BALANCE_MILESTONE:')])==3
print('120 completed bars milestone path PASS')
g['v220_candidates'].clear();g['v220_candidates'].update(actual)
for mode in list(g['v220_signals']):g['v220_signals'][mode]={}
for cutoff in (D(2026,9,29,12,0),D(2026,9,29,15,30)):
 text=dict(g['v220_summary_text'](cutoff))['BALANCE']
 assert '삼화콘덴서(001820)' in text
 if cutoff.hour==12:assert '돌파완료 12:37' not in text and '보합 98분째' in text
 else:assert '돌파완료 12:37' in text
print('actual ledger cutoff summary PASS')
# Initial ready at 90: no retroactive 60 milestone.
g['v220_outbox'].clear();c90={'code':'999903','stock':{'stock_name':'READY90'},'balance_box':{'box_id':'b90','base_start_time':D(2026,9,30,9,0),'base_ready_time':D(2026,9,30,10,30),'initial_ready_duration_min':90,'duration_min':90,'sent_milestones':set()},'balance_event_ids':set()}
assert g['v232_balance_event'](c90,'BASE_READY',D(2026,9,30,10,30),{'balance_duration_min':90})
assert set(c90['balance_box']['sent_milestones'])=={90}
print('initial ready90 no retrospective 60 PASS')
