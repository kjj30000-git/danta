# CURRENT PROJECT STATE

## Current validated release

- Version: **v1.7.1.3**
- Path: `code/releases/021_260911_v1.7.1.3.ipynb`
- Execution date: **2026-09-11**
- SHA-256: `c7d65e6754e8594a815a7cf9c57d4f8fb1950a76998a5a638749ffbbca52bff0`
- Saved default: `AUTO_TRADE_ENABLED = False`
- Status: release 실행 및 `data/1.7.1.3(260911)/` 결과 수집 완료

## Next target

- Version: **v2.0**
- Intended execution date: **2026-09-14**
- Parent: `code/releases/021_260911_v1.7.1.3.ipynb`
- Default mode: `EXECUTION_MODE = "RESEARCH"`
- Scope: 실제·키움 모의주문 없이 내부 가상매매와 데이터 수집, 유지·신규 전략 병렬연구

## Latest handoff

- `handoff/2026-09-13/v1.7.1.3_to_v2.0_연구전용_다중전략_최종인수인계서_2026-09-13.md`

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
