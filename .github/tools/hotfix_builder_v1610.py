from pathlib import Path

p = Path('.github/tools/build_v1_6_10.py')
s = p.read_text(encoding='utf-8')
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
p.write_text(s, encoding='utf-8')
print('BUILDER_QUOTING_HOTFIX_OK')
