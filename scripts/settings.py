"""Workspace configuration. Python 3.11+, standard library only."""
from pathlib import Path
import os
import re
import tomllib
from platform_io import configure_output

configure_output()

TOOL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(os.environ.get('WIKI_CONFIG', TOOL_ROOT / 'wiki.toml')).expanduser().resolve()
if 'WIKI_CONFIG' in os.environ and not CONFIG_PATH.is_file():
    raise ValueError(f'Configuration not found: {CONFIG_PATH}')
CONFIG = tomllib.loads(CONFIG_PATH.read_text(encoding='utf-8')) if CONFIG_PATH.exists() else {}
WORKSPACE = CONFIG_PATH.parent

def path(value):
    p = Path(value).expanduser()
    return (WORKSPACE / p).resolve() if not p.is_absolute() else p.resolve()

REPO_ROOT = path(os.environ.get('WIKI_REPO_ROOT', '.'))
WIKI_ROOT = path(os.environ.get('WIKI_ROOT', CONFIG.get('wiki', {}).get('path', 'docs/wiki')))
TITLE = CONFIG.get('wiki', {}).get('title', 'My Knowledge Wiki')
REVIEWER = CONFIG.get('wiki', {}).get('reviewer', 'human:owner')
if not isinstance(REVIEWER, str) or not re.fullmatch(r'human:[a-zA-Z0-9_-]+', REVIEWER):
    raise ValueError('wiki.reviewer must be human:<identifier>')
SOURCES = CONFIG.get('sources', {})
EXTRA_ROOTS = {}
for alias, entry in SOURCES.items():
    if not re.fullmatch(r'[A-Za-z0-9_-]+', alias) or not isinstance(entry, dict) or not entry.get('path') or not entry.get('kind'):
        raise ValueError(f'Invalid source configuration: {alias}')
    if entry.get('enabled', True):
        EXTRA_ROOTS[alias] = path(entry['path'])
# Legacy environment overrides also keep isolated fixture tests portable.
for alias, env in [('claude-sessions', 'WIKI_CLAUDE_SESSIONS_DIR'), ('codex-sessions', 'WIKI_CODEX_SESSIONS_DIR'), ('Clippings', 'WIKI_CLIPPINGS_DIR')]:
    if os.environ.get(env):
        EXTRA_ROOTS[alias] = path(os.environ[env])
REQUIRED_SOURCES = {alias for alias, entry in SOURCES.items() if entry.get('enabled', True)}
REQUIRED_KINDS = {SOURCES[alias]['kind'] for alias in REQUIRED_SOURCES} or {'documents'}
