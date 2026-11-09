# ski-rentals-2027 handoff

Rewritten **2026-11-09** (Claude Code). Read `CLAUDE.md` first for the rules, then this for what is true now.
**Rewrite this file at the end of every session — never append.** Under 150 lines.

## State

**Published**, at https://samueljwebber.github.io/ski-rentals-2027/ . Six pages, all linked from `index.html`
and `README.md`: the combined verdict (index), the alps extreme list, steep-and-town, the rentals shortlist,
the Zermatt month-stay report, and the three-resort best-snow report. Nothing is booked. Nothing in flight.

Verified live on 2026-11-09: Pages build `built` at commit a94b59b; the three-resort page returns 200 with the
9 November text; the index links both the three-resort and Zermatt pages.

Prices: the three-resort page was refreshed **2026-11-09**. Every other page still carries quotes from
**10–11 Sep 2026** (Zermatt: 10 Sep). Those are now two months old and were not re-checked.

## The brief this answers

Steep terrain first, then a short walk to the lift, then a real town. **Zermatt is the benchmark.** Lift speed
and real lift infrastructure count; marketing claims do not. Current answers: Engelberg, Telluride, Hakuba.
Hard rules in the three-resort page: refundable, under US$3,000 all-in for two, washer in the unit.

## Three-resort report: what is true on 2026-11-09

All three September picks are gone: Revelstoke's Begbie Retreat and Telluride's Clean & Cozy Studio are booked
for their weeks; the Telluride Main St alternative is booked too (its washer is now confirmed in-unit). Big
Sky's "Cute, Cozy & Fun" (51600238) lists washer and dryer as **not included**, so it fails the washer rule.

New picks, each with a free-cancellation date read on its own listing page:

| Week | Listing (Airbnb id) | Quote, USD, before tax | All-in | Full refund until |
|---|---|---|---|---|
| Revelstoke 23–30 Jan | New Condo with Mountain Views and Rooftop Hot tub (1521039495192820325) | $1,945 | $2,256 (+16%) | 22 Jan |
| Telluride 20–27 Feb | West Telluride Studio (29856063) | $2,152 | $2,523 (+17.22%) | 21 Jan |
| Big Sky 6–13 Mar | A Little Condo at Big Sky Montana (9624791) | $2,305 | $2,582 (+12%) | 4 Feb |

Total $7,361. Other new findings on the page: a strong El Niño is forecast (NOAA CPC, >83% through Jan–Mar
2027), with south-central Montana leaning dry and western Colorado near even; Telluride is on Epic while Big
Sky and Revelstoke are on Ikon/Mountain Collective; opening days 26 Nov (Telluride), 25 Nov (Big Sky), 5 Dec
(Revelstoke). Two corrections to the September text: the Revelstoke bus runs every 30–45 minutes, not every
15; and Presidents' Day is 15 Feb 2027, so a 20 Feb start already clears it.

## Choices made this session, and why (reversible)

- **Telluride moved from 27 Feb–6 Mar to 20–27 Feb.** On 27 Feb nothing in town with an in-unit washer is both
  refundable and under $3k: the refundable one (15985907) is $3,448 all-in; the in-budget one (19811781) is
  $2,912 but refunds in full only for 24 h. 20–27 Feb is still in Telluride's snowiest month (OnTheSnow
  averages). Both 27 Feb options stay on the page as alternatives. Cost: Telluride and Big Sky are no longer
  back-to-back.
- **Refundability ranked above the washer location wording.** The Revelstoke pick lists "Washer" with no
  location (its dryer says in-unit). Two Revelstoke condos that do say "Free washer – In unit" (Revyverse
  1020383229264071150 at $2,159; 53958745 at $2,662) refund in full only for 24 h.
- **Big Sky pick has the weakest rating (4.48/119)** and its washer and 10-minute walk come from the host's
  description. The better-rated Mountain Village condo (688364107479787274, $2,857) refunds 24 h only.
- The unpushed commit 2eac02b was pushed unchanged: it held research-window dates only, and its author email was
  already on every public commit. This session's commits use the GitHub noreply address.
