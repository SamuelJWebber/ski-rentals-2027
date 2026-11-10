# Independent Fable review, 2026-11-10 (not a pipeline round)

An outside check of what was pushed on 2026-11-09, by a different model from the one that built and
reviewed it: first-line reviewers attacked the work and compared it with other people's, then a
second reviewer tried to refute each HIGH and MEDIUM finding. Only the verified result is below.
Full reports, with commands and sources: `reviews/fable-2026-11-10/` (`ski-V.md` is the verification;
the others are the first-line reports, including claims the verifier narrowed or rejected).
**Nothing here has been implemented.** Mark each row Fixed / Rejected / Deferred as it is handled.

## Verdict table

| Finding | Their severity | Verdict | My severity | Corrected one-line statement |
|---|---|---|---|---|
| SKI-1 | HIGH | WEAKENED (washer wording UPHELD; price consequence UNVERIFIABLE) | HIGH, narrowed | Two cheaper Hakuba listings ($2,156, $2,231) were dismissed as "not stated in the unit" and their pages say "Free washer – In unit"; their cancellation lines were never read, so "$2,742 is the first in price order" is unsupported, not shown wrong. |
| SKI-2 | MEDIUM | UPHELD on the accommodation-tax bands (primary sources); consumption-tax part UNVERIFIABLE | MEDIUM | Hakuba's tax this winter is ¥400 per person per night at this price (¥900 in January), not ¥500 / ¥1,000: $2,733, not $2,742. Whether Airbnb's displayed total already contains consumption tax was not confirmed by any page I could reach. |
| SKI-3 | MEDIUM | UPHELD | MEDIUM | With the operator's January band starting price (CHF 436) the Zermatt week with two passes is from $3,069 at the site's rate ($3,054 at 10 Nov ECB), not from $2,940; these are still "from" prices. |
| SKI-4 | MEDIUM | WEAKENED | MEDIUM (low end) | "January only" is accurate inside the index's stated January-and-March frame, and the index does link the three-resort page; what is missing is one line on the Telluride card that the same studio is refundable for 20–27 Feb at $2,523 with tax (priced 9 Nov 2026). |
| SKI-5 | MEDIUM | WEAKENED | MEDIUM (low end) | The gap is a property of the source (OnTheSnow resort-reported, 14 recent rows, operating-season window, visible reporting gaps), not a transcription error; Crocker and ZRankings are one dataset, not two; "February is the snowiest month" at Telluride rests on 50 in against 47 in. |
| SKI-6 | MEDIUM | WEAKENED | LOW | The index's El Niño note omits Japan (true), but JMA's own statistics list no significant snowfall signal for the Sea of Japan side in El Niño winters; the cited JMA document is a one-winter forecast for 2023-24 with other drivers. |
| SKI-7 | MEDIUM | UPHELD | MEDIUM | The rentals page's first sentence still says Whistler has qualifying flats at $1,400–2,500; every Whistler row in the 9 Nov recheck is "not offered" except one at $2,710 before tax ($3,144 with tax). Whistler was not searched afresh, so the sentence is unsupported rather than proven false. |
| SKI-8 | MEDIUM | UPHELD | MEDIUM (low end) | Crocker and ZRankings both put Jackson's best period in January and say its steep south-facing terrain suffers in March; Crocker has it at 88% of normal in strong El Niño months. The site's sentence is a lift comparison with Crested Butte and makes no snow claim, so this is an omitted caveat. |

Counts: UPHELD 4 (SKI-2, 3, 7, 8), WEAKENED 4 (SKI-1, 4, 5, 6), REFUTED 0 whole findings, two parts UNVERIFIABLE
(SKI-1 refundability, SKI-2 consumption tax). Sub-claims refuted: SKI-4 "unlinked on another page"; SKI-5 "two
outside sources"; SKI-6 "JMA ties El Niño winters to below-normal snowfall on the Sea of Japan side" as a general
rule; SKI-3's fix "drop 'only the floors are known'".

## Fix first

1. Read rooms 678032453961510940 and 1025746272456071125 by hand for 13–20 March (total, cancellation line, washer
   wording), log them with the date, and until then change "the first listing in price order" to wording that
   says two cheaper in-unit candidates are unread.
2. Read the price breakdown on room 4721170 once to settle whether any tax is added to Airbnb's displayed total in
   Japan, then set Hakuba's tax to ¥400 (¥900 in January) with the ministry notice as the dated source and make
   the steep page and the index use one treatment.
