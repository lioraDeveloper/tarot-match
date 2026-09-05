# Aether — Tarot Matchmaker

**Reproduction brief for a new Cursor instance with no access to this repo.**

Build **this product exactly**, not a generic dating app and not a Next.js rewrite. Match stack, UX, rules, and copy tone below. Output a working local app that a user can open at `http://127.0.0.1:8000`.

Brand name: **Aether**. Product type: free tarot-energy dating app. Users 18+ only.

---

## 0. How to use this document

Treat every section as a requirement. If something is unspecified, prefer the simplest local-first choice that still matches the described UX. Do **not** invent social OAuth, Postgres, Redis, or paid ads unless listed. Optional OpenAI enrichment is allowed but **must degrade instantly** to a local interpreter.

Success = a new user can: register → draw 3 cards → see a top match % → keep that chat → open Discover with dozens of fake people (SVG portraits + %) → chat with Oracle bot (welcome + auto-replies) → send a photo in chat → switch EN/HE with RTL → shuffle card **order** every time the chamber opens (visible roman numerals on the back).

---

## 1. Stack (do not substitute)

| Layer | Choice |
|---|---|
| Backend | Python 3.13-compatible **FastAPI** + **uvicorn** |
| Frontend | Single-page app: `static/index.html` + `styles.css` + `app.js` + `i18n.js` + `cards.js` — **no React/Next, no npm** |
| DB | **SQLite** file `tarot_match.db` at project root (`PRAGMA foreign_keys=ON`, WAL) |
| Auth | Email + password. Cookie `tarot_session` (HttpOnly, SameSite=Lax, 14 days). HMAC-signed `user_id`. PBKDF2-HMAC-SHA256, 120000 iterations, format `pbkdf2$120000$salt$hex`. Secret from `APP_SECRET` or default `dev-tarot-match-change-me`. |
| Realtime | WebSocket `/ws/chat/{match_id}` (cookie auth) **plus** REST send + **2s polling** of inbox/thread so chat works without WS |
| Uploads | `static/uploads/` served as static files. Max **5 MB**. Magic-byte sniff: JPEG/PNG/GIF/WEBP only |
| Optional LLM | `OPENAI_API_KEY` + `OPENAI_MODEL` (default `gpt-4o-mini`), 8s timeout, JSON-only; on any failure use local copy |

Dependencies: `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `websockets`.

Run: `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

Ignore: `__pycache__`, `.env`, `*.db`, `*.db-wal`, `*.db-shm`. Track seed portraits: `static/uploads/portraits/*.svg` and `static/uploads/oracle.svg`. Do not git user `*.jpg`/`*.png` uploads.

---

## 2. Visual system

- Dark mystical dating UI: background `#07060f` / deep indigo, gold `#e4c46a`, purple `#8b5cf6`, muted lavender `#b7a8d4`.
- Serif headings (Palatino/Georgia), system UI body.
- Gold/purple bordered panels, pill buttons (solid gold primary, gold-outline ghost).
- RTL when language is Hebrew (`html dir=rtl`). Language toggle **EN | עב** in the nav, persisted `localStorage.aether_lang`. Default: saved lang, else `navigator.language` starting with `he` → Hebrew, else English.
- Copy tone: mystical **but readable**, like a real dating product. Avoid theatrical words: veil, seekers, bound, ritual-as-default. Hebrew should be natural (not calqued).
- Placeholder ad slot (dashed box): “Ad space — Aether stays free…” / Hebrew equivalent. Component conceptually `<BannerAd />`.
- Responsive: at `<900px` chats are inbox **or** thread (back button), not both; Discover/chamber grids tighten. Viewport meta present.

---

## 3. Information architecture (screens)

Unauthenticated: **Landing** → **Register** / **Login**.

Authenticated nav: **Draw** (chamber), **Discover**, **Profile**, **Chats** (with unread badge), **Log out**, language switch.

Post-login routing:

- No energy signature → chamber
- Else if conversations exist (Oracle always creates one) → chats
- Else → discover

Screens:

1. Landing
2. Register / Login
3. Chamber (22 Major Arcana, pick 3: past / present / future)
4. Reading result (signature + top match card)
5. Chats inbox + thread (WhatsApp-like)
6. Discover grid
7. Profile (prefs, photo, draw again)

---

## 4. Data model (SQLite)

### `users`

