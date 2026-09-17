# 조사 범위 기록

reviews/<batch>/inventory.json에 조사 경계를 남긴다. 실제 반영 기록은 applied.jsonl이다.

- version: 1
- period: from/through, 시간대 포함 ISO 시각
- basis: last_apply/last_full_review, 근거 경로·시각·범위. 최초는 unknown과 전체 조사 이유
- sources: wiki.toml의 활성 원천별 id(설정 별칭)·kind·location·status·reason·items
- 원천 status: scanned / partial / unavailable / not_applicable. 접근 실패는 unavailable. 빈 scanned는 실제 확인한 0건
- items: id·reference·status(reviewed/unread)·reason. reviewed이면 classification(new/update/conflict/duplicate/out_of_scope)과 comparison(기존 페이지와 대조 결과) 필수

현재 검토 대화처럼 승인 근거로만 등록한 원천은 not_applicable과 이유를 기록할 수 있다. 같은 kind의 서로 다른 폴더도 원천별로 기록한다.

`python3 -B scripts/inventory.py docs/wiki/reviews/<batch>/inventory.json --require-complete`

종료 0은 기록상 완료, 2는 유효하지만 미완료, 1은 형식 오류다. 모든 활성 원천과 검토 항목이 완료되어야 through가 반환된다. 선언된 기록의 일관성을 검사할 뿐 실제 원천 누락·읽기·의미 대조를 보증하지 않는다. 다음 실행은 전체 조사 경계와 미반영·보류 항목을 함께 이어받는다.