3. Replace "from $2,940" for the Zermatt January week with the January band's starting price (about $3,069, leaflet
   dated April 2026), and rewrite the rentals page's first sentence and North America heading from the 9 Nov rows.

---

# Review round 2 (2026-11-09)

Adversarial review of the published site at commit e3866e3, the end of the round 1 fix pass. No page, data
file or tool was changed by this review; only this file is committed. Line numbers are source lines in the named
file. "Scratch folder" means the folder HANDOFF.md names for the retired 9 Nov scripts and raw search TSVs (not in
git); it was read, never changed.

**Counts: 3 HIGH, 6 MEDIUM, 6 LOW. Round 1 regressions: 2.** R1-1 and R1-3 each pass their own verify step, but
the defect each describes survives elsewhere (R2-1, R2-2). R1-5 stays deferred to the owner.

How it was checked:
- `python tools/sitecheck.py` gives 19 checks ok; `python -m unittest discover -s tests` runs 68 tests, OK.
  `python tools/costs.py --check` and `python tools/recheck.py --check` report no drift.
- Re-derived without the project's code (awk or plain Python over the raw inputs): every cost-table cell,
  the 66/88/4 recheck tally and each of the 158 published statuses, Telluride's 17.22%, the SNOTEL, CPC and
  BC Hydro readings.
- One Airbnb listing page read live in the browser pane at human pace (R2-1). Official sources and the 73
  external links were fetched once each with an honest project identifier (the project name and its noreply
  address), never a browser User-Agent. titlis.ch was not contacted; HANDOFF schedules that for December.
- The audit skill's four lenses (silent wrong answer, stranger with a clone, leak hunter, bad actor) were run in
  turn in this session, because no subagent tool was available. The bad-actor lens found nothing that crosses a
  trust boundary: the tools read only files authored in this repo, with no eval, shell or unsafe deserialisation.
- `git log -p -20` read line by line; every page read as its reader would read it.

Seen live versus reproduced: R2-1's counterexample was seen live on 9 Nov 2026. R2-3 and R2-7 are reproduced on
scratch copies of the pages (fixture-level). R2-8's gaps are function-level tests of the two regexes.

## Round 1 findings, re-checked

| R1 | Check re-run | Holds? |
|---|---|---|
| R1-1 | grep for the old ranges finds only dated lines; the three answer totals reproduce | **No.** The Hakuba verdict is wrong (R2-1) |
| R1-2 | `grep -n "Email to send\|your four weeks\|your target\|book all three"` finds nothing | Yes |
| R1-3 | Index and README cells split lodging, tax and passes, with the definition stated | **No** on the North America page (R2-2) |
| R1-4 | Two full dated runs render (tests/test_recheck.py) | Yes for full runs; the partial runs the new method produces break the pages (R2-3) |
| R1-5 | 15 commits still carry the personal address; 868d81c still adds a local path; the hook is installed | Deferred (owner); path gap in R2-8 |
| R1-6 | grep matches only "Passo dei Salati 2,971 m", an elevation; St Anton reads −$102 (−4%) | Yes |
| R1-7 | grep finds only corrected lines | Yes |
| R1-8 | Independent scan of every cited room ID: all carry a dated note, except cost-table rows (own dated status) and an illustration at `steep:164` | Yes |
| R1-9 | 71,761 / 23,800 = 3.02 and 71,761 / 28,500 = 2.52 | Yes |
| R1-10 | Every North American all-in equals quote × stated rate within $1; one annotated 11.9% row | Yes (Japanese rows never checked, R2-4) |
| R1-11 | fit-qualifiers ok | Yes |
| R1-12 | A saved non-Airbnb page gives NOT_DETERMINED | Yes, but no code path calls it (R2-9) |
| R1-13 | No browser User-Agent in the repo; method stated in README and HANDOFF | Yes |
| R1-14, R1-15, R1-17, R1-19 | Each verify grep finds nothing | Yes |
| R1-16 | Fixed-date SNOTEL queries return 2, 4 and 3 in; CPC's archived October page returns 200 with the quoted sentence | Yes (one note, R2-13) |
| R1-18 | No undated "live quote"; no August to October deadline offered | Yes; the next deadlines are not covered (R2-6) |

---

## HIGH

### R2-1 · HIGH · Hakuba does have a refundable week under budget; the "none" verdict rests on one listing

