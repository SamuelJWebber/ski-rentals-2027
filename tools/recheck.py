"""Render the dated recheck sections of the four September pages from a recheck run in data/recheck/.

usage: python tools/recheck.py [RUN]          render data/recheck/RUN.json into the pages (default: latest run)
       python tools/recheck.py [RUN] --check  report blocks that differ from what the run would render

A run is RUN.json (dates, method text, pointers) plus RUN.tsv (one row per listing and stay). Every
date printed on the pages comes from the run's data: the September-listing tables carry the run date,
and the Zermatt fresh search and the Booking.com table each carry their own read date, so a later
run never relabels an older reading. Blocks are replaced between HTML comment markers by regex:

    <!-- recheck:start --> ... <!-- recheck:end -->              the section itself
    <!-- recheck-meta:start --> ... <!-- recheck-meta:end -->    the header line that cites the run
    <!-- recheck-nav:start --> ... <!-- recheck-nav:end -->      the navigation link text
    <!-- recheck-banner:start --> ... <!-- recheck-banner:end --> Zermatt's banner

so a rerun never depends on the exact old wording. Standard library only; nothing here fetches anything.
"""
import csv
import glob
import html
import io
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNS = os.path.join(REPO, 'data', 'recheck')

PAGES = {
    'alps': 'alps-extreme-ski-2027.html',
    'steep': 'steep-and-town-2027.html',
    'rentals': 'ski-rentals-2027.html',
    'zermatt': 'zermatt-month-stay-2026-27.html',
}
STYLE = {  # per page: table wrapper and status classes, as the pages' own CSS defines them
    'alps': dict(tw='tw', ok='tag g', part='tag w', no='tag r', plainwasher=True),
    'steep': dict(tw='wrap', ok='ok', part='part', no='no'),
    'rentals': dict(tw='wrap', ok='ok', part='part', no='no'),
    'zermatt': dict(tw='tbl', ok='ok', part='warn', no='bad'),
}
STATUS_TEXT = {'BOOKABLE': 'Bookable', 'NOT_OFFERED': 'Not offered for these dates',
               'REMOVED': 'Listing removed', 'NOT_DETERMINED': 'Not determined'}
MARKERS = ('recheck', 'recheck-meta', 'recheck-nav', 'recheck-banner')


# ---------------------------------------------------------------- dates

def long_date(iso):
    d = date.fromisoformat(iso)
    return f'{d.day} {d.strftime("%B")} {d.year}'


def short_date(iso):
    d = date.fromisoformat(iso)
    return f'{d.day} {d.strftime("%b")} {d.year}'


def day_month(iso):
    d = date.fromisoformat(iso)
    return f'{d.day} {d.strftime("%b")}'


def stay(cin, cout):
    a, b = date.fromisoformat(cin), date.fromisoformat(cout)
    ma, mb = a.strftime('%b'), b.strftime('%b')
    return f'{a.day} {ma}&ndash;{b.day} {mb}' if ma != mb else f'{a.day}&ndash;{b.day} {ma}'


# ---------------------------------------------------------------- loading

def latest_run():
    runs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(RUNS, '*.json')))
    if not runs:
        raise SystemExit('no recheck run in data/recheck/')
    return runs[-1]


def load(run=None, runs_dir=RUNS):
    run = run or latest_run()
    with open(os.path.join(runs_dir, run + '.json'), encoding='utf-8') as f:
        meta = json.load(f)
    with open(os.path.join(runs_dir, meta['rows']), encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))
    for r in rows:
        if r['status'] not in STATUS_TEXT:
            raise ValueError(f'unknown status {r["status"]!r} for {r["room_id"]}')
    meta['_dir'] = runs_dir
    meta['_checks'] = load_checks(meta)
    return meta, rows


def load_checks(meta):
    """Listing pages read by hand for this run (data/checks/<date>.tsv): {(room_id, check_in): row}."""
    rel = meta.get('checks')
    if not rel:
        return {}
    with open(os.path.join(meta['_dir'], rel), encoding='utf-8', newline='') as f:
        return {(r['room_id'], r['check_in']): r for r in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)}


def _read_rel(meta, rel):
    with open(os.path.join(meta['_dir'], rel), encoding='utf-8', newline='') as f:
        return f.read()


# ---------------------------------------------------------------- rendering

