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
BLOCK = {'p', 'div', 'li', 'ul', 'ol', 'td', 'th', 'tr', 'table', 'thead', 'tbody', 'section', 'header', 'footer',
         'main', 'nav', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt', 'dd', 'dl', 'pre', 'small'}
MONTHS = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'


# Every check registers itself here; the CLI and the tests run them by key.
CHECKS = {}


def register(key, fn):
    CHECKS[key] = fn
    return fn


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
                    if c.tag in ('style', 'script'):
                        continue
                    if c.tag == 'br':
                        out.append(' ')
                    block = c.tag in BLOCK
                    if block:
                        out.append(' ')
                    walk(c)
                    if block:
                        out.append(' ')
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


# ---------------------------------------------------------------- R1-6: currency labels on the Europe page

def _rows_in_recheck(text):
    m = re.search(r'<!-- recheck:start -->(.*?)<!-- recheck:end -->', text, re.S)
    return re.findall(r'<tr>.*?</tr>', m.group(1)) if m else []


def check_currency_labels(root=REPO):
    """R1-6: the Europe page's September Airbnb figures are the US dollars Airbnb displayed. No euro
    label converted to dollars, no "priced out" verdict, and St Anton's change measured in dollars."""
    name = 'alps-extreme-ski-2027.html'
    text, tree = page(root, name)
    body = tree.text()
    problems = [f'{name}: still says {p!r}' for p in ('$2,971', '€2,561', 'priced out', 'Cut from contention') if p in body]
    accom = re.search(r'<h2 id="accom">(.*?)<h2 id="passes">', text, re.S)
    if accom:
        for m in re.finditer(r'€[0-9][0-9,]* ≈ \$[0-9][0-9,]*', accom.group(1)):
            problems.append(f'{name}: Airbnb figure shown as euros converted to dollars: {m.group(0)}')
    st_anton = [r for r in _rows_in_recheck(text) if 'Pure Alpin' in r and 'check_in=2027-01-09' in r]
    if not st_anton:
        problems.append(f'{name}: St Anton row missing from the recheck table')
    elif '&minus;$102 (&minus;4%)' not in st_anton[0]:
        problems.append(f'{name}: St Anton change is not measured from the dollar quote (expected −$102, −4%)')
    return problems


register('currency-labels', check_currency_labels)


# ---------------------------------------------------------------- R1-7: corrections reach every page

# (pattern, the corrected fact, a qualifier that may sit within 200 characters to mark the old wording
# as superseded or as an estimate). Add a row whenever a correction is made, before closing it.
STALE_FACTS = [
    (r'two supermarkets, but no gym found', 'Fernie has a gym (Evolution Health & Fitness, verified 9 Nov 2026)', None),
    (r'no commercial gym appears in any directory', 'Fernie has a gym (verified 9 Nov 2026)', None),
    (r'10,000 sq ft', 'the Fernie gym size is unsourced', None),
    (r'5,200-person town', 'Fernie has 6,320 people (2021 census, as on the index)', None),
    (r'Town 5 km from the lift|5 km / 7', 'Fernie town is 8 km by road from the lift', None),
    (r'\bThe March answer\b|North American March answer', 'Crested Butte was dropped on the combined page', None),
    (r'every 2 h(?:ou)?rs?\b', 'the Revelstoke bus runs about every 30 to 45 minutes', r'September said'),
    (r"Jackson(?:'|’)s 40 minutes", 'Teton Village is 12 to 14 miles and 19 to 26 minutes from Jackson', None),
    (r'365[–-]390', 'the Engelberg 6-day pass is unverified (CHF 274 to 390)', r'(?i)unverified|estimate'),
]


def check_propagated_corrections(root=REPO):
    """R1-7: a fact corrected on one page is not still stated the old way on another."""
    problems = []
    for name in PAGES:
        text = page(root, name)[1].text()
        for pat, fact, qualifier in STALE_FACTS:
            for m in re.finditer(pat, text):
                window = text[max(0, m.start() - 200):m.end() + 200]
                if qualifier and re.search(qualifier, window):
                    continue
                problems.append(f'{name}: "{m.group(0)}" contradicts the correction: {fact}')
    return problems


register('propagated-corrections', check_propagated_corrections)


# ---------------------------------------------------------------- R1-8: pick status and recheck coverage

ROOM_REF = re.compile(r'/rooms/(\d{5,})|\((\d{7,})\)|[Rr]oom (\d{5,})')


def _room_refs(seg):
    return {next(g for g in m.groups() if g) for m in ROOM_REF.finditer(seg)}


def _unidentified_priced_rows(text):
    """Priced Airbnb rows in the steep page's listing tables that carry no room ID."""
    m = re.search(r'<section id="priced">(.*?)</section>', text, re.S)
    if not m:
        return []
    out = []
    for row in re.findall(r'<tr>.*?</tr>', m.group(1), re.S):
        if '<th' in row or '$' not in strip_tags(row) or _room_refs(row):
            continue
        out.append(strip_tags(row)[:60])
    return out


def check_pick_status(root=REPO):
    """R1-8: every listing a page cites outside its recheck table carries a dated recheck note; each
    recheck says it covers listings identified by room ID; the skipped count matches the page."""
    import recheck
    meta, rows = recheck.load()
    rooms = {r['room_id'] for r in rows}
    problems = []
    for tag, name in recheck.PAGES.items():
        text = read(root, name)
        block = re.search(r'<!-- recheck:start -->(.*?)<!-- recheck:end -->', text, re.S)
        outside = re.sub(r'<!-- recheck:start -->.*?<!-- recheck:end -->', '', text, flags=re.S)
        segments = re.findall(r'<tr>.*?</tr>', outside, re.S) + re.findall(r'<div class="card">.*?</ul>\s*</div>', outside, re.S)
        for seg in segments:
            for rid in sorted(_room_refs(seg) & rooms):
                if f'data-room="{rid}"' not in seg:
                    problems.append(f'{name}: listing {rid} is cited without its dated recheck status')
        if not block or 'identified by room ID' not in block.group(1):
            problems.append(f'{name}: the recheck does not say it covers only listings identified by room ID')
    steep = read(root, recheck.PAGES['steep'])
    skipped = _unidentified_priced_rows(steep)
    if skipped and f'{len(skipped)} more priced listings on this page have no room ID' not in steep:
        problems.append(f'steep-and-town-2027.html: {len(skipped)} priced listings have no room ID, and the recheck does not say so')
    if 'identified by room ID' not in page(root, 'index.html')[1].text():
        problems.append('index.html: the recheck tally does not say it covers only listings identified by room ID')
    return problems


register('pick-status', check_pick_status)


# ---------------------------------------------------------------- R1-9: capacity claims against the lift table

MULTIPLES = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'two and a half': 2.5, 'three and a half': 3.5, 'twice': 2}


