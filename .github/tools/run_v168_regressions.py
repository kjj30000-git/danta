#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import json
import sys
import traceback
from pathlib import Path

RELEASE = Path("code/releases/014_260902_v1.6.8.ipynb")
TESTS = [
    "test_v166_core_logic",
    "test_v166_live_order_safety",
    "test_v167_order_engine_safety",
    "test_v168_manual_sell_ledger_helpers",
]
OUT = Path("reports/regression/2026-09-01_v1.6.8_regression.txt")

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
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else str(s)


def load_fresh_module(path, suffix):
    nb = json.loads(path.read_text(encoding="utf-8-sig"))
    module_path = Path(f"_tmp_v168_{suffix}.py")
    module_path.write_text(
        src(nb["cells"][0]) + "\n" + src(nb["cells"][1]),
        encoding="utf-8",
    )
    mod_name = f"v168_regression_module_{suffix}"
    sys.modules.pop(mod_name, None)
    spec = importlib.util.spec_from_file_location(mod_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod, nb


lines = ["=" * 88, f"GITHUB_RELEASE: {RELEASE}", "=" * 88]
overall_ok = True

try:
    nb = json.loads(RELEASE.read_text(encoding="utf-8-sig"))
    assert len(nb.get("cells", [])) == 4
    assert all(c.get("cell_type") == "code" for c in nb["cells"])
    settings = src(nb["cells"][0])
    body = src(nb["cells"][1])
    continuity = src(nb["cells"][3])
    assert "AUTO_TRADE_ENABLED = False" in settings
    assert "FIRST_75_PASS" in body
    assert "T200_S150" in body
    assert "import tempfile" in body
    assert "PROJECT CONTINUITY PRINCIPLE" in continuity
    principle_at = continuity.find("# PROJECT CONTINUITY PRINCIPLE")
    first_dated = continuity.find("# 2026-")
    assert principle_at >= 0 and first_dated >= 0 and principle_at < first_dated
    lines.append(
        "STATIC_NOTEBOOK: PASS / 4 code cells, live OFF, strategy markers, "
        "tempfile import, principle before history"
    )
except Exception as e:
    overall_ok = False
    lines.append(f"STATIC_NOTEBOOK: FAIL / {type(e).__name__}: {e}")
    lines.append(traceback.format_exc())

for test_idx, name in enumerate(TESTS, 1):
    try:
        mod, _ = load_fresh_module(RELEASE, f"release_{test_idx}")
        fn = getattr(mod, name, None)
        if not callable(fn):
            overall_ok = False
            lines.append(f"{name}: MISSING")
            continue
        result = fn()
        lines.append(f"{name}: PASS / fresh-module / return={result!r}")
    except Exception as e:
        overall_ok = False
        lines.append(f"{name}: FAIL / fresh-module / {type(e).__name__}: {e}")
        lines.append(traceback.format_exc())

lines.append("=" * 88)
lines.append(f"OVERALL: {'PASS' if overall_ok else 'FAIL'}")
lines.append("NOTE: Independent new-chat candidate is comparison-only and does not gate this release.")
lines.append("NOTE: No broker/API live orders were submitted; regression helpers only.")
text = "\n".join(lines) + "\n"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(text, encoding="utf-8")
print(text)

if not overall_ok:
    raise SystemExit(1)
