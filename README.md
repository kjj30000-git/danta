# danta — 주식 단타 자동매매 프로젝트

이 저장소는 **코드 원본·검증 후보·인수인계·자동검증 보고서·장별 실행 결과**를 분리해서 관리합니다.

## 폴더 구조

- `CURRENT.md` — 현재 검증 기준본과 다음 작업
- `code/releases/` — **최종/기준 `.ipynb` 코드를 바로 보관**
- `code/candidates/` — 비교·독립검증용 후보 코드
- `handoff/` — 날짜별 인수인계서
- `reports/build/` — 빌드 검증 보고서
- `reports/comparison/` — 코드 비교 보고서
- `reports/regression/` — 회귀테스트 결과
- `reports/inspection/` — 핵심 구현 점검 보고서
- `data/` — `버전(실행일자)` 형식의 장별 실행 결과
- `.github/` — 자동 빌드/비교/검증 도구와 workflow

## Release 규칙

`code/releases/`에 들어가면 버전 폴더를 다시 거치지 않고 `.ipynb` 파일을 바로 볼 수 있게 관리합니다.

파일명의 날짜는 **해당 코드를 실제로 실행할 예정인 날짜**를 기준으로 합니다.

예:

```text
code/releases/
├─ 013_260830_v1.6.7_startmsg_fix.ipynb
├─ 014_260902_v1.6.8.ipynb
└─ 015_260903_v1.6.9.ipynb
```

기본적으로 release에는 `.ipynb`만 보관합니다. `.txt`와 `.py` 복사본은 별도 요청이 있을 때만 만듭니다.

## 실행 결과 업로드 규칙

장 종료 후 생성된 CSV와 상태 JSON은 `data/` 아래에 **`버전(날짜)`** 폴더로 묶어 올립니다.

폴더명 형식은 `X.Y.Z(YYMMDD[, YYMMDD...])`입니다. 같은 버전으로 여러 날짜를 실행했다면 날짜를 쉼표로 구분해 한 폴더에 기록합니다.

예:

```text
data/
├─ 1.6.7(260831, 260901)/
│  ├─ scanner_signals_v167.csv
│  ├─ scanner_system_v167.csv
│  ├─ paper_entry_decisions_v167.csv
│  ├─ paper_entry_path_v167.csv
│  ├─ paper_post_exit_v167.csv
│  ├─ paper_trades_v167.csv
│  ├─ live_orders_v167.csv
│  ├─ live_trades_v167.csv
│  └─ live_state_v167.json
└─ 1.6.8(260902)/
   └─ ...
```

해당 날짜에 생성되지 않은 파일 종류는 억지로 만들 필요가 없습니다. 실행 결과 폴더는 저장소 루트가 아니라 항상 `data/` 아래에 둡니다.

## 운영 원칙

최신 검증 코드 전체를 보존하고, 필요한 변경점만 최소 수정·통합한 뒤 새 전체본을 생성합니다.
프로젝트 채팅은 설계·결정·리뷰의 본체로 사용하고, GitHub 저장소는 완성된 코드·인수인계서·데이터 원본의 기본 보관 위치로 사용합니다.

---

## 프로젝트 불변 기준 (PROJECT CONTINUITY)

이 절은 버전별 기능보다 상위에 있는 장기 운영 원칙입니다. 향후 분석·설계·코드 작성 시 반드시 **README.md + 해당 작업의 최신 인수인계서 + 직전 검증 release 전체 코드**를 함께 읽습니다.

문서 역할은 다음과 같습니다.

- `README.md`: 모든 버전에 적용되는 불변 원칙
- 최신 인수인계서: 해당 분석·릴리스에서 합의한 구체적인 변경사항
- 직전 검증 release: 삭제하거나 재구성하지 않고 직접 승계할 구현 기준
- 새로운 명시적 사용자 결정이 있을 때만 기존 원칙을 변경하며, 변경 이유와 날짜를 README와 CONTINUITY에 기록

### 1. 분석과 코드 작성 단계 분리

기본 작업 순서는 다음과 같습니다.

1. 장 종료 결과와 과거 데이터를 병합·검증·분석
2. 확정·보류·기각 사항을 구분한 다음 릴리스용 인수인계서 작성
3. 새 채팅에서 인수인계서와 직전 검증 코드를 기준으로 전체 코드 작성
4. 부모 정의 보존·구문·cold-start·회귀검증 후 release 등록

데이터 분석과 전체 코드 작성을 한 번에 진행하지 않습니다. 표본이 부족하면 실전 조건을 완화하지 않고 Shadow 수집을 연장합니다.

### 2. Parent preservation

새 버전은 직전 최신 검증 코드를 처음부터 다시 쓰는 작업이 아닙니다.

