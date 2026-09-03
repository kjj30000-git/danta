from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from textwrap import dedent

BASE_NAME = "015_260903_v1.6.9.ipynb"
OUT_NAME = "016_260904_v1.6.10.ipynb"


def lines(text: str):
    return text.splitlines(keepends=True)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, got {count}")
    return text.replace(old, new, 1)


def build(base_path: Path, out_path: Path) -> None:
    nb = json.loads(base_path.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    if len(cells) != 4:
        raise RuntimeError(f"v1.6.9 exact base must have 4 cells, got {len(cells)}")
    ids = [c.get("id") for c in cells]
    if ids != ["v169-settings", "v169-program", "v169-quick-reference", "v169-continuity"]:
        raise RuntimeError(f"unexpected v1.6.9 cell ids: {ids}")

    # ------------------------------------------------------------------
    # Cell 1: user-facing settings. Five controls must be the first values.
    # ------------------------------------------------------------------
    settings = dedent(r'''
    # ============================================================
    # ★ 내일 운용 핵심 설정 — 실행 전 이 다섯 줄부터 확인
    # ============================================================
    AUTO_TRADE_ENABLED = False              # 자동매매 True/False
    LIVE_PROFIT_PROTECT_ENABLED = True      # 손익보호 True/False
    LIVE_TRADE_AMOUNT_WON = 1_000_000       # 종목당 금액
    LIVE_MAX_STOCKS = 5                     # 하루 진입 횟수
    LIVE_TOTAL_BUDGET_WON = 6_000_000       # 총 운용금액

    # 위 LIVE_MAX_STOCKS와 항상 함께 움직이는 기존 호환 alias
    LIVE_MAX_TRADES_PER_DAY = LIVE_MAX_STOCKS
    LIVE_MAX_CONCURRENT_POSITIONS = LIVE_MAX_STOCKS

    # ============================================================
    # ★ 나머지 실제매매 설정
    # ============================================================
    # False = 실계좌 API / True = 키움 모의투자 API
    USE_MOCK = False

    # 실제 진입군은 기존과 동일: PRE_HISTORY의 최초 75점 통과(PASS)만
    LIVE_ENTRY_MODE = "FIRST_75_PASS"
    LIVE_ENTRY_START = "09:05"
    LIVE_ENTRY_END = "09:30"   # v1.6.10은 09:30:00 미만(exclusive)으로 판정
    LIVE_ALLOWED_SESSIONS = {"MAIN"}

    # 실제 청산 기준: +2.50% / -1.50%
    LIVE_STRATEGY = "T250_S150"

    # 수익보호: 실제 평균매수가 대비 +1.00% 한 번 도달 후 +0.40%까지 밀리면 청산
    LIVE_PROFIT_PROTECT_ARM_PCT = 1.00
    LIVE_PROFIT_PROTECT_FLOOR_PCT = 0.40

    # 정오 회복청산: 12:00까지 +1.00% 미도달 종목만 +0.40% 회복 시 청산
    LIVE_NOON_RECOVERY_ENABLED = True
    LIVE_NOON_RECOVERY_TIME = "12:00"
    LIVE_NOON_RECOVERY_EXIT_PCT = 0.40

    # 장중 실제 강제청산 — NXT 실제보유는 v1.6.10에서 하지 않음
    LIVE_FORCE_EXIT_ENABLED = True
    LIVE_FORCE_EXIT_TIME = "15:20"
    LIVE_FORCE_EXIT_RETRY_SEC = 15

    # 시장가 체결 상승을 고려한 수량계산 여유율 (%)
    LIVE_MARKET_ORDER_BUFFER_PCT = 1.0

    # 하루 실제 손실 한도
    LIVE_DAILY_MAX_LOSS_WON = 100_000

    # 성과표용 추정 왕복 제비용. 실제 TP/SL/보호청산 트리거에는 차감하지 않음.
    ESTIMATED_ROUND_TRIP_COST_PCT = 0.23

    # 정규장 실제 주문 거래소 / 주문유형(3=시장가)
    LIVE_MAIN_EXCHANGE = "SOR"
    LIVE_ORDER_TYPE = "3"
    ''').lstrip()
    cells[0]["id"] = "v1610-settings"
    cells[0]["source"] = lines(settings)

    # ------------------------------------------------------------------
    # Cell 2: preserve exact v1.6.9 program, then apply local patches and
    # append v1.6.10 helpers/overrides. Existing order safety code stays.
    # ------------------------------------------------------------------
    program = "".join(cells[1].get("source", []))
    program = replace_once(program, "# 단타 자동 스크리너 v1.6.9", "# 단타 자동 스크리너 v1.6.10", "program title")
    program = replace_once(program, 'STRATEGY_VERSION = "v1.6.9"', 'STRATEGY_VERSION = "v1.6.10"', "strategy version")

    file_replacements = {
        'SIGNAL_LOG_FILE = "scanner_signals_v169.csv"': 'SIGNAL_LOG_FILE = "scanner_signals_v1610.csv"',
        'PAPER_TRADE_FILE = "paper_trades_v169.csv"': 'PAPER_TRADE_FILE = "paper_trades_v1610.csv"',
        'PAPER_ENTRY_DECISION_FILE = "paper_entry_decisions_v169.csv"': 'PAPER_ENTRY_DECISION_FILE = "paper_entry_decisions_v1610.csv"',
        'POST_EXIT_FILE = "paper_post_exit_v169.csv"': 'POST_EXIT_FILE = "paper_post_exit_v1610.csv"',
        'ENTRY_PATH_FILE = "paper_entry_path_v169.csv"': 'ENTRY_PATH_FILE = "paper_entry_path_v1610.csv"',
        'SYSTEM_LOG_FILE = "scanner_system_v169.csv"': 'SYSTEM_LOG_FILE = "scanner_system_v1610.csv"',
        'LIVE_TRADE_FILE = "live_trades_v169.csv"': 'LIVE_TRADE_FILE = "live_trades_v1610.csv"',
        'LIVE_ORDER_FILE = "live_orders_v169.csv"': 'LIVE_ORDER_FILE = "live_orders_v1610.csv"',
        'LIVE_STATE_FILE = "live_state_v169.json"': 'LIVE_STATE_FILE = "live_state_v1610.json"',
    }
    for old, new in file_replacements.items():
        program = replace_once(program, old, new, old)

    program = replace_once(
        program,
        'POST_EXIT_REFERENCE_STRATEGY = "T200_S150"',
        'POST_EXIT_REFERENCE_STRATEGY = "T250_S150"',
        "post-exit reference strategy",
    )
    program = program.replace('"paper_T200_S150_result"', '"paper_T250_S150_result"')
    program = program.replace('"paper_T200_S150_return_pct"', '"paper_T250_S150_return_pct"')
    program = program.replace('종목당 300만원 예산으로 1주 미만', '현재 종목당 예산으로 1주 미만')

    # 09:30:00 exclusive, both at decision gate and immediately before BUY submit.
    program = replace_once(
        program,
        '    now_hhmm = decision_time.strftime("%H:%M")\n'
        '    if not (LIVE_ENTRY_START <= now_hhmm <= LIVE_ENTRY_END):\n'
        '        return False, "실제진입 허용시간 밖"\n',
        '    if not is_live_entry_time_allowed(decision_time):\n'
        '        return False, "실제진입 허용시간 밖(종료시각 미포함)"\n',
        "decision-time exclusive boundary",
    )
    program = replace_once(
        program,
        '    order_check_time = datetime.now()\n'
        '    order_session = get_session_at(order_check_time)\n'
        '    order_hhmm = order_check_time.strftime("%H:%M")\n'
        '    if order_session not in LIVE_ALLOWED_SESSIONS or not (LIVE_ENTRY_START <= order_hhmm <= LIVE_ENTRY_END):\n'
        '        log(f"[실전진입 SKIP] {stock_name} / 주문 직전 실제 시간이 허용구간 밖")\n'
        '        return False\n',
        '    order_check_time = datetime.now()\n'
        '    order_session = get_session_at(order_check_time)\n'
        '    if order_session not in LIVE_ALLOWED_SESSIONS or not is_live_entry_time_allowed(order_check_time):\n'
        '        log(f"[실전진입 SKIP] {stock_name} / 주문 직전 실제 시간이 허용구간 밖(09:30:00 미만)")\n'
        '        return False\n',
        "pre-submit exclusive boundary",
    )

    # Startup quick-reference hook; function is defined by the appended block.
    program = replace_once(
        program,
        '    validate_scanner_config()\n'
        '    validate_live_trading_config()\n'
        '    get_kiwoom_token()\n',
        '    validate_scanner_config()\n'
        '    validate_live_trading_config()\n'
        '    emit_v1610_startup_reference()\n'
        '    get_kiwoom_token()\n',
        "run_scanner startup reference",
    )

    # REST fallback must also keep policy-followup-only codes alive.
    monitor_anchor = '        codes.update(post_exit_ids_by_code.keys())\n'
    if monitor_anchor not in program:
        raise RuntimeError("monitor_open_positions anchor missing")
    program = program.replace(
        monitor_anchor,
        monitor_anchor + '        codes.update(policy_followup_ids_by_code.keys())\n',
        1,
    )

    # Dynamic startup descriptions: remove misleading fixed 300/1800/T200 text.
    program = program.replace('log("TP/SL = +2.00% / -1.50%")', 'log(f"TP/SL = +{EXIT_STRATEGIES[LIVE_STRATEGY][\"tp\"]:.2f}% / {EXIT_STRATEGIES[LIVE_STRATEGY][\"sl\"]:.2f}%")')
    program = program.replace(
        'log("v1.6.9 = v1.6.8 안전장치 유지 / 300만원 / BUY계측 / 신규 Shadow 2종")',
        'log(f"v1.6.10 = v1.6.9 안전장치 유지 / 종목당 {LIVE_TRADE_AMOUNT_WON:,.0f}원 / 보호청산·정오회복 추가")',
    )

    appended = dedent(r'''

    # ============================================================
    # 39-A. v1.6.10 최소 통합 패치
    # - v1.6.9 주문/체결/broker precheck/live_state/연구 체계를 보존합니다.
    # - 아래 함수는 기존 함수를 필요한 부분만 감싸거나 override합니다.
    # ============================================================

    from datetime import time as dt_time

    LIVE_POLICY_RESEARCH_FILE = "paper_policy_research_v1610.csv"
    LIVE_PAPER_COMPARISON_FILE = "live_paper_comparison_v1610.csv"
    LIVE_PERFORMANCE_FILE = "live_performance_v1610.csv"
    POLICY_FOLLOWUP_STATE_FILE = "policy_followup_state_v1610.json"

    PROFIT_PROTECT_RESEARCH_ARMS = [0.75, 1.00, 1.25, 1.50]
    PROFIT_PROTECT_RESEARCH_FLOOR_PCT = 0.40
    STARTUP_BROKER_RETRY_COUNT = 3
    STARTUP_BROKER_RETRY_BACKOFF_SEC = [1.0, 2.0, 4.0]
    STARTUP_CONNECTIVITY_RECHECK_SEC = 30

    LIVE_REASON_KO.update({
        "PROFIT_PROTECT": "수익보호",
        "NOON_RECOVERY": "정오 회복청산",
        "STARTUP_CONNECTIVITY_WAIT": "시작 네트워크 연결 대기",
    })

    POLICY_FOLLOWUP_LOCK = threading.RLock()
    policy_followups = {}
    policy_followup_ids_by_code = {}
    startup_connectivity_wait = False
    startup_connectivity_last_error = ""
    startup_connectivity_last_check_ts = 0.0


    def _parse_hhmm(value):
        hh, mm = str(value).split(":", 1)
        return dt_time(int(hh), int(mm), 0)


    def is_live_entry_time_allowed(decision_time=None):
        """09:05:00 이상 / 09:30:00 미만. 종료시각은 exclusive입니다."""
        if decision_time is None:
            decision_time = datetime.now()
        if not isinstance(decision_time, datetime):
            return False
        t = decision_time.time()
        return _parse_hhmm(LIVE_ENTRY_START) <= t < _parse_hhmm(LIVE_ENTRY_END)


    def _logical_live_config_check():
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
        return True


    def validate_live_trading_config():
        """v1.6.10: exact-value lock 제거, 논리/안전 관계만 검증."""
        return _logical_live_config_check()


    def emit_v1610_startup_reference():
        rule = EXIT_STRATEGIES[LIVE_STRATEGY]
        lines_ = [
            "===== v1.6.10 QUICK REFERENCE =====",
            f"AUTO_TRADE_ENABLED = {AUTO_TRADE_ENABLED}",
            f"LIVE_PROFIT_PROTECT_ENABLED = {LIVE_PROFIT_PROTECT_ENABLED}",
            f"LIVE_NOON_RECOVERY_ENABLED = {LIVE_NOON_RECOVERY_ENABLED}",
            f"LIVE ENTRY = {LIVE_ENTRY_MODE}",
            f"진입시간 = MAIN {LIVE_ENTRY_START}:00 이상 / {LIVE_ENTRY_END}:00 미만",
            f"종목당 금액 = {LIVE_TRADE_AMOUNT_WON:,.0f}원",
            f"하루 최대 횟수 = {LIVE_MAX_STOCKS}회",
            f"총 운용금액 = {LIVE_TOTAL_BUDGET_WON:,.0f}원",
            f"일손실한도 = {LIVE_DAILY_MAX_LOSS_WON:,.0f}원",
            f"TP/SL = +{rule['tp']:.2f}% / {rule['sl']:.2f}%",
            f"수익보호 = +{LIVE_PROFIT_PROTECT_ARM_PCT:.2f}% 도달 후 +{LIVE_PROFIT_PROTECT_FLOOR_PCT:.2f}% floor",
            f"12시 회복청산 = 미armed 종목 +{LIVE_NOON_RECOVERY_EXIT_PCT:.2f}% 회복 시",
            f"추정 왕복비용 = {ESTIMATED_ROUND_TRIP_COST_PCT:.2f}%",
            f"{LIVE_FORCE_EXIT_TIME} 실제 강제청산 / NXT 가상추적만",
        ]
        for item in lines_:
            log(item)
        # Telegram 실패는 기존 send_telegram 정책대로 상태전이에 영향을 주지 않습니다.
        send_telegram("\n".join(lines_))


    def _ensure_v1610_position_fields(p):
        if not isinstance(p, dict):
            return p
        p.setdefault("max_return_pct", -999.0)
        p.setdefault("min_return_pct", 999.0)
        p.setdefault("profit_protect_armed", False)
        p.setdefault("profit_protect_armed_time", "")
        p.setdefault("profit_protect_armed_price", "")
        p.setdefault("profit_protect_floor_pct", LIVE_PROFIT_PROTECT_FLOOR_PCT)
        p.setdefault("profit_protect_trigger_time", "")
        p.setdefault("profit_protect_trigger_price", "")
        p.setdefault("profit_protect_trigger_return_pct", "")
        p.setdefault("noon_recovery_eligible", False)
        p.setdefault("noon_recovery_waiting", False)
        p.setdefault("noon_evaluated_time", "")
        p.setdefault("noon_return_pct", "")
        p.setdefault("noon_mfe_pct", "")
        p.setdefault("noon_recovery_trigger_time", "")
        p.setdefault("noon_recovery_trigger_price", "")
        p.setdefault("noon_recovery_trigger_return_pct", "")
        return p


    _v169_normalize_live_position_state = _normalize_live_position_state
    def _normalize_live_position_state(position):
        p = _v169_normalize_live_position_state(position)
        return _ensure_v1610_position_fields(p)


    def _current_gross_return_pct(p, current_price):
        avg = safe_float(p.get("avg_entry_price", 0))
        if avg <= 0 or current_price <= 0:
            return None
        return (current_price / avg - 1.0) * 100.0


    def _evaluate_v1610_live_exit_state(p, current_price, observed_time=None):
        """순수 상태판정. 주문 제출은 호출자가 담당합니다."""
        if observed_time is None:
            observed_time = datetime.now()
        _ensure_v1610_position_fields(p)
        ret = _current_gross_return_pct(p, current_price)
        if ret is None:
            return None, False, None

        previous_max = safe_float(p.get("max_return_pct", -999.0), -999.0)
        p["max_return_pct"] = max(previous_max, ret)
        p["min_return_pct"] = min(safe_float(p.get("min_return_pct", 999.0), 999.0), ret)
        changed = False

        target = safe_float(p.get("target_price", float("inf")))
        stop = safe_float(p.get("stop_price", 0))

        # 우선순위: TP -> SL -> 이미 확정된 NOON wait -> 수익보호.
        if current_price >= target:
            return "TAKE_PROFIT", changed, ret
        if current_price <= stop:
            return "STOP_LOSS", changed, ret

        noon_time = _parse_hhmm(LIVE_NOON_RECOVERY_TIME)
        if LIVE_NOON_RECOVERY_ENABLED and not p.get("noon_evaluated_time") and observed_time.time() >= noon_time:
            p["noon_evaluated_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            p["noon_return_pct"] = ret
            p["noon_mfe_pct"] = previous_max
            # 첫 12시 이후 tick 자체가 +1%로 점프해도, 정오 이전 MFE로 대상을 확정합니다.
            if (not p.get("profit_protect_armed")) and previous_max < LIVE_PROFIT_PROTECT_ARM_PCT:
                p["noon_recovery_eligible"] = True
                p["noon_recovery_waiting"] = True
            changed = True

        if p.get("noon_recovery_waiting"):
            if ret >= LIVE_NOON_RECOVERY_EXIT_PCT:
                p["noon_recovery_waiting"] = False
                p["noon_recovery_trigger_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                p["noon_recovery_trigger_price"] = current_price
                p["noon_recovery_trigger_return_pct"] = ret
                return "NOON_RECOVERY", True, ret
            # 정오에 약한 포지션으로 확정되면 오후 +1% 도달로 protect 모드로 재분류하지 않습니다.
            return None, changed, ret

        if not p.get("profit_protect_armed") and ret >= LIVE_PROFIT_PROTECT_ARM_PCT:
            p["profit_protect_armed"] = True
            p["profit_protect_armed_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            p["profit_protect_armed_price"] = current_price
            p["profit_protect_floor_pct"] = LIVE_PROFIT_PROTECT_FLOOR_PCT
            changed = True

        if (
            LIVE_PROFIT_PROTECT_ENABLED
            and p.get("profit_protect_armed")
            and ret <= LIVE_PROFIT_PROTECT_FLOOR_PCT
        ):
            p["profit_protect_trigger_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            p["profit_protect_trigger_price"] = current_price
            p["profit_protect_trigger_return_pct"] = ret
            return "PROFIT_PROTECT", True, ret

        return None, changed, ret


    def update_live_position_on_price(code, current_price):
        code = clean_stock_code(code)
        observed_time = datetime.now()
        with STATE_LOCK:
            p = live_positions.get(code)
            if not p:
                return
            if p.get("status") not in ["OPEN", "POSITION_MISMATCH"]:
                return
            if safe_int(p.get("auto_managed_qty", p.get("qty", 0))) <= 0:
                return
            p["last_price"] = current_price
            reason, changed, ret = _evaluate_v1610_live_exit_state(p, current_price, observed_time)
            entry_complete = bool(p.get("entry_complete", False))
            stock_name = p.get("stock_name", code)

        if changed:
            save_live_state()

        if reason is None:
            return

        if reason == "PROFIT_PROTECT":
            log(f"[수익보호 TRIGGER] {stock_name} ({code}) / {ret:+.3f}%")
        elif reason == "NOON_RECOVERY":
            log(f"[정오 회복청산 TRIGGER] {stock_name} ({code}) / {ret:+.3f}%")

        if entry_complete:
            submit_live_exit(code, reason, trigger_price=current_price)
        else:
            request_entry_cancel_for_exit(code, reason)


    _v169_handle_order_execution = handle_order_execution
    def handle_order_execution(values):
        _v169_handle_order_execution(values)
        if not isinstance(values, dict):
            return
        code = clean_stock_code(values.get("9001", ""))
        if not code:
            return
        changed = False
        with STATE_LOCK:
            p = live_positions.get(code)
            if p:
                _ensure_v1610_position_fields(p)
                changed = True
        if changed and AUTO_TRADE_ENABLED:
            save_live_state()
        _sync_live_followup_from_position(code)


    def _startup_retry(callable_, label):
        last = None
        for i in range(STARTUP_BROKER_RETRY_COUNT):
            try:
                return callable_()
            except Exception as e:
                last = e
                log(f"[STARTUP RETRY] {label} {i+1}/{STARTUP_BROKER_RETRY_COUNT} / {type(e).__name__}: {e}")
                if i + 1 < STARTUP_BROKER_RETRY_COUNT:
                    delay = STARTUP_BROKER_RETRY_BACKOFF_SEC[min(i, len(STARTUP_BROKER_RETRY_BACKOFF_SEC)-1)]
                    time.sleep(delay)
        raise last


    def _set_startup_connectivity_wait(error):
        global startup_connectivity_wait, startup_connectivity_last_error, startup_connectivity_last_check_ts
        startup_connectivity_wait = True
        startup_connectivity_last_error = f"{type(error).__name__}: {error}"
        startup_connectivity_last_check_ts = time.time()
        log(f"[STARTUP_CONNECTIVITY_WAIT] {startup_connectivity_last_error}")
        send_telegram(
            "⚠️ 시작 네트워크 연결 대기\n"
            f"{startup_connectivity_last_error}\n"
            "broker 계좌·보유·미체결 확인 전 신규 실제주문은 열지 않습니다.\n"
            "실제 주문상태 불명확(ORDER_STATUS_UNKNOWN)과는 별도로 처리합니다."
        )


    def _clear_startup_connectivity_wait():
        global startup_connectivity_wait, startup_connectivity_last_error
        if startup_connectivity_wait:
            log("[STARTUP_CONNECTIVITY_WAIT 해제] broker 상태 정상 확인")
        startup_connectivity_wait = False
        startup_connectivity_last_error = ""


    def initialize_broker_account_snapshot():
        global broker_startup_holdings
        if not AUTO_TRADE_ENABLED:
            return True
        try:
            def fetch_positions():
                with BROKER_SYNC_LOCK:
                    positions = get_broker_positions()
                    _update_broker_balance_cache(positions)
                    return positions
            positions = _startup_retry(fetch_positions, "positions")
            with STATE_LOCK:
                broker_startup_holdings = set(positions.keys()) - set(live_positions.keys())
            _clear_startup_connectivity_wait()
            log(f"broker 시작 잔고 확인 / 기존보유 {len(broker_startup_holdings)}종목")
            save_live_state()
            return True
        except Exception as e:
            _set_startup_connectivity_wait(e)
            return False


    def reconcile_live_state_with_broker():
        """v1.6.10: connectivity 실패는 비영속 WAIT, 실제 주문 불명확은 기존 SAFE HALT."""
        global live_recovery_mode, live_trading_halted, live_system_halt_reason, broker_startup_holdings
        if not AUTO_TRADE_ENABLED:
            return True
        try:
            def fetch_all():
                with BROKER_SYNC_LOCK:
                    positions = get_broker_positions()
                    pending = get_broker_pending_orders()
                    _update_broker_balance_cache(positions)
                    return positions, pending
            positions, pending = _startup_retry(fetch_all, "positions+pending")
        except Exception as e:
            _set_startup_connectivity_wait(e)
            return False

        _clear_startup_connectivity_wait()
        ambiguous = []
        with STATE_LOCK:
            broker_startup_holdings = set(positions.keys()) - set(live_positions.keys())

        for code in list(live_positions.keys()):
            balance = positions.get(code, {
                "stock_code": code, "held_qty": 0, "sellable_qty": 0, "avg_price": 0,
            })
            _sync_position_from_broker(code, balance, source="STARTUP_RECONCILE", external_event=True)

        with STATE_LOCK:
            for ord_no, order in live_orders.items():
                if order.get("status") not in ["SUBMITTED", "PARTIAL", "CANCEL_PENDING", "ORDER_STATUS_UNKNOWN"]:
                    continue
                if order.get("side") == "CANCEL":
                    continue
                if ord_no not in pending:
                    order["status"] = "ORDER_STATUS_UNKNOWN"
                    ambiguous.append(
                        f"{stock_display_name(order.get('stock_code',''), order.get('stock_name',''))} "
                        f"({clean_stock_code(order.get('stock_code',''))}) / 주문 {ord_no} 상태 불명확"
                    )

            if ambiguous:
                live_recovery_mode = True
                live_trading_halted = True
                live_system_halt_reason = "ORDER_STATUS_UNKNOWN"
            else:
                live_recovery_mode = False
                # broker snapshot이 완전하고 미해결 주문도 없을 때만 과거 startup성 ORDER_STATUS_UNKNOWN 해제.
                if live_system_halt_reason in ["", "이전 거래일 미해결 실전상태", "ORDER_STATUS_UNKNOWN", "STARTUP_CONNECTIVITY_WAIT"]:
                    live_trading_halted = False
                    live_system_halt_reason = ""

        save_live_state()
        if ambiguous:
            send_telegram(
                "🚨 주문상태 확인불가 / 실제매매 SAFE HALT\n"
                + "\n".join(ambiguous[:10])
                + "\n신규 실제주문은 중단하고 가상연구는 계속합니다."
            )
            return False
        log("실전상태와 broker 계좌 상태 동기화 완료")
        return True


    _v169_can_open_live_trade = can_open_live_trade
    def can_open_live_trade(stock, entry_mode="", pre_entry_type="", decision_time=None):
        global startup_connectivity_last_check_ts
        if AUTO_TRADE_ENABLED and startup_connectivity_wait:
            if time.time() - startup_connectivity_last_check_ts >= STARTUP_CONNECTIVITY_RECHECK_SEC:
                startup_connectivity_last_check_ts = time.time()
                reconcile_live_state_with_broker()
            if startup_connectivity_wait:
                return False, "STARTUP_CONNECTIVITY_WAIT / broker 확인 전 신규주문 차단"
        return _v169_can_open_live_trade(
            stock, entry_mode=entry_mode, pre_entry_type=pre_entry_type, decision_time=decision_time
        )


    def _atomic_json_write(path, payload):
        tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)


    def _reindex_policy_followups():
        global policy_followup_ids_by_code
        idx = {}
        for fid, item in policy_followups.items():
            if item.get("finalized"):
                continue
            code = clean_stock_code(item.get("stock_code", ""))
            if code:
                idx.setdefault(code, set()).add(fid)
        policy_followup_ids_by_code = idx


    def save_policy_followup_state():
        with POLICY_FOLLOWUP_LOCK:
            payload = {"version": STRATEGY_VERSION, "items": policy_followups}
            _atomic_json_write(POLICY_FOLLOWUP_STATE_FILE, payload)


    def load_policy_followup_state():
        global policy_followups
        if not os.path.exists(POLICY_FOLLOWUP_STATE_FILE):
            policy_followups = {}
            _reindex_policy_followups()
            return True
        try:
            with open(POLICY_FOLLOWUP_STATE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            items = payload.get("items", {}) if isinstance(payload, dict) else {}
            policy_followups = items if isinstance(items, dict) else {}
            _reindex_policy_followups()
            return True
        except Exception as e:
            log(f"[policy followup state load 오류] {e}")
            policy_followups = {}
            _reindex_policy_followups()
            return False


    def _policy_followup_id(p):
        paper_id = str(p.get("paper_trade_id", "")).strip()
        if paper_id:
            return paper_id
        order_no = str(p.get("entry_order_no", "")).strip()
        if order_no:
            return f"LIVE:{order_no}"
        return ""


    def _ensure_policy_followup_from_paper(p):
        if not isinstance(p, dict):
            return ""
        if p.get("entry_mode") != "PRE_HISTORY" or p.get("pre_entry_type") != "FIRST_75_PASS":
            return ""
        fid = str(p.get("trade_id", p.get("paper_trade_id", ""))).strip()
        if not fid:
            return ""
        with POLICY_FOLLOWUP_LOCK:
            item = policy_followups.get(fid)
            if item is None:
                entry_price = safe_float(p.get("entry_price", 0))
                item = {
                    "followup_id": fid,
                    "paper_trade_id": fid,
                    "stock_code": clean_stock_code(p.get("stock_code", "")),
                    "stock_name": p.get("stock_name", ""),
                    "entry_price": entry_price,
                    "entry_price_source": "PAPER",
                    "entry_time": _csv_datetime(p.get("entry_time", "")),
                    "entry_order_no": "",
                    "max_return_pct": -999.0,
                    "min_return_pct": 999.0,
                    "original_result": "OPEN",
                    "original_exit_time": "",
                    "original_exit_price": "",
                    "original_return_pct": "",
                    "profit_variants": {},
                    "noon_evaluated": False,
                    "noon_waiting": False,
                    "noon_triggered": False,
                    "noon_trigger_time": "",
                    "noon_trigger_price": "",
                    "noon_trigger_return_pct": "",
                    "live_exit_reason": "",
                    "live_exit_time": "",
                    "live_exit_price": "",
                    "live_exit_return_pct": "",
                    "snapshot_1520_return_pct": "",
                    "snapshot_2000_return_pct": "",
                    "post_live_max_return_pct": "",
                    "post_live_min_return_pct": "",
                    "finalized": False,
                }
                policy_followups[fid] = item
                policy_followup_ids_by_code.setdefault(item["stock_code"], set()).add(fid)
        return fid


    def _sync_live_followup_from_position(code):
        code = clean_stock_code(code)
        with STATE_LOCK:
            p = live_positions.get(code)
            if not p:
                return
            p_copy = dict(p)
        fid = _policy_followup_id(p_copy)
        if not fid:
            return
        with POLICY_FOLLOWUP_LOCK:
            item = policy_followups.get(fid)
            if item is None:
                item = {
                    "followup_id": fid,
                    "paper_trade_id": str(p_copy.get("paper_trade_id", "")),
                    "stock_code": code,
                    "stock_name": p_copy.get("stock_name", code),
                    "profit_variants": {},
                    "finalized": False,
                }
                policy_followups[fid] = item
            avg = safe_float(p_copy.get("avg_entry_price", 0))
            if avg > 0:
                item["entry_price"] = avg
                item["entry_price_source"] = "BROKER_ACTUAL"
            item["entry_order_no"] = p_copy.get("entry_order_no", "")
            item.setdefault("entry_time", _csv_datetime(p_copy.get("entry_time", "")))
            item.setdefault("max_return_pct", -999.0)
            item.setdefault("min_return_pct", 999.0)
            item.setdefault("original_result", "OPEN")
            item.setdefault("original_exit_time", "")
            item.setdefault("original_exit_price", "")
            item.setdefault("original_return_pct", "")
            item.setdefault("noon_evaluated", False)
            item.setdefault("noon_waiting", False)
            item.setdefault("noon_triggered", False)
            item.setdefault("live_exit_reason", "")
            item.setdefault("snapshot_1520_return_pct", "")
            item.setdefault("snapshot_2000_return_pct", "")
            item.setdefault("post_live_max_return_pct", "")
            item.setdefault("post_live_min_return_pct", "")
            policy_followup_ids_by_code.setdefault(code, set()).add(fid)
        save_policy_followup_state()


    def _append_policy_event(item, event, extra=None):
        row = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "version": STRATEGY_VERSION,
            "followup_id": item.get("followup_id", ""),
            "paper_trade_id": item.get("paper_trade_id", ""),
            "stock_code": item.get("stock_code", ""),
            "stock_name": item.get("stock_name", ""),
            "entry_price": item.get("entry_price", ""),
            "entry_price_source": item.get("entry_price_source", ""),
            "event": event,
        }
        if extra:
            row.update(extra)
        pd.DataFrame([row]).to_csv(
            LIVE_POLICY_RESEARCH_FILE,
            mode="a",
            header=not os.path.exists(LIVE_POLICY_RESEARCH_FILE),
            index=False,
            encoding="utf-8-sig",
        )


    def _append_live_paper_comparison(item, event="UPDATE"):
        live_ret = item.get("live_exit_return_pct", "")
        original_ret = item.get("original_return_pct", "")
        diff = ""
        if isinstance(live_ret, (int, float)) and isinstance(original_ret, (int, float)):
            diff = original_ret - live_ret
        row = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "version": STRATEGY_VERSION,
            "event": event,
            "followup_id": item.get("followup_id", ""),
            "paper_trade_id": item.get("paper_trade_id", ""),
            "entry_order_no": item.get("entry_order_no", ""),
            "stock_code": item.get("stock_code", ""),
            "stock_name": item.get("stock_name", ""),
            "live_exit_reason": item.get("live_exit_reason", ""),
            "live_exit_return_pct": live_ret,
            "paper_T250_S150_result": item.get("original_result", "OPEN"),
            "paper_T250_S150_return_pct": original_ret,
            "paper_T250_S150_exit_time": item.get("original_exit_time", ""),
            "return_difference_pct": diff,
            "snapshot_1520_return_pct": item.get("snapshot_1520_return_pct", ""),
            "snapshot_2000_return_pct": item.get("snapshot_2000_return_pct", ""),
            "post_live_max_return_pct": item.get("post_live_max_return_pct", ""),
            "post_live_min_return_pct": item.get("post_live_min_return_pct", ""),
        }
        pd.DataFrame([row]).to_csv(
            LIVE_PAPER_COMPARISON_FILE,
            mode="a",
            header=not os.path.exists(LIVE_PAPER_COMPARISON_FILE),
            index=False,
            encoding="utf-8-sig",
        )


    def _update_policy_followups_for_code(code, price, observed_time=None):
        code = clean_stock_code(code)
        if price <= 0:
            return
        if observed_time is None:
            observed_time = datetime.now()
        ids = list(policy_followup_ids_by_code.get(code, set()))
        if not ids:
            return
        changed = False
        finalized_ids = []

        with POLICY_FOLLOWUP_LOCK:
            for fid in ids:
                item = policy_followups.get(fid)
                if not item or item.get("finalized"):
                    continue
                entry = safe_float(item.get("entry_price", 0))
                if entry <= 0:
                    continue
                ret = (price / entry - 1.0) * 100.0
                previous_max = safe_float(item.get("max_return_pct", -999.0), -999.0)
                item["max_return_pct"] = max(previous_max, ret)
                item["min_return_pct"] = min(safe_float(item.get("min_return_pct", 999.0), 999.0), ret)
                item["last_price"] = price
                item["last_return_pct"] = ret
                changed = True

                # 원래 실전 기준 T250_S150 반사실 경로.
                if item.get("original_result", "OPEN") == "OPEN":
                    if ret >= 2.50:
                        item["original_result"] = "TAKE_PROFIT"
                    elif ret <= -1.50:
                        item["original_result"] = "STOP_LOSS"
                    if item.get("original_result") != "OPEN":
                        item["original_exit_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        item["original_exit_price"] = price
                        item["original_return_pct"] = ret
                        _append_policy_event(item, "ORIGINAL_T250_S150_EXIT", {
                            "result": item["original_result"], "return_pct": ret, "price": price,
                        })
                        if item.get("live_exit_reason"):
                            _append_live_paper_comparison(item, "ORIGINAL_FINAL")

                # 보호 activation 0.75/1.00/1.25/1.50 동시 반사실 연구.
                variants = item.setdefault("profit_variants", {})
                for arm in PROFIT_PROTECT_RESEARCH_ARMS:
                    key = f"ARM_{arm:.2f}_FLOOR_{PROFIT_PROTECT_RESEARCH_FLOOR_PCT:.2f}"
                    v = variants.setdefault(key, {"armed": False, "triggered": False})
                    if not v.get("armed") and ret >= arm:
                        v["armed"] = True
                        v["armed_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        v["armed_price"] = price
                    if v.get("armed") and not v.get("triggered") and ret <= PROFIT_PROTECT_RESEARCH_FLOOR_PCT:
                        v["triggered"] = True
                        v["trigger_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        v["trigger_price"] = price
                        v["trigger_return_pct"] = ret
                        _append_policy_event(item, "PROFIT_PROTECT_CF", {
                            "research_id": key, "arm_pct": arm,
                            "floor_pct": PROFIT_PROTECT_RESEARCH_FLOOR_PCT,
                            "return_pct": ret, "price": price,
                        })

                # 정오 회복 반사실. 정오 이전 max로 대상 여부를 확정.
                if not item.get("noon_evaluated") and observed_time.time() >= _parse_hhmm(LIVE_NOON_RECOVERY_TIME):
                    item["noon_evaluated"] = True
                    item["noon_evaluated_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    item["noon_return_pct"] = ret
                    item["noon_mfe_pct"] = previous_max
                    if previous_max < LIVE_PROFIT_PROTECT_ARM_PCT:
                        item["noon_waiting"] = True
                if item.get("noon_waiting") and not item.get("noon_triggered") and ret >= LIVE_NOON_RECOVERY_EXIT_PCT:
                    item["noon_waiting"] = False
                    item["noon_triggered"] = True
                    item["noon_trigger_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    item["noon_trigger_price"] = price
                    item["noon_trigger_return_pct"] = ret
                    _append_policy_event(item, "NOON_RECOVERY_CF", {
                        "return_pct": ret, "price": price,
                        "noon_mfe_pct": item.get("noon_mfe_pct", ""),
                    })

                if observed_time.time() >= _parse_hhmm(LIVE_FORCE_EXIT_TIME) and item.get("snapshot_1520_return_pct", "") == "":
                    item["snapshot_1520_return_pct"] = ret
                    item["snapshot_1520_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                if item.get("live_exit_reason"):
                    post_max = item.get("post_live_max_return_pct", "")
                    post_min = item.get("post_live_min_return_pct", "")
                    item["post_live_max_return_pct"] = ret if post_max == "" else max(safe_float(post_max), ret)
                    item["post_live_min_return_pct"] = ret if post_min == "" else min(safe_float(post_min), ret)

                if observed_time.time() >= dt_time(20, 0, 0):
                    item["snapshot_2000_return_pct"] = ret
                    item["snapshot_2000_time"] = observed_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    if item.get("original_result", "OPEN") == "OPEN":
                        item["original_result"] = "TIME_EXIT_2000"
                        item["original_exit_time"] = item["snapshot_2000_time"]
                        item["original_exit_price"] = price
                        item["original_return_pct"] = ret
                    item["finalized"] = True
                    _append_policy_event(item, "FOLLOWUP_2000_FINAL", {
                        "return_pct": ret, "price": price,
                        "original_result": item.get("original_result"),
                        "original_return_pct": item.get("original_return_pct"),
                    })
                    _append_live_paper_comparison(item, "FOLLOWUP_FINAL")
                    finalized_ids.append(fid)

        if finalized_ids:
            for fid in finalized_ids:
                policy_followup_ids_by_code.get(code, set()).discard(fid)
            if not policy_followup_ids_by_code.get(code):
                policy_followup_ids_by_code.pop(code, None)
        if changed:
            save_policy_followup_state()


    _v169_update_paper_position = update_paper_position
    def update_paper_position(code, current_price):
        code = clean_stock_code(code)
        # 신규 FIRST_75_PASS paper position을 policy follow-up에 먼저 등록.
        for trade_id in list(paper_position_ids_by_code.get(code, set())):
            p = paper_positions.get(trade_id)
            if p:
                _ensure_policy_followup_from_paper(p)
        _update_policy_followups_for_code(code, current_price, datetime.now())
        return _v169_update_paper_position(code, current_price)


    _v169_maybe_release_realtime = maybe_release_realtime
    def maybe_release_realtime(code):
        code = clean_stock_code(code)
        if policy_followup_ids_by_code.get(code):
            return
        return _v169_maybe_release_realtime(code)


    _v169_scan_market = scan_market
    def scan_market():
        # NXT_AFTER에는 follow-up 종목도 NXT 가능 종목만 _NX 체결을 추가 구독.
        session = get_session()
        if session == "NXT_AFTER" and websocket_manager is not None:
            for code in list(policy_followup_ids_by_code.keys()):
                try:
                    if is_nxt_tradable(code) is True:
                        websocket_manager.subscribe_stock(code, session)
                except Exception as e:
                    log(f"[NXT followup 구독 오류] {code} / {e}")
        return _v169_scan_market()


    _v169_save_live_trade_result = save_live_trade_result
    def save_live_trade_result(position, exit_price, result):
        pnl, ret = _v169_save_live_trade_result(position, exit_price, result)
        entry = safe_float(position.get("avg_entry_price", 0))
        qty = safe_int(position.get("exit_filled_qty", position.get("initial_qty", 0)))
        invested = entry * qty
        est_cost = invested * ESTIMATED_ROUND_TRIP_COST_PCT / 100.0
        perf = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "version": STRATEGY_VERSION,
            "paper_trade_id": position.get("paper_trade_id", ""),
            "entry_order_no": position.get("entry_order_no", ""),
            "stock_code": position.get("stock_code", ""),
            "stock_name": position.get("stock_name", ""),
            "exit_reason": result,
            "qty": qty,
            "actual_invested_amount": invested,
            "gross_return_pct": ret,
            "estimated_round_trip_cost_pct": ESTIMATED_ROUND_TRIP_COST_PCT,
            "estimated_net_return_pct": ret - ESTIMATED_ROUND_TRIP_COST_PCT,
            "gross_pnl_won": pnl,
            "estimated_cost_won": est_cost,
            "estimated_net_pnl_won": pnl - est_cost,
        }
        pd.DataFrame([perf]).to_csv(
            LIVE_PERFORMANCE_FILE, mode="a", header=not os.path.exists(LIVE_PERFORMANCE_FILE),
            index=False, encoding="utf-8-sig"
        )

        fid = _policy_followup_id(position)
        if fid:
            with POLICY_FOLLOWUP_LOCK:
                item = policy_followups.get(fid)
                if item is None:
                    item = {
                        "followup_id": fid,
                        "paper_trade_id": str(position.get("paper_trade_id", "")),
                        "stock_code": clean_stock_code(position.get("stock_code", "")),
                        "stock_name": position.get("stock_name", ""),
                        "entry_price": entry,
                        "entry_price_source": "BROKER_ACTUAL",
                        "profit_variants": {},
                        "original_result": "OPEN",
                        "max_return_pct": -999.0,
                        "min_return_pct": 999.0,
                        "finalized": False,
                    }
                    policy_followups[fid] = item
                item["entry_order_no"] = position.get("entry_order_no", "")
                item["live_exit_reason"] = result
                item["live_exit_time"] = _csv_datetime(position.get("sell_fill_time", position.get("live_exit_fill_time", datetime.now())))
                item["live_exit_price"] = exit_price
                item["live_exit_return_pct"] = ret
                item["post_live_max_return_pct"] = ret
                item["post_live_min_return_pct"] = ret
                code = clean_stock_code(item.get("stock_code", ""))
                if code:
                    policy_followup_ids_by_code.setdefault(code, set()).add(fid)
                _append_live_paper_comparison(item, "LIVE_EXIT")
            save_policy_followup_state()
        return pnl, ret


    _v169_build_strategy_result_row = build_strategy_result_row
    def build_strategy_result_row(position, strategy_name, strategy):
        row = _v169_build_strategy_result_row(position, strategy_name, strategy)
        gross = safe_float(row.get("return_rate", 0))
        row["estimated_round_trip_cost_pct"] = ESTIMATED_ROUND_TRIP_COST_PCT
        row["estimated_net_return_pct"] = gross - ESTIMATED_ROUND_TRIP_COST_PCT
        return row


    def _profit_factor(series):
        vals = [safe_float(x) for x in series]
        pos = sum(x for x in vals if x > 0)
        neg = -sum(x for x in vals if x < 0)
        if neg <= 0:
            return float("inf") if pos > 0 else 0.0
        return pos / neg


    def show_strategy_performance():
        if not os.path.exists(PAPER_TRADE_FILE):
            print("아직 가상매매 결과가 없습니다.")
            return
        df = pd.read_csv(PAPER_TRADE_FILE)
        if df.empty:
            print("아직 가상매매 결과가 없습니다.")
            return
        if "estimated_net_return_pct" not in df.columns:
            df["estimated_net_return_pct"] = df["return_rate"].astype(float) - ESTIMATED_ROUND_TRIP_COST_PCT
        rows = []
        for (strategy, tp, sl), g in df.groupby(["strategy", "TP", "SL"], dropna=False):
            gross = g["return_rate"].astype(float)
            net = g["estimated_net_return_pct"].astype(float)
            rows.append({
                "strategy": strategy, "TP": tp, "SL": sl,
                "trades": len(g),
                "wins": int((gross > 0).sum()),
                "losses": int((gross <= 0).sum()),
                "win_rate": float((gross > 0).mean() * 100),
                "gross_return_pct_sum": float(gross.sum()),
                "gross_return_pct_mean": float(gross.mean()),
                "estimated_net_return_pct_sum": float(net.sum()),
                "estimated_net_return_pct_mean": float(net.mean()),
                "gross_profit_factor": _profit_factor(gross),
                "net_profit_factor": _profit_factor(net),
            })
        display(pd.DataFrame(rows).sort_values(["estimated_net_return_pct_mean", "net_profit_factor"], ascending=False))


    _v169_force_close_all = force_close_all
    def force_close_all():
        result = _v169_force_close_all()
        now = datetime.now()
        # PROGRAM_END(20:00) 시점에 마지막 가격으로 follow-up을 확정.
        if now.time() >= dt_time(20, 0, 0):
            for code in list(policy_followup_ids_by_code.keys()):
                price = get_realtime_price(code)
                if not price:
                    with POLICY_FOLLOWUP_LOCK:
                        ids = list(policy_followup_ids_by_code.get(code, set()))
                        price = next((safe_float(policy_followups.get(fid, {}).get("last_price", 0)) for fid in ids if safe_float(policy_followups.get(fid, {}).get("last_price", 0)) > 0), 0)
                if price:
                    _update_policy_followups_for_code(code, price, now)
        return result


    # program cell 실행 후 state file이 있으면 follow-up 연구상태도 복원.
    load_policy_followup_state()


    def test_v1610_enhancements():
        """broker 호출 없이 v1.6.10 핵심 변경을 회귀검증합니다."""
        global LIVE_TRADE_AMOUNT_WON, LIVE_MAX_STOCKS, LIVE_TOTAL_BUDGET_WON
        global LIVE_MAX_TRADES_PER_DAY, LIVE_MAX_CONCURRENT_POSITIONS, LIVE_DAILY_MAX_LOSS_WON
        global LIVE_PROFIT_PROTECT_ENABLED, LIVE_NOON_RECOVERY_ENABLED

        assert STRATEGY_VERSION == "v1.6.10"
        assert len(EXIT_STRATEGIES) == 169
        assert EXIT_STRATEGIES["T250_S150"] == {"tp": 2.5, "sl": -1.5}
        assert LIVE_STRATEGY == "T250_S150"
        assert AUTO_TRADE_ENABLED is False

        # 시간경계
        assert not is_live_entry_time_allowed(datetime(2026, 9, 4, 9, 4, 59))
        assert is_live_entry_time_allowed(datetime(2026, 9, 4, 9, 5, 0))
        assert is_live_entry_time_allowed(datetime(2026, 9, 4, 9, 29, 59, 999000))
        assert not is_live_entry_time_allowed(datetime(2026, 9, 4, 9, 30, 0))
        assert not is_live_entry_time_allowed(datetime(2026, 9, 4, 9, 30, 42))

        backups = (LIVE_TRADE_AMOUNT_WON, LIVE_MAX_STOCKS, LIVE_TOTAL_BUDGET_WON,
                   LIVE_MAX_TRADES_PER_DAY, LIVE_MAX_CONCURRENT_POSITIONS, LIVE_DAILY_MAX_LOSS_WON)
        try:
            for amount, stocks, total in [(1_000_000, 5, 6_000_000), (2_000_000, 3, 7_000_000)]:
                LIVE_TRADE_AMOUNT_WON = amount
                LIVE_MAX_STOCKS = stocks
                LIVE_MAX_TRADES_PER_DAY = stocks
                LIVE_MAX_CONCURRENT_POSITIONS = stocks
                LIVE_TOTAL_BUDGET_WON = total
                LIVE_DAILY_MAX_LOSS_WON = 100_000
                assert validate_live_trading_config() is True

            bad_cases = [
                (0, 5, 6_000_000, 100_000),
                (1_000_000, 0, 6_000_000, 100_000),
                (1_000_000, 2.5, 6_000_000, 100_000),
                (2_000_000, 3, 1_000_000, 100_000),
                (1_000_000, 5, 6_000_000, 0),
            ]
            for amount, stocks, total, daily_loss in bad_cases:
                LIVE_TRADE_AMOUNT_WON = amount
                LIVE_MAX_STOCKS = stocks
                LIVE_MAX_TRADES_PER_DAY = stocks
                LIVE_MAX_CONCURRENT_POSITIONS = stocks
                LIVE_TOTAL_BUDGET_WON = total
                LIVE_DAILY_MAX_LOSS_WON = daily_loss
                try:
                    validate_live_trading_config()
                    raise AssertionError(f"invalid config accepted: {amount}, {stocks}, {total}, {daily_loss}")
                except ValueError:
                    pass
        finally:
            (LIVE_TRADE_AMOUNT_WON, LIVE_MAX_STOCKS, LIVE_TOTAL_BUDGET_WON,
             LIVE_MAX_TRADES_PER_DAY, LIVE_MAX_CONCURRENT_POSITIONS, LIVE_DAILY_MAX_LOSS_WON) = backups

        # 보호 / 정오 판정은 pure state로 검증.
        def fake_position():
            return {
                "avg_entry_price": 10000.0, "target_price": 10250.0, "stop_price": 9850.0,
                "status": "OPEN", "entry_complete": True, "auto_managed_qty": 1,
            }

        old_protect = LIVE_PROFIT_PROTECT_ENABLED
        old_noon = LIVE_NOON_RECOVERY_ENABLED
        try:
            LIVE_PROFIT_PROTECT_ENABLED = True
            LIVE_NOON_RECOVERY_ENABLED = True
            p = fake_position()
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 10100, datetime(2026,9,4,10,0,0))
            assert reason is None and p["profit_protect_armed"] is True
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 10040, datetime(2026,9,4,10,1,0))
            assert reason == "PROFIT_PROTECT"

            p = fake_position()
            _evaluate_v1610_live_exit_state(p, 10099, datetime(2026,9,4,11,0,0))
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 10040, datetime(2026,9,4,12,0,0))
            assert reason == "NOON_RECOVERY"

            p = fake_position()
            _evaluate_v1610_live_exit_state(p, 10099, datetime(2026,9,4,11,0,0))
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 9970, datetime(2026,9,4,12,0,0))
            assert reason is None and p["noon_recovery_waiting"] is True
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 10040, datetime(2026,9,4,13,0,0))
            assert reason == "NOON_RECOVERY"

            p = fake_position()
            _evaluate_v1610_live_exit_state(p, 10100, datetime(2026,9,4,11,0,0))
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 10050, datetime(2026,9,4,12,0,0))
            assert reason is None and p["noon_recovery_eligible"] is False

            p = fake_position()
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 10250, datetime(2026,9,4,10,0,0))
            assert reason == "TAKE_PROFIT"
            p = fake_position()
            reason, _, _ = _evaluate_v1610_live_exit_state(p, 9850, datetime(2026,9,4,10,0,0))
            assert reason == "STOP_LOSS"
        finally:
            LIVE_PROFIT_PROTECT_ENABLED = old_protect
            LIVE_NOON_RECOVERY_ENABLED = old_noon

        print("✅ v1.6.10 설정/09:30 exclusive/수익보호/정오회복 회귀 테스트 통과")
        return True
    ''')

    # Place overrides before END marker when possible, otherwise append.
    end_marker = "# ============================================================\n# END\n# ============================================================\n"
    if end_marker in program:
        program = program.replace(end_marker, appended + "\n" + end_marker, 1)
    else:
        program += appended

    cells[1]["id"] = "v1610-program"
    cells[1]["source"] = lines(program)

    # ------------------------------------------------------------------
    # Cell 3: quick reference (comments only; safe to execute).
    # ------------------------------------------------------------------
    quick = dedent(r'''
    # ============================================================
    # v1.6.10 QUICK REFERENCE
    # ============================================================
    # 저장 기본값: AUTO_TRADE_ENABLED=False
    # 다음 실제운용 시험: LIVE_PROFIT_PROTECT_ENABLED=True
    # 종목당 1,000,000원 / 하루 5회 / 총예산 6,000,000원
    # 실제진입: PRE_HISTORY의 FIRST_75_PASS만
    # 진입시간: MAIN 09:05:00 이상 / 09:30:00 미만(exclusive)
    # 동일종목 실제 하루 1회
    # TP/SL: T250_S150 = +2.50% / -1.50%
    # 수익보호: 실제 평균매수가 대비 +1.00% 도달 후 +0.40% floor 이탈 시 PROFIT_PROTECT
    # 정오 회복: 12:00까지 +1.00% 미도달 포지션만 +0.40% 회복 시 NOON_RECOVERY
    # 정오라는 이유만으로 손실 중 즉시매도하지 않음. 기본 SL -1.50% 유지.
    # 15:20 실제 강제청산 유지 / NXT 실제보유 금지 / 20:00까지 가상 follow-up
    # 추정 왕복비용 0.23%는 성과평가에만 차감. 실제 청산 트리거에는 미반영.
    # v1.6.9 broker pre-buy/pre-sell, sellable, 부분체결, 외부SELL, live_state atomic save 유지.
    # WIDE_HIGH_GAP/PRE_FAIL 등 Shadow와 169 TP/SL grid는 실전과 분리 유지.
    # ============================================================
    ''').lstrip()
    cells[2]["id"] = "v1610-quick-reference"
    cells[2]["source"] = lines(quick)

    # ------------------------------------------------------------------
    # Cell 4: continuity notes.
    # ------------------------------------------------------------------
    continuity = dedent(r'''
    # ============================================================
    # PROJECT CONTINUITY NOTES / DECISION HISTORY
    # ============================================================
    # 원칙: 최신 검증본을 엎어서 재작성하지 않고 지정된 최신 base에서 최소 수정/통합한다.
    # 이번 v1.6.10의 직접 parent는 code/releases/015_260903_v1.6.9.ipynb이다.
    #
    # 2026-09-03 (목)
    # - v1.6.9 실전 자동매매 3종목: JW신약 TP, 현대약품 SL, KB금융 SL.
    # - KB금융은 장중 약 +1% 수준 기회를 준 뒤 장시간 보유 후 -1.5%권 손절로 종료.
    # - 사용자는 최대수익보다 '수익/손익분기 기회를 준 종목이 큰 손실로 끝나는 상황'을 줄이는 안정 운용을 선호.
    # - 왕복 제비용 약 0.23% 관찰. gross와 0.23% 차감 estimated net return/PnL/net PF를 함께 평가.
    # - 다음 실전 기준을 T200_S150(+2.00/-1.50)에서 T250_S150(+2.50/-1.50)로 변경.
    # - T275_S150 / T275_S125 / T275_S100은 연구 유지, 표본 부족으로 실전 승격 금지.
    # - 수익보호 실제시험: 실제 평균매수가 대비 +1.00% 한 번 도달 후 +0.40%까지 밀리면 PROFIT_PROTECT.
    # - +0.40%는 비용 제외 수익률. 비용 0.23% 가정 시 추정 순 +0.17% 수준.
    # - 정오 조건부 회복청산: 12시까지 +1.00% 미도달 포지션은 손실에서 즉시 팔지 않고 +0.40% 회복 시 NOON_RECOVERY.
    # - 보호/회복 실제청산 후에도 원래 T250_S150, 15:20, 20:00/NXT 반사실 follow-up을 지속 기록.
    # - NXT 실전 보유는 보류. 실제 포지션은 15:20 청산, NXT는 연구만.
    # - 기본 실전금액을 종목당 100만원 / 하루5회 / 총예산600만원으로 축소.
    # - 첫 셀 맨 위에 자동매매/수익보호/종목당금액/횟수/총예산을 이 순서로 배치.
    # - v1.6.9의 300만원/1,800만원/30만원/5회 exact-value lock을 제거하고 논리 안전검증만 유지.
    # - v1.6.9 분단위 inclusive 시간비교로 09:30:42 진입 사례 확인. v1.6.10은 09:30:00 exclusive.
    # - 시작 네트워크/DNS 장애는 STARTUP_CONNECTIVITY_WAIT로 분리하고 broker 완전확인 전 신규주문 금지.
    # - 실제 미확인 주문/수량 불일치는 기존 ORDER_STATUS_UNKNOWN/POSITION_MISMATCH SAFE HALT 유지.
    # - SELL trigger→fill 지연의 대부분이 broker safety precheck였으나 안전검증은 삭제하지 않음.
    # - BASE/PRE_HISTORY/FIRST_75_PASS/LATER_PASS/CONFIRM, 모든 Shadow, WATCH Episode,
    #   ENTRY_PATH/POST_EXIT, 169 TP/SL grid, live↔paper 연결 구조는 parent v1.6.9에서 보존.
    # ============================================================
    ''').lstrip()
    cells[3]["id"] = "v1610-continuity"
    cells[3]["source"] = lines(continuity)

    # Notebook-level validation.
    if "v1.6.9" not in "".join(cells[3]["source"]):
        raise RuntimeError("continuity must name v1.6.9 parent")
    code = "".join(cells[1]["source"])
    compile(code, OUT_NAME, "exec")

    must_have = [
        'STRATEGY_VERSION = "v1.6.10"',
        'LIVE_STATE_FILE = "live_state_v1610.json"',
        'POST_EXIT_REFERENCE_STRATEGY = "T250_S150"',
        'def update_live_position_on_price(code, current_price):',
        'PROFIT_PROTECT', 'NOON_RECOVERY', 'STARTUP_CONNECTIVITY_WAIT',
        'policy_followup_state_v1610.json', 'def test_v1610_enhancements():',
        'WIDE_HIGH_GAP_SHADOW_ENABLED', 'PRE_FAIL_PULLBACK_SHADOW_ENABLED',
        'compute_broker_fill_delta', 'request_entry_cancel_for_exit',
    ]
    missing = [x for x in must_have if x not in code]
    if missing:
        raise RuntimeError(f"missing required preserved/new symbols: {missing}")

    settings_code = "".join(cells[0]["source"])
    first_values = [
        "AUTO_TRADE_ENABLED = False",
        "LIVE_PROFIT_PROTECT_ENABLED = True",
        "LIVE_TRADE_AMOUNT_WON = 1_000_000",
        "LIVE_MAX_STOCKS = 5",
        "LIVE_TOTAL_BUDGET_WON = 6_000_000",
    ]
    positions = [settings_code.index(v) for v in first_values]
    if positions != sorted(positions):
        raise RuntimeError("first five settings order broken")

    # Release notebook must remain only notebook content; no outputs.
    for c in cells:
        c["execution_count"] = None
        c["outputs"] = []

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: build_v1_6_10.py BASE.ipynb [OUTPUT.ipynb]")
    base = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else Path(OUT_NAME)
    if base.name != BASE_NAME:
        raise SystemExit(f"exact base required: {BASE_NAME}, got {base.name}")
    build(base, out)
    print(f"built: {out}")
