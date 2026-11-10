# Steep skiing with a real town, 2027

Ski research for winter 2027: refundable lodging under US$3,000 a week, priced for two sharing, Saturday to Saturday, in January and March 2027.

**[Read the combined verdict →](https://samueljwebber.github.io/ski-rentals-2027/)**

The brief was refined partway through to a strict priority order: **terrain first**, then **walking distance to a lift**, then **a real town** with a gym, a supermarket and life after skiing. The benchmark was Zermatt's shape at a lower price, with Jackson as the counter-example of a great mountain whose base is cut off from any town.

## The answers

<!-- answers:start -->
| | Resort | Lodging for two + tax | Two 6-day passes | Week for two | Note |
|---|---|---|---|---|---|
| Europe | **Engelberg** | $1,626–1,649 | $677–963 | $2,303–2,612 | 9–16 Jan 2027, lodging priced 9 Nov 2026. Washer in the flat; free cancellation before 4 Jan. The lift-pass price is unverified. |
| North America | **Telluride** | $2,014–2,259 | $3,003 | $5,017–5,262 | 23–30 Jan 2027, lodging priced 9 Nov 2026. Lift 7 a short walk away; free cancellation before 24 Dec. An Epic Pass covers the lifts. |
| Japan | **Hakuba** | $2,742 | $819 | $3,561 | 13–20 Mar 2027, lodging priced 9 Nov 2026. Washer in the unit; free cancellation before 11 Feb; a 5-minute drive or a shuttle ride from the lifts. January starts at $5,605 before tax. |

Week for two = lodging + tax + two adult 6-day lift passes; food and travel left out. Lodging priced 9 Nov 2026; lift passes as dated in the cost table, mostly September 2026 estimates; converted at the 10–11 Sep 2026 rates. The US$3,000 budget is tested against lodging plus tax. Every component and its source is in the [cost table](https://samueljwebber.github.io/ski-rentals-2027/#costs), generated from `data/costs.json`.
<!-- answers:end -->

Engelberg has 2,017 m of lift-served vertical, three glaciers, the Galtiberg and the Laub, and is best in January. Telluride's lifts launch off the town grid; March is its peak season. Hakuba is the only Japanese mountain here with sustained steep lift-served terrain.

## Reports

- **[index.html](index.html)** — the combined verdict across all three regions, the full ranking, and the findings that changed the shortlist.
- **[alps-extreme-ski-2027.html](alps-extreme-ski-2027.html)** — Europe, terrain first. 24 priced listings, lift-pass comparison, gym and supermarket data.
- **[steep-and-town-2027.html](steep-and-town-2027.html)** — North America and Japan, terrain first. 19 resorts, 60 priced options.
- **[ski-rentals-2027.html](ski-rentals-2027.html)** — the original brief, ranked on amenities and price rather than terrain.
- **[three-resorts-best-snow-2027.html](three-resorts-best-snow-2027.html)** — Revelstoke, Telluride and Big Sky, each in its best-snow week, with refundable picks under $3,000 and the 2026-27 El Niño outlook. Refreshed 9 November 2026.
- **[zermatt-month-stay-2026-27.html](zermatt-month-stay-2026-27.html)** — the benchmark itself: a month in Zermatt with a washer, by month and location, against a 10k budget.

## Research notes

Airbnb search pages quote in **US dollars by default regardless of country** — verified at a 1.383 ratio on the same Whistler listing. An earlier version of the rentals report divided Canadian figures by 1.38 and understated Whistler, Tremblant and Sun Peaks by about 38%; that is corrected. Airbnb's washer filter is also unreliable, surfacing listings with shared or surcharged laundry, so only amenities confirmed on the listing page are marked as in-unit.

Airbnb's free-cancellation badge is not the policy. Of nineteen listing policies read for the three-resort report on 9 November 2026, nine refunded in full only within 24 hours of booking. Of 28 more read the same day for the listings the other pages recommend, 22 showed a free-cancellation date, 2 refunded in full only for 24 hours and 4 did not render the line. Only the line on the listing page or at checkout counts.

The detailed pages were researched on 10 to 11 September 2026. On 9 November 2026 every Airbnb listing they identified by room ID was rechecked, the answers and the three-resort report were repriced, and each figure on the pages says which date it comes from. Re-check prices, cancellation terms and lift status before booking.

## How these pages are maintained

- **Costs.** Every week-for-two figure comes from [`data/costs.json`](data/costs.json): lodging, tax and two 6-day passes, each with its source. `python tools/costs.py` writes the figures into the pages and this README.
- **Rechecks.** A recheck run is `data/recheck/<date>.json` and `.tsv`; `python tools/recheck.py` renders the dated recheck sections and the status line on every listing a page cites. Listing pages read by hand go in `data/checks/<date>.tsv`.
- **Checks.** `python tools/sitecheck.py` and `python -m unittest discover -s tests` run with the standard library and no network. `sh tools/install-hooks.sh` installs a pre-push hook that runs them and rejects personal emails, local paths and tokens in outgoing commits.
- **How listings are rechecked.** Only the listings that drive a recommendation, each opened in a browser at human pace on the listing page itself, with its dates in the address. No scripted scraping and no browser disguise. Stop at the first HTTP 429, challenge or CAPTCHA and record it; never work around one. The scripts used for the 9 November run sent a browser User-Agent and are retired.
