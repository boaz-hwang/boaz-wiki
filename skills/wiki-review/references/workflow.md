# 위키 검토 도구 사용법

저장소 루트에서 실행한다. Python 표준 라이브러리만 필요하다. 규칙은 `SCHEMA.md`의 검토와 반영 절이다. `docs/wiki`는 기본값이며 실제 위키 경로와 검토자는 wiki.toml을 따른다.

## 파일 배치

```text
docs/wiki/reviews/<batch>/
  working/<topic>/card.json
  working/<topic>/draft/sources/example.md.txt
  working/<topic>/draft/overviews/example.md.txt
  topics/<topic>/r0001/
    card.json
    manifest.json
    review.md
    before/<정식 페이지 경로>.txt
    after/<정식 페이지 경로>.txt
  decisions.jsonl
  applied.jsonl
```

`batch`, `topic`은 영문 소문자·숫자·하이픈 ID. `working`은 수정 가능하고 rNNNN은 보존 사본이다. draft에는 카드 files에 나열한 변경 파일만 `.txt`를 덧붙여 둔다. 예: files의 `sources/example.md` → `draft/sources/example.md.txt`. 전후 사본도 `.md.txt`로 보존해 Obsidian 정식 링크와 충돌하지 않는다. 전체 위키 복사본을 넣지 않는다. 같은 페이지가 겹치는 미반영 주제는 한 묶음으로 준비한다. batch를 달리해 겹치더라도 먼저 반영된 변경 때문에 뒤의 기준 버전이 달라져 재검토가 필요하다.

## 검토 카드 예시

```json
{
  "title": "반품 정책 적용 범위",
  "summary": "주문 시점에 따른 반품 기간을 구분한다.",
  "files": ["sources/session-example.md", "entities/example.md"],
  "judgments": [
    {
      "kind": "fact",
      "before": "모든 주문 14일",
      "proposed": "2월 신규 주문은 30일",
      "reason": "사용자가 변경 정책의 적용 시점을 확인했다",
      "evidence": ["^[/codex-sessions/YYYY/MM/DD/rollout-example.jsonl:123]"]
    },
    {
      "kind": "scope",
      "before": "이전 주문 적용 여부 불명확",
      "proposed": "1월 주문은 기존 14일 유지",
      "reason": "기존 주문과 신규 주문을 구분한다",
      "evidence": ["^[/codex-sessions/YYYY/MM/DD/rollout-example.jsonl:123]"]
    }
  ],
  "dependencies": ["/documents/policy-change.md"]
}
```

예시 경로·줄은 실제 읽은 원문으로 바꾼다. `judgments`에는 fact, interpretation, naming, relationship, confidence, scope 중 관련 유형을 모두 담는다. 각각 before/proposed/reason/evidence 필수. evidence가 없는 해석은 빈 배열로 두고 불확실성을 reason에 설명한다. 변경 파일의 실제 diff가 최종 범위이며 카드 요약과 일치해야 한다.

도구가 각 초안의 줄 인용·로컬 sources·이미 존재하는 연결 페이지를 의존 근거에 자동 추가한다. 간접 근거도 dependencies로 지정한다. `/경로`는 전체 파일 버전, `^[/경로:줄-줄]`은 인용 줄 버전에 묶인다. 계속 추가되는 JSONL 세션은 반드시 줄 인용을 쓴다. 외부 URL의 내용 버전은 자동 확인하지 않으므로 로컬 Clippings 등 읽은 사본을 근거로 둔다.

특정 연결만 허용할 때 카드에 다음 필드를 더한다. 슬러그는 위키 루트 기준 정식 경로이며 `.md`를 붙이지 않는다. 배열에 없는 연결은 반영을 막는다. 생략한 방향은 제한하지 않는다. 빈 배열은 그 방향 연결을 모두 금지한다.

```json
{
  "link_constraints": [
    {
      "target": "sources/returns-policy",
      "inbound_from": ["overviews/customer-service"],
      "outbound_to": ["overviews/customer-service"]
    }
  ]
}
```

이 검사는 선택한 변경과 기존 전체 페이지를 합친 상태에서 본문 위키링크 및 related를 비교한다. 링크 별칭·짧은 슬러그도 정식 경로로 해석한다. 일반 텍스트로 흘러간 해석이나 향후 별도 변경의 범위는 자동 감지하지 않으므로 카드·기존 사용자 결정과 별도로 대조한다.

## 준비와 검토

```bash
python3 scripts/review.py prepare batch-id topic-id --card docs/wiki/reviews/batch-id/working/topic-id/card.json --draft-dir docs/wiki/reviews/batch-id/working/topic-id/draft
python3 scripts/review.py preview batch-id topic-id
python3 scripts/review.py status batch-id
```

