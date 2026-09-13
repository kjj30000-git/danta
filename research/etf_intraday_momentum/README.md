# ETF Intraday Momentum — 독립 연구 프로젝트

이 폴더는 Gao·Han·Li·Zhou(2018)의 `Market Intraday Momentum` 가설을 국내 KOSPI·KOSDAQ 지수와 지수 ETF 과거 분봉으로 검증하기 위한 독립 프로젝트다.

장중 자동매매 프로그램 `code/releases/022_260914_v2.0.ipynb`와 실행·API 대기열·CSV·상태파일을 공유하지 않는다. 이 프로젝트에는 실제 또는 모의 주문 기능을 넣지 않는다.

## 폴더 구조

- `handoff/` — 전체 코드 작성용 최종 인수인계서
- `notebooks/` — 이후 완성할 수집·정제·백테스트 전체 노트북
- `data/raw/` — 키움 REST 원응답 기반 분봉
- `data/processed/` — 정규화·검증을 마친 분봉
- `outputs/` — 백테스트 결과·품질 보고서

대용량 데이터 파일은 수집 전 보존정책과 GitHub 용량을 확인한다. 자격증명, 접근토큰 및 `.env`는 절대 커밋하지 않는다.

## 다음 작업

다음 문서를 먼저 읽고 전체 코드를 작성한다.

`handoff/2026-09-14_ETF_과거분봉_수집백테스트_전체코드작성_최종인수인계서.md`

예정 노트북:

`notebooks/RES_001_ETF_과거분봉_수집백테스트.ipynb`
