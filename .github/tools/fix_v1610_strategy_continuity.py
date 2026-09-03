from __future__ import annotations

import ast
import json
import re
from pathlib import Path

BASE = Path('code/releases/015_260903_v1.6.9.ipynb')
TARGET = Path('code/releases/016_260904_v1.6.10.ipynb')


def replace_first_function(src: str, name: str, replacement: str) -> str:
    pat = rf'(?ms)^def {re.escape(name)}\([^\n]*\):\n.*?(?=^def |\Z)'
    m = re.search(pat, src)
    if not m:
        raise RuntimeError(f'function not found: {name}')
    return src[:m.start()] + replacement.rstrip() + '\n\n' + src[m.end():]


base = json.loads(BASE.read_text(encoding='utf-8'))
nb = json.loads(TARGET.read_text(encoding='utf-8'))

base_cont = next(c for c in base['cells'] if c.get('id') == 'v169-continuity')
cur_cont = next(c for c in nb['cells'] if c.get('id') == 'v1610-continuity')
settings_cell = next(c for c in nb['cells'] if c.get('id') == 'v1610-settings')
program_cell = next(c for c in nb['cells'] if c.get('id') == 'v1610-program')
quick_cell = next(c for c in nb['cells'] if c.get('id') == 'v1610-quick-reference')

settings = ''.join(settings_cell['source'])
settings = settings.replace(
    '# 실제 청산 기준: +2.50% / -1.50%\nLIVE_STRATEGY = "T250_S150"',
    '# 실제 청산 전략: 기본 T250_S150. 아래 169-grid의 기존 전략명으로 자유 변경 가능\n'
    '# 예: T200_S150 / T250_S150 / T300_S200 등. 오타/미정의 전략명만 시작 시 차단\n'
    'LIVE_STRATEGY = "T250_S150"'
)
settings_cell['source'] = settings.splitlines(keepends=True)

program = ''.join(program_cell['source'])
old_logic = '''def _logical_live_config_check():
    if LIVE_ENTRY_MODE != "FIRST_75_PASS":
        raise ValueError("LIVE_ENTRY_MODE는 FIRST_75_PASS여야 합니다.")
    if not isinstance(LIVE_MAX_STOCKS, int) or isinstance(LIVE_MAX_STOCKS, bool) or LIVE_MAX_STOCKS <= 0:
        raise ValueError("LIVE_MAX_STOCKS는 1 이상의 정수여야 합니다.")
    if not isinstance(LIVE_TRADE_AMOUNT_WON, (int, float)) or LIVE_TRADE_AMOUNT_WON <= 0:
        raise ValueError("LIVE_TRADE_AMOUNT_WON은 1원 이상이어야 합니다.")
    if not isinstance(LIVE_TOTAL_BUDGET_WON, (int, float)) or LIVE_TOTAL_BUDGET_WON <= 0:
        raise ValueError("LIVE_TOTAL_BUDGET_WON은 1원 이상이어야 합니다.")
    if LIVE_TOTAL_BUDGET_WON < LIVE_TRADE_AMOUNT_WON:
        raise ValueError("총 운용예산이 종목당 매수예산보다 작습니다.")
    if not isinstance(LIVE_DAILY_MAX_LOSS_WON, (int, float)) or LIVE_DAILY_MAX_LOSS_WON <= 0:
        raise ValueError("LIVE_DAILY_MAX_LOSS_WON은 1원 이상이어야 합니다.")
    if LIVE_MARKET_ORDER_BUFFER_PCT < 0:
        raise ValueError("LIVE_MARKET_ORDER_BUFFER_PCT는 0 이상이어야 합니다.")
    if LIVE_STRATEGY != "T250_S150":
        raise ValueError("v1.6.10 LIVE_STRATEGY는 T250_S150이어야 합니다.")
    rule = EXIT_STRATEGIES.get(LIVE_STRATEGY)
    if rule != {"tp": 2.5, "sl": -1.5}:
        raise ValueError("T250_S150 정의가 +2.50/-1.50에서 변경되었습니다.")
    if LIVE_PROFIT_PROTECT_ARM_PCT <= LIVE_PROFIT_PROTECT_FLOOR_PCT:
        raise ValueError("수익보호 arm은 floor보다 커야 합니다.")
    if LIVE_NOON_RECOVERY_EXIT_PCT < 0:
        raise ValueError("LIVE_NOON_RECOVERY_EXIT_PCT는 0 이상이어야 합니다.")
    if ESTIMATED_ROUND_TRIP_COST_PCT < 0:
        raise ValueError("ESTIMATED_ROUND_TRIP_COST_PCT는 0 이상이어야 합니다.")
    return True'''

