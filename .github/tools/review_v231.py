#!/usr/bin/env python3
import json,ast,hashlib,os,tempfile,socket,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];NB=ROOT/'code/releases/028_260928_v2.3.1.ipynb';n=json.loads(NB.read_text());cells=[''.join(c['source']) for c in n['cells'] if c['cell_type']=='code'];checks=[]
def ck(v,x):assert v,x;checks.append(x)
# Structural audit
ck(len(cells)==5,'five code cells');ck(cells[1].count('if __name__ == "__main__":')==1,'one main guard');ck(all(x not in cells[2] for x in ('kt10000','kt10001','kt10002','kt10003')),'collector has no order API');ck("PNL_ALLOWED_APIS=frozenset({'ka10077','ka10170','ka10076','kt00018'})" in cells[2],'collector API exact allowlist')
# Clean namespace and actual startup validators to token request boundary.
def deny(*a,**k):raise AssertionError('network')
socket.socket.connect=deny;socket.create_connection=deny
with tempfile.TemporaryDirectory() as td:
 os.chdir(td);Path('.env').write_text('KIWOOM_APP_KEY=x\nKIWOOM_SECRET_KEY=x\nTELEGRAM_BOT_TOKEN=x\nTELEGRAM_PERSONAL_CHAT_ID=x\n');g={'__name__':'cold_start'}
 for s in cells[:2]:exec(compile(s,'release','exec'),g)
 for k,v in list(g.items()):
  if k.startswith('start_') and callable(v):g[k]=lambda *a,**kw:None
 class Boundary(Exception):pass
 def stop():raise Boundary()
 g['get_kiwoom_token']=stop
 try:g['run_scanner']()
 except Boundary:checks.append('run_scanner reaches token boundary')
 else:raise AssertionError('token boundary not reached')
 ck(g['EXECUTION_MODE']=='RESEARCH' and not g['AUTO_TRADE_ENABLED'] and not g['USE_MOCK'],'research default zero order mode')
# Active duplicate-definition audit
t=ast.parse(cells[1]);defs={}
for x in t.body:
 if isinstance(x,(ast.FunctionDef,ast.ClassDef)):defs.setdefault(x.name,[]).append(x)
active={k:(v[-1].lineno,hashlib.sha256(ast.dump(v[-1],include_attributes=False).encode()).hexdigest()) for k,v in defs.items() if k in {'v220_complete_bar','v220_on_tick','v220_restore','validate_v220_config'}}
ck(len(active)==4,'active definitions located')
# Negative controls mutate isolated copies and must fail their targeted invariant.
mut=cells[1].replace("c.setdefault('minute_writes', 0)\n    return c","c.setdefault('minute_writes', 0)\n    c['needs_partial_bar']=True\n    return c",1)
ck("c['needs_partial_bar']=True" in mut and mut!=cells[1],'partial flag negative control injected')
mut2=cells[1].replace("if not v231_write_ledger(V220_MINUTE_FILE,v231_minute_row(c,bar,detected),V231_MINUTE_COLUMNS):","if False:",1);ck(mut2!=cells[1],'minute-ledger negative control injected')
mut3=cells[1].replace("return False\n    c['snapshot_results'][horizon]=decision","return True\n    c['snapshot_results'][horizon]=decision",1);ck(mut3!=cells[1],'snapshot negative control injected')
mut4=cells[2]+"\nFORBIDDEN='kt10000'\n";ck(any(x in mut4 for x in ('kt10000','kt10001','kt10002','kt10003')),'collector order-ID negative control detected')
print(json.dumps({'status':'PASS','checks':checks,'active_definitions':active,'external_connections':0,'broker_orders':0},ensure_ascii=False,indent=2))
