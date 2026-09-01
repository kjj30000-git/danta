#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import json
import sys
import traceback
from pathlib import Path

FILES = [
    (
        "A_GITHUB",
        Path("code/releases/014_260901_v1.6.8.ipynb"),
        [
            "test_v166_core_logic",
            "test_v166_live_order_safety",
            "test_v167_order_engine_safety",
            "test_v168_manual_sell_ledger_helpers",
        ],
    ),
    (
        "B_NEWCHAT",
        Path("code/candidates/v1.6.8/014_260901_v1.6.8(새채팅).ipynb"),
        [
            "test_v166_core_logic",
            "test_v166_live_order_safety",
            "test_v167_order_engine_safety",
            "test_v168_live_ledger_and_timing",
        ],
    ),
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


lines = []
overall_ok = True
for file_idx, (label, path, tests) in enumerate(FILES, 1):
    lines.append("=" * 88)
    lines.append(f"{label}: {path}")
    lines.append("=" * 88)

    # Notebook/static checks are independent of runtime helper state.
    try:
        nb = json.loads(path.read_text(encoding="utf-8-sig"))
        assert len(nb.get("cells", [])) == 4
        assert all(c.get("cell_type") == "code" for c in nb["cells"])
        settings = src(nb["cells"][0])
        body = src(nb["cells"][1])
        continuity = src(nb["cells"][3])
        assert "AUTO_TRADE_ENABLED = False" in settings
        assert "FIRST_75_PASS" in body
        assert "T200_S150" in body
        assert "PROJECT CONTINUITY PRINCIPLE" in continuity
        lines.append("STATIC_NOTEBOOK: PASS / 4 code cells, live OFF, strategy markers, continuity marker")
    except Exception as e:
        overall_ok = False
        lines.append(f"STATIC_NOTEBOOK: FAIL / {type(e).__name__}: {e}")
        lines.append(traceback.format_exc())

    # IMPORTANT: every helper test gets a fresh module. The legacy helpers were
    # written as isolated tests and may mutate globals such as live_trade_count.
    # Reusing one module can create false failures unrelated to production code.
    for test_idx, name in enumerate(tests, 1):
        try:
            mod, _ = load_fresh_module(path, f"{file_idx}_{test_idx}")
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
lines.append("NOTE: No broker/API live orders were submitted; regression helpers only.")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

if not overall_ok:
    raise SystemExit(1)