- `id` TEXT UUID PK  
- `email` UNIQUE, stored lowercased  
- `password_hash`  
- `name`, `birth_date` (ISO date), `gender` (`woman` \| `man` \| `nonbinary`)  
- `looking_for_gender` JSON array of strings (`woman`, `man`, `nonbinary`, `any`)  
- `min_age_preference`, `max_age_preference` integers 18–99  
- `bio` TEXT  
- `energy_signature` JSON nullable  
- `last_spread` JSON nullable  
- `is_premium` INTEGER default 0  
- `last_redraw_at` ISO timestamp nullable  
- `created_at` ISO UTC  
- `photo_url` TEXT nullable  
- `is_bot` INTEGER default 0  

Derived `age` from birth date (not stored).

### `matches`

- `id` UUID  
- `user_id_1`, `user_id_2` FKs  
- `compatibility_score` REAL  
- `mystical_reasoning` TEXT  
- `status` `active` \| `unmatched`  
- `created_at`  

**Multiple concurrent active chats are allowed.** Redrawing cards must **not** close chats unless `unmatch_previous` is true (default **false**). Unmatch is explicit.

### `messages`

- `id`, `match_id`, `sender_id`, `content` (may be empty if image), `timestamp`, `image_url` nullable  

### `conversation_reads`

- PK (`match_id`, `user_id`), `last_read_at` — unread = messages from others after last_read (or all incoming if never read)

---

## 5. Auth & onboarding

Register fields: name, email, password (min 8), birth date, gender select, looking-for checkboxes (default women+men checked), age sliders min/max (defaults 25–40), bio.

Reject inverted age range, duplicate email (409), under-18, future birth date.

On register/login: set session cookie; **always open Oracle bot conversation** with welcome message if empty.

---

## 6. Tarot chamber (core)

Deck: **22 Major Arcana**, ids 0–21, English names The Fool … The World. Hebrew names: הכסיל, הקוסם, הכהנת הגדולה, הקיסרית, הקיסר, הכהן הגדול, המאהבים, המרכבה, העוצמה, הנזיר, גלגל המזל, הצדק, התלוי, המוות, המתינות, השטן, המגדל, הכוכב, הירח, השמש, המשפט, העולם.

Each card has element Fire/Air/Water/Earth, keywords, traits, short “love” sentence (EN + HE).

**Card art:** unique local SVG faces per id (gold/indigo, not identical backs-only). **Card backs:** still gold-bordered backs **plus large roman numeral + faint unique art/hue** so shuffle is visible. Fisher–Yates shuffle:

- Server: `GET /api/tarot/deck` returns shuffled order for current `X-Lang`.
- Client: shuffle again on **every** chamber open (nav Draw, Draw again, Shuffle button). If first card id unchanged after shuffle, rotate by one. 700ms shuffle CSS animation.

User picks **exactly 3 distinct** cards (order = past, present, future). Click toggles. Then “Read my cards”.

`POST /api/tarot/draw` body `{ card_ids: [int,int,int], unmatch_previous: false }`. Persist **English** signature in DB; return localized reading for `X-Lang`.

**Free redraw:** once every **5 minutes** (HTTP 402 with remaining minutes). **Premium** unlimited. First draw always allowed.

Interpretation (local, no API required):

- Dominant element by majority of the 3 cards.
- Archetype from element: Fire · Passion / Water · Depth / Air · Choice / Earth · Devotion (and HE). Overrides: future in {6,14,21} → Weaver; past in {13,16,15} → Phoenix; present in {2,18,9} → Oracle.
- Profile + interpretation strings as templated sentences from the three cards’ love lines + traits.

Compatibility score 62–99:

```
ELEMENT_SCORE (sorted pair):
Fire-Fire 88, Fire-Air 92, Fire-Earth 74, Fire-Water 70,
Water-Water 90, Water-Earth 91, Water-Air 76,
Air-Air 86, Air-Earth 72, Earth-Earth 89, else 75
```

Then: shared card ids → −4 each; no overlap +6; both have cards in {6,14,21} +5; one has {13,15,16,18} and other {17,19,8,14} +4. Round 1 decimal.

After draw: show signature + **top unused human** match (prefer non-bot). Create/reuse `matches` row. Button “Open chat” and “See more people”. Existing chats stay.

---

## 7. Discover

