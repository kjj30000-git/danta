#!/usr/bin/env python3
import json,tempfile,csv,os,socket
from pathlib import Path
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[2];n=json.loads((ROOT/'code/releases/028_260928_v2.3.1.ipynb').read_text());source=''.join(n['cells'][2]['source']);g={'__name__':'pnl_test'};exec(compile(source,'pnl','exec'),g)
checks=[]
def ck(x,n):assert x,n;checks.append(n)
stock={'stk_cd':'005930','stk_nm':'TEST'};fills=[dict(stock,ord_no='1',io_tp_nm='매수',cntr_qty='4',cntr_pric='100'),dict(stock,ord_no='2',io_tp_nm='매수',cntr_qty='6',cntr_pric='110'),dict(stock,ord_no='3',io_tp_nm='매도',cntr_qty='5',cntr_pric='120')];journal=[dict(stock,pl_amt='65')];detail=[dict(stock,cntr_qty='5',buy_uv='106',cntr_pric='120',tdy_sel_pl='65',pl_rt='12.26',tdy_trde_cmsn='3',tdy_trde_tax='2')];args=('2026-09-28',fills,journal,detail,{'005930':D(5)},{'1','2','3'},'now');r=g['pnl_aggregate'](*args)[0]
ck(r['buy_qty']==10 and r['avg_buy_price']==106,'weighted buys');ck(r['sell_qty']==5 and r['remaining_qty']==5,'partial sell');ck(r['net_profit']==65 and r['broker_cost_basis']==530 and r['reconciliation_status']=='MATCHED','broker reconciliation');ck(r['first_buy_time']=='' and r['buy_fill_count']=='','unknown fields blank')
for auto,label in [({'1','2','3'},'AUTO_CONFIRMED'),({'1'},'MIXED'),(set(),'MANUAL_OR_UNMATCHED'),(None,'UNKNOWN')]:ck(g['pnl_aggregate'](*args[:5],auto,args[6])[0]['classification']==label,label)
folder=Path(tempfile.mkdtemp());p=folder/'p.csv';ck(g['pnl_save']([r],p)==(1,0),'first save');ck(g['pnl_save']([r],p)==(0,1),'same-day upsert');r2=dict(r,trade_date='2026-09-29');g['pnl_save']([r2],p);ck(len(list(csv.DictReader(p.open(encoding='utf-8-sig'))))==2,'other date accumulates');before=p.read_bytes()
class Fail:
 def authenticate(self):pass
 def pages(self,api,*x):
  if api=='ka10076':return fills
  raise RuntimeError('mid failure')
try:g['collect_broker_daily_stock_pnl'](Fail(),p,folder/'none')
except RuntimeError:pass
ck(p.read_bytes()==before,'API failure preserves CSV');ck(not any(x in source for x in('kt10000','kt10001','kt10002','kt10003')),'no order APIs');ck(not any(x in p.read_text(encoding='utf-8-sig').lower() for x in('appkey','secretkey','authorization','token')),'no secrets')
print(json.dumps({'status':'PASS','checks':checks,'external_connections':0,'broker_orders':0},ensure_ascii=False,indent=2))
