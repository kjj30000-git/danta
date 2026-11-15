"""Network-disabled release tests; operational classes/functions are executed unmodified."""
import ast
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE=ROOT/'code/releases/032_261116_v2.3.5.ipynb'
if not CANDIDATE.exists():CANDIDATE=ROOT/'code/candidates/032_261116_v2.3.5.ipynb'
PARENT=ROOT/'code/releases/031_261109_v2.3.4.ipynb'
SOURCES=[''.join(c['source']) for c in json.loads(CANDIDATE.read_text())['cells']]
PARENTS=[''.join(c['source']) for c in json.loads(PARENT.read_text())['cells']]

# Test runner never gives imported names to the notebook namespace.
def blocked(*args,**kwargs):
    raise AssertionError('EXTERNAL_NETWORK_FORBIDDEN')
socket.socket.connect=blocked
socket.socket.connect_ex=blocked


def load():
    Path('.env').write_text('KIWOOM_APP_KEY=fixture\nKIWOOM_SECRET_KEY=fixture\nTELEGRAM_BOT_TOKEN=fixture\nTELEGRAM_PERSONAL_CHAT_ID=123\n')
    m={'__name__':'isolated_release'}
    for i in (0,1):exec(compile(SOURCES[i],f'cell{i+1}','exec'),m)
    m['log']=lambda *a,**k:None
    return m

