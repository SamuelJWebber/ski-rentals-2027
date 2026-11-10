"""Shared test helpers: the repo path, and the pages as they stood at the reviewed commit.

The reviewed pages come from git history, not from copies in the tree: copying them into tests/ would
republish on GitHub Pages the very text some fixes removed.
"""
import atexit
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, 'tools')
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

REVIEWED = '20cb727'  # the commit review round 1 examined
REVIEWED_R2 = 'd46aeed'  # the commit review round 2 (REVIEW.md) examined: the pages and data of e3866e3
FILES = ['index.html', 'alps-extreme-ski-2027.html', 'steep-and-town-2027.html', 'ski-rentals-2027.html',
         'three-resorts-best-snow-2027.html', 'zermatt-month-stay-2026-27.html', 'README.md', 'HANDOFF.md']
_exported = {}


def git(*args):
    return subprocess.run(['git', *args], cwd=REPO, capture_output=True, text=True, encoding='utf-8')


def have_commit(rev):
    return git('cat-file', '-e', f'{rev}^{{commit}}').returncode == 0


def export(rev=REVIEWED):
    """Write the site files as they were at `rev` into a temp dir and return its path (None if the
    commit is not in this clone, e.g. after a history rewrite)."""
    if rev in _exported:
        return _exported[rev]
    if not have_commit(rev):
        _exported[rev] = None
        return None
    d = tempfile.mkdtemp(prefix=f'site-{rev}-')
    atexit.register(shutil.rmtree, d, True)
    for f in FILES:
        r = git('show', f'{rev}:{f}')
        if r.returncode == 0:
            with open(os.path.join(d, f), 'w', encoding='utf-8', newline='') as fh:
                fh.write(r.stdout)
    _exported[rev] = d
    return d
