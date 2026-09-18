"""wiki 공용 유틸. 표준 라이브러리만 쓴다 (PyYAML 없음).

frontmatter 파서는 이 위키가 쓰는 부분집합만 지원한다:
- `key: value` 스칼라 (따옴표 있거나 없거나)
- `key: [a, b, c]` 인라인 리스트
- `key: { a: 1, b: 2 }` 인라인 매핑 (한 단계)
- `key:` 다음 줄부터 `  - item` 블록 리스트 (스칼라 또는 `- k: v` 매핑)
"""
from __future__ import annotations

import re
import os
from pathlib import Path

from settings import WIKI_ROOT, REPO_ROOT, EXTRA_ROOTS
PAGE_TYPES = {"concept", "entity", "source", "overview", "question", "research"}


def resolve_resource(path: str) -> Path:
    """`/저장소경로` 또는 `/Clippings/파일` 을 실제 파일 경로로 바꾼다."""
    rel = path.lstrip("/")
    if ".." in Path(rel).parts:
        raise ValueError(f"Source path escapes its root: {path}")
    head, _, tail = rel.partition("/")
    prefix = os.environ.get("WIKI_RESOURCE_PREFIX")
    if head in EXTRA_ROOTS:
        root, relative = EXTRA_ROOTS[head], tail
    elif prefix and rel.startswith(prefix.rstrip("/") + "/"):
        root, relative = WIKI_ROOT, rel[len(prefix.rstrip("/")) + 1:]
    else:
        root, relative = REPO_ROOT, rel
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"Source path escapes its root: {path}")
    return target

SKIP_FILES = {"index.md", "log.md", "SCHEMA.md"}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
CITATION_RE = re.compile(r"\^\[(/[^\]:]+?):(\d+)(?:-(\d+))?\]")
FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)


def _scalar(s: str):
    s = s.strip()
    if not s:
        return ""
    if (s[0] == s[-1]) and s[0] in "\"'" and len(s) >= 2:
        return s[1:-1]
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    if s == "[]":
        return []
    if s == "{}":
        return {}
    return s


def _split_top(s: str, sep: str = ","):
    out, depth, cur, quote = [], 0, "", None
    for ch in s:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            cur += ch
        elif ch in "[{":
            depth += 1
            cur += ch
        elif ch in "]}":
            depth -= 1
            cur += ch
        elif ch == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def _inline(s: str):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_inline(x) for x in _split_top(inner)] if inner else []
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        d = {}
        for part in _split_top(inner):
            if ":" in part:
                k, v = part.split(":", 1)
                d[k.strip()] = _inline(v)
        return d
    return _scalar(s)


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    text = text.replace("\r\n", "\n")
    m = FM_RE.match(text)
    if not m:
        return None, text
    block, body = m.group(1), text[m.end():]
    lines = block.split("\n")
    data: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith(" "):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.split(" #")[0] if not rest.strip().startswith(("\"", "'")) else rest
        rest = rest.strip()
        if rest:
            data[key] = _inline(rest)
            i += 1
            continue
        # block list or nested mapping
        items = []
        j = i + 1
        cur_map = None
        while j < len(lines) and (lines[j].startswith("  ") or not lines[j].strip()):
            l = lines[j]
            if not l.strip():
                j += 1
                continue
            stripped = l.strip()
            if stripped.startswith("- "):
                content = stripped[2:].strip()
                if ":" in content and not content.startswith(("\"", "'", "[", "{")):
                    k, v = content.split(":", 1)
                    cur_map = {k.strip(): _inline(v)}
                    items.append(cur_map)
                else:
                    cur_map = None
                    items.append(_inline(content))
            elif cur_map is not None and ":" in stripped:
                k, v = stripped.split(":", 1)
                cur_map[k.strip()] = _inline(v)
            j += 1
        data[key] = items
        i = j
    return data, body


def dump_frontmatter(data: dict) -> str:
    def q(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        v = str(v)
        if v == "" or re.search(r"[:#\[\]{}\"'\n]|^\s|\s$|^[-?&*!|>%@`]", v) or v.lower() in ("true", "false", "null", "yes", "no"):
            return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return v

    out = ["---"]
    for k, v in data.items():
        if isinstance(v, list):
            if not v:
                out.append(f"{k}: []")
            elif all(isinstance(x, dict) for x in v):
                out.append(f"{k}:")
                for item in v:
                    first = True
                    for ik, iv in item.items():
                        prefix = "  - " if first else "    "
                        out.append(f"{prefix}{ik}: {q(iv)}")
                        first = False
            else:
                out.append(f"{k}: [" + ", ".join(q(x) for x in v) + "]")
        elif isinstance(v, dict):
            out.append(f"{k}: {{ " + ", ".join(f"{ik}: {q(iv)}" for ik, iv in v.items()) + " }")
        else:
            out.append(f"{k}: {q(v)}")
    out.append("---")
    return "\n".join(out) + "\n"


def iter_pages():
    for p in sorted(WIKI_ROOT.rglob("*.md")):
        parts = p.relative_to(WIKI_ROOT).parts
        if p.name in SKIP_FILES or "scripts" in parts or "reviews" in parts:
            continue
        yield p


def slug_of(p: Path) -> str:
    return p.relative_to(WIKI_ROOT).with_suffix("").as_posix()


def build_resolver(pages):
    """Obsidian 과 같은 순서로 위키링크를 해석한다.
    1) wiki 루트 기준 정확한 경로  2) `wiki/` 접두 제거 후 경로  3) 고유한 basename  4) 고유한 경로 suffix.
    성공하면 slug, 실패하면 None 을 돌려준다."""
    slugs = {slug_of(p) for p in pages} | {"index", "log", "SCHEMA"}
    by_base: dict[str, list[str]] = {}
    for s in slugs:
        by_base.setdefault(s.rsplit("/", 1)[-1], []).append(s)

    def resolve(target: str):
        t = target.strip()
        if t.endswith(".md"):
            t = t[:-3]
        if t in slugs:
            return t
        if t.startswith("wiki/") and t[5:] in slugs:
            return t[5:]
        if "/" not in t:
            c = by_base.get(t, [])
            return c[0] if len(c) == 1 else None
        c = [s for s in slugs if s.endswith("/" + t) or s == t]
        return c[0] if len(c) == 1 else None

    return resolve
