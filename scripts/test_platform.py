"""Native lock exclusion and skill copies without symlink privileges."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from platform_io import file_lock
from skill_install import install_skill


class PlatformTests(unittest.TestCase):
    def test_lock_excludes_other_process_and_releases_on_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / '.lock'
            child = None
            try:
                with file_lock(lock):
                    code = (
                        'from pathlib import Path; from platform_io import file_lock; '
                        'import sys; print("ready", flush=True); '
                        '\nwith file_lock(Path(sys.argv[1])): print("acquired", flush=True)'
                    )
                    child = subprocess.Popen(
                        [sys.executable, '-B', '-c', code, str(lock)],
                        cwd=Path(__file__).parent, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True, encoding='utf-8')
                    self.assertEqual(child.stdout.readline().strip(), 'ready')
                    time.sleep(0.2)
                    self.assertIsNone(child.poll())
                    raise ValueError('release on failure')
            except ValueError:
                pass
            finally:
                if child:
                    try:
                        out, err = child.communicate(timeout=15)
                        self.assertEqual(child.returncode, 0, err)
                        self.assertEqual(out.strip(), 'acquired')
                    finally:
                        if child.poll() is None:
                            child.kill()
                            child.communicate()

    def test_copy_fallback_refreshes_and_preserves_user_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root/'source', root/'installed'
            source.mkdir()
            (source/'SKILL.md').write_text('first', encoding='utf-8')
            with patch.object(Path, 'symlink_to', side_effect=OSError('no privilege')):
                install_skill(source, dest)
                self.assertEqual((dest/'SKILL.md').read_text(encoding='utf-8'), 'first')
                (source/'SKILL.md').write_text('updated', encoding='utf-8')
                install_skill(source, dest)
                self.assertEqual((dest/'SKILL.md').read_text(encoding='utf-8'), 'updated')
                (dest/'SKILL.md').write_text('human edit', encoding='utf-8')
                install_skill(source, dest)
                self.assertEqual((dest/'SKILL.md').read_text(encoding='utf-8'), 'human edit')

    def test_existing_unmanaged_skill_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root/'source', root/'installed'
            source.mkdir()
            dest.mkdir()
            (dest/'SKILL.md').write_text('existing', encoding='utf-8')
            install_skill(source, dest)
            self.assertEqual((dest/'SKILL.md').read_text(encoding='utf-8'), 'existing')
