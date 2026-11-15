"""Deterministic minimal-parent builder. Run from repository root."""
import ast
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
PARENT = ROOT/'code/releases/031_261109_v2.3.4.ipynb'
TARGET = ROOT/'code/candidates/032_261116_v2.3.5.ipynb'
assert hashlib.sha256(PARENT.read_bytes()).hexdigest()=='70baaf1f4d86b5e0e1eda4c42c00b07066b5aba943f4d336be253e738ca21499'
n = json.loads(PARENT.read_text())
sources = [''.join(c['source']) for c in n['cells']]
settings = dict(experiment_id='V235_AB_20261116_FIXED_1', rule_id='AB_FIXED_1', capital=6000000, per_stock=1000000,
 max_slots=5,max_daily=5,top_n=10,max_candidates=20,observe_pct=2.,entry_min_pct=5.,entry_max_pct=20.,min_value=2000000000,
 rank_age=45,quote_age=1,spread_pct=.15,depth_fraction=.10,wait_sec=3,flow_ratio=1.5,tp_pct=1.5,sl_pct=-.8,
 hold_a_sec=300,hold_b_sec=600,cost_pct=.24,subscription_limit=200,protected_subscription_reserve=40,cutoff='15:20',decision_date='2026-12-15',
 pass_min_days=20,pass_min_fills=100,pass_min_symbols=30,pass_pf=1.2,pass_availability=.95,pass_max_drawdown_pct=5.,
 pass_max_positive_concentration=.30,pass_cluster_lcb=0.,stress_pct=[.1,.2,.4],delays_sec=[1,3,5])
sources[0] = sources[0].replace('v2.3.4','v2.3.5')+'\n# v2.3.5 사전 고정 실험: 모든 수치의 단일 설정원\nV235_CONFIG = '+repr(settings)+'\n'
s = sources[1].replace('단타 자동 스크리너 v2.3.4 (부모 v2.3.3)','단타 자동 스크리너 v2.3.5 (부모 v2.3.4)',1)
s = s.replace('STRATEGY_VERSION = "v2.3.4"','STRATEGY_VERSION = "v2.3.5"')
s = s.replace('"v2.3.4"}', '"v2.3.4", "v2.3.5"}')
s = s.replace("STRATEGY_VERSION!='v2.3.4'", "STRATEGY_VERSION!='v2.3.5'").replace('v2.3.4은 RESEARCH','v2.3.5은 RESEARCH')
# Isolate all output/state suffix literals without renaming parent definitions or historical notes.
s = s.replace('_v234.', '_v235.').replace('_v234_', '_v235_')
s = s.replace('from datetime import datetime, timedelta','from datetime import datetime, timedelta, timezone')
s = s.replace('    v234_start(datetime.now())','    v234_start(datetime.now())\n    v235_start(datetime.now())')
s = s.replace('            v234_index_schedule(datetime.now())','            v234_index_schedule(datetime.now())\n            v235_maintenance(datetime.now())',1)
s = s.replace('                v231_flush_notifications()','                v235_drain()\n                v235_maintenance(datetime.now(), ending=True)\n                v235_finalize()\n                v231_flush_notifications()',1)
s = s.replace('            rows = get_change_rate_rank(market_code)\n            observed = datetime.now()',
 '''            rows = get_change_rate_rank(market_code)
            observed = datetime.now()
            v235_enqueue('RANK', '', observed, dict(market=market_name, rows=rows))''',1)
# Keep parent candidate registrations (including excluded observations) but bounded subscriptions.
s = s.replace('                raw = await ws.recv()','                raw = await ws.recv()',1)
s = s.replace('                    v220_mark_stream_gap()','                    v220_mark_stream_gap()\n                    v235_enqueue("GAP", "", datetime.now(), {"reason":"RECONNECT"})',1)
start=s.index('                    if AUTO_TRADE_ENABLED:\n                        await self._register_order_stream()',s.index('async def _connect_once'))
end=s.index('                    continue',start)
s=s[:start]+'''                    asyncio.create_task(v235_bootstrap(self))
'''+s[end:]
s=s.replace('                if trnm == "REG":','''                if trnm in ('REG','REMOVE'):
                    if self.v235_ack is not None and not self.v235_ack.done():
                        self.v235_ack.set_result(response)
''',1)
s=s.replace('                    if rtype == "0B":','''                    if rtype == '0D':
                        v235_enqueue('QUOTE', clean_stock_code(item), datetime.now(), dict(values, v235_item=item))
                    elif rtype == "0B":
                        if '_' not in item:
                            v235_enqueue('TRADE', clean_stock_code(item), datetime.now(), dict(values, v235_item=item))
                            continue''',1)
