"""Consistency checks for the published pages. Standard library only, no network.

usage: python tools/sitecheck.py [--root DIR] [--pre-push]

Each check returns a list of problems (strings). The script prints them and exits 1 if there are any.
`--root` runs the checks against another copy of the pages (the tests use it to show a check fails
on the old pages). `--pre-push` also checks the commits about to be pushed (author emails, local
paths, secrets), which is what tools/hooks/pre-push runs.
"""
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

PAGES = [
    'index.html',
    'alps-extreme-ski-2027.html',
    'steep-and-town-2027.html',
    'ski-rentals-2027.html',
    'three-resorts-best-snow-2027.html',
    'zermatt-month-stay-2026-27.html',
]
VOID = {'br', 'img', 'meta', 'link', 'input', 'hr', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
MONTHS = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'


# ---------------------------------------------------------------- a small HTML tree

class Node:
    __slots__ = ('tag', 'attrs', 'children', 'parent', 'line')

    def __init__(self, tag, attrs, parent, line):
        self.tag, self.attrs, self.children, self.parent, self.line = tag, attrs, [], parent, line

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def text(self):
        out = []

        def walk(n):
            for c in n.children:
                if isinstance(c, Node):
                    if c.tag == 'br':
                        out.append(' ')
                    walk(c)
                else:
                    out.append(c)
        walk(self)
        return re.sub(r'\s+', ' ', ''.join(out)).strip()

    def classes(self):
        return (self.attrs.get('class') or '').split()

    def ancestors(self):
        n = self.parent
        while n is not None:
            yield n
            n = n.parent

    def find_all(self, tag=None, cls=None):
        for n in self.iter():
            if (tag is None or n.tag == tag) and (cls is None or cls in n.classes()):
                yield n

    def __repr__(self):
        return f'<{self.tag} line {self.line}>'


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root', {}, None, 0)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict((k, v or '') for k, v in attrs), self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict((k, v or '') for k, v in attrs), self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse(html_text):
    b = _Builder()
    b.feed(html_text)
    b.close()
    return b.root


def read(root, name):
    with open(os.path.join(root, name), encoding='utf-8') as f:
        return f.read()


_cache = {}


def page(root, name):
    key = (os.path.abspath(root), name)
    path = os.path.join(root, name)
    stamp = os.path.getmtime(path)
    if key not in _cache or _cache[key][0] != stamp:
        text = read(root, name)
        _cache[key] = (stamp, text, parse(text))
    return _cache[key][1], _cache[key][2]


def money(s):
    """'$2,350' -> 2350.0; accepts a leading ~ or ≈."""
    m = re.search(r'\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)', s)
    return float(m.group(1).replace(',', '')) if m else None


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()


# ---------------------------------------------------------------- R1-2: privacy

PRIVACY_PATTERNS = [
    (r'Email to send', 'an enquiry email drafted for the user'),
    (r'\bWe are looking for\b', 'a first-person enquiry'),
    (r'\bbook all three\b', 'a booking plan rather than options'),
    (r"\byour (?:four |two |target |chosen )?(?:weeks?|windows?|dates|trip)\b", 'second-person travel window'),
    (r"\bafter you'd go\b", 'second-person travel window'),
    (r'\b1 ?(?:to|–|-) ?3 people\b', 'party size'),
    (r'\(possibly 3\)', 'party size'),
    (r'\bweeks of 9 Jan, 16 Jan\b', 'the candidate travel weeks as a list'),
    (r'\bTarget weeks\b', 'the candidate travel weeks as a list'),
]
# Business contact addresses that are published by the businesses themselves.
EMAIL_ALLOW = {
    'reservations@nisade.com', 'enquiry@powderlife.com', 'enquiries@japanskiexperience.com',
}
PUBLIC_TEXT_FILES = ['README.md', 'HANDOFF.md']


def check_privacy(root=REPO):
    """No page, README or HANDOFF names the party, lists the candidate weeks as the user's, drafts an
    enquiry in the first person, or tells readers to book specific units."""
    problems = []
    texts = []
    for name in PAGES:
        _, tree = page(root, name)
        texts.append((name, tree.text()))
    for name in PUBLIC_TEXT_FILES:
        if os.path.exists(os.path.join(root, name)):
            texts.append((name, read(root, name)))
    for name, text in texts:
        for pat, why in PRIVACY_PATTERNS:
            for m in re.finditer(pat, text, re.I):
                problems.append(f'{name}: "{m.group(0)}" ({why})')
        for m in re.finditer(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text):
            addr = m.group(0).lower()
            if addr not in EMAIL_ALLOW and not addr.endswith('@users.noreply.github.com') \
                    and not addr.endswith('@anthropic.com'):
                problems.append(f'{name}: email address {addr} is not on the allow-list of business contacts')
        if re.search(r'[A-Za-z]:\\Users\\', text):
            problems.append(f'{name}: contains a local Windows user path')
    return problems


# ---------------------------------------------------------------- anchors

def check_anchors(root=REPO):
    """Every internal link resolves to an id on the target page."""
    problems = []
    ids = {}
    for name in PAGES:
        _, tree = page(root, name)
        ids[name] = {n.attrs['id'] for n in tree.iter() if 'id' in n.attrs}
    for name in PAGES:
        _, tree = page(root, name)
        for a in tree.find_all('a'):
            href = a.attrs.get('href', '')
            if href.startswith(('http:', 'https:', 'mailto:')) or not href:
                continue
            target, _, frag = href.partition('#')
            target = target or name
            if target not in ids:
                if not os.path.exists(os.path.join(root, target)):
                    problems.append(f'{name}:{a.line}: link to missing file {href}')
                continue
            if frag and frag not in ids[target]:
                problems.append(f'{name}:{a.line}: link to missing anchor {href}')
    return problems


# ---------------------------------------------------------------- R1-1 / R1-3: one cost model

def sentences(text):
    return [s for s in re.split(r'(?<=[.!?])\s+(?=[A-Z<(])', text) if s.strip()]


STALE_HEADLINES = ['2,350–2,750', '1,950–2,600', '1,950 incl', '≈$2,200', '$1,950 – $2,600']
ANSWERS = ('Engelberg', 'Telluride', 'Hakuba')


def check_costs(root=REPO):
    """Every figure marked data-cost matches data/costs.json, and the generated tables are current."""
    import costs
    return costs.check(root)


def check_headline_costs(root=REPO):
    """R1-1: the three answers carry figures from the cost model, and the superseded headline ranges
    appear only in a sentence that dates them to September."""
    problems = []
    texts = [(n, page(root, n)[1].text()) for n in PAGES]
    texts.append(('README.md', read(root, 'README.md')))
    for name, text in texts:
        for s in sentences(text):
            for stale in STALE_HEADLINES:
                if stale in s and 'September' not in s:
                    problems.append(f'{name}: undated superseded figure {stale!r} in: {s[:140]}')
    _, tree = page(root, 'index.html')
    for card in tree.find_all('div', 'card'):
        h4 = next(card.find_all('h4'), None)
        if h4 is None or h4.text() not in ANSWERS:
            continue
        price = next(card.find_all('div', 'price'), None)
        if price is None or not any('data-cost' in n.attrs for n in price.iter()):
            problems.append(f'index.html:{card.line}: the {h4.text()} answer price is not taken from the cost model')
    return problems


def _table_with_header(tree, prefix):
    for table in tree.find_all('table'):
        heads = [th.text() for th in table.find_all('th')]
        for i, h in enumerate(heads):
            if h.startswith(prefix):
                return table, i
    return None, None


def check_cost_definitions(root=REPO):
    """R1-3: every 'Week for two' cell is built the same way (a cost-model total, or a dash with the
    reason), the definition is stated under the table, and the README splits the parts."""
    problems = []
    _, tree = page(root, 'index.html')
    table, col = _table_with_header(tree, 'Week for two')
    if table is None:
        return ['index.html: no ranking table with a "Week for two" column']
    for tr in table.find_all('tr'):
        tds = [c for c in tr.children if isinstance(c, Node) and c.tag == 'td']
        if not tds:
            continue
        cell = tds[col]
        has_total = any(n.attrs.get('data-cost', '').endswith(':total') for n in cell.iter())
        if not has_total and not cell.text().startswith('—'):
            problems.append(f'index.html:{tr.line}: "{tds[0].text()}" week-for-two cell is not a cost-model total: {cell.text()!r}')
    defined = False
    n = table.parent
    if n is not None and n.parent is not None:
        sibs = [c for c in n.parent.children if isinstance(c, Node)]
        after = sibs[sibs.index(n) + 1:] if n in sibs else []
        defined = any('Week for two = lodging + tax + two 6-day' in s.text() for s in after[:2])
    if not defined:
        problems.append('index.html: no note under the ranking table stating what "Week for two" includes')
    readme = read(root, 'README.md')
    if '| Lodging for two + tax | Two 6-day passes | Week for two |' not in readme:
        problems.append('README.md: the answers table does not split lodging, tax and passes')
    return problems


# ---------------------------------------------------------------- registry and CLI

CHECKS = {}


def register(key, fn):
    CHECKS[key] = fn
    return fn


register('privacy', check_privacy)
register('anchors', check_anchors)
register('costs', check_costs)


def check_recheck_blocks(root=REPO):
    """R1-4: the recheck sections, header lines, nav links and banner match the latest run's data."""
    import recheck
    return recheck.check(root)


register('recheck-blocks', check_recheck_blocks)
register('headline-costs', check_headline_costs)
register('cost-definitions', check_cost_definitions)


def run(root=REPO, only=None):
    results = {}
    for key, fn in CHECKS.items():
        if only and key not in only:
            continue
        results[key] = fn(root)
    return results


def main(argv):
    root = REPO
    only = None
    pre_push = False
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == '--root':
            root = args.pop(0)
        elif a == '--only':
            only = set(args.pop(0).split(','))
        elif a == '--pre-push':
            pre_push = True
        else:
            print(__doc__)
            return 2
    results = run(root, only)
    if pre_push:
        import prepush
        results['pre-push'] = prepush.check_outgoing(REPO)
    bad = 0
    for key, problems in results.items():
        status = 'ok' if not problems else f'{len(problems)} problem(s)'
        print(f'[{key}] {status}')
        for p in problems:
            print('   ', p)
        bad += len(problems)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