def lift_capacities(tree):
    """{resort name as written in the lift-audit table: people per hour}."""
    table, col = _table_with_header(tree, 'Capacity per hour')
    caps = {}
    if table is None:
        return caps
    for tr in table.find_all('tr'):
        tds = [c for c in tr.children if isinstance(c, Node) and c.tag == 'td']
        if len(tds) > col:
            m = re.search(r'([0-9][0-9,]+)', tds[col].text())
            if m:
                caps[tds[1].text()] = int(m.group(1).replace(',', ''))
    return caps


def _cap_of(caps, name):
    for k, v in caps.items():
        if k.startswith(name) or name in k:
            return v
    return None


def check_capacity_claims(root=REPO):
    """R1-9: on the index, "N people an hour, about K times X's" and "more than A, B and C combined"
    must hold against the same page's lift-audit table, and no row may claim nothing comes close
    when another resort moves more people."""
    problems = []
    _, tree = page(root, 'index.html')
    caps = lift_capacities(tree)
    if not caps:
        return ['index.html: lift-audit table with a "Capacity per hour" column not found']
    text = tree.text()
    for m in re.finditer(r'([0-9][0-9,]+) people an hour, ([^.]*)', text):
        claimed = int(m.group(1).replace(',', ''))
        rest = m.group(2)
        for w, name in re.findall(r"about ((?:two|three|four|five)(?: and a half)?|twice) times ([A-Z][A-Za-z ]+?)'s", rest):
            other = _cap_of(caps, name.strip())
            if other is None:
                problems.append(f'index.html: capacity claim names {name!r}, which is not in the lift table')
            elif abs(claimed / other - MULTIPLES[w]) > 0.35:
                problems.append(f'index.html: {claimed:,} is {claimed / other:.2f} times {name}\'s {other:,}, not "{w}"')
        comb = re.search(r'more than ((?:[A-Z][A-Za-z ]+, )+[A-Z][A-Za-z ]+ and [A-Z][A-Za-z ]+) combined', rest)
        if comb:
            names = [n.strip() for n in re.split(r', | and ', comb.group(1))]
            total = sum(_cap_of(caps, n) or 0 for n in names)
            if total >= claimed:
                problems.append(f'index.html: claims {claimed:,} an hour beats {", ".join(names)} combined, but they total {total:,}')
    whistler = _cap_of(caps, 'Whistler')
    if 'Nothing else comes close' in text and whistler and any(v > whistler for v in caps.values()):
        problems.append('index.html: "Nothing else comes close" although the table lists a resort with more capacity')
    return problems


