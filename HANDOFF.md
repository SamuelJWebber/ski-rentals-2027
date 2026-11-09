# ski-rentals-2027 handoff

Rewritten **2026-11-09**, end of the second Claude Code pass that day. Read `CLAUDE.md` first for the rules.
**Rewrite this file at the end of every session — never append.** Under 150 lines.

## State

**Published** at https://samueljwebber.github.io/ski-rentals-2027/ . Six pages, all linked from `index.html`
and `README.md`: index (combined verdict), alps-extreme, steep-and-town, ski-rentals, zermatt-month-stay,
three-resorts-best-snow. Nothing is booked; nothing is in flight; the working tree is clean.

Verified live on 2026-11-09: Pages build `built` at commit baaf5d2; all six URLs return HTTP 200 and contain
the 9 November content (`id="changed"` on the index, `recheck:start` blocks on the four detailed pages).

Dates of the data: the three-resort page is fully 9 Nov 2026. The four September pages keep their 10–11 Sep
content, with a dated "Rechecked 9 November 2026" section added to each and specific facts marked
"Corrected 9 Nov 2026" in place. The index has a "What changed by 9 November 2026" section at the top.

## Recheck method from now on (review finding R1-13)

- **Only the listings that drive a recommendation**, each opened in the built-in browser pane at human pace on
  the listing page itself, with its dates in the address (`/rooms/<id>?check_in=...&check_out=...&adults=2`).
  With the pane hidden, take a screenshot first so the page draws, then read the text; the status rules are in
  `tools/listing_status.py`. Log every read in `data/checks/<date>.tsv` (price, cancellation line, washer).
- **No scripted scraping and no browser disguise.** Stop at the first HTTP 429, challenge or CAPTCHA, record it,
  and do not retry or route around it. Booking.com is read only in the browser pane as an ordinary visitor.
