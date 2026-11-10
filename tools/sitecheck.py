"""Consistency checks for the published pages. Standard library only, no network.

usage: python tools/sitecheck.py [--root DIR] [--today YYYY-MM-DD] [--only KEY,...] [--pre-push]

Each check returns a list of problems (strings). The script prints them and exits 1 if there are any.
`--root` runs the checks against another copy of the pages, with that copy's own data/ (the tests use
it to show a check fails on the old pages). `--today` sets the date the checks treat as today (default:
the real date), so a refund window or deadline that has passed fails the run. `--pre-push` also checks
the commits about to be pushed (author emails, local paths, booking wording, secrets), which is what
tools/hooks/pre-push runs.
"""
import json
import os
import re
import subprocess
import sys
from datetime import date
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
TODAY = None  # set by --today; None means the real date


def today():
    return TODAY or date.today()


def set_today(iso=None):
    """Treat `iso` (YYYY-MM-DD) as today in every check; None goes back to the real date."""
    global TODAY
    TODAY = date.fromisoformat(iso) if iso else None

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


def runs_dir(root):
    """The recheck runs that belong to the pages under root (its data/checks sits beside them)."""
    return os.path.join(root, 'data', 'recheck')


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

def tracked_text_files(root=REPO):
    """Every tracked text file under root (git ls-files), or every text file when root is not a clone."""
    import privacy
    r = subprocess.run(['git', 'ls-files'], cwd=root, capture_output=True, text=True, encoding='utf-8')
    names = r.stdout.split('\n') if r.returncode == 0 and r.stdout.strip() else []
    if not names:
        for dirpath, dirnames, files in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__')]
            names += [os.path.relpath(os.path.join(dirpath, f), root).replace('\\', '/') for f in files]
    return sorted(n for n in names if n and privacy.is_text(n) and os.path.exists(os.path.join(root, n)))


def check_privacy(root=REPO):
    """R1-2 and R2-8: no tracked text file names the party, lists the candidate weeks as the user's,
    drafts an enquiry in the first person, tells readers to book specific units, or records a booking in
    any wording (first person or impersonal, a label, a confirmation code); and none holds a local path in
    any form, an email outside the allow-list, or a token. Pages are read as their readers see them.
    Wording is not scanned in code and tests, which hold the patterns, and a review's quoted examples are
    evidence, not bookings."""
    import privacy
    problems = []
    for name in tracked_text_files(root):
        raw = read(root, name)
        text = page(root, name)[1].text() if name in PAGES else raw
        if privacy.wording_scope(name):
            for what, why in privacy.wording_problems(privacy.unquote_review(name, text)):
                problems.append(f'{name}: "{what}" ({why})')
        for what, why in privacy.other_problems(raw):
            problems.append(f'{name}: {why}' + (f' ({what})' if why.startswith('an email') else ''))
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


def cost_model(root=REPO, strict=True):
    """(the cost model beside the pages, problems): a model that does not load is a problem, not a crash,
    and leaves an empty model so the other checks still run. strict=False skips the schema checks
    (stay dates, dated pass prices) for checks that do not use those fields."""
    import costs
    try:
        if strict:
            return costs.load(costs.data_path(root)), []
        with open(costs.data_path(root), encoding='utf-8') as f:
            return json.load(f), []
    except (ValueError, KeyError, OSError) as e:
        return {'rows': []}, [f'data/costs.json: {e}']


def check_costs(root=REPO):
    """Every figure marked data-cost matches data/costs.json, and the generated tables are current."""
    import costs
    model, problems = cost_model(root)
    if problems:
        return problems
    return costs.check(root, model=model, today=today())


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


ST_ANTON = ('1455513831165257651', '2027-01-09')  # Pure Alpin Apart, 9-16 Jan: its September quote was in USD


def _st_anton_change(root):
    """The change cell the readings give St Anton's row: its newest quote against the September dollar quote."""
    import recheck
    _, rows = recheck.load(runs_dir=runs_dir(root))
    r = next((r for r in rows if r['page'] == 'alps' and (r['room_id'], r['check_in']) == ST_ANTON), None)
    return recheck.change_cell(r['sept_quote_usd'], r['quote_usd']) if r else None


