#!/usr/bin/env python3
import json,os,tempfile,socket,csv,ast,copy
from pathlib import Path
from datetime import datetime,timedelta
ROOT=Path(__file__).resolve().parents[2]; NB=ROOT/'code/releases/028_260928_v2.3.1.ipynb';PARENT=ROOT/'code/releases/027_260923_v2.3.0.ipynb'
def deny(*a,**k):raise AssertionError('external connection')
socket.socket.connect=deny;socket.create_connection=deny
n=json.loads(NB.read_text());work=Path(tempfile.mkdtemp());os.chdir(work);Path('.env').write_text('KIWOOM_APP_KEY=x\nKIWOOM_SECRET_KEY=x\nTELEGRAM_BOT_TOKEN=x\nTELEGRAM_PERSONAL_CHAT_ID=x\n')
g={'__name__':'release_test'}
for c in n['cells'][:2]:exec(compile(''.join(c['source']),'release','exec'),g)
checks=[]
def ck(x,n):assert x,n;checks.append(n)
base=datetime(2026,9,28,9,5,20);g['v220_reset_day'](base);g['v231_initialize_ledgers']();stock={'stock_code':'999901','stock_name':'TEST','score':80,'current_price':10000,'trading_value_source':'ACTUAL','actual_trading_value':1,'estimated_trading_value':1}
c=g['v230_create_candidate_state']({'code':'999901','stock':stock,'candidate_start_time':base,'sources':{'BASE'},'parent_trade_ids':['x'],'candidate_source':'BASE'});g['v220_candidates']['999901']=c
for q,(m,s,p) in enumerate([(0,20,10000),(0,40,10010),(1,0,10000),(1,30,10040),(2,0,10020),(2,30,10030),(3,0,10040)],1):g['v220_on_tick']('999901',p,base.replace(second=0)+timedelta(minutes=m,seconds=s),{'15':'1'},q)
ck(c['bar_counts']=={'bars':3,'valid_bars':2,'invalid_bars':1},'tick path one partial then valid bars');ck(c['high']==10040 and len(c['history'])==2,'history/high');ck(len(list(csv.DictReader(open(g['V220_MINUTE_FILE'],encoding='utf-8-sig'))))==3,'minute ledger all bars')
for _ in range(3):g['v230_ensure_candidate_schema'](c)
ck(not c['needs_partial_bar'],'schema idempotent')
# sequence gap, reconnect, recovery
for q,m in [(10,5),(11,6),(12,7),(13,8)]:g['v220_on_tick']('999901',10000,base.replace(second=0)+timedelta(minutes=m),{},q)
ck(c['history'][-1]['valid'] and c['invalid_reasons']['NON_CONTIGUOUS_MINUTE']>=1,'minute-gap recovery')
g['v220_on_tick']('999901',10000,base.replace(second=20)+timedelta(minutes=8),{},15)
for q,m in [(16,9),(17,10),(18,11)]:g['v220_on_tick']('999901',10000,base.replace(second=0)+timedelta(minutes=m),{},q)
ck(c['invalid_reasons'].get('SEQUENCE_GAP',0)>=1 and c['history'][-1]['valid'],'sequence-gap recovery');g['v220_mark_stream_gap']()
for q,m in [(19,12),(20,13),(21,14)]:g['v220_on_tick']('999901',10000,base.replace(second=0)+timedelta(minutes=m),{},q)
ck(c['history'][-1]['valid'],'reconnect recovery')
# state schema and day reset
g['v220_checkpoint'](True);ck(g['v220_restore'](base),'same-day restore');ck(g['v220_candidates']['999901']['needs_partial_bar'],'restart partial once');g['v220_reset_day'](base+timedelta(days=1));ck(not g['v220_candidates'] and all(v==0 for v in g['v220_metrics'].values()),'day reset')
# health isolation
g['v220_reset_day'](base);c=g['v230_create_candidate_state']({'code':'999901','stock':stock,'candidate_start_time':base,'sources':{'BASE'},'parent_trade_ids':[],'candidate_source':'BASE'});g['v220_candidates']['999901']=c;g['v231_check_health'](base+timedelta(minutes=5));ck(g['v220_halted'] and g['v220_entry_allowed'](stock,'BASE',{}),'health halt keeps BASE');ck(not g['v220_entry_allowed'](stock,'PULLBACK_STRUCTURE_ENTRY',{}),'health halt blocks new modes')
# snapshot ledger-first
g['v220_reset_day'](base);c=g['v230_create_candidate_state']({'code':'999901','stock':stock,'candidate_start_time':base,'sources':{'BASE'},'parent_trade_ids':[],'candidate_source':'BASE'});c.update(l1=9900,l1_time=base,fixed_b=10000,support_touch_count=2,data_status='OK',swing_highs=[10000,10010],swing_lows=[9900,9901]);c['snapshot_schedules']={30:base+timedelta(minutes=30)};bar={'minute':base+timedelta(minutes=29),'open':9900,'high':10000,'low':9900,'close':9990,'valid':True};old=g['v231_write_ledger'];g['v231_write_ledger']=lambda *a:False;g['v230_snapshot'](c,bar,30,bar['minute']+timedelta(minutes=1));ck(not c['snapshots_done'] and not c['pending'],'snapshot ledger-first');g['v231_write_ledger']=old
# strategy transition + grids
g['v220_reset_day'](base);c=g['v230_create_candidate_state']({'code':'999901','stock':stock,'candidate_start_time':base.replace(second=0),'sources':{'BASE'},'parent_trade_ids':[],'candidate_source':'BASE'});g['v220_candidates']['999901']=c
px=[(10000,10000,10000,10000),(10000,10000,9840,9850),(9850,9900,9850,9900),(9900,10000,9900,10000),(10000,10000,9940,9970),(9970,9990,9940,9980),(9980,10020,9970,10020),(10020,10020,9980,9990)]
for i,(o,h,l,z) in enumerate(px):b={'minute':base.replace(second=0)+timedelta(minutes=i),'open':o,'high':h,'low':l,'close':z,'volume':1,'tick_count':1,'valid':True};g['v220_complete_bar'](c,b,b['minute']+timedelta(minutes=1))
ck(c['state']=='STRUCTURE_READY' and c['pending'],'structure signal');g['v220_fill_pending'](c,10010,b['minute']+timedelta(minutes=1,seconds=1));tid=next(iter(c['entered'].values()));ck(len(g['paper_positions'][tid]['strategies'])==63,'new 63-grid')
# definitions/order engine preserved
pa=''.join(json.loads(PARENT.read_text())['cells'][1]['source']);ch=''.join(n['cells'][1]['source']);A={x.name:x for x in ast.parse(pa).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};B={x.name:x for x in ast.parse(ch).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};ck(set(A)<=set(B),'parent definitions preserved');keys=[k for k in A if any(t in k for t in('broker','submit_live','submit_stock','exit_worker','safe_rest','live_order','live_position')) and not k.startswith('run_')];ck(all(ast.dump(A[k],include_attributes=False)==ast.dump(B[k],include_attributes=False) for k in keys),'order/broker functions unchanged')
print(json.dumps({'status':'PASS','checks':checks,'parent_definitions':len(A),'order_broker_definitions':len(keys),'external_connections':0,'broker_orders':0},ensure_ascii=False,indent=2))
