"""Render the dated recheck sections of the four September pages, and the index tally, from dated readings.

usage: python tools/recheck.py [DATE]          render every reading up to DATE (default: all) into the pages
       python tools/recheck.py [DATE] --check  report blocks that differ from what the readings would render

Readings come from two places, and every reading keeps its own date:

    data/recheck/<date>.json + .tsv   a recheck run: one row per September listing and stay (page, room,
                                      dates, status, quote, washer wording), all read on the run's date by
                                      the method the .json states;
    data/checks/<date>.tsv            listing pages read one at a time in a browser (tools/log_read.py).

For every (page, room, stay) the newest reading wins, and a browser read of the listing page beats a run
on the same day. Older readings keep their own date, so a partial re-read never drops a row and never
relabels a row nobody re-read: each table row prints the date it was last read, and a heading that covers
several dates says how many rows each date holds. The Zermatt fresh search and the Booking.com table carry
their own read dates from the run that holds them. Blocks are replaced between HTML comment markers:

    <!-- recheck:start --> ... <!-- recheck:end -->              the section itself
    <!-- recheck-meta:start --> ... <!-- recheck-meta:end -->    the header line that cites the recheck
    <!-- recheck-nav:start --> ... <!-- recheck-nav:end -->      the navigation link text
    <!-- recheck-banner:start --> ... <!-- recheck-banner:end --> Zermatt's banner
    <!-- recheck-tally:start --> ... <!-- recheck-tally:end -->  the index's tally of every recheck

so a rerun never depends on the exact old wording. Nothing is written unless every page renders without
a problem. Standard library only; nothing here fetches anything.
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
INDEX = 'index.html'
STYLE = {  # per page: table wrapper and status classes, as the pages' own CSS defines them
    'alps': dict(tw='tw', ok='tag g', part='tag w', no='tag r', plainwasher=True),
    'steep': dict(tw='wrap', ok='ok', part='part', no='no'),
    'rentals': dict(tw='wrap', ok='ok', part='part', no='no'),
    'zermatt': dict(tw='tbl', ok='ok', part='warn', no='bad'),
}
STATUS_TEXT = {'BOOKABLE': 'Bookable', 'NOT_OFFERED': 'Not offered for these dates',
               'REMOVED': 'Listing removed', 'NOT_DETERMINED': 'Not determined'}
MARKERS = ('recheck', 'recheck-meta', 'recheck-nav', 'recheck-banner', 'recheck-tally')
BROWSER_METHOD = ('Rows marked as read in a browser were opened one at a time on the listing page itself, '
                  'at human pace, with the stay&rsquo;s dates and guests in the address; the status is what the '
                  'page showed (a price for the stay, or &ldquo;Those dates are not available&rdquo;).')


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


WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']


def number(n):
    """Small counts in words, as the pages write them; larger ones in figures."""
    return WORDS[n] if 0 <= n < len(WORDS) else f'{n:,}'


def and_list(items):
    items = list(items)
    if len(items) <= 1:
        return ''.join(items)
    return ', '.join(items[:-1]) + ' and ' + items[-1]


# ---------------------------------------------------------------- loading

def _read_tsv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))


def run_dates(runs_dir=RUNS):
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(runs_dir, '*.json'))
                  if re.fullmatch(r'\d{4}-\d{2}-\d{2}', os.path.basename(p)[:-5]))


def latest_run(runs_dir=RUNS):
    runs = run_dates(runs_dir)
    if not runs:
        raise SystemExit('no recheck run in data/recheck/')
    return runs[-1]


def load_run(run, runs_dir=RUNS):
    """One run: its meta and its rows, each row stamped with the run's date."""
    with open(os.path.join(runs_dir, run + '.json'), encoding='utf-8') as f:
        meta = json.load(f)
    rows = _read_tsv(os.path.join(runs_dir, meta['rows']))
    for r in rows:
        if r['status'] not in STATUS_TEXT:
            raise ValueError(f'unknown status {r["status"]!r} for {r["room_id"]}')
        r['read_date'] = meta['run_date']
        r['source'] = 'run'
        r['adults'] = r.get('adults') or '2'
    meta['_dir'] = runs_dir
    meta['_rows'] = rows
    return meta