The search behind the Japan answer stopped at the first listing whose own page puts the washer in the unit.
That one ($2,619) refunds in full only for 24 hours, and the site concluded that no refundable week exists. The
next listings up were never opened. One of them, read live on 9 Nov, has a free washer in the unit and free
cancellation until February, at $2,697 before tax, about $2,742 with tax: under the $3,000 line.

**Evidence**
- The verdict: `index.html:70` ("Hakuba does not"), `:80` ("Hakuba: no refundable week under budget"), `:153`
  (card label), `:245` (ranking verdict) and `HANDOFF.md:48`.
- The walk: `cheapest_inunit2.py` in the scratch folder sorts the washer-filtered results by price and stops at
  the first in-unit hit (`if flag: break`, line 54). It never reads a cancellation policy.
- Untested candidates, in the scratch folder:
  `awk -F'\t' 'NR>1 && $5!="" && $5+0<2 && $2+0>2618.14 && $2+0<=2955.13' hak_0313.tsv` lists 13 listings within 2 km at
  $2,663–2,895 (7 of them within 1.5 km). $2,955 is the most that stays under $3,000 after the cost model's
  ¥7,000 of tax. None of the 13 is in `data/checks/2026-11-09.tsv`.
- **Seen live, 9 Nov 2026, browser pane at human pace:** room 4721170, Chalet Ryumeiso Hakuba, 0.74 km in the
  raw search, `https://www.airbnb.com/rooms/4721170?check_in=2027-03-13&check_out=2027-03-20&adults=2`. The page
  showed "$2,697 for 7 nights", the amenity list "Free washer – In unit", and "Free cancellation before
  February 11. Cancel before March 6 for a partial refund." The raw search had it at $2,692. With ¥500 per
  person per night at 156 (= $45): $2,742 lodging and tax, $3,561 with two valley passes.
- Its page says the ski areas are "5 minutes away by car" with a shuttle stop outside. The $2,619 pick (1.33 km)
  is no closer, and neither is in Happo village or Wadano, which the card advises (`index.html:155`).
- The starting price is off too. `index.html:80` says washer-filtered listings "start at $1,592"; the raw search
  has room 1812996327187552512 at $1,563, 1.79 km, inside the 2 km the cost table states
  (`data/costs.json:110`), and Airbnb displayed the $1,592 listing as "$1,593".
- The same shortcut decides Zermatt's March row, "No: not refundable" (`data/costs.json:286`): two
  washer-filtered village listings at $2,748 (`wk0306_union.tsv`: rooms 18758028 and 43885505) were not opened.

**Fix:** recompute the Japan answer from listings that meet the brief, as R1-1 asked. Walk the washer-filtered
results in price order, reading washer location and cancellation line, until the first listing that is both
in-unit and refundable, or until lodging plus tax passes $3,000; log every listing opened in
`data/checks/<date>.tsv`. On current evidence the answer is Hakuba 13–20 Mar at $2,742 lodging and tax, free
cancellation before 11 Feb in the listing's local time, $3,561 with passes, a drive or shuttle from the lifts.
Rewrite `index.html:70,80,153,245`, the `hakuba_mar` row and HANDOFF together; do the same walk for Zermatt March.

**Verify:** every "no refundable … under budget" sentence names a logged walk that reached the budget line;
`grep -n "no refundable" *.html HANDOFF.md` returns only sentences backed by such a log.

### R2-2 · HIGH · The North America page still compares Zermatt with lift passes against Telluride without them

This is R1-3's defect, surviving on the page R1-3 cited. On one page, "all-in" means two different things, and
the verdict reads the wrong way round: Zermatt's week is quoted with two lift passes, Telluride's without, and
the text concludes that Zermatt is "inside or barely outside the stated budget" while Telluride "works". On the
page's own budget definition (lodging and tax, lift tickets listed separately), Zermatt is the cheaper of the two.

**Evidence**
- `steep-and-town-2027.html:63`: "Budget US$3,000 a week for the lodging including tax … lift tickets are
  listed separately"; `:195`: "Cheapest all-in = … lodging plus tax and no lift tickets".
- `:62` and `:78`: Telluride "$2,200 – $2,915 all-in", lodging and 17.22% tax.
- `:74`: "A 6-day Zermatt lift pass is from CHF 384 … For two people that is roughly $2,300–3,400 all-in —
  inside or barely outside the stated budget." That range is September lodging ($1,268–2,435) plus two passes
  and tax.
