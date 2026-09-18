#!/usr/bin/env python3
"""아직 위키에 정리하지 않은 Clippings 목록 (오래된 것부터).

처리됨 = 어떤 sources/ 페이지의 sources.resource 가 `/Clippings/<파일>` 을 가리킨다.
건너뜀 = log.md 에 `clip-skip | <Clippings 기준 상대 경로>` 항목이 있다.
그 외는 미처리. 원본 클리핑 파일은 절대 수정하지 않는다.

실행: python3 scripts/clippings_todo.py [--all]
"""
from __future__ import annotations

import re
import os
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wikilib import EXTRA_ROOTS, WIKI_ROOT, iter_pages, parse_frontmatter  # noqa: E402

CLIP_DIR = EXTRA_ROOTS.get("Clippings")
SWEEP_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] clip-sweep\b", re.M)
SKIP_RE = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\] clip-skip \| ([^|\n]+?)\s*(?:\||$)", re.M)


def processed() -> set[str]:
    done = set()
    for p in iter_pages():
        fm, _ = parse_frontmatter(p.read_text(encoding="utf-8-sig"))
        for s in (fm or {}).get("sources", []) or []:
            r = s.get("resource") if isinstance(s, dict) else None
            if isinstance(r, str) and r.startswith("/Clippings/"):
                done.add(r[len("/Clippings/"):])
    return done


def skipped() -> set[str]:
    log = WIKI_ROOT / "log.md"
    if not log.exists():
        return set()
    return {m.group(1).strip() for m in SKIP_RE.finditer(log.read_text(encoding="utf-8-sig"))}


def last_sweep_days() -> int | None:
    log = WIKI_ROOT / "log.md"
    if not log.exists():
        return None
    dates = [datetime.strptime(m.group(1), "%Y-%m-%d").date() for m in SWEEP_RE.finditer(log.read_text(encoding="utf-8-sig"))]
    return (date.today() - max(dates)).days if dates else None


def pending() -> list[Path]:
    if CLIP_DIR is None:
        raise FileNotFoundError("Configure sources.Clippings in wiki.toml first")
    if not CLIP_DIR.is_dir():
        raise FileNotFoundError(f"Clippings 디렉터리 없음: {CLIP_DIR}")
    def fail(error):
        raise error
    # Path.rglob can suppress traversal errors. Incomplete enumeration is not zero work.
    candidates = []
    for directory, _, names in os.walk(CLIP_DIR, onerror=fail):
        for name in names:
            if name.endswith('.md'):
                p = Path(directory) / name
                with p.open('rb') as stream:
                    stream.read(1)
                candidates.append(p)
    done, skip = processed(), skipped()
    files = [p for p in candidates if p.relative_to(CLIP_DIR).as_posix() not in done | skip]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def main() -> int:
    show_all = "--all" in sys.argv
    try:
        todo = pending()
    except OSError as error:
        print(f"[ERROR] Clippings 조사 불가: {error}", file=sys.stderr)
        return 2
    days = last_sweep_days()
    print(f"Clippings: {CLIP_DIR}")
    print(f"미처리 {len(todo)}건 · 처리 {len(processed())}건 · 건너뜀 {len(skipped())}건 · 마지막 clip-sweep: {f'{days}일 전' if days is not None else '기록 없음'}")
    for p in todo if show_all else todo[:20]:
        fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        fm = fm or {}
        title = str(fm.get("title") or p.stem)
        src = str(fm.get("source") or "")
        saved = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
        words = len(p.read_text(encoding="utf-8", errors="replace").split())
        print(f"- [{saved}] {title}  ({words}w)  {src}\n    /Clippings/{p.relative_to(CLIP_DIR).as_posix()}")
    if not show_all and len(todo) > 20:
        print(f"... 외 {len(todo) - 20}건 (--all)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