def load_readings(checks_dir, extra_files=(), until=None):
    """Every browser reading in checks_dir/*.tsv (plus any extra files), oldest first, stable within a day."""
    paths = sorted(glob.glob(os.path.join(checks_dir, '*.tsv'))) if checks_dir and os.path.isdir(checks_dir) else []
    for p in extra_files:
        if p and os.path.exists(p) and os.path.abspath(p) not in {os.path.abspath(q) for q in paths}:
            paths.append(p)
    out = []
    for path in paths:
        for r in _read_tsv(path):
            if r['status'] not in STATUS_TEXT:
                raise ValueError(f'{os.path.basename(path)}: unknown status {r["status"]!r} for {r["room_id"]}')
            if until and r['read_date'] > until:
                continue
            r['adults'] = r.get('adults') or '2'
            r['source'] = 'browser'
            out.append(r)
    out.sort(key=lambda r: r['read_date'])  # stable: file order within a day
    return out


def stay_key(r):
    return (r['room_id'], r['check_in'], r['check_out'], r['adults'])


def merge(metas, readings):
    """Table rows: the union of every run's rows, each carrying its newest reading and its own date."""
    table = {}
    for meta in metas:  # oldest run first, so a newer run's reading replaces an older one
        for r in meta['_rows']:
            key = (r['page'],) + stay_key(r)
            prev = table.get(key)
            row = dict(r)
            row['washer_date'] = r['read_date'] if r.get('washer') else (prev or {}).get('washer_date', '')
            if prev and not r.get('washer'):
                row['washer'] = prev.get('washer', '')
            table[key] = row
    newest, refunds = {}, {}
    for c in readings:  # oldest first, so the last one seen for a stay is the newest
        newest[stay_key(c)] = c
        if c.get('cancellation') and c['status'] == 'BOOKABLE':
            refunds[stay_key(c)] = c
    rows = []
    for key, row in table.items():
        c = newest.get(key[1:])
        if c is not None and c['read_date'] >= row['read_date']:
            row.update(status=c['status'], read_date=c['read_date'], source='browser',
                       quote_usd=c.get('total_usd', '') if c['status'] == 'BOOKABLE' else '')
        if row['status'] != 'BOOKABLE':
            row['quote_usd'] = ''
        f = refunds.get(key[1:])
        row['refund'], row['refund_date'] = (f['cancellation'], f['read_date']) if f else ('', '')
        row['read_any'] = c is not None  # some listing page was read for this stay
        if c is not None and not f and row['status'] == 'BOOKABLE' and c['read_date'] == row['read_date']:
            row['refund_date'] = c['read_date']  # read, but the cancellation line did not render
        rows.append(row)
    return rows


def load(run=None, runs_dir=RUNS, checks_dir=None):
    """Merge every run up to `run` (default: all of them) with every browser reading up to the same date.
    Returns (meta, rows): the newest run's meta, extended with '_runs' (every run's meta, oldest first),
    '_readings' (the browser readings) and '_dates' (the read dates the table rows carry)."""
    dates = run_dates(runs_dir)
    if run:
        dates = [d for d in dates if d <= run]
    if not dates:
        raise SystemExit('no recheck run in ' + runs_dir)
    metas = [load_run(d, runs_dir) for d in dates]
    meta = dict(metas[-1])
    if checks_dir is None:
        checks_dir = os.path.join(os.path.dirname(os.path.abspath(runs_dir)), 'checks')
    extra = [os.path.join(m['_dir'], m['checks']) for m in metas if m.get('checks')]
    readings = load_readings(checks_dir, extra, until=run)
    rows = merge(metas, readings)
    meta['_runs'] = metas
    meta['_readings'] = readings
    meta['_dates'] = sorted({r['read_date'] for r in rows})
    return meta, rows


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


def refund_text(line):
    """Short form of a cancellation line read on the listing page."""
    if line is None:
        return 'not read'
    t = line
    if not t:
        return 'did not render'
    m = re.match(r'Free cancellation before ([A-Z][a-z]+) (\d{1,2})\b', t)
    if m:
        return f'free cancellation before {int(m.group(2))} {m.group(1)[:3]}'
    m = re.match(r'Free cancellation for (\d+) hours', t)
    if m:
        return f'full refund only for {m.group(1)} hours after booking'
    return html.escape(t)


def _refund_cell(r):
    if r['status'] != 'BOOKABLE':
        return '&mdash;'
    if r['refund']:
        txt = refund_text(r['refund'])
        if r['refund_date'] != r['read_date']:
            txt += f' <span class="small">(read {day_month(r["refund_date"])})</span>'
        return txt
    return refund_text('' if r.get('refund_date') else None)