register('capacity-claims', check_capacity_claims)


# ---------------------------------------------------------------- R1-10: all-ins equal quote x (1 + rate)

# Lodging-tax rates the steep page states in "How to read the prices" (Telluride: the town's own rate).
STEEP_RATES = [
    (r'^Telluride|Telluride town', 17.22),
    (r'^(Whistler|Fernie|Red Mountain|Rossland|Revelstoke|Kicking Horse|Golden|Sun Peaks)|Whistler Village|Fernie Alpine|Red Mountain|Kicking Horse base', 16),
    (r'^Crested Butte|Mt Crested Butte', 16),
    (r'^(Park City|Snowbird|Salt Lake City)|Park City Old Town', 15),
    (r'^Taos', 15),
    (r'^(Jackson|Teton Village)|Jackson town', 13),
    (r'^Big Sky', 12),
    (r'^Mont-Tremblant', 18.5),
]


def _priced_tables(tree):
    for sec in tree.find_all('section'):
        if sec.attrs.get('id') != 'priced':
            continue
        for table in sec.find_all('table'):
            heads = [th.text() for th in table.find_all('th')]
            q = next((i for i, h in enumerate(heads) if h.startswith('Fetched')), None)
            a = next((i for i, h in enumerate(heads) if h.startswith('All-in')), None)
            if q is None or a is None:
                continue
            for tr in table.find_all('tr'):
                tds = [c for c in tr.children if isinstance(c, Node) and c.tag == 'td']
                if len(tds) > max(q, a):
                    yield tr, tds, q, a


def check_all_in_arithmetic(root=REPO):
    """R1-10: on the steep page every North American all-in equals the quote times (1 + the stated
    rate) within $1, unless the cell says why not; every scorecard 'cheapest all-in' is one of them."""
    name = 'steep-and-town-2027.html'
    _, tree = page(root, name)
    problems, listed = [], set()
    for tr, tds, q, a in _priced_tables(tree):
        label = tds[0].text() + ' | ' + tds[1].text()
        allin_txt = tds[a].text()
        for m in re.finditer(r'\$([0-9][0-9,]*)', allin_txt):
            listed.add(int(m.group(1).replace(',', '')))
        rate = next((r for pat, r in STEEP_RATES if re.search(pat, tds[0].text()) or re.search(pat, tds[1].text())), None)
        quote, allin = money(tds[q].text()), money(allin_txt)
        if rate is None or quote is None or allin is None or '→' in tds[q].text() or '&rarr;' in tds[q].text():
            continue
        if re.search(r'at \d+(\.\d+)?%', allin_txt):
            continue  # the cell states its own rate and why
        if abs(quote * (1 + rate / 100) - allin) > 1:
            problems.append(f'{name}:{tr.line}: {label[:50]}: ${quote:,.0f} at {rate}% is ${quote * (1 + rate / 100):,.0f}, page says ${allin:,.0f}')
    table, col = _table_with_header(tree, 'Cheapest all-in')
    if table is not None:
        for tr in table.find_all('tr'):
            tds = [c for c in tr.children if isinstance(c, Node) and c.tag == 'td']
            if len(tds) <= col or any('data-cost' in n.attrs for n in tds[col].iter()):
                continue
            v = money(tds[col].text())
            if v is not None and all(abs(v - x) > 1 for x in listed):
                problems.append(f'{name}:{tr.line}: scorecard {tds[0].text()} cheapest all-in ${v:,.0f} matches no listed option')
    return problems


