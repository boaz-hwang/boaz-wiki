"""Prepare a local wiki workspace without replacing existing files."""
from pathlib import Path
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    config = Path(os.environ.get('WIKI_CONFIG', ROOT / 'wiki.toml')).expanduser().resolve()
    config.parent.mkdir(parents=True, exist_ok=True)
    if not config.exists():
        config.write_bytes((ROOT / 'wiki.example.toml').read_bytes())
    from settings import WIKI_ROOT, REPO_ROOT, WORKSPACE
    if not WIKI_ROOT.is_relative_to(REPO_ROOT) or WIKI_ROOT == REPO_ROOT:
        raise ValueError('wiki.path must be a subdirectory of the workspace')
    WIKI_ROOT.mkdir(parents=True, exist_ok=True)
    for category in ('concepts','entities','sources','overviews','questions','research','reviews'):
        (WIKI_ROOT / category).mkdir(exist_ok=True)
    for name, text in [('SCHEMA.md', (ROOT / 'SCHEMA.md').read_text()), ('log.md', '# Wiki log\n')]:
        p = WIKI_ROOT / name
        if not p.exists(): p.write_text(text, encoding='utf-8')
    if not (WIKI_ROOT / 'index.md').exists():
        subprocess.run([sys.executable, '-B', str(ROOT/'scripts/build_index.py')], check=True)
    for provider in ('.claude', '.agents'):
        for skill in sorted((ROOT / 'skills').iterdir()):
            if not (skill / 'SKILL.md').is_file(): continue
            dest = WORKSPACE / provider / 'skills' / skill.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() or dest.is_symlink():
                if dest.resolve() != skill.resolve():
                    print(f'Existing skill preserved: {dest}')
                continue
            dest.symlink_to(os.path.relpath(skill, dest.parent), target_is_directory=True)
    if WORKSPACE != ROOT:
        pointer = f"\n<!-- boaz-wiki -->\nWiki rules: {WIKI_ROOT / 'SCHEMA.md'}. Read the index first.\nToolkit and skills: {ROOT}. Use WIKI_CONFIG={config} with its scripts.\n<!-- /boaz-wiki -->\n"
        for name in ('AGENTS.md', 'CLAUDE.md'):
            target = WORKSPACE / name
            old = target.read_text(encoding='utf-8') if target.exists() else ''
            pattern = r'\n?<!-- (?:llm|boaz)-wiki -->.*?<!-- /(?:llm|boaz)-wiki -->\n?'
            if re.search(pattern, old, flags=re.S):
                updated = re.sub(pattern, lambda _: pointer, old, count=1, flags=re.S)
            else:
                updated = old + pointer
            if updated != old:
                target.write_text(updated, encoding='utf-8')
    print(f'Workspace ready: {WIKI_ROOT}\nConfigure sources in {config}; follow the README starter prompt.')

if __name__ == '__main__':
    main()