def washer_class(w):
    if re.search(r'In unit', w) and not re.search(r'NOT INCLUDED', w):
        return 'ok'
    if re.search(r'NOT INCLUDED|In building|Paid|none listed', w):
        return 'no'
    return 'part'


def change_cell(sep, now):
    """Change between the two published (whole-dollar) quotes, so the cell always matches them."""
    if not sep or not now:
        return '&mdash;'
    d = int(now) - int(sep)
    pct = d / int(sep) * 100
    sign = '+' if d >= 0 else '&minus;'
    return f'{sign}${abs(d):,} ({sign}{abs(pct):.0f}%)'


def refund_text(check):
    """Short form of a cancellation line read on the listing page."""
    if check is None:
        return 'not read'
    t = check['cancellation']
    if not t:
        return 'did not render'
    m = re.match(r'Free cancellation before ([A-Z][a-z]+) (\d{1,2})\b', t)
    if m:
        return f'free cancellation before {int(m.group(2))} {m.group(1)[:3]}'
    if t.startswith('Free cancellation for 24 hours'):
        return 'full refund only for 24 hours after booking'
    return html.escape(t)


def row_html(r, st, checks=None):
    link = (f'https://www.airbnb.com/rooms/{r["room_id"]}?check_in={r["check_in"]}&amp;check_out={r["check_out"]}'
            f'&amp;adults={r["adults"]}')
    name = html.escape(r['name'] or f'Listing {r["room_id"]}')
    if r['sept_label']:
        name += f'<br><span class="small">September label: {html.escape(r["sept_label"])}</span>'
    status = r['status']
    cls = {'BOOKABLE': st['ok'], 'NOT_OFFERED': st['no'], 'REMOVED': st['no'], 'NOT_DETERMINED': st['part']}[status]
    now = r['quote_usd'] if status == 'BOOKABLE' else ''
    now_txt = f'${int(now):,}' if now else '&mdash;'
    sep_txt = f'${int(r["sept_quote_usd"]):,}' if r['sept_quote_usd'] else '&mdash;'
    w = r['washer']
    w_txt = html.escape(w) if w else '&mdash;'
    wc = '' if st.get('plainwasher') else (washer_class(w) if w else st['part'])
    return (f'<tr><td><a href="{link}">{name}</a></td><td class="num">{stay(r["check_in"], r["check_out"])}</td>'
            f'<td class="num">{sep_txt}</td><td><span class="{cls}">{STATUS_TEXT[status]}</span></td>'
            f'<td class="num">{now_txt}</td><td class="num">{change_cell(r["sept_quote_usd"], now)}</td>'
            f'<td class="{wc}">{w_txt}</td>'
            + (f'<td>{refund_text(checks.get((r["room_id"], r["check_in"]))) if status == "BOOKABLE" else "&mdash;"}</td>'
               if checks else '')
            + f'<td class="num">{r["rating"]}</td></tr>')


def counts(rows):
    c = dict.fromkeys(STATUS_TEXT, 0)
    for r in rows:
        c[r['status']] += 1
    c['n'] = len(rows)
    return c


def sort_key(r):
    return ((r['name'] or r['room_id']), f'{r["check_in"]}..{r["check_out"]}')


