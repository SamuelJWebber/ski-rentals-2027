"""Log one listing page read in a browser into data/checks/<date>.tsv, from the page's own text.

usage: python tools/log_read.py ROOM CHECK_IN CHECK_OUT [--adults N] [--date YYYY-MM-DD] [--note TEXT]
                                [--washer TEXT] [--text-file FILE] [--checks-dir DIR] [--allow-undetermined]
       python tools/log_read.py --batch FILE.json [--date YYYY-MM-DD] [--checks-dir DIR]

The page text comes from --text-file or standard input: copy it from the listing page once it has fully
drawn (in the browser pane, read it with get_page_text or select-all and copy). The text is classified by
tools/listing_status.py, never typed: the logged status, price, cancellation line and washer lines are
the page's own words, and the line that decided the status is kept in the `evidence` column, so
tools/sitecheck.py can re-derive every logged status. A page the code does not recognise as a listing
(a challenge, an error, a half-drawn page) is refused unless --allow-undetermined, and is then logged as
NOT_DETERMINED, never as "not offered" (review findings R1-12 and R2-9).

Only the classified lines are stored. Host names, reviews and anything else on the page are not. A
batch file is a JSON list of {room_id, check_in, check_out, adults, text or lines, washer, note}.
Standard library only; nothing here fetches anything.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import listing_status as ls  # noqa: E402

REPO = os.path.dirname(HERE)
CHECKS = os.path.join(REPO, 'data', 'checks')
FIELDS = ['read_date', 'room_id', 'check_in', 'check_out', 'adults', 'status', 'total_usd', 'originally_usd',
          'evidence', 'cancellation', 'washer', 'source', 'note']


def _clean(s):
    return re.sub(r'[\t\r\n]+', ' ', s or '').strip()


def classify(room, check_in, check_out, text, adults=2, read_date=None, washer=None, note='',
             allow_undetermined=False):
    """The data/checks row for one page read, or ValueError when the page cannot be classified."""
    for v, what in ((room, 'room'), (check_in, 'check-in'), (check_out, 'check-out')):
        if not v:
            raise ValueError(f'missing {what}')
    if not re.fullmatch(r'\d{5,}', str(room)):
        raise ValueError(f'{room!r} is not an Airbnb room ID')
    a, b = date.fromisoformat(check_in), date.fromisoformat(check_out)
    if b <= a:
        raise ValueError('check-out must follow check-in')
    c = ls.classify_listing_text(text)
    if c['status'] == ls.NOT_DETERMINED and not allow_undetermined:
        raise ValueError(f'room {room}: the text is not recognisably a listing page with a price or an '
                         'unavailability line (challenge, error, or not fully drawn); read it again, or pass '
                         '--allow-undetermined to log it as not determined')
    return {
        'read_date': read_date or date.today().isoformat(),
        'room_id': str(room), 'check_in': check_in, 'check_out': check_out, 'adults': str(adults),
        'status': c['status'],
        'total_usd': str(c['total_usd'] or ''), 'originally_usd': str(c['originally_usd'] or ''),
        'evidence': _clean(c['evidence']), 'cancellation': _clean(c['cancellation']),
        'washer': _clean(washer if washer is not None else c['washer']),
        'source': 'pasted', 'note': _clean(note),
    }


def append(rows, checks_dir=CHECKS):
    """Append rows to data/checks/<read_date>.tsv, writing the header for a new file."""
    written = []
    for row in rows:
        path = os.path.join(checks_dir, f'{row["read_date"]}.tsv')
        new = not os.path.exists(path)
        if not new:
            with open(path, encoding='utf-8', newline='') as f:
                head = f.readline().rstrip('\n').split('\t')
            if head != FIELDS:
                raise ValueError(f'{path}: its columns are not {FIELDS}')
        os.makedirs(checks_dir, exist_ok=True)
        with io.open(path, 'a', encoding='utf-8', newline='') as f:
            w = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\', lineterminator='\n')
            if new:
                w.writerow(FIELDS)
            w.writerow([row[k] for k in FIELDS])
        written.append(path)
    return written


def main(argv):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('room', nargs='?')
    p.add_argument('check_in', nargs='?')
    p.add_argument('check_out', nargs='?')
    p.add_argument('--adults', type=int, default=2)
    p.add_argument('--date')
    p.add_argument('--note', default='')
    p.add_argument('--washer')
    p.add_argument('--text-file')
    p.add_argument('--batch')
    p.add_argument('--checks-dir', default=CHECKS)
    p.add_argument('--allow-undetermined', action='store_true')
    a = p.parse_args(argv)
    rows = []
    try:
        if a.batch:
            with open(a.batch, encoding='utf-8') as f:
                for item in json.load(f):
                    text = item.get('text') or '\n'.join(item.get('lines', []))
                    rows.append(classify(item['room_id'], item['check_in'], item['check_out'], text,
                                         item.get('adults', 2), a.date or item.get('read_date'),
                                         item.get('washer') or None, item.get('note', ''), a.allow_undetermined))
        else:
            if a.text_file:
                with open(a.text_file, encoding='utf-8') as f:
                    text = f.read()
            else:
                text = sys.stdin.read()
            rows.append(classify(a.room, a.check_in, a.check_out, text, a.adults, a.date, a.washer, a.note,
                                 a.allow_undetermined))
    except (ValueError, KeyError) as e:
        print(f'not logged: {e}', file=sys.stderr)
        return 1
    append(rows, a.checks_dir)
    for r in rows:
        print('\t'.join(r[k] for k in FIELDS))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