- On one definition, from the index's own cost table (`index.html:272,276`): lodging and tax, Zermatt $1,992
  against Telluride $2,014–2,259; with two 6-day passes, Zermatt from $2,940 against Telluride $5,017–5,262.
- R1-3 cited this sentence (then `steep:74`) and asked for one definition everywhere; its status says Fixed.

**Fix:** state both resorts on one definition, taken from the cost model's spans (`zermatt_jan:lodging_tax`
and `telluride:lodging_tax`, and the `:total` spans where passes are added). Replace "inside or barely outside
the stated budget" with "inside the budget on lodging and tax". On the steep and three-resort pages keep
"all-in" for lodging plus tax and write "with passes" wherever passes are added; add a sitecheck rule that fails
an "all-in" figure which includes passes.

**Verify:** `grep -n "all-in" steep-and-town-2027.html` shows no figure that includes lift passes, and the
Zermatt note's figures sit in `data-cost` spans.

### R2-3 · HIGH · The next documented recheck would wipe 135 of the 158 published rows

The renderer stamps one date on every row of a run, and the new method (R1-13) re-reads only the listings that
drive a recommendation. So the next run either drops every listing it did not re-read from the published
tables, or relabels them with a date on which nobody looked at them.

**Evidence**
- `HANDOFF.md:109-110` (Next 2): re-read the recommended listings, write "`data/checks/<date>.tsv` and a new
  recheck run, then run `tools/recheck.py`".
- `tools/recheck.py:74-78` picks one run; `:231-233` builds each page's table from that run's rows only;
  `:185-189` print one run date for all of them.
- Reproduced on a scratch copy: a run holding the 23 rows that `data/checks/2026-11-09.tsv` covers, rendered
  with `recheck.apply(site, '2026-12-05', runs)`. The recheck tables shrink from 44 to 10 rows (Europe), 36 to 5
  (North America and Japan), 52 to 7 (rentals) and 26 to 1 (Zermatt). The Europe heading becomes "Rechecked 5
  December 2026: 10 of 10 listing-weeks still bookable" (today: 23 of 44), and each intro still says every
  identified listing "was looked up again on 5 Dec 2026". Of 135 status notes, 31 take the new date and 104 keep
  9 Nov; 104 problems are reported, for 89 rooms.
- `tools/recheck.py:336-349`: `apply()` writes the pages before reporting problems, so the command exits 1 after
  the damage is done. The message misleads:
  `no <!-- recheck-note for room 673104662730185469:start --> marker` (`:332,344`), when the room is missing
  from the run, not a marker missing from the page.
- The tests only use full copies of the 158 rows (`tests/test_recheck.py:21-45`), so nothing models a
  partial run.

**Fix:** give each row its own read date and merge runs: the newest reading per (room_id, check_in) wins and
older readings keep their own date. Print the date per row (status cell and note) and split the heading count
by read date ("23 re-read 5 Dec 2026; 135 as read 9 Nov 2026"). `apply()` writes nothing when it reports a
problem. Add a test with a 23-row run.

**Verify:** rerun the partial-run simulation. All four tables keep 158 rows, 23 carry the new date, the notes for
unread rows keep 9 Nov, and the command exits 0; a run missing a cited room changes no file.

---

## MEDIUM

### R2-4 · MEDIUM · Japanese all-ins use an undisclosed ~12% that the cost model dropped, and no check covers them

**Evidence**
- An implied-rate pass over the steep page's priced tables (plain regex; quote against all-in on every row):
  every North American row matches its stated rate. The 13 Japanese rows imply 12.0–12.9% (Hakuba, Myoko,
  Furano, Rusutsu, Wadano: `steep-and-town-2027.html:346,389-392,397-398,401`) and 14.2–14.5% (three Niseko
  rows, `:393-395`), except one Niseko row at 12.0% (`:347`, $1,303 to ~$1,460). The page's tax note (`:158`)
  states no Japanese rate; it says only "Kutchan adds a 2% accommodation tax".
- The cost model taxes Hakuba at ¥500 or ¥1,000 per person per night and Niseko at 2% (`data/costs.json:113-159,
  640-646`); `HANDOFF.md:83` says this replaced "the September ~12% assumption". The steep scorecard still uses
  the 12% figures: Niseko $1,460, Myoko $1,230, Furano $1,460 (`:182,186,189`).
