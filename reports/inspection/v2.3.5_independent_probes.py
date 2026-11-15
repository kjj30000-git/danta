"""Independent adversarial probes: reporting/continuity/transaction boundaries.

Uses the shipped notebook loader only to obtain an isolated namespace. It does
not reuse the implementation author's assertions or alter engine methods.
All broker/network access is forbidden by the loader.
"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('release_validation', ROOT/'reports/regression/v2.3.5_validation.py')
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

class IndependentReview(unittest.TestCase):
    def setUp(self):
        self.t = BASE.Validation('test_a_operational_chain_fill_exit_export_restore')
        self.t.setUp()
    def tearDown(self):
        self.t.tearDown()

    def test_report_account_return_preserves_actual_profit(self):
        t=self.t
        t.signal_a(); t.quote(t.at(3,0,30000)); t.quote(t.at(3,1),10220,10210)
        account=t.e.s['accounts']['UNFILTERED']
        trade=next(iter(account['trades'].values()))
        expected=(account['cash']-t.e.config['capital'])/t.e.config['capital']*100
        self.assertGreater(expected,0)
        t.e.daily(t.at(3,2)); t.e.commit()
        row=next(r for r in t.rows('SCORECARD') if r['policy']=='UNFILTERED' and r['strategy']==t.A)
        self.assertAlmostEqual(row['account_realized_return_pct'],expected)
        self.assertAlmostEqual(row['net_pnl'],trade['net_pnl'])

    def test_terminal_signal_is_not_later_missing_data(self):
        t=self.t
        c=t.signal_a(); t.quote(t.at(3,0,30000))
        for minute in (3,4):
            t.ticks(minute,10050)
        t.tick(5,0,10050)
        t.process('MAINTAIN','',t.at(5,1),{})
        rows=[r for r in t.rows('EVALUATION') if r['strategy']==t.A and r.get('evaluation_at') in (t.at(4).isoformat(),t.at(5).isoformat())]
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r['status']=='TERMINAL_ALREADY_SIGNALLED' for r in rows))

    def test_reconnect_requires_new_ack(self):
        t=self.t
        c=t.candidate()
        self.assertTrue(c['subscription_ok'])
        t.process('GAP','',t.at(3),{'reason':'RECONNECT'})
        self.assertFalse(c.get('subscription_ok',False))
        t.process('SUBSCRIPTION',c['code'],t.at(3,1),{'item':c['code'],'types':['0B','0D'],'status':'ACK'})
        self.assertTrue(c['subscription_ok'])

    def test_post05_partial_bar_invalidates_first_event(self):
        t=self.t
        c=t.candidate()
        c.update(b_status='READY',range_low=10000,range_ready_at=t.at(5).isoformat())
        bar=dict(minute=t.at(5).isoformat(),open=10000,high=10000,low=9900,close=10000,volume=20,trade_value=200000,valid=False)
        t.e.complete(c,bar,t.at(6),t.at(6)); t.e.commit()
        self.assertEqual(c['b_status'],'OPENING_RANGE_INCOMPLETE')
        self.assertTrue(c['post05_gap'])
        self.assertFalse(t.rows('FIRST_BREAK'))

    def test_reference_overlap_mismatch_never_initializes_range(self):
        t=self.t
        c=t.candidate()
        c.update(b_status='WAIT_REFERENCE',segment_start=t.at(4).isoformat())
        c['reference_check_bars']=[dict(minute=t.at(m).isoformat(),open=10010,high=10020,low=10000,close=10010,volume=100) for m in (5,6)]
        rows=[dict(cntr_tm=t.at(m).strftime('%Y%m%d%H%M%S'),open_pric='10010',high_pric='10020',low_pric='10000',cur_prc='10010',trde_qty='101') for m in range(7)]
        t.process('REFERENCE',c['code'],t.at(7,1),{'stk_min_pole_chart_qry':rows})
        self.assertNotEqual(c['b_status'],'READY')
        self.assertFalse(t.rows('RANGE_READY'))

    def test_sql_failure_recovery_does_not_duplicate_committed_journal(self):
        t=self.t
        c=t.candidate()
        before=t.e.db.execute('SELECT count(*) FROM journal').fetchone()[0]
        t.e.db.execute('PRAGMA query_only=ON')
        with self.assertRaises(Exception):
            t.process('GAP',c['code'],t.at(3),{'reason':'INDEPENDENT_WRITE_FAILURE'})
        t.e.db.execute('PRAGMA query_only=OFF')
        t.e.commit(); t.e.commit()
        matching=[r for r in t.rows('GAP') if r.get('reason')=='INDEPENDENT_WRITE_FAILURE']
        self.assertEqual(len(matching),1)
        self.assertGreater(t.e.db.execute('SELECT count(*) FROM journal').fetchone()[0],before)
        self.assertTrue(t.e.export())
        import sqlite3
        with sqlite3.connect('opportunity_state_v235.backup.sqlite3') as db:
            expected=db.execute('SELECT count(*) FROM journal').fetchone()[0]
        import csv
        total=0
        for p in Path('.').glob('opportunity_*_v235.csv'):
            with p.open(encoding='utf-8-sig',newline='') as f:total+=len(list(csv.DictReader(f)))
        self.assertEqual(total,expected)

    def test_rank_bad_row_isolated_from_normal_rows(self):
        t=self.t
        row=lambda code:dict(stk_cd=code,stk_nm='fixture',cur_prc='10000',now_trde_qty='1000',flu_rt='7')
        t.process('RANK','',t.at(),{'market':'KOSPI','rows':[row('999001'),None,row('999002')]})
        self.assertTrue({'999001','999002'}<=set(t.e.s['candidates']))
        self.assertFalse(t.e.halted)

    def test_remaining_active_slot_obeys_rank_priority(self):
        t=self.t
        t.e.config['max_candidates']=2
        old=t.candidate('999001',t.at(1))
        held=t.candidate('999003',t.at(1))
        old['active']=False
        held['active']=True
        row=lambda code:dict(stk_cd=code,stk_nm='fixture',cur_prc='10000',now_trde_qty='1000',flu_rt='7')
        t.process('RANK','',t.at(1,1),{'market':'KOSPI','rows':[row('999002'),row('999001')]})
        self.assertTrue(t.e.s['candidates']['999002']['active'])
        self.assertFalse(t.e.s['candidates']['999001']['active'])

    def test_unconfirmed_fill_is_reported_and_blocks_profit_pass(self):
        t=self.t
        t.signal_a(); t.quote(t.at(3,0,30000))
        t.process('MAINTAIN','',t.at(20,hour=15),{})
        t.process('MAINTAIN','',t.at(30,hour=15),{})
        report=t.rows('FIXED_EXPERIMENT_SCORECARD')[-1]
        row=next(r for r in report['rows'] if r['policy']=='UNFILTERED' and r['strategy']=='ALL_SHARED')
        self.assertEqual(row['unresolved_count'],1)
        self.assertEqual(len(row['unresolved_trade_ids']),1)
        self.assertNotEqual(row['decision'],'PASS')

    def test_known_condition_failure_is_not_missing_data(self):
        t=self.t
        c=t.candidate()
        t.ticks(0,10000);t.ticks(1,10000);t.ticks(2,10000,20)
        c['rank_at']=t.at(2,59).isoformat()
        cum=t.cum['999001']+10
        t.process('TRADE','999001',t.at(3),{'20':'090300','10':'10000','13':str(cum),'15':'10','14':'1000','12':'3','16':'9500','290':'2','v235_item':'999001'})
        rows=[r for r in t.rows('EVALUATION') if r['strategy']==t.A and r.get('evaluation_at')==t.at(3).isoformat()]
        self.assertEqual(len(rows),1)
        self.assertNotEqual(rows[0]['status'],'DATA_UNAVAILABLE')
        self.assertFalse(t.rows('SIGNAL'))

if __name__=='__main__':
    unittest.main(verbosity=2)
