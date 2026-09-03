from pathlib import Path

p = Path('.github/tools/build_v1_6_10.py')
s = p.read_text(encoding='utf-8')

# 1) Generated startup f-string quoting.
old_tp = r'EXIT_STRATEGIES[LIVE_STRATEGY][\"tp\"]'
old_sl = r'EXIT_STRATEGIES[LIVE_STRATEGY][\"sl\"]'
new_tp = r"EXIT_STRATEGIES[LIVE_STRATEGY][\'tp\']"
new_sl = r"EXIT_STRATEGIES[LIVE_STRATEGY][\'sl\']"
count_tp = s.count(old_tp)
count_sl = s.count(old_sl)
if count_tp != 1 or count_sl != 1:
    raise SystemExit(
        f'quoting hotfix targets mismatch: tp={count_tp}, sl={count_sl}'
    )
s = s.replace(old_tp, new_tp).replace(old_sl, new_sl)

# 2) Exact percentage boundaries must not miss because of binary float error.
replacements = [
    (
        'if ret >= LIVE_NOON_RECOVERY_EXIT_PCT:',
        'if ret + 1e-9 >= LIVE_NOON_RECOVERY_EXIT_PCT:',
    ),
    (
        'if not p.get("profit_protect_armed") and ret >= LIVE_PROFIT_PROTECT_ARM_PCT:',
        'if not p.get("profit_protect_armed") and ret + 1e-9 >= LIVE_PROFIT_PROTECT_ARM_PCT:',
    ),
    (
        'and ret <= LIVE_PROFIT_PROTECT_FLOOR_PCT\n',
        'and ret <= LIVE_PROFIT_PROTECT_FLOOR_PCT + 1e-9\n',
    ),
]
for old, new in replacements:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'percentage-boundary hotfix mismatch: {old!r} count={count}')
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('BUILDER_QUOTING_AND_THRESHOLD_HOTFIX_OK')