def check_currency_labels(root=REPO, expect=None):
    """R1-6: the Europe page's September Airbnb figures are the US dollars Airbnb displayed. No euro
    label converted to dollars, no "priced out" verdict, and St Anton's change measured in dollars: the
    change cell equals the newest quote minus the September dollar quote, whatever the newest quote is
    (R2-7), unless the caller passes the expected cell (the tests do, for the round-1 pages)."""
    name = 'alps-extreme-ski-2027.html'
    text, tree = page(root, name)
    body = tree.text()
    problems = [f'{name}: still says {p!r}' for p in ('$2,971', '€2,561', 'priced out', 'Cut from contention') if p in body]
    accom = re.search(r'<h2 id="accom">(.*?)<h2 id="passes">', text, re.S)
    if accom:
        for m in re.finditer(r'€[0-9][0-9,]* ≈ \$[0-9][0-9,]*', accom.group(1)):
            problems.append(f'{name}: Airbnb figure shown as euros converted to dollars: {m.group(0)}')
    st_anton = [r for r in _rows_in_recheck(text) if f'rooms/{ST_ANTON[0]}?check_in={ST_ANTON[1]}' in r]
    want = expect or _st_anton_change(root)
    if not st_anton:
        problems.append(f'{name}: St Anton row missing from the recheck table')
    elif want and want not in st_anton[0]:
        shown = want.replace('&minus;', '−').replace(' (', ', ').rstrip(')')
        problems.append(f'{name}: St Anton change is not measured from the dollar quote (expected {shown})')
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
    (r'already demolished', 'no source found on 9 Nov 2026 for the Hakuba base and terrace demolition',
     r'could not be traced|Unsourced'),
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
    meta, rows = recheck.load(runs_dir=runs_dir(root))
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


# ---------------------------------------------------------------- R2-9: every logged status from its own line

CANCEL_FORM = re.compile(r'(?:Free cancellation (?:before [A-Z][a-z]+ \d{1,2}|for \d+ hours)|Cancel before |'
                         r'Non-refundable|This reservation is non-refundable)')