def row_html(r, st, refunds=False):
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
    if w and r.get('washer_date') and r['washer_date'] != r['read_date']:
        w_txt += f' <span class="small">({day_month(r["washer_date"])})</span>'
    wc = '' if st.get('plainwasher') else (washer_class(w) if w else st['part'])
    how = ' <span class="small">(listing page)</span>' if r['source'] == 'browser' else ''
    return (f'<tr><td><a href="{link}">{name}</a></td><td class="num">{stay(r["check_in"], r["check_out"])}</td>'
            f'<td class="num">{sep_txt}</td><td class="num">{day_month(r["read_date"])}{how}</td>'
            f'<td><span class="{cls}">{STATUS_TEXT[status]}</span></td>'
            f'<td class="num">{now_txt}</td><td class="num">{change_cell(r["sept_quote_usd"], now)}</td>'
            f'<td class="{wc}">{w_txt}</td>'
            + (f'<td>{_refund_cell(r)}</td>' if refunds else '')
            + f'<td class="num">{r["rating"]}</td></tr>')


def counts(rows):
    c = dict.fromkeys(STATUS_TEXT, 0)
    for r in rows:
        c[r['status']] += 1
    c['n'] = len(rows)
    return c


def by_date(rows):
    """[(read_date, count)], newest first."""
    out = {}
    for r in rows:
        out[r['read_date']] = out.get(r['read_date'], 0) + 1
    return sorted(out.items(), reverse=True)


def sort_key(r):
    return ((r['name'] or r['room_id']), f'{r["check_in"]}..{r["check_out"]}')


def heading(rows, unit):
    c = counts(rows)
    dates = by_date(rows)
    if len(dates) == 1:
        return f'Rechecked {long_date(dates[0][0])}: {c["BOOKABLE"]} of {c["n"]} {unit} still bookable'
    split = '; '.join(f'{n} read {short_date(d)}' if i == 0 else f'{n} as read {short_date(d)}'
                      for i, (d, n) in enumerate(dates))
    return (f'Rechecked {and_list(short_date(d) for d, _ in reversed(dates))}: {c["BOOKABLE"]} of {c["n"]} {unit} '
            f'bookable as last read ({split})')


def table_section(tag, rows, meta):
    """Heading, intro, table and method for one page's September listings."""
    st = STYLE[tag]
    c = counts(rows)
    unit = 'listing-months' if tag == 'zermatt' else 'listing-weeks'
    head = heading(rows, unit)
    dates = by_date(rows)
    first = dates[-1][0]
    refunds = any(r['refund'] or r['refund_date'] for r in rows)
    unid = meta.get('unidentified', {}).get(tag)
    intro = (f'Every Airbnb listing this page priced in September and identified by room ID was looked up again on '
             f'{short_date(first)} for the same dates and guests')
    if len(dates) > 1:
        intro += ('; ' + and_list(f'{n} of them again on {short_date(d)}' for d, n in dates[:-1])
                  + ', and the Read column gives the date each row was last read')
    intro += (f'. {c["BOOKABLE"]} are {"still offered" if len(dates) == 1 else "offered as last read"}; '
              f'{c["NOT_OFFERED"]} are not offered for those dates '
              'any more (booked, blocked, or a changed minimum stay)'
              + (f'; {c["REMOVED"]} listing{"s have" if c["REMOVED"] != 1 else " has"} been removed from Airbnb' if c['REMOVED'] else '')
              + (f'; for {c["NOT_DETERMINED"]} the check could not tell' if c['NOT_DETERMINED'] else '')
              + '. '
              + (f'{unid["count"]} more priced listings on this page have no room ID'
                 + (f', {unid["note"]}' if unid.get('note') else '') + ', so they could not be rechecked. ' if unid else '')
              + 'Prices are Airbnb&rsquo;s total before taxes in US dollars, as in September. The washer column is the '
              'listing&rsquo;s own amenity wording as the run read it; a bare &ldquo;Washer&rdquo; does not say where it '
              'is. '
              + ('The refund column is the cancellation line on the listing page itself, for the listings the pages '
                 'recommend; the others were not read.' if refunds else
                 'Cancellation terms were not re-read for these rows.'))
    note = meta.get('notes', {}).get(tag)
    if note:
        intro += ' ' + note
    thead = ('<thead><tr><th>Listing</th><th>Dates</th><th>Sep quote</th><th>Read</th><th>Status</th>'
             '<th>Quote</th><th>Change</th><th>Washer, per listing</th>'
             + ('<th>Refund</th>' if refunds else '') + '<th>Rating</th></tr></thead>')
    body = '\n'.join(row_html(r, st, refunds) for r in sorted(rows, key=sort_key))
    table = f'<div class="{st["tw"]}"><table>\n{thead}\n<tbody>\n{body}\n</tbody></table></div>\n'
    return head, intro, table, method_html(meta, rows)