- The rentals page gives Kutchan's tax as 2% (`ski-rentals-2027.html:205`) and as 3% (`:270`, and `:277` "+10%
  VAT + 3% city tax"), and calls Japan's 10% consumption tax "a 10% accommodation tax" (`:205`).
- `tools/sitecheck.py:490-499` (STEEP_RATES) has no Japanese pattern, so `check_all_in_arithmetic` skips all 13
  rows.

**Fix:** one Japan tax table in data: Hakuba ¥500 or ¥1,000 per person per night; Niseko at Kutchan's rate from
the town's own page plus Hokkaido's per-person tax; and whether Airbnb's Japanese totals already include
consumption tax. Recompute the 13 rows and 3 scorecard cells from it, state the rates at `:158`, use one Kutchan
figure on every page, and add Japanese patterns to STEEP_RATES.

**Verify:** the implied-rate pass finds every priced row checked; `grep -n "Kutchan" *.html` gives one rate.

### R2-5 · MEDIUM · The headline totals date their lift passes 9 Nov 2026, but most pass prices are September estimates or 2025/26 prices

**Evidence**
- `README.md:18` and `index.html:260`: "Week for two = lodging + tax + two … 6-day lift passes, priced 9 Nov
  2026". The README rows (`:14-16`) repeat "priced 9 Nov 2026" beside the pass column.
- The pass sources in `data/costs.json`: Telluride $1,430 "(steep-and-town page, September 2026)" (`:88`);
  Hakuba ¥63,900 "(September 2026)" (`:127`); Engelberg CHF 274 "no season given" to 390 "September estimate"
  (`:48`); Whistler and Fernie 2025/26 day prices (`:203,465`); Crested Butte a "2025/26 proxy" (`:428`);
  Jackson and Snowbird "(September page)" (`:315,578`); Chamonix, Alagna and Andermatt estimates. Only Zermatt's
  floor was read on 9 Nov. Conversion uses the 10–11 Sep 2026 rates (`:6`).
- CLAUDE.md: "Every price carries its currency and the date it was quoted." The Europe page's own pass table
  dates each price by season; the README does not.

**Fix:** add a `quoted` date to every pass in data/costs.json and print it in the cost table. Reword both notes
to "lodging priced 9 Nov 2026; lift passes as dated in the cost table, mostly September 2026 estimates;
converted at 10–11 Sep 2026 rates", and the README row notes to "lodging priced 9 Nov 2026".

**Verify:** every `passes` entry in data/costs.json has a `quoted` date, and
`grep -n "priced 9 Nov 2026" README.md index.html` attaches that date to lodging only.

### R2-6 · MEDIUM · Refund windows start closing on 10 December, and nothing on the site or in the checks expires them

**Evidence**
- `data/checks/2026-11-09.tsv`: six listings say "Free cancellation before December 10", two December 17, four
  December 24, one December 26 and six January 4.
- Verdicts depend on them: the cost table says "Yes" for Chamonix and "Yes, on lodging and tax" for Zermatt
  January, each beside "Free cancellation before 10 Dec" (`index.html:276,279`).
- `grep -n -E 'today|date\.today|datetime\.now' tools/*.py tests/*.py` finds nothing. The only past-deadline rule
  (`tools/sitecheck.py:717-718`) matches August to October 2026. On 11 Dec the pages would still present those
  rows as refundable answers, and the pre-push check would pass.

**Fix:** give sitecheck a `--today` option (default today) that fails when a refund cutoff on a "Yes" row or a
pick has passed; print "refund windows read 9 Nov 2026; the first closes 10 Dec 2026" in the index header from
the data; mark lapsed rows "refund window closed" until they are re-read.

**Verify:** `python tools/sitecheck.py --today 2026-12-11` fails on today's pages and passes once those rows are
re-read or marked.

### R2-7 · MEDIUM · The site checks pin 9 November values, so a correct refresh fails the pre-push hook

**Evidence**
- `tools/sitecheck.py:330-331` requires St Anton's change cell to read exactly "−$102 (−4%)"; `:733` requires the
  index header, footer and README to contain "9 November 2026".
- Reproduced on a scratch copy: a later full run in which only St Anton's 9–16 Jan quote moves ($2,459 to
  $2,400) renders with no problems, then `check_currency_labels` reports "St Anton change is not measured from
  the dollar quote (expected −$102, −4%)". A header and README that name "5 December 2026" fail
  `check_dates_stamped` three times. The hook (`tools/hooks/pre-push:12`) then refuses the push.

