# ============================================================
# ★ 실제매매 설정 - 실행 전 반드시 확인
# ============================================================
# 이 블록은 파일/노트북의 가장 위에 둡니다.
# 실제매매 관련 값은 여기에서만 확인/수정하세요.
# ============================================================

# ------------------------------------------------------------
# 1) 실제 주문 ON / OFF
# ------------------------------------------------------------
# False = 연구/가상매매만 실행, 실제 주문 없음
# True  = 기존 가상연구 전체 유지 + FIRST_75_PASS만 실제 주문 검토
# ※ True + USE_MOCK=False이면 실계좌에 실제 주문이 나갑니다.
AUTO_TRADE_ENABLED = False

# False = 실계좌 API
# True  = 키움 모의투자 API
USE_MOCK = False


# ------------------------------------------------------------
# 2) 실제 진입전략
# ------------------------------------------------------------
# v1.6.8도 PRE_HISTORY + FIRST_75_PASS만 실제진입 허용
# BASE / LATER_PASS / CONFIRM / LIVE_FILTER_SHADOW / 70~74 Shadow는 실제 주문 금지
LIVE_ENTRY_MODE = "FIRST_75_PASS"

# 실제 신규진입: MAIN 09:05~09:30
LIVE_ENTRY_START = "09:05"
LIVE_ENTRY_END   = "09:30"
LIVE_ALLOWED_SESSIONS = {"MAIN"}


# ------------------------------------------------------------
# 3) 실제 매수금액 / 하루 한도
# ------------------------------------------------------------
# 종목당 최대 매수금액
LIVE_TRADE_AMOUNT_WON = 1_000_000

# 하루 최대 실제진입 종목 수
LIVE_MAX_STOCKS = 5
LIVE_MAX_TRADES_PER_DAY = LIVE_MAX_STOCKS
LIVE_MAX_CONCURRENT_POSITIONS = LIVE_MAX_STOCKS

# 실제 운용금액 안전 상한
LIVE_TOTAL_BUDGET_WON = 6_000_000

# 시장가 체결 상승을 고려한 수량계산 여유율 (%)
LIVE_MARKET_ORDER_BUFFER_PCT = 1.0

# 하루 실제 손실 한도
LIVE_DAILY_MAX_LOSS_WON = 100_000


# ------------------------------------------------------------
# 4) 실제 청산
# ------------------------------------------------------------
# 연구 기준전략 T200_S150 = TP +2.00% / SL -1.50%
LIVE_STRATEGY = "T200_S150"

# 장중 강제청산
LIVE_FORCE_EXIT_ENABLED = True
LIVE_FORCE_EXIT_TIME = "15:20"
LIVE_FORCE_EXIT_RETRY_SEC = 15


# ------------------------------------------------------------
# 5) 실제 주문 방식
# ------------------------------------------------------------
# 정규장 주문 거래소
LIVE_MAIN_EXCHANGE = "SOR"

# 주문유형: 3 = 시장가
LIVE_ORDER_TYPE = "3"


# ============================================================
# 단타 자동 스크리너 v1.6.7
# ============================================================
#
# AUTO_TRADE_ENABLED = False
#   → 가상매매만 실행
#
# AUTO_TRADE_ENABLED = True
#   → 실제 자동매매 + 가상매매 동시 실행
#
# 실제 주문은 키움 REST 주문 API,
# 가격/체결 추적은 WebSocket 실시간 시세를 사용합니다.
# ============================================================


# ============================================================
# 0. 인증정보 (.env)
# 코드와 분리해서 보관합니다.
# ============================================================

import os
from pathlib import Path


def load_local_env():
    """
    현재 작업폴더 또는 이 .py 파일과 같은 폴더의 .env를 읽습니다.
    추가 패키지 없이 표준 라이브러리만 사용합니다.
    """

    candidates = []

    try:
        candidates.append(
            Path(__file__).resolve().parent / ".env"
        )
    except Exception:
        pass

    candidates.append(
        Path.cwd() / ".env"
    )

    env_path = next(
        (p for p in candidates if p.exists()),
        None
    )

    if env_path is None:
        searched = " / ".join(
            str(p) for p in candidates
        )
        raise FileNotFoundError(
            ".env 파일을 찾을 수 없습니다. "
            f"확인 위치: {searched}"
        )

    with env_path.open(
        "r",
        encoding="utf-8-sig"
    ) as f:
        for raw_line in f:
            line = raw_line.strip()

            if (
                not line
                or line.startswith("#")
                or "=" not in line
            ):
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value[0] in ["\"", "'"]
            ):
                value = value[1:-1]

            os.environ.setdefault(
                key,
                value
            )

    return env_path


def env_bool(name, default=False):
    value = os.getenv(
        name,
        str(default)
    )

    return str(value).strip().lower() in [
        "1", "true", "yes", "y", "on"
    ]


ENV_FILE_PATH = load_local_env()

KIWOOM_APP_KEY = os.getenv(
    "KIWOOM_APP_KEY", ""
).strip()

KIWOOM_SECRET_KEY = os.getenv(
    "KIWOOM_SECRET_KEY", ""
).strip()

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN", ""
).strip()

TELEGRAM_PERSONAL_CHAT_ID = os.getenv(
    "TELEGRAM_PERSONAL_CHAT_ID", ""
).strip()

TELEGRAM_GROUP_CHAT_ID = os.getenv(
    "TELEGRAM_GROUP_CHAT_ID", ""
).strip()

TELEGRAM_SEND_PERSONAL = env_bool(
    "TELEGRAM_SEND_PERSONAL",
    True
)

TELEGRAM_SEND_GROUP = env_bool(
    "TELEGRAM_SEND_GROUP",
    False
)

TELEGRAM_CHAT_IDS = []

if (
    TELEGRAM_SEND_PERSONAL
    and TELEGRAM_PERSONAL_CHAT_ID
):
    TELEGRAM_CHAT_IDS.append(
        TELEGRAM_PERSONAL_CHAT_ID
    )

if (
    TELEGRAM_SEND_GROUP
    and TELEGRAM_GROUP_CHAT_ID
):
    TELEGRAM_CHAT_IDS.append(
        TELEGRAM_GROUP_CHAT_ID
    )


# ============================================================
# 1. ★ 사용자 설정
# 이 영역만 수정해서 운용하는 것을 권장합니다.
# ============================================================

STRATEGY_VERSION = "v1.6.8"



# ------------------------------------------------------------
# A. 핵심 연구 / 가상매매 전략
# ------------------------------------------------------------

# 가상매매 익절 / 손절 실험 범위 (%)
# TP: +1.00 ~ +4.00, 0.25% 간격 (13단계)
# SL: -0.50 ~ -3.50, 0.25% 간격 (13단계)
# 총 169개 조합을 같은 진입가에서 동시에 추적
PAPER_TP_LEVELS = [
    1.00, 1.25, 1.50, 1.75,
    2.00, 2.25, 2.50, 2.75,
    3.00, 3.25, 3.50, 3.75,
    4.00,
]

PAPER_SL_LEVELS = [
    -0.50, -0.75, -1.00, -1.25,
    -1.50, -1.75, -2.00, -2.25,
    -2.50, -2.75, -3.00, -3.25,
    -3.50,
]

# 전략명 예: T200_S150 = 익절 +2.00% / 손절 -1.50%
# dict 입력 순서는 TP 오름차순 → 같은 TP에서 손절폭 오름차순
EXIT_STRATEGIES = {
    f"T{int(round(tp * 100)):03d}_S{int(round(abs(sl) * 100)):03d}": {
        "tp": tp,
        "sl": sl,
    }
    for tp in PAPER_TP_LEVELS
    for sl in PAPER_SL_LEVELS
}

# ------------------------------------------------------------
# B. LIVE_FILTER_SHADOW 연구 설정
# 실제 FIRST_75_PASS 주문 필터가 아닙니다.
# ------------------------------------------------------------

# LIVE_FILTER_SHADOW 연구군의 고점이격 기준
LIVE_MAX_HIGH_GAP = 1.5


# ------------------------------------------------------------
# C. 종목 선정
# ------------------------------------------------------------

# 등락률 (%)
MIN_CHANGE_RATE = 5.0
MAX_CHANGE_RATE = 20.0

# 최소 거래대금: 200억원
MIN_TRADING_VALUE_WON = 20_000_000_000

# 당일고가 대비 최대 이격 (%)
MAX_HIGH_GAP = 3.0

# 최소 거래량
MIN_PRE_FILTER_VOLUME = 300_000

# 제외종목
EXCLUDE_ETF = True
EXCLUDE_ETN = True
EXCLUDE_SPAC = True
EXCLUDE_PREFERRED = True


# ------------------------------------------------------------
# D. 후보 점수
# ------------------------------------------------------------

# 신호 인정 최소 점수 (진입 자격)
MIN_SIGNAL_SCORE = 75

# WATCH는 진입조건이 아니라 사전 관찰 시작선입니다.
WATCH_SCORE = 60

# 가격/고점이격 rolling history 보관시간
PRICE_HISTORY_RETENTION_SEC = 600
HISTORY_LOOKBACKS_SEC = [15, 30, 60, 120, 180, 300]

# PRE_HISTORY 첫 주 시뮬레이션 조건
# 75점+이면서 최근 30초/60초 가격이 상승하고,
# 60초 동안 high_gap이 감소(고점 접근)할 때 진입합니다.
PRE_HISTORY_MIN_SEC = 60
PRE_HISTORY_REQUIRE_30S_UP = True
PRE_HISTORY_REQUIRE_60S_UP = True
PRE_HISTORY_REQUIRE_HIGH_GAP_60S_DOWN = True

# CONFIRM: 최초 75점+ 다음 정상 스캔에서 확인
CONFIRM_MIN_RISE_PCT = 0.10
CONFIRM_TIMEOUT_SEC = 45

# 70~74점 임계값 검증용 별도 연구군
SHADOW_SCORE_70_74_ENABLED = True
SHADOW_SCORE_MIN = 70
SHADOW_SCORE_MAX = 74

# 실전 진입시간/고점조건만 재현하는 연구용 SHADOW
LIVE_FILTER_SHADOW_ENABLED = True

# 기준전략 청산 후 가격 추적
POST_EXIT_TRACKING_ENABLED = True
POST_EXIT_REFERENCE_STRATEGY = "T200_S150"
POST_EXIT_HORIZONS_SEC = [300, 600, 1800]

# 진입 후 초기 가격경로 추적 (연구용)
# 기준전략이 먼저 청산되더라도 최대 5분까지 독립적으로 추적합니다.
ENTRY_PATH_TRACKING_ENABLED = True
ENTRY_PATH_HORIZONS_SEC = [30, 60, 120, 180, 300]

# 점수 가중치: 총 100점
WEIGHT_TRADING_VALUE = 40
WEIGHT_HIGH_POSITION = 25
WEIGHT_VALUE_GROWTH = 20
WEIGHT_VOLUME_GROWTH = 15

# 거래량/거래대금 증가율 비교 기준
GROWTH_LOOKBACK_SEC = 60


# ------------------------------------------------------------
# F. 가상매매
# ------------------------------------------------------------

PAPER_TRADE_ENABLED = True
AUTO_PAPER_ENTRY = True
ONE_ENTRY_PER_STOCK = True  # 동일 WATCH Episode + 동일 연구 mode 내 1회

# 가상 진입 슬리피지 (%)
PAPER_ENTRY_SLIPPAGE = 0.10


# ------------------------------------------------------------
# G. 운영시간
# ------------------------------------------------------------

PROGRAM_START = "08:00"
PROGRAM_END   = "20:00"

NXT_PRE_START = "08:00"
NXT_PRE_END   = "08:50"

MAIN_START = "09:00"
MAIN_END   = "15:30"

NXT_AFTER_START = "15:40"
NXT_AFTER_END   = "20:00"

# 전체 시장 스캔 / REST 백업확인 주기
SCAN_INTERVAL_SEC = 15
POSITION_CHECK_INTERVAL_SEC = 10


# ------------------------------------------------------------
# H. 시장 / 실시간 설정
# ------------------------------------------------------------

# 1=KRX, 2=NXT, 3=통합(SOR)
EXCHANGE_TYPE = "3"

# WebSocket 실시간 체결
WEBSOCKET_ENABLED = True

# NXT 거래 가능 여부 확인
NXT_ELIGIBILITY_CHECK = True


# ------------------------------------------------------------
# I. Telegram
# ------------------------------------------------------------

# 같은 종목 재알림 간격
ALERT_COOLDOWN_MIN = 30

# 하루 최대 알림 수
MAX_ALERTS_PER_DAY = float("inf")

# 자동 진단 시간
DIAGNOSTIC_TIMES = [
    "08:05",
    "09:05",
    "15:45",
]


# ------------------------------------------------------------
# J. 시스템 / API
# ------------------------------------------------------------

WEBSOCKET_STALE_SEC = 15
WEBSOCKET_GROUP_NO = "1"

# 재연결/다중진입 시 REG 요청을 몰아서 보내지 않도록 간격을 둡니다.
WEBSOCKET_REG_INTERVAL_SEC = 0.20
WEBSOCKET_REG_RETRY_COUNT = 3
WEBSOCKET_REG_RETRY_DELAY_SEC = 0.50

HTTP_TIMEOUT = 10
API_MIN_INTERVAL_SEC = 0.25

# KA10001은 HTTP 응답 대기만 병렬화합니다.
# 실제 요청 시작 간격은 API_MIN_INTERVAL_SEC가 제한합니다.
KA10001_MAX_WORKERS = 8

# v1.6.7 실제계좌 안전검증
# 주기 동기화는 WebSocket 가격처리와 분리된 worker에서 실행합니다.
BROKER_SYNC_INTERVAL_SEC = 30
BROKER_BALANCE_MAX_AGE_SEC = 5
EXTERNAL_EVENT_RESOLVE_DELAY_SEC = 1.0
LOCAL_SUBMIT_INTENT_MAX_SEC = HTTP_TIMEOUT + 5
LIVE_ASYNC_MAX_WORKERS = 3

DEBUG_MODE = True


# ------------------------------------------------------------
# K. 저장 파일
# ------------------------------------------------------------

SIGNAL_LOG_FILE = "scanner_signals_v168.csv"
PAPER_TRADE_FILE = "paper_trades_v168.csv"
PAPER_ENTRY_DECISION_FILE = "paper_entry_decisions_v168.csv"
POST_EXIT_FILE = "paper_post_exit_v168.csv"
ENTRY_PATH_FILE = "paper_entry_path_v168.csv"
SYSTEM_LOG_FILE = "scanner_system_v168.csv"

LIVE_TRADE_FILE = "live_trades_v168.csv"
LIVE_ORDER_FILE = "live_orders_v168.csv"
LIVE_STATE_FILE = "live_state_v168.json"


# ============================================================
# 2. API 설정
# ============================================================


# ------------------------------------------------------------
# KA10027
# 전일대비등락률상위
# ------------------------------------------------------------

CHANGE_RATE_API_ID = "ka10027"

CHANGE_RATE_API_PATH = "/api/dostk/rkinfo"


CHANGE_RATE_REQUEST = {

    "sort_tp": "1",

    "trde_qty_cnd": "0000",

    "stk_cnd": "1",

    "crd_cnd": "0",

    "updown_incls": "1",

    "pric_cnd": "0",

    "trde_prica_cnd": "0",

    "stex_tp": EXCHANGE_TYPE
}


# ------------------------------------------------------------
# KA10032
# 거래대금상위
# ------------------------------------------------------------

TRADING_VALUE_API_ID = "ka10032"

TRADING_VALUE_API_PATH = "/api/dostk/rkinfo"


TRADING_VALUE_REQUEST = {

    # 관리종목 제외
    "mang_stk_incls": "0",

    "stex_tp": EXCHANGE_TYPE
}


# ------------------------------------------------------------
# KA10001
# 주식기본정보
# ------------------------------------------------------------

QUOTE_API_ID = "ka10001"

QUOTE_API_PATH = "/api/dostk/stkinfo"


# ------------------------------------------------------------
# 실제 주문
# ------------------------------------------------------------

BUY_ORDER_API_ID = "kt10000"
SELL_ORDER_API_ID = "kt10001"
CANCEL_ORDER_API_ID = "kt10003"
ORDER_API_PATH = "/api/dostk/ordr"

# 실제 계좌 상태 확인
PENDING_ORDER_API_ID = "ka10075"
ACCOUNT_POSITION_API_ID = "kt00018"
ACCOUNT_API_PATH = "/api/dostk/acnt"


# ------------------------------------------------------------
# 시장
# ------------------------------------------------------------

MARKETS = [

    ("001", "KOSPI"),

    ("101", "KOSDAQ")

]


# ============================================================
# 3. 라이브러리
# ============================================================

import requests
import pandas as pd

import os
import csv
import time
import traceback
import json
import asyncio
import threading

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

try:
    import websockets
except ImportError:
    websockets = None

from datetime import datetime, timedelta


# ============================================================
# 4. 전역 상태값
# ============================================================

ACCESS_TOKEN = None

LAST_API_CALL_TS = 0.0

# REST 호출 속도제어를 메인스레드/WebSocket 주문스레드가 공유
API_RATE_LOCK = threading.Lock()

# 실시간/주문 상태 보호
STATE_LOCK = threading.RLock()

# WebSocket
websocket_manager = None
realtime_prices = {}
realtime_price_ts = {}

# 실제 자동매매 상태
live_orders = {}
live_positions = {}
live_entered_today = set()
live_processed_fill_ids = set()
# REST 주문응답과 WebSocket 체결의 극단적 순서역전을 잠시 보관
live_unmatched_order_events = {}
live_external_resolution_pending = set()
# REST 응답보다 WS 주문이 먼저 도착하는 경우 외부주문으로 오인하지 않기 위한 제출 intent
live_submit_intents = {}
live_trade_count = 0
live_daily_realized_pnl = 0.0
live_trading_halted = False
live_system_halt_reason = ""
last_live_force_exit_attempt_ts = 0.0
live_recovery_mode = False

# 종목 단위 격리. 시스템 전체 SAFE HALT와 분리합니다.
live_blocked_codes = {}
live_execution_issue_codes = set()

# 실제계좌 상태 원장
broker_balances = {}
broker_startup_holdings = set()
last_broker_full_sync_ts = 0.0

# 종료 요청이 들어온 순간부터 신규 BUY/SELL/CANCEL submit을 전면 차단합니다.
shutdown_requested = False

# 파일쓰기/계좌조회/비동기 실제주문 안전작업 보호
LIVE_CSV_LOCK = threading.Lock()

# v1.6.8 live_state 저장 전용 lock / 제한적 retry
LIVE_STATE_FILE_LOCK = threading.Lock()
LIVE_STATE_SAVE_RETRY_COUNT = 3
LIVE_STATE_SAVE_RETRY_DELAY_SEC = 0.05
BROKER_SYNC_LOCK = threading.Lock()
LIVE_ASYNC_EXECUTOR = ThreadPoolExecutor(
    max_workers=LIVE_ASYNC_MAX_WORKERS,
    thread_name_prefix="LiveSafety",
)


last_alert_time = {}

# (entry_mode, stock_code, watch_episode_id) 단위 진입 제한
# 이름은 기존 호환을 위해 유지하지만 v1.6.6부터 "하루 1회"가 아니라
# "같은 WATCH Episode + 같은 연구 mode 1회" 의미입니다.
paper_entered_today = set()

# trade_id -> position
paper_positions = {}
# stock_code -> set(trade_id)
paper_position_ids_by_code = {}

# Episode 재진입 분석 메타데이터
paper_stock_entry_counts_today = {}
paper_mode_entry_counts_today = {}
paper_last_trade_id_by_mode = {}
# 종료된 trade도 기준전략(T200_S150) 결과 연결을 위해 당일 메타는 유지
paper_trade_registry = {}

# 75점 이전 가격/고점이격/점수 이력
# code -> [{ts, price, high_gap, score, ...}, ...]
price_history = {}

# 60점+ 당일 최초 WATCH 상태 (기존 지표 보존)
watch_states = {}

# 연속 WATCH Episode 상태
# code -> {active, episode_no, episode_id, start_time, ...}
watch_episode_states = {}
watch_episode_counts = {}

# PRE_HISTORY 최초 75점 상태
# 최초 75점에서 PRE 통과 여부를 별도 보존하여 FIRST_75_PASS/LATER_PASS를 구분
pre_first_75_states = {}

# Shadow 오염 방지용: 실제 점수평가에서 75점+을 한 번이라도 본 종목
# (세션 경계 무효 관측은 first_75 전략상태에는 넣지 않되, Shadow 역행진입은 막습니다.)
score_75_seen_today = set()

# 70~74점 Shadow 최초 진입상태 (paired sample 연결용)
score_shadow_states = {}

# CONFIRM 최초 75점 신호 상태
confirm_pending = {}
confirm_started_today = set()

# 스캔 순번: CONFIRM의 '다음 정상 스캔' 판정용
scan_sequence = 0

# 기준전략 청산 후 가격 추적
# trade_id -> tracker / code -> set(trade_id)
post_exit_trackers = {}
post_exit_ids_by_code = {}

# 진입 후 30/60/120/180/300초 가격경로 추적
# trade_id -> tracker / code -> set(trade_id)
entry_path_trackers = {}
entry_path_ids_by_code = {}

# NXT 거래 가능 여부 캐시
# code : True / False
nxt_eligibility_cache = {}


# 60초 기준 증가율 계산용 히스토리
# code : [{"ts": epoch, "value": 숫자}, ...]
previous_volume = {}

# code : [{"ts": epoch, "source": ACTUAL/ESTIMATED, "value": 숫자}, ...]
previous_trading_value = {}


daily_alert_count = 0


current_trade_date = (
    datetime.now()
    .strftime("%Y-%m-%d")
)


sent_diagnostic_times = set()


last_scan_stats = {

    "received":
        0,

    "pre_filtered":
        0,

    "actual_count":
        0,

    "estimated_count":
        0,

    "value_passed":
        0,

    "final_candidates":
        0,

    "watch_candidates":
        0,

    "signal_candidates":
        0,

    "shadow_score_candidates":
        0,

    "confirm_pending":
        0,

    "ka10001_requested":
        0,

    "ka10001_success":
        0,

    "ka10001_error":
        0,

    "ka10001_429":
        0,

    "ka10001_502":
        0,

    "ka10001_timeout":
        0,

    "alerts":
        0,

    "top_candidates":
        []
}


# ============================================================
# 5. 공통 함수
# ============================================================

def safe_float(
    value,
    default=0.0
):

    if value is None:
        return default

    try:

        value = (
            str(value)
            .replace(",", "")
            .replace("+", "")
            .strip()
        )

        if value == "":
            return default

        return float(value)

    except Exception:

        return default


def safe_int(
    value,
    default=0
):

    return int(
        safe_float(
            value,
            default
        )
    )


def abs_price(value):

    return abs(
        safe_float(value)
    )


def clean_stock_code(code):

    cleaned = (
        str(code)
        .split("_")[0]
        .strip()
    )

    # 계좌조회 응답이 A005930 형태인 경우 A 제거
    if (
        len(cleaned) == 7
        and cleaned.startswith("A")
        and cleaned[1:].isdigit()
    ):
        cleaned = cleaned[1:]

    return cleaned


def first_existing(
    data,
    keys,
    default=None
):

    if not isinstance(
        data,
        dict
    ):

        return default


    for key in keys:

        if key in data:

            return data[key]


    return default


def find_first_list(data):

    if not isinstance(
        data,
        dict
    ):

        return []


    for key, value in (
        data.items()
    ):

        if isinstance(
            value,
            list
        ):

            if DEBUG_MODE:

                log(
                    f"[DEBUG] "
                    f"응답 LIST KEY = {key}"
                )

            return value


    return []


# ============================================================
# 6. 로그
# ============================================================

def log(message):

    now = (
        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    print(
        f"[{now}] {message}"
    )


    try:

        exists = (
            os.path.exists(
                SYSTEM_LOG_FILE
            )
        )


        with open(

            SYSTEM_LOG_FILE,

            "a",

            newline="",

            encoding="utf-8-sig"

        ) as f:


            writer = csv.writer(f)


            if not exists:

                writer.writerow([
                    "datetime",
                    "message"
                ])


            writer.writerow([
                now,
                message
            ])


    except Exception:

        pass


# ============================================================
# 6-A. 실제매매 상태 저장 / 복구
# ============================================================

def _json_safe(value):

    if isinstance(value, datetime):
        return {
            "__type__": "datetime",
            "value": value.isoformat()
        }

    if isinstance(value, set):
        return {
            "__type__": "set",
            "value": [
                _json_safe(x)
                for x in value
            ]
        }

    if isinstance(value, tuple):
        return {
            "__type__": "tuple",
            "value": [
                _json_safe(x)
                for x in value
            ]
        }

    if isinstance(value, list):
        return [
            _json_safe(x)
            for x in value
        ]

    if isinstance(value, dict):
        return {
            str(k): _json_safe(v)
            for k, v in value.items()
        }

    return value


def _json_restore(value):

    if isinstance(value, list):
        return [
            _json_restore(x)
            for x in value
        ]

    if not isinstance(value, dict):
        return value

    type_name = value.get(
        "__type__"
    )

    if type_name == "datetime":
        try:
            return datetime.fromisoformat(
                value.get(
                    "value",
                    ""
                )
            )
        except Exception:
            return datetime.now()

    if type_name == "set":
        return set(
            _json_restore(x)
            for x in value.get(
                "value",
                []
            )
        )

    if type_name == "tuple":
        return tuple(
            _json_restore(x)
            for x in value.get(
                "value",
                []
            )
        )

    return {
        k: _json_restore(v)
        for k, v in value.items()
    }


def _normalize_live_order_state(order):
    if not isinstance(order, dict):
        return {}

    order.setdefault("requested_qty", safe_int(order.get("qty", 0)))
    order.setdefault("filled_qty", 0)
    order.setdefault("filled_amount", 0.0)
    order.setdefault("broker_filled_qty", safe_int(order.get("filled_qty", 0)))
    order.setdefault("unfilled_qty", max(
        0,
        safe_int(order.get("requested_qty", 0))
        - safe_int(order.get("filled_qty", 0))
    ))
    order.setdefault("pending_auto_buy_qty", 0)
    order.setdefault("pending_auto_sell_qty", 0)
    order.setdefault("entry_seq", "")
    return order


def _normalize_live_position_state(position):
    if not isinstance(position, dict):
        return {}

    legacy_qty = safe_int(position.get("qty", 0))
    auto_qty = safe_int(position.get("auto_managed_qty", legacy_qty))
    position["auto_managed_qty"] = max(0, auto_qty)
    position["qty"] = position["auto_managed_qty"]  # legacy compatibility mirror
    position.setdefault("initial_qty", position["auto_managed_qty"])
    position.setdefault("external_qty", 0)
    position.setdefault("broker_held_qty", "")
    position.setdefault("broker_sellable_qty", "")
    position.setdefault("broker_avg_price", "")
    position.setdefault("broker_updated_at", "")
    position.setdefault("pending_auto_buy_qty", 0)
    position.setdefault("pending_auto_sell_qty", 0)
    position.setdefault("entry_seq", "")
    position.setdefault("exit_trigger_reason", "")
    position.setdefault("exit_trigger_time", "")
    position.setdefault("exit_trigger_price", "")

    # v1.6.8: 외부/수동 SELL은 프로그램 자동주문 원장과 분리하여
    # 주문번호별 requested-unfilled 누적체결량에서 delta만 관리합니다.
    position.setdefault("external_sell_order_progress", {})
    position.setdefault("external_sell_fill_lots", [])

    # v1.6.8: 청산 단계별 지연 계측. 기존 필드는 그대로 보존합니다.
    position.setdefault("broker_precheck_start_time", "")
    position.setdefault("broker_precheck_end_time", "")
    position.setdefault("broker_precheck_sec", "")
    position.setdefault("sell_order_time", position.get("live_exit_order_time", ""))
    position.setdefault("sell_fill_time", position.get("live_exit_fill_time", ""))
    position.setdefault("trigger_to_order_sec", "")
    position.setdefault("order_to_fill_sec", "")
    position.setdefault("trigger_to_fill_sec", "")

    return position



def save_live_state():
    """
    실제 자동매매 상태를 원자적으로 JSON 저장합니다.

    v1.6.8:
    - LIVE_STATE_FILE_LOCK으로 동일 프로세스 내 동시 save를 직렬화
    - 매 저장마다 고유 tmp 파일 사용
    - os.replace() atomic replace 유지
    - Windows 일시적 파일 점유를 고려해 짧은 제한적 retry
    - 단발성 저장실패만으로 SAFE HALT하지 않음
    """

    if not AUTO_TRADE_ENABLED:
        return

    last_error = None

    # state snapshot 자체는 기존 STATE_LOCK 보호를 그대로 유지합니다.
    with STATE_LOCK:
        state = {
            "trade_date": current_trade_date,
            "live_orders": live_orders,
            "live_positions": live_positions,
            "live_entered_today": live_entered_today,
            "live_processed_fill_ids": live_processed_fill_ids,
            "live_trade_count": live_trade_count,
            "live_daily_realized_pnl": live_daily_realized_pnl,
            "live_trading_halted": live_trading_halted,
            "live_system_halt_reason": live_system_halt_reason,
            "live_recovery_mode": live_recovery_mode,
            "live_blocked_codes": live_blocked_codes,
            "live_execution_issue_codes": live_execution_issue_codes,
            "broker_balances": broker_balances,
            "broker_startup_holdings": broker_startup_holdings,
        }
        safe_state = _json_safe(state)

    with LIVE_STATE_FILE_LOCK:
        for attempt in range(1, LIVE_STATE_SAVE_RETRY_COUNT + 1):
            tmp_file = None
            try:
                base_dir = os.path.dirname(os.path.abspath(LIVE_STATE_FILE)) or "."
                base_name = os.path.basename(LIVE_STATE_FILE)
                fd, tmp_file = tempfile.mkstemp(
                    prefix=f".{base_name}.",
                    suffix=".tmp",
                    dir=base_dir,
                    text=True,
                )
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(safe_state, f, ensure_ascii=False, indent=2)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass

                os.replace(tmp_file, LIVE_STATE_FILE)
                tmp_file = None
                return

            except Exception as e:
                last_error = e
                if tmp_file:
                    try:
                        os.remove(tmp_file)
                    except Exception:
                        pass

                if attempt < LIVE_STATE_SAVE_RETRY_COUNT:
                    time.sleep(LIVE_STATE_SAVE_RETRY_DELAY_SEC)

    log(
        f"[실전상태 저장 오류] {last_error} / "
        f"{LIVE_STATE_SAVE_RETRY_COUNT}회 시도 후 실패"
    )



def load_live_state():
    """
    v1.6.7 실전상태 복구.

    저장값은 그대로 신뢰하지 않고, 이후 reconcile_live_state_with_broker()에서
    broker 실제 보유/미체결과 교차검증합니다.
    """

    global live_orders
    global live_positions
    global live_entered_today
    global live_processed_fill_ids
    global live_unmatched_order_events
    global live_external_resolution_pending
    global live_submit_intents
    global live_trade_count
    global live_daily_realized_pnl
    global live_trading_halted
    global live_system_halt_reason
    global live_recovery_mode
    global live_blocked_codes
    global live_execution_issue_codes
    global broker_balances
    global broker_startup_holdings

    if not AUTO_TRADE_ENABLED:
        return False

    if not os.path.exists(LIVE_STATE_FILE):
        return False

    try:
        with open(LIVE_STATE_FILE, "r", encoding="utf-8") as f:
            state = _json_restore(json.load(f))

        state_orders = state.get("live_orders", {}) or {}
        state_positions = state.get("live_positions", {}) or {}

        for order in state_orders.values():
            _normalize_live_order_state(order)
        for position in state_positions.values():
            _normalize_live_position_state(position)

        unresolved = (
            any(safe_int(p.get("auto_managed_qty", p.get("qty", 0))) > 0
                for p in state_positions.values())
            or any(
                o.get("status") in [
                    "SUBMITTED", "PARTIAL", "CANCEL_PENDING",
                    "EXIT_TRIGGERED", "EXIT_VALIDATING", "ORDER_STATUS_UNKNOWN"
                ]
                for o in state_orders.values()
            )
        )

        old_trade_date = state.get("trade_date")
        same_day = old_trade_date == current_trade_date

        if not same_day and not unresolved:
            log("이전 거래일 실전상태는 미해결 건이 없어 복구하지 않습니다.")
            return False

        with STATE_LOCK:
            live_orders = state_orders
            live_positions = state_positions
            live_entered_today = set(state.get("live_entered_today", set())) if same_day else set(state_positions.keys())
            live_processed_fill_ids = set(state.get("live_processed_fill_ids", set()))
            live_unmatched_order_events = {}
            live_external_resolution_pending = set()
            live_submit_intents = {}
            live_trade_count = int(state.get("live_trade_count", len(live_entered_today))) if same_day else len(live_entered_today)
            live_daily_realized_pnl = float(state.get("live_daily_realized_pnl", 0.0)) if same_day else 0.0
            live_trading_halted = bool(state.get("live_trading_halted", False))
            live_system_halt_reason = str(state.get("live_system_halt_reason", ""))
            live_recovery_mode = bool(unresolved)
            live_blocked_codes = dict(state.get("live_blocked_codes", {}) or {})
            live_execution_issue_codes = set(state.get("live_execution_issue_codes", set()))
            broker_balances = dict(state.get("broker_balances", {}) or {})
            broker_startup_holdings = set(state.get("broker_startup_holdings", set()))

            # 전 거래일 미해결 상태는 신규진입을 일단 막고 broker 확인 후 판단.
            if not same_day and unresolved:
                live_trading_halted = True
                live_system_halt_reason = "이전 거래일 미해결 실전상태"

        log(
            "실전상태 복구 완료 / "
            f"상태일 {old_trade_date} / 포지션 {len(live_positions)}개 / 주문 {len(live_orders)}개"
        )
        return True

    except Exception as e:
        with STATE_LOCK:
            live_recovery_mode = True
            live_trading_halted = True
            live_system_halt_reason = "실전상태 파일 복구 실패"
        log(f"[실전상태 복구 오류] {e}")
        return False

# ============================================================
# 7. 서버
# ============================================================

if USE_MOCK:

    KIWOOM_BASE_URL = (
        "https://mockapi.kiwoom.com"
    )

else:

    KIWOOM_BASE_URL = (
        "https://api.kiwoom.com"
    )


# ============================================================
# 8. API 속도제어
# ============================================================

def wait_api_rate_limit():

    global LAST_API_CALL_TS

    # 메인 스캐너 REST 호출과 WebSocket 스레드의
    # 실제 주문 REST 호출이 동시에 발생해도
    # 전체 호출 간격을 하나의 락으로 관리합니다.
    with API_RATE_LOCK:

        now = time.time()

        elapsed = (
            now
            - LAST_API_CALL_TS
        )

        if (
            elapsed
            < API_MIN_INTERVAL_SEC
        ):

            time.sleep(
                API_MIN_INTERVAL_SEC
                - elapsed
            )

        LAST_API_CALL_TS = (
            time.time()
        )


# ============================================================
# 9. 접근토큰
# ============================================================

def get_kiwoom_token():

    global ACCESS_TOKEN


    url = (
        KIWOOM_BASE_URL
        + "/oauth2/token"
    )


    body = {

        "grant_type":
            "client_credentials",

        "appkey":
            KIWOOM_APP_KEY,

        "secretkey":
            KIWOOM_SECRET_KEY
    }


    log(
        "키움 접근토큰 발급 요청"
    )


    r = requests.post(

        url,

        json=body,

        timeout=HTTP_TIMEOUT
    )


    data = r.json()


    if r.status_code != 200:

        raise Exception(

            f"토큰 HTTP 오류 "
            f"{r.status_code} / {data}"
        )


    if data.get(
        "return_code",
        0
    ) != 0:

        raise Exception(
            f"토큰 발급 실패: {data}"
        )


    ACCESS_TOKEN = (
        data.get("token")
    )


    if not ACCESS_TOKEN:

        raise Exception(
            "접근토큰 없음"
        )


    log(

        "키움 접근토큰 발급 성공 / "
        f"만료: {data.get('expires_dt')}"
    )


    return ACCESS_TOKEN


# ============================================================
# 10. 키움 공통 POST
# ============================================================

def kiwoom_post(
    path,
    api_id,
    body
):

    global ACCESS_TOKEN


    if not ACCESS_TOKEN:

        get_kiwoom_token()


    wait_api_rate_limit()


    url = (
        KIWOOM_BASE_URL
        + path
    )


    headers = {

        "Content-Type":
            "application/json;charset=UTF-8",

        "authorization":
            f"Bearer {ACCESS_TOKEN}",

        "api-id":
            api_id
    }


    r = requests.post(

        url,

        headers=headers,

        json=body,

        timeout=HTTP_TIMEOUT
    )


    # 인증 만료 시 재시도
    if r.status_code in [
        401,
        403
    ]:

        get_kiwoom_token()

        wait_api_rate_limit()


        headers[
            "authorization"
        ] = (
            f"Bearer {ACCESS_TOKEN}"
        )


        r = requests.post(

            url,

            headers=headers,

            json=body,

            timeout=HTTP_TIMEOUT
        )


    try:

        data = r.json()

    except Exception:

        raise Exception(
            "JSON 응답 아님: "
            + r.text[:500]
        )


    if r.status_code != 200:

        raise Exception(

            f"HTTP "
            f"{r.status_code}: "
            f"{data}"
        )


    # 키움 자체 오류코드
    if (
        "return_code" in data
        and data.get(
            "return_code"
        ) not in [
            0,
            "0"
        ]
    ):

        raise Exception(
            f"키움 API 오류: {data}"
        )


    return data


# ============================================================
# 11. KA10027
# ============================================================

def get_change_rate_rank(
    market_code
):

    body = (
        CHANGE_RATE_REQUEST
        .copy()
    )


    body[
        "mrkt_tp"
    ] = market_code


    data = kiwoom_post(

        CHANGE_RATE_API_PATH,

        CHANGE_RATE_API_ID,

        body
    )


    return find_first_list(
        data
    )


# ============================================================
# 12. KA10027 정규화
# ============================================================

def normalize_change_row(
    row,
    market_name,
    rank
):

    raw_code = (
        first_existing(

            row,

            ["stk_cd"],

            ""
        )
    )


    price = abs_price(

        first_existing(

            row,

            ["cur_prc"],

            0
        )
    )


    volume = safe_int(

        first_existing(

            row,

            ["now_trde_qty"],

            0
        )
    )


    return {

        "market":
            market_name,

        "stock_code_raw":
            str(raw_code),

        "stock_code":
            clean_stock_code(
                raw_code
            ),

        "stock_name":
            str(
                first_existing(

                    row,

                    ["stk_nm"],

                    ""
                )
            ),

        "current_price":
            price,

        "change_rate":
            safe_float(

                first_existing(

                    row,

                    ["flu_rt"],

                    0
                )
            ),

        "volume":
            volume,

        "change_rank":
            rank,

        # fallback용 추정값
        "estimated_trading_value":
            price * volume
    }


# ============================================================
# 13. KA10032 거래대금 상위
# ============================================================

def get_trading_value_rank(
    market_code
):

    body = (
        TRADING_VALUE_REQUEST
        .copy()
    )


    body[
        "mrkt_tp"
    ] = market_code


    data = kiwoom_post(

        TRADING_VALUE_API_PATH,

        TRADING_VALUE_API_ID,

        body
    )


    return find_first_list(
        data
    )


# ============================================================
# 14. KA10032 Dictionary 만들기
# ============================================================

def build_actual_trading_value_map():

    """
    반환:

    {
        "005930": {
            "actual_trading_value": ...,
            "trading_value_rank": 1
        }
    }
    """


    value_map = {}


    for (
        market_code,
        market_name
    ) in MARKETS:


        try:

            rows = (
                get_trading_value_rank(
                    market_code
                )
            )


            log(

                f"{market_name} "
                f"KA10032 "
                f"{len(rows)}종목"
            )


            for row in rows:


                raw_code = (
                    row.get(
                        "stk_cd",
                        ""
                    )
                )


                code = (
                    clean_stock_code(
                        raw_code
                    )
                )


                # 실제 응답에서
                # trde_prica = 백만원
                raw_value = safe_float(

                    row.get(
                        "trde_prica",
                        0
                    )
                )


                actual_value = (
                    raw_value
                    * 1_000_000
                )


                rank = safe_int(

                    row.get(
                        "now_rank",
                        999
                    ),

                    999
                )


                if code:

                    value_map[
                        code
                    ] = {

                        "actual_trading_value":
                            actual_value,

                        "trading_value_rank":
                            rank
                    }


        except Exception as e:

            log(

                f"{market_name} "
                f"KA10032 오류: {e}"
            )


    return value_map


# ============================================================
# 15. 거래대금 실제/추정 결정
# ============================================================

def attach_trading_value(
    stock,
    actual_map
):

    code = stock[
        "stock_code"
    ]


    estimated = stock[
        "estimated_trading_value"
    ]


    actual_info = (
        actual_map.get(
            code
        )
    )


    if actual_info is not None:

        stock[
            "actual_trading_value"
        ] = actual_info[
            "actual_trading_value"
        ]


        stock[
            "estimated_trading_value"
        ] = estimated


        stock[
            "trading_value_used"
        ] = actual_info[
            "actual_trading_value"
        ]


        stock[
            "trading_value_source"
        ] = "ACTUAL"


        stock[
            "trading_value_rank"
        ] = actual_info[
            "trading_value_rank"
        ]


    else:

        stock[
            "actual_trading_value"
        ] = None


        stock[
            "estimated_trading_value"
        ] = estimated


        stock[
            "trading_value_used"
        ] = estimated


        stock[
            "trading_value_source"
        ] = "ESTIMATED"


        stock[
            "trading_value_rank"
        ] = None


# ============================================================
# 16. KA10001
# ============================================================

def get_stock_quote(
    stock_code
):

    body = {

        "stk_cd":
            clean_stock_code(
                stock_code
            )
    }


    return kiwoom_post(

        QUOTE_API_PATH,

        QUOTE_API_ID,

        body
    )


def get_stock_quote_exchange_code(
    exchange_stock_code
):
    """
    거래소 suffix를 보존해서 KA10001 조회.

    예)
    KRX : 005930
    NXT : 005930_NX
    SOR : 005930_AL
    """

    body = {
        "stk_cd":
            str(exchange_stock_code)
            .strip()
    }

    return kiwoom_post(
        QUOTE_API_PATH,
        QUOTE_API_ID,
        body
    )


def is_nxt_tradable(stock_code):
    """
    NXT 거래 가능 여부 확인.

    - 종목별 최초 1회만 확인하고 캐시 사용
    - NXT 코드(종목코드_NX)로 KA10001 조회
    - 키움이 해당 NXT 코드를 정상 응답하면 True
    - 종목코드 관련 키움 API 오류면 False
    - 네트워크/일시적 오류는 None(확인불가)
    """

    if not NXT_ELIGIBILITY_CHECK:
        return None

    code = clean_stock_code(
        stock_code
    )

    if code in nxt_eligibility_cache:
        return nxt_eligibility_cache[code]

    nxt_code = f"{code}_NX"

    try:
        data = get_stock_quote_exchange_code(
            nxt_code
        )

        # 정상적인 NXT 종목 응답이면 종목명 또는 현재가가 존재
        stock_name = str(
            data.get("stk_nm", "")
        ).strip()

        price = abs_price(
            data.get("cur_prc", 0)
        )

        result = bool(
            stock_name
            or price > 0
        )

        nxt_eligibility_cache[code] = result
        return result

    except Exception as e:
        message = str(e)

        # 유효하지 않은 NXT 종목코드 등 키움 자체 오류는
        # NXT 거래 불가로 처리하고 캐시
        if "키움 API 오류" in message:
            nxt_eligibility_cache[code] = False
            return False

        # 타임아웃/네트워크 등은 불가로 단정하지 않음
        log(
            f"[NXT 확인 오류] "
            f"{code} / {e}"
        )
        return None


def get_nxt_status_text(stock_code):
    tradable = is_nxt_tradable(
        stock_code
    )

    if tradable is True:
        return "NXT 거래 : ✅ 가능"

    if tradable is False:
        return "NXT 거래 : ❌ 불가"

    return "NXT 거래 : ⚠️ 확인불가"


def normalize_quote(data):

    return {

        "current_price":
            abs_price(
                data.get(
                    "cur_prc",
                    0
                )
            ),

        "day_high":
            abs_price(
                data.get(
                    "high_pric",
                    0
                )
            ),

        # 실제 응답에서 확인된 필드
        "volume":
            safe_int(
                data.get(
                    "trde_qty",
                    0
                )
            )
    }


# ============================================================
# 17. 제외종목
# ============================================================

def is_excluded_stock(stock):

    name = stock[
        "stock_name"
    ]

    upper = name.upper()


    if (
        EXCLUDE_ETN
        and "ETN" in upper
    ):

        return True


    if (
        EXCLUDE_SPAC
        and (
            "스팩" in name
            or "SPAC" in upper
        )
    ):

        return True


    if EXCLUDE_ETF:

        keywords = [

            "KODEX",
            "TIGER",
            "RISE ",
            "ACE ",
            "PLUS ",
            "SOL ",
            "HANARO",
            "KOSEF"
        ]


        if any(
            x in upper
            for x in keywords
        ):

            return True


    if EXCLUDE_PREFERRED:

        if (
            name.endswith("우")
            or name.endswith("우B")
            or name.endswith("우C")
        ):

            return True


    return False


# ============================================================
# 18. 사전필터
# ============================================================

def pass_pre_filter(stock):

    if is_excluded_stock(
        stock
    ):

        return False


    if not (

        MIN_CHANGE_RATE

        <= stock[
            "change_rate"
        ]

        <= MAX_CHANGE_RATE

    ):

        return False


    if (
        stock[
            "volume"
        ]
        < MIN_PRE_FILTER_VOLUME
    ):

        return False


    if (
        stock[
            "current_price"
        ]
        <= 0
    ):

        return False


    return True


# ============================================================
# 19. 고점 이격
# ============================================================

def calc_high_gap(
    price,
    day_high
):

    if (
        price <= 0
        or day_high <= 0
    ):

        return 999


    return (

        (day_high - price)

        / day_high

        * 100
    )



# ============================================================
# 19-A. v1.6.4 사전 가격 HISTORY / WATCH
# ============================================================

def _prune_price_history(code, now_ts=None):
    if now_ts is None:
        now_ts = time.time()

    rows = price_history.get(code, [])
    cutoff = now_ts - PRICE_HISTORY_RETENTION_SEC
    rows = [x for x in rows if x.get("ts", 0) >= cutoff]

    if rows:
        price_history[code] = rows
    else:
        price_history.pop(code, None)


def record_price_history(stock, stage="SCAN", now_ts=None):
    """이미 조회한 가격을 rolling history에 저장합니다. 추가 API 호출은 없습니다."""
    code = clean_stock_code(stock.get("stock_code", ""))
    price = safe_float(stock.get("current_price", 0))

    if not code or price <= 0:
        return

    if now_ts is None:
        now_ts = time.time()

    sample = {
        "ts": now_ts,
        "datetime": datetime.fromtimestamp(now_ts),
        "price": price,
        "high_gap": stock.get("high_gap"),
        "score": stock.get("score"),
        "change_rate": stock.get("change_rate"),
        "volume": stock.get("volume"),
        "stage": stage,
    }

    rows = price_history.setdefault(code, [])

    # 같은 스캔에서 KA10027 값 → KA10001/점수 값으로 풍부하게 갱신
    if rows and abs(now_ts - rows[-1]["ts"]) <= 3.0:
        old = rows[-1]
        old["ts"] = now_ts
        old["datetime"] = sample["datetime"]
        old["price"] = price
        for key in ["high_gap", "score", "change_rate", "volume"]:
            if sample.get(key) is not None:
                old[key] = sample[key]
        old["stage"] = stage
    else:
        rows.append(sample)

    _prune_price_history(code, now_ts)


def _history_tolerance_sec():
    return max(10.0, SCAN_INTERVAL_SEC * 1.75)


def _valid_high_gap_value(value):
    """None/빈값/999 sentinel은 제외하되 0.0%는 정상값으로 인정합니다."""
    if value is None:
        return None

    try:
        text = str(value).replace(",", "").strip()
        if text == "":
            return None
        x = float(text)
    except Exception:
        return None

    if x < 0 or x >= 900:
        return None

    return x



def _price_history_sample_near(
    code,
    target_ts,
    tolerance_sec=None,
    current_ts=None,
):
    """target 시각에 가장 가까운 과거 가격 샘플을 찾습니다.

    v1.6.4 핵심: current_ts가 주어지면 sample["ts"] < current_ts 인
    샘플만 후보로 사용합니다. 현재 샘플을 과거값으로 재사용하지 않습니다.
    """
    rows = [
        x for x in price_history.get(code, [])
        if safe_float(x.get("price", 0)) > 0
        and (
            current_ts is None
            or safe_float(x.get("ts", 0)) < current_ts
        )
    ]
    if not rows:
        return None

    if tolerance_sec is None:
        tolerance_sec = _history_tolerance_sec()

    best = min(rows, key=lambda x: abs(x.get("ts", 0) - target_ts))
    if abs(best.get("ts", 0) - target_ts) > tolerance_sec:
        return None
    return best


def _high_gap_history_sample_near(
    code,
    target_ts,
    tolerance_sec=None,
    current_ts=None,
):
    """target 시각에 가장 가까운 과거 high_gap 샘플을 찾습니다.

    v1.6.4 핵심: current_ts가 주어지면 sample["ts"] < current_ts 인
    샘플만 후보로 사용합니다.
    """
    rows = [
        x for x in price_history.get(code, [])
        if _valid_high_gap_value(x.get("high_gap")) is not None
        and (
            current_ts is None
            or safe_float(x.get("ts", 0)) < current_ts
        )
    ]
    if not rows:
        return None

    if tolerance_sec is None:
        tolerance_sec = _history_tolerance_sec()

    best = min(rows, key=lambda x: abs(x.get("ts", 0) - target_ts))
    if abs(best.get("ts", 0) - target_ts) > tolerance_sec:
        return None
    return best

def get_history_metrics(code, now_ts=None):
    code = clean_stock_code(code)
    rows = price_history.get(code, [])

    metrics = {
        "history_available_sec": 0.0,
        "history_sample_count": len(rows),
    }

    for sec in HISTORY_LOOKBACKS_SEC:
        metrics[f"price_change_{sec}s"] = None
        metrics[f"price_change_{sec}s_actual_sec"] = None

    for sec in [30, 60, 120, 180, 300]:
        metrics[f"high_gap_change_{sec}s"] = None
        metrics[f"high_gap_change_{sec}s_actual_sec"] = None

    if not rows:
        return metrics

    latest = rows[-1]
    if now_ts is None:
        now_ts = latest["ts"]

    first_ts = rows[0].get("ts", now_ts)
    metrics["history_available_sec"] = max(0.0, now_ts - first_ts)

    latest_price = safe_float(latest.get("price", 0))
    latest_hg = _valid_high_gap_value(latest.get("high_gap"))

    for sec in HISTORY_LOOKBACKS_SEC:
        if metrics["history_available_sec"] + 1e-9 < sec:
            continue

        old = _price_history_sample_near(
            code,
            now_ts - sec,
            current_ts=now_ts,
        )
        if old is None:
            continue

        old_price = safe_float(old.get("price", 0))
        if latest_price > 0 and old_price > 0:
            metrics[f"price_change_{sec}s"] = (
                (latest_price - old_price) / old_price * 100
            )
            metrics[f"price_change_{sec}s_actual_sec"] = max(
                0.0,
                now_ts - old.get("ts", now_ts)
            )

    for sec in [30, 60, 120, 180, 300]:
        old = _high_gap_history_sample_near(
            code,
            now_ts - sec,
            current_ts=now_ts,
        )
        if old is None:
            continue

        old_hg = _valid_high_gap_value(old.get("high_gap"))
        if latest_hg is None or old_hg is None:
            continue

        metrics[f"high_gap_change_{sec}s"] = latest_hg - old_hg
        metrics[f"high_gap_change_{sec}s_actual_sec"] = max(
            0.0,
            now_ts - old.get("ts", now_ts)
        )

    return metrics


def attach_history_metrics(stock):
    metrics = get_history_metrics(stock.get("stock_code", ""))
    stock.update(metrics)
    return metrics



def _stock_observation_time(stock):
    """기존 WATCH/history 호환용 관측시각: 스캔 샘플시각을 우선 사용합니다."""
    ts = stock.get("_scan_sample_ts")
    if ts is not None:
        try:
            return datetime.fromtimestamp(float(ts))
        except Exception:
            pass
    return datetime.now()


def _stock_score_time(stock):
    """KA10001 조회 + 점수 계산이 끝난 실제 판정시각을 반환합니다."""
    ts = stock.get("_score_evaluated_ts")
    if ts is not None:
        try:
            return datetime.fromtimestamp(float(ts))
        except Exception:
            pass
    return _stock_observation_time(stock)


def _stock_scan_start_time(stock):
    ts = stock.get("_scan_start_ts", stock.get("_scan_sample_ts"))
    if ts is not None:
        try:
            return datetime.fromtimestamp(float(ts))
        except Exception:
            pass
    return ""

def _new_watch_episode(stock, start_time=None):
    code = clean_stock_code(stock.get("stock_code", ""))
    if not code:
        return None

    if start_time is None:
        start_time = _stock_observation_time(stock)

    episode_no = watch_episode_counts.get(code, 0) + 1
    watch_episode_counts[code] = episode_no
    episode_id = (
        f"{start_time.strftime('%Y%m%d')}_{code}_E{episode_no:03d}"
    )

    # v1.6.6: first75/PRE/CONFIRM/Shadow의 "한 번" 상태는 Episode 단위입니다.
    # 이전 Episode의 paper trade 자체는 절대 삭제하지 않습니다.
    pre_first_75_states.pop(code, None)
    score_shadow_states.pop(code, None)
    confirm_pending.pop(code, None)
    confirm_started_today.discard(code)

    state = {
        "active": True,
        "episode_no": episode_no,
        "episode_id": episode_id,
        "start_time": start_time,
        "start_price": safe_float(stock.get("current_price", 0)),
        "start_score": safe_float(stock.get("score", 0)),
        "market": stock.get("market", ""),
        "last_observed_time": start_time,
        "last_score": safe_float(stock.get("score", 0)),
        "end_time": None,
        "end_reason": "",
    }
    watch_episode_states[code] = state

    log(
        f"[WATCH Episode 시작] {stock.get('stock_name', code)} / "
        f"{episode_id} / {state['start_score']:.0f}점"
    )
    return state



def register_watch_if_needed(stock):
    """기존 최초 WATCH와 신규 연속 Episode를 함께 관리합니다."""
    code = clean_stock_code(stock.get("stock_code", ""))
    score = safe_float(stock.get("score", 0))

    if not code or score < WATCH_SCORE:
        return False

    now = _stock_observation_time(stock)
    first_registered = False

    if code not in watch_states:
        watch_states[code] = {
            "watch_start_time": now,
            "watch_start_price": safe_float(stock.get("current_price", 0)),
            "watch_start_score": score,
            "market": stock.get("market", ""),
        }
        first_registered = True
        log(
            f"[WATCH 최초등록] {stock.get('stock_name', code)} / "
            f"{score:.0f}점 / {stock.get('current_price', 0):,.0f}원"
        )

    episode = watch_episode_states.get(code)
    if episode is None or not episode.get("active", False):
        episode = _new_watch_episode(stock, now)
    else:
        episode["last_observed_time"] = now
        episode["last_score"] = score
        if not episode.get("market"):
            episode["market"] = stock.get("market", "")

    return first_registered


def close_watch_episode(code, reason="CONDITION_EXIT", end_time=None):
    code = clean_stock_code(code)
    state = watch_episode_states.get(code)
    if not state or not state.get("active", False):
        return False

    if end_time is None:
        end_time = datetime.now()

    state["active"] = False
    state["end_time"] = end_time
    state["end_reason"] = reason

    log(
        f"[WATCH Episode 종료] {code} / {state.get('episode_id', '')} / {reason}"
    )
    return True


def update_watch_episodes_after_scan(observation_map):
    """
    정상적인 조건 이탈만 Episode를 종료합니다.
    KA10001/시장 API 오류 등 UNKNOWN은 Episode를 유지합니다.
    """
    for code, state in list(watch_episode_states.items()):
        if not state.get("active", False):
            continue

        obs = observation_map.get(code, {"status": "UNKNOWN", "reason": "NO_OBSERVATION"})
        status = obs.get("status")

        if status == "UNKNOWN":
            continue

        if status == "EVALUABLE":
            stock = obs.get("stock") or {}
            score = safe_float(stock.get("score", 0))
            if score >= WATCH_SCORE:
                state["last_observed_time"] = _stock_observation_time(stock)
                state["last_score"] = score
                continue
            close_watch_episode(code, "SCORE_BELOW_WATCH", _stock_observation_time(stock))
            continue

        if status == "FILTER_EXIT":
            close_watch_episode(code, obs.get("reason", "FILTER_EXIT"))


def attach_watch_metrics(stock, signal_time=None):
    code = clean_stock_code(stock.get("stock_code", ""))
    first_state = watch_states.get(code)
    episode = watch_episode_states.get(code)

    stock["watch_start_time"] = ""
    stock["watch_start_price"] = ""
    stock["watch_start_score"] = ""
    stock["watch_to_signal_sec"] = ""

    stock["watch_episode_id"] = ""
    stock["watch_episode_start_time"] = ""
    stock["watch_episode_start_price"] = ""
    stock["watch_episode_start_score"] = ""
    stock["watch_episode_to_signal_sec"] = ""

    if signal_time is None:
        signal_time = _stock_observation_time(stock)

    if first_state:
        start_time = first_state["watch_start_time"]
        stock["watch_start_time"] = start_time
        stock["watch_start_price"] = first_state["watch_start_price"]
        stock["watch_start_score"] = first_state["watch_start_score"]
        stock["watch_to_signal_sec"] = max(
            0.0,
            (signal_time - start_time).total_seconds()
        )

    if episode and episode.get("active", False):
        start_time = episode["start_time"]
        stock["watch_episode_id"] = episode.get("episode_id", "")
        stock["watch_episode_start_time"] = start_time
        stock["watch_episode_start_price"] = episode.get("start_price", "")
        stock["watch_episode_start_score"] = episode.get("start_score", "")
        stock["watch_episode_to_signal_sec"] = max(
            0.0,
            (signal_time - start_time).total_seconds()
        )



def evaluate_pre_history(stock):
    """PRE_HISTORY 판정을 PASS / FAIL / DATA_UNAVAILABLE로 구분합니다.

    전략 조건은 v1.6.3과 동일하며, 데이터 부족과 실제 조건 실패만 분리합니다.
    """
    history_sec = safe_float(stock.get("history_available_sec", 0))

    if history_sec < PRE_HISTORY_MIN_SEC:
        return "DATA_UNAVAILABLE", "INSUFFICIENT_HISTORY"

    p30 = stock.get("price_change_30s")
    p60 = stock.get("price_change_60s")
    hg60 = stock.get("high_gap_change_60s")

    if PRE_HISTORY_REQUIRE_30S_UP:
        if p30 is None:
            return "DATA_UNAVAILABLE", "NO_30S_PRICE"
        if p30 <= 0:
            return "FAIL", "PRICE_30S_NOT_POSITIVE"

    if PRE_HISTORY_REQUIRE_60S_UP:
        if p60 is None:
            return "DATA_UNAVAILABLE", "NO_60S_PRICE"
        if p60 <= 0:
            return "FAIL", "PRICE_60S_NOT_POSITIVE"

    if PRE_HISTORY_REQUIRE_HIGH_GAP_60S_DOWN:
        if hg60 is None:
            return "DATA_UNAVAILABLE", "NO_60S_HIGH_GAP"
        if hg60 >= 0:
            return "FAIL", "HIGH_GAP_60S_NOT_DECREASING"

    return "PASS", "OK"


def later_pass_origin_from_status(first_75_pre_status):
    if first_75_pre_status == "DATA_UNAVAILABLE":
        return "AFTER_DATA_UNAVAILABLE"
    if first_75_pre_status == "FAIL":
        return "AFTER_CONDITION_FAIL"
    return ""


def register_pre_first_75_if_needed(stock, signal_time=None):
    code = clean_stock_code(stock.get("stock_code", ""))
    if not code or code in pre_first_75_states:
        return pre_first_75_states.get(code)

    if safe_float(stock.get("score", 0)) < MIN_SIGNAL_SCORE:
        return None

    if signal_time is None:
        signal_time = _stock_score_time(stock)

    # v1.6.5: 세션 경계에서 발생한 75점 관측은 first_75 전략상태로 등록하지 않습니다.
    valid, _ = attach_session_decision_metrics(
        stock,
        stock.get("scan_session"),
        signal_time
    )
    if not valid:
        return None

    pre_status, reason = evaluate_pre_history(stock)

    p30 = stock.get("price_change_30s")
    first75_p30_positive = (
        bool(p30 > 0)
        if p30 is not None and p30 != ""
        else ""
    )

    prior_shadow = score_shadow_states.get(code) or {}
    prior_shadow_time = prior_shadow.get("shadow_time")
    prior_shadow_price = safe_float(prior_shadow.get("shadow_price", 0))
    first_price = safe_float(stock.get("current_price", 0))

    had_prior_shadow = (
        bool(prior_shadow)
        and isinstance(prior_shadow_time, datetime)
        and prior_shadow_time <= signal_time
    )

    prior_shadow_to_first75_sec = ""
    prior_shadow_to_first75_pct = ""

    if had_prior_shadow:
        prior_shadow_to_first75_sec = max(
            0.0,
            (signal_time - prior_shadow_time).total_seconds()
        )
        if prior_shadow_price > 0 and first_price > 0:
            prior_shadow_to_first75_pct = (
                (first_price / prior_shadow_price - 1) * 100
            )

    state = {
        "scan_start_time": _stock_scan_start_time(stock),
        "scan_session": stock.get("scan_session", ""),
        "first_75_time": signal_time,
        "first_75_price": first_price,
        "first_75_score": safe_float(stock.get("score", 0)),
        # 기존 분석 호환: result는 PASS/FAIL 이진값 유지
        "first_75_pre_result": "PASS" if pre_status == "PASS" else "FAIL",
        "first_75_pre_status": pre_status,
        "first_75_pre_reason": reason,
        "first75_price_30s_positive": first75_p30_positive,
        "had_prior_shadow_70_74": had_prior_shadow,
        "prior_shadow_trade_id": prior_shadow.get("shadow_trade_id", "") if had_prior_shadow else "",
        "prior_shadow_time": prior_shadow_time if had_prior_shadow else "",
        "prior_shadow_price": prior_shadow.get("shadow_price", "") if had_prior_shadow else "",
        "prior_shadow_score": prior_shadow.get("shadow_score", "") if had_prior_shadow else "",
        "prior_shadow_to_first75_sec": prior_shadow_to_first75_sec,
        "prior_shadow_to_first75_pct": prior_shadow_to_first75_pct,
    }
    pre_first_75_states[code] = state
    return state


def attach_pre_first_75_metrics(stock):
    code = clean_stock_code(stock.get("stock_code", ""))
    state = pre_first_75_states.get(code) or {}

    first_time = state.get("first_75_time")
    stock["scan_start_time"] = state.get(
        "scan_start_time",
        _stock_scan_start_time(stock)
    )
    stock["first_75_time"] = first_time or ""
    stock["first_75_price"] = state.get("first_75_price", "")
    stock["first_75_score"] = state.get("first_75_score", "")
    stock["first_75_pre_result"] = state.get("first_75_pre_result", "")
    stock["first_75_pre_status"] = state.get("first_75_pre_status", "")
    stock["first_75_pre_reason"] = state.get("first_75_pre_reason", "")
    stock["first75_price_30s_positive"] = state.get(
        "first75_price_30s_positive", ""
    )
    stock["had_prior_shadow_70_74"] = state.get(
        "had_prior_shadow_70_74", False
    )
    stock["prior_shadow_trade_id"] = state.get("prior_shadow_trade_id", "")
    stock["prior_shadow_time"] = state.get("prior_shadow_time", "")
    stock["prior_shadow_price"] = state.get("prior_shadow_price", "")
    stock["prior_shadow_score"] = state.get("prior_shadow_score", "")
    stock["prior_shadow_to_first75_sec"] = state.get(
        "prior_shadow_to_first75_sec", ""
    )
    stock["prior_shadow_to_first75_pct"] = state.get(
        "prior_shadow_to_first75_pct", ""
    )



def _optional_positive(value):
    if value is None or value == "":
        return ""
    return bool(safe_float(value) > 0)


def attach_analysis_flags(stock):
    stock["price_30s_positive"] = _optional_positive(
        stock.get("price_change_30s")
    )
    stock["price_60s_positive"] = _optional_positive(
        stock.get("price_change_60s")
    )
    if "first75_price_30s_positive" not in stock:
        stock["first75_price_30s_positive"] = ""
    return stock


def attach_entry_cost_metrics(stock, decision_time=None, signal_price=None):
    """
    first_75 실제 판정시각/가격 대비 현재 진입판정의 지연과 가격차를 계산합니다.
    PAPER_ENTRY_SLIPPAGE가 반영된 entry_price가 아니라 signal/current price를 사용합니다.
    """
    if decision_time is None:
        decision_time = _stock_score_time(stock)

    if signal_price is None:
        signal_price = safe_float(stock.get("current_price", 0))

    stock["entry_decision_time"] = decision_time
    stock["entry_signal_price"] = signal_price
    stock["entry_delay_from_first75_sec"] = ""
    stock["entry_vs_first75_pct"] = ""

    first_time = stock.get("first_75_time")
    first_price = safe_float(stock.get("first_75_price", 0))

    if isinstance(first_time, datetime) and isinstance(decision_time, datetime):
        stock["entry_delay_from_first75_sec"] = max(
            0.0,
            (decision_time - first_time).total_seconds()
        )

    if first_price > 0 and signal_price > 0:
        stock["entry_vs_first75_pct"] = (
            (signal_price / first_price - 1) * 100
        )

    attach_analysis_flags(stock)
    return stock


def _current_watch_episode_id(code, stock=None):
    code = clean_stock_code(code)

    if stock is not None:
        episode_id = str(stock.get("watch_episode_id", "") or "").strip()
        if episode_id:
            return episode_id

    episode = watch_episode_states.get(code) or {}
    if episode.get("active", False):
        episode_id = str(episode.get("episode_id", "") or "").strip()
        if episode_id:
            return episode_id

    # 테스트/수동호출 호환용. 정상 스캔 진입은 WATCH Episode가 항상 존재합니다.
    return "NO_EPISODE"


def make_trade_id(code, entry_mode, episode_id=None):
    now = datetime.now()
    episode_id = episode_id or _current_watch_episode_id(code)
    episode_tag = str(episode_id).split("_")[-1] if episode_id else "NOEP"
    return (
        f"{now.strftime('%Y%m%d')}_"
        f"{clean_stock_code(code)}_"
        f"{entry_mode}_{episode_tag}_"
        f"{now.strftime('%H%M%S%f')}"
    )



def paper_entry_key(code, entry_mode, episode_id=None):
    code = clean_stock_code(code)
    episode_id = episode_id or _current_watch_episode_id(code)
    return (
        str(entry_mode),
        code,
        str(episode_id),
    )



def has_paper_entered_today(code, entry_mode, episode_id=None):
    return paper_entry_key(code, entry_mode, episode_id) in paper_entered_today


def _research_mode_label(entry_mode, entry_meta=None, stock=None):
    entry_meta = entry_meta or {}
    stock = stock or {}
    pre_entry_type = (
        entry_meta.get("pre_entry_type")
        or stock.get("pre_entry_type")
        or ""
    )
    if entry_mode == "PRE_HISTORY" and pre_entry_type:
        return f"PRE_HISTORY:{pre_entry_type}"
    return str(entry_mode)


def _preview_paper_reentry_metadata(stock, entry_mode, entry_meta=None):
    code = clean_stock_code(stock.get("stock_code", ""))
    mode_label = _research_mode_label(entry_mode, entry_meta, stock)

    stock_seq = int(paper_stock_entry_counts_today.get(code, 0)) + 1
    mode_key = (code, mode_label)
    mode_seq = int(paper_mode_entry_counts_today.get(mode_key, 0)) + 1

    previous_trade_id = paper_last_trade_id_by_mode.get(mode_key, "")
    previous_result = ""
    if previous_trade_id:
        previous = paper_trade_registry.get(previous_trade_id, {})
        previous_result = previous.get("reference_result", "OPEN") or "OPEN"

    return {
        "stock_entry_seq_today": stock_seq,
        "mode_entry_seq_today": mode_seq,
        "is_reentry": mode_seq > 1,
        "previous_same_mode_result": previous_result,
        "previous_same_mode_trade_id": previous_trade_id,
        "research_mode_label": mode_label,
    }


def _commit_paper_reentry_metadata(stock, entry_mode, trade_id, entry_meta=None):
    meta = _preview_paper_reentry_metadata(stock, entry_mode, entry_meta)
    code = clean_stock_code(stock.get("stock_code", ""))
    mode_label = meta["research_mode_label"]
    mode_key = (code, mode_label)

    paper_stock_entry_counts_today[code] = meta["stock_entry_seq_today"]
    paper_mode_entry_counts_today[mode_key] = meta["mode_entry_seq_today"]
    paper_last_trade_id_by_mode[mode_key] = trade_id

    paper_trade_registry[trade_id] = {
        "stock_code": code,
        "entry_mode": entry_mode,
        "research_mode_label": mode_label,
        "pre_entry_type": (entry_meta or {}).get("pre_entry_type", ""),
        "watch_episode_id": _current_watch_episode_id(code, stock),
        "reference_result": "OPEN",
        "reference_return_pct": "",
        **meta,
    }
    return meta


def _update_paper_reference_outcome(position, strategy_name, strategy):
    if strategy_name != POST_EXIT_REFERENCE_STRATEGY:
        return

    trade_id = position.get("trade_id", "")
    if not trade_id:
        return

    entry = safe_float(position.get("entry_price", 0))
    exit_price = safe_float(strategy.get("exit_price", 0))
    ret = ""
    if entry > 0 and exit_price > 0:
        ret = (exit_price / entry - 1) * 100

    rec = paper_trade_registry.setdefault(trade_id, {})
    rec["reference_result"] = strategy.get("result", "")
    rec["reference_return_pct"] = ret


def get_paper_reference_outcome(trade_id):
    if not trade_id:
        return "", ""

    rec = paper_trade_registry.get(trade_id, {})
    result = rec.get("reference_result", "")
    ret = rec.get("reference_return_pct", "")

    if result:
        return result, ret

    p = paper_positions.get(trade_id)
    if not p:
        return "", ""

    strategy = (p.get("strategies") or {}).get(POST_EXIT_REFERENCE_STRATEGY, {})
    if strategy.get("status") == "CLOSED":
        entry = safe_float(p.get("entry_price", 0))
        exit_price = safe_float(strategy.get("exit_price", 0))
        ret = (exit_price / entry - 1) * 100 if entry > 0 and exit_price > 0 else ""
        return strategy.get("result", ""), ret

    return "OPEN", ""



ENTRY_DECISION_COLUMNS = [
    "datetime", "version", "stock_code", "stock_name",
    "entry_mode", "decision", "reason", "score", "current_price", "high_gap",
    "scan_session", "decision_session", "decision_time", "session_valid_at_decision",
    "history_available_sec", "history_sample_count",
    "price_change_15s", "price_change_15s_actual_sec",
    "price_change_30s", "price_change_30s_actual_sec",
    "price_change_60s", "price_change_60s_actual_sec",
    "price_change_120s", "price_change_120s_actual_sec",
    "price_change_180s", "price_change_180s_actual_sec",
    "price_change_300s", "price_change_300s_actual_sec",
    "high_gap_change_30s", "high_gap_change_30s_actual_sec",
    "high_gap_change_60s", "high_gap_change_60s_actual_sec",
    "high_gap_change_120s", "high_gap_change_120s_actual_sec",
    "high_gap_change_180s", "high_gap_change_180s_actual_sec",
    "high_gap_change_300s", "high_gap_change_300s_actual_sec",
    "price_30s_positive", "price_60s_positive", "first75_price_30s_positive",
    "watch_start_time", "watch_start_price", "watch_start_score", "watch_to_signal_sec",
    "watch_episode_id", "watch_episode_start_time", "watch_episode_start_price",
    "watch_episode_start_score", "watch_episode_to_signal_sec",
    "scan_start_time", "first_75_time", "first_75_price", "first_75_score",
    "first_75_pre_result", "first_75_pre_status", "first_75_pre_reason",
    "entry_decision_time", "entry_signal_price",
    "entry_delay_from_first75_sec", "entry_vs_first75_pct",
    "pre_status", "pre_entry_type", "later_pass_origin",
    "first_75_to_pre_entry_sec", "pre_history_rule",
    "first_signal_time", "first_signal_price", "confirm_delay_sec", "confirm_rise_pct",
    "confirm_observation_status", "confirm_observation_reason",
    "had_prior_shadow_70_74", "prior_shadow_trade_id",
    "prior_shadow_time", "prior_shadow_price", "prior_shadow_score",
    "prior_shadow_to_first75_sec", "prior_shadow_to_first75_pct",
    "stock_entry_seq_today", "mode_entry_seq_today", "is_reentry",
    "previous_same_mode_result", "previous_same_mode_trade_id",
]


def _csv_datetime(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return value if value is not None else ""



def save_entry_decision(stock, entry_mode, decision, reason="", extra=None):
    extra = extra or {}

    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "version": STRATEGY_VERSION,
        "stock_code": stock.get("stock_code", ""),
        "stock_name": stock.get("stock_name", ""),
        "entry_mode": entry_mode,
        "decision": decision,
        "reason": reason,
        "score": stock.get("score", ""),
        "current_price": stock.get("current_price", ""),
        "high_gap": stock.get("high_gap", ""),
        "scan_session": stock.get("scan_session", ""),
        "decision_session": stock.get("decision_session", ""),
        "decision_time": _csv_datetime(stock.get("decision_time", "")),
        "session_valid_at_decision": stock.get("session_valid_at_decision", ""),
        "history_available_sec": stock.get("history_available_sec", ""),
        "history_sample_count": stock.get("history_sample_count", ""),
        "price_30s_positive": stock.get("price_30s_positive", ""),
        "price_60s_positive": stock.get("price_60s_positive", ""),
        "first75_price_30s_positive": stock.get("first75_price_30s_positive", ""),
        "entry_decision_time": _csv_datetime(stock.get("entry_decision_time", "")),
        "entry_signal_price": stock.get("entry_signal_price", ""),
        "entry_delay_from_first75_sec": stock.get("entry_delay_from_first75_sec", ""),
        "entry_vs_first75_pct": stock.get("entry_vs_first75_pct", ""),
        "had_prior_shadow_70_74": stock.get("had_prior_shadow_70_74", ""),
        "prior_shadow_trade_id": stock.get("prior_shadow_trade_id", ""),
        "prior_shadow_time": _csv_datetime(stock.get("prior_shadow_time", "")),
        "prior_shadow_price": stock.get("prior_shadow_price", ""),
        "prior_shadow_score": stock.get("prior_shadow_score", ""),
        "prior_shadow_to_first75_sec": stock.get("prior_shadow_to_first75_sec", ""),
        "prior_shadow_to_first75_pct": stock.get("prior_shadow_to_first75_pct", ""),
    }

    for sec in HISTORY_LOOKBACKS_SEC:
        row[f"price_change_{sec}s"] = stock.get(f"price_change_{sec}s", "")
        row[f"price_change_{sec}s_actual_sec"] = stock.get(
            f"price_change_{sec}s_actual_sec", ""
        )

    for sec in [30, 60, 120, 180, 300]:
        row[f"high_gap_change_{sec}s"] = stock.get(f"high_gap_change_{sec}s", "")
        row[f"high_gap_change_{sec}s_actual_sec"] = stock.get(
            f"high_gap_change_{sec}s_actual_sec", ""
        )

    for key in [
        "watch_start_time", "watch_start_price", "watch_start_score", "watch_to_signal_sec",
        "watch_episode_id", "watch_episode_start_time", "watch_episode_start_price",
        "watch_episode_start_score", "watch_episode_to_signal_sec",
        "scan_start_time", "first_75_time", "first_75_price", "first_75_score",
        "first_75_pre_result", "first_75_pre_status", "first_75_pre_reason",
    ]:
        row[key] = _csv_datetime(stock.get(key, ""))

    for key, value in extra.items():
        if key in ENTRY_DECISION_COLUMNS:
            row[key] = _csv_datetime(value)

    # ENTER 결정행에서도 실제 생성될 재진입 순번을 바로 분석할 수 있게 기록합니다.
    if decision == "ENTER":
        preview = _preview_paper_reentry_metadata(stock, entry_mode, extra)
        for key in [
            "stock_entry_seq_today", "mode_entry_seq_today", "is_reentry",
            "previous_same_mode_result", "previous_same_mode_trade_id",
        ]:
            row.setdefault(key, preview.get(key, ""))
            if row.get(key, "") == "":
                row[key] = preview.get(key, "")

    fixed_row = {col: row.get(col, "") for col in ENTRY_DECISION_COLUMNS}
    pd.DataFrame([fixed_row], columns=ENTRY_DECISION_COLUMNS).to_csv(
        PAPER_ENTRY_DECISION_FILE,
        mode="a",
        header=not os.path.exists(PAPER_ENTRY_DECISION_FILE),
        index=False,
        encoding="utf-8-sig"
    )


def _prune_growth_history(history, now_ts):

    keep_sec = max(
        GROWTH_LOOKBACK_SEC * 3,
        180
    )

    cutoff = now_ts - keep_sec

    while (
        history
        and history[0]["ts"] < cutoff
    ):
        history.pop(0)


def calc_volume_growth(
    code,
    volume
):

    now_ts = time.time()

    history = previous_volume.setdefault(
        code,
        []
    )

    target_ts = (
        now_ts
        - GROWTH_LOOKBACK_SEC
    )

    old_value = None

    # 60초 전(또는 그 이전) 중 가장 최근 값을 사용
    for item in reversed(history):
        if item["ts"] <= target_ts:
            old_value = item["value"]
            break

    history.append({
        "ts": now_ts,
        "value": volume
    })

    _prune_growth_history(
        history,
        now_ts
    )

    if (
        old_value is None
        or old_value <= 0
    ):
        return 1.0

    return (
        volume
        / old_value
    )


# ============================================================
# 21. 거래대금 증가
#
# 실제↔추정 값이 섞이지 않도록 같은 source만 비교합니다.
# 스캔은 15초마다 하더라도 증가율은 GROWTH_LOOKBACK_SEC 기준입니다.
# ============================================================

def calc_value_growth(
    code,
    source,
    value
):

    now_ts = time.time()

    history = previous_trading_value.setdefault(
        code,
        []
    )

    target_ts = (
        now_ts
        - GROWTH_LOOKBACK_SEC
    )

    old_value = None

    for item in reversed(history):
        if (
            item["ts"] <= target_ts
            and item["source"] == source
        ):
            old_value = item["value"]
            break

    history.append({
        "ts": now_ts,
        "source": source,
        "value": value
    })

    _prune_growth_history(
        history,
        now_ts
    )

    if (
        old_value is None
        or old_value <= 0
    ):
        return 1.0

    return (
        value
        / old_value
    )


# ============================================================
# 22. 점수
# ============================================================

def calculate_score(stock):

    """
    최종 점수는 4개 요소만 사용합니다.

    1) 거래대금
    2) 당일 고점 근접도
    3) 거래대금 증가
    4) 거래량 증가

    등락률은 MIN_CHANGE_RATE ~ MAX_CHANGE_RATE 범위 안에
    들어오는지 여부만 pass_pre_filter()에서 확인합니다.

    따라서 예를 들어 3~15%, 5~20% 등으로 범위를 바꿔도
    이 함수는 수정할 필요가 없습니다.
    """


    # --------------------------------------------------------
    # ① 거래대금
    #
    # MIN_TRADING_VALUE_WON을 기준으로 배수를 사용합니다.
    # 기본값이 200억원이면:
    #   1배   = 200억
    #   1.5배 = 300억
    #   2.5배 = 500억
    #   3.5배 = 700억
    #   5배   = 1,000억
    #
    # 최소 거래대금 설정을 바꿔도 점수 구간이 자동으로 따라갑니다.
    # --------------------------------------------------------

    value = stock["trading_value_used"]
    min_value = MIN_TRADING_VALUE_WON

    if value >= min_value * 5.0:
        value_ratio = 1.00

    elif value >= min_value * 3.5:
        value_ratio = 0.92

    elif value >= min_value * 2.5:
        value_ratio = 0.83

    elif value >= min_value * 1.5:
        value_ratio = 0.72

    elif value >= min_value:
        value_ratio = 0.60

    else:
        value_ratio = 0.00

    s_value = round(
        WEIGHT_TRADING_VALUE
        * value_ratio
    )


    # --------------------------------------------------------
    # ② 당일 고점 근접도
    #
    # MAX_HIGH_GAP을 기준으로 상대 구간을 사용합니다.
    # 기본값이 3%이면:
    #   0.5% 이내 → 100%
    #   1.0% 이내 → 90%
    #   2.0% 이내 → 75%
    #   3.0% 이내 → 55%
    #
    # MAX_HIGH_GAP을 바꿔도 자동으로 따라갑니다.
    # --------------------------------------------------------

    hg = stock["high_gap"]

    if hg <= MAX_HIGH_GAP / 6:
        high_ratio = 1.00

    elif hg <= MAX_HIGH_GAP / 3:
        high_ratio = 0.90

    elif hg <= MAX_HIGH_GAP * 2 / 3:
        high_ratio = 0.75

    elif hg <= MAX_HIGH_GAP:
        high_ratio = 0.55

    else:
        high_ratio = 0.00

    s_high = round(
        WEIGHT_HIGH_POSITION
        * high_ratio
    )


    # --------------------------------------------------------
    # ③ 거래대금 증가
    # --------------------------------------------------------

    vg = stock["value_growth"]

    if vg >= 1.30:
        value_growth_ratio = 1.00

    elif vg >= 1.15:
        value_growth_ratio = 0.80

    elif vg >= 1.05:
        value_growth_ratio = 0.53

    else:
        value_growth_ratio = 0.27

    s_vg = round(
        WEIGHT_VALUE_GROWTH
        * value_growth_ratio
    )


    # --------------------------------------------------------
    # ④ 거래량 증가
    # --------------------------------------------------------

    vol_g = stock["volume_growth"]

    if vol_g >= 1.30:
        volume_growth_ratio = 1.00

    elif vol_g >= 1.15:
        volume_growth_ratio = 0.80

    elif vol_g >= 1.05:
        volume_growth_ratio = 0.60

    else:
        volume_growth_ratio = 0.30

    s_vol = round(
        WEIGHT_VOLUME_GROWTH
        * volume_growth_ratio
    )


    # --------------------------------------------------------
    # 총점
    # --------------------------------------------------------

    total = (
        s_value
        + s_high
        + s_vg
        + s_vol
    )


    # 분석용 상세점수도 함께 보관
    stock["score_detail"] = {
        "trading_value": s_value,
        "high_position": s_high,
        "value_growth": s_vg,
        "volume_growth": s_vol
    }


    return total


# ============================================================
# 23. Telegram
# ============================================================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/"
        f"sendMessage"
    )

    all_success = True

    for chat_id in TELEGRAM_CHAT_IDS:

        payload = {
            "chat_id": chat_id,
            "text": message
        }

        try:

            r = requests.post(
                url,
                data=payload,
                timeout=HTTP_TIMEOUT
            )

            result = r.json()

            if not result.get("ok"):

                log(
                    f"Telegram 실패 "
                    f"[{chat_id}]: {result}"
                )

                all_success = False

        except Exception as e:

            log(
                f"Telegram 오류 "
                f"[{chat_id}]: {e}"
            )

            all_success = False

    return all_success


# ============================================================
# 24. 세션
# ============================================================

def _hhmm_time(value):
    return datetime.strptime(
        str(value).strip(),
        "%H:%M"
    ).time()


def get_session_at(moment=None):
    """
    초 단위 실제 시각으로 세션을 판정합니다.
    시작은 inclusive, 종료는 exclusive입니다.

    예) MAIN: 09:00:00 <= t < 15:30:00
    """
    if moment is None:
        moment = datetime.now()

    if not isinstance(moment, datetime):
        raise TypeError("moment는 datetime이어야 합니다.")

    t = moment.time()

    if _hhmm_time(NXT_PRE_START) <= t < _hhmm_time(NXT_PRE_END):
        return "NXT_PRE"

    if _hhmm_time(MAIN_START) <= t < _hhmm_time(MAIN_END):
        return "MAIN"

    if _hhmm_time(NXT_AFTER_START) <= t < _hhmm_time(NXT_AFTER_END):
        return "NXT_AFTER"

    return "WAIT"


def get_session():
    return get_session_at(datetime.now())


def is_entry_session_valid(decision_time, expected_session):
    """
    신규진입 직전 세션 안전장치.

    - decision_time 실제 초 단위 시각이 expected_session 안에 있어야 함
    - scan 시작 세션(expected_session)과 decision 세션이 같아야 함
    """
    if not isinstance(decision_time, datetime):
        return False

    if expected_session not in {"NXT_PRE", "MAIN", "NXT_AFTER"}:
        return False

    return get_session_at(decision_time) == expected_session


def attach_session_decision_metrics(stock, scan_session=None, decision_time=None):
    if decision_time is None:
        decision_time = _stock_score_time(stock)

    if scan_session is None:
        scan_session = stock.get("scan_session")
        if not scan_session:
            scan_start = _stock_scan_start_time(stock)
            scan_session = (
                get_session_at(scan_start)
                if isinstance(scan_start, datetime)
                else "WAIT"
            )

    decision_session = (
        get_session_at(decision_time)
        if isinstance(decision_time, datetime)
        else "WAIT"
    )

    valid = is_entry_session_valid(
        decision_time,
        scan_session
    )

    stock["scan_session"] = scan_session
    stock["decision_time"] = decision_time
    stock["decision_session"] = decision_session
    stock["session_valid_at_decision"] = bool(valid)

    if valid:
        stock["session_guard_reason"] = "OK"
    elif decision_session == "WAIT":
        stock["session_guard_reason"] = "SESSION_CLOSED_AT_DECISION"
    elif scan_session != decision_session:
        stock["session_guard_reason"] = "SESSION_CHANGED_DURING_SCAN"
    else:
        stock["session_guard_reason"] = "SESSION_CLOSED_AT_DECISION"

    return valid, stock["session_guard_reason"]


# ============================================================
# 25. 알림 가능 여부
# ============================================================

def can_alert(code):

    global daily_alert_count


    if (
        daily_alert_count
        >= MAX_ALERTS_PER_DAY
    ):

        return False


    last = (
        last_alert_time
        .get(code)
    )


    if last is None:

        return True


    return (

        datetime.now()
        - last

        >= timedelta(
            minutes=
            ALERT_COOLDOWN_MIN
        )
    )


# ============================================================
# 25-A. v1.6.1 WebSocket / 실제 자동매매
# ============================================================

def get_websocket_url():

    if USE_MOCK:
        return (
            "wss://mockapi.kiwoom.com:10000"
            "/api/dostk/websocket"
        )

    return (
        "wss://api.kiwoom.com:10000"
        "/api/dostk/websocket"
    )


def realtime_item_code(
    stock_code,
    session=None
):

    code = clean_stock_code(
        stock_code
    )

    if session is None:
        session = get_session()

    # MAIN에서는 통합 SOR 체결을 사용
    if session == "MAIN":
        return f"{code}_AL"

    # NXT 프리/애프터는 NXT 코드
    if session in [
        "NXT_PRE",
        "NXT_AFTER"
    ]:
        return f"{code}_NX"

    return code


def is_realtime_price_fresh(code):

    code = clean_stock_code(code)

    ts = realtime_price_ts.get(code)

    if ts is None:
        return False

    return (
        time.time() - ts
        <= WEBSOCKET_STALE_SEC
    )


def get_realtime_price(code):

    code = clean_stock_code(code)

    if not is_realtime_price_fresh(code):
        return None

    price = realtime_prices.get(code)

    if price is None or price <= 0:
        return None

    return price


def is_focus_signal(stock):
    """
    최근 데이터 분석용 표시.
    가상매매 진입 자체를 막지는 않습니다.
    """

    now = datetime.now().strftime(
        "%H:%M"
    )

    return (
        LIVE_ENTRY_START
        <= now
        <= LIVE_ENTRY_END
        and stock.get(
            "high_gap",
            999
        ) <= LIVE_MAX_HIGH_GAP
    )


def validate_scanner_config():

    if not KIWOOM_APP_KEY:
        raise ValueError(".env의 KIWOOM_APP_KEY가 비어 있습니다.")

    if not KIWOOM_SECRET_KEY:
        raise ValueError(".env의 KIWOOM_SECRET_KEY가 비어 있습니다.")

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(".env의 TELEGRAM_BOT_TOKEN이 비어 있습니다.")

    if not TELEGRAM_CHAT_IDS:
        raise ValueError(
            "활성화된 Telegram CHAT ID가 없습니다. "
            ".env의 TELEGRAM_SEND_PERSONAL / TELEGRAM_SEND_GROUP 설정을 확인하세요."
        )

    if KA10001_MAX_WORKERS <= 0:
        raise ValueError("KA10001_MAX_WORKERS는 1 이상이어야 합니다.")

    if SCAN_INTERVAL_SEC <= 0:
        raise ValueError("SCAN_INTERVAL_SEC는 0보다 커야 합니다.")

    if GROWTH_LOOKBACK_SEC <= 0:
        raise ValueError("GROWTH_LOOKBACK_SEC는 0보다 커야 합니다.")

    if GROWTH_LOOKBACK_SEC < SCAN_INTERVAL_SEC:
        raise ValueError("GROWTH_LOOKBACK_SEC는 SCAN_INTERVAL_SEC 이상이어야 합니다.")

    if not (0 <= WATCH_SCORE <= 100):
        raise ValueError("WATCH_SCORE는 0~100 범위여야 합니다.")

    if not (0 <= MIN_SIGNAL_SCORE <= 100):
        raise ValueError("MIN_SIGNAL_SCORE는 0~100 범위여야 합니다.")

    if WATCH_SCORE >= MIN_SIGNAL_SCORE:
        raise ValueError("WATCH_SCORE는 MIN_SIGNAL_SCORE보다 낮아야 합니다.")

    if PRICE_HISTORY_RETENTION_SEC < max(HISTORY_LOOKBACKS_SEC):
        raise ValueError("PRICE_HISTORY_RETENTION_SEC가 최대 HISTORY_LOOKBACK보다 짧습니다.")

    if PRE_HISTORY_MIN_SEC <= 0:
        raise ValueError("PRE_HISTORY_MIN_SEC는 0보다 커야 합니다.")

    if CONFIRM_TIMEOUT_SEC <= 0:
        raise ValueError("CONFIRM_TIMEOUT_SEC는 0보다 커야 합니다.")

    if not (
        0 <= SHADOW_SCORE_MIN <= SHADOW_SCORE_MAX < MIN_SIGNAL_SCORE
    ):
        raise ValueError(
            "SHADOW_SCORE_MIN/MAX는 0 이상이며 MIN_SIGNAL_SCORE보다 낮은 범위여야 합니다."
        )

    if ENTRY_PATH_TRACKING_ENABLED and not ENTRY_PATH_HORIZONS_SEC:
        raise ValueError("ENTRY_PATH_HORIZONS_SEC가 비어 있습니다.")

    if ENTRY_PATH_HORIZONS_SEC and max(ENTRY_PATH_HORIZONS_SEC) > PRICE_HISTORY_RETENTION_SEC:
        # history 보관시간과 직접 연동되지는 않지만 설정 실수를 조기에 알립니다.
        pass

    if WEBSOCKET_REG_INTERVAL_SEC < 0:
        raise ValueError("WEBSOCKET_REG_INTERVAL_SEC는 0 이상이어야 합니다.")

    weight_sum = (
        WEIGHT_TRADING_VALUE
        + WEIGHT_HIGH_POSITION
        + WEIGHT_VALUE_GROWTH
        + WEIGHT_VOLUME_GROWTH
    )

    if weight_sum != 100:
        raise ValueError(f"점수 가중치 합계가 100이 아닙니다: {weight_sum}")

    if MIN_CHANGE_RATE > MAX_CHANGE_RATE:
        raise ValueError("MIN_CHANGE_RATE가 MAX_CHANGE_RATE보다 큽니다.")

    # v1.6.6 인수인계 핵심 연구조건 회귀 방지
    if WATCH_SCORE != 60 or MIN_SIGNAL_SCORE != 75:
        raise ValueError("WATCH/SIGNAL 기준이 v1.6.6 연구조건과 다릅니다.")
    if SCAN_INTERVAL_SEC != 15 or API_MIN_INTERVAL_SEC != 0.25:
        raise ValueError("SCAN/API 간격이 v1.6.6 연구조건과 다릅니다.")
    if GROWTH_LOOKBACK_SEC != 60:
        raise ValueError("GROWTH_LOOKBACK_SEC는 60초여야 합니다.")
    if len(EXIT_STRATEGIES) != 169:
        raise ValueError("TP/SL 연구 grid는 169개여야 합니다.")

    return True


def validate_live_trading_config():

    if LIVE_ENTRY_MODE != "FIRST_75_PASS":
        raise ValueError(
            "v1.6.7 LIVE_ENTRY_MODE는 FIRST_75_PASS로 고정해야 합니다."
        )

    if LIVE_STRATEGY != "T200_S150":
        raise ValueError(
            "v1.6.7 LIVE_STRATEGY는 T200_S150(+2/-1.5)로 고정해야 합니다."
        )

    if LIVE_STRATEGY not in EXIT_STRATEGIES:
        raise ValueError("LIVE_STRATEGY가 연구 grid에 없습니다.")

    if LIVE_TRADE_AMOUNT_WON <= 0:
        raise ValueError("LIVE_TRADE_AMOUNT_WON은 1원 이상이어야 합니다.")

    if LIVE_MAX_STOCKS != 5:
        raise ValueError("v1.6.7 첫 실전검증은 LIVE_MAX_STOCKS=5로 유지합니다.")

    if LIVE_TOTAL_BUDGET_WON <= 0:
        raise ValueError("LIVE_TOTAL_BUDGET_WON은 1원 이상이어야 합니다.")

    if LIVE_TOTAL_BUDGET_WON < LIVE_TRADE_AMOUNT_WON:
        raise ValueError("총 운용예산이 종목당 매수예산보다 작습니다.")

    if LIVE_DAILY_MAX_LOSS_WON <= 0:
        raise ValueError("LIVE_DAILY_MAX_LOSS_WON은 1원 이상이어야 합니다.")

    if LIVE_MARKET_ORDER_BUFFER_PCT < 0:
        raise ValueError("LIVE_MARKET_ORDER_BUFFER_PCT는 0 이상이어야 합니다.")

    rule = EXIT_STRATEGIES[LIVE_STRATEGY]
    if rule != {"tp": 2.0, "sl": -1.5}:
        raise ValueError("T200_S150 정의가 +2.00/-1.50에서 변경되었습니다.")

    return True


LIVE_ORDER_COLUMNS = [
    "datetime", "version", "event", "side", "stock_code", "stock_name",
    "order_no", "original_order_no", "fill_no",
    "requested_qty", "broker_filled_qty", "delta_qty", "unfilled_qty",
    "fill_price", "broker_status", "paper_trade_id", "entry_mode",
    "pre_entry_type", "watch_episode_id", "exchange", "order_type",
    "reason", "error", "response",
    "broker_held_qty", "broker_sellable_qty", "broker_avg_price",
    "auto_managed_qty", "external_qty",
    "pending_auto_buy_qty", "pending_auto_sell_qty",
    "signal_time", "signal_price", "live_order_time", "entry_seq",
    "broker_precheck_start_time", "broker_precheck_end_time", "broker_precheck_sec",
    "sell_order_time", "sell_fill_time",
    "trigger_to_order_sec", "order_to_fill_sec", "trigger_to_fill_sec",
    "external_auto_exit_qty", "external_exit_price",
    "external_order_no", "external_fill_time",
]


LIVE_REASON_KO = {
    "TAKE_PROFIT": "익절",
    "STOP_LOSS": "손절",
    "TIME_EXIT": "시간청산",
    "FORCE_EXIT": "강제청산",
    "EXIT_ERROR": "매도 오류",
    "POSITION_MISMATCH": "보유수량 불일치",
    "EXECUTION_QTY_MISMATCH": "체결수량 불일치",
    "ORDER_STATUS_UNKNOWN": "주문상태 확인불가",
    "EXTERNAL_ORDER_DETECTED": "수동주문 감지",
    "EXTERNAL_EXIT_CONFIRMED": "수동매도 확인",
    "MANUAL_INTERVENTION_REQUIRED": "수동개입 확인 필요",
}


class OrderStatusUnknownError(RuntimeError):
    pass


class ShutdownRequestedError(RuntimeError):
    pass


def reason_to_korean(reason):
    return LIVE_REASON_KO.get(str(reason), str(reason))


def stock_display_name(code, fallback=""):
    code = clean_stock_code(code)
    if fallback:
        return str(fallback)
    with STATE_LOCK:
        p = live_positions.get(code, {})
        if p.get("stock_name"):
            return p["stock_name"]
        for order in live_orders.values():
            if clean_stock_code(order.get("stock_code", "")) == code and order.get("stock_name"):
                return order["stock_name"]
        b = broker_balances.get(code, {})
        if b.get("stock_name"):
            return b["stock_name"]
    return "종목명 확인불가"


def live_slot_lines(entry_seq=""):
    with STATE_LOCK:
        used = len(live_entered_today)
        remaining = max(0, LIVE_MAX_TRADES_PER_DAY - used)
        current_holdings = sum(
            1 for p in live_positions.values()
            if safe_int(p.get("auto_managed_qty", p.get("qty", 0))) > 0
        )

    seq = entry_seq if entry_seq not in [None, ""] else used
    return (
        f"오늘 실제진입 : {seq} / {LIVE_MAX_TRADES_PER_DAY}번째\n"
        f"남은 실제진입 : {remaining}종목\n"
        f"현재 실제보유 : {current_holdings}종목"
    )


def save_live_order_event(row):
    """모든 event가 동일한 고정 스키마로 기록되도록 합니다."""

    record = {col: "" for col in LIVE_ORDER_COLUMNS}
    record["datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    record["version"] = STRATEGY_VERSION

    for key, value in dict(row or {}).items():
        if key in record:
            record[key] = value

    code = clean_stock_code(record.get("stock_code", ""))
    if code:
        record["stock_code"] = code
        if not record.get("stock_name"):
            record["stock_name"] = stock_display_name(code)

    with LIVE_CSV_LOCK:
        exists = os.path.exists(LIVE_ORDER_FILE) and os.path.getsize(LIVE_ORDER_FILE) > 0
        with open(LIVE_ORDER_FILE, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=LIVE_ORDER_COLUMNS, extrasaction="ignore")
            if not exists:
                writer.writeheader()
            writer.writerow(record)


def save_live_trade_result(position, exit_price, result):

    entry_price = safe_float(position.get("avg_entry_price", 0))
    qty = safe_int(
        position.get(
            "exit_filled_qty",
            position.get("auto_managed_qty_before_exit", position.get("initial_qty", 0))
        )
    )

    ret = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
    pnl = (exit_price - entry_price) * qty

    paper_result, paper_return = get_paper_reference_outcome(
        position.get("paper_trade_id", "")
    )

    trigger_time = position.get("exit_trigger_time", "")
    order_time = position.get("sell_order_time", position.get("live_exit_order_time", ""))
    fill_time = position.get("sell_fill_time", position.get("live_exit_fill_time", datetime.now()))

    trigger_to_order_sec = position.get("trigger_to_order_sec", "")
    if trigger_to_order_sec in ["", None]:
        trigger_to_order_sec = _elapsed_seconds_v168(trigger_time, order_time)

    order_to_fill_sec = position.get("order_to_fill_sec", "")
    if order_to_fill_sec in ["", None]:
        order_to_fill_sec = _elapsed_seconds_v168(order_time, fill_time)

    trigger_to_fill_sec = position.get("trigger_to_fill_sec", "")
    if trigger_to_fill_sec in ["", None]:
        trigger_to_fill_sec = _elapsed_seconds_v168(trigger_time, fill_time)

    trigger_price = safe_float(position.get("exit_trigger_price", 0))
    trigger_to_fill_slippage_pct = ""
    if trigger_price > 0:
        trigger_to_fill_slippage_pct = (exit_price / trigger_price - 1) * 100

    row = {
        "version": STRATEGY_VERSION,
        "stock_code": position["stock_code"],
        "stock_name": position["stock_name"],
        "strategy": LIVE_STRATEGY,
        "paper_trade_id": position.get("paper_trade_id", ""),
        "entry_mode": position.get("entry_mode", ""),
        "pre_entry_type": position.get("pre_entry_type", ""),
        "watch_episode_id": position.get("watch_episode_id", ""),
        "signal_time": position.get("signal_time_str", ""),
        "signal_price": position.get("signal_price", ""),
        "live_order_time": _csv_datetime(position.get("live_order_time", "")),
        "live_fill_time": _csv_datetime(position.get("live_fill_time", position.get("entry_time", ""))),
        "live_fill_price": round(entry_price, 2),
        "live_entry_delay_sec": position.get("live_entry_delay_sec", ""),
        "live_vs_signal_pct": position.get("live_vs_signal_pct", ""),
        "entry_time": _csv_datetime(position.get("entry_time", "")),
        "exit_trigger_reason": position.get("exit_trigger_reason", result),
        "exit_trigger_time": _csv_datetime(trigger_time),
        "exit_trigger_price": position.get("exit_trigger_price", ""),
        "strategy_entry_price": round(entry_price, 2),
        "target_price": round(safe_float(position.get("target_price", 0)), 2),
        "stop_price": round(safe_float(position.get("stop_price", 0)), 2),
        "sell_order_time": _csv_datetime(order_time),
        "broker_precheck_start_time": _csv_datetime(position.get("broker_precheck_start_time", "")),
        "broker_precheck_end_time": _csv_datetime(position.get("broker_precheck_end_time", "")),
        "broker_precheck_sec": position.get("broker_precheck_sec", ""),
        "sell_fill_time": _csv_datetime(fill_time),
        "trigger_to_order_sec": trigger_to_order_sec,
        "order_to_fill_sec": order_to_fill_sec,
        "sell_fill_avg_price": round(exit_price, 2),
        "trigger_to_fill_sec": trigger_to_fill_sec,
        "trigger_to_fill_slippage_pct": trigger_to_fill_slippage_pct,
        "live_exit_order_time": _csv_datetime(position.get("live_exit_order_time", "")),
        "live_exit_fill_time": _csv_datetime(fill_time),
        "exit_time": _csv_datetime(fill_time),
        "qty": qty,
        "actual_invested_amount": round(entry_price * qty, 0),
        "entry_price": round(entry_price, 2),
        "live_exit_fill_price": round(exit_price, 2),
        "exit_price": round(exit_price, 2),
        "live_gross_return_pct": round(ret, 4),
        "return_rate_gross": round(ret, 4),
        "live_realized_pnl": round(pnl, 0),
        "pnl_gross_won": round(pnl, 0),
        "result": result,
        "paper_T200_S150_result": paper_result,
        "paper_T200_S150_return_pct": (
            round(paper_return, 4) if isinstance(paper_return, (int, float)) else paper_return
        ),
        "broker_avg_price": position.get("broker_avg_price", ""),
        "broker_held_qty": position.get("broker_held_qty", ""),
        "broker_sellable_qty": position.get("broker_sellable_qty", ""),
        "auto_managed_qty": position.get("auto_managed_qty_before_exit", qty),
        "external_qty": position.get("external_qty", 0),
        "entry_order_no": position.get("entry_order_no", ""),
        "exit_order_no": position.get("exit_order_no", ""),
        "external_auto_exit_qty": position.get("external_auto_exit_qty", ""),
        "external_exit_price": position.get("external_exit_price", ""),
        "external_order_no": position.get("external_order_no", ""),
        "external_fill_time": _csv_datetime(position.get("external_fill_time", "")),
        "entry_seq": position.get("entry_seq", ""),
        "score": position.get("score", ""),
    }

    pd.DataFrame([row]).to_csv(
        LIVE_TRADE_FILE,
        mode="a",
        header=not os.path.exists(LIVE_TRADE_FILE),
        index=False,
        encoding="utf-8-sig"
    )

    return pnl, ret



def mark_code_blocked(code, reason, detail=""):
    code = clean_stock_code(code)
    with STATE_LOCK:
        live_blocked_codes[code] = {
            "reason": reason,
            "detail": detail,
            "time": datetime.now(),
        }
        p = live_positions.get(code)
        if p and p.get("status") not in ["EXIT_PENDING", "EXIT_VALIDATING"]:
            p["status"] = reason
    save_live_state()


def clear_code_block(code, allowed_reasons=None):
    code = clean_stock_code(code)
    with STATE_LOCK:
        current = live_blocked_codes.get(code)
        if current is None:
            return
        if allowed_reasons and current.get("reason") not in allowed_reasons:
            return
        live_blocked_codes.pop(code, None)
        p = live_positions.get(code)
        if p and safe_int(p.get("auto_managed_qty", 0)) > 0:
            p["status"] = "OPEN"
    save_live_state()


def set_live_system_halt(reason, code="", stock_name="", detail=""):
    global live_trading_halted
    global live_system_halt_reason
    global live_recovery_mode

    with STATE_LOCK:
        live_trading_halted = True
        live_recovery_mode = True
        live_system_halt_reason = str(reason)

    save_live_state()

    code = clean_stock_code(code)
    if code:
        name = stock_display_name(code, stock_name)
        subject = f"{name} ({code})"
    else:
        subject = "전체 실제매매"

    log(f"[SAFE HALT] {subject} / {reason} / {detail}")
    send_telegram(
        "🚨 실제매매 SAFE HALT\n"
        f"{subject}\n"
        f"사유 : {reason_to_korean(reason)}\n"
        f"{detail}\n"
        "신규 실제주문만 중단하고 가상연구는 계속합니다."
    )


def _record_execution_qty_issue(code, stock_name, detail):
    code = clean_stock_code(code)
    with STATE_LOCK:
        live_execution_issue_codes.add(code)
        issue_count = len(live_execution_issue_codes)

    mark_code_blocked(code, "EXECUTION_QTY_MISMATCH", detail)
    send_telegram(
        "🚨 체결수량 불일치\n"
        f"{stock_display_name(code, stock_name)} ({code})\n"
        f"{detail}\n"
        "해당 종목 자동주문을 격리합니다."
    )

    if issue_count >= 2:
        set_live_system_halt(
            "EXECUTION_QTY_MISMATCH",
            detail="복수 종목에서 체결수량 invariant 오류가 발생했습니다."
        )


def compute_broker_fill_delta(requested_qty, unfilled_qty, prev_filled_qty):
    requested_qty = safe_int(requested_qty)
    unfilled_qty = safe_int(unfilled_qty)
    prev_filled_qty = safe_int(prev_filled_qty)

    broker_filled_qty = requested_qty - unfilled_qty

    if requested_qty < 0 or unfilled_qty < 0:
        raise ValueError("requested/unfilled 수량이 음수입니다.")

    if not (0 <= broker_filled_qty <= requested_qty):
        raise ValueError(
            f"broker_filled_qty invariant 위반: requested={requested_qty}, "
            f"unfilled={unfilled_qty}, filled={broker_filled_qty}"
        )

    if prev_filled_qty < 0 or prev_filled_qty > requested_qty:
        raise ValueError(
            f"prev_filled_qty invariant 위반: prev={prev_filled_qty}, requested={requested_qty}"
        )

    delta_qty = broker_filled_qty - prev_filled_qty
    if delta_qty < 0:
        raise ValueError(
            f"누적체결량 역행: prev={prev_filled_qty}, broker={broker_filled_qty}"
        )

    return broker_filled_qty, delta_qty


def reconcile_managed_quantities(auto_managed_qty, external_qty, broker_held_qty):
    """
    수동매도 정책: external 물량부터 차감, 그 다음 auto 물량 차감.
    broker held만으로도 결과가 결정됩니다.
    """
    auto_managed_qty = max(0, safe_int(auto_managed_qty))
    external_qty = max(0, safe_int(external_qty))
    broker_held_qty = max(0, safe_int(broker_held_qty))

    new_auto = min(auto_managed_qty, broker_held_qty)
    new_external = max(0, broker_held_qty - new_auto)
    return new_auto, new_external


def _pending_internal_sell_for_code(code):
    code = clean_stock_code(code)
    with STATE_LOCK:
        return [
            o for o in live_orders.values()
            if clean_stock_code(o.get("stock_code", "")) == code
            and o.get("side") == "SELL"
            and o.get("status") in ["SUBMITTED", "PARTIAL", "EXIT_VALIDATING", "ORDER_STATUS_UNKNOWN"]
        ]


def _pending_internal_buy_for_code(code):
    code = clean_stock_code(code)
    with STATE_LOCK:
        return [
            o for o in live_orders.values()
            if clean_stock_code(o.get("stock_code", "")) == code
            and o.get("side") == "BUY"
            and o.get("status") in ["SUBMITTED", "PARTIAL", "CANCEL_PENDING", "ORDER_STATUS_UNKNOWN"]
        ]


def _set_submit_intent(code, side):
    code = clean_stock_code(code)
    side = str(side).upper()
    with STATE_LOCK:
        live_submit_intents[(code, side)] = time.time()


def _clear_submit_intent(code, side):
    code = clean_stock_code(code)
    side = str(side).upper()
    with STATE_LOCK:
        live_submit_intents.pop((code, side), None)


def _active_submit_intent_for_code(code):
    code = clean_stock_code(code)
    now = time.time()
    active = []
    with STATE_LOCK:
        for key, ts in list(live_submit_intents.items()):
            if now - safe_float(ts, 0) > LOCAL_SUBMIT_INTENT_MAX_SEC:
                live_submit_intents.pop(key, None)
                continue
            if key[0] == code:
                active.append((key, ts))
    return active


def submit_stock_order(
    side,
    stock_code,
    qty,
    exchange,
    order_type=LIVE_ORDER_TYPE,
    price=None,
    stock_name="",
):
    """REST 주문. 네트워크/timeout은 ORDER_STATUS_UNKNOWN으로 분류합니다."""

    if shutdown_requested:
        raise ShutdownRequestedError("종료 요청 후 신규 주문 제출 차단")

    code = clean_stock_code(stock_code)
    side = side.upper()
    qty = safe_int(qty)

    if qty <= 0:
        raise ValueError("주문수량은 1주 이상이어야 합니다.")

    if side == "BUY":
        api_id = BUY_ORDER_API_ID
    elif side == "SELL":
        api_id = SELL_ORDER_API_ID
    else:
        raise ValueError("side는 BUY 또는 SELL이어야 합니다.")

    body = {
        "dmst_stex_tp": exchange,
        "stk_cd": code,
        "ord_qty": str(qty),
        "ord_uv": "" if price is None else str(int(price)),
        "trde_tp": order_type,
        "cond_uv": ""
    }

    _set_submit_intent(code, side)

    try:
        response = kiwoom_post(ORDER_API_PATH, api_id, body)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        raise OrderStatusUnknownError(
            f"{side} 주문 REST 응답 불명확: {type(e).__name__}: {e}"
        ) from e

    ord_no = str(response.get("ord_no", "")).strip()
    if not ord_no:
        raise OrderStatusUnknownError(f"주문번호 없음 / 응답: {response}")

    save_live_order_event({
        "event": "ORDER_ACCEPTED",
        "side": side,
        "stock_code": code,
        "stock_name": stock_display_name(code, stock_name),
        "requested_qty": qty,
        "exchange": exchange,
        "order_type": order_type,
        "order_no": ord_no,
        "response": str(response),
    })
    return response


def submit_cancel_order(original_order_no, stock_code, exchange, cancel_qty=0, stock_name=""):
    """부분체결 BUY 잔량 보호용 취소. 사용자 수동매도 주문은 자동취소하지 않습니다."""

    if shutdown_requested:
        raise ShutdownRequestedError("종료 요청 후 신규 취소주문 제출 차단")

    code = clean_stock_code(stock_code)
    body = {
        "dmst_stex_tp": exchange,
        "orig_ord_no": str(original_order_no),
        "stk_cd": code,
        "cncl_qty": str(int(cancel_qty))
    }

    _set_submit_intent(code, "CANCEL")

    try:
        response = kiwoom_post(ORDER_API_PATH, CANCEL_ORDER_API_ID, body)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        raise OrderStatusUnknownError(
            f"CANCEL 주문 REST 응답 불명확: {type(e).__name__}: {e}"
        ) from e

    ord_no = str(response.get("ord_no", "")).strip()
    if not ord_no:
        raise OrderStatusUnknownError(f"취소주문번호 없음 / 응답: {response}")

    save_live_order_event({
        "event": "CANCEL_ACCEPTED",
        "side": "CANCEL",
        "stock_code": code,
        "stock_name": stock_display_name(code, stock_name),
        "original_order_no": str(original_order_no),
        "requested_qty": int(cancel_qty),
        "exchange": exchange,
        "order_no": ord_no,
        "response": str(response),
    })
    return response


def get_broker_pending_orders():
    """키움 미체결요청(ka10075) 결과를 주문번호 기준 dict로 반환합니다."""

    body = {
        "all_stk_tp": "0",
        "trde_tp": "0",
        "stk_cd": "",
        "stex_tp": "0"
    }

    data = kiwoom_post(ACCOUNT_API_PATH, PENDING_ORDER_API_ID, body)
    rows = find_first_list(data)
    result = {}

    for row in rows:
        ord_no = str(row.get("ord_no", "")).strip()
        if not ord_no:
            continue
        remaining_qty = safe_int(row.get("oso_qty", 0))
        if remaining_qty <= 0:
            continue
        result[ord_no] = {
            "order_no": ord_no,
            "stock_code": clean_stock_code(row.get("stk_cd", "")),
            "stock_name": str(row.get("stk_nm", "")),
            "remaining_qty": remaining_qty,
            "order_qty": safe_int(row.get("ord_qty", 0)),
            "original_order_no": str(row.get("orig_ord_no", "")).strip(),
            "order_type_text": str(row.get("io_tp_nm", "")),
        }
    return result


def get_broker_positions():
    """
    계좌평가잔고내역(kt00018)에서 총보유/매도가능/평균매입가를 확인합니다.
    sellable 필드가 없으면 held로 추정하지 않고 None을 유지합니다.
    """

    result = {}
    success_count = 0
    errors = []

    for exchange in ["KRX", "NXT"]:
        try:
            data = kiwoom_post(
                ACCOUNT_API_PATH,
                ACCOUNT_POSITION_API_ID,
                {"qry_tp": "2", "dmst_stex_tp": exchange}
            )
            rows = find_first_list(data)
            success_count += 1

            for row in rows:
                code = clean_stock_code(row.get("stk_cd", ""))
                if not code:
                    continue

                held_qty = safe_int(row.get("rmnd_qty", 0))
                if held_qty <= 0:
                    continue

                raw_sellable = first_existing(
                    row,
                    ["trde_able_qty", "sell_able_qty", "ord_psbl_qty"],
                    None,
                )
                sellable_qty = None if raw_sellable in [None, ""] else max(0, safe_int(raw_sellable))

                item = {
                    "stock_code": code,
                    "stock_name": str(row.get("stk_nm", "")),
                    "held_qty": held_qty,
                    "sellable_qty": sellable_qty,
                    "avg_price": abs_price(row.get("pur_pric", 0)),
                    "exchange": exchange,
                    "updated_at": datetime.now(),
                    # legacy compatibility
                    "qty": held_qty,
                    "tradable_qty": sellable_qty,
                }

                current = result.get(code)
                if current is None or held_qty > safe_int(current.get("held_qty", 0)):
                    result[code] = item

        except Exception as e:
            errors.append(f"{exchange}: {e}")

    if success_count == 0:
        raise Exception("계좌잔고 조회 실패 / " + " | ".join(errors))

    return result


def _update_broker_balance_cache(positions):
    global broker_balances
    global last_broker_full_sync_ts

    now = datetime.now()
    snapshot = {}
    for code, item in positions.items():
        x = dict(item)
        x["updated_at"] = now
        snapshot[clean_stock_code(code)] = x

    with STATE_LOCK:
        # full account snapshot: 목록에 없는 종목은 held=0으로 해석할 수 있도록 기존 cache를 교체
        broker_balances = snapshot
        last_broker_full_sync_ts = time.time()


def _elapsed_seconds_v168(start, end):
    if isinstance(start, datetime) and isinstance(end, datetime):
        return max(0.0, round((end - start).total_seconds(), 6))
    return ""


def _track_external_sell_execution(position, values):
    """
    v1.6.8 외부 SELL 누적체결 원장.

    broker_filled_qty = requested_qty - unfilled_qty
    delta_qty = broker_filled_qty - prev_filled_qty

    FID 911은 참고용이며 이벤트마다 단순 누적하지 않습니다.
    """
    if not isinstance(position, dict) or not isinstance(values, dict):
        return {
            "requested_qty": 0,
            "broker_filled_qty": 0,
            "delta_qty": 0,
            "unfilled_qty": 0,
            "fill_price": 0.0,
            "fill_no": "",
            "order_no": "",
            "quantity_known": False,
        }

    _normalize_live_position_state(position)

    order_no = str(values.get("9203", "")).strip()
    fill_no = str(values.get("909", "")).strip()
    requested_from_event = max(0, safe_int(values.get("900", 0)))
    unfilled_qty = max(0, safe_int(values.get("902", 0)))
    fill_price = abs_price(values.get("910", 0))

    progress_map = position.setdefault("external_sell_order_progress", {})
    progress = progress_map.setdefault(order_no, {
        "requested_qty": 0,
        "filled_qty": 0,
        "processed_fill_nos": [],
        "last_unfilled_qty": "",
        "updated_at": "",
    })

    requested_qty = requested_from_event or max(
        0, safe_int(progress.get("requested_qty", 0))
    )
    prev_filled_qty = max(0, safe_int(progress.get("filled_qty", 0)))

    if requested_qty <= 0:
        # 정확한 주문수량이 없는 이벤트에서는 체결량을 추정하지 않습니다.
        progress["last_unfilled_qty"] = unfilled_qty
        progress["updated_at"] = datetime.now()
        return {
            "requested_qty": 0,
            "broker_filled_qty": prev_filled_qty,
            "delta_qty": 0,
            "unfilled_qty": unfilled_qty,
            "fill_price": fill_price,
            "fill_no": fill_no,
            "order_no": order_no,
            "quantity_known": False,
        }

    requested_qty = max(requested_qty, prev_filled_qty)
    progress["requested_qty"] = requested_qty

    raw_broker_filled = requested_qty - unfilled_qty
    broker_filled_qty = min(requested_qty, max(0, raw_broker_filled))

    if broker_filled_qty < prev_filled_qty:
        # stale/out-of-order 이벤트는 재누적하지 않습니다.
        delta_qty = 0
        broker_filled_qty = prev_filled_qty
    else:
        delta_qty = broker_filled_qty - prev_filled_qty

    progress["filled_qty"] = broker_filled_qty
    progress["last_unfilled_qty"] = unfilled_qty
    progress["updated_at"] = datetime.now()

    if fill_no:
        processed = list(progress.get("processed_fill_nos", []))
        if fill_no not in processed:
            processed.append(fill_no)
        progress["processed_fill_nos"] = processed[-100:]

    if delta_qty > 0 and fill_price > 0:
        position.setdefault("external_sell_fill_lots", []).append({
            "order_no": order_no,
            "fill_no": fill_no,
            "qty_total": delta_qty,
            "qty_remaining": delta_qty,
            "price": fill_price,
            "fill_time": datetime.now(),
        })

    return {
        "requested_qty": requested_qty,
        "broker_filled_qty": broker_filled_qty,
        "delta_qty": delta_qty,
        "unfilled_qty": unfilled_qty,
        "fill_price": fill_price,
        "fill_no": fill_no,
        "order_no": order_no,
        "quantity_known": True,
    }


def _consume_external_sell_lots(position, qty):
    """외부 SELL 체결 lot을 시간순으로 qty만큼 소비합니다."""
    qty = max(0, safe_int(qty))
    if qty <= 0 or not isinstance(position, dict):
        return 0, 0.0, None, []

    lots = position.setdefault("external_sell_fill_lots", [])
    need = qty
    used = 0
    amount = 0.0
    last_fill_time = None
    order_nos = []

    for lot in lots:
        if need <= 0:
            break

        remaining = max(0, safe_int(lot.get("qty_remaining", 0)))
        price = safe_float(lot.get("price", 0))
        if remaining <= 0 or price <= 0:
            continue

        take = min(need, remaining)
        lot["qty_remaining"] = remaining - take
        used += take
        amount += price * take
        need -= take

        order_no = str(lot.get("order_no", "")).strip()
        if order_no and order_no not in order_nos:
            order_nos.append(order_no)

        ft = lot.get("fill_time")
        if isinstance(ft, datetime):
            last_fill_time = ft

    position["external_sell_fill_lots"] = [
        lot for lot in lots
        if safe_int(lot.get("qty_remaining", 0)) > 0
    ]

    return used, amount, last_fill_time, order_nos


def _apply_external_auto_realized_pnl(
    position_snapshot,
    exit_qty,
    exit_amount,
    exit_time,
    result,
    external_order_nos=None,
):
    """
    수동매도로 실제 감소한 auto_managed_qty만 gross 실현손익에 반영합니다.
    프로그램 실제 평균체결가(avg_entry_price)를 진입원가로 사용합니다.
    """
    global live_daily_realized_pnl
    global live_trading_halted
    global live_system_halt_reason

    exit_qty = max(0, safe_int(exit_qty))
    exit_amount = safe_float(exit_amount, 0)
    if exit_qty <= 0 or exit_amount <= 0:
        return None

    exit_price = exit_amount / exit_qty
    fill_time = exit_time if isinstance(exit_time, datetime) else datetime.now()
    order_nos = [
        str(x).strip() for x in (external_order_nos or []) if str(x).strip()
    ]
    external_order_no = ",".join(dict.fromkeys(order_nos))

    p = dict(position_snapshot)
    p["exit_filled_qty"] = exit_qty
    p["auto_managed_qty_before_exit"] = exit_qty
    p["external_auto_exit_qty"] = exit_qty
    p["external_exit_price"] = exit_price
    p["external_order_no"] = external_order_no
    p["external_fill_time"] = fill_time
    p["exit_order_no"] = external_order_no
    p["exit_reason"] = result
    p["exit_trigger_reason"] = result

    # 수동매도는 전략 TP/SL trigger가 아니므로 외부 체결시각을 기준으로 기록하되,
    # 자동청산 지연통계와 섞이지 않도록 broker_precheck 계측은 비워둡니다.
    p["exit_trigger_time"] = fill_time
    p["exit_trigger_price"] = exit_price
    p["live_exit_order_time"] = fill_time
    p["sell_order_time"] = fill_time
    p["live_exit_fill_time"] = fill_time
    p["sell_fill_time"] = fill_time
    p["trigger_to_order_sec"] = 0.0
    p["order_to_fill_sec"] = 0.0
    p["trigger_to_fill_sec"] = 0.0

    pnl, ret = save_live_trade_result(p, exit_price, result)

    with STATE_LOCK:
        live_daily_realized_pnl += pnl
        if (
            LIVE_DAILY_MAX_LOSS_WON > 0
            and live_daily_realized_pnl <= -LIVE_DAILY_MAX_LOSS_WON
        ):
            live_trading_halted = True
            live_system_halt_reason = "DAILY_LOSS_LIMIT"

    save_live_order_event({
        "event": "EXTERNAL_REALIZED_PNL",
        "side": "SELL",
        "stock_code": p.get("stock_code", ""),
        "stock_name": p.get("stock_name", ""),
        "order_no": external_order_no,
        "requested_qty": exit_qty,
        "broker_filled_qty": exit_qty,
        "delta_qty": exit_qty,
        "fill_price": exit_price,
        "reason": result,
        "auto_managed_qty": exit_qty,
        "external_auto_exit_qty": exit_qty,
        "external_exit_price": exit_price,
        "external_order_no": external_order_no,
        "external_fill_time": _csv_datetime(fill_time),
    })
    save_live_state()

    return {
        "qty": exit_qty,
        "exit_price": exit_price,
        "pnl": pnl,
        "ret": ret,
        "result": result,
    }

def _sync_position_from_broker(code, balance, source="PERIODIC", external_event=False):
    """broker 총보유를 auto/external 원장에 반영합니다."""

    code = clean_stock_code(code)
    full_external_exit = False
    changed = False
    unresolved_external_auto_qty = 0
    external_realized_payload = None

    pending_buy = bool(_pending_internal_buy_for_code(code))
    pending_sell = bool(_pending_internal_sell_for_code(code))

    # 자동 주문 체결 직후 broker 잔고 반영이 늦을 수 있으므로,
    # 내부 BUY/SELL이 진행 중이거나 AUTO_*_FILL 직후 sync에서는
    # broker 수량을 원장에 덮어쓰지 않고 검증값만 저장합니다.
    defer_quantity_reconcile = (
        pending_buy
        or pending_sell
        or (not external_event and source in ["AUTO_BUY_FILL", "AUTO_SELL_FILL"])
    )

    with STATE_LOCK:
        p = live_positions.get(code)
        if not p:
            return {"exists": False}

        _normalize_live_position_state(p)

        has_external_sell_lots = any(
            safe_int(lot.get("qty_remaining", 0)) > 0
            for lot in p.get("external_sell_fill_lots", [])
            if isinstance(lot, dict)
        )
        external_reconcile = external_event or has_external_sell_lots

        old_auto = safe_int(p.get("auto_managed_qty", 0))
        old_external = safe_int(p.get("external_qty", 0))
        held = safe_int((balance or {}).get("held_qty", 0))
        sellable = (balance or {}).get("sellable_qty", 0 if held == 0 else None)
        broker_avg = (balance or {}).get("avg_price", "")

        p["broker_held_qty"] = held
        p["broker_sellable_qty"] = "" if sellable is None else sellable
        p["broker_avg_price"] = broker_avg
        p["broker_updated_at"] = datetime.now()

        expected = old_auto + old_external
        if held != expected and not defer_quantity_reconcile:
            new_auto, new_external = reconcile_managed_quantities(
                old_auto, old_external, held
            )

            # 감소분 배분은 기존 합의대로 external_qty -> auto_managed_qty 순서.
            external_qty_reduced = max(0, old_external - new_external)
            auto_qty_reduced = max(0, old_auto - new_auto)
            position_snapshot = dict(p)

            if external_reconcile and (external_qty_reduced > 0 or auto_qty_reduced > 0):
                if external_qty_reduced > 0:
                    _consume_external_sell_lots(p, external_qty_reduced)

                if auto_qty_reduced > 0:
                    used_qty, used_amount, used_time, used_order_nos = (
                        _consume_external_sell_lots(p, auto_qty_reduced)
                    )
                    unresolved_external_auto_qty = max(
                        0, auto_qty_reduced - used_qty
                    )

                    if used_qty > 0:
                        external_realized_payload = {
                            "position_snapshot": position_snapshot,
                            "exit_qty": used_qty,
                            "exit_amount": used_amount,
                            "exit_time": used_time,
                            "result": (
                                "EXTERNAL_EXIT"
                                if new_auto == 0
                                else "EXTERNAL_PARTIAL_EXIT"
                            ),
                            "external_order_nos": used_order_nos,
                        }

            p["auto_managed_qty"] = new_auto
            p["qty"] = new_auto
            p["external_qty"] = new_external
            changed = True

            save_live_order_event({
                "event": "BROKER_POSITION_RECONCILED",
                "stock_code": code,
                "stock_name": p.get("stock_name", ""),
                "reason": source,
                "broker_held_qty": held,
                "broker_sellable_qty": "" if sellable is None else sellable,
                "broker_avg_price": broker_avg,
                "auto_managed_qty": new_auto,
                "external_qty": new_external,
            })

            if held == 0 and old_auto > 0 and not pending_sell:
                full_external_exit = True

        p["pending_auto_buy_qty"] = sum(
            max(
                0,
                safe_int(o.get("requested_qty", 0))
                - safe_int(o.get("filled_qty", 0)),
            )
            for o in live_orders.values()
            if clean_stock_code(o.get("stock_code", "")) == code
            and o.get("side") == "BUY"
            and o.get("status") in ["SUBMITTED", "PARTIAL", "CANCEL_PENDING"]
        )
        p["pending_auto_sell_qty"] = sum(
            max(
                0,
                safe_int(o.get("requested_qty", 0))
                - safe_int(o.get("filled_qty", 0)),
            )
            for o in live_orders.values()
            if clean_stock_code(o.get("stock_code", "")) == code
            and o.get("side") == "SELL"
            and o.get("status") in ["SUBMITTED", "PARTIAL", "ORDER_STATUS_UNKNOWN"]
        )

        if external_reconcile and pending_sell:
            p["status"] = "MANUAL_INTERVENTION_REQUIRED"
            live_blocked_codes[code] = {
                "reason": "MANUAL_INTERVENTION_REQUIRED",
                "detail": "자동매도 주문 중 수동개입 감지",
                "time": datetime.now(),
            }
        elif (
            external_reconcile
            and not full_external_exit
            and safe_int(p.get("auto_managed_qty", 0)) > 0
        ):
            p["status"] = "OPEN"
            current_block = live_blocked_codes.get(code, {})
            if current_block.get("reason") == "EXTERNAL_ORDER_DETECTED":
                live_blocked_codes.pop(code, None)

        result = {
            "exists": True,
            "old_auto": old_auto,
            "old_external": old_external,
            "held": held,
            "new_auto": safe_int(p.get("auto_managed_qty", 0)),
            "new_external": safe_int(p.get("external_qty", 0)),
            "sellable": sellable,
            "changed": changed,
            "full_external_exit": full_external_exit,
            "pending_buy": pending_buy,
            "pending_sell": pending_sell,
            "deferred": defer_quantity_reconcile,
            "stock_name": p.get("stock_name", code),
            "entry_seq": p.get("entry_seq", ""),
        }

    # CSV/Telegram I/O는 STATE_LOCK 밖에서 처리합니다.
    realized = None
    if external_realized_payload:
        realized = _apply_external_auto_realized_pnl(**external_realized_payload)

    if unresolved_external_auto_qty > 0:
        with STATE_LOCK:
            live_execution_issue_codes.add(code)
            live_blocked_codes[code] = {
                "reason": "EXTERNAL_PNL_UNRESOLVED",
                "detail": (
                    f"자동관리 감소 {unresolved_external_auto_qty}주 체결가 lot 확인불가"
                ),
                "time": datetime.now(),
            }

        save_live_order_event({
            "event": "EXTERNAL_PNL_UNRESOLVED",
            "side": "SELL",
            "stock_code": code,
            "stock_name": result.get("stock_name", code),
            "reason": source,
            "error": (
                f"수동매도로 자동관리 {unresolved_external_auto_qty}주 감소했으나 "
                "실제 외부 체결가 lot 부족"
            ),
            "auto_managed_qty": result.get("new_auto", 0),
            "external_qty": result.get("new_external", 0),
        })

        send_telegram(
            "🚨 수동매도 손익 확인 필요\n"
            f"{result['stock_name']} ({code})\n"
            f"자동관리 감소 {unresolved_external_auto_qty}주의 실제 외부 체결가를 "
            "원장에서 확인하지 못했습니다.\n"
            "해당 종목 추가 자동주문을 차단하고 계좌/체결내역 확인이 필요합니다."
        )

    if full_external_exit and unresolved_external_auto_qty == 0:
        # 손익을 먼저 기록한 뒤 v1.6.7의 기존 외부청산 확정/포지션 제거 사용.
        _finalize_external_exit(code, source=source)
    else:
        # 불완전 체결가를 임의 추정해 포지션을 조용히 닫지 않습니다.
        save_live_state()

    if realized:
        action_text = "전량" if realized.get("result") == "EXTERNAL_EXIT" else "부분"
        send_telegram(
            "🏁 자동관리 물량 수동청산 손익 반영\n"
            f"{result['stock_name']} ({code})\n"
            f"구분 : {action_text} 수동청산\n"
            f"반영수량 : {realized['qty']}주\n"
            f"외부체결가 : {realized['exit_price']:,.0f}원\n"
            f"수익률(비용전) : {realized['ret']:+.2f}%\n"
            f"손익(비용전) : {realized['pnl']:+,.0f}원\n"
            f"오늘 누적(비용전) : {live_daily_realized_pnl:+,.0f}원"
        )

    return result



def _finalize_external_exit(code, source="EXTERNAL"):
    code = clean_stock_code(code)
    with STATE_LOCK:
        p = live_positions.get(code)
        if not p:
            return
        stock_name = p.get("stock_name", code)
        entry_seq = p.get("entry_seq", "")
        p["status"] = "EXTERNAL_EXIT_CONFIRMED"
        p["auto_managed_qty"] = 0
        p["qty"] = 0
        p["external_qty"] = 0
        live_positions.pop(code, None)
        live_blocked_codes.pop(code, None)

    save_live_order_event({
        "event": "EXTERNAL_EXIT_CONFIRMED",
        "side": "SELL",
        "stock_code": code,
        "stock_name": stock_name,
        "reason": source,
        "broker_held_qty": 0,
        "auto_managed_qty": 0,
        "external_qty": 0,
    })
    save_live_state()
    send_telegram(
        f"{stock_name} / 수동매도 확인\n\n"
        "⚠️ 자동관리 종목 전량 수동매도 확인\n\n"
        f"{stock_name} ({code})\n"
        "broker 보유수량 : 0주\n"
        "자동 TP/SL 관리를 종료합니다.\n\n"
        + live_slot_lines(entry_seq)
    )
    maybe_release_realtime(code)


def _broker_sync_task(code=None, reason="PERIODIC", external_event=False):
    if not AUTO_TRADE_ENABLED:
        return None

    with BROKER_SYNC_LOCK:
        positions = get_broker_positions()
        _update_broker_balance_cache(positions)

        codes = [clean_stock_code(code)] if code else list(live_positions.keys())
        results = {}
        for target in codes:
            balance = positions.get(target, {
                "stock_code": target,
                "held_qty": 0,
                "sellable_qty": 0,
                "avg_price": 0,
                "updated_at": datetime.now(),
            })
            results[target] = _sync_position_from_broker(
                target, balance, source=reason, external_event=external_event
            )
        return results


def schedule_broker_sync(code=None, reason="PERIODIC", external_event=False):
    if not AUTO_TRADE_ENABLED or shutdown_requested:
        return None

    def runner():
        try:
            return _broker_sync_task(code, reason, external_event)
        except Exception as e:
            log(f"[broker 비동기 동기화 오류] {code or 'ALL'} / {reason} / {e}")
            return None

    return LIVE_ASYNC_EXECUTOR.submit(runner)


def initialize_broker_account_snapshot():
    """시작 시 기존/장기보유 종목을 기억하고 자동매수 대상에서 제외합니다."""
    global broker_startup_holdings

    if not AUTO_TRADE_ENABLED:
        return True

    try:
        with BROKER_SYNC_LOCK:
            positions = get_broker_positions()
            _update_broker_balance_cache(positions)
            with STATE_LOCK:
                broker_startup_holdings = set(positions.keys()) - set(live_positions.keys())
        log(f"broker 시작 잔고 확인 / 기존보유 {len(broker_startup_holdings)}종목")
        save_live_state()
        return True
    except Exception as e:
        set_live_system_halt(
            "ORDER_STATUS_UNKNOWN",
            detail=f"시작 계좌잔고 확인 실패: {e}"
        )
        return False


def reconcile_live_state_with_broker():
    """
    saved state와 broker 보유/미체결을 교차검증합니다.
    명확한 수동 증감은 종목 원장만 보정하고, 미체결 주문 자체가 불명확하면 SAFE HALT합니다.
    """
    global live_recovery_mode
    global live_trading_halted
    global live_system_halt_reason
    global broker_startup_holdings

    if not AUTO_TRADE_ENABLED:
        return True

    try:
        with BROKER_SYNC_LOCK:
            positions = get_broker_positions()
            pending = get_broker_pending_orders()
            _update_broker_balance_cache(positions)

        ambiguous = []

        with STATE_LOCK:
            broker_startup_holdings = set(positions.keys()) - set(live_positions.keys())

        for code in list(live_positions.keys()):
            balance = positions.get(code, {
                "stock_code": code,
                "held_qty": 0,
                "sellable_qty": 0,
                "avg_price": 0,
            })
            _sync_position_from_broker(code, balance, source="STARTUP_RECONCILE", external_event=True)

        with STATE_LOCK:
            for ord_no, order in live_orders.items():
                if order.get("status") not in [
                    "SUBMITTED", "PARTIAL", "CANCEL_PENDING", "ORDER_STATUS_UNKNOWN"
                ]:
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
                # 과거 recovery 때문에만 halt였으면 해제. 일손실 halt 등은 유지.
                if live_system_halt_reason in ["", "이전 거래일 미해결 실전상태"]:
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

    except Exception as e:
        set_live_system_halt(
            "ORDER_STATUS_UNKNOWN",
            detail=f"Startup 계좌검증 실패: {e}"
        )
        return False


def select_live_exchange(session):
    if session == "MAIN":
        return LIVE_MAIN_EXCHANGE
    if session in ["NXT_PRE", "NXT_AFTER"]:
        return "NXT"
    return "KRX"


def can_open_live_trade(stock, entry_mode="", pre_entry_type="", decision_time=None):

    if not AUTO_TRADE_ENABLED:
        return False, "AUTO_TRADE_ENABLED=False"
    if shutdown_requested:
        return False, "종료 요청으로 신규주문 차단"
    if entry_mode != "PRE_HISTORY" or pre_entry_type != LIVE_ENTRY_MODE:
        return False, "실제진입 전략 아님(FIRST_75_PASS 전용)"

    if decision_time is None:
        decision_time = _stock_score_time(stock)

    valid, guard_reason = attach_session_decision_metrics(
        stock, stock.get("scan_session"), decision_time
    )
    if not valid:
        return False, guard_reason

    decision_session = get_session_at(decision_time)
    if decision_session not in LIVE_ALLOWED_SESSIONS:
        return False, f"실제진입 허용 세션 아님: {decision_session}"

    now_hhmm = decision_time.strftime("%H:%M")
    if not (LIVE_ENTRY_START <= now_hhmm <= LIVE_ENTRY_END):
        return False, "실제진입 허용시간 밖"

    code = clean_stock_code(stock["stock_code"])

    with STATE_LOCK:
        if live_recovery_mode:
            return False, "실전상태 복구/확인 필요"
        if live_trading_halted:
            return False, f"실제 신규진입 중단 상태: {live_system_halt_reason or 'HALT'}"
        if code in live_blocked_codes:
            return False, f"해당 종목 격리: {live_blocked_codes[code].get('reason','')}"
        if code in broker_startup_holdings:
            return False, "프로그램 시작 전 기존 보유종목"
        if code in live_entered_today:
            return False, "오늘 이미 실제진입/주문시도한 종목"
        if code in live_positions:
            return False, "이미 실제 자동관리 중"
        if _pending_internal_buy_for_code(code):
            return False, "매수주문 처리 중"
        if len(live_entered_today) >= LIVE_MAX_TRADES_PER_DAY:
            return False, "하루 실제진입 종목 한도"

        active_codes = {
            c for c, p in live_positions.items()
            if safe_int(p.get("auto_managed_qty", p.get("qty", 0))) > 0
        }
        for o in live_orders.values():
            if o.get("side") == "BUY" and o.get("status") in ["SUBMITTED", "PARTIAL", "CANCEL_PENDING"]:
                active_codes.add(clean_stock_code(o.get("stock_code", "")))
        active_codes.discard("")
        if len(active_codes) >= LIVE_MAX_CONCURRENT_POSITIONS:
            return False, "동시보유 한도"

    return True, "OK"


def get_live_committed_amount():
    with STATE_LOCK:
        total = 0.0
        for p in live_positions.values():
            qty = safe_int(p.get("auto_managed_qty", p.get("qty", 0)))
            avg_price = safe_float(p.get("avg_entry_price", 0))
            total += qty * avg_price

        for order in live_orders.values():
            if order.get("side") != "BUY" or order.get("status") not in ["SUBMITTED", "PARTIAL", "CANCEL_PENDING"]:
                continue
            remaining_qty = max(
                0,
                safe_int(order.get("requested_qty", 0)) - safe_int(order.get("filled_qty", 0))
            )
            reference_price = safe_float(order.get("reference_price", 0))
            total += remaining_qty * reference_price * (1 + LIVE_MARKET_ORDER_BUFFER_PCT / 100)
        return total


def verify_pre_buy_account_clear(code, stock_name=""):
    """실제 BUY 직전 broker 보유/미체결을 새로 조회합니다."""
    code = clean_stock_code(code)

    try:
        with BROKER_SYNC_LOCK:
            positions = get_broker_positions()
            pending = get_broker_pending_orders()
            _update_broker_balance_cache(positions)
    except Exception as e:
        set_live_system_halt(
            "ORDER_STATUS_UNKNOWN",
            code=code,
            stock_name=stock_name,
            detail=f"매수 직전 계좌상태 확인 실패: {e}"
        )
        return False, "매수 직전 계좌상태 확인 실패"

    held = safe_int(positions.get(code, {}).get("held_qty", 0))
    if held > 0:
        with STATE_LOCK:
            broker_startup_holdings.add(code)
        save_live_order_event({
            "event": "LIVE_ENTRY_SKIPPED_EXISTING_HOLDING",
            "side": "BUY",
            "stock_code": code,
            "stock_name": stock_display_name(code, stock_name),
            "broker_held_qty": held,
            "reason": "기존/수동 보유종목",
        })
        return False, f"broker 기존 보유 {held}주"

    pending_for_code = [x for x in pending.values() if clean_stock_code(x.get("stock_code", "")) == code]
    if pending_for_code:
        return False, "broker 미체결 주문 존재"

    return True, "OK"


def maybe_open_live_trade(stock, entry_mode="", pre_entry_type="", paper_trade_id="", decision_time=None):
    global live_trade_count

    ok, reason = can_open_live_trade(
        stock,
        entry_mode=entry_mode,
        pre_entry_type=pre_entry_type,
        decision_time=decision_time,
    )
    if not ok:
        if DEBUG_MODE and AUTO_TRADE_ENABLED:
            log(f"[실전진입 SKIP] {stock['stock_name']} / {reason}")
        return False

    code = clean_stock_code(stock["stock_code"])
    stock_name = stock["stock_name"]

    # 기존 장기보유/장중 수동매수를 최종 주문 직전 다시 확인.
    account_ok, account_reason = verify_pre_buy_account_clear(code, stock_name)
    if not account_ok:
        log(f"[실전진입 SKIP] {stock_name} / {account_reason}")
        return False

    signal_price = safe_float(stock["current_price"])
    signal_time = decision_time if isinstance(decision_time, datetime) else _stock_score_time(stock)
    current_price = get_realtime_price(code) or signal_price
    if current_price <= 0 or signal_price <= 0:
        return False

    budget_price = current_price * (1 + LIVE_MARKET_ORDER_BUFFER_PCT / 100)
    qty = int(LIVE_TRADE_AMOUNT_WON // budget_price)
    if qty < 1:
        log(f"[실전진입 SKIP] {stock_name} / 종목당 100만원 예산으로 1주 미만")
        return False

    planned_amount = qty * budget_price
    committed_amount = get_live_committed_amount()
    if committed_amount + planned_amount > LIVE_TOTAL_BUDGET_WON:
        log(
            f"[실전진입 SKIP] {stock_name} / 총 예산 초과 "
            f"({committed_amount:,.0f}+{planned_amount:,.0f}>{LIVE_TOTAL_BUDGET_WON:,.0f})"
        )
        return False

    order_check_time = datetime.now()
    order_session = get_session_at(order_check_time)
    order_hhmm = order_check_time.strftime("%H:%M")
    if order_session not in LIVE_ALLOWED_SESSIONS or not (LIVE_ENTRY_START <= order_hhmm <= LIVE_ENTRY_END):
        log(f"[실전진입 SKIP] {stock_name} / 주문 직전 실제 시간이 허용구간 밖")
        return False

    exchange = select_live_exchange(order_session)
    if WEBSOCKET_ENABLED and websocket_manager is not None:
        websocket_manager.subscribe_stock(code, order_session)

    # submit 직전 슬롯을 확정. 오류/수동정리 후에도 되살리지 않습니다.
    with STATE_LOCK:
        if code in live_entered_today or len(live_entered_today) >= LIVE_MAX_TRADES_PER_DAY:
            return False
        entry_seq = len(live_entered_today) + 1
        live_entered_today.add(code)
        live_trade_count = len(live_entered_today)
    save_live_state()

    live_order_time = datetime.now()

    try:
        response = submit_stock_order(
            "BUY", code, qty, exchange, stock_name=stock_name
        )
        ord_no = str(response.get("ord_no", "")).strip()

        with STATE_LOCK:
            live_orders[ord_no] = _normalize_live_order_state({
                "order_no": ord_no,
                "side": "BUY",
                "stock_code": code,
                "stock_name": stock_name,
                "requested_qty": qty,
                "filled_qty": 0,
                "broker_filled_qty": 0,
                "unfilled_qty": qty,
                "filled_amount": 0.0,
                "status": "SUBMITTED",
                "exchange": exchange,
                "reference_price": current_price,
                "planned_amount": planned_amount,
                "signal_price": signal_price,
                "signal_time": signal_time,
                "signal_time_str": _csv_datetime(signal_time),
                "live_order_time": live_order_time,
                "score": stock.get("score", 0),
                "paper_trade_id": paper_trade_id,
                "entry_mode": entry_mode,
                "pre_entry_type": pre_entry_type,
                "watch_episode_id": stock.get("watch_episode_id", ""),
                "entry_seq": entry_seq,
            })

        _clear_submit_intent(code, "BUY")
        save_live_state()
        replay_unmatched_order_events(ord_no)

        save_live_order_event({
            "event": "LIVE_ENTRY_LINK",
            "side": "BUY",
            "stock_code": code,
            "stock_name": stock_name,
            "order_no": ord_no,
            "requested_qty": qty,
            "paper_trade_id": paper_trade_id,
            "entry_mode": entry_mode,
            "pre_entry_type": pre_entry_type,
            "watch_episode_id": stock.get("watch_episode_id", ""),
            "signal_time": _csv_datetime(signal_time),
            "signal_price": signal_price,
            "live_order_time": _csv_datetime(live_order_time),
            "entry_seq": entry_seq,
        })

        send_telegram(
            f"{stock_name} / 매수주문 / {qty}주\n\n"
            "🟠 실제 자동매수 주문 접수\n\n"
            f"{stock_name} ({code})\n"
            f"진입전략 : {pre_entry_type}\n"
            f"주문수량 : {qty}주\n"
            f"기준가격 : {current_price:,.0f}원\n"
            f"주문번호 : {ord_no}\n\n"
            + live_slot_lines(entry_seq)
        )
        return True

    except OrderStatusUnknownError as e:
        set_live_system_halt(
            "ORDER_STATUS_UNKNOWN",
            code=code,
            stock_name=stock_name,
            detail=str(e),
        )
        save_live_order_event({
            "event": "ORDER_STATUS_UNKNOWN",
            "side": "BUY",
            "stock_code": code,
            "stock_name": stock_name,
            "requested_qty": qty,
            "paper_trade_id": paper_trade_id,
            "entry_mode": entry_mode,
            "pre_entry_type": pre_entry_type,
            "watch_episode_id": stock.get("watch_episode_id", ""),
            "error": str(e),
            "entry_seq": entry_seq,
        })
        return False

    except ShutdownRequestedError:
        _clear_submit_intent(code, "BUY")
        return False

    except Exception as e:
        _clear_submit_intent(code, "BUY")
        # 명확한 API 오류/거부: 동일종목 자동 재주문 금지, 다른 종목은 계속 가능.
        log(f"[실제 매수주문 오류-재시도금지] {stock_name} ({code}) / {e}")
        save_live_order_event({
            "event": "LIVE_ENTRY_FAILED_NO_RETRY",
            "side": "BUY",
            "stock_code": code,
            "stock_name": stock_name,
            "requested_qty": qty,
            "paper_trade_id": paper_trade_id,
            "entry_mode": entry_mode,
            "pre_entry_type": pre_entry_type,
            "watch_episode_id": stock.get("watch_episode_id", ""),
            "error": str(e),
            "entry_seq": entry_seq,
        })
        send_telegram(
            "⚠️ 실제 자동매수 주문 실패 - 자동 재주문 없음\n"
            f"{stock_name} ({code})\n{e}\n\n"
            + live_slot_lines(entry_seq)
        )
        return False


def _find_external_pending_sell(code, pending_orders):
    code = clean_stock_code(code)
    with STATE_LOCK:
        internal_nos = set(live_orders.keys())

    for ord_no, item in pending_orders.items():
        if clean_stock_code(item.get("stock_code", "")) != code:
            continue
        if ord_no in internal_nos:
            continue
        text = str(item.get("order_type_text", ""))
        if "매도" in text:
            return item
    return None


def submit_live_exit(code, reason, trigger_price=None):
    """
    WebSocket 가격판단은 즉시 기록하고, broker 수량조회/REST SELL은 worker에서 처리합니다.
    """
    code = clean_stock_code(code)

    if shutdown_requested:
        return False

    with STATE_LOCK:
        p = live_positions.get(code)
        if not p:
            return False

        if p.get("status") not in ["OPEN", "POSITION_MISMATCH"]:
            return False

        if safe_int(p.get("auto_managed_qty", p.get("qty", 0))) <= 0:
            return False

        if p.get("pending_auto_sell_qty", 0) or _pending_internal_sell_for_code(code):
            return False

        if not p.get("entry_complete", False):
            # 부분체결 BUY는 기존 보호정책: 잔량취소 후 체결분 청산.
            return request_entry_cancel_for_exit(code, reason)

        p["status"] = "EXIT_TRIGGERED"
        p["exit_reason"] = reason
        p["exit_trigger_reason"] = reason
        p["exit_trigger_time"] = datetime.now()
        p["exit_trigger_price"] = (
            safe_float(trigger_price, 0)
            or safe_float(p.get("last_price", 0))
            or safe_float(get_realtime_price(code), 0)
        )

    save_live_state()
    LIVE_ASYNC_EXECUTOR.submit(_submit_live_exit_worker, code, reason)
    return True


def _submit_live_exit_worker(code, reason):
    code = clean_stock_code(code)

    if shutdown_requested:
        return False

    with STATE_LOCK:
        p = live_positions.get(code)
        if not p or p.get("status") != "EXIT_TRIGGERED":
            return False
        p["status"] = "EXIT_VALIDATING"
        stock_name = p.get("stock_name", code)
        exchange = p.get("exchange", LIVE_MAIN_EXCHANGE)
        entry_seq = p.get("entry_seq", "")

    save_live_state()

    broker_precheck_start_time = datetime.now()
    with STATE_LOCK:
        p = live_positions.get(code)
        if p:
            p["broker_precheck_start_time"] = broker_precheck_start_time

    try:
        with BROKER_SYNC_LOCK:
            positions = get_broker_positions()
            pending = get_broker_pending_orders()
            _update_broker_balance_cache(positions)
    except Exception as e:
        with STATE_LOCK:
            p = live_positions.get(code)
            if p:
                p["status"] = "EXIT_ERROR"
        mark_code_blocked(code, "EXIT_ERROR", f"broker 매도수량 확인 실패: {e}")
        send_telegram(
            "🚨 실제 자동매도 오류\n"
            f"{stock_name} ({code})\n"
            "사유 : 계좌 매도가능수량 확인 실패\n"
            f"{e}\n"
            "임의 수량으로 매도하지 않습니다."
        )
        return False

    broker_precheck_end_time = datetime.now()
    broker_precheck_sec = _elapsed_seconds_v168(
        broker_precheck_start_time, broker_precheck_end_time
    )
    with STATE_LOCK:
        p = live_positions.get(code)
        if p:
            p["broker_precheck_end_time"] = broker_precheck_end_time
            p["broker_precheck_sec"] = broker_precheck_sec
    save_live_state()

    balance = positions.get(code, {
        "stock_code": code,
        "held_qty": 0,
        "sellable_qty": 0,
        "avg_price": 0,
        "updated_at": datetime.now(),
    })

    external_pending_sell = _find_external_pending_sell(code, pending)
    if external_pending_sell:
        with STATE_LOCK:
            p = live_positions.get(code)
            if p:
                p["status"] = "MANUAL_INTERVENTION_REQUIRED"
        mark_code_blocked(code, "MANUAL_INTERVENTION_REQUIRED", "broker에 외부 매도 미체결 존재")
        send_telegram(
            "⚠️ 수동주문 감지\n"
            f"{stock_name} ({code})\n"
            "broker에 수동 매도 미체결이 있어 추가 자동매도를 제출하지 않습니다.\n"
            "기존 주문은 자동취소하지 않습니다."
        )
        return False

    with STATE_LOCK:
        p = live_positions.get(code)
        if not p:
            return False

        _normalize_live_position_state(p)
        old_auto = safe_int(p.get("auto_managed_qty", 0))
        old_external = safe_int(p.get("external_qty", 0))
        held = safe_int(balance.get("held_qty", 0))
        sellable = balance.get("sellable_qty", 0 if held == 0 else None)
        broker_avg = balance.get("avg_price", "")

        new_auto, new_external = reconcile_managed_quantities(old_auto, old_external, held)
        quantity_corrected = (new_auto != old_auto) or (new_external != old_external)

        p["auto_managed_qty"] = new_auto
        p["qty"] = new_auto
        p["external_qty"] = new_external
        p["broker_held_qty"] = held
        p["broker_sellable_qty"] = "" if sellable is None else sellable
        p["broker_avg_price"] = broker_avg
        p["broker_updated_at"] = datetime.now()

        if held == 0 or new_auto <= 0:
            p["status"] = "EXTERNAL_EXIT_CONFIRMED"
            should_external_close = True
        else:
            should_external_close = False

    if should_external_close:
        _finalize_external_exit(code, source="EXIT_PRECHECK_HELD_ZERO")
        return True

    if sellable is None:
        with STATE_LOCK:
            p = live_positions.get(code)
            if p:
                p["status"] = "EXIT_ERROR"
        mark_code_blocked(code, "EXIT_ERROR", "broker sellable_qty 필드 확인불가")
        send_telegram(
            "🚨 실제 자동매도 오류\n"
            f"{stock_name} ({code})\n"
            "계좌 매도가능수량을 신뢰할 수 없어 임의 매도하지 않습니다."
        )
        return False

    sellable = max(0, safe_int(sellable))
    qty = min(new_auto, sellable)
    if qty <= 0:
        with STATE_LOCK:
            p = live_positions.get(code)
            if p:
                p["status"] = "EXIT_ERROR"
        mark_code_blocked(code, "EXIT_ERROR", f"held={held}, sellable={sellable}, auto={new_auto}")
        send_telegram(
            "🚨 실제 자동매도 오류\n"
            f"{stock_name} ({code})\n"
            f"자동관리 : {new_auto}주 / 계좌보유 : {held}주 / 매도가능 : {sellable}주\n"
            "매도가능수량이 없어 자동 재시도하지 않습니다."
        )
        return False

    # qty가 auto보다 작으면 확인된 sellable만 사용. 같은 주문 완료 후 잔여 자동물량은 재검증 상태로 둡니다.
    with STATE_LOCK:
        p = live_positions.get(code)
        if not p or p.get("status") != "EXIT_VALIDATING":
            return False
        p["status"] = "EXIT_SUBMITTING"
        p["auto_managed_qty_before_exit"] = new_auto
        p["pending_auto_sell_qty"] = qty
        p["quantity_corrected_before_exit"] = quantity_corrected
        p["quantity_before_correction"] = old_auto

    save_live_state()

    if shutdown_requested:
        return False

    try:
        response = submit_stock_order(
            "SELL", code, qty, exchange, stock_name=stock_name
        )
        ord_no = str(response.get("ord_no", "")).strip()
        sell_order_time = datetime.now()

        with STATE_LOCK:
            p = live_positions.get(code)
            if not p:
                return False
            p["status"] = "EXIT_PENDING"
            p["exit_order_no"] = ord_no
            p["live_exit_order_time"] = sell_order_time
            p["sell_order_time"] = sell_order_time
            p["trigger_to_order_sec"] = _elapsed_seconds_v168(
                p.get("exit_trigger_time", ""), sell_order_time
            )

            live_orders[ord_no] = _normalize_live_order_state({
                "order_no": ord_no,
                "side": "SELL",
                "stock_code": code,
                "stock_name": stock_name,
                "requested_qty": qty,
                "filled_qty": 0,
                "broker_filled_qty": 0,
                "unfilled_qty": qty,
                "filled_amount": 0.0,
                "status": "SUBMITTED",
                "exchange": exchange,
                "reason": reason,
                "paper_trade_id": p.get("paper_trade_id", ""),
                "entry_mode": p.get("entry_mode", ""),
                "pre_entry_type": p.get("pre_entry_type", ""),
                "watch_episode_id": p.get("watch_episode_id", ""),
                "entry_seq": entry_seq,
                "broker_precheck_start_time": broker_precheck_start_time,
                "broker_precheck_end_time": broker_precheck_end_time,
                "broker_precheck_sec": broker_precheck_sec,
                "sell_order_time": sell_order_time,
                "trigger_to_order_sec": _elapsed_seconds_v168(
                    p.get("exit_trigger_time", ""), sell_order_time
                ),
            })

        _clear_submit_intent(code, "SELL")
        save_live_state()
        replay_unmatched_order_events(ord_no)

        send_telegram(
            f"{stock_name} / {reason_to_korean(reason)} 매도주문 / {qty}주\n\n"
            "🔵 실제 자동매도 주문 접수\n\n"
            f"{stock_name} ({code})\n"
            f"사유 : {reason_to_korean(reason)}\n"
            f"계좌 보유수량 : {held}주\n"
            f"계좌 매도가능수량 : {sellable}주\n"
            f"자동 매도수량 : {qty}주\n"
            f"주문번호 : {ord_no}"
        )
        return True

    except OrderStatusUnknownError as e:
        with STATE_LOCK:
            p = live_positions.get(code)
            if p:
                p["status"] = "ORDER_STATUS_UNKNOWN"
        set_live_system_halt(
            "ORDER_STATUS_UNKNOWN",
            code=code,
            stock_name=stock_name,
            detail=str(e),
        )
        return False

    except ShutdownRequestedError:
        _clear_submit_intent(code, "SELL")
        return False

    except Exception as e:
        _clear_submit_intent(code, "SELL")
        with STATE_LOCK:
            p = live_positions.get(code)
            if p:
                p["status"] = "EXIT_ERROR"
                p["pending_auto_sell_qty"] = 0
        mark_code_blocked(code, "EXIT_ERROR", str(e))
        send_telegram(
            "🚨 실제 자동매도 주문 실패\n"
            f"{stock_name} ({code})\n"
            f"사유 : {e}\n"
            "자동 반복매도는 차단되었습니다."
        )
        return False



def request_entry_cancel_for_exit(code, reason):
    """BUY 부분체결 중 TP/SL 발생 시 남은 자동 BUY 잔량만 취소 후 체결분 청산."""
    code = clean_stock_code(code)
    if shutdown_requested:
        return False

    with STATE_LOCK:
        p = live_positions.get(code)
        if not p:
            return False
        if p.get("entry_complete", False):
            return submit_live_exit(code, reason)
        if p.get("status") in ["ENTRY_CANCEL_SUBMITTING", "ENTRY_CANCEL_PENDING"]:
            return True

        original_order_no = str(p.get("entry_order_no", "")).strip()
        order = live_orders.get(original_order_no)
        if not original_order_no or order is None:
            mark_code_blocked(code, "POSITION_MISMATCH", "원매수 주문상태 없음")
            return False

        remaining_qty = max(
            0,
            safe_int(order.get("requested_qty", 0)) - safe_int(order.get("filled_qty", 0))
        )
        if remaining_qty <= 0:
            p["entry_complete"] = True
            p["status"] = "OPEN"
            return submit_live_exit(code, reason)

        p["status"] = "ENTRY_CANCEL_SUBMITTING"
        p["pending_exit_reason"] = reason
        exchange = order.get("exchange", p.get("exchange", LIVE_MAIN_EXCHANGE))
        stock_name = p.get("stock_name", code)

    save_live_state()

    try:
        response = submit_cancel_order(
            original_order_no, code, exchange, 0, stock_name=stock_name
        )
        cancel_order_no = str(response.get("ord_no", "")).strip()

        with STATE_LOCK:
            original = live_orders.get(original_order_no)
            if original:
                original["status"] = "CANCEL_PENDING"

            live_orders[cancel_order_no] = _normalize_live_order_state({
                "order_no": cancel_order_no,
                "side": "CANCEL",
                "stock_code": code,
                "stock_name": stock_name,
                "requested_qty": 0,
                "filled_qty": 0,
                "filled_amount": 0.0,
                "status": "SUBMITTED",
                "exchange": exchange,
                "original_order_no": original_order_no,
                "reason": reason,
            })
            p = live_positions.get(code)
            if p:
                p["status"] = "ENTRY_CANCEL_PENDING"

        _clear_submit_intent(code, "CANCEL")
        save_live_state()
        replay_unmatched_order_events(cancel_order_no)
        return True

    except OrderStatusUnknownError as e:
        set_live_system_halt(
            "ORDER_STATUS_UNKNOWN",
            code=code,
            stock_name=stock_name,
            detail=f"부분체결 BUY 취소상태 불명확: {e}",
        )
        return False
    except Exception as e:
        _clear_submit_intent(code, "CANCEL")
        mark_code_blocked(code, "MANUAL_INTERVENTION_REQUIRED", f"부분체결 BUY 취소 실패: {e}")
        return False


def update_live_position_on_price(code, current_price):
    code = clean_stock_code(code)

    with STATE_LOCK:
        p = live_positions.get(code)
        if not p:
            return
        if p.get("status") not in ["OPEN", "POSITION_MISMATCH"]:
            return
        if safe_int(p.get("auto_managed_qty", p.get("qty", 0))) <= 0:
            return

        p["last_price"] = current_price
        target = safe_float(p.get("target_price", float("inf")))
        stop = safe_float(p.get("stop_price", 0))
        entry_complete = bool(p.get("entry_complete", False))

    reason = None
    if current_price >= target:
        reason = "TAKE_PROFIT"
    elif current_price <= stop:
        reason = "STOP_LOSS"

    if reason is None:
        return

    if entry_complete:
        submit_live_exit(code, reason, trigger_price=current_price)
    else:
        request_entry_cancel_for_exit(code, reason)


def _finish_buy_cancel_event(code, cancel_order_no, original_order_no, status_text):
    pending_reason = None
    qty = 0

    with STATE_LOCK:
        cancel_order = live_orders.get(cancel_order_no)
        if cancel_order:
            cancel_order["status"] = "CANCEL_CONFIRMED"
            cancel_order["broker_status"] = status_text
            if not original_order_no:
                original_order_no = str(cancel_order.get("original_order_no", "")).strip()

        original = live_orders.get(original_order_no)
        if original:
            original["status"] = "CANCELED"
            original["broker_status"] = status_text

        p = live_positions.get(code)
        if p:
            p["entry_complete"] = True
            qty = safe_int(p.get("auto_managed_qty", p.get("qty", 0)))
            if p.get("status") in ["ENTRY_CANCEL_SUBMITTING", "ENTRY_CANCEL_PENDING"]:
                pending_reason = p.pop("pending_exit_reason", None)
                if qty > 0:
                    p["status"] = "OPEN"

    save_live_order_event({
        "event": "CANCEL_CONFIRMED",
        "side": "CANCEL",
        "stock_code": code,
        "order_no": cancel_order_no,
        "original_order_no": original_order_no,
        "broker_status": status_text,
    })
    save_live_state()

    if qty > 0 and pending_reason:
        submit_live_exit(code, pending_reason)
    else:
        maybe_release_realtime(code)


def _schedule_unmatched_resolution(order_no):
    order_no = str(order_no).strip()
    with STATE_LOCK:
        if order_no in live_external_resolution_pending:
            return
        live_external_resolution_pending.add(order_no)

    def worker():
        started = time.time()
        try:
            while True:
                time.sleep(EXTERNAL_EVENT_RESOLVE_DELAY_SEC)

                with STATE_LOCK:
                    if order_no in live_orders:
                        events = live_unmatched_order_events.pop(order_no, [])
                        is_internal = True
                    else:
                        events = list(live_unmatched_order_events.get(order_no, []))
                        is_internal = False

                if is_internal:
                    for event in events:
                        handle_order_execution(event)
                    return

                if not events:
                    return

                sample = events[-1]
                code = clean_stock_code(sample.get("9001", ""))

                # 이 code에 로컬 REST submit이 진행 중이면 외부주문 판정을 유예.
                if _active_submit_intent_for_code(code):
                    if time.time() - started <= LOCAL_SUBMIT_INTENT_MAX_SEC:
                        continue

                    # 로컬 submit 의도 중 끝내 주문번호를 연결하지 못했으면
                    # 사용자 수동주문으로 오인하지 않고 ORDER_STATUS_UNKNOWN 취급.
                    with STATE_LOCK:
                        unknown_events = live_unmatched_order_events.pop(order_no, [])
                    stock_name = stock_display_name(code)
                    save_live_order_event({
                        "event": "ORDER_STATUS_UNKNOWN",
                        "stock_code": code,
                        "stock_name": stock_name,
                        "order_no": order_no,
                        "reason": "ORDER_STATUS_UNKNOWN",
                        "error": "로컬 submit intent와 WS 이벤트를 주문번호로 연결하지 못함",
                    })
                    if not live_trading_halted:
                        set_live_system_halt(
                            "ORDER_STATUS_UNKNOWN",
                            code=code,
                            stock_name=stock_name,
                            detail="REST/WS 주문 연결 실패",
                        )
                    return

                with STATE_LOCK:
                    external_events = live_unmatched_order_events.pop(order_no, [])
                for event in external_events:
                    handle_external_order_event(event)
                return
        finally:
            with STATE_LOCK:
                live_external_resolution_pending.discard(order_no)

    LIVE_ASYNC_EXECUTOR.submit(worker)


def replay_unmatched_order_events(order_no):
    order_no = str(order_no).strip()
    with STATE_LOCK:
        events = live_unmatched_order_events.pop(order_no, [])
    for event in events:
        handle_order_execution(event)


def _parse_event_side(values):
    text = str(values.get("905", ""))
    if "매수" in text:
        return "BUY"
    if "매도" in text:
        return "SELL"
    return ""


def handle_external_order_event(values):
    """
    프로그램 주문번호가 아닌 사용자/외부 주문.

    - 프로그램과 무관한 다른 종목 개인매매는 자동포지션/손익/진입카운트에 편입하지 않음.
    - 자동관리 종목의 외부 SELL만 requested-unfilled 누적체결 원장에 기록.
    - 자동관리 종목의 외부 BUY는 기존 정책대로 external_qty 동기화 대상으로만 처리.
    """
    if not isinstance(values, dict):
        return

    code = clean_stock_code(values.get("9001", ""))
    ord_no = str(values.get("9203", "")).strip()
    side = _parse_event_side(values)
    status_text = str(values.get("913", ""))

    if not code or not side:
        return

    tracking = {
        "requested_qty": max(0, safe_int(values.get("900", 0))),
        "broker_filled_qty": "",
        "delta_qty": "",
        "unfilled_qty": max(0, safe_int(values.get("902", 0))),
        "fill_price": abs_price(values.get("910", 0)),
        "fill_no": str(values.get("909", "")).strip(),
        "order_no": ord_no,
        "quantity_known": False,
    }

    with STATE_LOCK:
        managed = code in live_positions

        if side == "BUY":
            # 사용자가 직접 산 종목은 실제 자동진입 대상에서 제외하는 기존 정책 유지.
            broker_startup_holdings.add(code)

        if not managed:
            # 다른 개인매매는 live 손익/카운트/포지션에 영향 없음.
            return

        p = live_positions.get(code)
        _normalize_live_position_state(p)
        stock_name = p.get("stock_name", code)

        if side == "SELL":
            tracking = _track_external_sell_execution(p, values)

        p["status"] = "EXTERNAL_ORDER_DETECTED"
        live_blocked_codes[code] = {
            "reason": "EXTERNAL_ORDER_DETECTED",
            "detail": f"외부 {side} 주문 {ord_no}",
            "time": datetime.now(),
        }

    save_live_order_event({
        "event": "EXTERNAL_ORDER_DETECTED",
        "side": side,
        "stock_code": code,
        "stock_name": stock_name,
        "order_no": ord_no,
        "fill_no": tracking.get("fill_no", ""),
        "requested_qty": tracking.get("requested_qty", ""),
        "broker_filled_qty": tracking.get("broker_filled_qty", ""),
        "delta_qty": tracking.get("delta_qty", ""),
        "unfilled_qty": tracking.get("unfilled_qty", ""),
        "fill_price": tracking.get("fill_price", ""),
        "broker_status": status_text,
        "reason": "EXTERNAL_ORDER_DETECTED",
    })

    save_live_state()

    # broker 잔고를 기준으로 external_qty -> auto_managed_qty 순서로 실제 감소분 확정.
    schedule_broker_sync(
        code,
        reason="EXTERNAL_ORDER_DETECTED",
        external_event=True,
    )



def _build_buy_fill_message(p, order):
    entry_seq = p.get("entry_seq", order.get("entry_seq", ""))
    qty = safe_int(order.get("filled_qty", 0))
    avg = safe_float(p.get("avg_entry_price", 0))
    amount = avg * qty
    return (
        f"{p['stock_name']} / 매수 / {qty}주 / {avg:,.0f}원\n\n"
        "✅ 실제 자동매수 체결완료\n\n"
        f"{p['stock_name']} ({p['stock_code']})\n\n"
        f"진입전략 : {p.get('pre_entry_type','FIRST_75_PASS')}\n"
        f"주문수량 : {qty}주\n"
        f"평균체결가 : {avg:,.0f}원\n"
        f"실제매수금액 : {amount:,.0f}원\n\n"
        f"익절기준 : +2.00% / 목표가 {safe_float(p.get('target_price',0)):,.0f}원\n"
        f"손절기준 : -1.50% / 손절가 {safe_float(p.get('stop_price',0)):,.0f}원\n\n"
        + live_slot_lines(entry_seq)
    )


def _build_sell_fill_message(p, order, final_exit_price, ret, pnl):
    reason = p.get("exit_reason", order.get("reason", "EXIT"))
    reason_ko = reason_to_korean(reason)
    entry_seq = p.get("entry_seq", order.get("entry_seq", ""))
    qty = safe_int(order.get("filled_qty", 0))
    base = (
        f"{p['stock_name']} / {reason_ko} / {ret:+.2f}% / {pnl:+,.0f}원\n\n"
        "🏁 실제 자동매매 청산완료\n\n"
        f"{p['stock_name']} ({p['stock_code']})\n\n"
        f"청산사유 : {reason_ko}\n"
        f"전략 기준매입가 : {safe_float(p.get('avg_entry_price',0)):,.0f}원\n"
        f"실제 평균매도가 : {final_exit_price:,.0f}원\n"
        f"수량 : {qty}주\n\n"
        f"익절기준 : +2.00% / 목표가 {safe_float(p.get('target_price',0)):,.0f}원\n"
        f"손절기준 : -1.50% / 손절가 {safe_float(p.get('stop_price',0)):,.0f}원\n"
        f"실제수익률 : {ret:+.2f}%\n"
        f"실현손익 : {pnl:+,.0f}원"
    )

    if p.get("quantity_corrected_before_exit"):
        base += (
            "\n\n⚠ 수량 보정\n"
            f"내부수량 : {safe_int(p.get('quantity_before_correction',0))}주\n"
            f"계좌 보유수량 : {safe_int(p.get('broker_held_qty',0))}주\n"
            f"계좌 매도가능수량 : {safe_int(p.get('broker_sellable_qty',0))}주\n"
            f"{qty}주 기준으로 자동매도 완료"
        )

    return base + "\n\n" + live_slot_lines(entry_seq)


def handle_order_execution(values):
    global live_daily_realized_pnl
    global live_trading_halted
    global live_system_halt_reason

    if not isinstance(values, dict):
        return

    code = clean_stock_code(values.get("9001", ""))
    ord_no = str(values.get("9203", "")).strip()
    if not code or not ord_no:
        return

    original_order_no = str(values.get("904", "")).strip()
    fill_price = abs_price(values.get("910", 0))
    event_fill_qty = safe_int(values.get("911", 0))  # 참고/로그용; 누적에 직접 더하지 않음
    unfilled_qty = safe_int(values.get("902", 0))
    status_text = str(values.get("913", ""))
    fill_no = str(values.get("909", "")).strip()
    reject_reason = str(values.get("919", "")).strip()

    with STATE_LOCK:
        order = live_orders.get(ord_no)

    if order is None:
        # own REST response보다 WS가 먼저 도착했을 가능성을 잠시 유예한 뒤 외부주문 판정.
        with STATE_LOCK:
            bucket = live_unmatched_order_events.setdefault(ord_no, [])
            bucket.append(dict(values))
            if len(bucket) > 20:
                del bucket[:-20]
        _schedule_unmatched_resolution(ord_no)
        return

    _normalize_live_order_state(order)
    side = order.get("side") or _parse_event_side(values)
    stock_name = order.get("stock_name") or stock_display_name(code)

    if side == "CANCEL" and fill_price <= 0 and "확인" in status_text:
        _finish_buy_cancel_event(code, ord_no, original_order_no, status_text)
        return

    if "거부" in status_text or "거부" in str(values.get("905", "")):
        with STATE_LOCK:
            order = live_orders.get(ord_no)
            if order:
                order["status"] = "REJECTED"
                order["broker_status"] = status_text
                order["reject_reason"] = reject_reason

            p = live_positions.get(code)
            if side == "SELL" and p:
                p["status"] = "EXIT_ERROR"
                p["pending_auto_sell_qty"] = 0
                live_blocked_codes[code] = {
                    "reason": "EXIT_ERROR",
                    "detail": reject_reason or status_text,
                    "time": datetime.now(),
                }
            if side == "CANCEL" and p and p.get("status") in ["ENTRY_CANCEL_SUBMITTING", "ENTRY_CANCEL_PENDING"]:
                p["status"] = "MANUAL_INTERVENTION_REQUIRED"
                live_blocked_codes[code] = {
                    "reason": "MANUAL_INTERVENTION_REQUIRED",
                    "detail": "부분체결 BUY 취소 거부",
                    "time": datetime.now(),
                }

        save_live_order_event({
            "event": "ORDER_REJECTED",
            "side": side,
            "stock_code": code,
            "stock_name": stock_name,
            "order_no": ord_no,
            "requested_qty": order.get("requested_qty", ""),
            "broker_filled_qty": order.get("filled_qty", 0),
            "unfilled_qty": unfilled_qty,
            "broker_status": status_text,
            "reason": "EXIT_ERROR" if side == "SELL" else "REJECTED",
            "error": reject_reason,
        })
        save_live_state()

        send_telegram(
            "🚨 실제 주문 거부\n"
            f"{stock_name} ({code})\n"
            f"구분 : {side}\n"
            f"주문번호 : {ord_no}\n"
            f"상태 : {status_text}\n"
            f"사유 : {reject_reason}\n"
            + ("자동 반복매도는 차단되었습니다." if side == "SELL" else "동일종목 자동 재주문은 하지 않습니다.")
        )
        return

    with STATE_LOCK:
        order = live_orders.get(ord_no)
        if order:
            order["broker_status"] = status_text

    # 체결가가 없는 접수/확인 이벤트는 상태만 저장.
    if fill_price <= 0:
        save_live_state()
        return

    requested_qty = safe_int(order.get("requested_qty", 0))
    prev_filled_qty = safe_int(order.get("filled_qty", 0))

    try:
        broker_filled_qty, delta_qty = compute_broker_fill_delta(
            requested_qty, unfilled_qty, prev_filled_qty
        )
    except Exception as e:
        _record_execution_qty_issue(
            code,
            stock_name,
            f"requested={requested_qty}, event911={event_fill_qty}, unfilled={unfilled_qty}, "
            f"prev={prev_filled_qty} / {e}"
        )
        return

    # 동일 누적체결 이벤트 재수신이면 수량/금액을 다시 더하지 않습니다.
    if delta_qty == 0:
        with STATE_LOCK:
            order = live_orders.get(ord_no)
            if order:
                order["broker_filled_qty"] = broker_filled_qty
                order["unfilled_qty"] = unfilled_qty
                order["status"] = "FILLED" if unfilled_qty == 0 else "PARTIAL"
        save_live_order_event({
            "event": "FILL_DUPLICATE_CUMULATIVE",
            "side": side,
            "stock_code": code,
            "stock_name": stock_name,
            "order_no": ord_no,
            "fill_no": fill_no,
            "requested_qty": requested_qty,
            "broker_filled_qty": broker_filled_qty,
            "delta_qty": 0,
            "unfilled_qty": unfilled_qty,
            "fill_price": fill_price,
            "broker_status": status_text,
        })
        save_live_state()
        return

    fill_key = (ord_no, fill_no, str(broker_filled_qty), str(fill_price))
    with STATE_LOCK:
        if fill_key in live_processed_fill_ids:
            return
        live_processed_fill_ids.add(fill_key)

    save_live_order_event({
        "event": "FILL",
        "side": side,
        "stock_code": code,
        "stock_name": stock_name,
        "order_no": ord_no,
        "fill_no": fill_no,
        "requested_qty": requested_qty,
        "broker_filled_qty": broker_filled_qty,
        "delta_qty": delta_qty,
        "unfilled_qty": unfilled_qty,
        "fill_price": fill_price,
        "broker_status": status_text,
        "paper_trade_id": order.get("paper_trade_id", ""),
        "entry_mode": order.get("entry_mode", ""),
        "pre_entry_type": order.get("pre_entry_type", ""),
        "watch_episode_id": order.get("watch_episode_id", ""),
        "entry_seq": order.get("entry_seq", ""),
        "broker_precheck_start_time": _csv_datetime(order.get("broker_precheck_start_time", "")),
        "broker_precheck_end_time": _csv_datetime(order.get("broker_precheck_end_time", "")),
        "broker_precheck_sec": order.get("broker_precheck_sec", ""),
        "sell_order_time": _csv_datetime(order.get("sell_order_time", "")),
        "trigger_to_order_sec": order.get("trigger_to_order_sec", ""),
    })

    if side == "BUY":
        pending_exit_reason = None
        fully_filled = (unfilled_qty == 0)

        with STATE_LOCK:
            order = live_orders[ord_no]
            order["filled_qty"] = broker_filled_qty
            order["broker_filled_qty"] = broker_filled_qty
            order["unfilled_qty"] = unfilled_qty
            order["filled_amount"] = safe_float(order.get("filled_amount", 0)) + fill_price * delta_qty
            order["status"] = "FILLED" if fully_filled else "PARTIAL"
            order["pending_auto_buy_qty"] = max(0, requested_qty - broker_filled_qty)

            p = live_positions.get(code)
            if p is None:
                p = _normalize_live_position_state({
                    "stock_code": code,
                    "stock_name": stock_name,
                    "qty": 0,
                    "auto_managed_qty": 0,
                    "external_qty": 0,
                    "initial_qty": 0,
                    "filled_amount": 0.0,
                    "avg_entry_price": 0.0,
                    "entry_time": datetime.now(),
                    "entry_order_no": ord_no,
                    "exit_order_no": "",
                    "exchange": order["exchange"],
                    "status": "OPEN",
                    "entry_complete": False,
                    "signal_price": order["signal_price"],
                    "signal_time_str": order["signal_time_str"],
                    "live_order_time": order.get("live_order_time", ""),
                    "live_fill_time": datetime.now(),
                    "paper_trade_id": order.get("paper_trade_id", ""),
                    "entry_mode": order.get("entry_mode", ""),
                    "pre_entry_type": order.get("pre_entry_type", ""),
                    "watch_episode_id": order.get("watch_episode_id", ""),
                    "entry_seq": order.get("entry_seq", ""),
                    "score": order.get("score", 0),
                    "last_price": fill_price,
                })
                live_positions[code] = p

            p["auto_managed_qty"] = safe_int(p.get("auto_managed_qty", 0)) + delta_qty
            p["qty"] = p["auto_managed_qty"]
            p["initial_qty"] = p["auto_managed_qty"]
            p["filled_amount"] = safe_float(p.get("filled_amount", 0)) + fill_price * delta_qty
            p["avg_entry_price"] = p["filled_amount"] / p["auto_managed_qty"]
            p["live_fill_time"] = datetime.now()
            p["pending_auto_buy_qty"] = max(0, requested_qty - broker_filled_qty)

            signal_dt = order.get("signal_time")
            if isinstance(signal_dt, datetime):
                p["live_entry_delay_sec"] = max(0.0, (p["live_fill_time"] - signal_dt).total_seconds())
            else:
                p["live_entry_delay_sec"] = ""

            signal_px = safe_float(order.get("signal_price", 0))
            p["live_vs_signal_pct"] = (
                (p["avg_entry_price"] / signal_px - 1) * 100 if signal_px > 0 else ""
            )

            # 전략기준가는 프로그램 자동체결 평균가. broker avg_price로 재계산하지 않습니다.
            rule = EXIT_STRATEGIES[LIVE_STRATEGY]
            p["target_price"] = p["avg_entry_price"] * (1 + rule["tp"] / 100)
            p["stop_price"] = p["avg_entry_price"] * (1 + rule["sl"] / 100)
            p["entry_complete"] = fully_filled

            if fully_filled and p.get("status") in ["ENTRY_CANCEL_SUBMITTING", "ENTRY_CANCEL_PENDING"]:
                pending_exit_reason = p.pop("pending_exit_reason", None)
                p["status"] = "OPEN"

            msg_position = dict(p)
            msg_order = dict(order)

        save_live_state()
        schedule_broker_sync(code, reason="AUTO_BUY_FILL", external_event=False)

        if fully_filled:
            send_telegram(_build_buy_fill_message(msg_position, msg_order))
            if pending_exit_reason:
                submit_live_exit(code, pending_exit_reason)

    elif side == "SELL":
        completed = False
        residual_error = False
        final_exit_price = fill_price
        position_copy = None

        with STATE_LOCK:
            order = live_orders[ord_no]
            order["filled_qty"] = broker_filled_qty
            order["broker_filled_qty"] = broker_filled_qty
            order["unfilled_qty"] = unfilled_qty
            order["filled_amount"] = safe_float(order.get("filled_amount", 0)) + fill_price * delta_qty
            order["status"] = "FILLED" if unfilled_qty == 0 else "PARTIAL"
            order["pending_auto_sell_qty"] = max(0, requested_qty - broker_filled_qty)

            p = live_positions.get(code)
            if p is None:
                _record_execution_qty_issue(code, stock_name, "SELL 체결인데 내부 자동포지션 없음")
                return

            p["auto_managed_qty"] = max(0, safe_int(p.get("auto_managed_qty", p.get("qty", 0))) - delta_qty)
            p["qty"] = p["auto_managed_qty"]
            p["pending_auto_sell_qty"] = max(0, requested_qty - broker_filled_qty)

            if unfilled_qty == 0:
                final_exit_price = (
                    safe_float(order.get("filled_amount", 0)) / broker_filled_qty
                    if broker_filled_qty > 0 else fill_price
                )

                sell_fill_time = datetime.now()
                p["live_exit_fill_time"] = sell_fill_time
                p["sell_fill_time"] = sell_fill_time
                p["order_to_fill_sec"] = _elapsed_seconds_v168(
                    p.get("sell_order_time", p.get("live_exit_order_time", "")),
                    sell_fill_time,
                )
                p["trigger_to_fill_sec"] = _elapsed_seconds_v168(
                    p.get("exit_trigger_time", ""), sell_fill_time
                )
                p["exit_filled_qty"] = broker_filled_qty

                if p["auto_managed_qty"] == 0:
                    completed = True
                    p["status"] = "CLOSED"
                    position_copy = dict(p)
                else:
                    # 확인된 sellable 일부만 매도됐거나 수동개입이 섞인 경우 반복주문 금지.
                    p["status"] = "POSITION_MISMATCH"
                    p["pending_auto_sell_qty"] = 0
                    live_blocked_codes[code] = {
                        "reason": "POSITION_MISMATCH",
                        "detail": f"SELL 전량체결 후 자동관리 잔량 {p['auto_managed_qty']}주",
                        "time": datetime.now(),
                    }
                    residual_error = True

        save_live_state()
        schedule_broker_sync(code, reason="AUTO_SELL_FILL", external_event=False)

        if completed and position_copy:
            pnl, ret = save_live_trade_result(
                position_copy, final_exit_price, position_copy.get("exit_reason", order.get("reason", "EXIT"))
            )

            with STATE_LOCK:
                live_daily_realized_pnl += pnl
                if LIVE_DAILY_MAX_LOSS_WON > 0 and live_daily_realized_pnl <= -LIVE_DAILY_MAX_LOSS_WON:
                    live_trading_halted = True
                    live_system_halt_reason = "일일 손실한도 도달"
                live_positions.pop(code, None)
                live_blocked_codes.pop(code, None)

            save_live_state()
            send_telegram(_build_sell_fill_message(position_copy, order, final_exit_price, ret, pnl))
            maybe_release_realtime(code)

        elif residual_error:
            send_telegram(
                "🚨 보유수량 불일치\n"
                f"{stock_name} ({code})\n"
                "자동매도 주문은 전량체결됐지만 자동관리 잔량이 남았습니다.\n"
                "해당 종목 추가 자동주문을 차단하고 broker 동기화를 진행합니다."
            )



def _pct_change(base_price, price):
    base_price = safe_float(base_price, 0)
    price = safe_float(price, 0)
    if base_price <= 0 or price <= 0:
        return None
    return (price - base_price) / base_price * 100


def capture_first_ws_tick(code, price, observed_time=None):
    """각 paper trade_id의 최초 WebSocket 0B 가격을 한 번만 기록합니다."""
    code = clean_stock_code(code)
    if price <= 0:
        return

    if observed_time is None:
        observed_time = datetime.now()

    trade_ids = list(paper_position_ids_by_code.get(code, set()))
    for trade_id in trade_ids:
        p = paper_positions.get(trade_id)
        if not p or p.get("first_ws_time") is not None:
            continue

        signal_time = p.get("signal_time")
        if not isinstance(signal_time, datetime):
            signal_time = p.get("entry_time")

        delay_sec = None
        if isinstance(signal_time, datetime):
            delay_sec = max(
                0.0,
                (observed_time - signal_time).total_seconds()
            )

        vs_signal = _pct_change(p.get("signal_price"), price)
        vs_entry = _pct_change(p.get("entry_price"), price)

        p["first_ws_time"] = observed_time
        p["first_ws_price"] = price
        p["first_ws_delay_sec"] = delay_sec
        p["first_ws_vs_signal_pct"] = vs_signal
        p["first_ws_vs_entry_pct"] = vs_entry
        p["first_ws_gap_abs_pct"] = (
            abs(vs_signal) if vs_signal is not None else None
        )

        # entry-path tracker에도 같은 값을 복사해 연구 CSV에서 재사용 가능하게 합니다.
        tracker = entry_path_trackers.get(trade_id)
        if tracker is not None and tracker.get("first_ws_time") is None:
            for key in [
                "first_ws_time", "first_ws_price", "first_ws_delay_sec",
                "first_ws_vs_signal_pct", "first_ws_vs_entry_pct",
                "first_ws_gap_abs_pct",
            ]:
                tracker[key] = p.get(key)


def handle_realtime_price(code, price, values=None):

    code = clean_stock_code(code)
    if price <= 0:
        return

    now = datetime.now()

    with STATE_LOCK:
        realtime_prices[code] = price
        realtime_price_ts[code] = time.time()

    # 반드시 paper position 업데이트보다 먼저 기록해야 첫 틱에서 즉시 청산되어도 남습니다.
    capture_first_ws_tick(code, price, now)

    update_paper_position(code, price)
    update_entry_path_tracking(code, price, now)
    update_post_exit_tracking(code, price)

    if AUTO_TRADE_ENABLED:
        update_live_position_on_price(code, price)

def maybe_release_realtime(code):

    code = clean_stock_code(code)

    with STATE_LOCK:
        paper_open = bool(paper_position_ids_by_code.get(code))
        entry_path_open = bool(entry_path_ids_by_code.get(code))
        post_exit_open = bool(post_exit_ids_by_code.get(code))
        live_open = code in live_positions
        live_order_open = any(
            o.get("stock_code") == code
            and o.get("status") in ["SUBMITTED", "PARTIAL", "CANCEL_PENDING"]
            for o in live_orders.values()
        )

    if (
        not paper_open
        and not entry_path_open
        and not post_exit_open
        and not live_open
        and not live_order_open
        and websocket_manager is not None
    ):
        websocket_manager.unsubscribe_stock(code)


def _is_normal_websocket_close(exc):
    """websockets 버전 차이를 흡수해 정상 close(1000/1001)를 판별합니다."""
    if exc is None:
        return False

    try:
        exc_mod = getattr(websockets, "exceptions", None) if websockets else None
        ok_cls = getattr(exc_mod, "ConnectionClosedOK", None)
        if ok_cls is not None and isinstance(exc, ok_cls):
            return True
    except Exception:
        pass

    codes = []
    direct_code = getattr(exc, "code", None)
    if direct_code is not None:
        codes.append(direct_code)

    for attr in ["rcvd", "sent"]:
        frame = getattr(exc, attr, None)
        frame_code = getattr(frame, "code", None)
        if frame_code is not None:
            codes.append(frame_code)

    if any(code in [1000, 1001] for code in codes):
        return True

    text = str(exc)
    return (
        "1000 (OK)" in text
        or "1001 (going away)" in text.lower()
    )


class KiwoomRealtimeManager:

    def __init__(self):
        self.url = get_websocket_url()
        self.thread = None
        self.loop = None
        self.websocket = None
        self.connected = False
        self.logged_in = False
        self.keep_running = False
        self.desired_items = {}
        self.lock = threading.RLock()
        self.reg_async_lock = None
        self.last_reg_send_ts = 0.0

    def start(self):
        if not WEBSOCKET_ENABLED:
            return

        if websockets is None:
            raise ImportError(
                "websockets 패키지가 없습니다. "
                "Jupyter에서 !pip install websockets 실행 후 커널을 재시작하세요."
            )

        if self.thread and self.thread.is_alive():
            return

        self.keep_running = True
        self.thread = threading.Thread(
            target=self._thread_main,
            daemon=True,
            name="KiwoomWebSocket"
        )
        self.thread.start()

    def stop(self):
        self.keep_running = False
        if self.loop and self.websocket:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.close(),
                    self.loop
                )
            except Exception:
                pass

    def _thread_main(self):
        asyncio.run(self._run_forever())

    async def _run_forever(self):
        self.loop = asyncio.get_running_loop()
        self.reg_async_lock = asyncio.Lock()

        while self.keep_running:
            try:
                await self._connect_once()
            except Exception as e:
                self.connected = False
                self.logged_in = False
                self.websocket = None

                if _is_normal_websocket_close(e):
                    if not self.keep_running:
                        log("[WebSocket] 정상 종료")
                        break
                    log("[WebSocket] 연결 정상 종료 / 재연결")
                    await asyncio.sleep(1)
                    continue

                log(f"[WebSocket 재연결 대기] {e}")
                if self.keep_running:
                    await asyncio.sleep(3)

    async def _connect_once(self):
        global ACCESS_TOKEN

        if not ACCESS_TOKEN:
            get_kiwoom_token()

        async with websockets.connect(
            self.url,
            ping_interval=None,
            close_timeout=5
        ) as ws:
            self.websocket = ws
            self.connected = True
            self.logged_in = False
            self.last_reg_send_ts = 0.0

            await self._send({"trnm": "LOGIN", "token": ACCESS_TOKEN})
            log("[WebSocket] 연결 / LOGIN 전송")

            while self.keep_running:
                raw = await ws.recv()
                response = json.loads(raw)
                trnm = response.get("trnm")

                if trnm == "PING":
                    await self._send(response)
                    continue

                if trnm == "LOGIN":
                    if response.get("return_code") not in [0, "0"]:
                        raise Exception(f"WebSocket 로그인 실패: {response}")

                    self.logged_in = True
                    log("[WebSocket] 로그인 성공")

                    if AUTO_TRADE_ENABLED:
                        await self._register_order_stream()
                    await self._reregister_all()
                    continue

                if trnm == "REG":
                    if response.get("return_code") not in [0, "0", None]:
                        log(f"[WebSocket REG 오류] {response}")
                    continue

                if trnm != "REAL":
                    continue

                for real in response.get("data", []):
                    rtype = str(real.get("type", ""))
                    item = str(real.get("item", ""))
                    values = real.get("values", {})

                    if rtype == "0B":
                        code = clean_stock_code(item)
                        price = abs_price(values.get("10", 0))
                        handle_realtime_price(code, price, values)
                    elif rtype == "00":
                        handle_order_execution(values)

    async def _send(self, message):
        if self.websocket is None:
            return

        if not isinstance(message, str):
            message = json.dumps(message, ensure_ascii=False)
        await self.websocket.send(message)

    async def _paced_reg_send(self, message):
        if self.reg_async_lock is None:
            self.reg_async_lock = asyncio.Lock()

        async with self.reg_async_lock:
            elapsed = time.time() - self.last_reg_send_ts
            if elapsed < WEBSOCKET_REG_INTERVAL_SEC:
                await asyncio.sleep(WEBSOCKET_REG_INTERVAL_SEC - elapsed)

            last_error = None
            for attempt in range(1, WEBSOCKET_REG_RETRY_COUNT + 1):
                try:
                    await self._send(message)
                    self.last_reg_send_ts = time.time()
                    return
                except Exception as e:
                    last_error = e
                    if attempt < WEBSOCKET_REG_RETRY_COUNT:
                        await asyncio.sleep(WEBSOCKET_REG_RETRY_DELAY_SEC)

            raise last_error

    async def _register_order_stream(self):
        await self._paced_reg_send({
            "trnm": "REG",
            "grp_no": WEBSOCKET_GROUP_NO,
            "refresh": "1",
            "data": [{"item": [""], "type": ["00"]}]
        })

    async def _register_item(self, item):
        await self._paced_reg_send({
            "trnm": "REG",
            "grp_no": WEBSOCKET_GROUP_NO,
            "refresh": "1",
            "data": [{"item": [item], "type": ["0B"]}]
        })

    async def _remove_item(self, item):
        await self._send({
            "trnm": "REMOVE",
            "grp_no": WEBSOCKET_GROUP_NO,
            "data": [{"item": [item], "type": ["0B"]}]
        })

    async def _reregister_all(self):
        with self.lock:
            items = [
                item
                for item_set in self.desired_items.values()
                for item in item_set
            ]

        if items:
            log(f"[WebSocket] 재등록 {len(items)}건 / 간격 {WEBSOCKET_REG_INTERVAL_SEC:.2f}초")

        for item in items:
            await self._register_item(item)

    def subscribe_stock(self, stock_code, session=None):
        code = clean_stock_code(stock_code)
        item = realtime_item_code(code, session)

        with self.lock:
            s = self.desired_items.setdefault(code, set())
            if item in s:
                return
            s.add(item)

        if self.logged_in and self.loop is not None:
            asyncio.run_coroutine_threadsafe(
                self._register_item(item),
                self.loop
            )

    def unsubscribe_stock(self, stock_code):
        code = clean_stock_code(stock_code)

        with self.lock:
            items = list(self.desired_items.pop(code, set()))

        if self.logged_in and self.loop is not None:
            for item in items:
                asyncio.run_coroutine_threadsafe(
                    self._remove_item(item),
                    self.loop
                )


def start_websocket_manager():

    global websocket_manager

    if not WEBSOCKET_ENABLED:
        return None

    if websocket_manager is None:
        websocket_manager = (
            KiwoomRealtimeManager()
        )

    websocket_manager.start()

    return websocket_manager


def subscribe_recovered_live_items():

    if (
        not AUTO_TRADE_ENABLED
        or websocket_manager is None
    ):
        return

    with STATE_LOCK:
        codes = set(
            live_positions.keys()
        )

        for order in live_orders.values():
            if order.get("status") in [
                "SUBMITTED",
                "PARTIAL",
                "CANCEL_PENDING"
            ]:
                code = clean_stock_code(
                    order.get(
                        "stock_code",
                        ""
                    )
                )
                if code:
                    codes.add(code)

    # 실제 자동진입은 MAIN만 허용하므로 복구 구독도 SOR 체결로 등록
    for code in codes:
        websocket_manager.subscribe_stock(
            code,
            "MAIN"
        )


def force_close_live_positions():
    with STATE_LOCK:
        items = [
            (code, bool(p.get("entry_complete", False)))
            for code, p in live_positions.items()
            if p.get("status") in ["OPEN", "POSITION_MISMATCH"]
            and safe_int(p.get("auto_managed_qty", p.get("qty", 0))) > 0
        ]

    for code, entry_complete in items:
        if entry_complete:
            submit_live_exit(code, "TIME_EXIT")
        else:
            request_entry_cancel_for_exit(code, "TIME_EXIT")

# ============================================================
# 26. 신호 저장
# ============================================================

def save_signal(stock):

    actual = stock["actual_trading_value"]

    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": STRATEGY_VERSION,
        "session": stock.get("decision_session", get_session()),
        "scan_session": stock.get("scan_session", ""),
        "decision_session": stock.get("decision_session", ""),
        "decision_time": _csv_datetime(stock.get("decision_time", "")),
        "session_valid_at_decision": stock.get("session_valid_at_decision", ""),
        "market": stock["market"],
        "stock_code": stock["stock_code"],
        "stock_name": stock["stock_name"],
        "current_price": stock["current_price"],
        "change_rate": stock["change_rate"],
        "volume": stock["volume"],
        "actual_trading_value": actual if actual is not None else "",
        "estimated_trading_value": stock["estimated_trading_value"],
        "trading_value_used": stock["trading_value_used"],
        "trading_value_source": stock["trading_value_source"],
        "trading_value_rank": (
            stock["trading_value_rank"]
            if stock["trading_value_rank"] is not None
            else ""
        ),
        "day_high": stock["day_high"],
        "high_gap": stock["high_gap"],
        "value_growth": stock["value_growth"],
        "volume_growth": stock["volume_growth"],
        "score": stock["score"],
        "score_trading_value": stock.get("score_detail", {}).get("trading_value", ""),
        "score_high_position": stock.get("score_detail", {}).get("high_position", ""),
        "score_value_growth": stock.get("score_detail", {}).get("value_growth", ""),
        "score_volume_growth": stock.get("score_detail", {}).get("volume_growth", ""),
        "focus_signal": is_focus_signal(stock),
        "watch_score": WATCH_SCORE,
        "watch_start_time": _csv_datetime(stock.get("watch_start_time", "")),
        "watch_start_price": stock.get("watch_start_price", ""),
        "watch_start_score": stock.get("watch_start_score", ""),
        "watch_to_signal_sec": stock.get("watch_to_signal_sec", ""),
        "watch_episode_id": stock.get("watch_episode_id", ""),
        "watch_episode_start_time": _csv_datetime(stock.get("watch_episode_start_time", "")),
        "watch_episode_start_price": stock.get("watch_episode_start_price", ""),
        "watch_episode_start_score": stock.get("watch_episode_start_score", ""),
        "watch_episode_to_signal_sec": stock.get("watch_episode_to_signal_sec", ""),
        "history_available_sec": stock.get("history_available_sec", ""),
        "history_sample_count": stock.get("history_sample_count", ""),
        "price_30s_positive": stock.get("price_30s_positive", ""),
        "price_60s_positive": stock.get("price_60s_positive", ""),
        "first75_price_30s_positive": stock.get("first75_price_30s_positive", ""),
        "had_prior_shadow_70_74": stock.get("had_prior_shadow_70_74", False),
        "prior_shadow_trade_id": stock.get("prior_shadow_trade_id", ""),
        "prior_shadow_time": _csv_datetime(stock.get("prior_shadow_time", "")),
        "prior_shadow_price": stock.get("prior_shadow_price", ""),
        "prior_shadow_score": stock.get("prior_shadow_score", ""),
        "prior_shadow_to_first75_sec": stock.get("prior_shadow_to_first75_sec", ""),
        "prior_shadow_to_first75_pct": stock.get("prior_shadow_to_first75_pct", ""),
    }

    for sec in HISTORY_LOOKBACKS_SEC:
        row[f"price_change_{sec}s"] = stock.get(f"price_change_{sec}s", "")
        row[f"price_change_{sec}s_actual_sec"] = stock.get(
            f"price_change_{sec}s_actual_sec", ""
        )

    for sec in [30, 60, 120, 180, 300]:
        row[f"high_gap_change_{sec}s"] = stock.get(f"high_gap_change_{sec}s", "")
        row[f"high_gap_change_{sec}s_actual_sec"] = stock.get(
            f"high_gap_change_{sec}s_actual_sec", ""
        )

    pd.DataFrame([row]).to_csv(
        SIGNAL_LOG_FILE,
        mode="a",
        header=not os.path.exists(SIGNAL_LOG_FILE),
        index=False,
        encoding="utf-8-sig"
    )

def send_stock_alert(stock):

    global daily_alert_count

    estimated_eok = stock["estimated_trading_value"] / 100_000_000
    source = stock["trading_value_source"]

    if source == "ACTUAL":
        actual_eok = stock["actual_trading_value"] / 100_000_000
        value_text = (
            f"실제 거래대금 : {actual_eok:,.1f}억원\n"
            f"추정 거래대금 : {estimated_eok:,.1f}억원\n"
            "거래대금 구분 : ACTUAL"
        )
    else:
        value_text = (
            "실제 거래대금 : KA10032 순위 밖\n"
            f"추정 거래대금 : 약 {estimated_eok:,.1f}억원\n"
            "거래대금 구분 : ESTIMATED"
        )

    nxt_text = get_nxt_status_text(stock["stock_code"])
    trade_mode_text = (
        "실제 자동매매 + 가상매매"
        if AUTO_TRADE_ENABLED
        else "가상매매만"
    )
    focus_text = "⭐ FOCUS 조건" if is_focus_signal(stock) else "일반 신호"

    def fmt(v, suffix="%"):
        if v is None or v == "":
            return "N/A"
        return f"{safe_float(v):+.2f}{suffix}"

    message = f"""
🚨 단타 후보 [{get_session()}]

{stock['stock_name']} ({stock['stock_code']})
{nxt_text}

현재가 : {stock['current_price']:,.0f}원
등락률 : {stock['change_rate']:+.2f}%
거래량 : {stock['volume']:,}주

{value_text}

당일고가 : {stock['day_high']:,.0f}원
고점대비 : -{stock['high_gap']:.2f}%

거래대금 증가 : {stock['value_growth']:.3f}배
거래량 증가 : {stock['volume_growth']:.3f}배

점수 : {stock['score']} / 100
WATCH : {WATCH_SCORE}점+
HISTORY : {safe_float(stock.get('history_available_sec', 0)):.0f}초
30초 가격 : {fmt(stock.get('price_change_30s'))}
60초 가격 : {fmt(stock.get('price_change_60s'))}
60초 고점이격 변화 : {fmt(stock.get('high_gap_change_60s'), '%p')}

가상전략
BASE / PRE_HISTORY / CONFIRM / LIVE_FILTER_SHADOW
각 진입마다 TP {PAPER_TP_LEVELS[0]:.2f}~{PAPER_TP_LEVELS[-1]:.2f}% × SL {PAPER_SL_LEVELS[0]:.2f}~{PAPER_SL_LEVELS[-1]:.2f}%
총 {len(EXIT_STRATEGIES)}개 조합 동시추적

운영모드 : {trade_mode_text}
분류 : {focus_text}
""".strip()

    if send_telegram(message):
        last_alert_time[stock["stock_code"]] = datetime.now()
        daily_alert_count += 1



def open_paper_trade(stock, entry_mode="BASE", entry_meta=None):

    if not PAPER_TRADE_ENABLED or not AUTO_PAPER_ENTRY:
        return None

    entry_meta = entry_meta or {}
    code = clean_stock_code(stock["stock_code"])
    episode_id = _current_watch_episode_id(code, stock)
    key = paper_entry_key(code, entry_mode, episode_id)

    if ONE_ENTRY_PER_STOCK and key in paper_entered_today:
        return None

    signal_price = safe_float(stock["current_price"])
    if signal_price <= 0:
        return None

    signal_time = _stock_score_time(stock)

    # v1.6.5의 초 단위 세션 guard를 그대로 유지합니다.
    valid, guard_reason = attach_session_decision_metrics(
        stock,
        stock.get("scan_session"),
        signal_time
    )
    if not valid:
        log(
            f"[가상진입 차단:{entry_mode}] "
            f"{stock.get('stock_name', code)} / {guard_reason}"
        )
        return None

    attach_pre_first_75_metrics(stock)
    attach_entry_cost_metrics(
        stock,
        signal_time,
        signal_price
    )

    entry_price = signal_price * (1 + PAPER_ENTRY_SLIPPAGE / 100)
    entry_time = datetime.now()
    trade_id = make_trade_id(code, entry_mode, episode_id)
    reentry_meta = _commit_paper_reentry_metadata(
        stock,
        entry_mode,
        trade_id,
        entry_meta
    )

    strategies = {}
    for name, rule in EXIT_STRATEGIES.items():
        strategies[name] = {
            "tp": rule["tp"],
            "sl": rule["sl"],
            "target_price": entry_price * (1 + rule["tp"] / 100),
            "stop_price": entry_price * (1 + rule["sl"] / 100),
            "status": "OPEN",
            "exit_time": None,
            "exit_price": None,
            "result": None,
        }

    p = {
        "trade_id": trade_id,
        "entry_mode": entry_mode,
        "stock_code": code,
        "stock_name": stock["stock_name"],
        "session": stock.get("decision_session", get_session()),
        "scan_session": stock.get("scan_session", ""),
        "decision_session": stock.get("decision_session", ""),
        "decision_time": stock.get("decision_time", signal_time),
        "session_valid_at_decision": stock.get("session_valid_at_decision", True),
        "signal_time": signal_time,
        "entry_decision_time": stock.get("entry_decision_time", signal_time),
        "entry_time": entry_time,
        "signal_price": signal_price,
        "entry_signal_price": stock.get("entry_signal_price", signal_price),
        "entry_price": entry_price,
        "entry_delay_from_first75_sec": stock.get("entry_delay_from_first75_sec", ""),
        "entry_vs_first75_pct": stock.get("entry_vs_first75_pct", ""),
        "last_price": signal_price,
        "max_price": signal_price,
        "min_price": signal_price,
        "score": stock["score"],
        "trading_value_source": stock["trading_value_source"],
        "actual_trading_value": stock["actual_trading_value"],
        "estimated_trading_value": stock["estimated_trading_value"],
        "high_gap": stock.get("high_gap"),
        "history_available_sec": stock.get("history_available_sec"),
        "history_sample_count": stock.get("history_sample_count"),
        "price_30s_positive": stock.get("price_30s_positive", ""),
        "price_60s_positive": stock.get("price_60s_positive", ""),
        "first75_price_30s_positive": stock.get("first75_price_30s_positive", ""),
        "watch_start_time": stock.get("watch_start_time"),
        "watch_start_price": stock.get("watch_start_price"),
        "watch_start_score": stock.get("watch_start_score"),
        "watch_to_signal_sec": stock.get("watch_to_signal_sec"),
        "watch_episode_id": episode_id,
        "watch_episode_start_time": stock.get("watch_episode_start_time"),
        "watch_episode_start_price": stock.get("watch_episode_start_price"),
        "watch_episode_start_score": stock.get("watch_episode_start_score"),
        "watch_episode_to_signal_sec": stock.get("watch_episode_to_signal_sec"),
        "scan_start_time": stock.get("scan_start_time", _stock_scan_start_time(stock)),
        "first_75_time": stock.get("first_75_time"),
        "first_75_price": stock.get("first_75_price"),
        "first_75_score": stock.get("first_75_score"),
        "first_75_pre_result": stock.get("first_75_pre_result"),
        "first_75_pre_status": stock.get("first_75_pre_status"),
        "first_75_pre_reason": stock.get("first_75_pre_reason"),
        "had_prior_shadow_70_74": stock.get("had_prior_shadow_70_74", False),
        "prior_shadow_trade_id": stock.get("prior_shadow_trade_id", ""),
        "prior_shadow_time": stock.get("prior_shadow_time", ""),
        "prior_shadow_price": stock.get("prior_shadow_price", ""),
        "prior_shadow_score": stock.get("prior_shadow_score", ""),
        "prior_shadow_to_first75_sec": stock.get("prior_shadow_to_first75_sec", ""),
        "prior_shadow_to_first75_pct": stock.get("prior_shadow_to_first75_pct", ""),
        # v1.6.6 Episode 재진입 분석값
        **reentry_meta,
        # 최초 WS tick 연구값: handle_realtime_price()에서 딱 한 번 채웁니다.
        "first_ws_time": None,
        "first_ws_price": None,
        "first_ws_delay_sec": None,
        "first_ws_vs_signal_pct": None,
        "first_ws_vs_entry_pct": None,
        "first_ws_gap_abs_pct": None,
        "strategies": strategies,
    }

    for sec in HISTORY_LOOKBACKS_SEC:
        p[f"price_change_{sec}s"] = stock.get(f"price_change_{sec}s")
        p[f"price_change_{sec}s_actual_sec"] = stock.get(
            f"price_change_{sec}s_actual_sec"
        )

    for sec in [30, 60, 120, 180, 300]:
        p[f"high_gap_change_{sec}s"] = stock.get(f"high_gap_change_{sec}s")
        p[f"high_gap_change_{sec}s_actual_sec"] = stock.get(
            f"high_gap_change_{sec}s_actual_sec"
        )

    p.update(entry_meta)

    paper_positions[trade_id] = p
    paper_position_ids_by_code.setdefault(code, set()).add(trade_id)
    paper_entered_today.add(key)

    start_entry_path_tracking(p)

    # paper trade 상태를 먼저 등록한 뒤 구독합니다.
    # 새 Episode trade가 이전 Episode trade와 동시에 살아 있어도 같은 code tick을 공유합니다.
    if (
        WEBSOCKET_ENABLED
        and websocket_manager is not None
    ):
        websocket_manager.subscribe_stock(
            code,
            stock.get("decision_session", get_session())
        )

    log(
        f"[가상진입:{entry_mode}] {stock['stock_name']} / "
        f"{entry_price:,.0f}원 / {len(EXIT_STRATEGIES)}개 전략 / "
        f"episode={episode_id} / mode_seq={reentry_meta['mode_entry_seq_today']} / "
        f"trade_id={trade_id}"
    )

    return trade_id



def _holding_sec(position, strategy):
    entry_time = position.get("entry_time")
    exit_time = strategy.get("exit_time")
    if not isinstance(entry_time, datetime) or not isinstance(exit_time, datetime):
        return None
    return max(0.0, (exit_time - entry_time).total_seconds())


def build_strategy_result_row(position, strategy_name, strategy):
    """가상전략 1개의 결과 행을 생성합니다."""

    entry = position["entry_price"]
    exit_price = strategy["exit_price"]
    ret = (exit_price - entry) / entry * 100
    mfe = (position["max_price"] - entry) / entry * 100
    mae = (position["min_price"] - entry) / entry * 100
    holding = _holding_sec(position, strategy)

    row = {
        "version": STRATEGY_VERSION,
        "trade_id": position.get("trade_id", ""),
        "entry_mode": position.get("entry_mode", "BASE"),
        "stock_code": position["stock_code"],
        "stock_name": position["stock_name"],
        "session": position["session"],
        "scan_session": position.get("scan_session", ""),
        "decision_session": position.get("decision_session", ""),
        "decision_time": _csv_datetime(position.get("decision_time", "")),
        "session_valid_at_decision": position.get("session_valid_at_decision", ""),
        "strategy": strategy_name,
        "TP": strategy["tp"],
        "SL": strategy["sl"],
        "signal_time": _csv_datetime(position.get("signal_time", "")),
        "entry_time": _csv_datetime(position["entry_time"]),
        "exit_time": _csv_datetime(strategy["exit_time"]),
        "holding_sec": round(holding, 3) if holding is not None else "",
        "entry_price": round(entry, 2),
        "exit_price": round(exit_price, 2),
        "return_rate": round(ret, 3),
        "MFE": round(mfe, 3),
        "MAE": round(mae, 3),
        "result": strategy["result"],
        "score": position["score"],
        "signal_price": position.get("signal_price", ""),
        "entry_decision_time": _csv_datetime(position.get("entry_decision_time", "")),
        "entry_signal_price": position.get("entry_signal_price", ""),
        "entry_delay_from_first75_sec": position.get("entry_delay_from_first75_sec", ""),
        "entry_vs_first75_pct": position.get("entry_vs_first75_pct", ""),
        "high_gap": position.get("high_gap", ""),
        "trading_value_source": position["trading_value_source"],
        "actual_trading_value": (
            position["actual_trading_value"]
            if position["actual_trading_value"] is not None
            else ""
        ),
        "estimated_trading_value": position["estimated_trading_value"],
        "first_ws_time": _csv_datetime(position.get("first_ws_time", "")),
        "first_ws_price": position.get("first_ws_price", ""),
        "first_ws_delay_sec": position.get("first_ws_delay_sec", ""),
        "first_ws_vs_signal_pct": position.get("first_ws_vs_signal_pct", ""),
        "first_ws_vs_entry_pct": position.get("first_ws_vs_entry_pct", ""),
        "first_ws_gap_abs_pct": position.get("first_ws_gap_abs_pct", ""),
        "watch_start_time": _csv_datetime(position.get("watch_start_time", "")),
        "watch_start_price": position.get("watch_start_price", ""),
        "watch_start_score": position.get("watch_start_score", ""),
        "watch_to_signal_sec": position.get("watch_to_signal_sec", ""),
        "watch_episode_id": position.get("watch_episode_id", ""),
        "watch_episode_start_time": _csv_datetime(position.get("watch_episode_start_time", "")),
        "watch_episode_start_price": position.get("watch_episode_start_price", ""),
        "watch_episode_start_score": position.get("watch_episode_start_score", ""),
        "watch_episode_to_signal_sec": position.get("watch_episode_to_signal_sec", ""),
        "stock_entry_seq_today": position.get("stock_entry_seq_today", ""),
        "mode_entry_seq_today": position.get("mode_entry_seq_today", ""),
        "is_reentry": position.get("is_reentry", False),
        "previous_same_mode_result": position.get("previous_same_mode_result", ""),
        "previous_same_mode_trade_id": position.get("previous_same_mode_trade_id", ""),
        "scan_start_time": _csv_datetime(position.get("scan_start_time", "")),
        "first_75_time": _csv_datetime(position.get("first_75_time", "")),
        "first_75_price": position.get("first_75_price", ""),
        "first_75_score": position.get("first_75_score", ""),
        "first_75_pre_result": position.get("first_75_pre_result", ""),
        "first_75_pre_status": position.get("first_75_pre_status", ""),
        "first_75_pre_reason": position.get("first_75_pre_reason", ""),
        "price_30s_positive": position.get("price_30s_positive", ""),
        "price_60s_positive": position.get("price_60s_positive", ""),
        "first75_price_30s_positive": position.get("first75_price_30s_positive", ""),
        "had_prior_shadow_70_74": position.get("had_prior_shadow_70_74", False),
        "prior_shadow_trade_id": position.get("prior_shadow_trade_id", ""),
        "prior_shadow_time": _csv_datetime(position.get("prior_shadow_time", "")),
        "prior_shadow_price": position.get("prior_shadow_price", ""),
        "prior_shadow_score": position.get("prior_shadow_score", ""),
        "prior_shadow_to_first75_sec": position.get("prior_shadow_to_first75_sec", ""),
        "prior_shadow_to_first75_pct": position.get("prior_shadow_to_first75_pct", ""),
        "pre_status": position.get("pre_status", ""),
        "pre_entry_type": position.get("pre_entry_type", ""),
        "later_pass_origin": position.get("later_pass_origin", ""),
        "first_75_to_pre_entry_sec": position.get("first_75_to_pre_entry_sec", ""),
        "confirm_first_signal_time": _csv_datetime(position.get("confirm_first_signal_time", "")),
        "confirm_first_signal_price": position.get("confirm_first_signal_price", ""),
        "confirm_delay_sec": position.get("confirm_delay_sec", ""),
        "confirm_rise_pct": position.get("confirm_rise_pct", ""),
    }

    for sec in HISTORY_LOOKBACKS_SEC:
        row[f"price_change_{sec}s"] = position.get(f"price_change_{sec}s", "")
        row[f"price_change_{sec}s_actual_sec"] = position.get(
            f"price_change_{sec}s_actual_sec", ""
        )

    for sec in [30, 60, 120, 180, 300]:
        row[f"high_gap_change_{sec}s"] = position.get(f"high_gap_change_{sec}s", "")
        row[f"high_gap_change_{sec}s_actual_sec"] = position.get(
            f"high_gap_change_{sec}s_actual_sec", ""
        )

    return row

def save_strategy_results(rows):
    """같은 틱에서 종료된 가상전략 결과를 한 번에 저장합니다."""

    if not rows:
        return

    pd.DataFrame(rows).to_csv(
        PAPER_TRADE_FILE,
        mode="a",
        header=not os.path.exists(
            PAPER_TRADE_FILE
        ),
        index=False,
        encoding="utf-8-sig"
    )




def _path_return(base_price, price):
    if base_price <= 0 or price <= 0:
        return None
    return (price - base_price) / base_price * 100



def start_entry_path_tracking(position):
    if not ENTRY_PATH_TRACKING_ENABLED:
        return

    trade_id = position.get("trade_id")
    code = clean_stock_code(position.get("stock_code", ""))
    entry_time = position.get("entry_time")
    signal_price = safe_float(position.get("signal_price", 0))
    entry_price = safe_float(position.get("entry_price", 0))

    if (
        not trade_id
        or not code
        or not isinstance(entry_time, datetime)
        or signal_price <= 0
        or entry_price <= 0
    ):
        return

    if trade_id in entry_path_trackers:
        return

    tracker = {
        "trade_id": trade_id,
        "entry_mode": position.get("entry_mode", ""),
        "stock_code": code,
        "stock_name": position.get("stock_name", ""),
        "signal_time": position.get("signal_time"),
        "entry_time": entry_time,
        "signal_price": signal_price,
        "entry_price": entry_price,
        "scan_session": position.get("scan_session", ""),
        "decision_session": position.get("decision_session", ""),
        "decision_time": position.get("decision_time"),
        "first_75_time": position.get("first_75_time"),
        "first_75_price": position.get("first_75_price"),
        "entry_decision_time": position.get("entry_decision_time"),
        "entry_signal_price": position.get("entry_signal_price"),
        "entry_delay_from_first75_sec": position.get("entry_delay_from_first75_sec"),
        "entry_vs_first75_pct": position.get("entry_vs_first75_pct"),
        "had_prior_shadow_70_74": position.get("had_prior_shadow_70_74", False),
        "prior_shadow_trade_id": position.get("prior_shadow_trade_id", ""),
        "last_price": signal_price,
        "last_observed_time": entry_time,
        "max_price": signal_price,
        "min_price": signal_price,
        "first_ws_time": position.get("first_ws_time"),
        "first_ws_price": position.get("first_ws_price"),
        "first_ws_delay_sec": position.get("first_ws_delay_sec"),
        "first_ws_vs_signal_pct": position.get("first_ws_vs_signal_pct"),
        "first_ws_vs_entry_pct": position.get("first_ws_vs_entry_pct"),
        "first_ws_gap_abs_pct": position.get("first_ws_gap_abs_pct"),
        "saved_horizons": set(),
        "status": "OPEN",
    }

    entry_path_trackers[trade_id] = tracker
    entry_path_ids_by_code.setdefault(code, set()).add(trade_id)

def save_entry_path_row(tracker, horizon_sec, observed_time, price, tracking_status="COMPLETE"):
    entry_time = tracker.get("entry_time")
    if not isinstance(entry_time, datetime):
        return

    actual_elapsed = max(0.0, (observed_time - entry_time).total_seconds())
    signal_price = safe_float(tracker.get("signal_price", 0))
    entry_price = safe_float(tracker.get("entry_price", 0))
    max_price = safe_float(tracker.get("max_price", price))
    min_price = safe_float(tracker.get("min_price", price))

    row = {
        "datetime": _csv_datetime(observed_time),
        "version": STRATEGY_VERSION,
        "trade_id": tracker.get("trade_id", ""),
        "entry_mode": tracker.get("entry_mode", ""),
        "stock_code": tracker.get("stock_code", ""),
        "stock_name": tracker.get("stock_name", ""),
        "entry_time": _csv_datetime(entry_time),
        "signal_price": signal_price,
        "entry_price": entry_price,
        "scan_session": tracker.get("scan_session", ""),
        "decision_session": tracker.get("decision_session", ""),
        "decision_time": _csv_datetime(tracker.get("decision_time", "")),
        "first_75_time": _csv_datetime(tracker.get("first_75_time", "")),
        "first_75_price": tracker.get("first_75_price", ""),
        "entry_decision_time": _csv_datetime(tracker.get("entry_decision_time", "")),
        "entry_signal_price": tracker.get("entry_signal_price", ""),
        "entry_delay_from_first75_sec": tracker.get("entry_delay_from_first75_sec", ""),
        "entry_vs_first75_pct": tracker.get("entry_vs_first75_pct", ""),
        "had_prior_shadow_70_74": tracker.get("had_prior_shadow_70_74", False),
        "prior_shadow_trade_id": tracker.get("prior_shadow_trade_id", ""),
        "first_ws_time": _csv_datetime(tracker.get("first_ws_time", "")),
        "first_ws_price": tracker.get("first_ws_price", ""),
        "first_ws_delay_sec": tracker.get("first_ws_delay_sec", ""),
        "first_ws_vs_signal_pct": tracker.get("first_ws_vs_signal_pct", ""),
        "first_ws_vs_entry_pct": tracker.get("first_ws_vs_entry_pct", ""),
        "first_ws_gap_abs_pct": tracker.get("first_ws_gap_abs_pct", ""),
        "horizon_sec": horizon_sec,
        "actual_elapsed_sec": round(actual_elapsed, 3),
        "price": price,
        "return_from_signal": _path_return(signal_price, price),
        "return_from_entry": _path_return(entry_price, price),
        "mfe_from_signal": _path_return(signal_price, max_price),
        "mae_from_signal": _path_return(signal_price, min_price),
        "mfe_from_entry": _path_return(entry_price, max_price),
        "mae_from_entry": _path_return(entry_price, min_price),
        "tracking_status": tracking_status,
    }

    pd.DataFrame([row]).to_csv(
        ENTRY_PATH_FILE,
        mode="a",
        header=not os.path.exists(ENTRY_PATH_FILE),
        index=False,
        encoding="utf-8-sig"
    )


def _remove_entry_path_tracker(trade_id):
    tracker = entry_path_trackers.pop(trade_id, None)
    if not tracker:
        return

    code = tracker.get("stock_code")
    ids = entry_path_ids_by_code.get(code)
    if ids is not None:
        ids.discard(trade_id)
        if not ids:
            entry_path_ids_by_code.pop(code, None)


def update_entry_path_tracking(code, current_price, observed_time=None):
    code = clean_stock_code(code)
    ids = list(entry_path_ids_by_code.get(code, set()))
    if not ids or current_price <= 0:
        return

    if observed_time is None:
        observed_time = datetime.now()

    completed = []

    for trade_id in ids:
        t = entry_path_trackers.get(trade_id)
        if not t:
            continue

        t["last_price"] = current_price
        t["last_observed_time"] = observed_time
        t["max_price"] = max(t["max_price"], current_price)
        t["min_price"] = min(t["min_price"], current_price)

        elapsed = max(0.0, (observed_time - t["entry_time"]).total_seconds())

        for horizon in ENTRY_PATH_HORIZONS_SEC:
            if horizon in t["saved_horizons"]:
                continue
            if elapsed < horizon:
                continue

            save_entry_path_row(
                t,
                horizon,
                observed_time,
                current_price,
                "COMPLETE"
            )
            t["saved_horizons"].add(horizon)

        if all(h in t["saved_horizons"] for h in ENTRY_PATH_HORIZONS_SEC):
            completed.append(trade_id)

    for trade_id in completed:
        _remove_entry_path_tracker(trade_id)

    if completed:
        maybe_release_realtime(code)


def finalize_entry_path_trackers(status="PARTIAL_PROGRAM_END"):
    now = datetime.now()

    for trade_id, tracker in list(entry_path_trackers.items()):
        observed_time = tracker.get("last_observed_time")
        if not isinstance(observed_time, datetime):
            observed_time = now

        price = safe_float(tracker.get("last_price", 0))
        if price <= 0:
            price = safe_float(tracker.get("signal_price", 0))

        # 아직 도달하지 못한 horizon만 PARTIAL 행으로 남겨 데이터 유실을 방지합니다.
        for horizon in ENTRY_PATH_HORIZONS_SEC:
            if horizon in tracker.get("saved_horizons", set()):
                continue
            save_entry_path_row(
                tracker,
                horizon,
                observed_time,
                price,
                status
            )

        _remove_entry_path_tracker(trade_id)


def _post_exit_return(exit_price, price):
    if exit_price <= 0 or price <= 0:
        return None
    return (price - exit_price) / exit_price * 100


def start_post_exit_tracking(position, strategy):
    if not POST_EXIT_TRACKING_ENABLED:
        return

    if strategy.get("result") not in ["TAKE_PROFIT", "STOP_LOSS"]:
        return

    trade_id = position.get("trade_id")
    code = position.get("stock_code")
    exit_price = safe_float(strategy.get("exit_price", 0))
    exit_time = strategy.get("exit_time")

    if not trade_id or not code or exit_price <= 0 or not isinstance(exit_time, datetime):
        return

    if trade_id in post_exit_trackers:
        return

    tracker = {
        "trade_id": trade_id,
        "entry_mode": position.get("entry_mode", ""),
        "stock_code": code,
        "stock_name": position.get("stock_name", ""),
        "strategy": POST_EXIT_REFERENCE_STRATEGY,
        "entry_time": position.get("entry_time"),
        "entry_price": position.get("entry_price"),
        "exit_time": exit_time,
        "exit_price": exit_price,
        "exit_result": strategy.get("result", ""),
        "max_price_after_exit": exit_price,
        "min_price_after_exit": exit_price,
        "return_5m": None,
        "return_10m": None,
        "return_30m": None,
        "status": "OPEN",
    }

    post_exit_trackers[trade_id] = tracker
    post_exit_ids_by_code.setdefault(code, set()).add(trade_id)


def save_post_exit_result(tracker, status="COMPLETE"):
    entry_time = tracker.get("entry_time")
    exit_time = tracker.get("exit_time")
    exit_price = safe_float(tracker.get("exit_price", 0))

    row = {
        "version": STRATEGY_VERSION,
        "trade_id": tracker.get("trade_id", ""),
        "entry_mode": tracker.get("entry_mode", ""),
        "stock_code": tracker.get("stock_code", ""),
        "stock_name": tracker.get("stock_name", ""),
        "strategy": tracker.get("strategy", ""),
        "entry_time": entry_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if isinstance(entry_time, datetime) else entry_time,
        "entry_price": tracker.get("entry_price", ""),
        "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if isinstance(exit_time, datetime) else exit_time,
        "exit_price": exit_price,
        "exit_result": tracker.get("exit_result", ""),
        "return_5m": tracker.get("return_5m", ""),
        "return_10m": tracker.get("return_10m", ""),
        "return_30m": tracker.get("return_30m", ""),
        "max_rebound_rate": _post_exit_return(exit_price, tracker.get("max_price_after_exit", exit_price)),
        "max_fall_rate": _post_exit_return(exit_price, tracker.get("min_price_after_exit", exit_price)),
        "tracking_status": status,
    }

    pd.DataFrame([row]).to_csv(
        POST_EXIT_FILE,
        mode="a",
        header=not os.path.exists(POST_EXIT_FILE),
        index=False,
        encoding="utf-8-sig"
    )


def _remove_post_exit_tracker(trade_id):
    tracker = post_exit_trackers.pop(trade_id, None)
    if not tracker:
        return

    code = tracker.get("stock_code")
    ids = post_exit_ids_by_code.get(code)
    if ids is not None:
        ids.discard(trade_id)
        if not ids:
            post_exit_ids_by_code.pop(code, None)


def update_post_exit_tracking(code, current_price):
    code = clean_stock_code(code)
    ids = list(post_exit_ids_by_code.get(code, set()))
    if not ids or current_price <= 0:
        return

    now = datetime.now()
    completed = []

    for trade_id in ids:
        t = post_exit_trackers.get(trade_id)
        if not t:
            continue

        t["max_price_after_exit"] = max(t["max_price_after_exit"], current_price)
        t["min_price_after_exit"] = min(t["min_price_after_exit"], current_price)

        elapsed = (now - t["exit_time"]).total_seconds()
        ret = _post_exit_return(t["exit_price"], current_price)

        if elapsed >= 300 and t["return_5m"] is None:
            t["return_5m"] = ret
        if elapsed >= 600 and t["return_10m"] is None:
            t["return_10m"] = ret
        if elapsed >= 1800 and t["return_30m"] is None:
            t["return_30m"] = ret
            save_post_exit_result(t, "COMPLETE")
            completed.append(trade_id)

    for trade_id in completed:
        _remove_post_exit_tracker(trade_id)

    if completed:
        maybe_release_realtime(code)


def finalize_post_exit_trackers():
    for trade_id, tracker in list(post_exit_trackers.items()):
        save_post_exit_result(tracker, "PARTIAL_PROGRAM_END")
        _remove_post_exit_tracker(trade_id)

# ============================================================
# 30. 가상전략 포지션 업데이트
# ============================================================

def update_paper_position(code, current_price):
    code = clean_stock_code(code)
    trade_ids = list(paper_position_ids_by_code.get(code, set()))

    if not trade_ids or current_price <= 0:
        return

    finished_trade_ids = []

    for trade_id in trade_ids:
        p = paper_positions.get(trade_id)
        if p is None:
            continue

        p["last_price"] = current_price
        p["max_price"] = max(p["max_price"], current_price)
        p["min_price"] = min(p["min_price"], current_price)

        closed_rows = []
        tp_count = 0
        sl_count = 0

        for strategy_name, strategy in p["strategies"].items():
            if strategy["status"] != "OPEN":
                continue

            result = None
            if current_price >= strategy["target_price"]:
                result = "TAKE_PROFIT"
                tp_count += 1
            elif current_price <= strategy["stop_price"]:
                result = "STOP_LOSS"
                sl_count += 1

            if result is None:
                continue

            strategy["status"] = "CLOSED"
            strategy["exit_time"] = datetime.now()
            strategy["exit_price"] = current_price
            strategy["result"] = result

            closed_rows.append(
                build_strategy_result_row(p, strategy_name, strategy)
            )

            _update_paper_reference_outcome(p, strategy_name, strategy)

            if strategy_name == POST_EXIT_REFERENCE_STRATEGY:
                start_post_exit_tracking(p, strategy)

        save_strategy_results(closed_rows)

        if closed_rows:
            log(
                f"[가상청산:{p.get('entry_mode')}] {p['stock_name']} / "
                f"익절 {tp_count}개 / 손절 {sl_count}개 / "
                f"가격 {current_price:,.0f}원"
            )

        if all(x["status"] == "CLOSED" for x in p["strategies"].values()):
            finished_trade_ids.append(trade_id)

    for trade_id in finished_trade_ids:
        p = paper_positions.pop(trade_id, None)
        if not p:
            continue
        ids = paper_position_ids_by_code.get(code)
        if ids is not None:
            ids.discard(trade_id)
            if not ids:
                paper_position_ids_by_code.pop(code, None)

    if finished_trade_ids:
        maybe_release_realtime(code)


def monitor_open_positions():

    # 정상 WebSocket 가격이 있으면 REST 조회를 생략하고,
    # 실시간 데이터가 끊기거나 오래된 종목만 REST로 보조합니다.
    with STATE_LOCK:
        codes = set(paper_position_ids_by_code.keys())
        codes.update(entry_path_ids_by_code.keys())
        codes.update(post_exit_ids_by_code.keys())

        if AUTO_TRADE_ENABLED:
            codes.update(live_positions.keys())

    for code in list(codes):
        if WEBSOCKET_ENABLED and is_realtime_price_fresh(code):
            continue

        try:
            raw = get_stock_quote(code)
            quote = normalize_quote(raw)
            price = quote["current_price"]

            if price <= 0:
                continue

            observed_time = datetime.now()
            update_paper_position(code, price)
            update_entry_path_tracking(code, price, observed_time)
            update_post_exit_tracking(code, price)

            if AUTO_TRADE_ENABLED:
                update_live_position_on_price(code, price)

        except Exception as e:
            log(f"[포지션 REST 백업 오류] {code} / {e}")

def force_close_all():

    trade_ids = list(paper_positions.keys())
    quote_cache = {}

    for trade_id in trade_ids:
        p = paper_positions.get(trade_id)
        if p is None:
            continue

        code = p["stock_code"]

        if code not in quote_cache:
            try:
                raw = get_stock_quote(code)
                quote = normalize_quote(raw)
                quote_cache[code] = quote["current_price"]
            except Exception:
                quote_cache[code] = None

        price = quote_cache.get(code)
        if price and price > 0:
            p["last_price"] = price
        else:
            price = p["last_price"]

        closed_rows = []
        for strategy_name, strategy in p["strategies"].items():
            if strategy["status"] != "OPEN":
                continue

            strategy["status"] = "CLOSED"
            strategy["exit_time"] = datetime.now()
            strategy["exit_price"] = price
            strategy["result"] = "TIME_EXIT"

            closed_rows.append(
                build_strategy_result_row(p, strategy_name, strategy)
            )
            _update_paper_reference_outcome(p, strategy_name, strategy)

        save_strategy_results(closed_rows)

        if closed_rows:
            log(
                f"[가상 강제청산:{p.get('entry_mode')}] {p['stock_name']} / "
                f"{len(closed_rows)}개 전략 / 가격 {price:,.0f}원"
            )

        paper_positions.pop(trade_id, None)
        ids = paper_position_ids_by_code.get(code)
        if ids is not None:
            ids.discard(trade_id)
            if not ids:
                paper_position_ids_by_code.pop(code, None)

        maybe_release_realtime(code)




def _stock_snapshot_for_pending(stock):
    # dict 내부 score_detail 정도는 얕은 복사로 충분하지만 안전하게 별도 복사
    snap = dict(stock)
    snap["score_detail"] = dict(stock.get("score_detail", {}))
    return snap



def maybe_open_pre_history(stock, signal_time=None):
    code = clean_stock_code(stock["stock_code"])
    if has_paper_entered_today(code, "PRE_HISTORY"):
        return None

    if signal_time is None:
        signal_time = _stock_score_time(stock)

    valid, guard_reason = attach_session_decision_metrics(
        stock,
        stock.get("scan_session"),
        signal_time
    )
    if not valid:
        save_entry_decision(
            stock,
            "PRE_HISTORY",
            "SKIP",
            guard_reason
        )
        return None

    first_state = register_pre_first_75_if_needed(stock, signal_time)
    attach_pre_first_75_metrics(stock)
    attach_entry_cost_metrics(stock, signal_time)

    if first_state is None:
        save_entry_decision(
            stock,
            "PRE_HISTORY",
            "SKIP",
            "FIRST_75_STATE_UNAVAILABLE"
        )
        return None

    pre_status, reason = evaluate_pre_history(stock)
    ok = pre_status == "PASS"

    pre_entry_type = ""
    later_pass_origin = ""
    first_to_entry_sec = ""

    if ok and first_state:
        first_time = first_state.get("first_75_time")
        if first_time == signal_time or (
            isinstance(first_time, datetime)
            and abs((signal_time - first_time).total_seconds()) < 0.001
        ):
            pre_entry_type = "FIRST_75_PASS"
        else:
            pre_entry_type = "LATER_PASS"
            later_pass_origin = later_pass_origin_from_status(
                first_state.get("first_75_pre_status", "")
            )

        if isinstance(first_time, datetime):
            first_to_entry_sec = max(
                0.0,
                (signal_time - first_time).total_seconds()
            )

    stock["pre_entry_type"] = pre_entry_type

    extra = {
        "pre_status": pre_status,
        "pre_entry_type": pre_entry_type,
        "later_pass_origin": later_pass_origin,
        "first_75_to_pre_entry_sec": first_to_entry_sec,
        "pre_history_rule": reason,
        "entry_decision_time": stock.get("entry_decision_time", ""),
        "entry_signal_price": stock.get("entry_signal_price", ""),
        "entry_delay_from_first75_sec": stock.get("entry_delay_from_first75_sec", ""),
        "entry_vs_first75_pct": stock.get("entry_vs_first75_pct", ""),
    }

    save_entry_decision(
        stock,
        "PRE_HISTORY",
        "ENTER" if ok else "SKIP",
        reason,
        extra
    )

    if not ok:
        return None

    paper_trade_id = open_paper_trade(
        stock,
        "PRE_HISTORY",
        {
            "pre_status": pre_status,
            "pre_history_rule": reason,
            "pre_entry_type": pre_entry_type,
            "later_pass_origin": later_pass_origin,
            "first_75_to_pre_entry_sec": first_to_entry_sec,
        }
    )

    # v1.6.6 actual gate: 오직 PRE_HISTORY + FIRST_75_PASS.
    # LATER_PASS는 연구용 paper만 유지합니다.
    if paper_trade_id and pre_entry_type == LIVE_ENTRY_MODE:
        maybe_open_live_trade(
            stock,
            entry_mode="PRE_HISTORY",
            pre_entry_type=pre_entry_type,
            paper_trade_id=paper_trade_id,
            decision_time=signal_time,
        )

    return paper_trade_id


def maybe_open_live_filter_shadow(stock):
    if not LIVE_FILTER_SHADOW_ENABLED:
        return None

    code = stock["stock_code"]
    if has_paper_entered_today(code, "LIVE_FILTER_SHADOW"):
        return None

    decision_time = _stock_score_time(stock)
    valid, _ = attach_session_decision_metrics(
        stock,
        stock.get("scan_session"),
        decision_time
    )
    if not valid:
        return None

    now_hhmm = decision_time.strftime("%H:%M")
    ok = (
        stock.get("decision_session") == "MAIN"
        and LIVE_ENTRY_START <= now_hhmm <= LIVE_ENTRY_END
        and stock.get("score", 0) >= MIN_SIGNAL_SCORE
        and stock.get("high_gap", 999) <= LIVE_MAX_HIGH_GAP
    )

    if not ok:
        return None

    attach_entry_cost_metrics(stock, decision_time)
    save_entry_decision(stock, "LIVE_FILTER_SHADOW", "ENTER", "PASS")
    return open_paper_trade(stock, "LIVE_FILTER_SHADOW")





def maybe_open_score_shadow_70_74(stock):
    """
    75점 임계값 검증용 70~74점 별도 연구군.

    조건:
    - 기존 종목선정 필터 통과 후 최종 점수 70~74
    - 당일 어떤 정상 점수평가에서도 75점+을 본 적 없음
    - 현재 WATCH Episode에서 SHADOW_SCORE_70_74 미진입
    - 실제 decision_time 기준 세션 유효
    """
    if not SHADOW_SCORE_70_74_ENABLED:
        return None

    code = clean_stock_code(stock.get("stock_code", ""))
    score = safe_float(stock.get("score", 0))

    if not (
        SHADOW_SCORE_MIN
        <= score
        <= SHADOW_SCORE_MAX
    ):
        return None

    if code in score_75_seen_today:
        return None

    if code in pre_first_75_states:
        return None

    if has_paper_entered_today(code, "SHADOW_SCORE_70_74"):
        return None

    decision_time = _stock_score_time(stock)
    valid, guard_reason = attach_session_decision_metrics(
        stock,
        stock.get("scan_session"),
        decision_time
    )

    attach_pre_first_75_metrics(stock)
    attach_entry_cost_metrics(stock, decision_time)

    if not valid:
        save_entry_decision(
            stock,
            "SHADOW_SCORE_70_74",
            "SKIP",
            guard_reason
        )
        return None

    save_entry_decision(
        stock,
        "SHADOW_SCORE_70_74",
        "ENTER",
        "SCORE_70_74_BEFORE_FIRST75"
    )

    trade_id = open_paper_trade(
        stock,
        "SHADOW_SCORE_70_74"
    )

    if trade_id:
        score_shadow_states[code] = {
            "shadow_trade_id": trade_id,
            "shadow_time": decision_time,
            "shadow_price": safe_float(stock.get("current_price", 0)),
            "shadow_score": score,
        }

    return trade_id


def start_confirm_if_needed(stock, current_scan_sequence, signal_time=None):
    code = clean_stock_code(stock["stock_code"])

    if code in confirm_started_today:
        return

    if has_paper_entered_today(code, "CONFIRM"):
        return

    if signal_time is None:
        signal_time = _stock_score_time(stock)

    valid, guard_reason = attach_session_decision_metrics(
        stock,
        stock.get("scan_session"),
        signal_time
    )
    if not valid:
        # 세션 경계 관측은 CONFIRM pending 상태를 새로 만들지 않습니다.
        save_entry_decision(
            stock,
            "CONFIRM",
            "SKIP",
            guard_reason,
            {
                "confirm_observation_status": "SESSION_GUARD",
                "confirm_observation_reason": guard_reason,
            }
        )
        return

    scan_start_time = _stock_scan_start_time(stock)
    attach_pre_first_75_metrics(stock)
    attach_entry_cost_metrics(stock, signal_time)

    confirm_started_today.add(code)
    confirm_pending[code] = {
        "created_scan_sequence": current_scan_sequence,
        # 기존 필드명은 호환을 위해 유지하되 값은 실제 first_75_time입니다.
        "first_signal_time": signal_time,
        "first_75_time": signal_time,
        "scan_start_time": scan_start_time,
        "scan_session": stock.get("scan_session", ""),
        "first_signal_price": safe_float(stock["current_price"]),
        "first_stock": _stock_snapshot_for_pending(stock),
        "market": stock.get("market", ""),
    }

    save_entry_decision(
        stock,
        "CONFIRM",
        "PENDING",
        "FIRST_75_SIGNAL",
        {
            "scan_start_time": scan_start_time,
            "first_signal_time": signal_time,
            "first_signal_price": stock["current_price"],
            "confirm_observation_status": "PENDING",
            "confirm_observation_reason": "FIRST_75_SIGNAL",
        }
    )


def _confirm_elapsed_sec(first_75_time, observation_time):
    if not isinstance(first_75_time, datetime):
        return None
    if not isinstance(observation_time, datetime):
        observation_time = datetime.now()
    return max(0.0, (observation_time - first_75_time).total_seconds())


def evaluate_confirm_pending(
    observation_map,
    current_scan_sequence,
    current_scan_session=None
):
    """최초 75점 실제 판정시각 이후 첫 정상 평가 가능 스캔에서 CONFIRM 판정."""

    for code, pending in list(confirm_pending.items()):
        if pending.get("created_scan_sequence") >= current_scan_sequence:
            continue

        first_time = pending.get("first_75_time", pending["first_signal_time"])
        first_price = pending["first_signal_price"]
        expected_session = pending.get("scan_session", "")

        obs = observation_map.get(
            code,
            {"status": "UNKNOWN", "reason": "NO_OBSERVATION", "stock": None}
        )
        status = obs.get("status", "UNKNOWN")
        obs_reason = obs.get("reason", "")
        stock = obs.get("stock")

        # 정상 점수평가가 된 종목은 해당 종목의 실제 점수계산 완료시각을 사용합니다.
        if status == "EVALUABLE" and stock is not None:
            observation_time = _stock_score_time(stock)
        else:
            observation_time = datetime.now()

        elapsed = _confirm_elapsed_sec(first_time, observation_time)
        if elapsed is None:
            elapsed = 0.0

        # v1.6.5: 최초 75점이 발생한 세션 밖에서는 CONFIRM을 이어가지 않습니다.
        if expected_session and not is_entry_session_valid(
            observation_time,
            expected_session
        ):
            decision_stock = stock if stock is not None else pending["first_stock"]
            decision_stock["scan_session"] = expected_session
            decision_stock["decision_time"] = observation_time
            decision_stock["decision_session"] = get_session_at(observation_time)
            decision_stock["session_valid_at_decision"] = False

            if decision_stock["decision_session"] == "WAIT":
                reason = "SESSION_CLOSED_AT_DECISION"
            else:
                reason = "SESSION_CHANGED_DURING_SCAN"

            attach_watch_metrics(decision_stock, first_time)
            attach_pre_first_75_metrics(decision_stock)
            attach_entry_cost_metrics(
                decision_stock,
                observation_time,
                safe_float(decision_stock.get("current_price", first_price))
            )

            save_entry_decision(
                decision_stock,
                "CONFIRM",
                "SKIP",
                reason,
                {
                    "scan_start_time": pending.get("scan_start_time", ""),
                    "first_signal_time": first_time,
                    "first_signal_price": first_price,
                    "confirm_delay_sec": elapsed,
                    "confirm_rise_pct": "",
                    "confirm_observation_status": "SESSION_GUARD",
                    "confirm_observation_reason": reason,
                }
            )

            confirm_pending.pop(code, None)
            continue

        # 조회불가 상태는 실제 first_75_time 기준 45초 안에서는 실패로 처리하지 않습니다.
        if status == "UNKNOWN" and elapsed <= CONFIRM_TIMEOUT_SEC:
            continue

        if status == "UNKNOWN" and elapsed > CONFIRM_TIMEOUT_SEC:
            ok = False
            reason = "DATA_UNAVAILABLE_TIMEOUT"
            decision_stock = pending["first_stock"]
            rise_pct = None

        elif elapsed > CONFIRM_TIMEOUT_SEC:
            ok = False
            reason = "TIMEOUT"
            decision_stock = stock if stock is not None else pending["first_stock"]
            rise_pct = None
            if stock is not None and first_price > 0:
                rise_pct = (
                    (safe_float(stock.get("current_price", 0)) - first_price)
                    / first_price * 100
                )

        elif status == "FILTER_EXIT":
            ok = False
            reason = obs_reason or "FILTER_EXIT"
            decision_stock = stock if stock is not None else pending["first_stock"]
            rise_pct = None

        elif status == "EVALUABLE":
            decision_stock = stock
            score = safe_float(stock.get("score", 0))
            rise_pct = None
            if first_price > 0:
                rise_pct = (
                    (safe_float(stock.get("current_price", 0)) - first_price)
                    / first_price * 100
                )

            if score < MIN_SIGNAL_SCORE:
                ok = False
                reason = "SCORE_BELOW_75"
            elif rise_pct is None or rise_pct < CONFIRM_MIN_RISE_PCT:
                ok = False
                reason = "RISE_BELOW_CONFIRM"
            else:
                ok = True
                reason = "PASS"

        else:
            if elapsed <= CONFIRM_TIMEOUT_SEC:
                continue
            ok = False
            reason = "DATA_UNAVAILABLE_TIMEOUT"
            decision_stock = pending["first_stock"]
            rise_pct = None

        if stock is not None:
            attach_session_decision_metrics(
                decision_stock,
                stock.get("scan_session", expected_session),
                observation_time
            )
        else:
            decision_stock["scan_session"] = expected_session
            decision_stock["decision_time"] = observation_time
            decision_stock["decision_session"] = get_session_at(observation_time)
            decision_stock["session_valid_at_decision"] = is_entry_session_valid(
                observation_time,
                expected_session
            )

        attach_watch_metrics(decision_stock, first_time)
        attach_pre_first_75_metrics(decision_stock)
        attach_entry_cost_metrics(
            decision_stock,
            observation_time,
            safe_float(decision_stock.get("current_price", first_price))
        )

        extra = {
            "scan_start_time": pending.get("scan_start_time", ""),
            "first_signal_time": first_time,
            "first_signal_price": first_price,
            "confirm_delay_sec": elapsed,
            "confirm_rise_pct": rise_pct if rise_pct is not None else "",
            "confirm_observation_status": status,
            "confirm_observation_reason": obs_reason,
            "entry_decision_time": decision_stock.get("entry_decision_time", ""),
            "entry_signal_price": decision_stock.get("entry_signal_price", ""),
            "entry_delay_from_first75_sec": decision_stock.get(
                "entry_delay_from_first75_sec", ""
            ),
            "entry_vs_first75_pct": decision_stock.get("entry_vs_first75_pct", ""),
        }

        save_entry_decision(
            decision_stock,
            "CONFIRM",
            "ENTER" if ok else "SKIP",
            reason,
            extra
        )

        if ok:
            open_paper_trade(
                stock,
                "CONFIRM",
                {
                    "confirm_first_signal_time": first_time,
                    "confirm_first_signal_price": first_price,
                    "confirm_delay_sec": elapsed,
                    "confirm_rise_pct": rise_pct,
                }
            )

        confirm_pending.pop(code, None)

def fetch_quotes_parallel(stocks):
    """
    KA10001 종목별 조회의 HTTP 응답 대기를 병렬화합니다.
    요청 시작 간격은 기존 API rate limiter가 그대로 제한합니다.

    반환:
      result_map: 정상 응답
      error_map : API/네트워크 오류 문자열
    """

    if not stocks:
        return {}, {}

    started = time.time()
    result_map = {}
    error_map = {}

    workers = min(
        KA10001_MAX_WORKERS,
        len(stocks)
    )

    with ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="KA10001"
    ) as executor:

        future_map = {
            executor.submit(
                get_stock_quote,
                stock["stock_code"]
            ): stock
            for stock in stocks
        }

        for future in as_completed(future_map):
            stock = future_map[future]
            code = stock["stock_code"]

            try:
                result_map[code] = future.result()
            except Exception as e:
                error_map[code] = str(e)
                log(
                    f"[KA10001 오류] "
                    f"{stock['stock_name']} / {e}"
                )

    elapsed = time.time() - started

    log(
        f"KA10001 병렬조회 "
        f"{len(result_map)}/{len(stocks)}종목 / "
        f"오류 {len(error_map)} / "
        f"{elapsed:.1f}초 / workers={workers}"
    )

    return result_map, error_map

def scan_market():

    global last_scan_stats
    global scan_sequence

    scan_sequence += 1
    current_scan_sequence = scan_sequence
    scan_started = time.time()
    scan_sample_ts = scan_started
    scan_start_time = datetime.fromtimestamp(scan_started)
    scan_session = get_session_at(scan_start_time)

    log(
        f"===== 시장 스캔 시작 / "
        f"scan_session={scan_session} / "
        f"{scan_start_time.strftime('%H:%M:%S.%f')[:-3]} ====="
    )
    all_stocks = []
    observation_map = {}
    market_query_ok = {}

    # 1. KA10027: 이 단계부터 현재가 history를 넓게 저장
    for market_code, market_name in MARKETS:
        try:
            rows = get_change_rate_rank(market_code)
            market_query_ok[market_name] = True
            log(f"{market_name} KA10027 {len(rows)}종목")

            for rank, row in enumerate(rows, start=1):
                stock = normalize_change_row(row, market_name, rank)
                stock["_scan_sample_ts"] = scan_sample_ts
                stock["_scan_start_ts"] = scan_started
                stock["_scan_session"] = scan_session
                stock["scan_session"] = scan_session
                all_stocks.append(stock)
                observation_map[stock["stock_code"]] = {
                    "status": "RANK_OBSERVED",
                    "reason": "KA10027_OBSERVED",
                    "stock": stock,
                }
                record_price_history(stock, stage="KA10027", now_ts=scan_sample_ts)

        except Exception as e:
            market_query_ok[market_name] = False
            log(f"{market_name} KA10027 오류: {e}")

    # 2. 기존 사전필터
    pre_candidates = []
    for stock in all_stocks:
        code = stock["stock_code"]
        if pass_pre_filter(stock):
            pre_candidates.append(stock)
        else:
            observation_map[code] = {
                "status": "FILTER_EXIT",
                "reason": "PRE_FILTER_EXIT",
                "stock": stock,
            }

    log(f"사전필터 통과 {len(pre_candidates)}종목")

    # 3. KA10032
    actual_map = build_actual_trading_value_map()

    # 4. 거래대금 부착/필터
    value_passed = []
    actual_count = 0
    estimated_count = 0

    for stock in pre_candidates:
        code = stock["stock_code"]
        attach_trading_value(stock, actual_map)

        if stock["trading_value_source"] == "ACTUAL":
            actual_count += 1
        else:
            estimated_count += 1

        if stock["trading_value_used"] < MIN_TRADING_VALUE_WON:
            observation_map[code] = {
                "status": "FILTER_EXIT",
                "reason": "TRADING_VALUE_BELOW_MIN",
                "stock": stock,
            }
            continue

        value_passed.append(stock)

    log(
        f"거래대금 데이터 출처 ACTUAL {actual_count} / ESTIMATED {estimated_count}"
    )
    log(
        f"거래대금 {MIN_TRADING_VALUE_WON / 100_000_000:,.0f}억+ 통과 "
        f"{len(value_passed)}종목"
    )

    # 5. KA10001 병렬조회
    quote_map, quote_error_map = fetch_quotes_parallel(value_passed)
    final_candidates = []

    for stock in value_passed:
        code = stock["stock_code"]
        try:
            raw = quote_map.get(code)
            if raw is None:
                observation_map[code] = {
                    "status": "UNKNOWN",
                    "reason": "KA10001_ERROR" if code in quote_error_map else "KA10001_NO_DATA",
                    "stock": stock,
                }
                continue

            quote = normalize_quote(raw)

            if quote["current_price"] > 0:
                stock["current_price"] = quote["current_price"]
            if quote["volume"] > 0:
                stock["volume"] = quote["volume"]

            stock["estimated_trading_value"] = (
                stock["current_price"] * stock["volume"]
            )

            if stock["trading_value_source"] == "ESTIMATED":
                stock["trading_value_used"] = stock["estimated_trading_value"]
                if stock["trading_value_used"] < MIN_TRADING_VALUE_WON:
                    observation_map[code] = {
                        "status": "FILTER_EXIT",
                        "reason": "ESTIMATED_VALUE_BELOW_MIN",
                        "stock": stock,
                    }
                    continue

            # 기존 60초 증가율 로직 보존
            stock["volume_growth"] = calc_volume_growth(code, stock["volume"])
            stock["value_growth"] = calc_value_growth(
                code,
                stock["trading_value_source"],
                stock["trading_value_used"]
            )

            stock["day_high"] = quote["day_high"]
            stock["high_gap"] = calc_high_gap(
                stock["current_price"],
                stock["day_high"]
            )

            # 고점필터 탈락 종목도 richer history는 남깁니다.
            record_price_history(stock, stage="KA10001", now_ts=scan_sample_ts)

            if stock["high_gap"] > MAX_HIGH_GAP:
                observation_map[code] = {
                    "status": "FILTER_EXIT",
                    "reason": "HIGH_GAP_FILTER_EXIT",
                    "stock": stock,
                }
                continue

            stock["score"] = calculate_score(stock)
            # v1.6.4에서 도입된 실제 판정시각을 유지하고,
            # v1.6.5에서는 초 단위 세션 정보까지 함께 고정합니다.
            stock["_score_evaluated_ts"] = time.time()
            stock["scan_start_time"] = scan_start_time
            decision_time = _stock_score_time(stock)
            attach_session_decision_metrics(
                stock,
                scan_session,
                decision_time
            )

            # Shadow 오염방지용 관측 이력은 전략 first_75 상태와 분리합니다.
            if safe_float(stock.get("score", 0)) >= MIN_SIGNAL_SCORE:
                score_75_seen_today.add(code)

            # 같은 스캔 sample에 점수까지 병합
            record_price_history(stock, stage="SCORED", now_ts=scan_sample_ts)
            attach_history_metrics(stock)
            attach_analysis_flags(stock)
            register_watch_if_needed(stock)
            attach_watch_metrics(stock)
            attach_pre_first_75_metrics(stock)

            observation_map[code] = {
                "status": "EVALUABLE",
                "reason": "SCORED",
                "stock": stock,
            }
            final_candidates.append(stock)

        except Exception as e:
            observation_map[code] = {
                "status": "UNKNOWN",
                "reason": "POSTPROCESS_ERROR",
                "stock": stock,
            }
            log(f"[후처리 오류] {stock['stock_name']} / {e}")

    # 기존 활성 WATCH/CONFIRM 종목이 KA10027 결과에서 아예 사라진 경우:
    # 해당 시장 조회가 정상이라면 조건이탈, 시장 API 자체가 실패했다면 UNKNOWN.
    tracked_codes = {
        code
        for code, state in watch_episode_states.items()
        if state.get("active", False)
    }
    tracked_codes.update(confirm_pending.keys())

    for code in tracked_codes:
        if code in observation_map:
            continue

        market = ""
        episode = watch_episode_states.get(code)
        if episode:
            market = episode.get("market", "")
        if not market and code in confirm_pending:
            market = confirm_pending[code].get("market", "")

        if market and market_query_ok.get(market) is True:
            observation_map[code] = {
                "status": "FILTER_EXIT",
                "reason": "NOT_IN_KA10027",
                "stock": None,
            }
        else:
            observation_map[code] = {
                "status": "UNKNOWN",
                "reason": "KA10027_MARKET_UNAVAILABLE",
                "stock": None,
            }

    final_candidates.sort(key=lambda x: x["score"], reverse=True)

    signal_candidates = [
        stock for stock in final_candidates
        if stock["score"] >= MIN_SIGNAL_SCORE
    ]

    shadow_score_candidates = [
        stock for stock in final_candidates
        if SHADOW_SCORE_MIN <= stock["score"] <= SHADOW_SCORE_MAX
    ]

    watch_candidates = [
        stock for stock in final_candidates
        if stock["score"] >= WATCH_SCORE
    ]

    # 정상 관측에서 WATCH 조건을 이탈한 Episode만 종료합니다.
    update_watch_episodes_after_scan(observation_map)

    log(
        f"고점필터 통과 {len(final_candidates)}종목 / "
        f"WATCH {WATCH_SCORE}점+ {len(watch_candidates)}종목 / "
        f"신호 {MIN_SIGNAL_SCORE}점+ {len(signal_candidates)}종목 / "
        f"Shadow {SHADOW_SCORE_MIN}~{SHADOW_SCORE_MAX}점 "
        f"{len(shadow_score_candidates)}종목"
    )

    # 이전 스캔의 CONFIRM 후보는 이번 평가 가능한 관측에서 판정
    evaluate_confirm_pending(
        observation_map,
        current_scan_sequence,
        scan_session
    )

    ka10001_error_texts = list(quote_error_map.values())
    ka10001_429 = sum("429" in str(x) for x in ka10001_error_texts)
    ka10001_502 = sum("502" in str(x) for x in ka10001_error_texts)
    ka10001_timeout = sum(
        any(token in str(x).lower() for token in ["timeout", "timed out"])
        for x in ka10001_error_texts
    )

    log(
        f"[KA10001 품질] 요청 {len(value_passed)} / "
        f"성공 {len(quote_map)} / 오류 {len(quote_error_map)} / "
        f"429 {ka10001_429} / 502 {ka10001_502} / "
        f"timeout {ka10001_timeout}"
    )

    last_scan_stats = {
        "received": len(all_stocks),
        "pre_filtered": len(pre_candidates),
        "actual_count": actual_count,
        "estimated_count": estimated_count,
        "value_passed": len(value_passed),
        "final_candidates": len(final_candidates),
        "watch_candidates": len(watch_candidates),
        "signal_candidates": len(signal_candidates),
        "shadow_score_candidates": len(shadow_score_candidates),
        "confirm_pending": len(confirm_pending),
        "ka10001_requested": len(value_passed),
        "ka10001_success": len(quote_map),
        "ka10001_error": len(quote_error_map),
        "ka10001_429": ka10001_429,
        "ka10001_502": ka10001_502,
        "ka10001_timeout": ka10001_timeout,
        "alerts": daily_alert_count,
        "top_candidates": signal_candidates[:3]
    }

    # 70~74점 Shadow는 signal_candidates(75점+) 루프와 분리합니다.
    # 추가 KA10001 호출 없이 이미 계산된 final_candidates를 그대로 사용합니다.
    for stock in shadow_score_candidates:
        signal_time = _stock_score_time(stock)
        attach_history_metrics(stock)
        attach_analysis_flags(stock)
        attach_watch_metrics(stock, signal_time)
        attach_pre_first_75_metrics(stock)
        maybe_open_score_shadow_70_74(stock)

    for stock in signal_candidates:
        signal_time = _stock_score_time(stock)
        attach_history_metrics(stock)
        attach_analysis_flags(stock)
        attach_watch_metrics(stock, signal_time)

        valid, guard_reason = attach_session_decision_metrics(
            stock,
            scan_session,
            signal_time
        )

        # scanner signal은 연구 관측값으로 남겨도 되지만,
        # 세션 경계 무효 관측은 first_75/진입/CONFIRM 상태에 편입하지 않습니다.
        if not valid:
            attach_pre_first_75_metrics(stock)
            attach_entry_cost_metrics(stock, signal_time)
            save_signal(stock)

            if not has_paper_entered_today(stock["stock_code"], "BASE"):
                save_entry_decision(
                    stock,
                    "BASE",
                    "SKIP",
                    guard_reason
                )
            continue

        register_pre_first_75_if_needed(stock, signal_time)
        attach_pre_first_75_metrics(stock)
        attach_entry_cost_metrics(stock, signal_time)

        save_signal(stock)

        # 1) BASE: 기존 대조군. 조건 변경 없음.
        if not has_paper_entered_today(stock["stock_code"], "BASE"):
            save_entry_decision(
                stock,
                "BASE",
                "ENTER",
                "75_SCORE",
                {
                    "entry_decision_time": stock.get("entry_decision_time", ""),
                    "entry_signal_price": stock.get("entry_signal_price", ""),
                    "entry_delay_from_first75_sec": stock.get(
                        "entry_delay_from_first75_sec", ""
                    ),
                    "entry_vs_first75_pct": stock.get("entry_vs_first75_pct", ""),
                }
            )
            open_paper_trade(stock, "BASE")

        # 2) PRE_HISTORY: 전략조건은 그대로, 최초/나중 통과만 구분
        maybe_open_pre_history(stock, signal_time)

        # 3) 실제매매 조건만 재현한 기존 SHADOW
        maybe_open_live_filter_shadow(stock)

        # 4) CONFIRM: 최초 75점 신호를 대기상태로 등록
        start_confirm_if_needed(stock, current_scan_sequence, signal_time)

        # 실제 주문은 maybe_open_pre_history() 내부에서
        # FIRST_75_PASS가 생성된 바로 그 신호에만 연결됩니다.

        if can_alert(stock["stock_code"]):
            send_stock_alert(stock)

    elapsed = time.time() - scan_started
    log(f"===== 시장 스캔 종료 / {elapsed:.1f}초 =====")

    return final_candidates

def send_diagnostic():

    stats = last_scan_stats

    lines = [
        "🔎 스크리너 자동 진단",
        "",
        f"시간 : {datetime.now().strftime('%H:%M:%S')}",
        f"세션 : {get_session()}",
        "",
        f"KA10027 수신 : {stats['received']}종목",
        f"사전필터 통과 : {stats['pre_filtered']}종목",
        f"실제 거래대금 적용 : {stats['actual_count']}종목",
        f"추정 거래대금 적용 : {stats['estimated_count']}종목",
        f"거래대금 기준 통과 : {stats['value_passed']}종목",
        f"고점필터 통과 : {stats['final_candidates']}종목",
        f"WATCH {WATCH_SCORE}점+ : {stats.get('watch_candidates', 0)}종목",
        f"신호 {MIN_SIGNAL_SCORE}점+ : {stats['signal_candidates']}종목",
        f"Shadow {SHADOW_SCORE_MIN}~{SHADOW_SCORE_MAX}점 : "
        f"{stats.get('shadow_score_candidates', 0)}종목",
        f"CONFIRM 대기 : {len(confirm_pending)}종목",
        f"KA10001 요청/성공/오류 : "
        f"{stats.get('ka10001_requested', 0)}/"
        f"{stats.get('ka10001_success', 0)}/"
        f"{stats.get('ka10001_error', 0)}",
        f"KA10001 429/502/timeout : "
        f"{stats.get('ka10001_429', 0)}/"
        f"{stats.get('ka10001_502', 0)}/"
        f"{stats.get('ka10001_timeout', 0)}",
        f"오늘 WATCH 최초등록 누적 : {len(watch_states)}종목",
        f"활성 WATCH Episode : {sum(1 for x in watch_episode_states.values() if x.get('active'))}개",
        f"오늘 알림 : {daily_alert_count}건",
        f"열린 가상 trade : {len(paper_positions)}개",
        f"진입경로 추적 : {len(entry_path_trackers)}개",
        f"청산후 추적 : {len(post_exit_trackers)}개",
        ""
    ]

    top = stats["top_candidates"]
    if top:
        lines.append("[상위 후보]")
        for i, stock in enumerate(top, start=1):
            eok = stock["trading_value_used"] / 100_000_000
            source = stock["trading_value_source"]
            prefix = "" if source == "ACTUAL" else "약 "
            lines.append(
                f"{i}. {stock['stock_name']} / "
                f"{stock['change_rate']:+.2f}% / "
                f"{prefix}{eok:,.0f}억 [{source}] / "
                f"{stock['score']}점 / "
                f"hist {safe_float(stock.get('history_available_sec', 0)):.0f}s"
            )
    else:
        lines.append("현재 점수 기준 통과 후보 없음")

    send_telegram("\n".join(lines))


def check_new_day():

    global current_trade_date
    global daily_alert_count
    global last_alert_time
    global paper_entered_today
    global paper_positions
    global paper_position_ids_by_code
    global paper_stock_entry_counts_today
    global paper_mode_entry_counts_today
    global paper_last_trade_id_by_mode
    global paper_trade_registry
    global price_history
    global watch_states
    global watch_episode_states
    global watch_episode_counts
    global pre_first_75_states
    global score_75_seen_today
    global score_shadow_states
    global confirm_pending
    global confirm_started_today
    global scan_sequence
    global post_exit_trackers
    global post_exit_ids_by_code
    global entry_path_trackers
    global entry_path_ids_by_code
    global previous_volume
    global previous_trading_value
    global sent_diagnostic_times
    global nxt_eligibility_cache
    global live_orders
    global live_positions
    global live_entered_today
    global live_processed_fill_ids
    global live_unmatched_order_events
    global live_external_resolution_pending
    global live_submit_intents
    global live_trade_count
    global live_daily_realized_pnl
    global live_trading_halted
    global live_system_halt_reason
    global live_recovery_mode
    global live_blocked_codes
    global live_execution_issue_codes
    global broker_balances
    global broker_startup_holdings
    global last_broker_full_sync_ts
    global last_live_force_exit_attempt_ts
    global realtime_prices
    global realtime_price_ts

    today = datetime.now().strftime("%Y-%m-%d")
    if today == current_trade_date:
        return

    with STATE_LOCK:
        unresolved_live = (
            bool(live_positions)
            or any(
                o.get("status") in [
                    "SUBMITTED", "PARTIAL", "CANCEL_PENDING",
                    "EXIT_TRIGGERED", "EXIT_VALIDATING", "ORDER_STATUS_UNKNOWN"
                ]
                for o in live_orders.values()
            )
        )

    # 전 거래일 연구용 잔여 tracker는 부분결과로 보존
    finalize_entry_path_trackers("PARTIAL_NEW_DAY")
    finalize_post_exit_trackers()

    current_trade_date = today
    daily_alert_count = 0
    last_alert_time = {}
    paper_entered_today = set()
    paper_positions = {}
    paper_position_ids_by_code = {}
    paper_stock_entry_counts_today = {}
    paper_mode_entry_counts_today = {}
    paper_last_trade_id_by_mode = {}
    paper_trade_registry = {}
    price_history = {}
    watch_states = {}
    watch_episode_states = {}
    watch_episode_counts = {}
    pre_first_75_states = {}
    score_75_seen_today = set()
    score_shadow_states = {}
    confirm_pending = {}
    confirm_started_today = set()
    scan_sequence = 0
    post_exit_trackers = {}
    post_exit_ids_by_code = {}
    entry_path_trackers = {}
    entry_path_ids_by_code = {}
    previous_volume = {}
    previous_trading_value = {}
    sent_diagnostic_times = set()
    nxt_eligibility_cache = {}
    realtime_prices = {}
    realtime_price_ts = {}
    last_live_force_exit_attempt_ts = 0.0
    broker_balances = {}
    broker_startup_holdings = set()
    last_broker_full_sync_ts = 0.0
    live_external_resolution_pending = set()
    live_submit_intents = {}

    if unresolved_live and AUTO_TRADE_ENABLED:
        live_recovery_mode = True
        live_trading_halted = True
        live_system_halt_reason = "거래일 변경 시 미해결 실제상태"
        live_entered_today = set(live_positions.keys())
        live_trade_count = len(live_entered_today)
        live_daily_realized_pnl = 0.0
        save_live_state()
        send_telegram(
            "🚨 거래일 변경 시 실제 포지션/주문 잔존\n"
            "상태를 유지하고 신규 실제매매를 SAFE HALT합니다.\n"
            "가상연구는 계속합니다."
        )
    else:
        live_orders = {}
        live_positions = {}
        live_entered_today = set()
        live_processed_fill_ids = set()
        live_unmatched_order_events = {}
        live_trade_count = 0
        live_daily_realized_pnl = 0.0
        live_trading_halted = False
        live_system_halt_reason = ""
        live_recovery_mode = False
        live_blocked_codes = {}
        live_execution_issue_codes = set()
        save_live_state()

        if AUTO_TRADE_ENABLED:
            schedule_broker_sync(None, reason="NEW_DAY_START", external_event=False)

    log("새 거래일 초기화")

def test_kiwoom():

    try:

        get_kiwoom_token()

        print(
            "✅ 키움 인증 정상"
        )

        return True


    except Exception as e:

        print(
            "❌ 키움 인증 실패"
        )

        print(e)

        return False


def test_telegram():

    result = send_telegram(

        f"✅ 단타 스크리너 {STRATEGY_VERSION} "
        "Telegram 테스트 성공"
    )


    print(
        "Telegram:",
        result
    )


def test_ka10027():

    rows = (
        get_change_rate_rank(
            "001"
        )
    )


    print(
        "수신 종목:",
        len(rows)
    )


    if rows:

        print(
            "\n원본:"
        )

        print(
            rows[0]
        )


        print(
            "\n정규화:"
        )

        print(

            normalize_change_row(

                rows[0],

                "KOSPI",

                1
            )
        )


def test_ka10032():

    rows = (
        get_trading_value_rank(
            "001"
        )
    )


    print(
        "수신 종목:",
        len(rows)
    )


    if rows:

        print(
            "\n첫 종목:"
        )

        print(
            rows[0]
        )


        # 금호건설 찾기
        kumho = [

            x

            for x in rows

            if clean_stock_code(
                x.get(
                    "stk_cd",
                    ""
                )
            )
            == "002990"
        ]


        if kumho:

            print(
                "\n금호건설:"
            )

            print(
                kumho[0]
            )


            raw_value = safe_float(

                kumho[
                    0
                ].get(
                    "trde_prica",
                    0
                )
            )


            print(

                "실제 거래대금:",
                f"{raw_value / 100:,.2f}억원"
            )


def test_actual_value_map():

    value_map = (
        build_actual_trading_value_map()
    )


    print(
        "거래대금 Map 종목 수:",
        len(value_map)
    )


    code = "002990"


    if code in value_map:

        item = (
            value_map[
                code
            ]
        )


        print(
            "\n금호건설:"
        )


        print(
            item
        )


        print(

            "실제 거래대금:",
            f"{item['actual_trading_value'] / 100_000_000:,.2f}억원"
        )


def test_actual_vs_estimated():

    """
    실제 거래대금과
    현재가×거래량 추정치 차이 확인
    """


    rows = (
        get_change_rate_rank(
            "001"
        )
    )


    target = None


    for i, row in enumerate(
        rows,
        start=1
    ):

        if (
            clean_stock_code(
                row.get(
                    "stk_cd",
                    ""
                )
            )
            == "002990"
        ):

            target = (
                normalize_change_row(

                    row,

                    "KOSPI",

                    i
                )
            )

            break


    if target is None:

        print(
            "KA10027에 금호건설 없음"
        )

        return


    actual_map = (
        build_actual_trading_value_map()
    )


    attach_trading_value(

        target,

        actual_map
    )


    print(
        "종목:",
        target[
            "stock_name"
        ]
    )


    print(

        "실제 거래대금:",

        (
            f"{target['actual_trading_value'] / 100_000_000:,.2f}억원"

            if target[
                "actual_trading_value"
            ] is not None

            else "없음"
        )
    )


    print(

        "추정 거래대금:",

        f"{target['estimated_trading_value'] / 100_000_000:,.2f}억원"
    )


    print(

        "최종 사용값:",

        f"{target['trading_value_used'] / 100_000_000:,.2f}억원"
    )


    print(

        "SOURCE:",

        target[
            "trading_value_source"
        ]
    )


def test_quote(
    stock_code="002990"
):

    raw = get_stock_quote(
        stock_code
    )


    print(
        "원본:"
    )

    print(raw)


    print(
        "\n정규화:"
    )

    print(
        normalize_quote(
            raw
        )
    )


def test_nxt(
    stock_code="005930"
):

    # 테스트할 때는 캐시를 비워 실제 API를 다시 확인
    code = clean_stock_code(
        stock_code
    )

    nxt_eligibility_cache.pop(
        code,
        None
    )

    result = is_nxt_tradable(
        code
    )

    print(
        f"{code} / "
        f"{get_nxt_status_text(code)} / "
        f"raw={result}"
    )


def test_paper_strategies():

    test_time = datetime(2026, 8, 27, 9, 10, 0)

    fake = {
        "stock_code": "999999",
        "stock_name": "테스트종목",
        "current_price": 10000,
        "score": 85,
        "trading_value_source": "ACTUAL",
        "actual_trading_value": 50_000_000_000,
        "estimated_trading_value": 52_000_000_000,
        "high_gap": 0.5,
        "history_available_sec": 180,
        "price_change_30s": 0.2,
        "price_change_60s": 0.4,
        "high_gap_change_60s": -0.3,
        "scan_session": "MAIN",
        "_scan_start_ts": (test_time - timedelta(seconds=5)).timestamp(),
        "_score_evaluated_ts": test_time.timestamp(),
    }

    trade_id = open_paper_trade(fake, "BASE")
    p = paper_positions.get(trade_id)

    print("trade_id:", trade_id)
    print("가상진입가:", p["entry_price"])
    print("전략 수:", len(p["strategies"]))

    for name in ["T100_S050", "T200_S150", "T400_S350"]:
        strategy = p["strategies"].get(name)
        if strategy:
            print(
                name,
                "TP", strategy["tp"],
                "/ SL", strategy["sl"],
                "/ 목표가", round(strategy["target_price"], 0),
                "/ 손절가", round(strategy["stop_price"], 0)
            )

    paper_positions.pop(trade_id, None)
    paper_position_ids_by_code.pop("999999", None)
    paper_entered_today.discard(("BASE", "999999"))


def test_scan_once():

    candidates = (
        scan_market()
    )


    if not candidates:

        print(
            "\n조건 통과 종목 없음"
        )

        return


    data = []


    for x in candidates:


        actual = (

            x[
                "actual_trading_value"
            ]

            / 100_000_000

            if x[
                "actual_trading_value"
            ] is not None

            else None
        )


        estimated = (

            x[
                "estimated_trading_value"
            ]

            / 100_000_000
        )


        used = (

            x[
                "trading_value_used"
            ]

            / 100_000_000
        )


        data.append({

            "종목":
                x[
                    "stock_name"
                ],

            "현재가":
                x[
                    "current_price"
                ],

            "등락률":
                x[
                    "change_rate"
                ],

            "거래량":
                x[
                    "volume"
                ],

            "실제거래대금(억)":
                actual,

            "추정거래대금(억)":
                round(
                    estimated,
                    1
                ),

            "사용거래대금(억)":
                round(
                    used,
                    1
                ),

            "SOURCE":
                x[
                    "trading_value_source"
                ],

            "당일고가":
                x[
                    "day_high"
                ],

            "고점대비%":
                round(
                    x[
                        "high_gap"
                    ],
                    2
                ),

            "점수":
                x[
                    "score"
                ],

            "알림대상":
                (
                    x["score"]
                    >= MIN_SIGNAL_SCORE
                ),

            "거래대금점수":
                x.get(
                    "score_detail",
                    {}
                ).get(
                    "trading_value",
                    0
                ),

            "고점점수":
                x.get(
                    "score_detail",
                    {}
                ).get(
                    "high_position",
                    0
                ),

            "거래대금증가점수":
                x.get(
                    "score_detail",
                    {}
                ).get(
                    "value_growth",
                    0
                ),

            "거래량증가점수":
                x.get(
                    "score_detail",
                    {}
                ).get(
                    "volume_growth",
                    0
                )
        })


    display(
        pd.DataFrame(
            data
        )
    )


def test_auto_trade_config():

    print(
        "AUTO_TRADE_ENABLED =",
        AUTO_TRADE_ENABLED
    )

    print(
        "운영모드 =",
        (
            "실제 자동매매 + 가상매매"
            if AUTO_TRADE_ENABLED
            else "가상매매만"
        )
    )

    print(
        "LIVE_STRATEGY =",
        LIVE_STRATEGY,
        EXIT_STRATEGIES.get(
            LIVE_STRATEGY
        )
    )

    print(
        "종목당 매수예산 =",
        f"{LIVE_TRADE_AMOUNT_WON:,.0f}원"
    )

    print(
        "최대 종목 수 =",
        LIVE_MAX_STOCKS
    )

    print(
        "총 운용예산 =",
        f"{LIVE_TOTAL_BUDGET_WON:,.0f}원"
    )

    print(
        "수량계산 여유율 =",
        f"{LIVE_MARKET_ORDER_BUFFER_PCT:.1f}%"
    )

    print(
        "하루 최대손실 =",
        f"{LIVE_DAILY_MAX_LOSS_WON:,.0f}원"
    )

    if AUTO_TRADE_ENABLED:
        validate_live_trading_config()
        print(
            "✅ 실제 자동매매 안전설정 검증 통과"
        )
    else:
        print(
            "✅ 실제 주문 OFF 상태"
        )


def test_websocket(
    stock_code="005930",
    wait_sec=8
):

    get_kiwoom_token()

    manager = start_websocket_manager()

    if manager is None:
        print(
            "WEBSOCKET_ENABLED=False"
        )
        return

    session = get_session()

    print(
        f"WebSocket 테스트 세션: {session}"
    )

    print(
        "등록코드:",
        realtime_item_code(
            stock_code,
            session
        )
    )

    manager.subscribe_stock(
        stock_code,
        session
    )

    deadline = (
        time.time()
        + wait_sec
    )

    while time.time() < deadline:
        price = get_realtime_price(
            stock_code
        )

        if price:
            print(
                f"✅ 실시간 체결 수신: "
                f"{stock_code} / "
                f"{price:,.0f}원"
            )
            return price

        time.sleep(0.5)

    print(
        "⚠️ 지정 시간 동안 실시간 체결이 없었습니다. "
        "장 상태/NXT 거래가능 여부/종목 거래 여부를 확인하세요."
    )
    return None


# ============================================================
# 37. 전략 성과 확인
# ============================================================

def show_strategy_performance():

    if not os.path.exists(PAPER_TRADE_FILE):
        print("아직 가상매매 결과가 없습니다.")
        return

    df = pd.read_csv(PAPER_TRADE_FILE)

    group_cols = ["strategy", "TP", "SL"]
    if "entry_mode" in df.columns:
        group_cols = ["entry_mode"] + group_cols

    summary = (
        df
        .groupby(group_cols)
        .agg(
            거래횟수=("return_rate", "count"),
            승률=("return_rate", lambda x: (x > 0).mean() * 100),
            평균수익률=("return_rate", "mean"),
            평균MFE=("MFE", "mean"),
            평균MAE=("MAE", "mean")
        )
        .reset_index()
    )

    display(summary)



def test_v166_core_logic():
    """네트워크 없이 v1.6.6 핵심 회귀/Episode/실전 Gate를 점검합니다."""
    global price_history
    global PAPER_ENTRY_DECISION_FILE
    global paper_entered_today
    global paper_positions
    global paper_position_ids_by_code
    global paper_stock_entry_counts_today
    global paper_mode_entry_counts_today
    global paper_last_trade_id_by_mode
    global paper_trade_registry
    global entry_path_trackers
    global entry_path_ids_by_code
    global post_exit_trackers
    global post_exit_ids_by_code
    global pre_first_75_states
    global score_75_seen_today
    global score_shadow_states
    global confirm_pending
    global confirm_started_today
    global watch_episode_states
    global watch_episode_counts
    global live_entered_today
    global live_positions
    global live_orders
    global live_trade_count
    global live_trading_halted
    global live_recovery_mode
    global AUTO_TRADE_ENABLED
    global WEBSOCKET_ENABLED
    global websocket_manager

    print("전략 수:", len(EXIT_STRATEGIES))

    # 0) 배포/핵심 연구설정 회귀
    assert STRATEGY_VERSION == "v1.6.8"
    assert len(EXIT_STRATEGIES) == 169
    assert AUTO_TRADE_ENABLED is False
    assert LIVE_ENTRY_MODE == "FIRST_75_PASS"
    assert WATCH_SCORE == 60
    assert MIN_SIGNAL_SCORE == 75
    assert SCAN_INTERVAL_SEC == 15
    assert API_MIN_INTERVAL_SEC == 0.25
    assert GROWTH_LOOKBACK_SEC == 60
    assert PRE_HISTORY_MIN_SEC == 60
    assert CONFIRM_MIN_RISE_PCT == 0.10
    assert CONFIRM_TIMEOUT_SEC == 45
    assert EXIT_STRATEGIES["T200_S150"] == {"tp": 2.0, "sl": -1.5}
    assert ENTRY_PATH_HORIZONS_SEC == [30, 60, 120, 180, 300]
    assert POST_EXIT_HORIZONS_SEC == [300, 600, 1800]
    assert len(ENTRY_DECISION_COLUMNS) == len(set(ENTRY_DECISION_COLUMNS))

    # 1) history current sample 제외 회귀
    backup_history = price_history
    try:
        price_history = {
            "999999": [
                {"ts": 970.0, "price": 100.0, "high_gap": 2.0},
                {"ts": 1000.0, "price": 101.0, "high_gap": 1.5},
            ]
        }
        metrics = get_history_metrics("999999", now_ts=1000.0)
        assert abs(metrics["price_change_15s_actual_sec"] - 30.0) < 1e-9
        assert abs(metrics["high_gap_change_30s_actual_sec"] - 30.0) < 1e-9
    finally:
        price_history = backup_history

    # 2) PRE / CONFIRM 회귀
    base = {
        "history_available_sec": 60,
        "price_change_30s": 0.2,
        "price_change_60s": 0.3,
        "high_gap_change_60s": -0.1,
    }
    assert evaluate_pre_history(base) == ("PASS", "OK")
    assert evaluate_pre_history(dict(base, price_change_30s=0.0))[0] == "FAIL"
    assert evaluate_pre_history(dict(base, high_gap_change_60s=None))[0] == "DATA_UNAVAILABLE"
    t_first = datetime(2026, 8, 27, 9, 10, 0)
    t_confirm = t_first + timedelta(seconds=30)
    assert abs(_confirm_elapsed_sec(t_first, t_confirm) - 30.0) < 1e-9

    # 3) 초 단위 세션 경계 회귀
    assert get_session_at(datetime(2026, 8, 27, 15, 29, 59)) == "MAIN"
    assert get_session_at(datetime(2026, 8, 27, 15, 30, 0)) == "WAIT"

    # 4) Episode 재진입 / 같은 Episode 중복금지 / 이전 trade OPEN 허용
    backups = {
        "PAPER_ENTRY_DECISION_FILE": PAPER_ENTRY_DECISION_FILE,
        "paper_entered_today": paper_entered_today,
        "paper_positions": paper_positions,
        "paper_position_ids_by_code": paper_position_ids_by_code,
        "paper_stock_entry_counts_today": paper_stock_entry_counts_today,
        "paper_mode_entry_counts_today": paper_mode_entry_counts_today,
        "paper_last_trade_id_by_mode": paper_last_trade_id_by_mode,
        "paper_trade_registry": paper_trade_registry,
        "entry_path_trackers": entry_path_trackers,
        "entry_path_ids_by_code": entry_path_ids_by_code,
        "post_exit_trackers": post_exit_trackers,
        "post_exit_ids_by_code": post_exit_ids_by_code,
        "pre_first_75_states": pre_first_75_states,
        "score_75_seen_today": score_75_seen_today,
        "score_shadow_states": score_shadow_states,
        "confirm_pending": confirm_pending,
        "confirm_started_today": confirm_started_today,
        "watch_episode_states": watch_episode_states,
        "watch_episode_counts": watch_episode_counts,
        "live_entered_today": live_entered_today,
        "live_positions": live_positions,
        "live_orders": live_orders,
        "live_trade_count": live_trade_count,
        "live_trading_halted": live_trading_halted,
        "live_recovery_mode": live_recovery_mode,
        "AUTO_TRADE_ENABLED": AUTO_TRADE_ENABLED,
        "WEBSOCKET_ENABLED": WEBSOCKET_ENABLED,
        "websocket_manager": websocket_manager,
    }

    test_decision_file = os.path.join(os.getcwd(), "_v166_test_entry_decisions.csv")

    try:
        PAPER_ENTRY_DECISION_FILE = test_decision_file
        if os.path.exists(test_decision_file):
            os.remove(test_decision_file)

        paper_entered_today = set()
        paper_positions = {}
        paper_position_ids_by_code = {}
        paper_stock_entry_counts_today = {}
        paper_mode_entry_counts_today = {}
        paper_last_trade_id_by_mode = {}
        paper_trade_registry = {}
        entry_path_trackers = {}
        entry_path_ids_by_code = {}
        post_exit_trackers = {}
        post_exit_ids_by_code = {}
        pre_first_75_states = {}
        score_75_seen_today = set()
        score_shadow_states = {}
        confirm_pending = {}
        confirm_started_today = set()
        watch_episode_states = {}
        watch_episode_counts = {}
        live_entered_today = set()
        live_positions = {}
        live_orders = {}
        live_trade_count = 0
        live_trading_halted = False
        live_recovery_mode = False
        WEBSOCKET_ENABLED = False
        websocket_manager = None

        def make_stock(code, score, when, price=100.0):
            s = {
                "stock_code": code,
                "stock_name": f"테스트{code}",
                "market": "KOSPI",
                "current_price": price,
                "change_rate": 8.0,
                "volume": 1_000_000,
                "score": score,
                "high_gap": 1.0,
                "trading_value_source": "ACTUAL",
                "trading_value_used": 50_000_000_000,
                "trading_value_rank": 1,
                "actual_trading_value": 50_000_000_000,
                "estimated_trading_value": 50_000_000_000,
                "day_high": 101.0,
                "value_growth": 1.1,
                "volume_growth": 1.1,
                "history_available_sec": 60,
                "history_sample_count": 5,
                "price_change_30s": 0.2,
                "price_change_60s": 0.3,
                "high_gap_change_60s": -0.1,
                "scan_session": "MAIN",
                "_scan_start_ts": (when - timedelta(seconds=5)).timestamp(),
                "_scan_sample_ts": (when - timedelta(seconds=1)).timestamp(),
                "_score_evaluated_ts": when.timestamp(),
            }
            attach_session_decision_metrics(s, "MAIN", when)
            register_watch_if_needed(s)
            attach_watch_metrics(s, when)
            return s

        code = "990100"
        t1 = datetime(2026, 8, 27, 9, 10, 0)
        s1 = make_stock(code, 76, t1, 100.0)
        register_pre_first_75_if_needed(s1, t1)
        attach_pre_first_75_metrics(s1)

        trade1 = open_paper_trade(
            s1, "PRE_HISTORY", {"pre_entry_type": "FIRST_75_PASS"}
        )
        assert trade1
        assert len(paper_positions[trade1]["strategies"]) == 169
        assert paper_positions[trade1]["mode_entry_seq_today"] == 1
        assert paper_positions[trade1]["is_reentry"] is False

        # 같은 Episode에서는 재진입 금지
        assert open_paper_trade(
            s1, "PRE_HISTORY", {"pre_entry_type": "FIRST_75_PASS"}
        ) is None

        # Episode #1 종료 후 #2 시작. 이전 169 전략은 OPEN인 채 유지.
        close_watch_episode(code, "TEST_END", t1 + timedelta(minutes=1))
        t2 = t1 + timedelta(minutes=2)
        s2 = make_stock(code, 76, t2, 101.0)
        register_pre_first_75_if_needed(s2, t2)
        attach_pre_first_75_metrics(s2)

        trade2 = open_paper_trade(
            s2, "PRE_HISTORY", {"pre_entry_type": "FIRST_75_PASS"}
        )
        assert trade2 and trade2 != trade1
        assert trade1 in paper_positions and trade2 in paper_positions
        assert paper_positions[trade2]["mode_entry_seq_today"] == 2
        assert paper_positions[trade2]["is_reentry"] is True
        assert paper_positions[trade2]["previous_same_mode_trade_id"] == trade1
        assert paper_positions[trade2]["previous_same_mode_result"] == "OPEN"

        # 5) 모든 mode의 Episode key가 분리됨(BASE 예시)
        base2 = open_paper_trade(s2, "BASE")
        assert base2
        assert open_paper_trade(s2, "BASE") is None
        close_watch_episode(code, "TEST_END2", t2 + timedelta(minutes=1))
        t3 = t2 + timedelta(minutes=2)
        s3 = make_stock(code, 76, t3, 102.0)
        base3 = open_paper_trade(s3, "BASE")
        assert base3 and base3 != base2

        # 6) WebSocket 해제 조건: paper/path/post-exit 중 하나라도 있으면 해제 금지
        class DummyWS:
            def __init__(self):
                self.unsubscribed = []
            def unsubscribe_stock(self, c):
                self.unsubscribed.append(c)

        websocket_manager = DummyWS()
        test_ws_code = "990200"
        paper_position_ids_by_code[test_ws_code] = {"T1"}
        maybe_release_realtime(test_ws_code)
        assert websocket_manager.unsubscribed == []
        paper_position_ids_by_code.pop(test_ws_code, None)
        entry_path_ids_by_code[test_ws_code] = {"P1"}
        maybe_release_realtime(test_ws_code)
        assert websocket_manager.unsubscribed == []
        entry_path_ids_by_code.pop(test_ws_code, None)
        post_exit_ids_by_code[test_ws_code] = {"X1"}
        maybe_release_realtime(test_ws_code)
        assert websocket_manager.unsubscribed == []
        post_exit_ids_by_code.pop(test_ws_code, None)
        maybe_release_realtime(test_ws_code)
        assert websocket_manager.unsubscribed == [test_ws_code]

        # 7) 실제진입 Gate: OFF / 전략 / 시간 / 5종목 / 동일종목
        gate_stock = make_stock("990300", 76, datetime(2026, 8, 27, 9, 10, 0), 100.0)
        AUTO_TRADE_ENABLED = False
        assert can_open_live_trade(
            gate_stock, "PRE_HISTORY", "FIRST_75_PASS", datetime(2026, 8, 27, 9, 10, 0)
        )[0] is False

        AUTO_TRADE_ENABLED = True
        assert can_open_live_trade(
            gate_stock, "BASE", "", datetime(2026, 8, 27, 9, 10, 0)
        )[0] is False
        assert can_open_live_trade(
            gate_stock, "PRE_HISTORY", "LATER_PASS", datetime(2026, 8, 27, 9, 10, 0)
        )[0] is False
        assert can_open_live_trade(
            gate_stock, "CONFIRM", "", datetime(2026, 8, 27, 9, 10, 0)
        )[0] is False
        assert can_open_live_trade(
            gate_stock, "PRE_HISTORY", "FIRST_75_PASS", datetime(2026, 8, 27, 9, 10, 0)
        )[0] is True
        assert can_open_live_trade(
            gate_stock, "PRE_HISTORY", "FIRST_75_PASS", datetime(2026, 8, 27, 9, 4, 59)
        )[0] is False

        live_entered_today = {"1", "2", "3", "4", "5"}
        assert can_open_live_trade(
            gate_stock, "PRE_HISTORY", "FIRST_75_PASS", datetime(2026, 8, 27, 9, 10, 0)
        )[0] is False

        live_entered_today = {gate_stock["stock_code"]}
        assert can_open_live_trade(
            gate_stock, "PRE_HISTORY", "FIRST_75_PASS", datetime(2026, 8, 27, 9, 10, 0)
        )[0] is False

        # 8) 고가주 수량: 100만원 / buffer 반영 후 0주
        high_price = 1_050_000
        budget_price = high_price * (1 + LIVE_MARKET_ORDER_BUFFER_PCT / 100)
        assert int(LIVE_TRADE_AMOUNT_WON // budget_price) == 0

        # 9) paper/live 연결 필드
        live_link_fields = {
            "paper_trade_id", "entry_mode", "pre_entry_type", "watch_episode_id"
        }
        # 실제 함수 소스 레벨에서도 네 필드를 order에 보존하는지 확인
        import inspect
        maybe_src = inspect.getsource(maybe_open_live_trade)
        assert all(field in maybe_src for field in live_link_fields)

    finally:
        PAPER_ENTRY_DECISION_FILE = backups["PAPER_ENTRY_DECISION_FILE"]
        paper_entered_today = backups["paper_entered_today"]
        paper_positions = backups["paper_positions"]
        paper_position_ids_by_code = backups["paper_position_ids_by_code"]
        paper_stock_entry_counts_today = backups["paper_stock_entry_counts_today"]
        paper_mode_entry_counts_today = backups["paper_mode_entry_counts_today"]
        paper_last_trade_id_by_mode = backups["paper_last_trade_id_by_mode"]
        paper_trade_registry = backups["paper_trade_registry"]
        entry_path_trackers = backups["entry_path_trackers"]
        entry_path_ids_by_code = backups["entry_path_ids_by_code"]
        post_exit_trackers = backups["post_exit_trackers"]
        post_exit_ids_by_code = backups["post_exit_ids_by_code"]
        pre_first_75_states = backups["pre_first_75_states"]
        score_75_seen_today = backups["score_75_seen_today"]
        score_shadow_states = backups["score_shadow_states"]
        confirm_pending = backups["confirm_pending"]
        confirm_started_today = backups["confirm_started_today"]
        watch_episode_states = backups["watch_episode_states"]
        watch_episode_counts = backups["watch_episode_counts"]
        live_entered_today = backups["live_entered_today"]
        live_positions = backups["live_positions"]
        live_orders = backups["live_orders"]
        live_trade_count = backups["live_trade_count"]
        live_trading_halted = backups["live_trading_halted"]
        live_recovery_mode = backups["live_recovery_mode"]
        AUTO_TRADE_ENABLED = backups["AUTO_TRADE_ENABLED"]
        WEBSOCKET_ENABLED = backups["WEBSOCKET_ENABLED"]
        websocket_manager = backups["websocket_manager"]

        if os.path.exists(test_decision_file):
            os.remove(test_decision_file)

    print("✅ v1.6.7 핵심 연구 회귀 / Episode 재진입 / 실전 Gate 검증 통과")



def test_v166_episode_mode_reentry():
    """Shadow/CONFIRM까지 새 WATCH Episode 상태가 독립적으로 다시 열리는지 확인합니다."""
    global PAPER_ENTRY_DECISION_FILE
    global paper_entered_today
    global paper_positions
    global paper_position_ids_by_code
    global paper_stock_entry_counts_today
    global paper_mode_entry_counts_today
    global paper_last_trade_id_by_mode
    global paper_trade_registry
    global entry_path_trackers
    global entry_path_ids_by_code
    global pre_first_75_states
    global score_75_seen_today
    global score_shadow_states
    global confirm_pending
    global confirm_started_today
    global watch_episode_states
    global watch_episode_counts
    global WEBSOCKET_ENABLED
    global websocket_manager

    backups = {
        "PAPER_ENTRY_DECISION_FILE": PAPER_ENTRY_DECISION_FILE,
        "paper_entered_today": paper_entered_today,
        "paper_positions": paper_positions,
        "paper_position_ids_by_code": paper_position_ids_by_code,
        "paper_stock_entry_counts_today": paper_stock_entry_counts_today,
        "paper_mode_entry_counts_today": paper_mode_entry_counts_today,
        "paper_last_trade_id_by_mode": paper_last_trade_id_by_mode,
        "paper_trade_registry": paper_trade_registry,
        "entry_path_trackers": entry_path_trackers,
        "entry_path_ids_by_code": entry_path_ids_by_code,
        "pre_first_75_states": pre_first_75_states,
        "score_75_seen_today": score_75_seen_today,
        "score_shadow_states": score_shadow_states,
        "confirm_pending": confirm_pending,
        "confirm_started_today": confirm_started_today,
        "watch_episode_states": watch_episode_states,
        "watch_episode_counts": watch_episode_counts,
        "WEBSOCKET_ENABLED": WEBSOCKET_ENABLED,
        "websocket_manager": websocket_manager,
    }

    test_file = os.path.join(os.getcwd(), "_v166_test_episode_modes.csv")

    try:
        PAPER_ENTRY_DECISION_FILE = test_file
        if os.path.exists(test_file):
            os.remove(test_file)

        paper_entered_today = set()
        paper_positions = {}
        paper_position_ids_by_code = {}
        paper_stock_entry_counts_today = {}
        paper_mode_entry_counts_today = {}
        paper_last_trade_id_by_mode = {}
        paper_trade_registry = {}
        entry_path_trackers = {}
        entry_path_ids_by_code = {}
        pre_first_75_states = {}
        score_75_seen_today = set()
        score_shadow_states = {}
        confirm_pending = {}
        confirm_started_today = set()
        watch_episode_states = {}
        watch_episode_counts = {}
        WEBSOCKET_ENABLED = False
        websocket_manager = None

        def make_stock(code, score, when, price=100.0, high_gap=1.0):
            stock = {
                "stock_code": code,
                "stock_name": f"테스트{code}",
                "market": "KOSPI",
                "current_price": price,
                "score": score,
                "high_gap": high_gap,
                "trading_value_source": "ACTUAL",
                "actual_trading_value": 50_000_000_000,
                "estimated_trading_value": 50_000_000_000,
                "history_available_sec": 60,
                "history_sample_count": 5,
                "price_change_30s": 0.2,
                "price_change_60s": 0.3,
                "high_gap_change_60s": -0.1,
                "scan_session": "MAIN",
                "_scan_start_ts": (when - timedelta(seconds=5)).timestamp(),
                "_scan_sample_ts": (when - timedelta(seconds=1)).timestamp(),
                "_score_evaluated_ts": when.timestamp(),
            }
            attach_session_decision_metrics(stock, "MAIN", when)
            register_watch_if_needed(stock)
            attach_watch_metrics(stock, when)
            return stock

        # SHADOW_SCORE_70_74: 당일 75 미도달 조건은 유지하면서 Episode별 재진입.
        code_shadow = "991001"
        t1 = datetime(2026, 8, 27, 9, 10, 0)
        sh1 = make_stock(code_shadow, 72, t1)
        shadow_trade_1 = maybe_open_score_shadow_70_74(sh1)
        assert shadow_trade_1
        close_watch_episode(code_shadow, "TEST", t1 + timedelta(seconds=30))
        sh2 = make_stock(code_shadow, 73, t1 + timedelta(minutes=1))
        shadow_trade_2 = maybe_open_score_shadow_70_74(sh2)
        assert shadow_trade_2 and shadow_trade_2 != shadow_trade_1

        # LIVE_FILTER_SHADOW도 Episode별 재진입.
        code_live_shadow = "991002"
        ls1 = make_stock(code_live_shadow, 76, t1, high_gap=1.0)
        live_shadow_1 = maybe_open_live_filter_shadow(ls1)
        assert live_shadow_1
        close_watch_episode(code_live_shadow, "TEST", t1 + timedelta(seconds=30))
        ls2 = make_stock(code_live_shadow, 77, t1 + timedelta(minutes=1), high_gap=1.0)
        live_shadow_2 = maybe_open_live_filter_shadow(ls2)
        assert live_shadow_2 and live_shadow_2 != live_shadow_1

        # CONFIRM pending/started 상태도 새 Episode에서 새로 시작 가능.
        code_confirm = "991003"
        c1 = make_stock(code_confirm, 76, t1)
        start_confirm_if_needed(c1, 1, t1)
        assert code_confirm in confirm_pending
        first_pending_time = confirm_pending[code_confirm]["first_75_time"]
        close_watch_episode(code_confirm, "TEST", t1 + timedelta(seconds=30))
        c2_time = t1 + timedelta(minutes=1)
        c2 = make_stock(code_confirm, 76, c2_time)
        assert code_confirm not in confirm_pending
        assert code_confirm not in confirm_started_today
        start_confirm_if_needed(c2, 2, c2_time)
        assert code_confirm in confirm_pending
        assert confirm_pending[code_confirm]["first_75_time"] != first_pending_time

    finally:
        PAPER_ENTRY_DECISION_FILE = backups["PAPER_ENTRY_DECISION_FILE"]
        paper_entered_today = backups["paper_entered_today"]
        paper_positions = backups["paper_positions"]
        paper_position_ids_by_code = backups["paper_position_ids_by_code"]
        paper_stock_entry_counts_today = backups["paper_stock_entry_counts_today"]
        paper_mode_entry_counts_today = backups["paper_mode_entry_counts_today"]
        paper_last_trade_id_by_mode = backups["paper_last_trade_id_by_mode"]
        paper_trade_registry = backups["paper_trade_registry"]
        entry_path_trackers = backups["entry_path_trackers"]
        entry_path_ids_by_code = backups["entry_path_ids_by_code"]
        pre_first_75_states = backups["pre_first_75_states"]
        score_75_seen_today = backups["score_75_seen_today"]
        score_shadow_states = backups["score_shadow_states"]
        confirm_pending = backups["confirm_pending"]
        confirm_started_today = backups["confirm_started_today"]
        watch_episode_states = backups["watch_episode_states"]
        watch_episode_counts = backups["watch_episode_counts"]
        WEBSOCKET_ENABLED = backups["WEBSOCKET_ENABLED"]
        websocket_manager = backups["websocket_manager"]
        if os.path.exists(test_file):
            os.remove(test_file)

    print("✅ v1.6.6 모든 연구 mode Episode 재진입 상태 검증 통과")


def test_v166_live_order_safety():
    """실제 주문실패 무재시도/고가주 SKIP/live-paper 연결을 네트워크 없이 검증합니다."""
    global AUTO_TRADE_ENABLED
    global WEBSOCKET_ENABLED
    global websocket_manager
    global live_entered_today
    global live_positions
    global live_orders
    global live_trading_halted
    global live_recovery_mode
    global datetime
    global submit_stock_order
    global send_telegram
    global save_live_state
    global save_live_order_event
    global replay_unmatched_order_events

    RealDatetime = datetime
    backups = {
        "AUTO_TRADE_ENABLED": AUTO_TRADE_ENABLED,
        "WEBSOCKET_ENABLED": WEBSOCKET_ENABLED,
        "websocket_manager": websocket_manager,
        "live_entered_today": live_entered_today,
        "live_positions": live_positions,
        "live_orders": live_orders,
        "live_trading_halted": live_trading_halted,
        "live_recovery_mode": live_recovery_mode,
        "datetime": datetime,
        "submit_stock_order": submit_stock_order,
        "send_telegram": send_telegram,
        "save_live_state": save_live_state,
        "save_live_order_event": save_live_order_event,
        "replay_unmatched_order_events": replay_unmatched_order_events,
    }

    class FixedDatetime(RealDatetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 8, 27, 9, 10, 5)

    try:
        datetime = FixedDatetime
        AUTO_TRADE_ENABLED = True
        WEBSOCKET_ENABLED = False
        websocket_manager = None
        live_entered_today = set()
        live_positions = {}
        live_orders = {}
        live_trading_halted = False
        live_recovery_mode = False
        send_telegram = lambda *args, **kwargs: True
        save_live_state = lambda: None
        save_live_order_event = lambda row: None
        replay_unmatched_order_events = lambda order_no: None

        stock = {
            "stock_code": "991100",
            "stock_name": "실전안전테스트",
            "current_price": 100_000,
            "score": 76,
            "high_gap": 1.0,
            "scan_session": "MAIN",
            "_scan_start_ts": FixedDatetime(2026, 8, 27, 9, 10, 0).timestamp(),
            "_score_evaluated_ts": FixedDatetime(2026, 8, 27, 9, 10, 5).timestamp(),
            "watch_episode_id": "20260827_991100_E001",
        }
        signal_time = FixedDatetime(2026, 8, 27, 9, 10, 5)

        # 주문 실패: 1회 호출 후 동일 종목 재시도 차단.
        calls = []
        def fail_submit(*args, **kwargs):
            calls.append((args, kwargs))
            raise RuntimeError("TEST_ORDER_FAIL")
        submit_stock_order = fail_submit

        assert maybe_open_live_trade(
            stock,
            "PRE_HISTORY",
            "FIRST_75_PASS",
            "PAPER_TEST_1",
            signal_time,
        ) is False
        assert stock["stock_code"] in live_entered_today
        assert len(calls) == 1
        ok, reason = can_open_live_trade(
            stock,
            "PRE_HISTORY",
            "FIRST_75_PASS",
            signal_time,
        )
        assert ok is False and "이미 실제진입/주문시도" in reason

        # 고가주: qty=0이면 주문함수 자체를 호출하지 않음.
        high = dict(stock)
        high["stock_code"] = "991101"
        high["stock_name"] = "고가주테스트"
        high["current_price"] = 1_050_000
        high["watch_episode_id"] = "20260827_991101_E001"
        live_entered_today = set()
        calls.clear()
        assert maybe_open_live_trade(
            high,
            "PRE_HISTORY",
            "FIRST_75_PASS",
            "PAPER_HIGH",
            signal_time,
        ) is False
        assert calls == []
        assert high["stock_code"] not in live_entered_today

        # 정상 접수: 동일 paper 신호 연결정보 보존.
        live_entered_today = set()
        live_orders = {}
        def ok_submit(*args, **kwargs):
            return {"ord_no": "TEST123"}
        submit_stock_order = ok_submit
        assert maybe_open_live_trade(
            stock,
            "PRE_HISTORY",
            "FIRST_75_PASS",
            "PAPER_TEST_1",
            signal_time,
        ) is True
        order = live_orders["TEST123"]
        assert order["paper_trade_id"] == "PAPER_TEST_1"
        assert order["entry_mode"] == "PRE_HISTORY"
        assert order["pre_entry_type"] == "FIRST_75_PASS"
        assert order["watch_episode_id"] == "20260827_991100_E001"

    finally:
        AUTO_TRADE_ENABLED = backups["AUTO_TRADE_ENABLED"]
        WEBSOCKET_ENABLED = backups["WEBSOCKET_ENABLED"]
        websocket_manager = backups["websocket_manager"]
        live_entered_today = backups["live_entered_today"]
        live_positions = backups["live_positions"]
        live_orders = backups["live_orders"]
        live_trading_halted = backups["live_trading_halted"]
        live_recovery_mode = backups["live_recovery_mode"]
        datetime = backups["datetime"]
        submit_stock_order = backups["submit_stock_order"]
        send_telegram = backups["send_telegram"]
        save_live_state = backups["save_live_state"]
        save_live_order_event = backups["save_live_order_event"]
        replay_unmatched_order_events = backups["replay_unmatched_order_events"]

    print("✅ v1.6.6 회귀 테스트 정의 유지 (v1.6.7에서는 test_v167_order_engine_safety 추가)")


def test_v167_order_engine_safety():
    """네트워크 없이 v1.6.7 P0/P1 핵심 수량/안전 로직을 검증합니다."""
    global live_orders, live_positions, live_entered_today
    global live_processed_fill_ids, live_submit_intents, live_trade_count
    global live_daily_realized_pnl, live_trading_halted, live_system_halt_reason
    global live_recovery_mode, live_blocked_codes, live_execution_issue_codes
    global broker_balances, broker_startup_holdings, shutdown_requested
    global send_telegram, save_live_state, save_live_order_event
    global schedule_broker_sync, save_live_trade_result, kiwoom_post
    global LIVE_ORDER_FILE

    backups = {
        "live_orders": live_orders,
        "live_positions": live_positions,
        "live_entered_today": live_entered_today,
        "live_processed_fill_ids": live_processed_fill_ids,
        "live_submit_intents": live_submit_intents,
        "live_trade_count": live_trade_count,
        "live_daily_realized_pnl": live_daily_realized_pnl,
        "live_trading_halted": live_trading_halted,
        "live_system_halt_reason": live_system_halt_reason,
        "live_recovery_mode": live_recovery_mode,
        "live_blocked_codes": live_blocked_codes,
        "live_execution_issue_codes": live_execution_issue_codes,
        "broker_balances": broker_balances,
        "broker_startup_holdings": broker_startup_holdings,
        "shutdown_requested": shutdown_requested,
        "send_telegram": send_telegram,
        "save_live_state": save_live_state,
        "save_live_order_event": save_live_order_event,
        "schedule_broker_sync": schedule_broker_sync,
        "save_live_trade_result": save_live_trade_result,
        "kiwoom_post": kiwoom_post,
        "LIVE_ORDER_FILE": LIVE_ORDER_FILE,
    }

    try:
        send_telegram = lambda *a, **k: True
        save_live_state = lambda: None
        save_live_order_event = lambda row: None
        schedule_broker_sync = lambda *a, **k: None
        save_live_trade_result = lambda *a, **k: (0.0, 0.0)

        live_orders = {}
        live_positions = {}
        live_entered_today = set()
        live_processed_fill_ids = set()
        live_submit_intents = {}
        live_trade_count = 0
        live_daily_realized_pnl = 0.0
        live_trading_halted = False
        live_system_halt_reason = ""
        live_recovery_mode = False
        live_blocked_codes = {}
        live_execution_issue_codes = set()
        broker_balances = {}
        broker_startup_holdings = set()
        shutdown_requested = False

        # BUY: 107주 주문, 이벤트 10/97 -> 107/0이어도 최종 107.
        live_orders["B1"] = _normalize_live_order_state({
            "order_no": "B1", "side": "BUY", "stock_code": "001210", "stock_name": "금호전기",
            "requested_qty": 107, "filled_qty": 0, "filled_amount": 0.0, "status": "SUBMITTED",
            "exchange": "SOR", "signal_price": 10000, "signal_time_str": "", "signal_time": datetime.now(),
            "live_order_time": datetime.now(), "score": 80, "entry_seq": 1,
            "paper_trade_id": "P1", "entry_mode": "PRE_HISTORY", "pre_entry_type": "FIRST_75_PASS",
            "watch_episode_id": "W1",
        })
        handle_order_execution({"9001":"001210","9203":"B1","910":"10000","911":"10","902":"97","909":"F1","913":"체결","905":"매수"})
        handle_order_execution({"9001":"001210","9203":"B1","910":"10010","911":"107","902":"0","909":"F2","913":"체결","905":"매수"})
        assert live_orders["B1"]["filled_qty"] == 107
        assert live_positions["001210"]["auto_managed_qty"] == 107

        # 동일 누적 이벤트 재수신: 수량 증가 없음.
        handle_order_execution({"9001":"001210","9203":"B1","910":"10010","911":"107","902":"0","909":"F3","913":"체결","905":"매수"})
        assert live_orders["B1"]["filled_qty"] == 107
        assert live_positions["001210"]["auto_managed_qty"] == 107

        # SELL: 71주 주문, 46/25 -> 71/0이면 최종 71, 117 금지.
        live_positions["S00001"] = _normalize_live_position_state({
            "stock_code":"S00001", "stock_name":"우리기술", "auto_managed_qty":71, "qty":71,
            "initial_qty":71, "avg_entry_price":10000, "filled_amount":710000, "entry_complete":True,
            "status":"EXIT_PENDING", "entry_seq":2, "target_price":10200, "stop_price":9850,
            "exit_reason":"STOP_LOSS", "exit_trigger_reason":"STOP_LOSS", "exit_trigger_time":datetime.now(),
            "exit_trigger_price":9850,
        })
        live_orders["S1"] = _normalize_live_order_state({
            "order_no":"S1", "side":"SELL", "stock_code":"S00001", "stock_name":"우리기술",
            "requested_qty":71, "filled_qty":0, "filled_amount":0.0, "status":"SUBMITTED", "reason":"STOP_LOSS",
            "entry_seq":2,
        })
        handle_order_execution({"9001":"S00001","9203":"S1","910":"9850","911":"46","902":"25","909":"SF1","913":"체결","905":"매도"})
        assert live_orders["S1"]["filled_qty"] == 46
        handle_order_execution({"9001":"S00001","9203":"S1","910":"9840","911":"71","902":"0","909":"SF2","913":"체결","905":"매도"})
        assert live_orders["S1"]["filled_qty"] == 71
        assert "S00001" not in live_positions

        # 수동추가/수동매도 원장 정책.
        assert reconcile_managed_quantities(100, 0, 120) == (100, 20)
        assert reconcile_managed_quantities(100, 20, 70) == (70, 0)
        assert reconcile_managed_quantities(100, 20, 0) == (0, 0)
        # legacy 내부117 / broker107 -> 자동관리 107로 보정 가능.
        assert reconcile_managed_quantities(117, 0, 107) == (107, 0)

        # 핵심 누적 delta 순수함수.
        assert compute_broker_fill_delta(107, 97, 0) == (10, 10)
        assert compute_broker_fill_delta(107, 0, 10) == (107, 97)
        assert compute_broker_fill_delta(107, 0, 107) == (107, 0)

        # 주문 timeout -> ORDER_STATUS_UNKNOWN.
        def timeout_post(*a, **k):
            raise requests.exceptions.Timeout("test timeout")
        kiwoom_post = timeout_post
        try:
            submit_stock_order("BUY", "000001", 1, "SOR", stock_name="테스트")
            raise AssertionError("timeout이 OrderStatusUnknownError가 아니었습니다.")
        except OrderStatusUnknownError:
            pass

        # 종료요청 후 REST 호출 자체가 0건이어야 함.
        calls = {"n":0}
        def count_post(*a, **k):
            calls["n"] += 1
            return {"ord_no":"X"}
        kiwoom_post = count_post
        shutdown_requested = True
        try:
            submit_stock_order("SELL", "000001", 1, "SOR", stock_name="테스트")
            raise AssertionError("shutdown_requested에서 주문이 허용되었습니다.")
        except ShutdownRequestedError:
            pass
        assert calls["n"] == 0
        shutdown_requested = False

        # 고정 CSV 스키마는 event마다 컬럼 수가 달라도 정상 read_csv 가능.
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        tmp.close()
        LIVE_ORDER_FILE = tmp.name
        pathlib_available = True
        # 원래 함수 복구해 실제 CSV writer를 테스트.
        save_live_order_event = backups["save_live_order_event"]
        save_live_order_event({"event":"A", "stock_code":"000001", "requested_qty":1})
        save_live_order_event({"event":"B", "stock_code":"000002", "error":"x", "fill_price":1000})
        df = pd.read_csv(LIVE_ORDER_FILE)
        assert list(df.columns) == LIVE_ORDER_COLUMNS
        assert len(df) == 2
        try:
            os.unlink(LIVE_ORDER_FILE)
        except Exception:
            pass

        print("✅ v1.6.7 주문엔진 안전성 테스트 통과")
        return True

    finally:
        live_orders = backups["live_orders"]
        live_positions = backups["live_positions"]
        live_entered_today = backups["live_entered_today"]
        live_processed_fill_ids = backups["live_processed_fill_ids"]
        live_submit_intents = backups["live_submit_intents"]
        live_trade_count = backups["live_trade_count"]
        live_daily_realized_pnl = backups["live_daily_realized_pnl"]
        live_trading_halted = backups["live_trading_halted"]
        live_system_halt_reason = backups["live_system_halt_reason"]
        live_recovery_mode = backups["live_recovery_mode"]
        live_blocked_codes = backups["live_blocked_codes"]
        live_execution_issue_codes = backups["live_execution_issue_codes"]
        broker_balances = backups["broker_balances"]
        broker_startup_holdings = backups["broker_startup_holdings"]
        shutdown_requested = backups["shutdown_requested"]
        send_telegram = backups["send_telegram"]
        save_live_state = backups["save_live_state"]
        save_live_order_event = backups["save_live_order_event"]
        schedule_broker_sync = backups["schedule_broker_sync"]
        save_live_trade_result = backups["save_live_trade_result"]
        kiwoom_post = backups["kiwoom_post"]
        LIVE_ORDER_FILE = backups["LIVE_ORDER_FILE"]


def test_v168_manual_sell_ledger_helpers():
    """v1.6.8 외부 SELL 누적delta/수량배분/청산시간 helper 회귀테스트."""

    p = {
        "qty": 100,
        "auto_managed_qty": 100,
        "external_qty": 20,
    }
    _normalize_live_position_state(p)

    a = _track_external_sell_execution(p, {
        "9203": "EXT001", "909": "F1", "900": "50", "902": "30",
        "910": "10100", "911": "20",
    })
    assert a["broker_filled_qty"] == 20 and a["delta_qty"] == 20

    b = _track_external_sell_execution(p, {
        "9203": "EXT001", "909": "F2", "900": "50", "902": "0",
        "910": "10200", "911": "30",
    })
    assert b["broker_filled_qty"] == 50 and b["delta_qty"] == 30

    c = _track_external_sell_execution(p, {
        "9203": "EXT001", "909": "F2", "900": "50", "902": "0",
        "910": "10200", "911": "50",
    })
    assert c["broker_filled_qty"] == 50 and c["delta_qty"] == 0

    new_auto, new_external = reconcile_managed_quantities(100, 20, 70)
    assert new_external == 0 and new_auto == 70

    t0 = datetime(2026, 9, 1, 9, 28, 22, 220000)
    t1 = datetime(2026, 9, 1, 9, 28, 34, 790000)
    assert abs(_elapsed_seconds_v168(t0, t1) - 12.57) < 0.001

    print("✅ v1.6.8 외부 SELL delta/배분/청산시간 helper 테스트 통과")
    return True

def run_scanner():

    global sent_diagnostic_times
    global last_live_force_exit_attempt_ts
    global shutdown_requested

    shutdown_requested = False

    log("========================================")
    log(f"스크리너 시작 {STRATEGY_VERSION}")
    log(f"AUTO_TRADE_ENABLED = {AUTO_TRADE_ENABLED}")
    if AUTO_TRADE_ENABLED:
        log("⚠ 실제 주문 ON")
        log(f"LIVE ENTRY = {LIVE_ENTRY_MODE}")
        log(f"시간 = MAIN {LIVE_ENTRY_START}~{LIVE_ENTRY_END}")
        log(f"종목당 최대 = {LIVE_TRADE_AMOUNT_WON:,.0f}원")
        log(f"하루 최대 = {LIVE_MAX_STOCKS}종목 / 동일종목 하루 1회")
        log("TP/SL = +2.00% / -1.50%")
        log("v1.6.8 = v1.6.7 안전장치 유지 / 수동매도 손익·상태저장·청산계측 보완")
    else:
        log("실제 주문 OFF / 연구·가상매매만 실행")
    log("========================================")

    validate_scanner_config()
    validate_live_trading_config()
    get_kiwoom_token()

    restored = load_live_state()
    if AUTO_TRADE_ENABLED:
        if restored:
            reconcile_live_state_with_broker()
        else:
            initialize_broker_account_snapshot()

    start_websocket_manager()
    subscribe_recovered_live_items()

    # v1.6.7 START TELEGRAM COMPACT FORMAT FIX - 2026-08-30
    trade_mode_header = (
        "🔴 실제 자동매매 ON — 실제 주문 실행"
        if AUTO_TRADE_ENABLED
        else "🟢 가상매매 ONLY — 실제 주문 없음"
    )

    live_rule = EXIT_STRATEGIES[LIVE_STRATEGY]

    send_telegram(
        f"🟢 단타 스크리너 {STRATEGY_VERSION} 시작\n\n"
        f"{trade_mode_header}\n"
        f"• 실제진입 : {LIVE_ENTRY_MODE} ONLY\n"
        f"• 진입시간 : MAIN {LIVE_ENTRY_START}~{LIVE_ENTRY_END}\n"
        f"• 종목당 예산 : {LIVE_TRADE_AMOUNT_WON:,.0f}원\n"
        f"• 하루한도 : 최대 {LIVE_MAX_STOCKS}종목 / 동일종목 1회\n"
        f"• 총 예산 : {LIVE_TOTAL_BUDGET_WON:,.0f}원\n"
        f"• 청산 : TP +{live_rule['tp']:.2f}% / SL {live_rule['sl']:.2f}%\n\n"
        "🛡 실제계좌 안전장치\n"
        "• 기존보유 자동매수 제외\n"
        "• auto / external 수량 분리\n"
        "• broker sellable 기준 매도\n"
        "• 주문상태 불명확 : 실제매매 SAFE HALT / 가상연구 계속\n\n"
        "🔎 스캐너\n"
        f"• 운영시간 : {PROGRAM_START}~{PROGRAM_END}\n"
        f"• 스캔 : {SCAN_INTERVAL_SEC}초 / 증가율 약 {GROWTH_LOOKBACK_SEC}초\n"
        f"• WATCH : {WATCH_SCORE}점+ / 진입자격 : {MIN_SIGNAL_SCORE}점+\n"
        f"• 필터 : 등락률 {MIN_CHANGE_RATE:.1f}~{MAX_CHANGE_RATE:.1f}% / "
        f"거래대금 {MIN_TRADING_VALUE_WON / 100_000_000:,.0f}억원+ / "
        f"고점이격 {MAX_HIGH_GAP:.1f}% 이내\n"
        "• WebSocket : 가격/주문체결 실시간 추적\n\n"
        "🔬 가상연구\n"
        "• BASE / PRE_HISTORY / CONFIRM / LIVE_FILTER_SHADOW / SHADOW_SCORE_70_74\n"
        f"• {len(EXIT_STRATEGIES)}개 TP/SL 동시추적 / Episode 재진입 유지"
    )

    last_scan_ts = 0.0
    last_position_check_ts = 0.0
    last_broker_sync_schedule_ts = 0.0

    while True:
        try:
            check_new_day()
            hhmm = datetime.now().strftime("%H:%M")

            if hhmm >= PROGRAM_END:
                # 종료 요청 플래그를 가장 먼저 올려 이후 신규 BUY/SELL/CANCEL submit을 차단.
                shutdown_requested = True
                force_close_all()
                finalize_entry_path_trackers("PARTIAL_PROGRAM_END")
                finalize_post_exit_trackers()

                send_telegram(
                    "🔴 오늘 스크리너 종료\n"
                    f"후보 알림 {daily_alert_count}건\n"
                    f"WATCH 누적 {len(watch_states)}종목"
                )

                if AUTO_TRADE_ENABLED:
                    with STATE_LOCK:
                        remaining_live = [
                            f"{p.get('stock_name', code)} ({code})"
                            for code, p in live_positions.items()
                            if safe_int(p.get("auto_managed_qty", p.get("qty", 0))) > 0
                        ]
                    if remaining_live:
                        send_telegram(
                            "🚨 프로그램 종료 시 실제 자동관리 포지션이 남아 있습니다.\n"
                            + "\n".join(remaining_live[:10])
                            + "\n계좌를 직접 확인하세요."
                        )

                if websocket_manager is not None:
                    websocket_manager.stop()

                save_live_state()
                log("프로그램 정상 종료")
                break

            if hhmm < PROGRAM_START:
                time.sleep(5)
                continue

            if hhmm in DIAGNOSTIC_TIMES and hhmm not in sent_diagnostic_times:
                send_diagnostic()
                sent_diagnostic_times.add(hhmm)

            if (
                AUTO_TRADE_ENABLED
                and not shutdown_requested
                and time.time() - last_broker_sync_schedule_ts >= BROKER_SYNC_INTERVAL_SEC
            ):
                schedule_broker_sync(None, reason="PERIODIC", external_event=False)
                last_broker_sync_schedule_ts = time.time()

            if (
                AUTO_TRADE_ENABLED
                and LIVE_FORCE_EXIT_ENABLED
                and hhmm >= LIVE_FORCE_EXIT_TIME
                and time.time() - last_live_force_exit_attempt_ts >= LIVE_FORCE_EXIT_RETRY_SEC
            ):
                force_close_live_positions()
                last_live_force_exit_attempt_ts = time.time()

            if time.time() - last_position_check_ts >= POSITION_CHECK_INTERVAL_SEC:
                monitor_open_positions()
                last_position_check_ts = time.time()

            if get_session() != "WAIT":
                if time.time() - last_scan_ts >= SCAN_INTERVAL_SEC:
                    last_scan_ts = time.time()
                    scan_market()

            time.sleep(1)

        except KeyboardInterrupt:
            # P0: 첫 동작으로 submit gate를 닫습니다.
            shutdown_requested = True
            finalize_entry_path_trackers("PARTIAL_INTERRUPTED")
            finalize_post_exit_trackers()
            if websocket_manager is not None:
                websocket_manager.stop()
            save_live_state()
            log("사용자가 프로그램 중단 / 신규 주문 제출 차단 완료")
            break

        except Exception as e:
            log(f"메인루프 오류: {e}")
            traceback.print_exc()
            time.sleep(5)

# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    run_scanner()





# ============================================================



# ============================================================
# 변수 / 용어 QUICK REFERENCE
# ============================================================
#
# [AUTO_TRADE_ENABLED]
# False = 가상연구만 실행 / 실제 주문 없음
# True  = 기존 가상연구 전체 + FIRST_75_PASS 실제주문 검토
# v1.6.8 전달본 기본값은 반드시 False.
#
# [WATCH_SCORE / MIN_SIGNAL_SCORE]
# WATCH_SCORE=60 : 진입 기준이 아니라 사전 관찰 시작선.
# MIN_SIGNAL_SCORE=75 : 75점 이상이 실제 신호/연구 진입 자격선.
#
# [WATCH Episode]
# 종목이 WATCH_SCORE 이상으로 올라온 뒤 조건에서 이탈하기 전까지의 연속 관찰 구간.
# 조건에서 정상 이탈 후 다시 올라오면 새 Episode가 시작될 수 있음.
# 실제매매는 동일 종목 하루 1회 정책을 별도로 유지.
#
# [BASE]
# 75점 이상 최초 신호를 가장 넓게 보는 기준 연구군.
#
# [PRE_HISTORY]
# 75점 이상 시점에 과거 가격 HISTORY가 충분하고,
# 직전 30초/60초 상승 + 60초 high_gap 감소 조건을 보는 연구군.
#
# [FIRST_75_PASS]
# 해당 WATCH Episode에서 최초 75점 도달 시 PRE_HISTORY까지 PASS한 신호.
# v1.6.8 실제매매는 이 신호만 사용.
#
# [LATER_PASS]
# 최초 75점에서는 PRE_HISTORY를 통과하지 못했지만 이후 정상 스캔에서 통과한 연구군.
# 실제매매에는 사용하지 않음.
#
# [CONFIRM]
# 최초 75점 신호 이후 다음 정상 스캔에서 추가 상승을 확인하는 연구군.
# 실제매매에는 사용하지 않음.
#
# [price_change_30s / price_change_60s]
# 현재 판정시점 가격이 약 30초/60초 전 가격보다 몇 % 변했는지.
# 양수면 해당 기간 가격 상승.
#
# [history_available_sec]
# 현재 종목에 대해 프로그램이 실제 확보한 rolling 가격 HISTORY 길이(초).
# PRE_HISTORY_MIN_SEC보다 짧으면 조건 실패가 아니라 DATA_UNAVAILABLE로 구분.
#
# [day_high / high_gap / high_gap_change_60s]
# day_high = 당일 고가
# high_gap = 당일 고가 대비 현재가의 이격률(%). 작을수록 고점에 가까움.
# high_gap_change_60s = 현재 high_gap - 약 60초 전 high_gap.
# 음수면 최근 60초 동안 고점에 가까워진 방향.
#
# [MAX_HIGH_GAP / LIVE_MAX_HIGH_GAP / 연구 high_gap<=0.25]
# MAX_HIGH_GAP = 스캐너/점수 체계의 넓은 고점이격 기준.
# LIVE_MAX_HIGH_GAP = LIVE_FILTER_SHADOW 연구용 기준이며 실제 FIRST_75_PASS 주문필터 아님.
# high_gap<=0.25 등 더 좁은 값은 사후 연구분석 조건이며 v1.6.8 실제 진입조건으로 구현하지 않음.
#
# [ENTRY_PATH]
# 진입 후 30/60/120/180/300초 가격경로를 독립 추적하는 연구자료.
# price_change_30s/60s는 진입 '전' 방향성이고 ENTRY_PATH는 진입 '후' 경로라는 차이.
#
# [MFE / MAE]
# MFE = 진입 후 가장 유리했던 최대 수익구간.
# MAE = 진입 후 가장 불리했던 최대 손실구간.
#
# [TP / SL / TIME_EXIT / T200_S150]
# TP = Take Profit(익절), SL = Stop Loss(손절), TIME_EXIT = 시간청산.
# T200_S150 = TP +2.00%, SL -1.50%.
#
# [SHADOW / LIVE_FILTER_SHADOW / SHADOW_SCORE_70_74]
# 실제 주문 없이 조건 성능만 비교하는 연구군.
# LIVE_FILTER_SHADOW = 실제 운용시간/고점조건을 재현하는 연구용 Shadow.
# SHADOW_SCORE_70_74 = 75점 직전 70~74점 구간 연구.
#
# [POST_EXIT]
# 기준전략 T200_S150 청산 후 5/10/30분 가격을 추가 추적하는 연구자료.
#
# [v1.6.8 청산 지연 필드]
# exit_trigger_time         = TP/SL/TIME_EXIT가 처음 발생한 시각
# broker_precheck_start_time= SELL 전 broker 보유/매도가능/미체결 조회 시작
# broker_precheck_end_time  = 위 안전조회 종료
# broker_precheck_sec       = broker 사전조회 소요시간
# sell_order_time           = 실제 SELL 주문 REST 응답/주문번호 확인 시각
# sell_fill_time            = SELL 체결 완료 시각
# trigger_to_order_sec      = trigger -> 주문제출 완료
# order_to_fill_sec         = 주문 -> 체결
# trigger_to_fill_sec       = trigger -> 체결 전체
# ============================================================


# PROJECT CONTINUITY NOTES / DECISION HISTORY
# ============================================================
# 목적:
# - 다음 버전/다음 채팅에서 최신 코드만 읽어도 주요 의사결정과
#   현재 적용조건/연구후보를 파악할 수 있게 한다.
# - 과거 이력은 삭제/수정하지 않고 새 판단을 누적한다.
# - 최근 성과가 좋아도 연구후보를 자동으로 실전필터로 승격하지 않는다.
#
# [현재 적용조건]
# - 연구: BASE / PRE_HISTORY(FIRST_75_PASS, LATER_PASS) / CONFIRM /
#   LIVE_FILTER_SHADOW / SHADOW_SCORE_70_74 모두 유지.
# - 연구 grid: TP +1.00~+4.00 / SL -0.50~-3.50 / 0.25% 간격 = 169개.
# - WATCH 60 / SIGNAL 75 / SCAN 15초 / API 최소간격 0.25초 / growth 약 60초.
# - PRE: history>=60, 30s>0, 60s>0, high_gap_change_60s<0.
# - CONFIRM: 첫 정상평가, 75 유지, first75 대비 +0.10%, 45초 이내.
# - v1.6.6 paper: 새 WATCH Episode마다 동일종목/동일mode 재진입 허용.
# - 실제: FIRST_75_PASS만, MAIN 09:05~09:30, 종목당 최대 100만원,
#   하루 최대 5종목, 동일종목 하루 1회, qty=0 고가주 SKIP,
#   T200_S150(+2/-1.5), 주문실패 자동재주문 없음.
#
# [연구 후보 - 아직 실제 필터 아님]
# - FIRST_75_PASS에서 09:05 이후가 상대적으로 양호한 경향.
# - first75 직전 60초 가격상승률 +0.5~+2.0% 구간 양호 후보.
# - 진입 당시 high_gap <= 0.25% 양호 후보.
# - first75 score >= 80 양호 후보.
# - 표본 부족/후행최적화 위험 때문에 위 조건은 실제진입 필터에 넣지 않음.
#
# 2026-08-17 (월)
# - 가상매매 우선 검증 결정.
# - REST 후보탐색 + WebSocket 진입후 추적 구조.
# - KA10001 병목 확인 및 병렬조회 도입.
# - 169 TP/SL 연구체계 확립.
#
# 2026-08-18 (화)
# - 병렬조회/WebSocket 장중 정상검증.
# - SCAN 15초 / API 0.25초 운영방향.
#
# 2026-08-19 (수) ~ 2026-08-21 (금)
# - BASE 표본 누적.
# - 8/18~8/21 기준 T200_S150 평균 약 -0.34%.
# - TP/SL보다 진입 직전 가격방향 연구 필요성 확인.
#
# 2026-08-22 (토) ~ 2026-08-23 (일)
# - v1.6.2 설계.
# - BASE 대조군 고정.
# - PRE_HISTORY / CONFIRM / LIVE_FILTER_SHADOW 도입.
#
# 2026-08-24 (월)
# - BASE/PRE/CONFIRM/LIVE_FILTER 병렬비교 시작.
# - PRE를 최초통과와 지연통과로 분리할 필요성 확인.
#
# 2026-08-25 (화)
# - FIRST_75_PASS / LATER_PASS 분리.
# - FIRST가 LATER보다 우수하게 관찰.
# - 진입 직전 30초 방향성 중요 후보.
# - entry path/post-exit 정밀기록 방향 확정.
#
# 2026-08-26 (수)
# - v1.6.4 운영.
# - 시간축/PRE 상태/first WS 신뢰도 정리.
# - FIRST > LATER 재현.
# - 15:30:56 세션 경계 오진입 버그 발견.
#
# 2026-08-26 (수) 저녁
# - v1.6.5 설계.
# - 초 단위 session guard.
# - first75→entry 지연비용.
# - 70~74 Shadow.
# - Shadow→75 paired sample.
#
# 2026-08-27 (목)
# - v1.6.5 20시까지 정상 운영.
# - 61진입×169 = 10,309 결과 정상.
# - 70~74 중 끝내 75를 못 넘는 종목군이 약함.
# - CONFIRM은 진입지연 비용 문제 가능성.
# - LATER의 추격진입 문제 지속 관찰.
#
# 2026-08-27 (목)
# - FIRST_75_PASS 누적 N=14 / 평균 약 +0.51%.
# - LATER_PASS N=14 / 평균 약 -1.02%.
# - 3거래일 연속 FIRST > LATER.
#
# 2026-08-27 (목)
# - FIRST 심화 연구후보: 09:05 이후, 60초 +0.5~2.0%,
#   high_gap <=0.25%, first75 score >=80.
# - 표본 부족/후행최적화 위험으로 실제필터에는 적용하지 않음.
#
# 2026-08-27 (목)
# - 제한적 실제매매 시작방향 합의.
# - 실제진입 FIRST_75_PASS만 / MAIN 09:05~09:30.
# - 종목당 최대 100만원 / 하루 최대 5종목 / 동일종목 하루 1회.
# - 고가주 1주 불가 시 SKIP / TP +2 / SL -1.5.
# - 주문실패 자동재주문 없음.
#
# 2026-08-27 (목)
# - 가상매매는 새 WATCH Episode에서 동일종목 재진입 허용 결정.
# - 실제매매는 동일종목 하루 1회 유지.
# - 연구시스템은 실전전략 때문에 변형하지 않는 원칙 재확인.
#
# 2026-08-27 (목) v1.6.6 구현
# - v1.6.5 최신 코드를 직접 확장.
# - paper entry key를 (entry_mode, code, watch_episode_id)로 확장.
# - 이전 Episode의 169 전략이 OPEN이어도 새 Episode trade_id 생성 허용.
# - 재진입 분석 컬럼(stock/mode seq, is_reentry, previous result/trade_id) 추가.
# - 실제 주문 호출을 PRE_HISTORY FIRST_75_PASS 생성 지점으로 한정.
# - 주문 실패/거부 후 같은 종목 자동 재시도 금지.
# - live order/fill/exit와 동일 paper_trade_id 연결 필드 추가.

#
# 2026-08-28 (금)
# - v1.6.6 실제 자동매매 5종목 소액 테스트.
# - 실제진입 Gate는 FIRST_75_PASS / 09:05~09:30으로 정상동작.
# - 우리기술/심텍/해치텍 자동청산 완료.
# - 금호전기에서 107주 주문/실제보유 107주인데 내부 117주로 잘못 인식하는 체결수량 누적 오류 확인.
# - 우리기술 SELL에서도 46주 후 누적 71주 이벤트를 117주로 잘못 누적하여 BUY/SELL 공통 부분체결 해석 버그로 판단.
# - 금호전기 매도가능수량 부족 오류가 반복되고 프로그램 중단 이후에도 잠시 주문시도가 이어지는 문제 확인.
# - 실제계좌 보유/매도가능수량과 내부상태 교차검증 필요성 확정.
# - 특정 종목 오류는 해당 종목 격리, 다른 실매매는 계속하는 방향 합의.
# - 시스템 전체 주문상태 불명확 시 실제매매만 SAFE HALT하고 가상연구는 계속하기로 함.
# - 내부수량과 broker수량이 다르면 broker 실제 매도가능수량으로 자동매도하는 방향 합의.
# - TP/SL 목표가격은 WebSocket 전략기준가로 고정하고 broker 평균매입가로 재계산하지 않기로 함.
# - 사용자의 기존/장기보유 종목은 실제 자동매수 제외.
# - 사용자의 수동추가매수 물량은 자동물량과 분리.
# - 사용자의 수동매도는 broker 상태를 통해 자동물량을 동기화.
# - 자동매도 주문 중 수동개입 시 기존 주문 자동취소는 하지 않고 추가주문 차단 후 잔고 동기화.
# - Telegram 매도 첫 줄을 '종목명 / 익절·손절 / 실제수익률 / 실제손익' 형식으로 변경.
# - 매수/매도 알림 마지막에 오늘 실제진입 순번 / 남은 실제진입 / 현재 실제보유 표시.
# - 모든 실매매 오류 알림에 종목명(종목코드) 필수 표시.
# - 09:00~09:05 실전 확대는 향후 누적성과 분석 후 검토하고 월요일에는 09:05~09:30 유지.
#
# 2026-08-30 (일) v1.6.7 구현
# - v1.6.6 최신 Notebook 3셀 구조를 직접 수정. 연구체계/169-grid/Episode 재진입 로직은 유지.
# - BUY/SELL 체결수량을 requested_qty-unfilled_qty 누적값으로 계산하고 delta만 원장에 반영.
# - 중복 누적체결 이벤트는 delta=0으로 무시하며 requested_qty invariant 위반 시 종목 격리.
# - broker held/sellable/avg_price 원장을 추가하고 실제 SELL은 broker sellable 검증 후 비동기 worker에서 제출.
# - 기존보유/장중 수동매수 종목은 실제 자동매수 제외. 개인매매는 자동포지션에 편입하지 않음.
# - auto_managed_qty / external_qty / pending_auto_buy_qty / pending_auto_sell_qty 분리.
# - 수동매도는 external 물량 우선 차감 후 auto 물량 차감 규칙으로 동기화.
# - 자동매도 중 수동개입은 기존 주문을 취소하지 않고 추가주문 차단 후 broker 상태 확인.
# - 주문 timeout/네트워크 응답불명확은 ORDER_STATUS_UNKNOWN으로 처리하고 실제매매만 SAFE HALT.
# - shutdown_requested를 추가하여 KeyboardInterrupt/종료 요청 즉시 신규 BUY/SELL/CANCEL submit 차단.
# - live_orders CSV를 고정 스키마로 변경하고 live 기록에 trigger/broker/auto/external 필드 확대.
# - Telegram 매수/매도 요약 첫 줄과 마지막 슬롯/현재보유 표시, 오류 알림 종목명+코드 표시 적용.
# ============================================================

# ============================================================
# PROJECT CONTINUITY PRINCIPLE
# ============================================================
# 최신 검증 코드 전체를 보존하고 필요한 변경점만 최소 수정/통합한 뒤 전체본 제공.
# 기존 최신 검증 코드를 엎어서 재작성하지 않는다.
#
# 2026-08-31 (월)
# - v1.6.8 전체코드는 반드시 013_260830_v1.6.7_startmsg_fix.ipynb를 직접 base로 한다.
# - 013_260831_v1.6.7_manual_pnl_fix.ipynb는 임시 실험본이므로 base로 사용하지 않는다.
# - 실제 진입전략은 FIRST_75_PASS only / MAIN 09:05~09:30 / 종목당 100만원 / 하루 5종목 /
#   동일종목 실제 1회 / T200_S150(+2.00/-1.50)를 유지한다.
# - 가상연구 BASE/PRE_HISTORY/FIRST_75_PASS/LATER_PASS/CONFIRM/LIVE_FILTER_SHADOW/
#   SHADOW_SCORE_70_74, WATCH Episode, ENTRY_PATH, POST_EXIT, 169 TP/SL grid는 유지한다.
#
# 2026-09-01 (화)
# - 비에이치 실전에서 STOP_LOSS trigger 09:28:22.220 -> SELL order 09:28:34.736 ->
#   fill 09:28:34.790, trigger-to-fill 약 12.57초를 확인했다.
# - SELL 전 broker positions + pending/sellable 안전검증은 제거하지 않는다.
#   안전을 유지한 상태에서 trigger/precheck/order/fill 단계별 시간을 계측한다.
# - live_state_v167.json.tmp Permission denied 경쟁 가능성을 확인했다.
#   v1.6.8에서는 전용 lock + 고유 tmp + atomic os.replace + 제한적 retry로 보완하며,
#   단발성 state 저장 실패만으로 SAFE HALT하지 않는다.
# - 수동/외부 SELL 손익은 broker requested_qty-unfilled_qty 누적체결량의 delta만 사용한다.
#   FID 911을 매 이벤트마다 증분처럼 누적하지 않는다.
# - 수동매도로 broker held가 감소하면 external_qty를 먼저 차감하고 그 다음 auto_managed_qty를 차감한다.
#   실제 감소한 auto_managed_qty만 프로그램의 live 실현손익/일손실 한도에 반영한다.
# - 프로그램과 무관한 개인매매는 live 손익/진입카운트에 편입하지 않는다.
# - 자동 SELL 진행 중 수동개입이 감지되어도 사용자 주문을 자동취소하지 않으며,
#   추가 주문을 차단하고 broker 동기화로 상태를 확정해 이중손익을 막는다.
#
# [향후 연구 후보 - v1.6.8 필터/수집 기능 아님]
# - FIRST_75_PASS 발생 건수와 성과가 장초반 시장상태와 관련되는지 향후 검증한다.
# - 후보 시장상태: KOSPI/KOSDAQ 장초반 등락률, 시장 상승확산도, 전체 거래활성도,
#   삼성전자·SK하이닉스 장초반 추세.
# - 위 항목은 v1.6.8 실제진입 필터나 신규 데이터수집 기능으로 구현하지 않는다.
# ============================================================
