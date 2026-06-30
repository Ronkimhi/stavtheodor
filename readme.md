# Art Radar Website

One self-contained file: `index.html`. No build step, no dependencies. Everything (styles, the archival image, all posts) is inside the single file.

---

## Publish on Netlify (2 minutes)

1. Go to [app.netlify.com](https://app.netlify.com) and log in with the **ronkkimhi@gmail.com** account
2. On the Sites page, find the deploy drop zone (or go to **Add new site → Deploy manually**)
3. Drag the **whole `art-radar-website` folder** (not just the file) onto the drop zone
4. Netlify gives you a link like `something-random.netlify.app`. Rename it: **Site settings → Site details → Change site name** → e.g. `art-radar` → the link becomes `art-radar.netlify.app`
5. Paste that link into the Art Radar group description, as promised in the June 12 post

**Updating the site later:** open the site in Netlify → **Deploys** tab → drag the folder onto the page again. The link stays the same.

**Custom domain (optional, later):** Stav owns **www.stavtheodor.com** (it appears on the portfolio contact card). In Netlify: **Domain settings → Add custom domain** → e.g. `radar.stavtheodor.com`, then add the DNS record Netlify shows you at the domain registrar.

---

## Adding a new post (the dual-publish flow)

From now on every post goes to both channels:

1. Publish in the WhatsApp group as usual
2. Paste the final version to Claude: *"Here's the final version I published: [paste]"*
3. Claude will:
   - Save it to `B-brain/04-published/01-whatsapp/YYYY-MM-DD-[slug].md` (Published Posts Protocol)
   - Add it to `index.html` at the **top** of the posts section, using the commented `POST TEMPLATE` block inside the file
4. Re-deploy: drag the folder onto the Netlify Deploys page again

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
- **Deploy only this folder** (`index.html`, `images/`, the favicon files, `og-image.jpg`, this README). Nothing else should be dragged onto Netlify.
- `og-image.jpg` is the social share card (the image shown when the link is pasted into WhatsApp, etc.). `favicon.svg` / `favicon-32.png` / `apple-touch-icon.png` are the browser-tab and home-screen icons. All are referenced by absolute URL in the page head, so if the site is ever renamed from `stavtheodor.com`, those URLs must be updated to match.