def check_reading_evidence(root=REPO):
    """R2-9: every browser reading in data/checks keeps the page's own line that decided its status, and
    that line supports the status: a price line for BOOKABLE (with the same total), the page's own
    unavailability line for NOT_OFFERED, a removal notice for REMOVED. Rows typed by hand on 9 Nov
    (source=typed) kept no price line, so a typed BOOKABLE needs a total; a typed "not offered" still
    needs the page's own line. A cancellation line must be one Airbnb writes."""
    import csv
    import glob
    import listing_status as ls
    import log_read
    problems = []
    for path in sorted(glob.glob(os.path.join(root, 'data', 'checks', '*.tsv'))):
        name = 'data/checks/' + os.path.basename(path)
        with open(path, encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            if reader.fieldnames != log_read.FIELDS:
                problems.append(f'{name}: columns are not those tools/log_read.py writes ({", ".join(log_read.FIELDS)})')
                continue
            rows = list(reader)
        for i, r in enumerate(rows, 2):
            where = f'{name}:{i} (room {r["room_id"]}, {r["check_in"]})'
            if r['source'] not in ('pasted', 'typed'):
                problems.append(f'{where}: source is {r["source"]!r}, not pasted or typed')
                continue
            status, total, _ = ls.status_from_evidence(r['evidence'])
            if r['source'] == 'pasted' or r['evidence']:
                if status != r['status']:
                    problems.append(f'{where}: the stored line supports {status}, the row says {r["status"]}: '
                                    f'{r["evidence"][:60]!r}')
                elif status == ls.BOOKABLE and str(total) != r['total_usd']:
                    problems.append(f'{where}: the stored line says ${total:,}, the row says ${r["total_usd"]}')
            elif r['status'] == ls.BOOKABLE and not r['total_usd']:
                problems.append(f'{where}: a typed BOOKABLE row with no total')
            elif r['status'] in (ls.NOT_OFFERED, ls.REMOVED):
                problems.append(f'{where}: {r["status"]} without the page\'s own line in the evidence column')
            if r['cancellation'] and not CANCEL_FORM.match(r['cancellation']):
                problems.append(f'{where}: {r["cancellation"][:50]!r} is not a cancellation line Airbnb writes')
    return problems


register('reading-evidence', check_reading_evidence)


# ---------------------------------------------------------------- R2-1: a logged walk behind every "cheapest" and "none"

def _step_passes(st):
    return st.get('washer') == 'in unit' and st.get('refund', '').startswith('Free cancellation before')


def _step_fails(st):
    return (st.get('washer') == 'not stated in the unit'
            or bool(re.match(r'Free cancellation for \d+ hours|Non-refundable', st.get('refund', ''))))


def load_walks(root=REPO):
    import glob
    out = {}
    for path in sorted(glob.glob(os.path.join(root, 'data', 'walks', '*.json'))):
        with open(path, encoding='utf-8') as f:
            for w in json.load(f)['walks']:
                out[w['key']] = dict(w, _file='data/walks/' + os.path.basename(path))
    return out


def check_walks(root=REPO):
    """R2-1: every walk log holds together, and every claim it backs says what it found. Steps run in the
    search's price order. A 'pick' walk ends at a listing whose own page puts the washer in the unit and
    gives a free-cancellation date, within the budget with tax, and every earlier step fails on the washer
    or the refund. A 'budget_line' walk has no passing step within the budget, and a step or the next
    result past it. A step citing data/checks matches the logged read. The cost row a walk backs names the
    pick at the price read on its page, with a verdict that agrees. Every sentence saying there is "no
    refundable" option names a resort and month whose walk reached the budget line, unless the sentence
    marks itself as a correction."""
    import csv
    import glob
    problems = []
    walks = load_walks(root)
    reads = {}
    for path in sorted(glob.glob(os.path.join(root, 'data', 'checks', '*.tsv'))):
        with open(path, encoding='utf-8', newline='') as f:
            for r in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
                reads[(r['room_id'], r['check_in'])] = r
    for key, w in walks.items():
        where = f'{w["_file"]} {key}'
        steps = w['steps']
        prices = [s['search_usd'] for s in steps]
        if prices != sorted(prices):
            problems.append(f'{where}: the steps are not in the search\'s price order')
        line = w['budget_usd'] - w['tax_usd']
        for i, st in enumerate(steps):
            if 'data/checks' in st.get('refund_read', '') + st.get('washer_read', ''):
                r = reads.get((st['room_id'], w['check_in']))
                if r is None:
                    problems.append(f'{where}: step {st["room_id"]} cites data/checks, which has no read of it')
                elif st.get('refund') and r['cancellation'] != st['refund']:
                    problems.append(f'{where}: step {st["room_id"]} refund line differs from data/checks')
                elif st.get('page_usd') and str(st['page_usd']) != r['total_usd']:
                    problems.append(f'{where}: step {st["room_id"]} page price differs from data/checks')
        if w['outcome'] == 'pick':
            last = steps[-1] if steps else {}
            if last.get('room_id') != w['pick'] or not _step_passes(last):
                problems.append(f'{where}: the walk does not end at a listing with the washer in the unit and free cancellation')
            elif last['search_usd'] > line:
                problems.append(f'{where}: the pick is past the budget line with tax')
            for st in steps[:-1]:
                if not _step_fails(st):
                    problems.append(f'{where}: step {st["room_id"]} before the pick neither fails on the washer nor on the refund')
        elif w['outcome'] == 'budget_line':
            for st in steps:
                if st['search_usd'] <= line and _step_passes(st):
                    problems.append(f'{where}: step {st["room_id"]} passes within the budget, so the walk did not reach the line')
                elif st['search_usd'] <= line and not _step_fails(st):
                    problems.append(f'{where}: step {st["room_id"]} within the budget was not shown to fail')
            beyond = [st for st in steps if st['search_usd'] > line] + ([w['next']] if w.get('next') else [])
            if not beyond:
                problems.append(f'{where}: the walk stops before the budget line')
        else:
            problems.append(f'{where}: unknown outcome {w["outcome"]!r}')
    model, bad = cost_model(root, strict=False)
    problems += bad
    for row in model['rows']:
        k = row.get('walk')
        if not k:
            if re.match(r'(?:Cheapest|First) listing', row['lodging']['basis']) and row['lodging']['usd']:
                problems.append(f'data/costs.json {row["key"]}: a "cheapest" basis with no walk log behind it')
            continue
        w = walks.get(k)
        if w is None:
            problems.append(f'data/costs.json {row["key"]}: walk {k!r} is not in data/walks')
            continue
        if w['outcome'] == 'pick':
            pick = w['steps'][-1]
            if row['lodging']['rooms'][:1] != [w['pick']]:
                problems.append(f'data/costs.json {row["key"]}: the row does not price the walk\'s pick {w["pick"]}')
            elif pick.get('page_usd') and row['lodging']['usd'] != [pick['page_usd'], pick['page_usd']]:
                problems.append(f'data/costs.json {row["key"]}: lodging differs from the pick\'s page price ${pick["page_usd"]:,}')
        if (w['outcome'] == 'budget_line') == row['fits'].startswith('Yes'):
            problems.append(f'data/costs.json {row["key"]}: the verdict {row["fits"]!r} contradicts the walk ({w["outcome"]})')
    months = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '12': 'Dec'}
    found = {(w['resort'], months.get(w['check_in'][5:7], '?')): w['outcome'] for w in walks.values()}
    texts = [(n, page(root, n)[1].text()) for n in PAGES]
    texts += [(n, read(root, n)) for n in ('README.md', 'HANDOFF.md') if os.path.exists(os.path.join(root, n))]
    for name, text in texts:
        for s in sentences(text):
            if not re.search(r'\bno refundable\b', s, re.I) or re.search(r'Corrected|first said|was wrong', s):
                continue
            named = [(r, m) for (r, m) in found if r in s and re.search(m, s)]
            if any(found[k] == 'pick' for k in named):
                problems.append(f'{name}: "no refundable" for a resort and month whose walk found one: {s[:120]}')
            elif not any(found[k] == 'budget_line' for k in named):
                problems.append(f'{name}: "no refundable" with no logged walk that reached the budget line: {s[:120]}')
    return problems


