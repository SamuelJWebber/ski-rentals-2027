"""R1-12: a page the code does not recognise is "not determined", never "not offered"."""
import base64
import json
import os
import re
import unittest

from helpers import REPO
import listing_status as ls

FIX = os.path.join(REPO, 'tests', 'fixtures')


def fixture(name):
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def search_page(room_ids, total='$1,234'):
    """A minimal page shaped like an Airbnb search page's server-rendered data."""
    results = [{'demandStayListing': {'id': base64.b64encode(f'DemandStayListing:{r}'.encode()).decode()},
                'structuredDisplayPrice': {'explanationData': {'priceDetails': [
                    {'items': [{'accessibilityLabel': f'{total} total before taxes'}]}]}}} for r in room_ids]
    data = {'niobeClientData': [['StaysSearch', {'data': {'presentation': {'staysSearch': {'results': {
        'searchResults': results, 'paginationInfo': {'pageCursors': []}}}}}}]]}
    return f'<html><script id="data-deferred-state-0" type="application/json">{json.dumps(data)}</script></html>'


def old_dated_status(pages, room_id):
    """The 9 Nov recheck2.py logic without its fetching, as the review quoted it: a page with no
    search data falls through to NOT_IN_DATED_SEARCH."""
    def deferred(html):
        m = re.search(r'<script id="data-deferred-state-0"[^>]*>(.*?)</script>', html, re.S)
        return json.loads(m.group(1)) if m else None
    seen = 0
    for html in pages:
        blocks = [b for b in ls._find(deferred(html) or {}, 'searchResults', []) if isinstance(b, list)]
        for blk in blocks:
            for r in blk:
                lst = r.get('demandStayListing') or {}
                if lst.get('id'):
                    seen += 1
                    if base64.b64decode(lst['id']).decode().split(':')[1] == str(room_id):
                        return 'AVAILABLE'
    return 'NOT_IN_DATED_SEARCH'


class R1_12_ListingText(unittest.TestCase):
    def test_bookable_page(self):
        r = ls.classify_listing_text(fixture('listing_bookable.txt'))
        self.assertEqual((r['status'], r['total_usd'], r['originally_usd']), (ls.BOOKABLE, 1571, 1857))
        self.assertTrue(r['cancellation'].startswith('Free cancellation before January 4.'))

    def test_24_hour_refund_is_read(self):
        r = ls.classify_listing_text(fixture('listing_24h_refund.txt'))
        self.assertEqual(r['status'], ls.BOOKABLE)
        self.assertTrue(r['cancellation'].startswith('Free cancellation for 24 hours.'))

    def test_dates_not_available(self):
        self.assertEqual(ls.classify_listing_text(fixture('listing_not_offered.txt'))['status'], ls.NOT_OFFERED)

    def test_removed_listing(self):
        self.assertEqual(ls.classify_listing_text(fixture('page_removed.txt'))['status'], ls.REMOVED)

    def test_unrecognised_pages_are_not_determined(self):
        for text in ('', fixture('challenge.txt'), fixture('not_airbnb.html')):
            self.assertEqual(ls.classify_listing_text(text)['status'], ls.NOT_DETERMINED, text[:40])


class R1_12_SearchPages(unittest.TestCase):
    def test_listing_in_results_is_bookable(self):
        self.assertEqual(ls.status_from_search_pages([search_page(['111', '222'])], '222')[:2], (ls.BOOKABLE, 1234))

    def test_results_read_to_the_end_without_it(self):
        self.assertEqual(ls.status_from_search_pages([search_page(['111'])], '222')[0], ls.NOT_OFFERED)

    def test_capped_results_prove_nothing(self):
        self.assertEqual(ls.status_from_search_pages([search_page(['111'])], '222', page_cap=1)[0], ls.NOT_DETERMINED)

    def test_saved_non_airbnb_page_is_not_determined(self):
        page = fixture('not_airbnb.html')
        self.assertEqual(old_dated_status([page], '222'), 'NOT_IN_DATED_SEARCH')   # the bug the review found
        self.assertEqual(ls.status_from_search_pages([page], '222')[0], ls.NOT_DETERMINED)

    def test_blank_page_is_not_determined(self):
        self.assertEqual(ls.status_from_search_pages([''], '222')[0], ls.NOT_DETERMINED)
        self.assertEqual(ls.status_from_search_pages([], '222')[0], ls.NOT_DETERMINED)


if __name__ == '__main__':
    unittest.main()
