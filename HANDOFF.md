# ski-rentals-2027 handoff

Rewritten **2026-11-09**, end of the review round 1 fix pass (Claude Code). Read `CLAUDE.md` first for the rules.
**Rewrite this file at the end of every session — never append.** Under 150 lines.

## State

Published at https://samueljwebber.github.io/ski-rentals-2027/ : six pages, all linked from `index.html` and
`README.md`. Nothing is booked and nothing is in flight; everything is committed and pushed. Review round 1
(`REVIEW.md`, 19 findings): 18 fixed, 1 deferred (R1-5, the history rewrite). Each finding has a status line
with its commit and test.

## How the pages are built now

- `data/costs.json` → `python tools/costs.py`: every week-for-two figure (lodging + tax + two 6-day passes, food
  left out) on the index cards, ranking table and cost table, the Europe verdict, the Hakuba card and the README.
  Figures sit in `data-cost` elements; edit the data and rerun, never the figure.
- `data/recheck/<date>.json` + `.tsv` (plus `zermatt-fresh-<date>.html` and `data/booking/<date>.tsv`) →
  `python tools/recheck.py`: the four recheck sections, header lines, nav links, the Zermatt banner and the dated
  status line on every listing a page cites. Each piece prints its own read date; blocks sit between markers.
- `data/checks/<date>.tsv`: listing pages read by hand (price, cancellation line). `data/readings.tsv`: dated
  snapshot of the CPC, SNOTEL and BC Hydro readings. `tools/listing_status.py`: the status rules.
- `python tools/sitecheck.py` (18 checks) and `python -m unittest discover -s tests` (66 tests), standard library,
  no network. Each finding's test also runs on the reviewed commit 20cb727 from git history and must fail there.
- `sh tools/install-hooks.sh` installs the pre-push hook (done in this clone): noreply emails only, no local
  paths or tokens, all checks green. When correcting a fact, add its old wording to `STALE_FACTS` in sitecheck.

## Recheck method from now on (review finding R1-13)

- **Only the listings that drive a recommendation**, each opened in the built-in browser pane at human pace on the
  listing page itself, dates in the address (`/rooms/<id>?check_in=...&check_out=...&adults=2`). With the pane
  hidden, take a screenshot before and between scrolls so lazy sections draw, then read the text. Log every read
  in `data/checks/<date>.tsv`.
- **No scripted scraping and no browser disguise.** Stop at the first HTTP 429, challenge or CAPTCHA, record it,
  and do not retry or route around it. Booking.com only in the browser pane, as an ordinary visitor.
