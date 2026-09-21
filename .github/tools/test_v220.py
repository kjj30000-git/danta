#!/usr/bin/env python3
"""独立プロセス用: 外部通信を実行前から封鎖して実関数を検証する。"""
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'code/releases/026_260922_v2.2.0.ipynb'
PARENT=ROOT/'code/releases/025_260916_v2.1.2.ipynb'

# 関数説明: 外部通信の試行自体を失敗にします。
def forbidden(*args,**kwargs):
    raise AssertionError('external network forbidden')

# 関数説明: notebookを新規namespaceで上から実行し、実関数fixtureを呼びます。
def main():
    import requests
    socket.socket.connect=forbidden
    socket.create_connection=forbidden
    requests.sessions.Session.request=forbidden
    notebook=json.loads(TARGET.read_text())
    parent=json.loads(PARENT.read_text())
    sources=[''.join(c['source']) for c in notebook['cells']]
    ps=[''.join(c['source']) for c in parent['cells']]
    assert len(sources)==4 and sources[2].startswith(ps[2]) and sources[3].startswith(ps[3])
    before=ast.parse(ps[1]);after=ast.parse(sources[1])
    defs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    old,new=defs(before),defs(after)
    assert set(old)<=set(new)
    changed=sorted(k for k in old if old[k]!=new[k])
    critical=['submit_stock_order','submit_cancel_order','submit_live_exit','_submit_live_exit_worker',
        '_safe_rest_exit_snapshot','compute_broker_fill_delta','reconcile_managed_quantities',
        'handle_order_execution','save_live_state','load_live_state','maybe_open_live_trade',
        '_evaluate_live_exit_policy','PriorityAPIAdmissionController','v20_run_etf_research']
    assert not set(changed)&set(critical),(set(changed)&set(critical))
    with tempfile.TemporaryDirectory(prefix='v220_validation_') as tmp:
        os.chdir(tmp)
        Path('.env').write_text('KIWOOM_APP_KEY=dummy\nKIWOOM_SECRET_KEY=dummy\nTELEGRAM_BOT_TOKEN=dummy\nTELEGRAM_PERSONAL_CHAT_ID=fixture\n')
        ns={'__name__':'v220_coldstart'}
        for i,src in enumerate(sources):exec(compile(src,f'cell{i+1}','exec'),ns)
        assert ns['EXECUTION_MODE']=='RESEARCH' and not ns['AUTO_TRADE_ENABLED'] and not ns['USE_MOCK']
        ns['validate_v220_config']();ns['validate_scanner_config']();ns['validate_live_trading_config']()
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            old_report=ns['run_off_hours_validation']()
            report=ns['run_v220_off_hours_validation']()
        report['parent_replay']=old_report['status']
        report['parent_definitions']=len(old)
        report['preserved_definitions']=len(set(old)&set(new))
        report['changed_definitions']=changed
        report['unchanged_order_engine_and_etf']=critical
        report['notebook_sha256']=hashlib.sha256(TARGET.read_bytes()).hexdigest()
        # Release自身のimport欠落を静的validatorが検出できることを確認。
        validator=ROOT/'.github/tools/validate_release_notebook.py'
        negative=[]
        for label,fragment in [('uuid','import uuid\n'),('median','from statistics import median\n'),('copy','import copy\n')]:
            mutant=json.loads(TARGET.read_text())
            src=''.join(mutant['cells'][1]['source'])
            assert src.count(fragment)==1
            mutant['cells'][1]['source']=src.replace(fragment,'').splitlines(keepends=True)
            path=Path(tmp)/f'bad_{label}.ipynb';path.write_text(json.dumps(mutant))
            p=subprocess.run([sys.executable,str(validator),str(path)],capture_output=True,text=True)
            assert p.returncode!=0 and 'undefined name' in p.stdout and label in p.stdout,(label,p.stdout,p.stderr)
            negative.append(label+': correctly rejected')
        report['negative_controls']=negative
    dest=ROOT/'reports/regression/v2.2.0_results.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