new_logic = '''def _logical_live_config_check():
    if LIVE_ENTRY_MODE != "FIRST_75_PASS":
        raise ValueError("LIVE_ENTRY_MODE는 FIRST_75_PASS여야 합니다.")
    if not isinstance(LIVE_MAX_STOCKS, int) or isinstance(LIVE_MAX_STOCKS, bool) or LIVE_MAX_STOCKS <= 0:
        raise ValueError("LIVE_MAX_STOCKS는 1 이상의 정수여야 합니다.")
    if not isinstance(LIVE_TRADE_AMOUNT_WON, (int, float)) or LIVE_TRADE_AMOUNT_WON <= 0:
        raise ValueError("LIVE_TRADE_AMOUNT_WON은 1원 이상이어야 합니다.")
    if not isinstance(LIVE_TOTAL_BUDGET_WON, (int, float)) or LIVE_TOTAL_BUDGET_WON <= 0:
        raise ValueError("LIVE_TOTAL_BUDGET_WON은 1원 이상이어야 합니다.")
    if LIVE_TOTAL_BUDGET_WON < LIVE_TRADE_AMOUNT_WON:
        raise ValueError("총 운용예산이 종목당 매수예산보다 작습니다.")
    if not isinstance(LIVE_DAILY_MAX_LOSS_WON, (int, float)) or LIVE_DAILY_MAX_LOSS_WON <= 0:
        raise ValueError("LIVE_DAILY_MAX_LOSS_WON은 1원 이상이어야 합니다.")
    if LIVE_MARKET_ORDER_BUFFER_PCT < 0:
        raise ValueError("LIVE_MARKET_ORDER_BUFFER_PCT는 0 이상이어야 합니다.")
    rule = EXIT_STRATEGIES.get(LIVE_STRATEGY)
    if not isinstance(rule, dict) or "tp" not in rule or "sl" not in rule:
        raise ValueError(
            f"LIVE_STRATEGY={LIVE_STRATEGY!r}는 정의되지 않은 전략입니다. "
            "EXIT_STRATEGIES의 169-grid 전략명 중 하나를 사용하세요."
        )
    if not isinstance(rule["tp"], (int, float)) or not isinstance(rule["sl"], (int, float)):
        raise ValueError("선택한 LIVE_STRATEGY의 TP/SL 정의가 숫자가 아닙니다.")
    if rule["tp"] <= 0 or rule["sl"] >= 0:
        raise ValueError("선택한 LIVE_STRATEGY는 TP>0, SL<0 구조여야 합니다.")
    if LIVE_PROFIT_PROTECT_ARM_PCT <= LIVE_PROFIT_PROTECT_FLOOR_PCT:
        raise ValueError("수익보호 arm은 floor보다 커야 합니다.")
    if LIVE_NOON_RECOVERY_EXIT_PCT < 0:
        raise ValueError("LIVE_NOON_RECOVERY_EXIT_PCT는 0 이상이어야 합니다.")
    if ESTIMATED_ROUND_TRIP_COST_PCT < 0:
        raise ValueError("ESTIMATED_ROUND_TRIP_COST_PCT는 0 이상이어야 합니다.")
    return True'''

if old_logic not in program:
    raise RuntimeError('expected v1.6.10 strategy-lock logic not found')
program = program.replace(old_logic, new_logic, 1)
program = program.replace(
    '    assert LIVE_STRATEGY == "T250_S150"\n',
    '    assert LIVE_STRATEGY in EXIT_STRATEGIES\n',
    1,
)
program_cell['source'] = program.splitlines(keepends=True)

quick = ''.join(quick_cell['source'])
quick = quick.replace(
    '# TP/SL: T250_S150 = +2.50% / -1.50%\n',
    '# TP/SL 기본값: T250_S150 = +2.50% / -1.50%\n'
    '# LIVE_STRATEGY는 EXIT_STRATEGIES 169-grid 안에서 자유 변경 가능\n',
)
quick_cell['source'] = quick.splitlines(keepends=True)

# v1.6.10에서 작성된 9/3 이력은 보존하되, v1.6.9 continuity 전체 뒤에 누적한다.
cur_text = ''.join(cur_cont['source'])
marker = '# 2026-09-03 (목)\n'
pos = cur_text.find(marker)
if pos < 0:
    raise RuntimeError('current v1.6.10 continuity 2026-09-03 marker not found')
cur_tail = cur_text[pos:].rstrip() + '\n'

correction = '''#\n# 2026-09-03 (목) v1.6.10 후속 수정\n# - LIVE_STRATEGY는 T250_S150 고정잠금을 제거했다.\n# - 기본 저장값은 T250_S150이지만 EXIT_STRATEGIES의 기존 169-grid 전략명 중 하나로 자유 변경 가능하다.\n# - 존재하지 않는 전략명/오타, 비정상 TP/SL 정의만 시작 검증에서 차단한다.\n# - 실제 target_price / stop_price는 선택한 LIVE_STRATEGY의 TP/SL을 사용한다.\n# - v1.6.10 최초 생성 과정에서 v1.6.9 Continuity 셀이 새 셀로 교체되어 과거 누적 이력이 빠진 문제를 확인했다.\n# - v1.6.9의 기존 Continuity 전체를 원문 그대로 복원하고, v1.6.10 이력은 그 아래에 누적했다.\n# - 앞으로 Continuity/Decision History는 과거 이력을 삭제·요약·대체하지 않고 append-only로 유지한다.\n# ============================================================\n'''

base_text = ''.join(base_cont['source']).rstrip() + '\n\n'
cur_cont['source'] = (base_text + cur_tail + '\n' + correction).splitlines(keepends=True)

# 모든 셀 컴파일 및 구조 검증
for cell in nb['cells']:
    if cell.get('cell_type') == 'code':
        compile(''.join(cell.get('source', [])), cell.get('id', 'cell'), 'exec')
    cell['execution_count'] = None
    cell['outputs'] = []

# 변경 검증
final_program = ''.join(program_cell['source'])
assert 'LIVE_STRATEGY != "T250_S150"' not in final_program
assert 'T250_S150 정의가 +2.50/-1.50에서 변경되었습니다.' not in final_program
assert 'EXIT_STRATEGIES.get(LIVE_STRATEGY)' in final_program
final_cont = ''.join(cur_cont['source'])
for day in ['2026-08-17 (월)', '2026-08-27 (목)', '2026-08-30 (일)', '2026-09-01 (화)', '2026-09-02 (수)', '2026-09-03 (목)']:
    assert day in final_cont, day
assert len(final_cont) > len(base_text)

TARGET.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('V1610_STRATEGY_FREEDOM_OK')
print('V1610_CONTINUITY_RESTORED_OK')
