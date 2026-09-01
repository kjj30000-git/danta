#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import json
import sys
import traceback
from pathlib import Path

FILES = [
    ("A_GITHUB", Path("014_260901_v1.6.8.ipynb"), "test_v168_manual_sell_ledger_helpers"),
    ("B_NEWCHAT", Path("014_260901_v1.6.8(새채팅).ipynb"), "test_v168_live_ledger_and_timing"),
]
OUT = Path("v1.6.8_regression_run_report_260901.txt")

Path(".env").write_text(
    "KIWOOM_APP_KEY=dummy\n"
    "KIWOOM_SECRET_KEY=dummy\n"
    "TELEGRAM_BOT_TOKEN=dummy\n"
    "TELEGRAM_PERSONAL_CHAT_ID=1\n"
    "TELEGRAM_SEND_PERSONAL=true\n"
    "TELEGRAM_SEND_GROUP=false\n",
    encoding="utf-8",
)

def src(cell):
    s=cell.get("source","")
    return "".join(s) if isinstance(s,list) else str(s)

lines=[]
for idx,(label,path,v168_test) in enumerate(FILES,1):
    lines.append("="*80)
    lines.append(f"{label}: {path}")
    lines.append("="*80)
    try:
        nb=json.loads(path.read_text(encoding="utf-8-sig"))
        module_path=Path(f"_tmp_v168_{idx}.py")
        module_path.write_text(src(nb["cells"][0])+"\n"+src(nb["cells"][1]),encoding="utf-8")
        mod_name=f"v168_regression_module_{idx}"
        spec=importlib.util.spec_from_file_location(mod_name,module_path)
        mod=importlib.util.module_from_spec(spec)
        sys.modules[mod_name]=mod
        spec.loader.exec_module(mod)
        tests=["test_v166_core_logic","test_v166_live_order_safety",v168_test]
        for name in tests:
            fn=getattr(mod,name,None)
            if not callable(fn):
                lines.append(f"{name}: MISSING")
                continue
            try:
                result=fn()
                lines.append(f"{name}: PASS / return={result!r}")
            except Exception as e:
                lines.append(f"{name}: FAIL / {type(e).__name__}: {e}")
                lines.append(traceback.format_exc())
    except Exception as e:
        lines.append(f"MODULE_LOAD: FAIL / {type(e).__name__}: {e}")
        lines.append(traceback.format_exc())

OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