register('walks', check_walks)


# ---------------------------------------------------------------- R2-6: refund windows expire

PICK_LINK = re.compile(r'/rooms/(\d+)\?check_in=(\d{4}-\d{2}-\d{2})&(?:amp;)?check_out=(\d{4}-\d{2}-\d{2})')


def check_refund_windows(root=REPO):
    """R2-6: as of today (--today), no cost-table row still answers "Yes" on a refund window that has
    closed, no pick on the three-resort page rests on one, and the index header gives the refund windows'
    read date and the first one to close, from the data. A listing read again with a later window passes;
    a row costs.py has marked closed passes."""
    import costs
    model, problems = cost_model(root)
    readings = costs.load_readings(root)
    t = today()
    for row in model['rows']:
        st = costs.refund_state(row, readings)
        _, closed = costs.refund_text(row, st, t)
        if closed and row['fits'].startswith('Yes'):
            table = re.search(r'<!-- costs:start -->(.*?)<!-- costs:end -->', read(root, 'index.html'), re.S)
            cell = re.search(rf'data-cost="{row["key"]}:total".*?</tr>', table.group(1) if table else '', re.S)
            if cell and 'Refund window closed' not in cell.group(0):
                problems.append(f'index.html: {row["resort"]} {costs.week_label(row)} answers "Yes" on a refund window '
                                f'that closed on {costs.short(st["cutoff"])}; read the listing again or run tools/costs.py')
    newest = {}
    for r in readings:
        newest[(r['room_id'], r['check_in'], r['check_out'])] = r
    text = read(root, 'three-resorts-best-snow-2027.html')
    picks = re.search(r'<section id="picks">(.*?)</section>', text, re.S)
    for m in PICK_LINK.finditer(picks.group(1) if picks else ''):
        r = newest.get(m.groups())
        if r is None:
            problems.append(f'three-resorts-best-snow-2027.html: pick {m.group(1)} has no listing-page reading in data/checks')
            continue
        c = costs.cutoff(r['cancellation'], m.group(2))
        if c is None:
            problems.append(f'three-resorts-best-snow-2027.html: pick {m.group(1)} has no free-cancellation date on record')
        elif c <= t:
            problems.append(f'three-resorts-best-snow-2027.html: pick {m.group(1)}\'s refund window closed on '
                            f'{costs.short(c)} (read {r["read_date"]}); read it again or drop the pick')
    if '<!-- refund-window:start -->' not in read(root, 'index.html'):
        problems.append('index.html: the header does not say when the refund windows were read and when the first closes')
    return problems


