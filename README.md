# danta — 주식 단타 자동매매 프로젝트

이 저장소는 **코드 원본·검증 후보·인수인계·자동검증 보고서·장별 CSV 결과**를 분리해서 관리합니다.

## 폴더 구조

- `CURRENT.md` — 현재 검증 기준본과 다음 작업
- `code/releases/` — 버전별 기준/릴리스 코드
- `code/candidates/` — 비교·독립검증용 후보 코드
- `handoff/` — 날짜별 인수인계서
- `reports/build/` — 빌드 검증 보고서
- `reports/comparison/` — 코드 비교 보고서
- `reports/regression/` — 회귀테스트 결과
- `reports/inspection/` — 핵심 구현 점검 보고서
- `data/` — 날짜별 장 결과 CSV
- `.github/` — 자동 빌드/비교/검증 도구와 workflow

## 일일 CSV 업로드 규칙

장 종료 후 그날 생성된 CSV는 아래처럼 날짜와 실행 버전을 묶어 올립니다.

```text
data/
└─ YYYY-MM-DD/
   └─ vX.Y.Z/
      ├─ scanner_signals_*.csv
      ├─ scanner_system_*.csv
      ├─ paper_entry_decisions_*.csv
      ├─ paper_entry_path_*.csv
      ├─ paper_post_exit_*.csv
      ├─ paper_trades_*.csv
      ├─ live_orders_*.csv
      └─ live_trades_*.csv
```

파일이 없는 종류는 억지로 만들 필요가 없습니다.

## 운영 원칙

최신 검증 코드 전체를 보존하고, 필요한 변경점만 최소 수정·통합한 뒤 새 전체본을 생성합니다.
프로젝트 채팅은 설계·결정·리뷰의 본체로 사용하고, GitHub는 실제 코드/데이터 원본의 본체로 사용합니다.
