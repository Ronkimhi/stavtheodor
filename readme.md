# Art Radar Website

One self-contained file: `index.html`. No build step, no dependencies. Everything (styles, the archival image, all posts) is inside the single file.

---

## Hosting: GitHub Pages (migrated from Netlify 2026-06-30)

The site is served from the `Ronkimhi/stavtheodor` GitHub repo via GitHub Pages, with `stavtheodor.com` (apex + `www`) pointed at it via `CNAME` and GoDaddy DNS. Pushing to `main` deploys automatically — no manual drag-and-drop step.

**Deploying a change:** `git add`, `git commit`, `git push origin main`. GitHub Pages picks it up within a minute or two.

---

## Adding a new post (the dual-publish flow)

From now on every post goes to both channels:

1. Publish in the WhatsApp group as usual
2. Paste the final version to Claude: *"Here's the final version I published: [paste]"*
3. Claude will:
   - Save it to `B-brain/04-published/01-whatsapp/YYYY-MM-DD-[slug].md` (Published Posts Protocol)
   - Add it to `index.html` at the **top** of the posts section, using the commented `POST TEMPLATE` block inside the file
4. Run `python3 build-post-pages.py`. This regenerates `radar/<slug>/index.html` (a standalone, indexable permalink page) for every post — including the new one — updates `sitemap.xml`, and points each post's JSON-LD `url`/`mainEntityOfPage` at its real permalink instead of a same-page anchor. It also adds a small "Permalink" link under the post's date on the homepage. The homepage's layout, content, and reading experience are untouched — this step only adds the per-post URLs SEO/LLM-citation needs.
5. Commit and push (see Hosting above)

## Adding photos to a post

Send Claude the image file(s) and say which post they belong to. They get optimized into `images/` (max 900px, JPEG ~72 quality, named `YYYY-MM-DD-[slug].jpg`) and referenced from the post, with a quiet caption. The page is designed to look finished with or without them.

## Updating the portfolio slideshow

The portfolio is an inline slideshow in the `#portfolio` section, built from the `.pptx` deck (no longer an external Google Slides link). The 40 slides live as `images/portfolio/slide-01.jpg` … `slide-40.jpg`.

To update it after editing the deck: send Claude the new `.pptx`. Claude renders it (PowerPoint exports it to PDF, then it is rasterized to ~1600px JPEGs), replaces the slides in `images/portfolio/`, and you redeploy. The `.pptx`/PDF and any build scratch files are **never** deployed. If the slide count changes, the `total` in the small `<script>` at the bottom of `index.html` and the `/ 40` in the counter must be updated to match.

## Media notes (2026-06-12 export)

- 15 images from the WhatsApp media export are live on the site: the May 20 gallery picks grid (7), Pollock, the Guggenheim Pop image, Duchamp's Nude Descending a Staircase, and the Fifth Avenue post grid (5)
- The original export (including the raw chat file, which contains member phone numbers and must NEVER be deployed or shared) lives at `B-brain/04-published/01-whatsapp/media-export-2026-06-12/`
- Not used: 3 videos (too heavy for the page; the Clinamen post links the experience instead)
- The June 4 Montclair Art Museum post (Shaffer collection) was added 2026-06-13 after it was initially missed
- The deployed set is everything in this repo: `index.html`, `images/`, `radar/` (generated permalinks), the favicon files, `og-image.jpg`, `sitemap.xml`, `robots.txt`, `llms.txt`, `agent.txt`, `CNAME`, this README. `.pptx`/PDF/build scratch files are never committed.
- `og-image.jpg` is the social share card (the image shown when the link is pasted into WhatsApp, etc.). `favicon.svg` / `favicon-32.png` / `apple-touch-icon.png` are the browser-tab and home-screen icons. All are referenced by absolute URL in the page head, so if the site is ever renamed from `stavtheodor.com`, those URLs must be updated to match.