- 사용자가 지정한 직전 검증 release를 직접 읽고 필요한 부분만 최소 수정·통합
- 기존 함수·클래스·상수·import·주문엔진·연구체계·파일 구조 보존
- QUICK REFERENCE와 PROJECT CONTINUITY는 부모 원문을 유지하고 append-only로 추가
- `if __name__ == "__main__": run_scanner()`는 프로그램 셀 최하단에 정확히 1회
- 일부 검색 결과나 과거 답변의 코드 조각으로 전체 코드를 재조립하지 않음
- parent definition preservation, top-level use-before-definition, compile, 외부 연결을 막은 cold-start, 행동 회귀검증 필수

### 3. 주문 안전장치 우선

과거 실전 사고를 막기 위한 다음 구조는 명시적 합의 없이 삭제·우회하지 않습니다.

- `requested_qty - unfilled_qty` 기반 체결수량 계산과 초과수량 invariant
- broker 실제 보유수량·매도가능수량·미체결 조회
- 자동관리수량과 외부/수동 보유수량 분리
- 중복 BUY/SELL 및 초과매도 방지
- `ORDER_STATUS_UNKNOWN` SAFE HALT와 `EXIT_ERROR`
- shutdown 이후 신규 주문 차단
- `live_state` atomic save·복구
- 주문·체결·사전조회 latency 및 slippage 기록

청산 지연 개선은 안전검사를 제거하는 방식이 아니라 독립 조회 병렬화, 단계별 시간계측, 실패 처리 강화 방식으로 검증합니다. 일부 조회만 성공한 상태를 정상 잔고로 간주하지 않습니다.

### 4. 연구와 실제매매 분리

- 연구 후보는 먼저 Shadow/counterfactual로 수집
- 충분한 날짜 밖 검증 없이 실제 주문에 연결하지 않음
- 기존 BASE, PRE_HISTORY, FIRST_75_PASS, LATER_PASS, CONFIRM, LIVE_FILTER_SHADOW, SHADOW_SCORE_70_74, WIDE_HIGH_GAP_SHADOW, PRE_FAIL_PULLBACK_SHADOW, WATCH Episode, ENTRY_PATH, POST_EXIT, 169개 TP/SL grid 보존
- 새 진입 연구의 목표는 75점 임계값 미세조정이 아니라 상승 초중반을 포착하는 독립 패턴 탐색
- 새 전략의 실전 승격 여부는 표본 수, 날짜별 재현성, 비용 후 기대값과 Profit Factor로 결정
- 릴리스에 저장하는 기본값은 항상 `AUTO_TRADE_ENABLED=False`

### 5. 데이터 병합·성과 분석 원칙

- `paper_trades`의 TP 13 × SL 13 = 169행은 169개 독립 거래가 아니라 하나의 `trade_id`에 대한 169개 전략 결과
- 진입 표본은 고유 `trade_id`, 전략 결과는 `trade_id + TP + SL` 단위로 구분
- 원본 대용량 CSV와 분할본을 동시에 중복 적재하지 않음
- 분할본은 part 순서, 반복 헤더 제거, UTF-8 BOM 처리 후 논리적으로 결합
- 버전별 컬럼 합집합과 provenance를 보존하고 없는 값은 임의 추정하지 않음
- `stock_code`는 문자열로 보존
- 진입 시점 이후의 MFE·MAE·청산 결과를 진입 feature로 사용하는 미래정보 누수 금지
- 날짜 순서 기반 holdout/walk-forward 및 동일 종목·동일 날짜 그룹 분리
- 모든 성과는 gross와 왕복 추정비용 0.23% 차감 net을 함께 표시
- 승률뿐 아니라 표본 수, 평균·중앙값, gross/net Profit Factor, MFE/MAE, 손실 꼬리, 날짜별 안정성을 함께 평가

### 6. 설정과 표시값의 일치

사용자 설정은 첫 셀에서 명확히 보이고 합리적 범위 안에서 변경 가능해야 합니다.

- 자동매매 ON/OFF
- 수익보호 ON/OFF
- 종목당 투자금액, 최대 진입 횟수, 총예산
- 실제 진입 전략
- TP/SL, 진입·청산 시간, 비용 가정

특정 금액·횟수·전략을 숨은 값으로 고정하지 않습니다. Telegram과 로그의 TP/SL·목표가·손절가도 문자열로 하드코딩하지 않고 실제 선택된 설정에서 동적으로 표시합니다.

### 7. GitHub 전달과 버전 정책

- 완성된 전체 코드는 `code/releases/`
- 작업별 인수인계서는 `handoff/YYYY-MM-DD/`
- 장별 원본 데이터는 `data/버전(실행일자)/`
- GitHub를 코드·인수인계·데이터의 기본 전달 및 보관 경로로 사용
- 전략 세대가 바뀌는 다음 릴리스는 `v1.6.11`이 아니라 **v1.7.0**
- `v2.0`은 주문엔진·데이터 모델·실행 구조 등 호환성을 깨는 전면 재설계에 사용

현재 분석 인수인계서:

`handoff/2026-09-04/v1.6.10_to_v1.7.0_데이터분석_인수인계서_2026-09-04.md`
