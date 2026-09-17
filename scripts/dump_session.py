#!/usr/bin/env python3
"""Read Claude/Codex messages with original JSONL line numbers, without truncation."""
import argparse
import json
from pathlib import Path

from wikilib import EXTRA_ROOTS, resolve_resource


def blocks(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
    return ""


def messages(record, tools=False):
    kind = record.get("type")
    if kind == "attachment":
        item = record.get("attachment", {})
        if item.get("type") == "queued_command":
            role = "user" if item.get("origin", {}).get("kind") == "human" else "queued_context"
            yield role, item.get("prompt", "")
    elif kind in ("user", "assistant"):
        content = record.get("message", {}).get("content", [])
        if isinstance(content, str):
            yield kind, content
        else:
            for item in content:
                if item.get("type") == "text":
                    yield kind, item.get("text", "")
                elif tools and item.get("type") == "tool_use":
                    yield "tool " + item.get("name", ""), json.dumps(item.get("input", {}), ensure_ascii=False)
                elif tools and item.get("type") == "tool_result":
                    yield "tool_result", blocks(item.get("content", ""))
    elif kind == "response_item":
        payload = record.get("payload", {})
        if payload.get("type") == "message" and payload.get("role") in ("user", "assistant"):
            yield payload["role"], blocks(payload.get("content", []))
        elif tools and payload.get("type") in ("function_call", "function_call_output", "custom_tool_call", "custom_tool_call_output"):
            yield payload["type"], str(payload.get("arguments", payload.get("input", payload.get("output", ""))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="local path or /claude-sessions/... or /codex-sessions/...")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    parser.add_argument("--tools", action="store_true")
    parser.add_argument("--max-chars", type=int, default=0, help="0 = full text; positive limit is for discovery only")
    args = parser.parse_args()
    if args.start < 1 or (args.end is not None and args.end < args.start) or args.max_chars < 0:
        parser.error("invalid line range or character limit")
    path = Path(args.path).expanduser()
    if args.path.lstrip("/").partition("/")[0] in EXTRA_ROOTS:
        path = resolve_resource(args.path)
    # Codex stores the same visible messages in event_msg and response_item.
    # Prefer response_item when present; older event-only logs still work.
    has_messages = False
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            p = record.get("payload", {})
            if record.get("type") == "response_item" and p.get("type") == "message" and p.get("role") in ("user", "assistant"):
                has_messages = True
                break
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if number < args.start:
                continue
            if args.end is not None and number > args.end:
                break
            record = json.loads(line)
            output = list(messages(record, args.tools))
            if not has_messages and record.get("type") == "event_msg":
                p = record.get("payload", {})
                role = {"user_message": "user", "agent_message": "assistant"}.get(p.get("type"))
                if role:
                    output.append((role, p.get("message", "")))
            for role, text in output:
                if not text.strip():
                    continue
                if args.max_chars and len(text) > args.max_chars:
                    text = text[:args.max_chars] + "\n[TRUNCATED: reread without --max-chars before citing]"
                print(f"L{number} [{role}]\n{text}\n")


if __name__ == "__main__":
    main()