- `index.html` headline "Verify before you commit" became "Checks still open before committing" (rule:
  headlines are never commands).

## How it was verified (method worth reusing)

- **Plain HTTP works for Airbnb search and listing data.** Search pages server-render each result's 7-night
  total before taxes, rating and approximate coordinates. Listing pages server-render the full amenity list,
  including items marked "not included" and the in-unit / in-building / paid qualifiers on the washer — the
  "behind a fold" problem from September does not apply to this data. Neither gives the price on a listing
  page or the cancellation policy.
- Useful search parameters: `amenities[]=33` (washer), `room_types[]=Entire home/apt`, `currency=USD`.
  `flexible_cancellation=true` filters but is **incomplete**: it missed 9624791, which has free cancellation.
  Read each policy on the listing page instead.
- **Prices and cancellation lines** were read in the Claude desktop app's built-in browser, because the Claude
  in Chrome extension was not connected. When that pane is hidden, Airbnb pages do not render until a
  screenshot is taken; scroll, screenshot, then read `document.body.innerText`.
- Official facts (season dates, taxes, passes, CPC outlook, BC rules, shuttle) came from a research subagent
  using WebFetch, every one with URL and date; they are cited in the page footer.
- The scripts were scratch-only and are not in the repo. Re-creating them takes about 30 lines each.

## Unverified or open

- Revelstoke pick: where the washer is (listed without a location).
- Big Sky pick: washer and dryer named in the description only; walk time is the host's claim.
- Lead not on the page: "Basecamp Resorts Revelstoke I 1 Bedroom Apartment" (45117750), $1,840 before tax for
  23–30 Jan, matched the free-cancellation filter, washer listed without location. Possibly downtown, which
  would help the town criterion. Its policy line and address were not read.
- Telluride's 17.22% tax was read from the Wayback copy (dated 2025-12-23); telluride-co.gov did not resolve.
- Big Sky's own snow report did not load; Revelstoke's still showed last spring's text. Revelstoke closing
  date not found on the resort site. No 2026-27 BC Transit Route 5 timetable yet (latest notice 13 Nov 2025).
- OnTheSnow monthly averages on the page were read 14 Sep 2026, not re-read.
- `index.html` says Telluride's Lift 7 and 8 replacements were "approved in June 2026"; the US Forest Service
  project page read "Pre NEPA" on 9 Nov 2026 with no decision signed. Not resolved; the index text is unchanged.
- Big Sky tram per-ride price for 2026-27 not found.

## Next

1. Re-check the CPC ENSO update (12 Nov 2026, then monthly) and the three resorts' bases through December; the
   page's refund deadlines (21 Jan, 22 Jan, 4 Feb) are the decision points.
2. Refresh the other pages' September prices (index, alps, steep-and-town, rentals, Zermatt), at least the
   headline picks, the same way: search totals and amenities over HTTP, policies on the listing page.
3. Resolve the Lift 7/8 approval discrepancy in `index.html`.

## Needs the user

- Whether moving Telluride to 20–27 Feb is acceptable, or whether to pay $3,448 (refundable) or accept a
  24-hour refund window ($2,912) to keep 27 Feb.
- Any booking or host message (washer location for the Revelstoke pick) — assistants do not book or contact.
- Claude in Chrome was not connected this session; the built-in browser was used instead. No action needed
  unless Chrome is preferred.

## Corrections already made — do not undo them

Andermatt's queue figures are unsourceable and size is the real caveat. St Anton is a European co-leader, kept
off the top by the washer and not by price. Fernie's Polar Peak rarely opens and its gym is unverified.
Airbnb quotes USD by default — an unlabelled figure caused one published error. The Revelstoke bus is every
30–45 minutes, not 15. Airbnb's free-cancellation badge is not the policy: 6 of 11 policies read on 9 Nov
refunded in full for 24 hours only.

## Standing

**This repo is public.** No personal details, no booking references, no payment information. Every price
carries its currency and the date it was quoted. A claim that cannot be sourced is cut or marked
unsourceable, not softened.