def table_section(tag, rows, meta):
    """Heading, intro, table and method for one page's September listings."""
    st = STYLE[tag]
    run = meta['run_date']
    c = counts(rows)
    unit = 'listing-months' if tag == 'zermatt' else 'listing-weeks'
    head = f'Rechecked {long_date(run)}: {c["BOOKABLE"]} of {c["n"]} {unit} still bookable'
    checks = meta.get('_checks') or {}
    unid = meta.get('unidentified', {}).get(tag)
    intro = (f'Every Airbnb listing this page priced in September and identified by room ID was looked up again on '
             f'{short_date(run)} for the same dates and guests. {c["BOOKABLE"]} are still offered; {c["NOT_OFFERED"]} '
             'are not offered for those dates '
             'any more (booked, blocked, or a changed minimum stay)'
             + (f'; {c["REMOVED"]} listing{"s have" if c["REMOVED"] != 1 else " has"} been removed from Airbnb' if c['REMOVED'] else '')
             + (f'; for {c["NOT_DETERMINED"]} the check could not tell' if c['NOT_DETERMINED'] else '')
             + '. '
             + (f'{unid["count"]} more priced listings on this page have no room ID'
                + (f', {unid["note"]}' if unid.get('note') else '') + ', so they could not be rechecked. ' if unid else '')
             + f'Prices are Airbnb&rsquo;s total before taxes in US dollars, as in September. The washer column is the '
             f'listing&rsquo;s own amenity wording on {day_month(run)}; a bare &ldquo;Washer&rdquo; does not say where it '
             'is. '
             + (f'The refund column is the cancellation line on the listing page itself, read on {day_month(run)} for the '
                'listings the pages recommend; the others were not read.' if checks else
                'Cancellation terms were not re-read for these rows.'))
    note = meta.get('notes', {}).get(tag)
    if note:
        intro += ' ' + note
    thead = (f'<thead><tr><th>Listing</th><th>Dates</th><th>Sep quote</th><th>{day_month(run)}</th>'
             f'<th>{day_month(run)} quote</th><th>Change</th><th>Washer, per listing</th>'
             + (f'<th>Refund, read {day_month(run)}</th>' if checks else '') + '<th>Rating</th></tr></thead>')
    body = '\n'.join(row_html(r, st, checks) for r in sorted(rows, key=sort_key))
    table = f'<div class="{st["tw"]}"><table>\n{thead}\n<tbody>\n{body}\n</tbody></table></div>\n'
    method = f'<p class="small">{meta["method"]}</p>\n'
    return head, intro, table, method


def booking_html(meta):
    b = meta['booking']
    with open(os.path.join(meta['_dir'], b['rows']), encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))
    d = b['date']
    trs = []
    for r in rows:
        nc = f' class="{r["nov_cell_class"]}"' if r['nov_cell_class'] else ''
        cc = f' class="{r["cancel_class"]}"' if r['cancel_class'] else ''
        trs.append(f'<tr><td>{r["property_html"]}</td><td class="num">{r["dates"]}</td><td class="num">{r["september"]}</td>'
                   f'<td{nc}>{r["nov"]}</td><td{cc}>{r["cancellation"]}</td></tr>')
    return (f'<h3>Japan hotels on Booking.com, rechecked {long_date(d)}</h3>\n<p>{b["intro"]}</p>\n'
            f'<div class="wrap"><table>\n<thead><tr><th>Property</th><th>Dates</th><th>September</th><th>{short_date(d)}</th>'
            f'<th>Cancellation on {day_month(d)}</th></tr></thead>\n<tbody>\n' + '\n'.join(trs) + '\n</tbody></table></div>\n')


def render_block(tag, meta, rows):
    sel = [r for r in rows if r['page'] == tag]
    head, intro, table, method = table_section(tag, sel, meta)
    if tag == 'alps':
        return f'<h2 id="recheck">{head}</h2>\n<p>{intro}</p>\n{table}{method}'
    if tag == 'steep':
        return f'<section id="recheck">\n<h2>{head}</h2>\n<p>{intro}</p>\n{table}{method}</section>\n'
    if tag == 'rentals':
        return f'<section id="recheck">\n<h2>{head}</h2>\n<p>{intro}</p>\n{table}{method}{booking_html(meta)}</section>\n'
    if tag == 'zermatt':
        fresh = _read_rel(meta, meta['zermatt_fresh']['fragment'])
        head = head.replace('Rechecked ', 'The September listings, rechecked ', 1)
        return f'{fresh}<h3>{head}</h3>\n<p>{intro}</p>\n{table}{method}'
    raise ValueError(tag)


def render_small(tag, meta, rows):
    """{marker: text} for the header line, nav link and banner of one page."""
    run = meta['run_date']
    c = counts([r for r in rows if r['page'] == tag])
    out = {}
    if tag == 'alps':
        out['recheck-meta'] = f'listings rechecked {short_date(run)}, {c["BOOKABLE"]} of {c["n"]} listing-weeks still bookable'
        out['recheck-nav'] = f'Rechecked {short_date(run)}'
    elif tag in ('steep', 'rentals'):
        out['recheck-meta'] = f'listings rechecked {short_date(run)}'
        out['recheck-nav'] = f'Rechecked {day_month(run)}'
    elif tag == 'zermatt':
        z = meta['zermatt_fresh']
        out['recheck-banner'] = (f'<p class="note"><strong>Rechecked {short_date(z["date"])}.</strong> {z["banner"]} '
                                 '<a href="#fresh">See the recheck</a>.</p>\n')
    return out


