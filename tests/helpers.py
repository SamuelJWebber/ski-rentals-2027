"""Shared test helpers: the repo path, and the site as it stood at a reviewed commit.

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
    """Write the site as it was at `rev` into a temp dir and return its path (None if the commit is not in
    this clone, e.g. after a history rewrite). The tools read their data from the root they check, so the
    data/ tree comes along: the one committed at `rev`, or, for a commit from before data/ existed (round
    1's 20cb727), a copy of today's data/, so those old pages are checked against today's data on purpose."""
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
    data = [p for p in git('ls-tree', '-r', '--name-only', rev, 'data').stdout.split('\n') if p]
    if data:
        for p in data:
            dst = os.path.join(d, *p.split('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'w', encoding='utf-8', newline='') as fh:
                fh.write(git('show', f'{rev}:{p}').stdout)
    else:
        shutil.copytree(os.path.join(REPO, 'data'), os.path.join(d, 'data'))
    _exported[rev] = d
    return d
