"""Decide a listing's status for a dated stay from what a page shows. Pure functions; nothing here
fetches anything.

classify_listing_text(text)
    For the method used from 9 Nov 2026 on: a listing page opened in the browser pane at human pace
    (https://www.airbnb.com/rooms/<id>?check_in=...&check_out=...&adults=2), its visible text read
    once it has rendered. Returns a dict with status, total_usd, originally_usd, cancellation, the
    evidence line that decided the status, and the page's own washer lines. tools/log_read.py runs it
    on every page read and logs the result in data/checks/<date>.tsv.

status_from_evidence(line)
    The status one stored line supports: the price line ("$2,697 for 7 nights"), the page's own "Those
    dates are not available", or a removal notice. tools/sitecheck.py re-derives every logged status
    from its stored line with this, so a half-drawn page or a challenge typed in as "not available"
    cannot become a published "not offered" (review finding R2-9).

status_from_search_pages(pages, room_id)
    For saved Airbnb search pages (the method of the 9 Nov recheck): the listing is bookable if it is
    in the results, not offered if the results were read to the end without it.

Statuses: BOOKABLE, NOT_OFFERED, REMOVED, NOT_DETERMINED. Anything the code does not positively
recognise (a blank page, a bot challenge, an error page, changed markup) is NOT_DETERMINED. It is
never NOT_OFFERED, which the pages publish as "not offered for these dates" (review finding R1-12).
"""
import base64
import json
import re

BOOKABLE, NOT_OFFERED, REMOVED, NOT_DETERMINED = 'BOOKABLE', 'NOT_OFFERED', 'REMOVED', 'NOT_DETERMINED'

# Text that only an Airbnb listing page shows, so a page without it is not one.
LISTING_MARKERS = re.compile(r"Things to know|Where you(?:'|’)ll sleep|What this place offers|Show all \d+ amenities|"
                             r"Hosted by|Meet your host|You won(?:'|’)t be charged yet")
TOTAL = re.compile(r'\$([0-9][0-9,]*) (?:for (\d+) nights|monthly)(?:, originally \$([0-9][0-9,]*))?')
UNAVAILABLE = re.compile(r"Those dates are not available|These dates are not available|"
                         r"(?:Those|These) dates aren(?:'|’)t available|dates are unavailable", re.I)
GONE = re.compile(r"can(?:'|’)t seem to find the page|This (?:listing|place) is no longer available|"
                  r"listing (?:has been|was) (?:removed|deactivated)", re.I)
CANCEL = re.compile(r'Free cancellation (?:before [A-Z][a-z]+ \d{1,2}|for \d+ hours)[^.\n]*\.'
                    r'(?: (?:Cancel before|After that)[^.\n]*\.)?')
# A line about laundry, a washer or a dryer, but not a dishwasher or a hair dryer.
WASHER = re.compile(r'(?<![Dd]ish)(?<![Dd]ish )[Ww]asher|[Ll]aundry|(?<![Hh]air )[Dd]ryer')


def _dollars(s):
    return int(s.replace(',', '')) if s else None


def classify_listing_text(text):
    """status, total_usd, originally_usd, cancellation, evidence (the line that decided the status, as
    the page wrote it) and washer (the page's own lines that mention a washer or laundry)."""
    text = text or ''
    out = {'status': NOT_DETERMINED, 'total_usd': None, 'originally_usd': None, 'cancellation': '',
           'evidence': '', 'washer': washer_lines(text)}
    c = CANCEL.search(text)
    if c:
        out['cancellation'] = c.group(0)
    g = GONE.search(text)
    if g and not LISTING_MARKERS.search(text):
        out.update(status=REMOVED, evidence=_line_of(text, g))
        return out
    if not LISTING_MARKERS.search(text):
        return out  # not recognisably a listing page: blank, challenge, error, or changed markup
    u = UNAVAILABLE.search(text)
    if u:
        out.update(status=NOT_OFFERED, evidence=_line_of(text, u))
        return out
    m = TOTAL.search(text)
    if m:
        out.update(status=BOOKABLE, total_usd=_dollars(m.group(1)), originally_usd=_dollars(m.group(3)),
                   evidence=_line_of(text, m))
    return out


def _line_of(text, m):
    """The whole line a match sits on, stripped."""
    start = text.rfind('\n', 0, m.start()) + 1
    end = text.find('\n', m.end())
    return text[start:end if end != -1 else len(text)].strip()


def washer_lines(text):
    """The page's own lines that mention a washer or laundry (not a dishwasher), in page order, once each."""
    out = []
    for line in (text or '').splitlines():
        line = line.strip()
        if line and len(line) <= 200 and WASHER.search(line) and line not in out:
            out.append(line)
    return '; '.join(out)


def status_from_evidence(line):
    """(status, total_usd, originally_usd) that one stored line supports: a price line, the page's own
    unavailability line, or a removal notice. Anything else supports only NOT_DETERMINED."""
    line = line or ''
    m = TOTAL.search(line)
    if m:
        return BOOKABLE, _dollars(m.group(1)), _dollars(m.group(3))
    if UNAVAILABLE.search(line):
        return NOT_OFFERED, None, None
    if GONE.search(line):
        return REMOVED, None, None
    return NOT_DETERMINED, None, None


# ---------------------------------------------------------------- saved search pages

def _deferred(html):
    m = re.search(r'<script id="data-deferred-state-0"[^>]*>(.*?)</script>', html or '', re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def _find(o, key, acc):
    if isinstance(o, dict):
        if key in o and o[key] not in (None, [], ''):
            acc.append(o[key])
        for v in o.values():
            _find(v, key, acc)
    elif isinstance(o, list):
        for v in o:
            _find(v, key, acc)
    return acc


def status_from_search_pages(pages, room_id, page_cap=None):
    """`pages` is the HTML of each search page read, in order. Returns (status, total_usd, seen)."""
    seen = 0
    if not pages:
        return NOT_DETERMINED, None, 0
    for i, html in enumerate(pages):
        data = _deferred(html)
        if data is None:
            return NOT_DETERMINED, None, seen  # not a search page: blocked, blank or changed markup
        if i == 0 and not _find(data, 'paginationInfo', []):
            return NOT_DETERMINED, None, seen
        for block in (b for b in _find(data, 'searchResults', []) if isinstance(b, list)):
            for r in block:
                lst = r.get('demandStayListing') or {}
                if not lst.get('id'):
                    continue
                seen += 1
                try:
                    rid = base64.b64decode(lst['id']).decode().split(':')[1]
                except (ValueError, IndexError):
                    continue
                if rid != str(room_id):
                    continue
                total = None
                sdp = r.get('structuredDisplayPrice') or {}
                for grp in ((sdp.get('explanationData') or {}).get('priceDetails') or []):
                    for it in grp.get('items') or []:
                        lab = it.get('accessibilityLabel') or ''
                        if 'total before taxes' in lab:
                            total = lab.split(' ')[0]
                return BOOKABLE, _dollars((total or '').replace('$', '')), seen
    if page_cap is not None and len(pages) >= page_cap:
        return NOT_DETERMINED, None, seen  # the results never ran out, so absence proves nothing
    return NOT_OFFERED, None, seen
