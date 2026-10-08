<h1 align="center">BOAZ Wiki</h1>

<p align="center">
  <strong>Turn your docs and AI session records into a knowledge wiki you can trace back to its sources and keep up to date.</strong>
</p>

<p align="center">
  <strong>English</strong> · <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/boaz-hwang/boaz-wiki/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/boaz-hwang/boaz-wiki/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-black.svg"></a>
</p>

---

Claude Code or Codex reads your docs and AI session records and writes linked Markdown. Every claim cites its source. You judge the meaning and scope of each change proposal. Python tools check citations, links, review versions, and the apply step. You can read the finished wiki in Obsidian.

Inspired by [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format) and [OpenWiki](https://github.com/langchain-ai/openwiki). It packages a flow developed while running a real work wiki: **source check → change proposal → human decision → apply the approved version**.

## Getting started

You need Python 3.11 or later, Git, and Claude Code or Codex with access to your local files. No packages beyond Python itself. Runs on macOS, Linux, and Windows PowerShell. Obsidian is optional.

```bash
git clone https://github.com/boaz-hwang/boaz-wiki.git
cd boaz-wiki
```

Open this folder in your coding agent, fill in the brackets in the prompt below, and paste it. Your docs can live in another folder. If you have no sessions, memory, or Git history, write `none`.

### Copyable start prompt

```text
I want to build an LLM wiki about [project or work name].

Use OpenWiki and Open Knowledge Format as references, and follow this
repository's README, AGENTS, SCHEMA, and skills.

- Docs and project paths: [...]
- Related sessions and memory: [location, or check with me]
- Obsidian vault: [path, or check with me]
- Material to exclude: [none, or the scope]

First, look at the current repo, docs, and vault structure. Analyze the docs in
the given scope, related sessions, memory, and Git history as sources, and build
a wiki that links concepts, entities, and questions. Keep the original text and
its sources, and separate facts, interpretations, plans, and results.

Organize the wiki under docs to fit the existing structure, and connect it so
that I (in Obsidian) and the agent read and edit the same Markdown. Preserve
existing docs, settings, and my edits.

Record what you investigated and what remains unverified, and show me the
reviewed change proposals and the points I need to decide, all at once. Apply
them according to my decisions, and set things up so that I can update, review,
and query the wiki with this repository's skills from then on.
```

This prompt keeps the order of my actual first request: "whole project → analyze sessions, memory, and commits as sources → organize under docs → connect to Obsidian". On top of that it adds exploring the repo and vault to fit the current structure, a way of working where you and the agent edit the same files, input fields for source paths, the review and apply steps, and hand-off to the follow-up skills.

<details>
<summary>The original prompt it started from (Korean)</summary>

```text
이 프로젝트에 관해 llm wiki 를 만들거야

openwiki 와 open knowledge format 참고해줘.

앱에 관련된 모든 내용에 대해 정리할건데, 클로드코드 세션 전체 분석해서 또한 claude mem 기록 분석해서, 그리고 github commit 이력 분석해서 source 로 여기고 llm wiki 를 만들어줘.

폴더구조는 docs 하위에 정리해주고, 이걸 obsidian 에서 확인할 수 있도록 app/wiki 폴더를 새로만들어서 연결해줘.
```

Roughly: "I'm going to build an LLM wiki for this project. Refer to openwiki and open knowledge format. Cover everything about the app: analyze all Claude Code sessions, the claude-mem records, and the GitHub commit history, treat them as sources, and build the LLM wiki. Put the folder structure under docs, and create a new app/wiki folder linked to it so I can view it in Obsidian."

</details>

## After the first build

| What you want | Example request | Skill |
|---|---|---|
| Bring everything up to date | "Compare docs and sessions since the last review and update the wiki." | [wiki-update](skills/wiki-update/SKILL.md) |
| Add specific material | "Link this meeting note into the existing wiki." | [wiki-ingest](skills/wiki-ingest/SKILL.md) |
| Review, revise, apply | "Apply proposals 1 and 2, and revise 3 with this wording." | [wiki-review](skills/wiki-review/SKILL.md) |
| Answers with evidence | "Based on the wiki, tell me why we made this decision." | [wiki-query](skills/wiki-query/SKILL.md) |

Setup installs the 4 skills into the project's `.claude/skills/` and `.agents/skills/`. On Windows it copies the files; on macOS and Linux it links them with symlinks. Running setup again refreshes managed copies you have not modified, and keeps skills you edited and any existing entries. If the current session does not pick them up right away, ask the agent to read the matching `skills/<name>/SKILL.md`, or reopen the session.

## What it leaves behind

```text
docs/wiki/
  SCHEMA.md                 operating rules for this wiki
  index.md                  auto-generated table of contents
  log.md                    history of work and applied changes
  concepts/ entities/       concepts and central entities
  sources/                  summaries of originals, with sources
  overviews/ questions/     explanations and answers that link several sources
  research/                 per-project research judgments
  reviews/                  before/after, user decisions, and apply records
```

Investigation scope goes in `inventory.json`, user decisions in `decisions.jsonl`, and actual applies in `applied.jsonl`. Approval is kept separate from fact verification of a page (`verified`). After a partial apply, you can pick up unreviewed material and deferred decisions where you left off.

Tools and templates live in `scripts/`, `skills/`, and `templates/`. [SCHEMA.md](SCHEMA.md) holds the shared rules. The agent reads the [execution format](skills/wiki-review/references/workflow.md) when it needs it.

## Editing together in Obsidian

Open `docs/wiki` as a vault, or link the same folder from an existing vault. If you already have a wiki, keep it where it is and point to it in the settings. Internal links in wiki pages use Obsidian wikilinks. Citations of the form `^[/alias/file:line]` are resolved by the agent and the check tools; they are not Obsidian's built-in jump-to-line links. Add a Markdown link that opens the original when you need one.

Your edits are read again in the next run. If a page changes after a review proposal was prepared, the tools block applying that version, so the agent re-checks against the latest text. If you edited a page whose facts were already verified, check its verification history with review as well. Review copies are kept as `.md.txt`; you can exclude them from Obsidian search with `-path:reviews`.

## Configuration and support scope

Setup creates `wiki.toml` from `wiki.example.toml`. Register each source with its path and kind. Relative paths are resolved from the config file's location. Select another workspace with `WIKI_CONFIG=/path/to/wiki.toml`. The wiki lives under that workspace.

- **Docs:** file/line citations for Markdown and MDX. For other documents, the original location is recorded and the document is first converted to readable text.
- **Sessions:** roles and original line numbers in Claude Code and Codex JSONL, and verification of actual user replies. Even when you start from docs only with no past sessions, approval records link to the session of the current review conversation.
- **Memory, Git, other agents:** the agent cross-checks anything it can read. No dedicated automatic connectors are provided; evidence is confirmed against original documents and user statements.
- **Source scope:** include/exclude and project filters are investigation instructions for the agent. They are not a sandbox that enforces file access.

The Python tools do not call an LLM. Writing content and reviewing meaning are done by the agent you use, and a check that a file exists does not prove its content is correct. The current format is this project's Markdown convention; it does not claim full OKF compatibility.

Local `wiki.toml` and the generated `docs/wiki/` are excluded by default so they are not committed to the public tool repository. Original sessions are linked from outside the tool repository, not copied. If you want to keep your knowledge in Git, decide its visibility first and store it in a separate private repository. To re-verify originals on another computer, you also need to connect the source paths there.

### Windows PowerShell

Use the clone command and start prompt above as they are. Install the agent and Python on Windows. To prepare a workspace yourself, run these from the repository folder.

```powershell
python -B scripts/setup.py
python -B scripts/lint.py
python -B scripts/review.py status
```

Run the `python3` commands in these docs as `python` in PowerShell. If you use the Python Launcher, `py -3` also works. Installing skills does not need administrator rights.

To build a wiki for another project, set the config path first.

```powershell
$env:WIKI_CONFIG = 'C:\Projects\My Project\wiki.toml'
python -B scripts/setup.py
```

Write Windows paths in `wiki.toml` with single quotes, like `path = 'C:\Users\me\Documents'`, or as `C:/Users/me/Documents`. Save settings, docs, and JSON as UTF-8. In Obsidian, open the generated wiki folder as a vault to edit the same files together. You can also create the wiki under an existing vault.

## Example and checks

Practice a first build and a policy change with the [fictional returns policy example](examples/README.md) (written in Korean).

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py'
python3 -B scripts/lint.py
python3 -B scripts/review.py status
```

The first command runs checks on fictional data in a temporary workspace. The other two check and query your current wiki after setup. preview/apply runs the structure checks automatically, verifies the change version, evidence, approval, and link scope, and rolls back on failure.

## Inspiration and license

- [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format): inspired the idea of managing human-readable Markdown together with source, generation, and verification metadata.
- [OpenWiki](https://github.com/langchain-ai/openwiki): inspired the flow of an agent organizing sources into linked knowledge and keeping it updated.

This project is a separate implementation developed from running a real wiki at AX BOAZ. It contains no code from either project and no real work material. The code, skills, docs, and fictional examples in this repository are provided under the [MIT License](LICENSE).