- **The 9 Nov scripts are retired.** search.py, recheck.py, recheck2.py, verify.py and cheapest_inunit*.py sent a
  browser User-Agent while fetching hundreds of Airbnb pages over plain HTTP; they are not to be run again. They
  and the raw TSVs stay in `.codex-temp\ski-rentals-2027-2026-11-09\` under the machine's `code` folder, outside
  git. Rendering moved into the repo: `tools/recheck.py` replaces gen_sections.py and insert_sections.py.
- **Official sources** (CPC, NRCS, BC Hydro, municipal pages) are fetched with an honest project identifier,
  never a browser User-Agent.

## Findings now on the pages

- **Three-resort report.** All three 14 Sep picks were booked or failed the washer rule. Picks on 9 Nov, each
  with a washer in the unit (photo-confirmed for Revelstoke and Big Sky) and a free-cancellation date:
  Revelstoke 23–30 Jan, "New Condo with Mountain Views" (1521039495192820325), $1,945 → $2,256 all-in, free to
  22 Jan; Telluride **20–27 Feb**, West Telluride Studio (29856063), $2,152 → $2,523, free to 21 Jan; Big Sky
  6–13 Mar, "A Little Condo" (9624791), $2,305 → $2,582, free to 4 Feb. Total $7,361. Also: NOAA strong El Niño
  outlook, snow-station readings, opening dates, Epic-vs-Ikon, Revelstoke bus every 30–45 min (not 15).
- **Recheck of every September Airbnb listing:** 158 listing-weeks — 66 bookable, 87 not offered, 4 listings
  removed, 1 undetermined. Of the 66, only 15 state a free in-unit washer; 27 list a building or paid washer.
- **Zermatt month:** January no longer fits 10k with a washer stated in the flat (cheapest such: $38,302; village
  from $6,122 with a paid building washer). February $7,452 and March $7,779 still fit via one studio
  (673758664490334985); Täsch March $4,927 (39332849). Week: village $1,923 (9–16 Jan), $2,671 (6–13 Mar).
- **Corrections on the index and other pages:** Telluride and Hakuba are on Epic, not Ikon; only Niseko United
  of the Japanese resorts named on the rentals page is on Ikon. Telluride lodging tax is 17.22% (town page),
  not 11.9%: steep-and-town Telluride all-ins and the index's "≈$2,100" (now ≈$2,200) recomputed. Lifts 7/8 were
  not approved in June 2026 (draft decision only). Hakuba's new gondola is +78% capacity, not double. Zermatt
  CHF 384 is a dynamic-pricing floor. St Anton's Epic terms added. Engelberg's $914 listing is still bookable
  ($906) but lists a paid building washer. Airbnb totals are labelled "total before taxes" (open question closed).
- **Booking.com (rentals page):** Hinode Hills refundable $2,180 (13–20 Mar); Always Niseko no availability
  16–23 Jan; Setsu, MUSE, Chalet Ivy, Yamakei non-refundable only; Yu Kiroro refundable only on a $6,249 suite.
- **Policies read on 9 Nov:** 15 Airbnb listings; 7 refund in full only within 24 hours of booking.

## Choices made, and why (all reversible)

- **Telluride moved from 27 Feb–6 Mar to 20–27 Feb.** On 27 Feb nothing in town with an in-unit washer was both
  refundable and under $3k ($3,448 refundable, or $2,912 with a 24-hour refund). Both stay on the page.
- **Pick rule:** among listings passing the hard rules, the one near the lifts whose full refund runs latest,
  so the snowpack can decide. This keeps the Revelstoke pick over two cheaper condos refundable only to 24 Dec.
- **Big Sky pick has the weakest rating (4.48/119);** the two better-rated alternatives refund 24 h only.
- **Telluride Valley Floor listing (21539429)** keeps its 11.9% all-in with a note: it is outside the town and
  the county rate was not checked.
- **Scripts kept out of the public repo** (they scrape Airbnb's page data); kept in `.codex-temp` instead.
- The September commit 2eac02b was pushed unchanged: no new personal data; its email was already public.

## Unverified or open — exact

- **Cancellation terms not read** for the 66 still-bookable September listings (only price, availability and
  amenities were rechecked), nor for: 15395305 (Telluride Jan; the line never rendered), Hakuba 15857739 (never
  rendered), The Dreamcatcher, Comfy Condo (Big Sky), Revelstoke Retreat, Revylation.
- **Undetermined:** 36729825 (Westgate Park City, 9–16 Jan) — the search hit its cap even with the tight box.
- **"Not offered"** cannot distinguish booked from a changed minimum stay or blocked calendar.
- **Engelberg six-day pass** CHF 274 still unverified (titlis.ch returned 429; not retried).
- **Hakuba Adam:** December 2027 opening rests on third-party reports of an operator release; "base ski school
  and summit terrace demolished" was not rechecked.
- **Telluride gondola funding** status comes from search snippets (SMART documents returned 403). Lift 7/8 type
  (fixed-grip vs detachable) is not stated in anything read.
- **BC snow outlook** has no current numeric source; the page relies on Environment Canada's 1998 study.
- **Snow reports:** Big Sky's resort page did not load; Revelstoke's still showed last spring's text; Revelstoke
  closing day not published (Kids Ski Free runs to 11 Apr 2027).
- **Steep-and-town tax assumptions** for other places (CO 16%, UT 15%, WY 13%, NM 15%, Quebec 18.5%) were not
  rechecked. BC 16% and MT 12% were confirmed.
- **Not rechecked at all this session:** the lift-audit numbers, terrain write-ups, gym and supermarket claims,
  Jackson details, and every non-Airbnb, non-Booking source on the September pages.
- Some ratings come from Airbnb's headline line rather than the review block; a blank rating means neither
  appeared in the page data.

## Next

1. Read the cancellation line for the still-bookable September listings that a page recommends (start with
   the index's three answers and each page's top picks), then mark them on the recheck tables.
2. CPC's ENSO update is due 12 Nov 2026, then monthly; watch bases against the refund deadlines (Revelstoke
   22 Jan, Telluride 21 Jan, Big Sky 4 Feb; Engelberg option 4 Jan; West Telluride Studio for January 24 Dec).
3. Re-run the recheck before those deadlines with the saved scripts (`recheck.py` then `make_tight_spec.py`,
   `recheck2.py` with `BOX=0.0012 PAGES=15`, `gen_sections.py`, `insert_sections.py`).
4. The repo now enters a review pipeline: adversarial reviews written to `REVIEW.md`, each followed by a fix pass.

## Needs the user

Nothing is needed to continue the research. Booking, and any message to a host, are the user's alone.

## Corrections already made — do not undo them

Andermatt's queue figures are unsourceable and size is the real caveat. St Anton is a European co-leader, kept
off the top by the washer and not by price. Fernie's Polar Peak rarely opens and its gym is unverified.
Airbnb quotes USD by default — an unlabelled figure caused one published error. Telluride and Hakuba are on
Epic, not Ikon. Telluride's lodging tax is 17.22%, not 11.9%. Lifts 7/8 were not approved in June 2026. The
Revelstoke bus is every 30–45 minutes, not 15. Airbnb's free-cancellation badge is not the policy.

## Standing

**This repo is public.** No personal details, no booking references, no payment information. Every price
carries its currency and the date it was quoted. A claim that cannot be sourced is cut or marked
unsourceable, not softened.