register('all-in-arithmetic', check_all_in_arithmetic)


# ---------------------------------------------------------------- R1-11: "fits" says which budget

FIT = re.compile(r'\bfits?\b')
BUDGET_VIEW = re.compile(r'lodging|all-in|passes|pass\b|skiing|10k on|with tax')


def check_fit_qualifiers(root=REPO):
    """R1-11: on the Zermatt page every sentence saying something fits (or no longer fits) the budget
    says which view it uses, lodging alone or all-in with lift passes; on the index, the same for any
    sentence about a Zermatt or Täsch month."""
    problems = []
    for name in ('zermatt-month-stay-2026-27.html', 'index.html'):
        for s in sentences(page(root, name)[1].text()):
            if not FIT.search(s):
                continue
            if name == 'index.html' and not re.search(r'Zermatt|Täsch|T&auml;sch|month', s):
                continue
            if not BUDGET_VIEW.search(s):
                problems.append(f'{name}: "fits" without saying lodging-only or all-in: {s[:150]}')
    return problems


register('fit-qualifiers', check_fit_qualifiers)


# ---------------------------------------------------------------- R1-13: the recheck method

# Assembled at run time so this file does not itself contain a User-Agent string.
BROWSER_UA = re.compile('|'.join(['Mozil' + r'la/5\.0', 'Apple' + 'WebKit/', 'Chro' + r'me/\d{2,3}\.\d']))
METHOD_PHRASES = ('human pace', '429')


def check_method(root=REPO):
    """R1-13: no file in the repo carries a browser User-Agent; README and HANDOFF state the recheck
    method (a browser at human pace, stop at the first 429), and HANDOFF describes no scraping as the
    method to reuse."""
    problems = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__')]
        for f in files:
            if not f.endswith(('.py', '.html', '.md', '.json', '.tsv', '.sh', '.txt')) and f != 'pre-push':
                continue
            path = os.path.join(dirpath, f)
            with open(path, encoding='utf-8', errors='replace') as fh:
                if BROWSER_UA.search(fh.read()):
                    problems.append(f'{os.path.relpath(path, root)}: carries a browser User-Agent string')
    for name in ('README.md', 'HANDOFF.md'):
        text = read(root, name) if os.path.exists(os.path.join(root, name)) else ''
        for phrase in METHOD_PHRASES:
            if phrase not in text:
                problems.append(f'{name}: does not state the recheck method ({phrase!r} missing)')
    handoff = read(root, 'HANDOFF.md') if os.path.exists(os.path.join(root, 'HANDOFF.md')) else ''
    for s in sentences(handoff):
        if re.search(r'plain HTTP|User-Agent', s) and not re.search(r'retired|never|no longer|not to be', s):
            problems.append(f'HANDOFF.md: describes scripted fetching as the method: {s[:120]}')
    return problems


register('method', check_method)


# ---------------------------------------------------------------- LOW findings: superseded wording

# finding: [(pattern, why)]; any match on any page is a problem.
SUPERSEDED = {
    'R1-14': [(r'of these, only Niseko United|Of the Japanese resorts on the rentals page, only Niseko',
               'say which resorts the Ikon correction covers (Furano, Shiga Kogen and Myoko Suginohara are on Ikon)')],
    'R1-15': [(r'[Ff]ree cancellation to\b|[Rr]efundable to\b|\b[Ff]ree to \d|until 2[12] January|'
               r'refund in full only until|partial to \d|refunds until the day before',
               'Airbnb\'s cutoff falls before the date, in the listing\'s local time')],
    'R1-17': [(r'\b2 ?am\b|2 a\.m\.', 'the gondola\'s late Friday and Saturday hours are not published')],
    'R1-19': [(r'Ranks 6th of 9', 'Telluride is 10th of 16 in the lift audit'),
              (r'Telluride/Big Sky tie', 'Telluride peaks in February; Big Sky ties December with March'),
              (r'convert CAD at 1\.38', 'Airbnb quotes are already US dollars'),
              (r'Airbnb totals are all-in', 'Airbnb totals are before taxes'),
              (r'4 listings had been removed', '4 listing-weeks from 3 listings were removed'),
              (r'0\.80 CHF', 'the pages use 0.81 CHF per USD')],
}


