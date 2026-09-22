# CURRENT PROJECT STATE

## Current validated release

- Version: **v1.7.1.3**
- Path: `code/releases/021_260911_v1.7.1.3.ipynb`
- Execution date: **2026-09-11**
- SHA-256: `c7d65e6754e8594a815a7cf9c57d4f8fb1950a76998a5a638749ffbbca52bff0`
- Saved default: `AUTO_TRADE_ENABLED = False`
- Status: release 실행 및 `data/1.7.1.3(260911)/` 결과 수집 완료

## Current research release

- Version: **v2.2.0**
- Intended execution date: **2026-09-22**
- Parent: `code/releases/025_260916_v2.1.2.ipynb`
- Default mode: `EXECUTION_MODE = "RESEARCH"`
- Scope: BASE·FIRST_75_PASS 의미 보존, PULLBACK_SUPPORT_ENTRY·PULLBACK_RECLAIM_ENTRY 신규 수집, 그 밖의 주식 신규 진입 생성 OFF, ETF 계통 불변
- Release: `code/releases/026_260922_v2.2.0.ipynb`
- SHA-256: `0b69fd0a3cf164a73ac5152b6674eb14199d8d6a101aa698f707fba221094dbe`
- Verification basis: 4-cell compile·pyflakes·clean-process cold-start·부모 replay·부모 정의 302/302·1차 fixture 66개·독립 2차 fixture 32개·negative-control·결정적 재빌드
- Reports: [빌드 검증](reports/build/v2.2.0_build_validation_2026-09-21.md) · [2차 비판적 리뷰](reports/inspection/v2.2.0_second_review_2026-09-21.md) · [최종 회귀검증](reports/regression/v2.2.0_final_regression_2026-09-21.md)
- Status: **정적·mock 검증 PASS / RESEARCH 실행 가능**. 검증 중 외부 연결·실제·키움 모의주문은 모두 0건이며 실전 확대 승인이 아님

## Latest handoff

- [v2.3.0 가격구조·시간별 SNAPSHOT 최종 인수인계서](handoff/2026-09-22/v2.2.0_to_v2.3.0_STRUCTURE_SNAPSHOT_최종인수인계서_2026-09-22.md)

## Next approved design: v2.3.0 (2026-09-22 (화))

- 부모는 검증된 `code/releases/026_260922_v2.2.0.ipynb` 전체본이며 BASE·FIRST_75_PASS·ETF·주문안전 경로를 보존한다.
- v2.2.0 `PULLBACK_SUPPORT_ENTRY`와 `PULLBACK_RECLAIM_ENTRY`는 코드·과거 호환성을 남기고 신규 생성과 Telegram만 OFF한다.
- 신규 `PULLBACK_STRUCTURE_ENTRY`는 시간 제한 없이 `L1 → R1/B → L2 방어 → B+0.10% 완료봉 종가 돌파 → 다음 완료봉 B−0.20% 유지`로 진입한다.
- 신규 SNAPSHOT은 유효 L1 뒤 30·60·90·120·150·180·210·240분을 평가하며 DIRECT와 RECLAIM을 독립 가상진입으로 비교한다.
- SNAPSHOT은 실제 가상진입 생성 시에만 Telegram을 발송한다. 모든 신규 알림은 README의 문단·글머리기호 가독성 규칙을 따른다.
- BASE/FIRST_75는 기존 169-grid, 신규 STRUCTURE/SNAPSHOT 3종은 TP +1.00~+3.00%와 SL −0.75~−2.25%의 63-grid를 사용한다. 신규 대표 표시전략은 `T200_S125`다.
- 눌림 신규 진입은 15:10 이전, 평가는 15:20까지다. 240분 이후에도 STRUCTURE는 시간필터 없이 관찰하되 세션 경계는 지킨다.
- 목표 버전은 v2.3.0이며 아직 release 코드가 아니다. 구현·검증은 최신 인수인계서를 따른다.

## v2.2.0 implementation and validation (2026-09-21 (월))

- `code/releases/026_260922_v2.2.0.ipynb`로 구현했으며 부모 4개 code cell과 top-level 정의 302개를 보존했다.
- 주식 신규 진입 연구는 `BASE`, `FIRST_75_PASS`, `PULLBACK_SUPPORT_ENTRY`, `PULLBACK_RECLAIM_ENTRY` 4개다. 나머지 주식 전략은 함수·컬럼·과거 CSV 호환성을 유지하면서 신규 생성만 차단했다. ETF 코드는 변경하지 않았다.
- 완료 1분봉으로 눌림 -1.50%, 지지 이탈 허용폭 0.30%, 후보 3봉, 확정 5봉·저점 대비 종가 +0.40%, SUPPORT 이후 직전 5봉 고점 +0.10% RECLAIM을 구현했다.
- 후보 등록 중간봉, 재시작 첫 봉, WS sequence gap·재연결 봉은 불완전 봉으로 처리해 확정 판단에서 제외한다.
- 신호 다음 수신 tick에서 가상체결하고 신규 전략별·종목별 당일 1회만 169-grid를 원자적으로 생성한다. 후보 상태에서는 grid를 생성하지 않는다.
- 후보·paper grid·중복키·Telegram outbox를 원자 저장하며 signal ledger의 `FILL`로 checkpoint crash window를 복구한다.
- Telegram 전략 prefix, 기존 후보 상세, 09:30~15:30 매시 30분 누적 요약, 전송 불명 상태의 중복 방지 정책을 반영했다.
- 1차 fixture 66개와 독립 2차 fixture 32개가 PASS했다. 외부 연결·실제·모의 주문은 0건이었고 결정적 재빌드 결과도 동일했다.
- Kiwoom 0B field 15 거래량 의미와 서버의 무통지 누락은 첫 장중 실행에서 관찰한다. 거래량은 진입 필수가 아닌 feature다.
- 기본값은 `EXECUTION_MODE="RESEARCH"`이며 실제·키움 모의 주문은 0건이어야 한다.

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