**Fix:** check invariants, not values: the change cell equals the run's quote minus the September quote; the
header names the latest run's date from the data. Keep the regression tests against 20cb727 by passing their
expected strings in from the test.

**Verify:** the same simulation passes the checks, and the tests that run on 20cb727 still fail there.

### R2-8 · MEDIUM · The privacy scan would not stop a booking written into the public handoff

HANDOFF.md is the only channel the two assistants share. It is public on GitHub and served on the Pages site,
and it already carries booking state ("Nothing is booked", `HANDOFF.md:9`) and a list of last safe cancellation
days for the options (`:71-75`). A first booking would most likely be recorded there, and the scan looks only
for first-person wording.

**Evidence**
- `tools/sitecheck.py:160-173` (PRIVACY_PATTERNS) and `:178`, run on five impersonal phrasings shaped like
  `UNIT is booked for DATES`, `Booked: UNIT, DATES`, `Reserved the UNIT …`, `Booking confirmed for DATES, code
  HM + eight characters` and `User booked the UNIT …`: all five pass. Only `We booked …` and `Our booking …` are
  caught. REVIEW.md, data/ and tests/ are not scanned at all.
- Local paths: `tools/prepush.py:30` and `tools/sitecheck.py:201` both miss the form this machine's Git Bash
  prints (`/c/Users/<name>/…`), and the WSL and macOS forms; the sitecheck scan also misses the
  forward-slash Windows form. Tested with both regexes.
- HANDOFF.md and REVIEW.md return 200 from the Pages site and match the commit.

**Fix:** keep booking state and the cutoff action list in a private note outside any repository, and leave
HANDOFF.md to research state. Extend the patterns to impersonal booking verbs near a room ID or a date and to
Airbnb confirmation-code shapes; scan every tracked text file; add `/[a-z]/Users/[^/]+` and `/mnt/[a-z]/` to
both path checks.

**Verify:** the five placeholder phrasings, and a Git Bash path on an added line, are rejected by
`python tools/sitecheck.py --pre-push`.

### R2-9 · MEDIUM · The R1-12 status rules guard nothing: no code path calls them

**Evidence**
- `grep -rn "listing_status\|classify_listing_text" --include=*.py .` finds only
  `tests/test_listing_status.py`. `tools/recheck.py:95-101` reads statuses straight from
  `data/checks/<date>.tsv`, which a session types by hand; no page text is kept.
- R1-12's status says the code returns NOT_DETERMINED "for listing-page text read in the browser". With the pane
  hidden, pages draw lazily (`HANDOFF.md:30-32`); a half-drawn page or a challenge typed in as "not available"
  goes straight to a published "Not offered", with nothing to catch it.

**Fix:** a small `tools/log_read.py` that takes the pasted page text, runs `classify_listing_text` and appends the
row (status, price line, cancellation line, washer line) to data/checks; or keep those verbatim lines in
data/checks and have sitecheck re-derive each status from them.

**Verify:** a data/checks row whose stored text does not support its status fails sitecheck.

---

## LOW

### R2-10 · LOW · Seventeen recheck quotes are $1 below what Airbnb showed, so one listing can carry two prices

**Evidence:** joining `data/recheck/2026-11-09.tsv` to the raw `price_line` in all.tsv and tight.tsv, 49 of the
66 bookable quotes equal the displayed price and 17 are exactly $1 lower: the pipeline truncated totals such as
906.21, which Airbnb displays as $907. On the site, the Sunny 1-room apartment is $906 at `index.html:82` and
$907 at `:130,271`; Crested Butte is $1,347 in its note (`steep-and-town-2027.html:371`) and $1,348 in the cost
table; Silverado is $1,454 in its notes (`ski-rentals-2027.html:89,225`) against $1,455 read on its page. The
three-resort tables differ from `data/checks` the same way: Revelstoke Retreat $2,256 against $2,257 read,
Revylation $2,862 against $2,863, Comfy Condo $2,998 against $2,999 (`three-resorts-best-snow-2027.html:235,236,
215`), so their all-ins should be $2,618, $3,321 and $3,359.

**Fix:** store the displayed price, correct the 17 run rows and the 3 table rows, and check that each (room,
dates) carries one price across data/checks, the run and the pages.

