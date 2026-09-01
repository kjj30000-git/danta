#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import traceback
from pathlib import Path

FILES = [
    ("A_GITHUB", Path("014_260901_v1.6.8.ipynb"), "test_v168_manual_sell_ledger_helpers"),
    ("B_NEWCHAT", Path("014_260901_v1.6.8(새채팅).ipynb"), "test_v168_live_ledger_and_timing"),
]
OUT = Path("v1.6.8_regression_run_report_260901.txt")

# Dummy env only satisfies module-level config validation prerequisites.
# No scanner/main function is executed and no live API call is intentionally made.
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
for label,path,v168_test in FILES:
    lines.append("="*80)
    lines.append(f"{label}: {path}")
    lines.append("="*80)
    try:
        nb=json.loads(path.read_text(encoding="utf-8-sig"))
        ns={"__name__":"v168_regression_module","__file__":str(path.resolve())}
        exec(compile(src(nb["cells"][0]), f"{path}:cell1", "exec"),ns,ns)
        exec(compile(src(nb["cells"][1]), f"{path}:cell2", "exec"),ns,ns)
        tests=["test_v166_core_logic","test_v166_live_order_safety",v168_test]
        for name in tests:
            fn=ns.get(name)
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