Always in nav (even before draw). Grid of people: photo, name, age, archetype, **compatibility %**, Message / Open chat.

Sort: **Oracle first**, then descending score.

Filters (`passes_filters`):

- Viewer’s age range vs other’s age.
- Viewer’s looking-for vs other’s gender (`any` bypasses).
- Reciprocal age + looking-for **except** emails ending `@demo.local` (demo people skip reciprocal so Discover stays full).
- Bots always pass.
- Unmatched partners excluded from new open (bot may still reopen).
- People already in an active chat: still listed, marked already chatting, reuse thread.

Need energy signature to score; if missing, score 72.

`POST /api/match/open` `{ user_id }` creates/reuses active match.

---

## 8. Chats (WhatsApp-style)

Inbox of **all active** matches: avatar, name, last preview (text or 📷), time, unread badge. Total unread on Chats nav.

Opening a thread marks read. Pinned “Why you matched” insight. Bubbles me/them. Composer + **＋ photo** (multipart `POST /api/chat/image`). Unmatch with confirm (status unmatched; Discover can show them again except blocked humans).

Polling ~2s while on chats. WebSocket broadcasts `{type:"message", message}` when possible.

---

## 9. Oracle bot (required)

- Email `oracle@aether.local`, `is_bot=1`, `is_premium=1`, gender `nonbinary`, looking `any`, ages 18–99, birth `1996-06-21`, cards `[2,18,17]`, photo `/static/uploads/oracle.svg` (moon/star, gold on indigo).
- Display name Oracle / אורקל. Localized bio.
- Password hashed dummy (not for login).
- On every `/api/me` and register/login: `get_or_create_match` with user; if no messages, send welcome (EN/HE).
- After user text: wait ~650ms, pick reply from a pool of 10 (index = `sum(ord(c) for c in content) % 10`). Image replies: 3-line pool by lang.
- Appears in Discover with a %.

---

## 10. Photos

Profile: `POST /api/users/photo` multipart field `photo`. Chat: field `image` + `match_id` + optional `content`. Store UUID filename under `static/uploads/`. Show in inbox, thread header, Discover, profile.

Demo portraits: **deterministic stylized SVG people** (not initials, not stock URLs, no CDN). Seeded from `hash(email+"|"+name)`: skin/hair/eyes/clothes/background, hair styles by gender, optional glasses/beard/earrings. Write `static/uploads/portraits/{email-local-slug}.svg`.

---

## 11. Demo people (seed on every startup, upsert by email)

Password for all: `demo1234`. After defining each row, **force** `looking_for_gender=["any"]`, `min_age_preference=18`, `max_age_preference=99` so Discover is dense. Refresh portrait SVG on upsert. Do **not** delete real users.

46 people (`email` → name, birth, gender, original 3 card ids, bio):