def method_html(meta, rows):
    """The method of every source that holds a row of this table, dated where there are several."""
    runs = sorted({r['read_date'] for r in rows if r['source'] == 'run'})
    by_run = {m['run_date']: m for m in meta['_runs']}
    parts = []
    for d in runs:
        text = by_run[d]['method']
        parts.append(text if len(runs) == 1 else f'Run of {short_date(d)}. {text}')
    if any(r['source'] == 'browser' for r in rows):
        parts.append(BROWSER_METHOD)
    return '<p class="small">' + ' '.join(parts) + '</p>\n'


def booking_html(meta):
    b = meta['booking']
    rows = _read_tsv(os.path.join(meta['_dir'], b['rows']))
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


def _dates_phrase(rows):
    return and_list(short_date(d) for d, _ in reversed(by_date(rows)))


def render_small(tag, meta, rows):
    """{marker: text} for the header line, nav link and banner of one page."""
    sel = [r for r in rows if r['page'] == tag]
    c = counts(sel)
    latest = by_date(sel)[0][0]
    out = {}
    if tag == 'alps':
        still = 'still bookable' if len(by_date(sel)) == 1 else 'bookable as last read'
        out['recheck-meta'] = f'listings rechecked {_dates_phrase(sel)}, {c["BOOKABLE"]} of {c["n"]} listing-weeks {still}'
        out['recheck-nav'] = f'Rechecked {short_date(latest)}'
    elif tag in ('steep', 'rentals'):
        out['recheck-meta'] = f'listings rechecked {_dates_phrase(sel)}'
        out['recheck-nav'] = f'Rechecked {day_month(latest)}'
    elif tag == 'zermatt':
        z = meta['zermatt_fresh']
        out['recheck-banner'] = (f'<p class="note"><strong>Rechecked {short_date(z["date"])}.</strong> {z["banner"]} '
                                 '<a href="#fresh">See the recheck</a>.</p>\n')
    return out


def render_tally(meta, rows):
    """The index's one-paragraph tally of every recheck table."""
    c = counts(rows)
    weeks = sum(1 for r in rows if r['page'] != 'zermatt')
    months = c['n'] - weeks
    bookable = [r for r in rows if r['status'] == 'BOOKABLE']
    free_in_unit = sum(1 for r in bookable if 'Free washer – In unit' in r['washer'])
    removed_listings = len({r['room_id'] for r in rows if r['status'] == 'REMOVED'})
    browser_no = sum(1 for r in rows if r['status'] == 'NOT_OFFERED' and r['source'] == 'browser')
    dates = by_date(rows)
    when = (f'on {long_date(dates[0][0])[:-5]}' if len(dates) == 1 else
            'as last read (' + '; '.join(f'{n} rows read {short_date(d)}' for d, n in dates) + ')')
    unid = meta.get('unidentified', {}).get('steep')
    text = (f'Of the {weeks} listing-weeks and {months} listing-months the detailed pages identified by room ID, '
            f'{c["BOOKABLE"]} were still bookable {when}, {c["NOT_OFFERED"]} were not offered for those dates'
            + (f' ({number(browser_no)} of them read on the listing page itself)' if browser_no else '')
            + (f', {c["NOT_DETERMINED"]} could not be determined' if c['NOT_DETERMINED'] else '')
            + f' and {c["REMOVED"]} (from {removed_listings} listings) had been removed.'
            + (f' Another {unid["count"]} priced listings on the North America and Japan page, '
               f'{unid.get("note", "")}, carry no room ID and could not be rechecked.' if unid else '')
            + f' Of the {c["BOOKABLE"]}, only {free_in_unit} state a free washer inside the unit.')
    return text


NOTE = re.compile(r'(<span class="small recheck-note" data-room="(?P<room>\d+)"(?: data-label="(?P<label>[^"]*)")?>)'
                  r'(?P<body>[^<]*)(</span>)')


