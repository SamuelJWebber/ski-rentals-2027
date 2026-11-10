"""One cost model for every "week for two" figure on the site.

usage: python tools/costs.py [--today YYYY-MM-DD]           rewrite the cost figures in the pages and README
       python tools/costs.py [--today YYYY-MM-DD] --check   report figures that do not match the data

A week for two = lodging (Airbnb total before tax) + lodging or tourist tax + two 6-day lift passes.
Pages carry the figures in elements marked data-cost="<row key>:<field>", where field is one of
lodging, tax, lodging_tax, passes, total. The full table sits between <!-- costs:start --> and
<!-- costs:end --> on index.html, the README answers table between <!-- answers:start --> and
<!-- answers:end -->, and the index header's refund-window line between <!-- refund-window:start -->
and <!-- refund-window:end -->.

Every row carries its stay dates, every lift-pass price the date it was quoted, and every refund line
comes from the newest listing-page reading in data/checks for the row's rooms and dates. A refund window
that has closed by --today (default: today) is printed as closed and the row's "Yes" is withdrawn until
the listing is read again (review finding R2-6). Standard library only.
"""
import html
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, 'data', 'costs.json')
PAGES = ['index.html', 'alps-extreme-ski-2027.html', 'steep-and-town-2027.html', 'ski-rentals-2027.html',
         'three-resorts-best-snow-2027.html', 'zermatt-month-stay-2026-27.html']
FIELDS = ('lodging', 'tax', 'lodging_tax', 'passes', 'total')
SPAN = re.compile(r'(<(?P<tag>[a-z0-9]+)\b[^>]*\bdata-cost="(?P<key>[a-z_]+):(?P<field>[a-z_]+)"[^>]*>)(?P<body>[^<]*)(</(?P=tag)>)')
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']


def data_path(root=REPO):
    """The cost data that belongs to the pages under root."""
    return os.path.join(root, 'data', 'costs.json')


def load(path=DATA):
    with open(path, encoding='utf-8') as f:
        model = json.load(f)
    for row in model['rows']:
        for k in ('check_in', 'check_out'):
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', row.get(k) or ''):
                raise ValueError(f'{row["key"]}: no {k} date, so its week and listing links cannot be dated')
        if not row['passes'].get('quoted'):
            raise ValueError(f'{row["key"]}: the lift-pass price has no quoted date')
    return model


