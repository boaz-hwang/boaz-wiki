# BOAZ Wiki

내 문서와 AI 작업 기록을, 출처를 따라 확인하고 계속 갱신할 수 있는 지식 위키로 만듭니다.

Claude Code나 Codex가 자료를 읽고 연결된 Markdown을 작성합니다. 사용자는 변경안의 의미와 범위를 판단하고, Python 도구는 인용·링크·검토 버전과 반영을 검사합니다. 만들어진 위키는 Obsidian에서 읽을 수 있습니다.

[Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format)과 [OpenWiki](https://github.com/langchain-ai/openwiki)에서 영감을 받았습니다. 실제 업무 위키를 운영하며 발전시킨 **원천 대조 → 변경안 → 사람 판단 → 승인 버전 반영** 흐름을 담았습니다.

## 시작하기

Python 3.11 이상, Git, 로컬 파일을 읽을 수 있는 Claude Code 또는 Codex가 필요합니다. Python 외 별도 패키지는 필요 없습니다. 실행 도구는 macOS·Linux를 대상으로 하며 Windows에서는 WSL을 사용합니다. Obsidian은 선택입니다.

```bash
git clone https://github.com/boaz-hwang/boaz-wiki.git
cd boaz-wiki
```

이 폴더를 코딩 에이전트에서 열고, 아래 프롬프트의 대괄호를 바꿔 붙여넣으세요. 문서는 다른 폴더에 있어도 됩니다. 세션·메모리·Git 이력이 없으면 `없음`이라고 적으면 됩니다.

### 복사해서 시작하는 프롬프트

```text
[프로젝트/업무 이름]에 관해 LLM wiki를 만들 거야.

OpenWiki와 Open Knowledge Format을 참고하고, 이 저장소의 README·AGENTS·SCHEMA와
스킬에 따라 진행해줘.

- 문서·프로젝트 경로: [...]
- 관련 세션·메모리: [위치 또는 함께 확인]
- Obsidian Vault: [경로 또는 함께 확인]
- 제외할 자료: [없음 또는 범위]

먼저 현재 레포·문서·Vault 구조를 살펴봐줘. 지정한 범위의 문서와 관련 세션,
메모리, Git 이력을 source로 분석해서 개념·대상·질문이 연결된 위키를 만들어줘.
원문과 출처를 보존하고, 사실·해석·계획·실행 결과를 구분해줘.

위키는 기존 구조에 맞춰 docs 아래에 정리하고, Obsidian에서 나와 에이전트가
같은 Markdown을 읽고 수정하도록 연결해줘. 기존 문서·설정·내 편집을 보존해줘.

조사 범위와 미확인을 기록하고, 검토한 변경안과 내가 판단할 내용을 한 번에
보여줘. 내 결정에 따라 반영하고, 이후에는 이 저장소의 스킬로 갱신·검토·질문할
수 있도록 준비해줘.
```

이 프롬프트는 실제 첫 요청의 “프로젝트 전체 → 세션·메모리·커밋을 source로 분석 → docs 아래 정리 → Obsidian 연결” 순서를 유지했습니다. 현재 구조에 맞춰 레포·Vault 탐색, 같은 파일을 함께 수정하는 협업 방식, 원천 경로 입력, 검토·반영 절차와 후속 스킬 연결을 더했습니다.

<details>
<summary>출발점이 된 원문 프롬프트</summary>

```text
이 프로젝트에 관해 llm wiki 를 만들거야

openwiki 와 open knowledge format 참고해줘.

앱에 관련된 모든 내용에 대해 정리할건데, 클로드코드 세션 전체 분석해서 또한 claude mem 기록 분석해서, 그리고 github commit 이력 분석해서 source 로 여기고 llm wiki 를 만들어줘.

폴더구조는 docs 하위에 정리해주고, 이걸 obsidian 에서 확인할 수 있도록 app/wiki 폴더를 새로만들어서 연결해줘.
```

</details>

## 만든 다음에는

| 원하는 일 | 요청 예 | 스킬 |
|---|---|---|
| 전체 최신화 | “지난 검토 이후 문서와 세션을 대조해 위키 업데이트해줘.” | [wiki-update](skills/wiki-update/SKILL.md) |
| 특정 자료 추가 | “이 회의록을 기존 위키에 연결해줘.” | [wiki-ingest](skills/wiki-ingest/SKILL.md) |
| 검토·수정·반영 | “변경안 1·2는 반영하고, 3은 이 표현으로 수정해줘.” | [wiki-review](skills/wiki-review/SKILL.md) |
| 근거 있는 답변 | “위키 기준으로 이 결정을 왜 했는지 알려줘.” | [wiki-query](skills/wiki-query/SKILL.md) |

setup은 프로젝트의 `.claude/skills/`와 `.agents/skills/`에 4개 스킬을 연결합니다. 기존 항목은 보존합니다. 현재 세션에서 바로 발견되지 않으면 해당 `skills/<이름>/SKILL.md`를 읽으라고 요청하거나 세션을 다시 여세요.

## 무엇을 남기나

```text
docs/wiki/
  SCHEMA.md                 이 위키의 운영 규칙
  index.md                  자동 생성 목차
  log.md                    작업·반영 이력
  concepts/ entities/       개념과 중심 대상
  sources/                  원문 요약과 출처
  overviews/ questions/     여러 자료를 연결한 설명과 답
  research/                 프로젝트별 연구 판단
  reviews/                  변경 전후·사용자 판단·반영 기록
```

조사 범위는 `inventory.json`, 사용자 판단은 `decisions.jsonl`, 실제 반영은 `applied.jsonl`에 남깁니다. 승인과 페이지의 사실 검증(`verified`)은 구분합니다. 부분 반영 뒤에도 미검토 자료와 보류한 판단을 이어갈 수 있습니다.

도구와 양식은 `scripts/`, `skills/`, `templates/`에 있고, [SCHEMA.md](SCHEMA.md)가 공통 규칙입니다. [실행 형식](skills/wiki-review/references/workflow.md)은 에이전트가 필요할 때 읽습니다.

## Obsidian에서 함께 편집하기

`docs/wiki`를 Vault로 열거나 기존 Vault에서 같은 폴더를 연결합니다. 기존 위키가 있으면 그 위치를 유지하고 설정으로 연결할 수 있습니다. 위키 본문의 내부 링크는 Obsidian 위키링크를 사용합니다. `^[/별칭/파일:줄]` 인용은 에이전트와 검사 도구가 해석하며, Obsidian 기본 기능의 줄 이동 링크는 아닙니다. 필요하면 원문을 여는 Markdown 링크를 함께 붙입니다.

사람의 편집은 다음 작업에서 다시 읽습니다. 검토안 준비 이후 본문이 바뀌면 도구가 해당 버전의 반영을 막으므로 최신 본문에서 다시 대조합니다. 사실 검증을 마친 페이지를 직접 수정했다면 검증 이력도 review로 확인하세요. 검토 사본은 `.md.txt`로 보존하며 Obsidian 검색에서 `-path:reviews`로 제외할 수 있습니다.

## 설정과 지원 범위

`wiki.example.toml`을 기반으로 setup이 `wiki.toml`을 만듭니다. 원천별 경로와 종류를 등록하며, 상대 경로는 설정 파일 위치 기준입니다. 다른 작업 공간은 `WIKI_CONFIG=/path/to/wiki.toml`로 선택할 수 있습니다. 위키는 해당 작업 공간 아래에 둡니다.

- **문서:** Markdown·MDX의 파일/줄 인용. 다른 문서는 원문 위치를 기록하고 먼저 읽을 수 있는 텍스트로 변환합니다.
- **세션:** Claude Code·Codex JSONL의 역할·원본 줄과 실제 사용자 응답 검증. 과거 세션 없이 문서만 시작할 때도, 승인 기록에는 현재 검토 대화의 세션을 연결합니다.
- **메모리·Git·기타 에이전트:** 에이전트가 읽기 가능한 자료를 대조합니다. 자동 전용 연결은 제공하지 않으며 원본 문서·사용자 발언으로 근거를 확인합니다.
- **원천 범위:** include/exclude·프로젝트 필터는 에이전트의 조사 지침입니다. 파일 접근 권한을 강제하는 샌드박스가 아닙니다.

Python 도구는 LLM을 호출하지 않습니다. 내용 작성과 의미 검토는 사용 중인 에이전트가 수행하며, 파일이 존재한다는 검사만으로 내용의 정확성이 증명되지는 않습니다. 현재 형식은 이 프로젝트의 Markdown 규칙이며 OKF 전체 호환성을 주장하지 않습니다.

로컬 `wiki.toml`, 생성된 `docs/wiki/`는 공개 도구 저장소에 커밋하지 않도록 기본 제외합니다. 원본 세션은 도구 저장소 밖에서 연결하며 복사하지 않습니다. 지식을 Git으로 보관하려면 공개 범위를 먼저 정하고 별도 비공개 저장소에 저장하세요. 다른 컴퓨터에서 원문을 재검증하려면 원천 경로도 연결해야 합니다.

## 예제와 검증

[가상 반품 정책 예제](examples/README.md)로 첫 생성과 정책 변경을 연습할 수 있습니다.

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py'
python3 -B scripts/lint.py
python3 -B scripts/review.py status
```

첫 명령은 임시 작업 공간의 가상 데이터로 검사합니다. 나머지 두 명령은 setup 이후 현재 위키를 검사·조회합니다. preview/apply는 구조 검사를 자동 실행하며 변경 버전·근거·승인·링크 범위를 확인하고 실패 시 복구합니다.

## 영감과 라이선스

- [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format): 사람이 읽는 Markdown과 출처·생성·검증 메타데이터를 함께 관리하는 방향에서 영감을 받았습니다.
- [OpenWiki](https://github.com/langchain-ai/openwiki): 에이전트가 원천을 연결된 지식으로 정리하고 갱신하는 흐름에서 영감을 받았습니다.

이 프로젝트는 AX BOAZ의 실제 위키 운영에서 발전시킨 별도 구현입니다. 두 프로젝트의 코드나 실제 업무 자료를 포함하지 않습니다. 이 저장소의 코드·스킬·문서·가상 예제는 [MIT License](LICENSE)로 제공합니다.