register('refund-windows', check_refund_windows)


# ---------------------------------------------------------------- R2-5: every lift-pass price is dated

def check_pass_dates(root=REPO):
    """R2-5: every lift-pass price in data/costs.json carries the date it was quoted and the cost table
    prints it; where the README or the index dates a week for two, the date it gives belongs to the
    lodging, and the passes are dated separately."""
    model, problems = cost_model(root)
    html_text = read(root, 'index.html')
    for row in model['rows']:
        q = row['passes']['quoted']
        cell = re.search(rf'data-cost="{row["key"]}:passes">[^<]*</span><br><span class="small">([^<]*)</span>', html_text)
        if cell and f'Quoted {html_escape(q)}' not in cell.group(1):
            problems.append(f'index.html: the {row["key"]} pass price does not print its quoted date ({q})')
    texts = [('README.md', read(root, 'README.md')), ('index.html', page(root, 'index.html')[1].text())]
    for name, text in texts:
        for s in sentences(text):
            if not re.search(r'Week for two = ', s):
                continue
            for m in re.finditer(rf'\bpriced \d{{1,2}} (?:{MONTHS})[a-z]* \d{{4}}', s):
                if not re.search(r'[Ll]odging\s*$', s[:m.start()]):
                    problems.append(f'{name}: a week for two is dated "{m.group(0)}" as a whole, but its lift '
                                    f'passes are mostly September estimates: {s[:110]}')
    return problems


def html_escape(s):
    import html
    return html.escape(s)


register('pass-dates', check_pass_dates)


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


# ---------------------------------------------------------------- R2-2: "all-in" means lodging plus tax

ALL_IN_PAGES = ('steep-and-town-2027.html', 'three-resorts-best-snow-2027.html')
ALL_IN_FIGURE = re.compile(r'(?P<cur>US)?\$\s?(?P<x>[0-9][0-9,]*)(?:\s*(?:–|-)\s*\$?(?P<y>[0-9][0-9,]*))?'
                           r'(?P<gap>(?:\s+[a-z]+){0,2})\s+all-in\b')
ALL_IN_SPAN = re.compile(r'data-cost="[a-z_]+:(?P<field>[a-z_]+)"[^>]*>[^<]*</span>(?:\s|&nbsp;)*(?:<[^>]+>\s*)*all-in\b')


def _listed_all_ins(tree):
    """Every figure in an All-in column of the page's tables (the lodging-plus-tax totals it lists)."""
    out = set()
    for table in tree.find_all('table'):
        rows = [[c for c in tr.children if isinstance(c, Node) and c.tag in ('td', 'th')] for tr in table.find_all('tr')]
        heads = [c.text() for c in rows[0]] if rows else []
        cols = [i for i, h in enumerate(heads) if h.startswith('All-in')]
        for cells in rows[1:]:
            for i in cols:
                if i < len(cells):
                    out.update(int(v.replace(',', '')) for v in re.findall(r'\$([0-9][0-9,]*)', cells[i].text()))
    return out


def check_all_in_figures(root=REPO):
    """R2-2: on the North America and three-resort pages "all-in" is lodging plus tax, with lift tickets
    listed separately. Every figure called all-in must be one of the page's own all-in totals (or a
    rounded one where the sentence says roughly or about), a cost-model lodging_tax figure, or the
    budget line itself; a cost-model figure that includes passes may never be called all-in."""
    problems = []
    for name in ALL_IN_PAGES:
        text, tree = page(root, name)
        listed = _listed_all_ins(tree)
        for m in ALL_IN_SPAN.finditer(text):
            if m.group('field') != 'lodging_tax':
                problems.append(f'{name}: a {m.group("field")} figure, which includes lift passes, is called all-in')
        body = tree.text()
        for m in ALL_IN_FIGURE.finditer(body):
            before = body[max(0, m.start() - 40):m.start()]
            if re.search(r'(?:under|over|below|above|budget|cap of)\s*$', before):
                continue  # the budget line, not a priced figure
            if m.group('gap').strip() and m.group('gap').strip() not in ('for two',):
                continue
            rough = re.search(r'(?:roughly|about|around|~|≈)\s*$', before)
            tol = 50 if rough else 1
            for v in (m.group('x'), m.group('y')):
                if v is None:
                    continue
                n = int(v.replace(',', ''))
                if m.group('y') is not None and v == m.group('y') and n < 1000 and m.group('x'):
                    n = int(m.group('x').replace(',', '')) // 1000 * 1000 + n  # "$2,200–900" style
                if any(abs(n - x) <= tol for x in listed):
                    continue
                if _is_cost_lodging_tax(text, m, n):
                    continue
                problems.append(f'{name}: ${n:,} is called all-in but is not one of the page\'s lodging-plus-tax '
                                f'totals: {body[max(0, m.start() - 80):m.end() + 20]}')
    return problems