| email | name | birth | gender | cards | bio |
|---|---|---|---|---|---|
| nova@demo.local | Nova | 1996-04-12 | woman | 18,6,17 | Night swims, vinyl, and people who mean what they say. |
| orion@demo.local | Orion | 1992-11-03 | man | 9,1,19 | Architect by day, stargazer by habit. |
| lumen@demo.local | Lumen | 1998-07-21 | nonbinary | 2,14,21 | I collect first sentences and last trains. |
| sol@demo.local | Sol | 1994-01-30 | man | 19,8,6 | Cooks too much food. Believes in second chances. |
| iris@demo.local | Iris | 1997-09-08 | woman | 3,2,17 | Museum benches, strong tea, slow-burn conversation. |
| kai@demo.local | Kai | 1991-05-16 | man | 7,13,10 | Sailing instructor. Terrible at small talk, excellent at weather. |
| mira@demo.local | Mira | 1995-12-02 | woman | 12,11,14 | Therapist off-duty. I still want mystery. |
| ash@demo.local | Ash | 1993-08-19 | nonbinary | 15,8,20 | Poet with a day job in lighting design. |
| noa@demo.local | נועה | 1994-03-14 | woman | 0,4,16 | I bake challah on Fridays and ruin it with too much honey. |
| yonatan@demo.local | יונתן | 1993-02-08 | man | 1,5,10 | Builds furniture. Can't assemble IKEA without a fight. |
| tali@demo.local | טלי | 1994-06-22 | woman | 3,7,19 | Graphic designer who still sketches on receipts. |
| eitan@demo.local | איתן | 1996-08-27 | man | 0,8,21 | Cyclist. Will show you a hidden lookout and a decent espresso. |
| maya@demo.local | מאיה | 1994-01-09 | woman | 4,11,17 | Weekend hikes, weekday playlists, always one book in my bag. |
| roi@demo.local | רועי | 1990-01-19 | man | 5,9,18 | Radio producer. Asks good questions, burns toast. |
| shira@demo.local | שירה | 1993-10-17 | woman | 1,12,16 | Choir kid who grew into someone who sings in the kitchen. |
| adam@demo.local | אדם | 1997-05-03 | man | 6,10,20 | Software, but I swear I'm fun at dinner. |
| yael@demo.local | יעל | 1992-04-28 | woman | 0,3,13 | Runs a tiny plant shop. Talks to the ferns, not sorry. |
| daniel@demo.local | דניאל | 1994-10-12 | man | 4,14,21 | Climbs on weekends. Reads poetry like it's a map. |
| sage@demo.local | Sage | 1992-03-21 | man | 2,8,19 | Bartender who remembers your order and your dog's name. |
| rowan@demo.local | Rowan | 1997-08-16 | nonbinary | 5,11,16 | Makes zines, rides a beat-up bike, believes in long breakfasts. |
| tess@demo.local | Tess | 1993-02-11 | woman | 1,7,17 | I will argue about movies and then cook you pasta. |
| leo@demo.local | Leo | 1999-06-14 | man | 9,13,21 | Photographer. Golden hour is a personality trait. |
| priya@demo.local | Priya | 1995-08-04 | woman | 0,10,15 | Ceramicist. Hands always a little dusty. Heart not. |
| mateo@demo.local | Mateo | 1995-04-02 | man | 3,8,18 | I make a mean shakshuka and a worse first impression. Stay for the second. |
| wren@demo.local | Wren | 1994-11-23 | nonbinary | 4,12,20 | Sound designer. I notice the room before the people. Then the people. |
| nadia@demo.local | Nadia | 1993-12-19 | woman | 2,6,16 | Night-shift nurse. Daytime sun, strong coffee, honest people. |
| felix@demo.local | Felix | 1991-09-18 | man | 5,13,19 | Jazz piano, thrift stores, terrible puns. |
| zara@demo.local | Zara | 1992-05-07 | woman | 1,11,21 | DJ on Saturdays, librarian energy the rest of the week. |
| jonas@demo.local | Jonas | 1998-12-06 | man | 7,14,18 | Marine biologist inland. I miss the water and talk about it anyway. |
| amira@demo.local | אמירה | 1994-11-25 | woman | 0,9,20 | Makes pickles, plans trips, texts back. |
| nico@demo.local | Nico | 1996-01-11 | man | 3,10,16 | Tattoo apprentice. Quiet until the conversation gets real. |
| leila@demo.local | ליילה | 1994-09-30 | woman | 4,8,15 | I collect city maps and get lost on purpose. |
| omer@demo.local | עומר | 1993-07-29 | man | 2,11,19 | Farmer's market loyalist. Brings extra peaches. |
| daphne@demo.local | דפנה | 1991-07-15 | woman | 6,12,21 | Editor. I notice the sentence you almost said. |
| hila@demo.local | הילה | 1993-05-11 | woman | 0,5,14 | Yoga at dawn, leftovers at midnight. Looking for someone who laughs first. |
| gal@demo.local | גל | 1995-02-20 | woman | 1,8,13 | Documentary editor. I'll notice the light in the room before I sit down. |
| sivan@demo.local | סיון | 1994-03-18 | woman | 2,9,16 | I keep a notebook of first dates that went well. The food section is long. |
| elena@demo.local | Elena | 1991-08-09 | woman | 3,11,20 | Violin on Tuesdays, sea on Fridays. I text when I say I will. |
| ravi@demo.local | Ravi | 1992-11-21 | man | 7,12,19 | Cooks too hot, apologizes too late, stays for dessert. |
| inbar@demo.local | ענבר | 1996-09-04 | woman | 5,10,17 | Architect of tiny apartments and large breakfasts. |
| tom@demo.local | תום | 1994-06-01 | man | 0,8,18 | Trail runner. Will share water and a terrible joke. |
| lina@demo.local | Lina | 1997-03-27 | woman | 2,14,21 | Makes playlists named after weather. Currently: warm front. |
| ido@demo.local | עידו | 1990-12-14 | man | 4,9,16 | History teacher. Knows too many stories and one good pasta. |
| noga@demo.local | נגה | 1995-07-08 | woman | 1,6,20 | I keep succulents alive. People, we'll see. |
| samir@demo.local | Samir | 1993-01-26 | man | 3,13,19 | Saxophone on the roof when the neighbors forgive me. |
| ruth@demo.local | רות | 1991-04-16 | woman | 8,11,17 | Bookstore mornings. I'll dog-ear your favorite page. |

