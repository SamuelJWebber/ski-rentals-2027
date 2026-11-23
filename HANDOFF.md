# ski-rentals-2027 handoff

Rewritten **2026-11-22**. Read `CLAUDE.md` first for the rules.
**Rewrite this file at the end of every session, never append.** Under 150 lines.

## State

Published at https://samueljwebber.github.io/ski-rentals-2027/ : six pages, **public repo**. The pages are a
**snapshot of 9 November 2026 that nobody maintains**, and since 2026-11-21 every page says so in a line above its
title. Nothing has been rechecked since 9 November. The first refund cutoff the pages quote is 10 December 2026.

An independent review was filed on 2026-11-10 (`REVIEW.md`, top table; `reviews/fable-2026-11-10/`). On 2026-11-21
SKI-3 (Zermatt week pass floor) and the snapshot banner were fixed. On 2026-11-22 every offline finding was closed:
Zermatt month-pass March bands (CHF 1,270–1,422, Täsch March ~$9,415–9,790), SKI-2 Hakuba accommodation-tax bands
(¥400 Mar -> $2,733 / $3,552; ¥900 Jan -> $5,686 / $6,505) with consumption-tax uncertainty disclosed, SKI-1's
interim wording (unread cheaper candidates disclosed), SKI-4 (Telluride 20–27 Feb $2,523), SKI-5 (Crocker snow
comparison), SKI-6 (JMA stats + TCC No. 152 pointer), SKI-7 (rentals lede, NA heading, Top picks), SKI-8 (Jackson
March/El Niño caveats), and known slips (R2-10 index $906/$907, R2-11, R2-13, R2-14).

140 tests run via `python -m unittest discover -s tests` (139 pass, 1 Windows `sh`-stub test skipped) and
`python tools/sitecheck.py --pre-push` is clean (25 checks + pre-push).

## Next, in order

1. **SKI-1 (open, needs live browser hand-read).** Two cheaper Hakuba listings (rooms `678032453961510940` at
   $2,156 and `1025746272456071125` at $2,231, 13–20 March) state "Free washer – In unit" on their own pages and
   need a human read in the browser pane (total, cancellation line, washer wording), logged in
   `data/checks/<date>.tsv`. No script may fetch Airbnb.
2. **SKI-2 checkout consumption-tax read (open, needs live browser hand-read).** Open room `4721170` (13–20 Mar) in
   the browser pane once to read its price breakdown and confirm whether Japan's 10% consumption tax is inside
   Airbnb's $2,697 total or added on top ($3,003 if added on top of the displayed total). Only then decide whether
   to strip the September ~12% from the 13 Japanese rows on `steep-and-town-2027.html`.
3. If the pages are ever refreshed, rerun the hand recheck of recommendation-driving listings and update the
   snapshot line's date. Otherwise leave them; the snapshot banner states what they are.

## Unverified

- Whether Airbnb adds Japan's 10% consumption tax at checkout on room `4721170` (SKI-2).
- The cancellation lines of rooms `678032453961510940` and `1025746272456071125` (SKI-1).
- The Zermatt pass bands (CHF 436 / 488 6-day; CHF 1,270 / 1,422 1-month) come from the review's read of the
  operator's April 2026 leaflet on 10 Nov 2026 (ticket pages answered 404 to a plain fetch on 21 Nov).

## How the pages are built now

- `data/costs.json` -> `python tools/costs.py`: every week-for-two figure (lodging + tax + two 6-day passes, food
  left out) on index cards, ranking table, cost table, Hakuba card, steep page, and README. Edit data, never figures.
- `data/recheck/<date>.json` + `.tsv` (+ `zermatt-fresh-<date>.html` and `data/booking/<date>.tsv`) ->
  `python tools/recheck.py`: recheck sections, header lines, nav links, Zermatt banner, and dated listing notes.
- `data/checks/<date>.tsv`: listing pages read by hand (`tools/log_read.py`). `data/readings.tsv`: dated snapshot
  of CPC, SNOTEL, and BC Hydro readings. `tools/listing_status.py`: status rules.
- `python tools/sitecheck.py` (25 checks) and `python -m unittest discover -s tests` (140 tests), standard library,
  no network. Findings also test against historical commits via `tests/helpers.py`.
- `sh tools/install-hooks.sh` installs the pre-push hook: noreply emails only, no local paths or tokens, all checks
  green. When correcting a fact, add its old wording to `STALE_FACTS` in `tools/sitecheck.py`.

## Recheck method (review finding R1-13)

- **Only the listings that drive a recommendation**, each opened in the built-in browser pane at human pace on the
  listing page itself (`/rooms/<id>?check_in=...&check_out=...&adults=2`). With the pane hidden, take screenshots
  before and between scrolls so lazy sections draw, then read the text and log in `data/checks/<date>.tsv`.
- **No scripted scraping and no browser disguise.** Stop at the first HTTP 429, challenge or CAPTCHA, record it,
  and do not retry or route around it. Booking.com only in the browser pane, as an ordinary visitor.
- **The 9 Nov scripts are retired** (they sent a browser User-Agent) and are never to be run again. Official
  sources (CPC, NRCS, BC Hydro, municipal pages) use an honest project identifier, never a browser User-Agent.

## What is true now (9 Nov 2026 data, updated through 2026-11-22 corrections)

- **Engelberg**, 9–16 Jan: $1,626–1,649 lodging and tax, $2,303–2,612 with passes (`1267557874578220140`, $1,571,
  free cancellation before 4 Jan; no smoke/CO alarm).
- **Telluride**, 23–30 Jan: $2,014–2,259 lodging and 17.22% tax (`29856063` $1,718, `15395305` $1,927, free
  cancellation before 24 Dec); $5,017–5,262 with tickets (Epic covers lifts). Also `29856063` refundable for
  20–27 Feb at $2,523 with tax (free cancellation before 21 Jan).
- **Hakuba**, 13–20 Mar: $2,733 lodging and ¥400/person/night tax (`4721170`, $2,697, free cancellation before
  11 Feb, 5-min drive or shuttle); $3,552 with passes. Two cheaper in-unit candidates ($2,156, $2,231) unread on
  cancellation; January from $5,605 ($5,686 with ¥900/person/night tax).
- **Zermatt**: Jan week fits on lodging and tax ($1,992); with two passes from $3,069 (CHF 436 Basic band). March
  week from $3,817–3,945 (CHF 436–488). Month pass Jan–Mar from CHF 1,270–1,422; Täsch March ~$9,415–9,790.
- **Recheck**: 132 listing-weeks + 26 Zermatt listing-months (158 rows): 66 bookable, 88 not offered, 4 removed
  (3 listings); 26 unidentified steep-page rows not rechecked.
- **Whistler**: only `1450123020779481422` still offered for 9–16 Jan at $3,144 with tax; Whistler not re-searched.
- **Fernie**: Evolution Health & Fitness, 1192 8th Ave, day passes (site read 9 Nov).

## Needs the user

- R1-5 **decided 2026-11-22: no history rewrite** (15 pre-2026-10-02 commits keep old author address; hook + tests
  hold noreply going forward). GitHub Settings -> Emails ("Keep my email addresses private" & "Block command line
  pushes that expose my email") stops future exposure at source.
