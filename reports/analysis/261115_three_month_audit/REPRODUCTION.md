# 계산 재현

원본 commit은 REPORT.md에 고정했다. 원본 CSV는 수정하지 않았다.

- 대표 결과(paper_cutoff_exits가 별도인 v234는 해당 원장을 연결하고 trade_id+strategy로 중복 제거): paper_trades 분할본을 순서대로 읽고 완전중복 제거. strategy=T250_S150(BASE/FIRST) 또는 T200_S125(STRUCTURE/SNAPSHOT/BALANCE). FIRST는 entry_mode=PRE_HISTORY, pre_entry_type=FIRST_75_PASS. net은 estimated_net_return_pct. 초기 net 부재는 원본 통계에서 공란 유지.
- 포트폴리오: 진입시각/종목코드 순으로, 일별5회/동시5개/종목100만원/총600만원/동일종목 하루1회. 정수주 내림. exit_time이 다음 진입 전에 도래하면 자금 반환. 완료 대표 결과가 있는 표본만 재현했으므로 완전 계좌 성과 아님.
- opening: opening_events의 candidate_id+policy로 FILL/EXIT one-to-one 연결. details의 net_pct 사용. 이 원장은 paper_trades와 합치지 않는다.
- 불확실성: 날짜별 sum/count를 복원추출한 날짜 군집 bootstrap 5,000회(v233)/10,000회(opening), seed261115.
- opening_audit.py는 원본 계산 스크립트로 REPO_ROOT_PLACEHOLDER를 checkout 경로로 치환하고 /tmp/audit를 임시 출력으로 사용한다. portfolio_audit.py의 reps.pkl은 위 대표 결과를 이어 붙인 중간물이다. 원본 체결가와 저장 비용을 그대로 사용한다.
- file_inventory.csv는 csv.reader 기준 구조 점검이며 JSON/.bak 파싱도 수행했다. 폭오류·손상 로그는 REPORT에 기재.