**Verify:** the join finds 66 of 66 equal.

### R2-11 · LOW · The Zermatt page says the week listings' cancellation terms were not read; they were

**Evidence:** `zermatt-month-stay-2026-27.html:83`, generated from `data/recheck/zermatt-fresh-2026-11-09.html:12`:
"Cancellation terms were not read for any of these." `data/checks/2026-11-09.tsv` has both: 1005849900575274943
"Free cancellation before December 10" and 749164300750846312 "Free cancellation for 24 hours", and
`index.html:83` quotes them.

**Fix:** put the two read lines into the fragment (say the Täsch weeks were not read) and rerun tools/recheck.py.

**Verify:** the Zermatt page no longer says the terms were not read for any of these.

### R2-12 · LOW · Two Zermatt "Not offered" rows come from searches that saw nothing, and neither confirmation is logged

**Evidence:** the raw results give `results_seen` 0 for 1556537260452412398 (5 Dec–5 Jan) and for
1295138371680887002 (5 Jan–5 Feb, 3 adults), 1 for 4735826 and 2 for 16965204; all four publish "Not offered". A
search that saw zero listings is the R1-12 failure signature. Round 1 confirmed the first in the browser, but
that read is not in data/checks; the second was never read (`zermatt-month-stay-2026-27.html:107,153`).

**Fix:** read both listing pages with their dates and guest count and log them, or publish "not determined".

**Verify:** both rows have a data/checks entry.

### R2-13 · LOW · A note written on 9 Nov reports the 12 Nov CPC discussion as already published

**Evidence:** `data/readings.tsv:2`: "The live page was replaced by the 12 Nov 2026 discussion", three days
before that discussion exists.

**Fix:** "From 12 Nov 2026 the live page shows the November discussion; the archived copy keeps the October
text." HANDOFF's Next 1 will add the November reading anyway.

**Verify:** the row is in the future tense, or names the November reading.

### R2-14 · LOW · Counts and words that do not match their data

**Evidence**
- `index.html:78`: "Of the 158 listing-weeks"; 26 of them are Zermatt listing-months
  (`zermatt-month-stay-2026-27.html:84`).
- `three-resorts-best-snow-2027.html:93,272` and `README.md:36`: nineteen policies, nine for 24 hours only, ten
  with a date. The page's tables show 18 (9 and 9), and 15 of the 19 reads are logged nowhere in the repo
  (data/checks holds 4).
- `index.html:170,275` and `HANDOFF.md:55`: "the only September Whistler listing still offered". Two Whistler
  listings on the steep page have no room ID and were never rechecked (`steep-and-town-2027.html:361-362`).
- `three-resorts-best-snow-2027.html:74,85,88-90` calls three listings "Booked" where Airbnb only showed the dates
  as unavailable; the other pages say "not offered (booked, blocked, or a changed minimum stay)".
- Jackson's and Snowbird's passes are "5 to 6 day" tickets in a column of two 6-day passes (`index.html:278,285`).
- `HANDOFF.md:109`: "Before 9 Dec (the earliest cutoff)". The earliest cutoff is "before 10 Dec", so the last
  safe day is 9 Dec.

**Fix:** reword each; log the 15 missing policy reads or say eighteen.

**Verify:** each count reproduces from the data it names.

### R2-15 · LOW · Tool edges that fail quietly

**Evidence**
- With `--root`, five checks still read the working tree's data (`tools/sitecheck.py:245,400,707,778,809`), so a
  run against another copy checks that copy's pages against this copy's data.
- `tools/costs.py:99-108`: `_room_links` knows five weeks; any other week (the three-resort page's 20–27 Feb, for
  example) silently gets an undated listing link. `:88-96`: `_tax_label` prints only the low end of a percent
  range.
- `tools/recheck.py:332,344`: the misleading missing-room message (R2-3).
- `tools/hooks/pre-push:6` prefers `python3`, which on a fresh Windows machine is often the Microsoft Store alias
  stub; it works on this machine, but elsewhere it fails and blocks every push.

**Fix:** pass `root` through to the data loaders; build listing links from ISO dates stored per row; print both
ends of a range; reword the message; prefer `python` on Windows. Add a test for each.

**Verify:** the new tests pass, and costs.py refuses a row whose week it cannot date.

---

## Bigger improvements (ranked)