class Validation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=Path.cwd();os.chdir(self.tmp.name)
        self.m=load();self.dt=self.m['datetime'];self.td=self.m['timedelta']
        self.day=self.dt(2026,11,16,9)
        self.e=self.m['Opportunity235']('opportunity_state_v235.sqlite3',self.day)
        self.A=self.m['V235_A'];self.B=self.m['V235_B'];self.cum={}
    def tearDown(self):
        self.e.db.close();os.chdir(self.old);self.tmp.cleanup()
    def at(self,minute=0,second=0,microsecond=0,hour=9):return self.day.replace(hour=hour,minute=minute,second=second,microsecond=microsecond)
    def process(self,kind,code,at,data,detected=None):self.e.process(kind,code,at,data,detected or at)
    def candidate(self,code='999001',at=None):
        at=at or self.at(microsecond=1000)
        row={'stk_cd':code,'stk_nm':'fixture','cur_prc':'10000','now_trde_qty':'100000','flu_rt':'7'}
        self.process('RANK','',at,{'market':'KOSPI','rows':[row]})
        self.e.master[code]={'market':'KOSPI','day':'2026-11-16','ordinary':True}
        self.process('SUBSCRIPTION',code,at,{'item':code,'types':['0B','0D'],'status':'ACK'})
        return self.e.s['candidates'][code]
    def tick(self,minute,second,price,qty=10,code='999001',detected=None):
        at=self.at(minute,second)
        self.cum[code]=self.cum.get(code,0)+qty
        self.process('TRADE',code,at,{'20':at.strftime('%H%M%S'),'10':str(price),'13':str(self.cum[code]),'15':str(qty),'14':'3000','12':'7','16':'9500','290':'2','v235_item':code},detected)
    def ticks(self,minute,price,qty=10,code='999001',last=None):
        for sec in range(60):self.tick(minute,sec,last if last and sec==59 else price,qty,code)
    def quote(self,at,ask=10050,bid=10040,aq=2000,bq=2000,code='999001',**extra):
        self.process('QUOTE',code,at,{'21':at.strftime('%H%M%S'),'41':str(ask),'51':str(bid),'61':str(aq),'71':str(bq),'v235_item':code,**extra})
    def signal_a(self,code='999001'):
        c=self.candidate(code)
        self.ticks(0,10000,10,code);self.ticks(1,10000,10,code);self.ticks(2,9990,20,code,last=10050)
        # Fresh rank snapshot independently of trade value updates.
        c['rank_at']=self.at(2,59).isoformat()
        self.tick(3,0,10050,10,code,detected=self.at(3,0,10000))
        return c
    def rows(self,kind):return [json.loads(p) for p, in self.e.db.execute('SELECT payload FROM journal WHERE kind=?',(kind,))]

    def test_a_operational_chain_fill_exit_export_restore(self):
        c=self.signal_a();self.assertIn(self.A,c['used_signals'])
        self.assertEqual(len(self.rows('SIGNAL')),1)
        self.quote(self.at(3,0,30000));self.assertEqual(self.e.s['accounts']['UNFILTERED']['count'],1)
        self.quote(self.at(3,1),10220,10210)
        t=next(iter(self.e.s['accounts']['UNFILTERED']['trades'].values()))
        self.assertEqual(t['status'],'CLOSED');self.assertGreater(t['net_pct'],0)
        self.assertTrue(self.e.export())
        self.assertTrue(Path('opportunity_events_v235.csv').exists())
        ids=self.e.db.execute('SELECT count(*) FROM journal').fetchone()[0]
        self.e.db.close();self.e=self.m['Opportunity235']('opportunity_state_v235.sqlite3',self.at(3,2))
        self.assertEqual(self.e.s['accounts']['UNFILTERED']['count'],1)
        self.assertGreater(self.e.db.execute('SELECT count(*) FROM journal').fetchone()[0],ids)
        self.quote(self.at(3,3),10220,10210)
        self.assertEqual(len([r for r in self.rows('EXIT') if r['policy']=='UNFILTERED']),1)

    def test_b_reference_true_path_and_no_retro_signal(self):
        c=self.candidate();self.ticks(4,10020);self.ticks(5,10020);self.ticks(6,10030);self.tick(7,0,9980)
        ref={'stk_min_pole_chart_qry':[{'cntr_tm':self.at(i).strftime('%Y%m%d%H%M%S'),'low_pric':'10000' if i<5 else str(10020 if i==5 else 10030),'high_pric':'10030' if i<5 else str(10020 if i==5 else 10030),'open_pric':'10010' if i<5 else str(10020 if i==5 else 10030),'cur_prc':'10020' if i<5 else str(10020 if i==5 else 10030),'trde_qty':'100' if i<5 else '600'} for i in range(7)]}
        self.process('REFERENCE','999001',self.at(7,1),ref)
        self.assertEqual(c['b_status'],'READY')
        for sec in range(1,60):self.tick(7,sec,9980)
        c['rank_at']=self.at(7,59).isoformat()
        self.tick(8,0,9990);self.assertEqual(c['b_status'],'BREAK')
        for sec in range(1,60):self.tick(8,sec,10050 if sec==59 else 9990,20)
        c['rank_at']=self.at(8,59).isoformat()
        self.tick(9,0,10050,detected=self.at(9,0,10000))
        self.assertIn(self.B,c['used_signals'])
        signal=[r for r in self.rows('SIGNAL') if r['strategy']==self.B][0]
        self.assertGreaterEqual(signal['detected_at'],c['range_ready_at'])
        self.quote(self.at(9,0,30000));self.assertEqual(self.e.s['accounts']['UNFILTERED']['count'],1)

    def test_b_gap_after_range_blocks_second_first_event(self):
        c=self.candidate();c.update(b_status='READY',range_low=10000,range_ready_at=self.at(5).isoformat())
        self.process('GAP','999001',self.at(5,30),{'reason':'RECONNECT'})
        self.assertEqual(c['b_status'],'OPENING_RANGE_INCOMPLETE')

    def test_future_index_and_correct_t_anchor(self):
        c=self.candidate()
        for minute in range(7):self.process('INDEX','001',self.at(minute),{'20':self.at(minute).strftime('%H%M%S'),'10':str(100+minute),'16':'100'})
        ctx=self.e.context(self.at(6,10),c,10000)
        self.assertAlmostEqual(ctx['KOSPI']['change_5m_pct'],(106/101-1)*100)
        self.assertEqual(ctx['KOSPI']['anchor_300'],self.at(1).isoformat())
        ctx=self.e.context(self.at(5,30),c,10000)
        self.assertIsNone(ctx['KOSPI']['change_5m_pct'])
        self.assertIsNone(ctx['relative_strength_pp'])
        future=self.e.context(self.at(4,59),c,10000)
        self.assertLessEqual(future['KOSPI']['received_at'],self.at(4,59).isoformat())

    def test_no_index_blocks_comparison_only(self):
        self.signal_a();self.assertEqual(len(self.e.s['accounts']['UNFILTERED']['trades']),1)
        self.assertFalse(self.e.s['accounts']['INDEX_UP']['trades'])
        self.assertTrue(any(k.startswith('PAIR:') for k in self.e.s['accounts']))

    def test_duplicate_and_signed_wide_exit(self):
        self.signal_a();self.quote(self.at(3,0,30000),-10050,-10040)
        count=len(self.rows('FILL'));self.quote(self.at(3,0,40000),-10050,-10040)
        self.assertEqual(count,len(self.rows('FILL')))
        self.quote(self.at(3,1),-10100,-9900)
        t=next(iter(self.e.s['accounts']['UNFILTERED']['trades'].values()))
        self.assertEqual(t['status'],'CLOSED');self.assertEqual(t['exit_reason'],'STOP_LOSS')

    def test_wait_deadline_delay5_no_fill(self):
        self.signal_a();self.quote(self.at(3,3,10000))
        self.assertEqual(self.e.s['accounts']['UNFILTERED']['count'],0)
        self.assertEqual(next(iter(self.e.s['accounts']['UNFILTERED']['trades'].values()))['status'],'NO_FILL')
        self.quote(self.at(3,5))
        self.assertEqual(self.e.s['accounts']['UNFILTERED_DELAY_5']['count'],0)

    def test_partial_exit_inventory_and_unconfirmed(self):
        self.signal_a();self.quote(self.at(3,0,30000));self.quote(self.at(3,1),10220,10210,bq=100)
        t=next(iter(self.e.s['accounts']['UNFILTERED']['trades'].values()))
        self.assertEqual(t['sold'],10);self.assertEqual(t['status'],'EXIT_PENDING')
        self.quote(self.at(3,1,10000),10220,10210,bq=100);self.assertEqual(t['sold'],10)
        self.process('MAINTAIN','',self.at(20,hour=15),{})
        self.assertEqual(t['status'],'EXIT_UNCONFIRMED');self.assertNotIn('net_pct',t)

    def test_time_exit_uses_first_fresh_bid_not_stale(self):
        self.signal_a();self.quote(self.at(3,0,30000));t=next(iter(self.e.s['accounts']['UNFILTERED']['trades'].values()))
        self.process('MAINTAIN','',self.at(8,1),{})
        self.assertEqual(t['status'],'EXIT_PENDING')
        self.quote(self.at(8,2),10050,10040)
        self.assertEqual(t['status'],'CLOSED');self.assertEqual(t['exit_reason'],'TIME_EXIT')

    def test_product_missing_and_volume_reverse(self):
        c=self.candidate();self.e.master.clear()
        self.assertIn('PRODUCT_CLASSIFICATION_UNAVAILABLE',self.e.common(c,self.at()))
        self.tick(1,0,10000);self.cum['999001']=-100;self.tick(1,1,10000)
        self.assertTrue(self.rows('GAP'))

    def test_boundaries_and_tick_prices(self):
        tick=self.m['v235_tick_price']
        self.assertEqual(tick(1999),2000);self.assertEqual(tick(2000),2005);self.assertEqual(tick(2000,-1),1999)
        self.assertEqual(tick(5000,-1),4995);self.assertEqual(tick(20000),20050)
        between=self.m['v234_between']
        for h,start,end in [(9,'09:02','09:10'),(9,'09:05','10:00')]:
            a=self.day.replace(hour=int(start[:2]),minute=int(start[3:]));b=self.day.replace(hour=int(end[:2]),minute=int(end[3:]))
            self.assertFalse(between(a-self.td(microseconds=1),start,end));self.assertTrue(between(a,start,end))
            self.assertTrue(between(b-self.td(microseconds=1),start,end));self.assertFalse(between(b,start,end))

    def test_active_limit_rank_churn(self):
        for market in ('KOSPI','KOSDAQ'):
            rows=[{'stk_cd':str(800000+(0 if market=='KOSPI' else 100)+i),'stk_nm':'x','cur_prc':'10000','now_trde_qty':'100000','flu_rt':'7'} for i in range(10)]
            self.process('RANK','',self.at(1),{'market':market,'rows':rows})
        rows=[{'stk_cd':str(810000+i),'stk_nm':'x','cur_prc':'10000','now_trde_qty':'100000','flu_rt':'7'} for i in range(10)]
        self.process('RANK','',self.at(1,1),{'market':'KOSPI','rows':rows})
        self.assertLessEqual(sum(c['active'] for c in self.e.s['candidates'].values()),20)

    def test_shared_budget_count_and_reject_same_stock(self):
        c=self.candidate();c.update(actual_value=3000000000,value_at=self.at(3).isoformat(),rank_at=self.at(3).isoformat(),change_at=self.at(3).isoformat())
        bar={'minute':self.at(2).isoformat(),'close':10000}
        self.e.signal(c,self.A,bar,self.at(3));self.e.signal(c,self.B,bar,self.at(3));self.e.commit()
        self.assertEqual(len(self.e.s['accounts']['UNFILTERED']['trades']),1)
        self.assertTrue(any(r['reason']=='SAME_STOCK' for r in self.rows('REJECT')))
        self.e.invariants()

    def test_export_failure_does_not_duplicate_fills(self):
        self.signal_a();self.quote(self.at(3,0,30000))
        Path('opportunity_events_v235.tmp').mkdir()
        self.assertFalse(self.e.export());self.assertEqual(self.e.s['accounts']['UNFILTERED']['count'],1)
        Path('opportunity_events_v235.tmp').rmdir();self.assertTrue(self.e.export())

    def test_parent_definition_preservation_and_independent_cell(self):
        defs=lambda s:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        before,after=defs(PARENTS[1]),defs(SOURCES[1])
        self.assertTrue(before.keys()<=after.keys())
        for name in ['submit_stock_order','submit_live_exit','_submit_live_exit_worker','compute_broker_fill_delta','get_broker_positions','get_broker_pending_orders','handle_order_execution','force_close_live_positions','maybe_open_live_trade']:
            self.assertEqual(before[name],after[name],name)
        self.assertEqual(SOURCES[2],PARENTS[2]);self.assertTrue(SOURCES[3].startswith(PARENTS[3]));self.assertTrue(SOURCES[4].startswith(PARENTS[4]))
        self.assertFalse(self.m['AUTO_TRADE_ENABLED']);self.assertFalse(self.m['USE_MOCK'])
        self.assertTrue(self.m['test_v1713_order_safety']())

    def test_clean_cold_start_token_boundary(self):
        class TokenBoundary(BaseException):pass
        calls=[]
        def token():calls.append('TOKEN');raise TokenBoundary
        self.m['get_kiwoom_token']=token
        # Only external worker startup boundaries suppressed; actual config/start/database code is executed.
        for name in ('start_research_writer','start_research_safety_workers','start_live_exit_dispatcher','start_live_exit_watchdog','start_research_compute_worker','start_live_state_flusher'):
            self.m[name]=lambda:None
        self.m['OFF_HOURS_VALIDATION_MODE']=True
        with self.assertRaises(TokenBoundary):self.m['run_scanner']()
        self.assertEqual(calls,['TOKEN'])
        self.assertEqual(self.m['EXECUTION_MODE'],'RESEARCH')
        self.m['v235_queue'].put(None);self.m['v235_thread'].join(2)
        self.m['v235_engine'].db.close();self.m['v234_db'].close()

    def test_subscription_actual_admission_ack_and_200_limit(self):
        import asyncio
        c=self.candidate();c['subscription_ok']=False
        manager=self.m['KiwoomRealtimeManager']()
        self.m['v235_engine']=self.e;self.m['websocket_manager']=manager
        async def exercise():
            async def send(message):
                # Only external websocket boundary is replaced; pacing/admission/ACK event code is real.
                manager.v235_ack.set_result({'trnm':message['trnm'],'return_code':0})
            manager._send=send
            self.m['WEBSOCKET_REG_INTERVAL_SEC']=0
            self.assertTrue(await manager._register_item('999001'))
        asyncio.run(exercise())
        while not self.m['v235_queue'].empty():
            kind,code,at,data=self.m['v235_queue'].get_nowait()
            self.process(kind,code,self.at(),data)
            self.m['v235_queue'].task_done()
        self.assertTrue(c['subscription_ok'])
        for i in range(77):self.assertTrue(self.m['v235_subscription_admit'](manager,str(700000+i),['0B','0D']))
        self.assertTrue(self.m['v235_subscription_admit'](manager,'799998',['0B','0D']))
        self.assertFalse(self.m['v235_subscription_admit'](manager,'799999',['0B','0D']))
        self.assertIn('999001',manager.v235_desired)
        for i in range(20):
            code=str(600000+i);self.m['paper_position_ids_by_code'][code]={'held'}
            self.assertTrue(self.m['v235_subscription_admit'](manager,code,['0B','0D']))
        self.m['paper_position_ids_by_code']['699999']={'held'}
        self.assertFalse(self.m['v235_subscription_admit'](manager,'699999',['0B','0D']))

    def test_post_exit_path_survives_early_tp(self):
        self.signal_a();self.quote(self.at(3,0,30000));self.quote(self.at(3,1),10220,10210)
        for minute,second in ((4,1),(6,1),(8,1)):self.quote(self.at(minute,second),10220,10210)
        t=next(iter(self.e.s['accounts']['UNFILTERED']['trades'].values()))
        self.assertEqual(t['horizons'],[60,180,300]);self.assertEqual(t['status'],'CLOSED')

    def test_reject_unverified_minute_contract(self):
        c=self.candidate();c.update(b_status='WAIT_REFERENCE',reference_check_bars=[])
        self.process('REFERENCE','999001',self.at(7),{'stk_min_pole_chart_qry':[]})
        self.assertNotEqual(c['b_status'],'READY')
        self.assertTrue(self.rows('REFERENCE_CONTRACT_UNVERIFIED'))

    def test_sqlite_failure_keeps_events_for_recovery(self):
        self.candidate();self.e.db.execute('PRAGMA query_only=ON')
        with self.assertRaises(Exception):self.process('GAP','999001',self.at(3),{'reason':'DISK_FAILURE_FIXTURE'})
        self.assertTrue(self.e.halted);self.assertTrue(self.e.events)
        self.e.db.execute('PRAGMA query_only=OFF');self.e.commit()
        self.assertTrue(any(r['reason']=='DISK_FAILURE_FIXTURE' for r in self.rows('GAP')))

    def test_first_signal_daily_limit_and_shared_funds(self):
        for i in range(6):
            code=str(900000+i);c=self.candidate(code,self.at(3))
            c.update(actual_value=3000000000,value_at=self.at(3).isoformat(),rank_at=self.at(3).isoformat(),change_at=self.at(3).isoformat(),in_rank=True)
            self.e.signal(c,self.A,{'minute':self.at(2).isoformat(),'close':10000},self.at(3));self.e.commit()
        a=self.e.s['accounts']['UNFILTERED'];self.assertEqual(len(a['trades']),5);self.assertEqual(a['reserved'],5000000)
        self.assertTrue(any(r['reason']=='DAILY_LIMIT' for r in self.rows('REJECT')))
        for i in range(5):
            code=str(900000+i);self.e.s['candidates'][code]['in_rank']=True
            self.quote(self.at(3,0,30000),ask=10000,bid=9990,code=code)
        self.assertEqual(a['count'],5);self.e.invariants()

    def test_twenty_stock_sustained_pipeline_benchmark(self):
        started=time.perf_counter()
        for market,base in (('KOSPI',800000),('KOSDAQ',800100)):
            rows=[{'stk_cd':str(base+i),'stk_nm':'x','cur_prc':'10000','now_trde_qty':'100000','flu_rt':'7'} for i in range(10)]
            self.process('RANK','',self.at(),{'market':market,'rows':rows})
        codes=list(self.e.s['candidates'])
        count=0
        for sec in range(60):
            for code in codes:
                self.tick(1,sec,10000,10,code)
                self.quote(self.at(1,sec),10000,9990,code=code)
                count+=2
        elapsed=time.perf_counter()-started
        print(f'PERF raw_events={count} seconds={elapsed:.3f} events_per_sec={count/elapsed:.1f}')
        self.assertLess(elapsed,60,'Cannot sustain 20 stocks x 1Hz trade+quote')
        self.e.invariants()


    def test_simultaneous_priority_and_future_received_quote(self):
        # Fill four slots. Last same-time reservation initially B, then A displaces it.
        for i in range(5):
            code=str(910000+i);c=self.candidate(code,self.at(3))
            c.update(actual_value=3000000000,value_at=self.at(3).isoformat(),rank_at=self.at(3).isoformat(),change_at=self.at(3).isoformat())
            self.e.signal(c,self.B,{'minute':self.at(2).isoformat(),'close':10000},self.at(3))
        c=self.candidate('910010',self.at(3));c.update(actual_value=3000000000,value_at=self.at(3).isoformat(),rank_at=self.at(3).isoformat(),change_at=self.at(3).isoformat())
        self.e.signal(c,self.A,{'minute':self.at(2).isoformat(),'close':10000},self.at(3));self.e.commit()
        active=[t for t in self.e.s['accounts']['UNFILTERED']['trades'].values() if t['status']=='PENDING']
        self.assertEqual(len(active),5);self.assertTrue(any(t['strategy']==self.A for t in active))
        self.assertTrue(any(r.get('reason')=='SIMULTANEOUS_PRIORITY' for r in self.rows('NO_FILL')))

    def test_new_process_restores_subscription_targets(self):
        self.signal_a();self.quote(self.at(3,0,30000))
        self.e.db.close();self.e=self.m['Opportunity235']('opportunity_state_v235.sqlite3',self.at(4))
        self.m['v235_engine']=self.e
        manager=self.m['KiwoomRealtimeManager']()
        self.m['v235_restore_subscription_targets'](manager)
        self.assertIn('999001',manager.desired_items['999001'])
        self.assertFalse(self.e.s['candidates']['999001']['subscription_ok'])

    def test_import_negative_controls_detect_missing_modules(self):
        import subprocess
        source='\n'.join(SOURCES)
        for original,replacement in [('import zipfile',''),('import statistics',''),('from datetime import datetime, timedelta, timezone','from datetime import datetime, timedelta')]:
            altered=source.replace(original,replacement)
            Path('negative.py').write_text(altered)
            r=subprocess.run([sys.executable,'-m','pyflakes','negative.py'],text=True,capture_output=True)
            self.assertIn('undefined name',r.stdout,original)


if __name__=='__main__':unittest.main(verbosity=2)
