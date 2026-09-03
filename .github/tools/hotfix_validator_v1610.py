from pathlib import Path

p = Path('.github/tools/validate_v1_6_10.py')
s = p.read_text(encoding='utf-8')

old = '        "LIVE_ENTRY_START <= now_hhmm <= LIVE_ENTRY_END",\n'
if s.count(old) != 1:
    raise SystemExit(f'raw-time validator target mismatch: {s.count(old)}')
s = s.replace(old, '', 1)

anchor = '        "def is_live_entry_time_allowed",\n'
insert = (
    '        "def is_live_entry_time_allowed",\n'
    '        "if not is_live_entry_time_allowed(decision_time):",\n'
    '        "or not is_live_entry_time_allowed(order_check_time):",\n'
)
if s.count(anchor) != 1:
    raise SystemExit(f'entry-gate validator anchor mismatch: {s.count(anchor)}')
s = s.replace(anchor, insert, 1)

p.write_text(s, encoding='utf-8')
print('VALIDATOR_ACTIVE_ENTRY_GATE_HOTFIX_OK')