NOTE = re.compile(r'(<span class="small recheck-note" data-room="(?P<room>\d+)"(?: data-label="(?P<label>[^"]*)")?>)'
                  r'(?P<body>[^<]*)(</span>)')


def note_text(room, label, tag, meta, rows):
    """The dated status line for one listing wherever a page cites it outside the recheck table."""
    sel = [r for r in rows if r['room_id'] == room and r['page'] == tag] or [r for r in rows if r['room_id'] == room]
    if not sel:
        return None
    checks = meta.get('_checks') or {}
    parts = []
    for r in sorted(sel, key=lambda r: r['check_in']):
        when = stay(r['check_in'], r['check_out'])
        if r['status'] == 'REMOVED':
            part = 'listing removed from Airbnb'
        elif r['status'] == 'NOT_OFFERED':
            part = f'not offered for {when}'
        elif r['status'] == 'NOT_DETERMINED':
            part = f'{when} could not be determined'
        else:
            part = f'bookable for {when} at ${int(r["quote_usd"]):,}'
            c = checks.get((r['room_id'], r['check_in']))
            if c and c['cancellation']:
                part += ', ' + refund_text(c)
        if part not in parts:
            parts.append(part)
    prefix = f'{html.escape(label)}, rechecked' if label else 'Rechecked'
    return f'{prefix} {short_date(meta["run_date"])}: ' + '; '.join(parts) + '.'


def fill_notes(text, tag, meta, rows):
    """Return (text with every recheck note refreshed, rooms cited in a note but absent from the run)."""
    missing = []

    def sub(m):
        t = note_text(m.group('room'), m.group('label'), tag, meta, rows)
        if t is None:
            missing.append(m.group('room'))
            return m.group(0)
        return m.group(1) + t + m.group(5)
    return NOTE.sub(sub, text), missing


def _sub_marker(text, name, body):
    start, end = f'<!-- {name}:start -->', f'<!-- {name}:end -->'
    pat = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    found = len(pat.findall(text))
    if found == 0:
        return text, False
    if name == 'recheck':
        repl = start + '\n' + body + end
    else:
        repl = start + body + end
    return pat.sub(lambda m: repl, text), True


def render_page(tag, text, meta, rows):
    """Return (new_text, missing_markers)."""
    missing = []
    text, ok = _sub_marker(text, 'recheck', render_block(tag, meta, rows))
    if not ok:
        missing.append('recheck')
    for name, body in render_small(tag, meta, rows).items():
        text, ok = _sub_marker(text, name, body)
        if not ok:
            missing.append(name)
    text, rooms = fill_notes(text, tag, meta, rows)
    missing += [f'recheck-note for room {r}' for r in rooms]
    return text, missing


def apply(root=REPO, run=None, runs_dir=RUNS):
    meta, rows = load(run, runs_dir)
    changed, problems = [], []
    for tag, name in PAGES.items():
        path = os.path.join(root, name)
        with io.open(path, encoding='utf-8', newline='') as f:
            text = f.read()
        new, missing = render_page(tag, text, meta, rows)
        problems += [f'{name}: no <!-- {m}:start --> marker' for m in missing]
        if new != text:
            with io.open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(new)
            changed.append(name)
    return changed, problems


def check(root=REPO, run=None, runs_dir=RUNS):
    meta, rows = load(run, runs_dir)
    problems = []
    for tag, name in PAGES.items():
        with io.open(os.path.join(root, name), encoding='utf-8', newline='') as f:
            text = f.read()
        new, missing = render_page(tag, text, meta, rows)
        problems += [f'{name}: no <!-- {m}:start --> marker' for m in missing]
        if new != text:
            problems.append(f'{name}: recheck blocks differ from run {meta["run_date"]}; run python tools/recheck.py')
    return problems


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    run = args[0] if args else None
    if '--check' in sys.argv:
        p = check(run=run)
        print('\n'.join(p) or 'recheck blocks match the run')
        sys.exit(1 if p else 0)
    changed, problems = apply(run=run)
    print('changed:', changed or 'nothing')
    if problems:
        print('\n'.join(problems))
        sys.exit(1)