def _note_part(r):
    when = stay(r['check_in'], r['check_out'])
    if r['status'] == 'REMOVED':
        return 'listing removed from Airbnb'
    if r['status'] == 'NOT_OFFERED':
        return f'not offered for {when}'
    if r['status'] == 'NOT_DETERMINED':
        return f'{when} could not be determined'
    q = r.get('quote_usd') or r.get('total_usd')
    part = f'bookable for {when} at ${int(q):,}'
    line = r.get('refund') if 'refund' in r else r.get('cancellation')
    if line:
        part += ', ' + refund_text(line)
    return part


def note_text(room, label, tag, meta, rows):
    """The dated status line for one listing wherever a page cites it outside the recheck table: the
    rows of this page's table for that room, else any table's, else the browser readings of the room."""
    sel = [r for r in rows if r['room_id'] == room and r['page'] == tag] or [r for r in rows if r['room_id'] == room]
    if not sel:
        newest = {}
        for c in meta.get('_readings', []):
            if c['room_id'] == room:
                newest[stay_key(c)] = c
        sel = list(newest.values())
    if not sel:
        return None
    parts, dates = [], []
    for r in sorted(sel, key=lambda r: r['check_in']):
        p = _note_part(r)
        if (p, r['read_date']) not in parts:
            parts.append((p, r['read_date']))
            dates.append(r['read_date'])
    prefix = f'{html.escape(label)}, rechecked' if label else 'Rechecked'
    if len(set(dates)) == 1:
        seen = []
        for p, _ in parts:
            if p not in seen:
                seen.append(p)
        return f'{prefix} {short_date(dates[0])}: ' + '; '.join(seen) + '.'
    return f'{prefix}: ' + '; '.join(f'{p} (read {short_date(d)})' for p, d in parts) + '.'


def fill_notes(text, tag, meta, rows):
    """Return (text with every recheck note refreshed, rooms cited in a note that no reading has)."""
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
    """Return (new_text, problems) for one page."""
    problems = []
    if tag == 'index':
        text, ok = _sub_marker(text, 'recheck-tally', render_tally(meta, rows))
        if not ok:
            problems.append('no <!-- recheck-tally:start --> marker')
        return text, problems
    text, ok = _sub_marker(text, 'recheck', render_block(tag, meta, rows))
    if not ok:
        problems.append('no <!-- recheck:start --> marker')
    for name, body in render_small(tag, meta, rows).items():
        text, ok = _sub_marker(text, name, body)
        if not ok:
            problems.append(f'no <!-- {name}:start --> marker')
    text, rooms = fill_notes(text, tag, meta, rows)
    problems += [f'listing {r} is cited in a recheck note, but no run or browser reading has it' for r in rooms]
    return text, problems


def _targets():
    return list(PAGES.items()) + [('index', INDEX)]


def render_all(root=REPO, run=None, runs_dir=RUNS, checks_dir=None):
    """{file name: (old text, new text)} and the problems, without writing anything."""
    meta, rows = load(run, runs_dir, checks_dir)
    out, problems = {}, []
    for tag, name in _targets():
        with io.open(os.path.join(root, name), encoding='utf-8', newline='') as f:
            text = f.read()
        new, p = render_page(tag, text, meta, rows)
        problems += [f'{name}: {x}' for x in p]
        out[name] = (text, new)
    return meta, out, problems


def apply(root=REPO, run=None, runs_dir=RUNS, checks_dir=None):
    """Write every page whose blocks change, but only when no page has a problem."""
    _, out, problems = render_all(root, run, runs_dir, checks_dir)
    if problems:
        return [], problems
    changed = []
    for name, (old, new) in out.items():
        if new != old:
            with io.open(os.path.join(root, name), 'w', encoding='utf-8', newline='') as f:
                f.write(new)
            changed.append(name)
    return changed, []


def check(root=REPO, run=None, runs_dir=RUNS, checks_dir=None):
    meta, out, problems = render_all(root, run, runs_dir, checks_dir)
    for name, (old, new) in out.items():
        if new != old:
            problems.append(f'{name}: recheck blocks differ from the readings; run python tools/recheck.py')
    return problems


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    run = args[0] if args else None
    if '--check' in sys.argv:
        p = check(run=run)
        print('\n'.join(p) or 'recheck blocks match the readings')
        sys.exit(1 if p else 0)
    changed, problems = apply(run=run)
    if problems:
        print('nothing written:')
        print('\n'.join(problems))
        sys.exit(1)
    print('changed:', changed or 'nothing')