prepare가 전체 revision 해시와 review.md 경로를 출력한다. preview는 임시 합본에서 build_index.py와 lint.py를 자동 실행해 index·인용·링크를 검사한다. 이 구조 검사 뒤 근거·의미·범위 검토는 wiki-review가 수행한다. 정식 페이지나 index는 바꾸지 않는다. 서로 새 페이지를 참조하는 주제는 `preview batch-id topic-a topic-b`로 함께 검사한다.

사용자에게 보내는 최종 답변은 SKILL.md의 출력 계약에 따른 간결한 번호 질문 목록이다. 카드·검사 로그·상세 diff는 내부 검토 자료로 보존하고 질문에 필요한 맥락만 추린다. 실제 답을 기다리되 승인 대기를 이유로 준비·검사를 미루지 않는다.

출력 예시:

1. 현재 “모든 주문 14일”을 “2월 신규 주문만 30일, 1월 주문은 14일 유지”로 반품 정책에 반영할까요? (추천: 반영 / 수정 / 보류 / 제외)
2. 문서 A의 “출시 완료”와 회의록 B의 “출시 예정”은 같은 제품·시점의 기록인데, 어느 쪽이 맞나요?

## 사람 판단 기록

사용자의 답을 다음 response.json으로 옮긴다. 파일은 `reviews/<batch>/working/`에 둔다. 판단은 카드의 정확한 버전에만 적용한다.

```json
{
  "by": "human:owner",
  "evidence": "^[/codex-sessions/YYYY/MM/DD/rollout-example.jsonl:150]",
  "quote": "2월 신규 주문은 30일, 1월 주문은 14일로 반영해줘.",
  "judgments": [
    {"kind": "fact", "value": "2월 신규 주문은 30일"},
    {"kind": "scope", "value": "1월 주문은 기존 14일 유지"}
  ]
}
```

```bash
python3 scripts/review.py decide batch-id topic-id --revision FULL_REVISION_HASH --decision approved --response docs/wiki/reviews/batch-id/working/response.json
```

decision: approved / changes_requested / deferred / rejected. quote는 실제 사용자 메시지의 연속된 원문이어야 한다. Claude 일반·작업 중 추가 메시지와 Codex 사용자 메시지를 지원한다. 모델·도구 출력을 인용하면 실패한다. 원본 세션 파일은 위키에 복사하지 않는다. `WIKI_CLAUDE_SESSIONS_DIR`와 `WIKI_CODEX_SESSIONS_DIR`로 원본 위치를 지정할 수 있다.

“제안대로”는 사용자가 보고 답한 항목에만 매핑한다. 수정 지시가 있으면 기존 버전에 changes_requested를 기록하고 초안을 고쳐 prepare한다. 그 지시를 그대로 구현한 새 버전은 같은 사용자 발언을 근거로 approved를 기록할 수 있다. 지시에 없던 결론·연결까지 생기면 그 차이를 다시 물어야 한다. 응답 유형별 내용을 정리하는 것은 에이전트의 책임이며 스크립트가 의미 일치를 판정하지 않는다.

## 반영과 재검토

```bash
python3 scripts/review.py apply batch-id topic-id
python3 scripts/review.py status
```

apply는 최신 버전의 승인·근거·변경 전 상태를 다시 확인하고 임시 전체 lint를 통과한 뒤 반영한다. 선택한 파일 외에는 파생 index, append-only log, 반영 receipt만 쓴다. 기존 verified를 자동 승계하지 않으며 이전 검증은 verification_history에 by/at/revision/scope로 보존해야 한다. 적용된 동일 버전 재실행은 추가 쓰기를 하지 않는다.

기준이 바뀌면 오류가 해당 항목과 경로를 알려준다. 그 주제만 현재 문서에서 다시 준비해 차이를 검토한다. 다른 주제 승인은 재사용한다. 경고는 사람이 판단할 내용으로 보고하며 errors는 반영을 막는다. 소스·세션을 읽을 수 없으면 검사를 우회하지 말고 그 항목의 근거를 복원한다.

쓰기에 실패하면 이전 상태로 되돌린다. 프로세스가 중단되어 journal이 남은 경우:

```bash
python3 scripts/review.py recover
```

복구 대상에 제3의 편집 내용이 있으면 덮어쓰지 않고 중단한다. journal before/after와 현재 파일을 대조하고 사용자 작업을 보존한 뒤 재시도한다. 변경 파일·카드·판단·receipt·log·index만 선택해 커밋하고 사용자가 지정한 저장소와 공개 범위를 따른다.
