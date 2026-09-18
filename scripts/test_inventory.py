import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

import inventory


def record():
    return {'version': 1, 'period': {'from': '2026-09-01T00:00:00+09:00', 'through': '2026-09-16T00:00:00+09:00'},
            'basis': {'last_apply': 'log.md: partial client update', 'last_full_review': 'unknown; reviewed from initial wiki creation'},
            'sources': [{'id': kind, 'kind': kind, 'location': '/fixture/' + kind, 'status': 'scanned',
                         'reason': 'enumerated and compared all period records; no candidates', 'items': []}
                        for kind in sorted(inventory.REQUIRED)]}


class InventoryTests(unittest.TestCase):
    def test_empty_successful_scan_has_boundary(self):
        data = record()
        self.assertEqual(inventory.validate(data)['through'], data['period']['through'])

    def test_unavailable_and_partial_have_no_boundary(self):
        for status in ('partial', 'unavailable'):
            data = record()
            data['sources'][0]['status'] = status
            result = inventory.validate(data)
            self.assertFalse(result['complete'])
            self.assertIsNone(result['through'])

    def test_unread_blocks_even_scanned_source(self):
        data = record()
        data['sources'][0]['items'] = [{'id': 'a', 'reference': '/a', 'status': 'unread', 'reason': 'cannot read'}]
        self.assertFalse(inventory.validate(data)['complete'])

    def test_reviewed_requires_comparison_and_classification(self):
        data = record()
        item = {'id': 'a', 'reference': '/a', 'status': 'reviewed', 'reason': 'already ingested',
                'classification': 'duplicate', 'comparison': 'sources/a'}
        data['sources'][0]['items'] = [item]
        self.assertTrue(inventory.validate(data)['complete'])
        for key in ('classification', 'comparison'):
            broken = copy.deepcopy(data)
            del broken['sources'][0]['items'][0][key]
            with self.assertRaises(ValueError):
                inventory.validate(broken)

    def test_missing_provider_and_duplicate_source_rejected(self):
        data = record()
        data['sources'].pop()
        with self.assertRaises(ValueError):
            inventory.validate(data)
        data = record()
        data['sources'].append(copy.deepcopy(data['sources'][0]))
        with self.assertRaises(ValueError):
            inventory.validate(data)

    def test_configured_kind_is_required(self):
        data = record()
        required = sorted(inventory.REQUIRED)[0]
        data['sources'] = [s for s in data['sources'] if s['kind'] != required]
        with self.assertRaisesRegex(ValueError, required):
            inventory.validate(data)

    def test_invalid_period_and_legacy_not_promoted(self):
        for period in ({'from': '2026-09-17T00:00:00Z', 'through': '2026-09-16T00:00:00Z'},
                       {'from': '2026-09-01', 'through': '2026-09-16'}):
            data = record()
            data['period'] = period
            with self.assertRaises(ValueError):
                inventory.validate(data)
        with self.assertRaises(ValueError):
            inventory.validate({'complete': True, 'applied': ['client-a']})

    def test_cli_incomplete_and_invalid_exit_codes(self):
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stdout(io.StringIO()):
            path = Path(root) / 'inventory.json'
            data = record()
            data['sources'][0]['status'] = 'unavailable'
            path.write_text(json.dumps(data), encoding='utf-8')
            self.assertEqual(inventory.main([str(path), '--require-complete']), 2)
            self.assertEqual(inventory.main([str(path)]), 0)
            path.write_text('{}', encoding='utf-8')
            self.assertEqual(inventory.main([str(path)]), 1)
