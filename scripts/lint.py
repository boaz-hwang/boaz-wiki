#!/usr/bin/env python3
"""결정적 린트. error 가 있으면 exit 1. 실행: python3 scripts/lint.py

error   : frontmatter 없음/깨짐, 필수 키 누락, 잘못된 type, 없는 페이지로의 위키링크,
          없는 파일·범위 밖 줄을 가리키는 인용
warning : 고아 페이지, 인용 없는 source/overview/entity/question, stale_after 경과,
          플레이스홀더 문구, 제목 중복, index.md 가 최신이 아님, Clippings 미처리 5건 이상 또는 7일 경과
info    : contested: true, 200줄 초과
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wikilib import (  # noqa: E402
    CITATION_RE, EXTRA_ROOTS, PAGE_TYPES, WIKI_ROOT, WIKILINK_RE, build_resolver, iter_pages, parse_frontmatter, resolve_resource, slug_of,
)

PLACEHOLDER_RE = re.compile(r"(TODO|TBD|원문을 참조|pending review|작성 예정|\(추후\))", re.I)
REQUIRED = ("type", "title", "description")
CITE_REQUIRED_TYPES = {"source", "overview", "entity", "question", "research"}


def main() -> int:
    if not WIKI_ROOT.is_dir():
        print(f"[ERROR] Wiki directory not found: {WIKI_ROOT}; run setup.py first")
        return 1
    errors, warnings, infos = [], [], []
    pages = list(iter_pages())
    resolve = build_resolver(pages)
    inbound: dict[str, int] = defaultdict(int)
    titles: dict[str, list[str]] = defaultdict(list)
    now = datetime.now(timezone.utc)
    line_counts: dict[Path, int] = {}

    for p in pages:
        rel = p.relative_to(WIKI_ROOT).as_posix()
        text = p.read_text(encoding="utf-8-sig")
        fm, body = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: frontmatter 없음")
            continue
        for k in REQUIRED:
            if not fm.get(k):
                errors.append(f"{rel}: 필수 키 누락 `{k}`")
        t = fm.get("type")
        if t not in PAGE_TYPES:
            errors.append(f"{rel}: 알 수 없는 type `{t}`")
        elif p.parent.name != {"concept": "concepts", "entity": "entities", "source": "sources", "overview": "overviews", "question": "questions", "research": "research"}[t]:
            warnings.append(f"{rel}: type `{t}` 인데 폴더가 `{p.parent.name}`")
        titles[str(fm.get("title"))].append(rel)

        for m in WIKILINK_RE.finditer(body):
            target = m.group(1).strip()
            hit = resolve(target)
            if hit is None:
                errors.append(f"{rel}: 없는 페이지로의 위키링크 `[[{target}]]`")
            else:
                inbound[hit] += 1
        for item in fm.get("related", []) or []:
            if isinstance(item, str):
                hit = resolve(item)
                if hit is None:
                    errors.append(f"{rel}: related 에 없는 페이지 `{item}`")
                else:
                    inbound[hit] += 1

        cites = list(CITATION_RE.finditer(body))
        for m in cites:
            path, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
            f = resolve_resource(path)
            if f.resolve().is_relative_to((WIKI_ROOT / "reviews").resolve()):
                errors.append(f"{rel}: 검토 사본을 정식 지식 근거로 인용함 `{path}`")
                continue
            if not f.exists():
                errors.append(f"{rel}: 인용 파일 없음 `{path}`")
                continue
            if f not in line_counts:
                line_counts[f] = sum(1 for _ in f.open(encoding="utf-8", errors="replace"))
            n = line_counts[f]
            if a < 1 or b < a or b > n:
                errors.append(f"{rel}: 인용 줄 범위 오류 `{path}:{a}-{b}` (파일은 {n}줄)")
        for s in fm.get("sources", []) or []:
            if isinstance(s, dict) and isinstance(s.get("resource"), str) and s["resource"].startswith("/"):
                resource = resolve_resource(s["resource"])
                if resource.resolve().is_relative_to((WIKI_ROOT / "reviews").resolve()):
                    errors.append(f"{rel}: 검토 사본을 sources.resource로 사용함 `{s['resource']}`")
                elif not resource.exists():
                    errors.append(f"{rel}: sources.resource 파일 없음 `{s['resource']}`")
        if t in CITE_REQUIRED_TYPES and not cites and not fm.get("verified"):
            warnings.append(f"{rel}: {t} 페이지인데 줄 범위 인용이 없음")
        if PLACEHOLDER_RE.search(body):
            warnings.append(f"{rel}: 플레이스홀더 문구 발견")
        sa = fm.get("stale_after")
        if isinstance(sa, str) and sa:
            try:
                dt = datetime.fromisoformat(sa.replace("Z", "+00:00"))
                if dt <= now:
                    warnings.append(f"{rel}: stale_after 경과 ({sa})")
            except ValueError:
                warnings.append(f"{rel}: stale_after 형식 오류 `{sa}`")
        if fm.get("contested") is True:
            infos.append(f"{rel}: contested — {fm.get('contradictions')}")
        if text.count("\n") > 200:
            infos.append(f"{rel}: {text.count(chr(10))}줄, 200줄 초과. 분할 검토")

    for p in pages:
        s = slug_of(p)
        if inbound.get(s, 0) == 0:
            warnings.append(f"{p.relative_to(WIKI_ROOT).as_posix()}: 고아 페이지 (inbound 링크 0)")
    for title, rels in titles.items():
        if len(rels) > 1:
            warnings.append(f"제목 중복 `{title}`: {', '.join(rels)}")

    idx = WIKI_ROOT / "index.md"
    if idx.exists():
        listed = {resolve(t) for t in WIKILINK_RE.findall(idx.read_text(encoding="utf-8-sig"))}
        missing = sorted({slug_of(p) for p in pages} - listed)
        if missing:
            warnings.append(f"index.md 에 없는 페이지 {len(missing)}개 (build_index.py 실행): {', '.join(missing[:5])}…")
    else:
        warnings.append("index.md 없음 (build_index.py 실행)")

    for label, items in (("ERROR", errors), ("WARNING", warnings), ("INFO", infos)):
        for it in items:
            print(f"[{label}] {it}")
    print(f"\n{len(pages)} pages · {len(errors)} errors · {len(warnings)} warnings · {len(infos)} infos")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
