# Referral page copy: /refer/ (draft for Stav's OK)

For Claude Code to build later as `content/pages/refer.json` (task T9 in claude-code-tasks.md). Not built, not published.

**Build rules**
- English and Hebrew twins for every heading and paragraph.
- No em or en dashes. No fees, prices, percentages, discounts or rewards. Designer terms stay in the private partner sheet.
- Audience order: past clients first (who will mostly refer new homeowners), then friends forwarding a link.
- CTA system (task T3): primary **Book a 15-minute call** (`BOOKING_URL`, not rendered until Ron creates the booking page), secondary **Write to Stav** (the live hero button, `data-write`), and the microline "Tell me about the space: the room, the walls, the timeline." No photo ask and no upload anywhere on the page. The form is the existing free Formspree form after T1, with `referred_by`. Never send a test submission.
- Fact trace: every claim below is already on stavtheodor.com or in `content/BRIEF.md`.

**Suggested head**
- head_title: `Refer a Friend to an Art Advisor` (32 characters, 44 with " · THEODORA")
- meta_description: `Know someone finishing a new home or moving in New Jersey or New York? Send them here. Art curator Stav Theodor starts with a 15-minute call. No pressure.` (154)
- title_en: Know someone with bare walls?
- title_he: מכירים מישהו עם קירות ריקים?

---

## Lead
**EN:** Most of my clients come to me through someone they trust: their designer, or a friend who has seen the walls. If you know someone finishing a new build or moving into a new home, this page is for them.

**HE:** רוב הלקוחות מגיעים אליי דרך מישהו שהם סומכים עליו: המעצב שלהם, או חבר שראה את הקירות. אם אתם מכירים מישהו שמסיים בנייה או עובר לבית חדש, הדף הזה בשבילו.

## If a friend sent you here
**EN:** You are probably close to moving in, or just did. The furniture is in, the walls are not. That is the moment I work best in. I am Stav Theodor, an art curator and advisor based in Tenafly, New Jersey. I represent you, the buyer, not a gallery or a roster of artists, so the art can come from anywhere. My first question is never about style; it is what you want to feel at home.

**HE:** כנראה שאתם לפני כניסה לבית, או רגע אחריה. הרהיטים כבר בפנים, הקירות עדיין לא. זה בדיוק הרגע שבו אני עובדת הכי טוב. אני סתיו תאודור, אוצרת ויועצת אמנות מטנאפליי, ניו ג'רזי. אני מייצגת אתכם, הקונים, לא גלריה ולא רשימת אמנים. השאלה הראשונה שלי היא אף פעם לא על סגנון, אלא מה אתם רוצים להרגיש בבית.

## How it starts
**EN:**
1. Book a 15-minute call, or write to me about the space: the room, the walls, the timeline.
2. I tell you what I see and how I would approach it.
3. If it feels right, we take it from there: sourcing, budget, framing and installation by my own insured team.

**HE:**
1. קבעו שיחה של 15 דקות, או כתבו לי על החלל: החדר, הקירות, לוח הזמנים.
2. אספר לכם מה אני רואה ואיך הייתי ניגשת לזה.
3. אם זה מרגיש נכון, ממשיכים משם: איתור, תקציב, מסגור והתקנה עם צוות מבוטח משלי.

## Already working with a designer?
**EN:** Good. I work alongside interior designers and architects, not around them. Your designer keeps the room and the credit; I bring the art.

**HE:** מצוין. אני עובדת לצד מעצבי פנים ואדריכלים, לא מעליהם. המעצב שומר על החדר ועל הקרדיט, ואני מביאה את האמנות.

## If you are a past client
**EN:** Thank you for the walls we did together. If someone asks you about them, you can send them this page, or simply introduce us by email. I will take good care of them, and I will let you know we spoke.

**HE:** תודה על הקירות שעשינו יחד. אם מישהו שואל עליהם, אפשר לשלוח לו את הדף הזה, או פשוט להכיר בינינו במייל. אשמור עליו היטב, ואעדכן אתכם שדיברנו.

## Proof links (built pages only)
- Closter new construction: /projects/closter-new-jersey-new-construction/
- Manhattan skyline residence: /projects/manhattan-skyline-residence/
- How the process works: /advisory/how-the-art-advisory-process-works/

Claude Code: link only to project pages that exist in the build; check_site must pass.

## CTA block
**Primary button (EN / HE):** Book a 15-minute call / קביעת שיחה של 15 דקות (links `BOOKING_URL`; hidden until it exists)
**Secondary button (EN / HE):** Write to Stav / כתבו לסתיו (same as the live hero button)
**Microline EN:** Tell me about the space: the room, the walls, the timeline.
**Microline HE:** ספרו לי על החלל: החדר, הקירות, לוח הזמנים.
**Under it EN:** Or write to stav@stavtheodor.com or call (201) 351-8367.
**Under it HE:** או כתבו ל stav@stavtheodor.com או התקשרו ל (201) 351-8367.

## Form (reuse the existing form after task T1)
- Required: name and email only. Optional: message ("Tell me about your space"), timeline chips, "Who sent you?" (maps to `referred_by`).
- No photo upload and no file field. No budget field on this page.
