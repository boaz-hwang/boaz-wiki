"""Link skills, or maintain copies when directory symlinks are unavailable."""
import hashlib
import json
import os
import shutil

MARKER = '.boaz-wiki-copy.json'


def snapshot(folder):
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob('*'))
        if p.is_file() and p.name != MARKER
    }


def install_skill(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        if dest.resolve() != source.resolve():
            print(f'Existing skill preserved: {dest}')
        return
    if dest.exists():
        marker = dest / MARKER
        try:
            previous = json.loads(marker.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            previous = None
        if previous is None or snapshot(dest) != previous:
            print(f'Existing skill preserved: {dest}')
            return
        # Only overwrite a complete, unchanged managed copy.
        shutil.rmtree(dest)
    if os.name != 'nt':
        try:
            dest.symlink_to(os.path.relpath(source, dest.parent), target_is_directory=True)
            return
        except OSError:
            pass
    shutil.copytree(source, dest)
    (dest / MARKER).write_text(json.dumps(snapshot(dest)), encoding='utf-8')