- **The 9 Nov scripts are retired.** search.py, recheck.py, recheck2.py, verify.py and cheapest_inunit*.py sent a
  browser User-Agent while fetching hundreds of Airbnb pages over plain HTTP; they are not to be run again. They
  and the raw TSVs stay in `.codex-temp\ski-rentals-2027-2026-11-09\` under the machine's `code` folder.
- **Official sources** (CPC, NRCS, BC Hydro, municipal pages) are fetched with an honest project identifier,
  never a browser User-Agent.

## What is true now (9 Nov 2026)

- **Engelberg**, 9–16 Jan: $1,626–1,649 lodging and tourist tax, $2,303–2,612 with two 6-day passes, from a flat
  with the washer in the unit (1267557874578220140, $1,571, free cancellation before 4 Jan; no smoke or CO alarm).
- **Telluride**, 23–30 Jan: $2,014–2,259 lodging and 17.22% tax (29856063 at $1,718, 15395305 at $1,927, both free
  cancellation before 24 Dec); $5,017–5,262 with two 6-day tickets. Epic covers the lifts.
- **Hakuba**: no refundable week under budget. 13–20 Mar from $2,619 with an in-unit washer, but it refunds in full
  only for 24 hours; January from $5,605.
- **Zermatt**: a January week fits on lodging and tax ($1,992); with passes it is "from $2,940", at a floor price
  the operator charges only 1–27 Nov and 19 Apr–2 May. Season pass CHF 1,850 from 1 Nov, 1,960 from 1 Dec.
- **Recheck**: 158 listing-weeks identified by room ID: 66 bookable, 88 not offered, 4 removed (3 listings). The
  steep page has 26 more priced listings without a room ID (every Japanese one), not rechecked. Of the 66 bookable,
  15 state a free washer in the unit and 29 a building or paid one (27 in the building, 2 paid in the unit).
- **Whistler**: the only September listing still offered is $3,144 with tax (9–16 Jan); not searched afresh.
- **Fernie has a gym**: Evolution Health & Fitness, 1192 8th Ave, day passes (its own site, read 9 Nov).

## Verified, and how

- **Seen live, 9 Nov 2026, browser pane at human pace:** 33 listing pages (`data/checks/2026-11-09.tsv`): 24 showed
  a free-cancellation date, 4 refund in full only for 24 hours, 4 did not render the line, 1 (Westgate, the one row
  the scripts could not determine) showed "Those dates are not available". The live index and cost table render.
- **Fetched 9 Nov with a project identifier:** SNOTEL fixed-date queries (Lone Mountain 2 in, Lizard Head Pass 4,
  Idarado 3), CPC's archived October ENSO discussion, BC Hydro Mt Revelstoke (18 cm at 15:45).
- **Read 9 Nov with web tools:** Matterhorn Paradise pass prices; Evolution Fernie's site; engelberg.ch (CHF 213
  covers only Brunni); titlis.ch answered 429 to one request, not retried; Hakuba lodging tax from hotel notices.
- **Fixture-proven only:** cost arithmetic, recheck rendering and reruns, status rules on saved or hand-written
  pages, pre-push rules (tests). Reproduced: the old insert_sections.py exits 1 on a copy of the reviewed pages.

## Refund cutoffs of the options on the pages (last safe day is the day before, listing's local time)

Zermatt Baccara studio 9–16 Jan: before 10 Dec. Telluride 23–30 Jan options: before 24 Dec. Engelberg flats
9–16 Jan: before 4 Jan. Three-resort options: Telluride 20–27 Feb before 21 Jan, Revelstoke 23–30 Jan before
22 Jan, Big Sky 6–13 Mar before 4 Feb. Every other read cutoff is in the recheck tables' refund column.

## Choices made, and why (all reversible)

- **Budget test is lodging plus tax**, with two 6-day passes in their own column: a season pass covers the lifts at
  many of these resorts. Food is left out everywhere (the September Engelberg figure counted $750–1,150 of it).
- **Zermatt passes are floors** ("from $X"), because the operator's lowest price applies only in shoulder weeks.
- **Hakuba tax** is the Nagano and Hakuba village per-person tax (about ¥500 a night, ¥1,000 at January rates),
  replacing the September ~12% assumption in the cost model; Europe tourist taxes are labelled assumptions.
- **Fernie gym**: corrected the index rather than propagating its "no gym found" (R1-7).
- **Scorecard**: eight steep-page cells re-derived from listed rows (R1-10); card ranges likewise.
- **Stay dates stay on price rows**; party size, the enquiry draft and first-person framing are gone (R1-2).
- **Scrapers retired**, not moved into this public repo; rendering, rules and data moved in instead.

## Unverified or open — exact

- Engelberg 6-day Titlis pass: CHF 274–390 (UK operator page with no season; September estimate).
- Zermatt January and March 6-day and month pass prices: only the floors are known.
- Tax assumptions not rechecked: CO 16% outside Telluride, UT 15%, WY 13%, NM 15%, Quebec 18.5%; Europe tourist
  taxes; Niseko's Hokkaido tax (only Kutchan's 2% is in the model). Hakuba's rates come from hotel notices.
- Cancellation lines not read for most of the 66 bookable rows (the refund column says which).
- No fresh search for Whistler, Jackson, Chamonix, Andermatt and the others; only September listings were rechecked.
- CPC outlook percentages were read before this pass and confirmed by the review, not re-read from the images.
- Not rechecked at all: Hakuba Adam opening date, Telluride gondola funding, Lift 7/8 type, a numeric BC snow
  outlook, the Big Sky and Revelstoke snow reports, lift-audit numbers, terrain write-ups, gym and supermarket
  claims, Jackson details.

## Next

1. CPC's ENSO update is due 12 Nov 2026: link the new archived discussion (`enso_disc_nov2026/`) on the
   three-resort page and add the reading to `data/readings.tsv`.
2. Before 9 Dec (the earliest cutoff), re-read the recommended listings by the method above, write
   `data/checks/<date>.tsv` and a new recheck run, then run `tools/recheck.py` and `tools/costs.py`.
3. Verify the North American tax assumptions from official pages; they drive every all-in on the steep page.
4. Engelberg pass: one request to titlis.ch in December; stop at a 429.
5. Review round 2 follows; keep `STALE_FACTS` and the cost data current with every correction.

## Needs the user (true walls only)

- **R1-5 history rewrite.** Removing the personal email from 15 published commits and the local path from 868d81c
  needs your go-ahead for a force-push to this public repo (`git filter-repo` with a mailmap to the noreply
  address and a path replacement). Clones and GitHub's cached commits keep the old text either way.
- **CLAUDE.md privacy line.** The review's suggested hard line (below, under Standing) was not added to CLAUDE.md,
  because an agent may not edit it on an agent's instruction; add it if you agree.

## Corrections already made — do not undo them

Andermatt's queue figures are unsourceable and size is the real caveat. St Anton is kept off the top by the
washer, not the price, and its September quotes were US dollars. Fernie's Polar Peak rarely opens; Fernie town
does have a gym (Evolution, verified 9 Nov). Airbnb quotes USD by default. Telluride and Hakuba are on Epic, not
Ikon; Furano, Shiga Kogen and Myoko Suginohara are on Ikon. Telluride's lodging tax is 17.22%. Lifts 7/8 were
not approved in June 2026. The Revelstoke bus runs every 30–45 minutes. Jackson's Teton Village is 19–26 minutes
away. Whistler's capacity is about three times Telluride's, not more than six resorts combined. Airbnb's
free-cancellation badge is not the policy, and its cutoff falls before the date shown.

## Standing

This repo is public: no personal details, booking references, payment information, party size or first-person
plans. A unit someone books is never identifiable on the site: remove or anonymise its row the day it is booked.
Every price carries its currency and the date it was quoted. A claim that cannot be sourced is cut or marked.
