"""One cost model for every "week for two" figure on the site.

usage: python tools/costs.py            rewrite the cost figures in the pages and README from data/costs.json
       python tools/costs.py --check    report figures that do not match the data, change nothing

A week for two = lodging (Airbnb total before tax) + lodging or tourist tax + two 6-day lift passes.
Pages carry the figures in elements marked data-cost="<row key>:<field>", where field is one of
lodging, tax, lodging_tax, passes, total. The full table sits between <!-- costs:start --> and
<!-- costs:end --> on index.html, and the README answers table between <!-- answers:start --> and
<!-- answers:end -->. Standard library only.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, 'data', 'costs.json')
PAGES = ['index.html', 'alps-extreme-ski-2027.html', 'steep-and-town-2027.html', 'ski-rentals-2027.html',
         'three-resorts-best-snow-2027.html', 'zermatt-month-stay-2026-27.html']
FIELDS = ('lodging', 'tax', 'lodging_tax', 'passes', 'total')
SPAN = re.compile(r'(<(?P<tag>[a-z0-9]+)\b[^>]*\bdata-cost="(?P<key>[a-z_]+):(?P<field>[a-z_]+)"[^>]*>)(?P<body>[^<]*)(</(?P=tag)>)')


def load(path=DATA):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


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
    if t['kind'] == 'percent':
        a = t['amount'][0]
        return f'{a:g}%'
    cur = {'CHF': 'CHF ', 'EUR': '€', 'JPY': '¥', 'USD': '$'}[t['currency']]
    lo, hi = t['amount']
    amt = f'{cur}{lo:,.2f}'.replace('.00', '') if lo == hi else f'{cur}{lo:,.2f}–{hi:,.2f}'.replace('.00', '')
    return f'{amt} per person per night'


def _room_links(row):
    weeks = {'9–16 Jan 2027': ('2027-01-09', '2027-01-16'), '16–23 Jan 2027': ('2027-01-16', '2027-01-23'),
             '23–30 Jan 2027': ('2027-01-23', '2027-01-30'), '6–13 Mar 2027': ('2027-03-06', '2027-03-13'),
             '13–20 Mar 2027': ('2027-03-13', '2027-03-20')}
    cin, cout = weeks.get(row['week'], (None, None))
    links = []
    for rid in row['lodging'].get('rooms', []):
        q = f'?check_in={cin}&amp;check_out={cout}&amp;adults=2' if cin else ''
        links.append(f'<a href="https://www.airbnb.com/rooms/{rid}{q}">{rid}</a>')
    return ', '.join(links)


def render_table(model):
    v = values(model)
    rows = []
    for row in model['rows']:
        k = row['key']
        lod = row['lodging']
        lodging_cell = (f'<span data-cost="{k}:lodging">{v[(k, "lodging")]}</span>'
                        f'<br><span class="small">{html.escape(lod["basis"])}. Quoted {lod["quoted"]}; room {_room_links(row)}</span>')
        rows.append(
            '<tr>'
            f'<td><b>{html.escape(row["resort"])}</b><br><span class="small">{row["week"]}</span></td>'
            f'<td class="num">{lodging_cell}</td>'
            f'<td class="num"><span data-cost="{k}:tax">{v[(k, "tax")]}</span><br><span class="small">{html.escape(_tax_label(row))}. {html.escape(row["tax"]["basis"])}</span></td>'
            f'<td class="num"><span data-cost="{k}:lodging_tax">{v[(k, "lodging_tax")]}</span></td>'
            f'<td class="num"><span data-cost="{k}:passes">{v[(k, "passes")]}</span><br><span class="small">{html.escape(row["passes"]["basis"])}. {html.escape(row["passes"]["covered_by"])}</span></td>'
            f'<td class="num"><b><span data-cost="{k}:total">{v[(k, "total")]}</span></b></td>'
            f'<td>{html.escape(row["refund"])}<br><span class="small">Washer: {html.escape(row["washer"])}</span></td>'
            f'<td>{html.escape(row["fits"])}</td>'
            '</tr>')
    head = ('<thead><tr><th>Resort and week</th><th>Lodging for two, before tax</th><th>Tax</th>'
            '<th>Lodging and tax</th><th>Two 6-day passes</th><th>Week for two</th>'
            '<th>Refund and washer</th><th>Under $3,000 on lodging and tax, refundable, washer in the unit?</th></tr></thead>')
    return ('<div class="wrap"><table class="costs">\n' + head + '\n<tbody>\n' + '\n'.join(rows) + '\n</tbody></table></div>\n'
            f'<p class="meta">{html.escape(model["definition"])} Currency: {html.escape(model["fx"]["label"])}. '
            'Generated from <code>data/costs.json</code> by <code>tools/costs.py</code>.</p>\n')


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
    out.append(f'Week for two = lodging + tax + two adult 6-day lift passes, priced {model["as_of"]}; food and travel '
               'left out. The US$3,000 budget is tested against lodging plus tax. Every component and its source is '
               'in the [cost table](https://samueljwebber.github.io/ski-rentals-2027/#costs), generated from '
               '`data/costs.json`.')
    return '\n'.join(out) + '\n'


def _replace_block(text, start, end, body):
    pat = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    if not pat.search(text):
        return text, False
    return pat.sub(lambda m: start + '\n' + body + end, text, count=1), True


def fill_spans(text, vals):
    def sub(m):
        key = (m.group('key'), m.group('field'))
        if key not in vals:
            return m.group(0)
        return m.group(1) + vals[key] + m.group(6)
    return SPAN.sub(sub, text)


def data_path(root=REPO):
    """The cost data that belongs to the pages under root."""
    return os.path.join(root, 'data', 'costs.json')


def apply(root=REPO, model=None):
    model = model or load(data_path(root))
    vals = values(model)
    changed = []
    for name in PAGES:
        path = os.path.join(root, name)
        with open(path, encoding='utf-8', newline='') as f:
            text = f.read()
        new = text
        if name == 'index.html':
            new, _ = _replace_block(new, '<!-- costs:start -->', '<!-- costs:end -->', render_table(model))
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


def check(root=REPO, model=None):
    """Problems: a data-cost element whose text differs from the model, an unknown key, a missing
    generated block, or a generated block that is out of date."""
    model = model or load(data_path(root))
    vals = values(model)
    problems = []
    seen_keys = set()
    for name in PAGES:
        with open(os.path.join(root, name), encoding='utf-8') as f:
            text = f.read()
        for m in SPAN.finditer(text):
            key = (m.group('key'), m.group('field'))
            seen_keys.add(m.group('key'))
            line = text.count('\n', 0, m.start()) + 1
            if key not in vals:
                problems.append(f'{name}:{line}: data-cost="{key[0]}:{key[1]}" is not in data/costs.json')
            elif m.group('body') != vals[key]:
                problems.append(f'{name}:{line}: {key[0]}:{key[1]} shows {m.group("body")!r}, data gives {vals[key]!r}')
        if name == 'index.html':
            m = re.search(r'<!-- costs:start -->\n(.*?)<!-- costs:end -->', text, re.S)
            if not m:
                problems.append('index.html: no <!-- costs:start --> block')
            elif m.group(1) != render_table(model):
                problems.append('index.html: the cost table is out of date; run python tools/costs.py')
    with open(os.path.join(root, 'README.md'), encoding='utf-8') as f:
        readme = f.read()
    m = re.search(r'<!-- answers:start -->\n(.*?)<!-- answers:end -->', readme, re.S)
    if not m:
        problems.append('README.md: no <!-- answers:start --> block')
    elif m.group(1) != render_readme(model):
        problems.append('README.md: the answers table is out of date; run python tools/costs.py')
    return problems


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--check' in sys.argv:
        p = check()
        print('\n'.join(p) or 'cost figures match data/costs.json')
        sys.exit(1 if p else 0)
    print('changed:', apply() or 'nothing')
