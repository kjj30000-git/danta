from __future__ import annotations

import json
from pathlib import Path

BASE = Path('code/releases/015_260903_v1.6.9.ipynb')
TARGET = Path('code/releases/016_260904_v1.6.10.ipynb')

base = json.loads(BASE.read_text(encoding='utf-8'))
nb = json.loads(TARGET.read_text(encoding='utf-8'))

base_quick = next(c for c in base['cells'] if c.get('id') == 'v169-quick-reference')
quick = next(c for c in nb['cells'] if c.get('id') == 'v1610-quick-reference')
program = next(c for c in nb['cells'] if c.get('id') == 'v1610-program')
continuity = next(c for c in nb['cells'] if c.get('id') == 'v1610-continuity')

# 1) v1.6.9 QUICK REFERENCE 전체를 원문 그대로 승계하고 v1.6.10 변경사항만 append.
base_quick_source = list(base_quick['source'])
addendum = '''\n# ============================================================\n# v1.6.10 QUICK REFERENCE ADDENDUM — 위 v1.6.9 원문에 추가\n# ============================================================\n# 아래 내용이 v1.6.9 설명과 충돌하는 경우 v1.6.10 현재 운용값은 이 ADDENDUM을 따른다.\n# - 기본 LIVE_STRATEGY = T250_S150(+2.50/-1.50).\n# - LIVE_STRATEGY는 EXIT_STRATEGIES 169-grid의 기존 전략명 중 자유 변경 가능.\n# - 수익보호: 실제 평균매수가 대비 +1.00% 도달 후 +0.40%까지 밀리면 PROFIT_PROTECT.\n# - 정오 회복: 12:00까지 +1.00% 미도달 포지션만 +0.40% 회복 시 NOON_RECOVERY.\n# - 실제 진입시간은 MAIN 09:05:00 이상 / 09:30:00 미만(exclusive).\n# - 15:20 실제 강제청산 유지. NXT 실제보유는 하지 않고 20:00까지 가상 follow-up만 수행.\n# - 추정 왕복비용 0.23%는 성과평가용이며 실제 TP/SL/보호 트리거에는 차감하지 않음.\n# - STARTUP_CONNECTIVITY_WAIT는 시작 네트워크/DNS 장애와 실제 주문상태 불명확 SAFE HALT를 구분.\n# - 신규 정책 연구/비교 파일: paper_policy_research_v1610.csv / live_paper_comparison_v1610.csv /\n#   live_performance_v1610.csv / policy_followup_state_v1610.json.\n# - 기존 BASE/PRE_HISTORY/FIRST_75_PASS/LATER_PASS/CONFIRM/Shadow/169-grid/ENTRY_PATH/POST_EXIT는 유지.\n# ============================================================\n'''
quick['source'] = base_quick_source + addendum.splitlines(keepends=True)

# 2) v1.6.10 patch가 run_scanner() 호출 뒤에 붙은 구조를 바로잡음.
#    기존 함수/로직을 이동시키는 것이 아니라, 실행 호출 블록만 마지막으로 옮긴다.
text = ''.join(program['source'])
main_block = '''# ============================================================\n# 실행\n# ============================================================\n\nif __name__ == "__main__":\n    run_scanner()\n'''
if text.count(main_block) != 1:
    raise RuntimeError(f'expected exactly one original main block, found {text.count(main_block)}')
patch_marker = '# 39-A. v1.6.10 최소 통합 패치\n'
if patch_marker not in text:
    raise RuntimeError('v1.6.10 patch marker not found')
old_main_pos = text.index(main_block)
patch_pos = text.index(patch_marker)
print(f'BEFORE_REPAIR_MAIN_POS={old_main_pos}')
print(f'V1610_PATCH_POS={patch_pos}')
print(f'BEFORE_REPAIR_PATCH_AFTER_MAIN={patch_pos > old_main_pos}')

text = text.replace(main_block, '', 1).rstrip() + '\n\n\n' + main_block
program['source'] = text.splitlines(keepends=True)

# 3) Continuity에 이번 수정의 구조적 이유를 append-only로 기록.
cont_text = ''.join(continuity['source'])
note_marker = '# 2026-09-03 (목) v1.6.10 QUICK REFERENCE / 실행순서 후속 수정\n'
if note_marker not in cont_text:
    note = '''\n#\n# 2026-09-03 (목) v1.6.10 QUICK REFERENCE / 실행순서 후속 수정\n# - v1.6.10 최초 생성 시 v1.6.9의 상세 '변수 / 용어 QUICK REFERENCE'를 짧은 새 요약셀로 교체한 문제를 확인.\n# - v1.6.9 QUICK REFERENCE 전체를 원문 그대로 복원하고 v1.6.10 변경사항만 아래 ADDENDUM으로 누적.\n# - v1.6.10 신규 보강 코드(39-A)가 기존 if __name__ == '__main__': run_scanner() 호출 뒤에 append된 구조를 확인.\n# - 39-A 이후 코드는 v1.6.9 기존 코드의 위치 이동이 아니라 v1.6.10에서 새로 추가한 override/보강 코드다.\n# - Notebook 셀 실행 시 run_scanner()가 먼저 시작되면 뒤의 v1.6.10 override 정의가 실행되지 못할 수 있으므로 실행 호출 블록만 프로그램셀 최하단으로 이동.\n# - 기존 v1.6.9 함수/주문엔진/연구코드의 상대적 위치와 본문은 이 수정에서 변경하지 않음.\n# - 앞으로 QUICK REFERENCE와 CONTINUITY는 모두 parent 원문 전체 승계 + append-only를 원칙으로 한다.\n# ============================================================\n'''
    continuity['source'] = (cont_text.rstrip() + '\n' + note).splitlines(keepends=True)

# 4) 구조/컴파일 검증.
for c in nb['cells']:
    if c.get('cell_type') == 'code':
        compile(''.join(c.get('source', [])), c.get('id', 'cell'), 'exec')
    c['execution_count'] = None
    c['outputs'] = []

final_quick = ''.join(quick['source'])
final_program = ''.join(program['source'])
final_cont = ''.join(continuity['source'])
base_quick_text = ''.join(base_quick_source)
assert final_quick.startswith(base_quick_text)
assert '# v1.6.10 QUICK REFERENCE ADDENDUM' in final_quick
for marker in ['# [ENTRY_PATH]', '# [MFE / MAE]', '# [TP / SL / TIME_EXIT / T200_S150]', '# [v1.6.9 BUY 체결품질 필드]', '# [v1.6.8부터 유지하는 청산 지연 필드]']:
    assert marker in final_quick, marker
assert final_program.count('if __name__ == "__main__":\n    run_scanner()') == 1
assert final_program.index(patch_marker) < final_program.index('if __name__ == "__main__":\n    run_scanner()')
assert final_program.rstrip().endswith('if __name__ == "__main__":\n    run_scanner()')
assert note_marker in final_cont

TARGET.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('V1610_QUICK_REFERENCE_RESTORED_OK')
print('V1610_MAIN_CALL_MOVED_AFTER_PATCH_OK')
