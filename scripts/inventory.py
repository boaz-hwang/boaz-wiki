#!/usr/bin/env python3
"""Validate declared review coverage; does not discover sources or prove semantic review."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from settings import REQUIRED_KINDS, REQUIRED_SOURCES, SOURCES
REQUIRED = REQUIRED_KINDS
CLASSIFICATIONS = {'new', 'update', 'conflict', 'duplicate', 'out_of_scope'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def timestamp(value):
    require(nonempty(value), 'period timestamps required')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(dt.tzinfo is not None, 'period timestamps need timezone')
    return dt


def validate(data):
    require(isinstance(data, dict) and data.get('version') == 1, 'inventory version must be 1')
    period = data.get('period', {})
    require(isinstance(period, dict), 'period must be an object')
    start, end = timestamp(period.get('from')), timestamp(period.get('through'))
    require(start <= end, 'period.from must not follow through')
    basis = data.get('basis', {})
    require(isinstance(basis, dict), 'basis must be an object')
    require(all(nonempty(basis.get(k)) for k in ('last_apply', 'last_full_review')), 'both boundary evidence notes required; unknown must be explicit')
    sources = data.get('sources')
    require(isinstance(sources, list), 'sources must be a list')
    kinds, ids, incomplete = set(), set(), []
    for source in sources:
        require(isinstance(source, dict), 'source must be an object')
        sid = source.get('id')
        require(nonempty(sid) and sid not in ids, 'source id missing or duplicated')
        ids.add(sid)
        require(all(nonempty(source.get(k)) for k in ('kind', 'location', 'reason')), f'{sid}: kind/location/reason required')
        if sid in REQUIRED_SOURCES:
            require(source['kind'] == SOURCES[sid]['kind'], f'{sid}: configured source kind mismatch')
        kinds.add(source['kind'])
        status = source.get('status')
        require(status in {'scanned', 'partial', 'unavailable', 'not_applicable'}, f'{sid}: invalid status')
        items = source.get('items')
        require(isinstance(items, list), f'{sid}: items must be a list')
        require(status != 'not_applicable' or not items, f'{sid}: not_applicable cannot contain items')
        if status in {'partial', 'unavailable'}:
            incomplete.append(sid)
        item_ids = set()
        for item in items:
            require(isinstance(item, dict), f'{sid}: item must be an object')
            iid = item.get('id')
            require(nonempty(iid) and iid not in item_ids, f'{sid}: item id missing or duplicated')
            item_ids.add(iid)
            require(all(nonempty(item.get(k)) for k in ('reference', 'reason')), f'{sid}/{iid}: reference/reason required')
            require(item.get('status') in {'reviewed', 'unread'}, f'{sid}/{iid}: invalid status')
            if item['status'] == 'unread':
                incomplete.append(f'{sid}/{iid}')
            else:
                require(item.get('classification') in CLASSIFICATIONS, f'{sid}/{iid}: classification required')
                require(nonempty(item.get('comparison')), f'{sid}/{iid}: existing-wiki comparison required')
    require(REQUIRED_SOURCES <= ids, f'missing configured sources: {sorted(REQUIRED_SOURCES - ids)}')
    require(REQUIRED <= kinds, f'missing source kinds: {sorted(REQUIRED - kinds)}')
    return {'complete': not incomplete, 'through': period['through'] if not incomplete else None, 'incomplete': incomplete}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = validate(json.loads(args.path.read_text(encoding='utf-8-sig')))
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 2 if args.require_complete and not result['complete'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
