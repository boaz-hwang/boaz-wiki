#!/usr/bin/env python3
"""docs/wiki/index.md 를 frontmatter 에서 생성한다. 손으로 편집하지 않는다. 실행: python3 scripts/build_index.py"""
from __future__ import annotations

import sys
from collections import defaultdict
from settings import TITLE
from datetime import datetime, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from wikilib import WIKI_ROOT, iter_pages, parse_frontmatter, slug_of  # noqa: E402

ORDER = [
    ("overview", "개요 (overviews)"),
    ("question", "질문 (questions)"),
    ("concept", "개념 (concepts)"),
    ("entity", "고객사·프로그램·도구 (entities)"),
    ("research", "연구 (research)"),
    ("source", "원문 요약 (sources)"),
]


def main() -> int:
    groups: dict[str, list[tuple[str, str, str, dict]]] = defaultdict(list)
    for p in iter_pages():
        fm, _ = parse_frontmatter(p.read_text(encoding="utf-8-sig"))
        if not fm:
            continue
        groups[str(fm.get("type", "?"))].append((str(fm.get("title", p.stem)), slug_of(p), str(fm.get("description", "")), fm))
    total = sum(len(v) for v in groups.values())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = [
        "---",
        'wiki_format: "1"',
        f"generated: {{ by: process:build_index.py, at: {now} }}",
        "---",
        "",
        f"# {TITLE}",
        "",
        f"페이지 {total}개. 이 파일은 `scripts/build_index.py`가 생성한다. 규칙은 [[SCHEMA]] 참고, 작업 기록은 [[log]].",
        "",
    ]
    for t, label in ORDER:
        items = groups.get(t, [])
        if not items:
            continue
        out.append(f"## {label} · {len(items)}")
        out.append("")
        for title, slug, desc, fm in sorted(items, key=lambda x: x[0]):
            flags = []
            if fm.get("status") == "deprecated":
                flags.append("deprecated")
            if fm.get("contested") is True:
                flags.append("contested")
            if fm.get("status") == "draft":
                flags.append("draft")
            flag = f" `{' · '.join(flags)}`" if flags else ""
            out.append(f"- [[{slug}|{title}]]{flag} — {desc}")
        out.append("")
    (WIKI_ROOT / "index.md").write_text("\n".join(out), encoding="utf-8")
    print(f"index.md: {total} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