1. **Readings, not runs.** One table of dated readings (room, dates, read date, method, price line, cancellation
   line, washer line, status), appended by every browser read and merged by the renderer. It fixes R2-3, R2-9 and
   R2-10 together, and lets every row say when it was last seen.
2. **A saved walk log behind every "cheapest" or "none" claim.** Version the non-personal search results and the
   per-listing washer and refund reads under `data/searches/<date>/`, and have sitecheck require a log for each
   "cheapest …" or "no … under budget" sentence. Today a stranger with the repo cannot reproduce any "cheapest
   with a washer in the unit" figure, and R2-1 shows what that hides.
3. **A date-aware check and a "valid until" line**: `--today` in sitecheck, and the first open refund cutoff
   printed in the index header from the data (R2-6).
4. **One tax table for every page**, Japan included, feeding costs.py, the steep page's all-ins and the rentals
   and three-resort tables (R2-4).
5. **A private place for anything booked.** HANDOFF.md stays the research handoff; booking state, cutoff actions
   and timing live in a private note; the scan covers impersonal wording and every path form (R2-8, R1-5).
6. **Invariant checks** in place of 9 Nov literals, so the hook keeps protecting the site after the next refresh
   (R2-7).

---

## Checked and solid

- **Tests and checks.** 19 sitecheck checks ok and 68 unittest cases pass; `costs.py --check` and
  `recheck.py --check` report no drift. `.git/hooks/pre-push` is identical to `tools/hooks/pre-push`, and the
  clone's identity is the noreply address.
- **Publication.** The latest Pages build is "built" at e3866e3, which is HEAD and origin/main. All six pages,
  data/readings.tsv, data/costs.json, README, HANDOFF and REVIEW return 200 and match the commit apart from line
  endings.
- **The three answers, recomputed by hand.** Engelberg: $1,571 + CHF 3.20–4.50 × 14 at 0.81 = $1,626–1,649, plus
  CHF 274–390 × 2 = $2,303–2,612. Telluride: $1,718 and $1,927 × 1.1722 = $2,014–2,259, plus $1,430 × 2 × 1.05 =
  $5,017–5,262. Hakuba: $2,619 + ¥7,000 at 156 = $2,664, plus ¥63,900 × 2 = $3,483. All 48 cost-table cells
  (16 rows × lodging and tax, passes, total) recompute to the dollar from the inputs printed in each row.
- **Recheck statuses from the raw data.** Joining all.tsv and tight.tsv with the hand reads gives 66 bookable, 88
  not offered and 4 removed (3 listings), and each of the 158 published statuses matches its raw source. Washer
  wording among the 66: 15 free in the unit, 27 in the building, 2 paid in the unit, 22 a bare "Washer".
- **Hand-read log.** data/checks has 33 rows: 24 with a free-cancellation date, 4 for 24 hours only, 4 blank and 1
  not available. The 28 outside the three-resort page split 22, 2 and 4, as the README says.
- **Telluride 17.22%**, re-read on the town's taxes page on 9 Nov (one request): SMART 1.07, state 2.90, county
  1.00, town 4.50, food-and-lodging excise 2.00, short-term-rental excise 2.50, town lodgers' 2.00, SMART
  lodgers' 1.25, and "The total tax to be collected on short-term rentals is 17.22%."
- **Readings.** The fixed-date SNOTEL queries return 2, 4 and 3 in. CPC's archived October discussion contains "a
  strong-to-very strong El Niño likely through January-March 2027 (remaining greater than an 83% chance)". BC
  Hydro's file shows 18 cm and 51 mm at 15:45 on 9 Nov.
- **Arithmetic.** Every North American all-in on the steep page matches its stated rate within $1 (the one 11.9%
  row is annotated). The rentals page's all-ins match its stated rates (16, about 15, 20.4, about 16 and 18.5%).
  The three-resort totals of $7,361, $8,285 and $7,751 add up.
- **Links.** 72 of 73 external links outside Airbnb and Booking.com return 200; VRBO returns 429, already
  disclosed. Every internal anchor resolves.
- **History since round 1.** `git log -p 800768a..HEAD` adds no email outside the allow-list, no local path and
  nothing token-shaped. No tracked text file contains mojibake.
- **Calendar.** Easter falls on 28 Mar 2027, Coming of Age Day on 11 Jan, MLK Day on 18 Jan and Presidents' Day on
  15 Feb. Every logged cutoff falls 30, 14, 5 or 1 days before arrival, Airbnb's standard tiers.