def check_superseded(root=REPO, findings=None):
    problems = []
    for name in PAGES:
        text = page(root, name)[1].text()
        for fid, rules in SUPERSEDED.items():
            if findings and fid not in findings:
                continue
            for pat, why in rules:
                for m in re.finditer(pat, text):
                    problems.append(f'{fid} {name}: "{m.group(0)}": {why}')
    return problems


register('superseded-wording', check_superseded)


def _half_up(x):
    return int(x + 0.5)


def check_three_resorts_arithmetic(root=REPO):
    """Every all-in on the three-resort page equals quote x (1 + the column's rate), rounded half up,
    and the combined totals equal the sums of the rows they name."""
    name = 'three-resorts-best-snow-2027.html'
    _, tree = page(root, name)
    problems, allin_by_name = [], {}
    for table in tree.find_all('table'):
        rows = [[c for c in tr.children if isinstance(c, Node) and c.tag in ('td', 'th')] for tr in table.find_all('tr')]
        if not rows:
            continue
        head = [c.text() for c in rows[0]]
        rate_col = next((i for i, h in enumerate(head) if re.match(r'All-in \+[0-9.]+%', h)), None)
        quote_col = next((i for i, h in enumerate(head) if h == 'Quote'), None)
        if rate_col is None or quote_col is None:
            continue
        rate = float(re.search(r'\+([0-9.]+)%', head[rate_col]).group(1))
        for cells in rows[1:]:
            q, a = money(cells[quote_col].text()), money(cells[rate_col].text())
            if q is None or a is None:
                continue
            want = _half_up(q * (1 + rate / 100))
            allin_by_name[cells[0].text()] = a
            if int(a) != want:
                problems.append(f'{name}: {cells[0].text()[:40]}: ${q:,.0f} + {rate}% = ${want:,}, page says ${a:,.0f}')
    text = tree.text()
    picks = [v for k, v in allin_by_name.items() if '(pick)' in k]
    m = re.search(r'All three weeks together: \$([0-9,]+)', text)
    if m and picks and int(m.group(1).replace(',', '')) != int(sum(picks)):
        problems.append(f'{name}: "all three weeks together" says ${m.group(1)}, the picks sum to ${int(sum(picks)):,}')
    return problems


register('three-resorts-arithmetic', check_three_resorts_arithmetic)


# ---------------------------------------------------------------- R1-16: rolling sources are labelled

ROLLING_URL = re.compile(r'enso_advisory/ensodisc\.shtml|/long_range/lead0\d/|/-\d+,0/|bchydro\.com/info/res_hydromet/data/')
ROLLING_NOTE = re.compile(r'replaced each month|rolling file|page updates|readings\.tsv')


def check_rolling_citations(root=REPO):
    """R1-16: a link to a source that replaces itself (CPC's current discussion and outlook images, a
    SNOTEL 'last N days' window, BC Hydro's rolling file) carries a note that it updates, next to it."""
    problems = []
    for name in PAGES:
        _, tree = page(root, name)
        for a in tree.find_all('a'):
            href = a.attrs.get('href', '')
            m = ROLLING_URL.search(href)
            if not m:
                continue
            block = next((n for n in a.ancestors() if n.tag in ('li', 'p', 'td', 'div')), None)
            if block is None or not ROLLING_NOTE.search(block.text()):
                problems.append(f'{name}:{a.line}: links a source that updates itself ({m.group(0)}) without saying so: {href[:90]}')
    if not os.path.exists(os.path.join(REPO, 'data', 'readings.tsv')):
        problems.append('data/readings.tsv: no dated snapshot of the live readings')
    return problems


register('rolling-citations', check_rolling_citations)


# ---------------------------------------------------------------- registry and CLI

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