s=s.replace('                        v234_index_tick(item, values, datetime.now())','''                        v234_index_tick(item, values, datetime.now())
                        v235_enqueue('INDEX', item, datetime.now(), values)''',1)
s=s.replace('        self.last_reg_send_ts = 0.0','''        self.last_reg_send_ts = 0.0
        self.v235_desired = {}
        self.v235_ack = None
        self.v235_rejected = set()
        self.v235_removing = set()''',1)
s=s.replace('            v220_maintenance(datetime.now(), ending=True)\n            v231_flush_notifications()', '            v220_maintenance(datetime.now(), ending=True)\n            v235_finalize()\n            v231_flush_notifications()',1)
# AST localized replacement of WS methods only.
def method(name, body):
 global s
 tree=ast.parse(s);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='KiwoomRealtimeManager')
 node=next(x for x in cls.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==name)
 lines=s.splitlines(True);lines[node.lineno-1:node.end_lineno]=[body+'\n'];s=''.join(lines)
method('_paced_reg_send', '''    async def _paced_reg_send(self, message):
        if self.reg_async_lock is None:
            self.reg_async_lock = asyncio.Lock()
        async with self.reg_async_lock:
            request_key=json.dumps(message.get('data',[]),sort_keys=True)
            if 'CAPACITY' in self.v235_rejected or request_key in self.v235_rejected:
                for packet in message.get('data',[]):
                    for item in packet.get('item',[]):
                        v235_subscription_event(item,packet.get('type',[]),'REJECTED_NO_RETRY')
                return False
            elapsed = time.time() - self.last_reg_send_ts
            if elapsed < WEBSOCKET_REG_INTERVAL_SEC:
                await asyncio.sleep(WEBSOCKET_REG_INTERVAL_SEC - elapsed)
            self.v235_ack = asyncio.get_running_loop().create_future()
            data = message.get('data', [])
            try:
                await self._send(message)
                self.last_reg_send_ts = time.time()
                response = await asyncio.wait_for(self.v235_ack, 5)
                ok = response.get('return_code') in (0, '0')
                for packet in data:
                    for item in packet.get('item', []):
                        v235_subscription_event(item, packet.get('type', []),
                            ('REMOVED' if message['trnm']=='REMOVE' else 'ACK') if ok else 'REJECTED', response)
                if not ok:
                    self.v235_rejected.add('CAPACITY' if '105118' in str(response) else request_key)
                return ok
            except Exception as exc:
                self.v235_rejected.add(request_key)
                for packet in data:
                    for item in packet.get('item', []):
                        v235_subscription_event(item, packet.get('type', []), 'DELIVERY_UNKNOWN', {'error':type(exc).__name__})
                return False
            finally:
                self.v235_ack = None''')
method('_register_item','''    async def _register_item(self, item):
        types = ['0B'] if '_' in item else ['0B', '0D']
        if not v235_subscription_admit(self, item, types):
            return False
        return await self._paced_reg_send({'trnm':'REG', 'grp_no':WEBSOCKET_GROUP_NO,
            'refresh':'1', 'data':[{'item':[item], 'type':types}]})''')
method('_remove_item','''    async def _remove_item(self, item):
        ok = await self._paced_reg_send({'trnm':'REMOVE', 'grp_no':WEBSOCKET_GROUP_NO,
            'data':[{'item':[item], 'type':list(self.v235_desired.get(item,{'0B','0D'}))}]})
        if ok:
            v235_subscription_admit(self, item, ['0B','0D'], remove=True)
        return ok''')
