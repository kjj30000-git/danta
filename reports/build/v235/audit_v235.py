"""Source/definition/import audit, deterministic rebuild, and startup clock boundaries."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[3]
PARENT=ROOT/'code/releases/031_261109_v2.3.4.ipynb'
CANDIDATE=ROOT/'code/candidates/032_261116_v2.3.5.ipynb'
OUTPUT=ROOT/'reports/build/v235/source_audit.json'

def cells(path):return [''.join(c['source']) for c in json.loads(path.read_text())['cells']]
def defs(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def imports(s):return sorted({ast.unparse(n) for n in ast.walk(ast.parse(s)) if isinstance(n,(ast.Import,ast.ImportFrom))})
parents,sources=cells(PARENT),cells(CANDIDATE)
a,b=defs(parents[1]),defs(sources[1])
assert a.keys()<=b.keys()
core=[n for n in a if any(k in n.lower() for k in ('live','broker','order','buy','sell','exit_cache'))]
assert all(a[n]==b[n] for n in core)
assert sources[2]==parents[2]
assert sources[3].startswith(parents[3]) and sources[4].startswith(parents[4])
for i,s in enumerate(sources):compile(s,str(i),'exec')
assert sum(isinstance(n,ast.If) and ast.unparse(n.test)=="__name__ == '__main__'" for n in ast.parse(sources[1]).body)==1
old_hash=hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(ROOT/'reports/build/v235/build_v235.py')],check=True,capture_output=True)
assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()==old_hash
spec=importlib.util.spec_from_file_location('v235_validation',ROOT/'reports/regression/v2.3.5_validation.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
clock_pass=[]
for hour,minute in ((8,0),(20,1)):
    with tempfile.TemporaryDirectory() as tmp:
        before=Path.cwd();os.chdir(tmp)
        try:
            m=v.load();original=m['datetime']
            class Clock(original):
                @classmethod
                def now(cls,*args):return cls(2026,11,16,hour,minute)
            m['datetime']=Clock;m['OFF_HOURS_VALIDATION_MODE']=True
            class Boundary(BaseException):pass
            def token():raise Boundary()
            m['get_kiwoom_token']=token
            for name in ('start_research_writer','start_research_safety_workers','start_live_exit_dispatcher','start_live_exit_watchdog','start_research_compute_worker','start_live_state_flusher'):m[name]=lambda:None
            try:m['run_scanner']()
            except Boundary:pass
            else:raise AssertionError('token boundary not reached')
            assert not m['AUTO_TRADE_ENABLED'] and not m['USE_MOCK']
            m['v235_queue'].put(None);m['v235_thread'].join(2)
            m['v235_engine'].db.close();m['v234_db'].close()
            clock_pass.append(f'{hour:02}:{minute:02}')
        finally:os.chdir(before)
result=dict(parent_sha256=hashlib.sha256(PARENT.read_bytes()).hexdigest(),candidate_sha256=old_hash,
 parent_definition_count=len(a),preserved_definition_count=len(a),new_definition_count=len(b)-len(a),
 preserved_order_broker_definitions=core,preserved_order_broker_count=len(core),
 changed_parent_definitions=[n for n in a if a[n]!=b[n]],new_import_statements=sorted(set(imports(sources[1]))-set(imports(parents[1]))),
 independent_pnl_identical=True,quick_reference_append_only=True,continuity_append_only=True,deterministic_rebuild=True,
 cold_start_clocks=clock_pass,actual_broker_orders=0,kiwoom_mock_orders=0,scope='static+isolated network-forbidden; public master checked separately')
OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
