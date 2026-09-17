import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import clippings_todo as clips


class ClippingsTests(unittest.TestCase):
    def test_missing_is_failure_not_empty_success(self):
        with tempfile.TemporaryDirectory() as root, patch.object(clips, 'CLIP_DIR', Path(root) / 'missing'):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(clips.main(), 2)
            self.assertNotIn('미처리 0건', out.getvalue())
            self.assertIn('조사 불가', err.getvalue())

    def test_existing_empty_directory_succeeds(self):
        with tempfile.TemporaryDirectory() as root, patch.object(clips, 'CLIP_DIR', Path(root)), \
                patch.object(clips, 'processed', return_value=set()), patch.object(clips, 'skipped', return_value=set()), \
                patch.object(clips, 'last_sweep_days', return_value=None), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(clips.main(), 0)
            self.assertIn('미처리 0건', out.getvalue())

    def test_all_candidates_and_relative_path_identity(self):
        with tempfile.TemporaryDirectory() as root, patch.object(clips, 'CLIP_DIR', Path(root)), \
                patch.object(clips, 'processed', return_value={'a/same.md'}), \
                patch.object(clips, 'skipped', return_value={'skip.md'}):
            base = Path(root)
            for name in ['a/same.md', 'b/same.md', 'skip.md'] + [f'{i}.md' for i in range(11)]:
                file = base / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text('article')
            pending = {p.relative_to(base).as_posix() for p in clips.pending()}
            self.assertEqual(len(pending), 12)
            self.assertIn('b/same.md', pending)
            self.assertNotIn('a/same.md', pending)
            self.assertNotIn('skip.md', pending)

    def test_enumeration_permission_error_propagates(self):
        def walk(path, onerror):
            onerror(PermissionError('fixture traversal denied'))
            return iter(())
        with tempfile.TemporaryDirectory() as root, patch.object(clips, 'CLIP_DIR', Path(root)), \
                patch.object(clips.os, 'walk', side_effect=walk):
            with self.assertRaises(PermissionError):
                clips.pending()

    def test_unreadable_file_propagates(self):
        with tempfile.TemporaryDirectory() as root, patch.object(clips, 'CLIP_DIR', Path(root)):
            (Path(root) / 'a.md').write_text('article')
            with patch.object(Path, 'open', side_effect=PermissionError('fixture read denied')):
                with self.assertRaises(PermissionError):
                    clips.pending()