def _is_cost_lodging_tax(html_text, m, n):
    """True when the figure sits in a data-cost lodging_tax span somewhere on the page."""
    for s in re.finditer(r'data-cost="[a-z_]+:lodging_tax"[^>]*>([^<]*)<', html_text):
        vals = [int(v.replace(',', '')) for v in re.findall(r'([0-9][0-9,]{2,})', s.group(1))]
        if n in vals:
            return True
    return False


register('all-in-figures', check_all_in_figures)


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
    'R2-2': [(r'barely outside the stated budget',
              'on lodging and tax the January Zermatt week is inside the budget; passes are a separate column')],
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
    if not os.path.exists(os.path.join(root, 'data', 'readings.tsv')):
        problems.append('data/readings.tsv: no dated snapshot of the live readings')
    return problems


register('rolling-citations', check_rolling_citations)


# ---------------------------------------------------------------- R1-18: dates and expired advice

# The September 2026 pages' undated deadlines, all past by November 2026 (round 1, R1-18).
PAST_DEADLINE = re.compile(r'\bby 29 Sep\b(?! 20\d\d)|re-shop in October|closes today|runs to 21 Sep\b(?! 20\d\d)')
# An action with a full-dated deadline ("book by 29 Sep 2026", "cancel before 10 Dec 2026"), checked
# against --today rather than a fixed month list. A date in a heading or in history is not a deadline.
DATED_DEADLINE = re.compile(r'\b(?:book|reserve|buy|purchase|re-?shop|re-?read|lock in|decide|confirm|cancel|order|'
                            r'sign up|apply|check)\w*\b[^.;]{0,40}?\b(?:by|before|until) (\d{1,2}) '
                            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (20\d\d)\b', re.I)
MONTH_NUM = {m: i for i, m in enumerate(MONTHS.split('|'), 1)}


def _passed_deadline(s):
    for m in DATED_DEADLINE.finditer(s):
        if date(int(m.group(3)), MONTH_NUM[m.group(2)], int(m.group(1))) <= today():
            return True
    return bool(PAST_DEADLINE.search(s))
DONE_WORDS = re.compile(r'expired|has passed|have passed|ended|closed')


def latest_read(root=REPO):
    """The newest date any listing was read, from the recheck runs and the listing-page readings."""
    import recheck
    meta, rows = recheck.load(runs_dir=runs_dir(root))
    return max([r['read_date'] for r in rows] + [r['read_date'] for r in meta['_readings']])


def check_dates_stamped(root=REPO, latest=None):
    """R1-18: the index header and footer and the README date both research rounds; no deadline that
    has passed is offered as an action; no 'live quote' sentence is undated; the Zermatt season pass
    is not quoted at its October price. R2-7: the recheck date they must name is the newest read date
    in the data, not a fixed day, so a later recheck passes once the pages name it."""
    import recheck
    problems = []
    latest = latest or latest_read(root)
    want = recheck.long_date(latest)
    _, tree = page(root, 'index.html')
    header = next(tree.find_all('header'), None)
    footer = next(tree.find_all('footer'), None)
    for where, t in (('index.html header', header.text() if header else ''),
                     ('index.html footer', footer.text() if footer else ''),
                     ('README.md', read(root, 'README.md'))):
        if not ('September 2026' in t and want in t and 'recheck' in t):
            problems.append(f'{where}: does not date both research rounds (September, and the {want} recheck)')
    for name in PAGES:
        for s in sentences(page(root, name)[1].text()):
            if _passed_deadline(s) and not DONE_WORDS.search(s):
                problems.append(f'{name}: past deadline offered as an action: {s[:130]}')
            if re.search(r'live quote', s) and not re.search(rf'(?:{MONTHS})\w* \d{{4}}|\d{{1,2}} (?:{MONTHS})', s):
                problems.append(f'{name}: undated live quote: {s[:130]}')
    if 'from 1,750' in page(root, 'zermatt-month-stay-2026-27.html')[1].text():
        problems.append('zermatt-month-stay-2026-27.html: season pass quoted "from 1,750", its October price')
    return problems


register('dates-stamped', check_dates_stamped)


# ---------------------------------------------------------------- tax breakdowns sum to their totals

def check_tax_breakdowns(root=REPO):
    """A stated tax total equals the sum of the components the same sentence lists after it, as in
    'Telluride's rate is 17.22% ...: 2.9% state, 1% county, ...' or 'Add 16% ... tax (8% PST, 3% ..., 5% GST)'."""
    problems = []
    for name in PAGES:
        for s in sentences(page(root, name)[1].text()):
            if 'tax' not in s.lower():
                continue
            m = re.search(r'(\d+(?:\.\d+)?)%[^:()]{0,160}?(?::|\()\s*((?:\d+(?:\.\d+)?% [^,;)]+(?:,| and )\s*)+\d+(?:\.\d+)?% [^,;).]+)', s)
            if not m:
                continue
            total = float(m.group(1))
            parts = [float(x) for x in re.findall(r'(\d+(?:\.\d+)?)%', m.group(2))]
            if len(parts) >= 2 and abs(sum(parts) - total) > 0.005:
                problems.append(f'{name}: {total:g}% is stated, the listed parts sum to {sum(parts):g}%: {s[:120]}')
    return problems


register('tax-breakdowns', check_tax_breakdowns)


# ---------------------------------------------------------------- tallies on the index match the run

def check_tallies(root=REPO):
    """The index's recheck tally is the block tools/recheck.py generates from the readings, and every
    count in it reproduces from them: listing-weeks and listing-months apart (R2-14), bookable, not
    offered, removed, undetermined, and free in-unit washers."""
    import recheck
    meta, rows = recheck.load(runs_dir=runs_dir(root))
    c = recheck.counts(rows)
    weeks = sum(1 for r in rows if r['page'] != 'zermatt')
    free_in_unit = sum(1 for r in rows if r['status'] == 'BOOKABLE' and 'Free washer – In unit' in r['washer'])
    removed_listings = len({r['room_id'] for r in rows if r['status'] == 'REMOVED'})
    html_text, tree = page(root, 'index.html')
    problems = []
    if '<!-- recheck-tally:start -->' not in html_text:
        problems.append('index.html: the recheck tally is not the generated <!-- recheck-tally --> block')
    text = tree.text()
    want = [
        (f'Of the {weeks} listing-weeks and {c["n"] - weeks} listing-months', 'weeks and months apart'),
        (f'{c["BOOKABLE"]} were still bookable', 'bookable'),
        (f'{c["NOT_OFFERED"]} were not offered', 'not offered'),
        (f'{c["REMOVED"]} (from {removed_listings} listings) had been removed', 'removed'),
        (f'Of the {c["BOOKABLE"]}, only {free_in_unit} state a free washer', 'free in-unit washers'),
    ]
    problems += [f'index.html: the recheck tally should read "{s}" ({what}, from the readings)' for s, what in want
                 if s not in text]
    if c['NOT_DETERMINED'] and 'could not be determined' not in text:
        problems.append('index.html: the tally omits the rows the recheck could not determine')
    return problems


register('tallies', check_tallies)


# ---------------------------------------------------------------- registry and CLI

register('privacy', check_privacy)
register('anchors', check_anchors)
register('costs', check_costs)


def check_recheck_blocks(root=REPO):
    """R1-4: the recheck sections, header lines, nav links and banner match the latest run's data."""
    import recheck
    return recheck.check(root, runs_dir=runs_dir(root))


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
        elif a == '--today':
            set_today(args.pop(0))
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