---

## 12. HTTP API

All JSON APIs except uploads: `Content-Type: application/json`. Send header **`X-Lang: en|he`**. Errors: `{ "detail": "<localized string>" }`.

| Method | Path | Notes |
|---|---|---|
| GET | `/` | SPA, `Cache-Control: no-store` |
| GET | `/api/tarot/deck` | shuffled 22 `{id,name,element}` |
| POST | `/api/auth/register` | sets cookie |
| POST | `/api/auth/login` | |
| POST | `/api/auth/logout` | clears cookie |
| GET | `/api/me` | user, conversations, unread_total, monetization flags, active_match=latest inbox item |
| PUT | `/api/users/preferences` | |
| POST | `/api/users/photo` | multipart |
| POST | `/api/tarot/draw` | |
| GET | `/api/match/find` | top unused candidate |
| GET | `/api/discover` | `{ people: [...] }` |
| POST | `/api/match/open` | `{user_id}` |
| GET | `/api/conversations` | |
| GET | `/api/chat/{matchId}` | marks read |
| POST | `/api/chat/send` | `{match_id, content}` |
| POST | `/api/chat/image` | multipart |
| POST | `/api/match/unmatch` | `{match_id}` |
| WS | `/ws/chat/{matchId}` | |

Monetization placeholders: `is_premium` default false; locked flags `unlimited_redraws`, `who_drew_for_you`, `global_filters`. No payments.

---

## 13. Suggested file layout

```
app/__init__.py
app/main.py          # FastAPI routes
app/db.py
app/auth.py
app/tarot.py         # 22 cards, interpret, compatibility, localize
app/matching.py
app/seed.py
app/bot.py
app/portraits.py     # SVG generator
static/index.html    # loads i18n.js, cards.js, app.js
static/styles.css
static/app.js
static/i18n.js       # full EN+HE UI strings + card name arrays
static/cards.js      # CARD_SVG[0..21]
static/uploads/oracle.svg
static/uploads/portraits/*.svg  # generated on seed
requirements.txt
README.md
```

Startup: `init_db()` → mkdir uploads → `seed_demo_users()` → `ensure_bot_user()`.

---

## 14. i18n UI keys (implement both languages)

Nav: Draw / Discover / Profile / Chats / Log out. Hebrew: חדר/גילוי/פרופיל/שיחות/יציאה (or equivalent natural labels matching current app: Draw=חדר or “קלפים” — use **חדר / גילוי / פרופיל / שיחות / יציאה**).

Landing EN: kicker “Tarot dating”; title “Meet someone whose cards complete yours.”; CTAs “Get started” / “I have an account”.

Chamber: “Pick three cards by instinct.” Slots Past / Present / Future. Buttons Shuffle / Read my cards.

Profile: “Draw again” (not weekly). Note: chats survive redraw. Free redraw every 5 minutes.

Chats: “Say hello.” placeholder “Message…”.

Include Hebrew card names in `I18N.he.cards[0..21]` matching HE_CARDS.

---

## 15. Out of scope (do not build)

Social login, real AdSense, Stripe, Postgres/Redis, native iOS/Android stores, public internet deploy, deleting user DBs, weekly redraw (old spec — **wrong**).

---

## 16. Acceptance checks

1. Fresh DB: 46 demo + Oracle; Discover for a typical 25–40 looking-for-women/men user shows a large grid with portraits and %.
2. Register → chamber cards **change order** on each visit; backs show roman numerals.
3. Draw → top match + Oracle already in Chats with unread welcome.
4. Second chat from Discover does not close the first.
5. Bot replies to text and photos.
6. EN/HE toggle flips copy, RTL, card names, bot name אורקל.
7. Second draw within 5 minutes → 402 for free user.
8. Profile photo appears in Discover/inbox; chat image renders in a bubble.