def _half_up(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def compute(row, model):
    """Return {field: (low, high)} in USD (floats), or None where a part is unknown."""
    fx = model['fx']['per_usd']
    people, nights = row.get('people', model['people']), row.get('nights', model['nights'])
    out = dict.fromkeys(FIELDS)
    lod = row['lodging']['usd']
    passes = row['passes']
    p_rate = fx[passes['currency']]
    tt = 1 + passes.get('ticket_tax', 0) / 100
    out['passes'] = tuple(e * people * tt / p_rate for e in passes['each'])
    if lod is None:
        return out
    lo, hi = lod
    out['lodging'] = (float(lo), float(hi))
    tax = row['tax']
    if tax['kind'] == 'percent':
        out['tax'] = (lo * tax['amount'][0] / 100, hi * tax['amount'][1] / 100)
    elif tax['kind'] == 'per_person_night':
        rate = fx[tax['currency']]
        out['tax'] = tuple(a * people * nights / rate for a in tax['amount'])
    else:
        raise ValueError(f'unknown tax kind {tax["kind"]!r} in {row["key"]}')
    out['lodging_tax'] = (lo + out['tax'][0], hi + out['tax'][1])
    out['total'] = (out['lodging_tax'][0] + out['passes'][0], out['lodging_tax'][1] + out['passes'][1])
    return out


def fmt(pair):
    """(1626.3, 1648.8) -> '$1,626–1,649'; equal ends -> '$1,626'; None -> '—'."""
    if pair is None:
        return '—'
    lo, hi = _half_up(pair[0]), _half_up(pair[1])
    if lo == hi:
        return f'${lo:,}'
    return f'${lo:,}–{hi:,}'


def values(model):
    """{(key, field): formatted string} for every row and field. A pass price marked as a floor
    (a dynamic-pricing minimum) makes the passes and the total read 'from $X'."""
    out = {}
    for row in model['rows']:
        c = compute(row, model)
        floor = row['passes'].get('floor')
        for f in FIELDS:
            v = fmt(c[f])
            if floor and f in ('passes', 'total') and v != '—':
                v = 'from ' + v
            out[(row['key'], f)] = v
    return out


def _tax_label(row):
    t = row['tax']
    lo, hi = t['amount']
    if t['kind'] == 'percent':
        return f'{lo:g}%' if lo == hi else f'{lo:g}–{hi:g}%'
    cur = {'CHF': 'CHF ', 'EUR': '€', 'JPY': '¥', 'USD': '$'}[t['currency']]
    amt = f'{cur}{lo:,.2f}'.replace('.00', '') if lo == hi else f'{cur}{lo:,.2f}–{hi:,.2f}'.replace('.00', '')
    return f'{amt} per person per night'


def week_label(row):
    a, b = date.fromisoformat(row['check_in']), date.fromisoformat(row['check_out'])
    ma, mb = a.strftime('%b'), b.strftime('%b')
    if ma == mb:
        return f'{a.day}–{b.day} {ma} {b.year}'
    return f'{a.day} {ma}–{b.day} {mb} {b.year}'


def _room_links(row):
    links = []
    for rid in row['lodging'].get('rooms', []):
        q = f'?check_in={row["check_in"]}&amp;check_out={row["check_out"]}&amp;adults=2'
        links.append(f'<a href="https://www.airbnb.com/rooms/{rid}{q}">{rid}</a>')
    return ', '.join(links)


def short(d):
    return f'{d.day} {d.strftime("%b")} {d.year}'


# ---------------------------------------------------------------- refund windows from the readings

def load_readings(root=REPO):
    """The browser readings beside the pages (data/checks), newest last."""
    sys.path.insert(0, HERE)
    import recheck
    return recheck.load_readings(os.path.join(root, 'data', 'checks'))


def cutoff(line, check_in):
    """The date in 'Free cancellation before February 11.' for a stay starting check_in, or None."""
    m = re.match(r'Free cancellation before ([A-Z][a-z]+) (\d{1,2})\b', line or '')
    if not m or m.group(1) not in MONTHS:
        return None
    cin = date.fromisoformat(check_in)
    d = date(cin.year, MONTHS.index(m.group(1)) + 1, int(m.group(2)))
    return d if d <= cin else date(cin.year - 1, d.month, d.day)


def refund_state(row, readings):
    """What the newest listing-page readings for the row's rooms and dates say about cancellation:
    {'kind': 'date'|'hours'|'unrendered'|None, 'cutoff': date (the earliest across the rooms), 'read': iso}."""
    newest = {}
    for r in readings:
        if r['check_in'] == row['check_in'] and r['check_out'] == row['check_out'] and r['adults'] == '2':
            newest[r['room_id']] = r
    got = [newest[rid] for rid in row['lodging'].get('rooms', []) if rid in newest]
    if not got:
        return {'kind': None, 'cutoff': None, 'read': None, 'n': 0}
    read = max(r['read_date'] for r in got)
    cuts = [cutoff(r['cancellation'], row['check_in']) for r in got]
    if all(cuts):
        return {'kind': 'date', 'cutoff': min(cuts), 'read': read, 'n': len(got)}
    if any(re.match(r'Free cancellation for \d+ hours', r['cancellation'] or '') for r in got):
        return {'kind': 'hours', 'cutoff': None, 'read': read, 'n': len(got)}
    return {'kind': 'unrendered', 'cutoff': None, 'read': read, 'n': len(got)}


def refund_text(row, st, today):
    """The cost table's refund line, and whether the window has closed by today."""
    if st['kind'] is None:
        return row.get('refund', 'Not read'), False
    read = short(date.fromisoformat(st['read']))
    who = 'listings' if st['n'] > 1 else 'listing'
    if st['kind'] == 'date':
        c = st['cutoff']
        both = ' for both' if st['n'] == 2 else ''
        if today >= c:
            return (f'Refund window closed on {short(c)}: free cancellation was before {c.day} {c.strftime("%b")}{both} '
                    f'({who} read {read}); not refundable until re-read'), True
        return f'Free cancellation before {c.day} {c.strftime("%b")}{both} ({who} read {read})', False
    if st['kind'] == 'hours':
        return f'Full refund for 24 hours after booking only ({who} read {read})', False
    return f'Not read (the policy section did not render, {who} read {read})', False


def verdict(row, closed):
    if closed and row['fits'].startswith('Yes'):
        return 'Not known: its refund window has closed, so the listing needs reading again'
    return row['fits']


def render_table(model, today=None, readings=()):
    today = today or date.today()
    v = values(model)
    rows = []
    for row in model['rows']:
        k = row['key']
        lod = row['lodging']
        refund, closed = refund_text(row, refund_state(row, readings), today)
        lodging_cell = (f'<span data-cost="{k}:lodging">{v[(k, "lodging")]}</span>'
                        f'<br><span class="small">{html.escape(lod["basis"])}. Quoted {lod["quoted"]}; room {_room_links(row)}</span>')
        rows.append(
            '<tr>'
            f'<td><b>{html.escape(row["resort"])}</b><br><span class="small">{week_label(row)}</span></td>'
            f'<td class="num">{lodging_cell}</td>'
            f'<td class="num"><span data-cost="{k}:tax">{v[(k, "tax")]}</span><br><span class="small">{html.escape(_tax_label(row))}. {html.escape(row["tax"]["basis"])}</span></td>'
            f'<td class="num"><span data-cost="{k}:lodging_tax">{v[(k, "lodging_tax")]}</span></td>'
            f'<td class="num"><span data-cost="{k}:passes">{v[(k, "passes")]}</span><br><span class="small">{html.escape(row["passes"]["basis"])}. '
            f'Quoted {html.escape(row["passes"]["quoted"])}. {html.escape(row["passes"]["covered_by"])}</span></td>'
            f'<td class="num"><b><span data-cost="{k}:total">{v[(k, "total")]}</span></b></td>'
            f'<td>{html.escape(refund)}<br><span class="small">Washer: {html.escape(row["washer"])}</span></td>'
            f'<td>{html.escape(verdict(row, closed))}</td>'
            '</tr>')
    head = ('<thead><tr><th>Resort and week</th><th>Lodging for two, before tax</th><th>Tax</th>'
            '<th>Lodging and tax</th><th>Two 6-day passes</th><th>Week for two</th>'
            '<th>Refund and washer</th><th>Under $3,000 on lodging and tax, refundable, washer in the unit?</th></tr></thead>')
    return ('<div class="wrap"><table class="costs">\n' + head + '\n<tbody>\n' + '\n'.join(rows) + '\n</tbody></table></div>\n'
            f'<p class="meta">{html.escape(model["definition"])} Currency: {html.escape(model["fx"]["label"])}. '
            'Generated from <code>data/costs.json</code> and the listing-page reads in <code>data/checks</code> '
            'by <code>tools/costs.py</code>.</p>\n')


def render_refund_window(model, today=None, readings=()):
    """One sentence for the index header: when the refund windows were read and when the next one closes."""
    today = today or date.today()
    states = [refund_state(row, readings) for row in model['rows']]
    dated = [s for s in states if s['kind'] == 'date']
    if not dated:
        return 'No refund window is on record.'
    reads = sorted({s['read'] for s in dated})
    when = ' and '.join(short(date.fromisoformat(r)) for r in reads)
    open_ = sorted(s['cutoff'] for s in dated if s['cutoff'] > today)
    closed = [s for s in dated if s['cutoff'] <= today]
    if not open_:
        return (f'Every refund window in the cost table, read {when}, has closed; the answers need their listings '
                f'read again.')
    if closed:
        return (f'Refund windows read {when}: {len(closed)} in the cost table have closed, and the next closes on '
                f'{short(open_[0])}.')
    return f'Refund windows read {when}; the first in the cost table closes on {short(open_[0])}.'


def render_readme(model):
    v = values(model)
    out = ['| | Resort | Lodging for two + tax | Two 6-day passes | Week for two | Note |',
           '|---|---|---|---|---|---|']
    for row in model['rows']:
        if 'readme_note' not in row:
            continue
        k = row['key']
        out.append(f'| {row["region"]} | **{row["resort"]}** | {v[(k, "lodging_tax")]} | {v[(k, "passes")]} | '
                   f'{v[(k, "total")]} | {row["readme_note"]} |')
    out.append('')
    out.append(f'Week for two = lodging + tax + two adult 6-day lift passes; food and travel left out. Lodging priced '
               f'{model["as_of"]}; lift passes as dated in the cost table, mostly September 2026 estimates; converted at '
               'the 10–11 Sep 2026 rates. The US$3,000 budget is tested against lodging plus tax. Every component and its '
               'source is in the [cost table](https://samueljwebber.github.io/ski-rentals-2027/#costs), generated from '
               '`data/costs.json`.')
    return '\n'.join(out) + '\n'


def _replace_block(text, start, end, body, newline=True):
    pat = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    if not pat.search(text):
        return text, False
    return pat.sub(lambda m: start + ('\n' if newline else '') + body + end, text, count=1), True


def fill_spans(text, vals):
    def sub(m):
        key = (m.group('key'), m.group('field'))
        if key not in vals:
            return m.group(0)
        return m.group(1) + vals[key] + m.group(6)
    return SPAN.sub(sub, text)


def _render(root, model, today):
    readings = load_readings(root)
    return render_table(model, today, readings), render_refund_window(model, today, readings)


def apply(root=REPO, model=None, today=None):
    model = model or load(data_path(root))
    vals = values(model)
    table, window = _render(root, model, today)
    changed = []
    for name in PAGES:
        path = os.path.join(root, name)
        with open(path, encoding='utf-8', newline='') as f:
            text = f.read()
        new = text
        if name == 'index.html':
            new, _ = _replace_block(new, '<!-- costs:start -->', '<!-- costs:end -->', table)
            new, _ = _replace_block(new, '<!-- refund-window:start -->', '<!-- refund-window:end -->', window, False)
        new = fill_spans(new, vals)
        if new != text:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(new)
            changed.append(name)
    rp = os.path.join(root, 'README.md')
    with open(rp, encoding='utf-8', newline='') as f:
        text = f.read()
    new, _ = _replace_block(text, '<!-- answers:start -->', '<!-- answers:end -->', render_readme(model))
    if new != text:
        with open(rp, 'w', encoding='utf-8', newline='') as f:
            f.write(new)
        changed.append('README.md')
    return changed


def check(root=REPO, model=None, today=None):
    """Problems: a data-cost element whose text differs from the model, an unknown key, a missing
    generated block, or a generated block that is out of date (including a refund window that has
    closed since the table was written)."""
    model = model or load(data_path(root))
    vals = values(model)
    table, window = _render(root, model, today)
    problems = []
    for name in PAGES:
        with open(os.path.join(root, name), encoding='utf-8') as f:
            text = f.read()
        for m in SPAN.finditer(text):
            key = (m.group('key'), m.group('field'))
            line = text.count('\n', 0, m.start()) + 1
            if key not in vals:
                problems.append(f'{name}:{line}: data-cost="{key[0]}:{key[1]}" is not in data/costs.json')
            elif m.group('body') != vals[key]:
                problems.append(f'{name}:{line}: {key[0]}:{key[1]} shows {m.group("body")!r}, data gives {vals[key]!r}')
        if name == 'index.html':
            m = re.search(r'<!-- costs:start -->\n(.*?)<!-- costs:end -->', text, re.S)
            if not m:
                problems.append('index.html: no <!-- costs:start --> block')
            elif m.group(1) != table:
                problems.append('index.html: the cost table is out of date; run python tools/costs.py')
            m = re.search(r'<!-- refund-window:start -->(.*?)<!-- refund-window:end -->', text, re.S)
            if not m:
                problems.append('index.html: no <!-- refund-window:start --> line in the header')
            elif m.group(1) != window:
                problems.append(f'index.html: the refund-window line is out of date ({window!r}); run python tools/costs.py')
    with open(os.path.join(root, 'README.md'), encoding='utf-8') as f:
        readme = f.read()
    m = re.search(r'<!-- answers:start -->\n(.*?)<!-- answers:end -->', readme, re.S)
    if not m:
        problems.append('README.md: no <!-- answers:start --> block')
    elif m.group(1) != render_readme(model):
        problems.append('README.md: the answers table is out of date; run python tools/costs.py')
    return problems


def _today(argv):
    if '--today' in argv:
        return date.fromisoformat(argv[argv.index('--today') + 1])
    return None


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--check' in sys.argv:
        p = check(today=_today(sys.argv))
        print('\n'.join(p) or 'cost figures match data/costs.json')
        sys.exit(1 if p else 0)
    print('changed:', apply(today=_today(sys.argv)) or 'nothing')
