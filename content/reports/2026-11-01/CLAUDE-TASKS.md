# Claude tasks from the Nov 1 2026 report

Source: `content/reports/2026-11-01/REPORT.md` and `pages.csv` (GA4 Aug 3 to Oct 31 2026, GSC Sep 26 to Oct 30 2026).

## Rules for every task

- One branch and one PR per task. Never push to main.
- Content-only tasks (copy, titles, metas, FAQs, answers.md, internal links in content/pages/*.json, new guides, meta-refresh redirect stubs) can merge once `python3 tools/check_site.py` passes. Anything touching templates, JS, forms or the build needs Ron's review: open the PR and stop.
- CTA is email only: "Write to Stav" / "כתבו לסתיו", microline "Tell me about the space: the room, the walls, the timeline." No photo upload, no Calendly or booking tool.
- No em or en dashes in any copy. Real facts only; never invent numbers, clients or quotes.
- Public repo: no lead names, lead emails or phones, no referral fee, no client budgets or prices.
- Log every status change (started, PR opened, merged, blocked) in the Status log of `content/INBOUND-PLAN.md`.

## Overlap with content/INBOUND-PLAN.md

R1 and R2 extend T5: where T5 already has approved title and meta values for a page, use those and do not rewrite them. R5 replaces the open part of T6. R6 is the same decision as T7/T8 and stays held.

## R1. Titles and metas for the 7 highest-impression guides (content-only)

Pages (GSC impressions, CTR, position, top query):
- /guide/art-sourcing-for-interior-designers/ (469, 1.07%, 8.0, "art sourcing")
- /guide/dental-office-decor/ (406, 2.22%, 9.3, "dental office decor")
- /guide/restaurant-wall-decor/ (326, 0.61%, 8.2, "restaurant art and decor vendor")
- /guide/hotel-artwork/ (283, 1.06%, 9.0, "guidelines for art in hotels")
- /guide/how-to-hang-pictures/ (231, 0.43%, 16.3, "what is the 60 inch rule for hanging pictures")
- /guide/office-wall-art/ (137, 0.73%, 8.7, "art office")
- /guide/planning-art-in-construction-drawings/ (113, 0.88%, 8.0)

Acceptance:
- Each `<title>` is 60 characters or fewer and starts with the page's top query wording (or its closest natural phrasing).
- Each meta description is 140 to 160 characters, names a concrete benefit and ends with a reason to click.
- H1 still matches the page topic; no body copy removed.
- `tools/check_site.py` passes. Record old and new titles in the PR description.

## R2. Titles and metas for 8 money pages with zero clicks (content-only)

Pages (impressions, position): /advisory/ (149, 8.5), /hotels/ (94, 5.8), /for-designers/ (90, 8.0), /investment-firms/ (58, 7.5), /art-advisor-bergen-county/ (46, 7.0), /medical-practices/ (39, 11.0), /for-brokers/ (32, 11.4), /for-advisors/ (28, 6.7).

Acceptance: same title and meta rules as R1; each title names the audience and place (for example Bergen County, Tenafly, NYC) where the page covers one; `tools/check_site.py` passes; old and new titles listed in the PR.

## R3. Make the Bergen County new-build cluster findable (content-only)

Targets: /art-advisor-bergen-county/ (1 view, 46 impressions, 0 clicks in the window) and /advisory/art-for-a-new-build-in-bergen-county/ (1 view, 0 impressions).

Acceptance:
- Add a contextual link to /art-advisor-bergen-county/ AND to /advisory/art-for-a-new-build-in-bergen-county/ in the body copy of each of: /art-consultant-tenafly-nj/, /art-curator-new-jersey/, /guide/planning-art-in-construction-drawings/, /advisory/commissioning-art-for-a-new-home/, /projects/closter-new-jersey-new-construction/.
- On /art-advisor-bergen-county/ add an FAQ block (3 to 5 questions) answering, in Stav's real process, the questions new-build owners ask: when to bring in an art advisor during construction, working alongside the interior designer or architect, which Bergen County towns are served (Tenafly, Englewood Cliffs, Alpine, Cresskill, Demarest, Closter and others she actually serves). No prices.
- Add the same towns once to `answers.md` if that file lists service areas.
- `tools/check_site.py` passes.

## R4. Get the 7 stuck non-museum pages indexed (content-only)

Discovered, not indexed: /guide/art-advisor-vs-art-consultant/, /advisory/residential-art-consultant/, /advisory/art-for-a-new-apartment-on-a-budget/, /advisory/moved-to-nyc-empty-walls-art/, /advisory/where-to-buy-original-art-nyc/, /radar/four-tribeca-galleries-september-2026/, /radar/three-tel-aviv-shows/.

Acceptance:
- Each page gets at least 2 contextual body links from indexed pages with traffic (pick from /art-curator-new-york/, /advisory/, /radar/, /guide/, /art-curator-new-jersey/, /about/).
- Each is in sitemap.xml with a current lastmod.
- `tools/check_site.py` passes. List the added links in the PR. (Grok Bot will request indexing in Search Console after merge.)

## R5. Redirect stubs for the old Wix URLs still 404 on Google (content-only)

URLs still 404 on Nov 1: /press, /work-1/tel-aviv-apartment, /work-1/luxury-home-in-hertzliya-pituch, /work-1/st-regis-amman-jordan. (/contact and /blog already resolve; leave them.)

Acceptance:
- Each gets a meta-refresh stub with a canonical tag, using the repo's existing redirect stub pattern: /press to /about/, /work-1/tel-aviv-apartment to /projects/tel-aviv-private-residence-shtisel-commission/ only if that is the same project, otherwise /projects/; /work-1/luxury-home-in-hertzliya-pituch to /projects/herzliya-pituach-sea-view-apartment/ if same project, otherwise /projects/; /work-1/st-regis-amman-jordan to /projects/hotels-and-hospitality-collections/.
- Stubs carry `noindex` like /2/ does and are not added to sitemap.xml.
- `curl -s -o /dev/null -w '%{http_code}'` on each live URL returns 200 after deploy. `tools/check_site.py` passes.
- If adding stub files requires a build change, stop and ask Ron.

## R6. Museum indexing (needs Ron's review, hold until Ron OKs, same as T7/T8)

Numbers: 144 museum pages, 126 of the site's 133 discovered-not-indexed URLs, 9 GSC clicks, 0 key events in 12 months; many landings are Direct with 0 to 1 seconds of engagement.

Proposal for Ron: add `noindex, follow` to /museum/artists/* pages with 0 GSC impressions in the window and remove them from sitemap.xml; keep the 17 indexed museum pages (for example /museum/artists/tomb-of-the-leopards/ with 7 clicks on 282 impressions). This is a template and sitemap change, so open the PR and stop for Ron.

## R7. Link each industry guide to its money page (content-only)

Pairs: /guide/dental-office-decor/ and /guide/medical-office-wall-art/ to /medical-practices/; /guide/hotel-artwork/ to /hotels/; /guide/restaurant-wall-decor/ to /restaurants/; /guide/law-office-art/ to /law-firms/; /guide/financial-advisor-office-art/ to /wealth-managers/ and /investment-firms/; /guide/office-wall-art/ and /guide/buy-lease-or-commission-office-art/ to /law-firms/ and /investment-firms/; /guide/art-sourcing-for-interior-designers/ to /for-designers/.

Acceptance: one contextual link in the first two paragraphs and one next to the closing "Write to Stav" CTA on each guide; no new CTA types; `tools/check_site.py` passes.

## R8. Brand query "theodora" (needs Ron's review if a template changes)

"theodora" had 117 impressions at average position 11.9 and 0 clicks. Add or complete Organization / LocalBusiness JSON-LD on the homepage with name "THEODORA", alternateName "Stav Theodor", the Tenafly address as shown on Google Business Profile, and sameAs links to the real profiles already linked in the site footer. If the JSON-LD lives in content/pages/*.json this is content-only; if a template must change, open the PR and stop for Ron. Acceptance: Google Rich Results Test shows the Organization with no errors; `tools/check_site.py` passes.

## Not for Claude (Grok Bot with Ron's yes or no)

- GA4: confirm click_email is a key event; turn on internal traffic and bot filtering. Google settings, needs Ron yes or no.
- Business Profile link: google / listing sent 27 sessions with 0 engaged. Grok Bot will test the profile's website link and report.
- Search Console: request indexing for R4 pages after merge.
