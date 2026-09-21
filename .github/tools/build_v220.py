#!/usr/bin/env python3
"""v2.1.2 전체를 보존한 재현 가능한 v2.2.0 국소 빌드."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / 'code/releases/025_260916_v2.1.2.ipynb'
TARGET = ROOT / 'code/releases/026_260922_v2.2.0.ipynb'
EXPECTED = 'f6c8e82d1b14c07169bc716aca79c2f8b0bbefeaf6596bd35e80cbdd2771ac62'
assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == EXPECTED
nb = json.loads(PARENT.read_text(encoding='utf-8'))
cells = [''.join(c['source']) for c in nb['cells']]
s = cells[1]

# 함수 설명: 중복/누락된 편집 marker를 빌드 오류로 처리합니다.
def replace(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:120], s.count(old), count)
    s = s.replace(old, new)

# 함수 설명: 한 함수 본문만 치환하고 다른 부모 정의는 건드리지 않습니다.
def transform(name, fn):
    global s
    tree = ast.parse(s)
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    lines = s.splitlines(keepends=True)
    before = ''.join(lines[node.lineno-1:node.end_lineno])
    after = fn(before)
    assert after != before, name
    s = ''.join(lines[:node.lineno-1]) + after + ''.join(lines[node.end_lineno:])

cells[0] = cells[0].replace('v2.1.2', 'v2.2.0')
for flag in ('SHADOW_SCORE_70_74_ENABLED','WIDE_HIGH_GAP_SHADOW_ENABLED','PRE_FAIL_PULLBACK_SHADOW_ENABLED',
             'CALM_FIRST_75_ENABLED','CALM_FIRST_75_PROTECT_ENABLED','ORB_DIRECT_ENABLED','ORB_RETEST_ENABLED',
             'ORB_RS_RETEST_ENABLED','OPENING_LEADER_ENABLED','OPENING_LEADER_DIRECT_ENABLED',
             'OPENING_LEADER_RETEST_ENABLED','OPENING_LEADER_RS_ENABLED'):
    assert flag + ' = True' in cells[0]
    cells[0] = cells[0].replace(flag + ' = True', flag + ' = False')
settings = '''# v2.2.0 눌림 연구 — 합의된 값, 시간대/최대깊이/거래량 추가 필터 없음
PULLBACK_SUPPORT_ENABLED = True
PULLBACK_RECLAIM_ENABLED = True
PULLBACK_RULE_VERSION = "pullback_support_v1"
PULLBACK_START_PCT = 1.50
PULLBACK_BREAK_TOLERANCE_PCT = 0.30
PULLBACK_CANDIDATE_BARS = 3
PULLBACK_CONFIRM_BARS = 5
PULLBACK_RECOVERY_PCT = 0.40
PULLBACK_RECLAIM_BARS = 5
PULLBACK_RECLAIM_BUFFER_PCT = 0.10
V220_SUMMARY_ENABLED = True
V220_SUMMARY_TIMES = ["09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30"]

'''
cells[0] = cells[0].replace('# 신규진입 중단/폐기 전략', settings + '# 신규진입 중단/폐기 전략')
replace('STRATEGY_VERSION = "v2.1.2"', 'STRATEGY_VERSION = "v2.2.0"')
replace('# 단타 자동 스크리너 v1.7.1.3', '# 단타 자동 스크리너 v2.2.0 (부모 v2.1.2 최소 통합)')
# 현재 출력은 버전별 분리. 과거 설명 및 부모 함수 이름은 보존합니다.
for node in ast.parse(s).body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        val = node.value.value
        if val.endswith(('.csv','.json','.jsonl')) and any(t in val for t in ('_v212','_v1713')):
            s = s.replace('"'+val+'"', '"'+val.replace('_v212','_v220').replace('_v1713','_v220')+'"')
module = (ROOT / '.github/tools/v220_pullback.py').read_text(encoding='utf-8')
replace('def _memory_usage_mb():', module + '\n\n# 함수 설명: 프로세스 메모리 사용량을 조회합니다.\ndef _memory_usage_mb():')
# 변경하지 않는 상수라도 첫 셀 grid 사용자 설정을 덮어쓰지 않습니다.
start=s.index('PAPER_TP_LEVELS = ['); end=s.index('# 전략명 예:', start)
s=s[:start]+'# PAPER_TP_LEVELS / PAPER_SL_LEVELS는 Cell 1 단일 설정원입니다.\n\n'+s[end:]
# 중앙 OFF gate / 169 atomicity / 후보 hook.
transform('open_paper_trade', lambda x:x.replace('    if not PAPER_TRADE_ENABLED', '    if not v220_entry_allowed(stock, entry_mode, entry_meta):\n        return None\n\n    if not PAPER_TRADE_ENABLED',1).replace('    return trade_id\n','    v220_on_legacy_entry(stock, entry_mode, trade_id, entry_meta)\n    return trade_id\n'))
transform('_validate_selected_exit_strategies',lambda x:x.replace('    return exit_strategies', '''    for name, rule in exit_strategies.items():
        if not math.isfinite(rule['tp']) or not math.isfinite(rule['sl']) or rule['tp'] <= 0 or not (-100 < rule['sl'] < 0):
            raise ValueError(f'{name}: finite TP>0 / -100<SL<0 required')
    return exit_strategies'''))
# 가격 queue snapshot에 원 거래량과 연속번호를 동봉; WS/live 우선순위는 유지합니다.
transform('handle_realtime_price',lambda x:x.replace('    if not code or price <= 0:', '    if shutdown_requested or not code or price <= 0:').replace('    snapshot=(code,price,now,(live_started-received_perf)*1000,live_ms)', '''    v220_tick_sequences[code] = v220_tick_sequences.get(code, 0) + 1
    snapshot=(code,price,now,(live_started-received_perf)*1000,live_ms,dict(values or {}),v220_tick_sequences[code])'''))
transform('_research_compute_loop',lambda x:x.replace('        code,price,now,receive_ms,live_ms=item', '        code,price,now,receive_ms,live_ms,values,sequence=item').replace('''            capture_first_ws_tick(code,price,now)
            update_policy_shadow_trackers(code,price,now)
            update_wide_snapshot_trackers(code,price,now)
            update_paper_position(code,price)
            update_entry_path_tracking(code,price,now)
            update_post_exit_tracking(code,price)''','''            with V220_LOCK:
                capture_first_ws_tick(code,price,now)
                update_policy_shadow_trackers(code,price,now)
                update_wide_snapshot_trackers(code,price,now)
                update_paper_position(code,price)
                update_entry_path_tracking(code,price,now)
                update_post_exit_tracking(code,price)
                v220_on_tick(code,price,now,values,sequence)'''))
replace('                    self.logged_in = True\n                    log(', '                    self.logged_in = True\n                    v220_mark_stream_gap()\n                    log(')
# 후보 lifecycle을 포함한 동일 연구 lock에서 구독해제를 판정합니다.
transform('maybe_release_realtime',lambda x:x.replace('        not paper_open','        not (code in v220_candidates and not shutdown_requested)\n        and not paper_open',1))
# WS 구독/해제 예약 순서를 같은 manager lock 안에서 확정합니다.
replace('        with self.lock:\n            items = list(self.desired_items.pop(code, set()))\n\n        if self.logged_in and self.loop is not None:\n            for item in items:\n                asyncio.run_coroutine_threadsafe(\n                    self._remove_item(item),\n                    self.loop\n                )', '        with self.lock:\n            if code in v220_candidates and not shutdown_requested:\n                return\n            items = list(self.desired_items.pop(code, set()))\n            if self.logged_in and self.loop is not None:\n                for item in items:\n                    asyncio.run_coroutine_threadsafe(self._remove_item(item), self.loop)')
# OFF ORB universe의 반복 REST 확대를 중단합니다.
transform('v20_prepare_orb_universe',lambda x:x.replace('    day=moment.date()', '    if not (ORB_DIRECT_ENABLED or ORB_RETEST_ENABLED or ORB_RS_RETEST_ENABLED): return\n    day=moment.date()'))
# 전략별 알림은 진입 hook과 outbox에서 독립 생성. 기존 generic 재알림은 제거.
transform('scan_market',lambda x:x.replace('''        if can_alert(stock["stock_code"]):
            send_stock_alert(stock)''','''        # v2.2.0 개별 알림은 확정 전략별 entry hook에서 생성합니다.'''))
transform('send_stock_alert', lambda x:'''def send_stock_alert(stock, strategy="BASE", entry_meta=None):
    """기존 호출 호환: 네트워크 대신 전략별 outbox에 메시지를 예약합니다."""
    with V220_LOCK:
        v220_queue_alert(stock, strategy, entry_meta or {"signal_time": _stock_score_time(stock)})
        return v220_checkpoint(True)
''')
# 모든 행의 스키마를 동일하게 확장합니다.
transform('build_strategy_result_row',lambda x:x.replace('    return row', '''    for key in V220_META_COLUMNS:
        if key not in row:
            value = position.get(key, "")
            row[key] = _csv_datetime(value) if isinstance(value, datetime) else value
    row['recovery_status'] = position.get('recovery_status', '')
    return row'''))
# 일간 rollover 앞뒤로 snapshot과 신규 원장을 정리합니다.
transform('check_new_day',lambda x:x.replace('    current_trade_date = today', '    v220_maintenance(datetime.now(), ending=True)\n    v220_candidates.clear()\n    current_trade_date = today').replace('    log("새 거래일 초기화")','    v220_reset_day(datetime.now())\n    v220_checkpoint(True)\n    log("새 거래일 초기화")'))
transform('validate_v21_opening_leader_config',lambda x:x.replace('assert STRATEGY_VERSION == "v2.1.2"','assert STRATEGY_VERSION == "v2.2.0"'))
# 설정을 worker 시작 전에 검증하고 복구를 신규 진입보다 먼저 완료합니다.
transform('run_scanner',lambda x:x.replace('    shutdown_requested = False', '''    validate_v220_config()
    validate_scanner_config()
    validate_live_trading_config()
    v220_restore()
    shutdown_requested = False''',1).replace('    subscribe_recovered_live_items()', '    subscribe_recovered_live_items()\n    v220_start()').replace('            hhmm = datetime.now().strftime("%H:%M")','            v220_maintenance(datetime.now())\n            hhmm = datetime.now().strftime("%H:%M")').replace('                shutdown_requested = True\n                force_close_all()', '                shutdown_requested = True\n                v220_quiesce()\n                v220_maintenance(datetime.now(), ending=True)\n                force_close_all()').replace('            shutdown_requested = True\n            finalize_entry_path_trackers','            shutdown_requested = True\n            v220_quiesce()\n            v220_maintenance(datetime.now(), ending=True)\n            finalize_entry_path_trackers').replace('                save_live_state()\n                flush_research_writer()', '                save_live_state()\n                v220_checkpoint(True)\n                flush_research_writer()').replace('            save_live_state()\n            flush_research_writer()', '            save_live_state()\n            v220_checkpoint(True)\n            flush_research_writer()'))
# 시작 알림의 과거 ON 표기를 실제 v2.2.0 상태로 정리합니다.
start=s.index('        "• BASE / FIRST_75_PASS / SHADOW_SCORE_70_74\\n"')
end=s.index('        f"• 연구 queue=',start)
s=s[:start]+'''        f"• BASE={BASE_RESEARCH_ENABLED} / FIRST_75_PASS={FIRST_75_RESEARCH_ENABLED}\\n"
        f"• PULLBACK_SUPPORT={PULLBACK_SUPPORT_ENABLED} / RECLAIM={PULLBACK_RECLAIM_ENABLED}\\n"
        f"• 주식 나머지 신규수집 OFF / ETF={ETF_INTRADAY_MOMENTUM_ENABLED} (기존 보존)\\n"
        f"• 눌림 -{PULLBACK_START_PCT:.2f}% / 지지 허용폭 {PULLBACK_BREAK_TOLERANCE_PCT:.2f}%\\n"
        f"• 지지 {PULLBACK_CANDIDATE_BARS}/{PULLBACK_CONFIRM_BARS}봉 / 회복 +{PULLBACK_RECOVERY_PCT:.2f}%\\n"
        f"• RECLAIM 직전 {PULLBACK_RECLAIM_BARS}봉 고점 +{PULLBACK_RECLAIM_BUFFER_PCT:.2f}% / 체결 때만 169-grid\\n"
        f"• 누적알림={V220_SUMMARY_ENABLED} / {', '.join(V220_SUMMARY_TIMES)}\\n"
'''+s[end:]
# 연구 lock은 WS/live가 아닌 연구 상태 관련 짧은 함수들만 보호합니다.
for name in ('open_paper_trade','update_paper_position','force_close_all',
             'v20_force_close_research_due','check_new_day','register_watch_if_needed',
             'close_watch_episode','register_pre_first_75_if_needed'):
    replace('def '+name+'(', '@v220_serialized\ndef '+name+'(')
# 장외 모드에서도 새 상태머신 fixture를 실행합니다 (테스트 함수는 빌드 삽입).
replay=(ROOT/'.github/tools/v220_replay.py').read_text(encoding='utf-8')
replace('# ============================================================\n# 실행\n# ============================================================',replay+'\n# ============================================================\n# 실행\n# ============================================================')
replace('        run_off_hours_validation()\n    else:', '        run_off_hours_validation()\n        run_v220_off_hours_validation()\n    else:')
# 원본문서 3/4셀은 변경하지 않고 뒤에만 추가합니다.
add='''
# 2026-09-21 (월) — v2.2.0 통합 연구 release (예정 실행일 2026-09-22)
# - 부모 025_260916_v2.1.2.ipynb 전체 보존. BASE/FIRST_75 의미/조건 유지.
# - 활성 주식 진입: BASE / FIRST_75_PASS / PULLBACK_SUPPORT_ENTRY / PULLBACK_RECLAIM_ENTRY.
# - 다른 주식 신규진입 OFF; 함수/과거호환 보존. ETF 코드/grid/정책은 보존.
# - 후보는 기존 grid 종료 후에도 당일 관찰 종료까지 유지. 별도 반복 REST 없음.
# - 완료봉: -1.50% 눌림, 0.30% 저점 허용폭, 지지3/5봉, 저점 회복 +0.40%.
# - SUPPORT 다음 봉부터 직전5봉 high +0.10% 종가 돌파가 RECLAIM.
# - 전략시간/깊이상한 없음, Higher Low/거래량은 feature only.
# - 신호 후 다음 수신 tick 체결, 새 전략별 종목당 하루1회, 체결 시에만 169-grid.
# - 후보 등록 중간봉/queue 누락/미관측 분봉은 지지로 세지 않고 DATA_UNAVAILABLE.
# - 동일봉 high/low 순서를 알 수 없으므로 신규고점 봉 다음 봉부터 눌림 평가.
# - BASE/FIRST 기존 본문 유지 + 전략명, 가상전략 안내문 삭제, 매시30분 누적목록.
# - outbox 영속 예약; 발송 응답불명확은 DELIVERY_UNKNOWN으로 기록하고 자동 재전송 금지.
# - 재시작: 신호/열린 grid/중복키 복구; 미관측 가격구간 RECOVERY_PARTIAL.
# - 신규 출력은 _v220. 비용0.24%, 기본RESEARCH, 실제/키움모의주문0건.
# - OFF_HOURS_VALIDATION_MODE=True: 기존 replay + 신규 상태/체결/알림 fixture, 외부 연결 없음.
# - 연구 검증 통과는 broker/장중 무결함 보증이 아님. 장중 데이터누락/부하를 별도 관찰.
'''
cells[1]=s;cells[2]+=add;cells[3]+=add
for c,src in zip(nb['cells'],cells):
    c['source']=src.splitlines(keepends=True);c['execution_count']=None;c['outputs']=[]
for i,src in enumerate(cells):compile(src,f'cell{i+1}','exec')
TARGET.write_text(json.dumps(nb,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
print(TARGET)
print(hashlib.sha256(TARGET.read_bytes()).hexdigest())