method('subscribe_stock','''    def subscribe_stock(self, stock_code, session=None):
        code = clean_stock_code(stock_code)
        item = realtime_item_code(code, session)
        with self.lock:
            items = self.desired_items.setdefault(code, set())
            if item in items:
                return True
            if not v235_subscription_admit(self, item, ['0B']):
                return False
            items.add(item)
        if self.logged_in and self.loop is not None:
            asyncio.run_coroutine_threadsafe(self._register_item(item), self.loop)
        return True''')
method('unsubscribe_stock','''    def unsubscribe_stock(self, stock_code):
        code = clean_stock_code(stock_code)
        if v235_keep_ticks(code) and not shutdown_requested:
            return False
        with self.lock:
            items = list(self.desired_items.get(code, set()))
            if self.logged_in and self.loop is not None:
                for item in items:
                    asyncio.run_coroutine_threadsafe(v235_remove_confirmed(self,item,code), self.loop)
        return True''')
s=s.replace('    get_kiwoom_token()\n\n    restored = load_live_state()', '    get_kiwoom_token()\n    v235_launch_master()\n\n    restored = load_live_state()',1)
s=s.replace('        for item in items:\n            await self._register_item(item)', '        for item in sorted(items,key=lambda i:(v235_subscription_priority(i),i)):\n            await self._register_item(item)',1)
# On reconnect errors remain until explicit reconnect (no capacity-rejection retry storm).
s=s.replace('            self.logged_in = False\n            self.last_reg_send_ts', '            self.logged_in = False\n            self.v235_rejected.clear()\n            self.v235_removing.clear()\n            self.last_reg_send_ts',1)
# Limit legacy direct admission while retaining every observed candidate ledger row.
s=s.replace("    if v234_commit(c, [('', 'CANDIDATE', observed, details)]) and websocket_manager is not None:",
 "    if v234_commit(c, [('', 'CANDIDATE', observed, details)]) and websocket_manager is not None and stock.get('change_rank',999)<=10 and stock.get('change_rate',0)>=2:")
# Fix parent 5m t-anchor; retain all other parent behavior.
s=s.replace('anchor = stamp - timedelta(minutes=5)','anchor = at - timedelta(minutes=5)')
s=s.replace('(anchor - lag[0]).total_seconds() <= V234_INDEX_MAX_AGE_SEC','(anchor - lag[0]).total_seconds() <= 15')
s=s.replace("row[0].date() == at.date() and row[1] <= at", "row[0].date() == at.date() and row[0] <= row[1] <= at")
# Capture stock open before delayed score quote. Existing independent PnL cell untouched.
s=s.replace("    opening = v234_stock_open(c, received)","""    current_open = abs(safe_float(values.get('16')))
    if current_open and not c.get('main_open'):
        c.update(main_open=current_open, main_open_at=received)
    opening = v234_stock_open(c, received)""",1)
# Add all new definitions before sole main guard, keeping parent full source.
insert=s.index('\nif __name__ == "__main__":',s.index('v234_dropped_codes = set()'))
schemas=json.loads((HERE/'master_schemas.json').read_text())
addition='\nV235_MASTER_SCHEMAS = '+repr(schemas)+'\n'+(HERE/'opportunity.py').read_text()+'\n'+(HERE/'subscriptions.py').read_text()+'\n'+(HERE/'integration.py').read_text()
s=s[:insert]+addition+s[insert:]
sources[1]=s
sources[3]+='\n# v2.3.5: A 수급 지속/B 하락 실패 회복, 지수 UNFILTERED/INDEX_UP 정책별 공유600만원.\n# quote_plus_0p24_estimated, 대표 TP1.5/SL-0.8, A300초/B600초, 연구 전용.\n'
sources[4]+='\n# 2026-11-15 (일) v2.3.5: 부모 전체 보존, A/B·지수·공용구독·호가/자금 원장 추가.\n# 미검증 입력은 평가불가, 과거 수익 미입증, RESEARCH 실제·키움 모의주문0건.\n'
for c,source in zip(n['cells'],sources):
 c['source']=source.splitlines(True)
 c['outputs']=[];c['execution_count']=None
TARGET.write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n')
print(TARGET)
