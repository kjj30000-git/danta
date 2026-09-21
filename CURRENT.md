# CURRENT PROJECT STATE

## Current validated release

- Version: **v1.7.1.3**
- Path: `code/releases/021_260911_v1.7.1.3.ipynb`
- Execution date: **2026-09-11**
- SHA-256: `c7d65e6754e8594a815a7cf9c57d4f8fb1950a76998a5a638749ffbbca52bff0`
- Saved default: `AUTO_TRADE_ENABLED = False`
- Status: release 실행 및 `data/1.7.1.3(260911)/` 결과 수집 완료

## Current research release

- Version: **v2.1.2**
- Intended execution date: **2026-09-16**
- Parent: `code/releases/024_260915_v2.1.1.ipynb`
- Default mode: `EXECUTION_MODE = "RESEARCH"`
- Scope: FIRST_75_PASS 의미 보존, LATER_PASS OFF 실제 생성 차단, CALM 계통의 확정 FIRST 부모관계 복구
- Release: `code/releases/025_260916_v2.1.2.ipynb`
- SHA-256: `f6c8e82d1b14c07169bc716aca79c2f8b0bbefeaf6596bd35e80cbdd2771ac62`
- Verification basis: compile·pyflakes·clean-process cold-start·시간경계 replay·169/20/16 grid·FIRST/LATER/CALM 행동 회귀·negative-control·2차 비판적 리뷰
- Status: **정적·mock 검증 PASS / RESEARCH 실행 가능**. 실제·키움 모의주문은 0건이어야 하며 실전 확대 승인이 아님

## Latest handoff

- [v2.2.0 눌림·지지·재상승 최종 인수인계서](handoff/2026-09-21/v2.1.2_to_v2.2.0_PULLBACK_SUPPORT_최종인수인계서_2026-09-21.md)

## Next implementation — v2.2.0 (2026-09-21 (월))

- Status: **최종 인수인계서 등록 / 다음 코드 구현·검증 대상**. 현재 연구 release v2.1.2를 대체하는 검증 완료 선언이 아니다.
- 예상 release 번호: **026**. 실행일이 확정되기 전 날짜를 넣은 release 경로를 임의로 만들지 않는다.
- 설계 기준: [v2.2.0 눌림·지지·재상승 최종 인수인계서](handoff/2026-09-21/v2.1.2_to_v2.2.0_PULLBACK_SUPPORT_최종인수인계서_2026-09-21.md)
- 부모: `code/releases/025_260916_v2.1.2.ipynb` 전체를 직접 읽고 최소 수정·통합한다.
- 주식 신규 진입 연구는 `BASE`, `FIRST_75_PASS`, `PULLBACK_SUPPORT_ENTRY`, `PULLBACK_RECLAIM_ENTRY` 4개로 정리한다. BASE/FIRST_75의 기존 조건과 저장 의미는 유지한다.
- 나머지 주식 전략은 신규 진입 표본 생성 OFF이며 함수·컬럼·과거 CSV 호환성은 보존한다. ETF 관련 기존 코드·파일·grid는 이번 변경 대상이 아니다.
- BASE/FIRST_75 후보는 기존 paper trade 종료 후에도 당일 관찰 종료까지 추적한다.
- 완료 1분봉 기준 눌림 -1.50%, 지지 이탈 허용폭 0.30%, 지지 후보 3봉, 확정 5봉 및 저점 대비 종가 +0.40%, RECLAIM은 SUPPORT 다음 봉부터 직전 5봉 고점 +0.10% 종가 돌파로 판단한다.
- 신규 전략의 시간대 필터와 최대 눌림깊이 상한은 두지 않는다. 세션·프로그램 종료·기존 강제청산 경계는 유지한다. Higher Low와 거래량은 저장용 feature이며 진입 필수조건이 아니다.
- 새 두 전략도 각각 가상체결 시에만 169-grid를 생성한다. 후보 대기 단계에서는 생성하지 않으며, 각 신규 전략은 동일종목 당일 최대 1회다. 왕복 추정비용은 0.24%다.
- 신호 확정 뒤 첫 가용가격으로 가상체결하고 신호/체결 시각·가격을 분리한다.
- Telegram은 기존 WATCH/HISTORY/30초/60초/고점이격 본문을 유지하고 전략명 prefix를 추가한다. 기존 가상전략 안내문만 삭제하며 grid는 유지한다.
- 09:30~15:30 매시 30분에 전략별 당일 누적목록을 발송한다. `번호. 종목명(종목코드) - HH:MM:SS` 형식, 최초 신호시각 순서, 전략별 동일종목 1회 표시를 사용한다.
- 합의사항을 v2.2.0 한 릴리스에 일괄 반영하되 기능별 검증 후 1차 검증 → 독립 2차 비판적 리뷰 → 수정 → 최종 전체 회귀검증을 수행한다.
- 기본값은 `EXECUTION_MODE="RESEARCH"`이며 실제·키움 모의 주문은 0건이다.

## Historical decisions

아래 v2.1/v2.0 항목은 과거 버전의 결정 이력이다. v2.2.0 신규 수집 ON/OFF와 grid 적용 대상은 위의 최신 설계 및 인수인계서를 따른다. 기존 구현·과거 CSV·주문 안전장치는 보존한다.

## v2.1 fixed decisions

- 부모 `code/releases/022_260914_v2.0.ipynb` 전체를 복제하고 국소 수정
- 09:00~09:15 등락률 상위 후보를 동적으로 독립 추적
- 09:01~09:15에 `OPENING_LEADER_DIRECT`, `OPENING_LEADER_RETEST`, `OPENING_LEADER_RS` 가상진입
- 등락률 상위는 발견 기준, 실제 거래대금 20억원은 진입 유동성 기준
- FIRST_75 점수를 신규 전략 진입조건으로 사용하지 않음
- 기존 거래대금 상위 ORB와 상태·이름·표본을 분리
- 신규 관찰 파일 `opening_leader_observations_v21.csv`
- 신규 전략은 `NEW_STOCK_20` grid와 왕복 추정비용 0.24% 사용
- 저장·운영 기본값 `RESEARCH`, 실제·키움 모의주문 0건
- 구현 후 1차 검증, 독립 2차 비판적 리뷰, 수정 후 전체 회귀검증

## v2.0 fixed decisions

- 단일 실행 모드 문자열 `RESEARCH` / `MOCK` / `LIVE`; 이중차단은 추가하지 않음
- v2.0 저장·운영 기본값은 `RESEARCH`
- v1.7.1.3 주문엔진은 시간기록 산식 오류만 수정하고 나머지 개선은 동결
- 기존 BASE/FIRST_75 대조군과 선택된 Shadow 유지
- CALM_FIRST_75, CALM 보호청산, ORB 3종, ETF 장후반 모멘텀 신규 수집
- 기존 169 grid, 신규 주식 20 grid, ETF 16 grid를 서로 구분
- 전략 함수 바로 위에 유지/중단/폐기/신규 상태 주석
- Cell 3 QUICK REFERENCE와 Cell 4 CONTINUITY는 부모 구조 보존 후 append-only
- 구현 후 1차 검증과 독립적인 2차 비판적 리뷰를 자동 수행

## Data convention

Scanner / paper / live CSV와 상태 JSON은 다음 형식으로 저장한다.

`data/X.Y.Z(YYMMDD[, YYMMDD...])/`

v2.0 신규 ETF 파일과 연구 파일도 동일한 실행일자 폴더 아래에 둔다.
