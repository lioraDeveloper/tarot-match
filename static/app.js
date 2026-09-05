const ROMAN = ["0","I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX","XXI"];
const LANG_KEY = "aether_lang";

function detectLang() {
  const saved = localStorage.getItem(LANG_KEY);
  if (saved === "he" || saved === "en") return saved;
  return (navigator.language || "").toLowerCase().startsWith("he") ? "he" : "en";
}

const state = {
  user: null,
  match: null,
  conversations: [],
  unreadTotal: 0,
  discover: [],
  deck: [],
  selected: [],
  shuffling: false,
  revealed: false,
  reading: null,
  messages: [],
  error: "",
  view: "landing",
  ws: null,
  lang: detectLang(),
  pollId: null,
  mobileThread: false,
  deferredInstall: null,
  showInstall: false,
  union: null, // { phase, match, partnerName, showGreen }
};

const $app = document.getElementById("app");

function t(key) {
  const pack = I18N[state.lang] || I18N.en;
  return pack[key] ?? I18N.en[key] ?? key;
}

function cardName(id) {
  const pack = I18N[state.lang] || I18N.en;
  return pack.cards[id] || I18N.en.cards[id] || "";
}

function elementName(el) {
  const key = String(el || "").toLowerCase();
  if (key === "fire" || key === "water" || key === "air" || key === "earth") return t(key);
  return el || "";
}

function applyDir() {
  const pack = I18N[state.lang] || I18N.en;
  document.documentElement.lang = pack.htmlLang;
  document.documentElement.dir = pack.dir;
  document.title = state.lang === "he" ? "Aether — שידוך בטארוט" : "Aether — Tarot Matchmaker";
}

function localizeError(msg) {
  const map = {
    "Sign in to continue.": { he: "צריך להתחבר כדי להמשיך." },
    "Sign in to enter the chamber.": { he: "צריך להתחבר כדי להמשיך." },
    "Session expired. Sign in again.": { he: "פג תוקף החיבור. צריך להיכנס שוב." },
    "Session expired.": { he: "פג תוקף החיבור. צריך להיכנס שוב." },
    "Birth date must be YYYY-MM-DD.": { he: "תאריך לידה בפורמט YYYY-MM-DD." },
    "You must be 18 or older to join.": { he: "ההרשמה מותרת מגיל 18 ומעלה." },
    "Birth date cannot be in the future.": { he: "תאריך לידה לא יכול להיות בעתיד." },
    "The age range is backwards.": { he: "טווח הגילים הפוך." },
    "Age range is inverted.": { he: "טווח הגילים הפוך." },
    "That email already has a profile.": { he: "לאימייל הזה כבר יש פרופיל." },
    "Email or password did not match.": { he: "אימייל או סיסמה לא נכונים." },
    "Select exactly three distinct Major Arcana cards.": { he: "יש לבחור בדיוק שלושה קלפי ארקנה ראשית שונים." },
    "Chat not found.": { he: "השיחה לא נמצאה." },
    "Thread not found.": { he: "השיחה לא נמצאה." },
    "This chat is closed.": { he: "השיחה הזאת נסגרה." },
    "This connection is closed.": { he: "השיחה הזאת נסגרה." },
    "That's not your chat.": { he: "זאת לא השיחה שלך." },
    "Not your thread.": { he: "זאת לא השיחה שלך." },
    "Please choose a photo (JPG, PNG, WEBP, or GIF).": { he: t("notImage") },
    "Photo must be under 5 MB.": { he: t("photoTooBig") },
    "Add a message or a photo.": { he: "צריך הודעה או תמונה." },
    "That profile isn't available.": { he: "הפרופיל הזה לא זמין." },
    "Draw your cards first — then you can browse people.": { he: t("needDraw") },
  };
  if (state.lang === "he" && map[msg]?.he) return map[msg].he;
  if (state.lang === "he" && msg && (msg.startsWith("Free accounts can redraw") || msg.startsWith("Free seekers may redraw"))) {
    return msg
      .replace("Free accounts can redraw every 5 minutes. Next draw in about ", "בחשבון חינמי אפשר לקרוא מחדש כל 5 דקות. הפתיחה הבאה בעוד כ־")
      .replace("Free accounts can redraw once a week. Next draw in about ", "בחשבון חינמי אפשר לקרוא מחדש כל 5 דקות. הפתיחה הבאה בעוד כ־")
      .replace("Free seekers may redraw once per week. Next opening in ~", "בחשבון חינמי אפשר לקרוא מחדש כל 5 דקות. הפתיחה הבאה בעוד כ־")
      .replace(" min. Premium removes the wait.", " דקות. בפרימיום אין המתנה.")
      .replace("h. Premium removes the wait.", " דקות. בפרימיום אין המתנה.")
      .replace("h. Premium unlocks unlimited rituals.", " דקות. בפרימיום אין המתנה.");
  }
  return msg;
}

function shuffleDeck() {
  const prevFirst = state.deck[0] && state.deck[0].id;
  const deck = (state.deck || []).slice();
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  if (deck.length > 1 && prevFirst !== undefined && deck[0].id === prevFirst) {
    deck.push(deck.shift());
  }
  state.deck = deck;
}

function openChamber() {
  state.selected = [];
  state.revealed = false;
  state.error = "";
  shuffleDeck();
  state.shuffling = true;
  state.view = "chamber";
  render();
  setTimeout(() => {
    if (state.view !== "chamber") return;
    state.shuffling = false;
    render();
  }, 700);
}

function navigate(view) {
  if (view === "chamber") {
    openChamber();
    return;
  }
  state.view = view;
  state.error = "";
  if (view !== "union") state.union = null;
  if (view !== "chat") state.mobileThread = false;
  render();
  if (view === "discover") loadDiscover();
  if (view === "chat") {
    (async () => {
      await refreshInbox();
      const threadVisible = state.mobileThread || window.matchMedia("(min-width: 900px)").matches;
      if (state.match && threadVisible) await loadChat(state.match.id);
      if (state.view === "chat") render();
    })();
  }
}

async function setLang(lang) {
  state.lang = lang;
  localStorage.setItem(LANG_KEY, lang);
  applyDir();
  if (state.user) {
    try {
      await hydrateMe();
      if (state.view === "chat" && state.match) await loadChat(state.match.id);
      if (state.view === "discover") await loadDiscover();
    } catch {
      /* stay on current view */
    }
  }
  render();
}

async function api(path, opts = {}) {
  const extra = opts.headers || {};
  const headers = { "X-Lang": state.lang, ...extra };
  const isForm = opts.body instanceof FormData;
  if (!isForm) headers["Content-Type"] = extra["Content-Type"] || "application/json";
  else delete headers["Content-Type"];
  const res = await fetch(path, {
    credentials: "include",
    ...opts,
    headers,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    const raw = typeof detail === "string" ? detail : (detail && JSON.stringify(detail)) || t("veilFailed");
    throw new Error(localizeError(raw));
  }
  return data;
}

function applyMe(me) {
  state.user = me.user;
  state.conversations = me.conversations || [];
  state.unreadTotal = me.unread_total || 0;
  if (state.match) {
    const still = state.conversations.find((c) => c.id === state.match.id);
    if (still) state.match = still;
  } else if (me.active_match) {
    state.match = me.active_match;
  }
}

async function hydrateMe() {
  const me = await api("/api/me");
  applyMe(me);
  if (state.reading && state.user.last_spread) {
    state.reading = {
      energy_signature: state.user.energy_signature,
      last_spread: state.user.last_spread,
    };
  }
  return me;
}

async function boot() {
  applyDir();
  startPolling();
  try {
    const me = await hydrateMe();
    const deck = await api("/api/tarot/deck");
    state.deck = deck.cards;
    if (!state.user.energy_signature) navigate("chamber");
    else if ((me.unread_total || 0) > 0 || (me.conversations || []).length) navigate("chat");
    else navigate("discover");
  } catch {
    const deck = await api("/api/tarot/deck");
    state.deck = deck.cards;
    navigate("landing");
  }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function initials(name) {
  const parts = String(name || "?").trim().split(/\s+/);
  const letters = (parts[0]?.[0] || "?") + (parts[1]?.[0] || "");
  return letters.toUpperCase();
}

function avatarHtml(person, cls = "") {
  const url = person?.photo_url;
  const name = person?.name || "";
  if (url) {
    return `<img class="avatar ${cls}" src="${esc(url)}" alt="${esc(name)}" />`;
  }
  const extra = person?.is_bot ? " avatar-bot" : "";
  return `<div class="avatar avatar-fallback ${cls}${extra}" aria-hidden="true">${esc(initials(name))}</div>`;
}

function unreadBadge(n) {
  const count = Number(n) || 0;
  if (count <= 0) return "";
  return `<span class="badge">${count > 9 ? "9+" : count}</span>`;
}

function langSwitch() {
  return `<div class="lang-switch" role="group" aria-label="Language">
    <button type="button" class="${state.lang === "en" ? "on" : ""}" data-lang="en">EN</button>
    <button type="button" class="${state.lang === "he" ? "on" : ""}" data-lang="he">עב</button>
  </div>`;
}

function navBar() {
  const unread = unreadBadge(state.unreadTotal);
  const links = state.user
    ? `<button class="link" data-go="chamber">${esc(t("navChamber"))}</button>
       <button class="link" data-go="discover">${esc(t("navDiscover"))}</button>
       <button class="link" data-go="profile">${esc(t("navProfile"))}</button>
       <button class="link" data-go="chat">${esc(t("navChat"))}${unread}</button>
       <button class="link" id="logout">${esc(t("navLeave"))}</button>`
    : "";
  return `${installBar()}<header class="nav">
    <div class="brand">${esc(t("brand"))}</div>
    <div class="nav-end">${links}${langSwitch()}</div>
  </header>`;
}

function installBar() {
  if (!state.showInstall) return "";
  const canPrompt = !!state.deferredInstall;
  const cta = canPrompt
    ? `<button type="button" class="primary small" id="install-app">${esc(t("installCta"))}</button>`
    : `<span class="muted" style="font-size:0.78rem">${esc(t("installHowIos"))}</span>`;
  return `<div class="install-bar" role="region" aria-label="${esc(t("installTitle"))}">
    <div class="install-copy"><strong>${esc(t("installTitle"))}</strong> — ${esc(t("installBody"))}</div>
    <div class="actions">${cta}
      <button type="button" class="ghost small" id="install-dismiss">${esc(t("installLater"))}</button>
    </div>
  </div>`;
}

function tabBar() {
  if (!state.user) return "";
  const unread = unreadBadge(state.unreadTotal);
  const items = [
    ["chamber", "✧", "navChamber"],
    ["discover", "◎", "navDiscover"],
    ["chat", "✎", "navChat"],
    ["profile", "◉", "navProfile"],
  ];
  const tabs = items.map(([view, ico, label]) => {
    const on = state.view === view || (view === "chamber" && state.view === "reading");
    const badge = view === "chat" ? unread : "";
    return `<button type="button" class="${on ? "on" : ""}" data-go="${view}" aria-current="${on ? "page" : "false"}">
      <span class="tab-ico" aria-hidden="true">${ico}</span>
      <span>${esc(t(label))}${badge}</span>
    </button>`;
  }).join("");
  return `<nav class="tabbar" aria-label="Aether">${tabs}</nav>`;
}

function adSlot() {
  return `<aside class="ad-slot" data-component="BannerAd">${esc(t("adSlot"))}</aside>`;
}

function landing() {
  return `${navBar()}<div class="shell center">
    <p class="hero-kicker">${esc(t("landingKicker"))}</p>
    <h1>${t("landingTitle")}</h1>
    <p class="muted">${esc(t("landingBody"))}</p>
    <p class="trial-banner">${esc(t("trialBadge"))}</p>
    <div class="actions" style="justify-content:center">
      <button class="primary" data-go="register">${esc(t("beginRitual"))}</button>
      <button class="ghost" data-go="login">${esc(t("haveKey"))}</button>
    </div>
  </div>${tabBar()}`;
}

function authForm(mode) {
  const isReg = mode === "register";
  return `${navBar()}<div class="shell"><div class="card-panel" style="max-width:640px;margin:0 auto">
    <p class="hero-kicker">${esc(isReg ? t("onboarding") : t("returning"))}</p>
    <h2>${esc(isReg ? t("nameField") : t("enterAether"))}</h2>
    <form id="auth-form">
      ${isReg ? `<label>${esc(t("name"))}</label><input name="name" required maxlength="80" />` : ""}
      <label>${esc(t("email"))}</label><input name="email" type="email" required />
      <label>${esc(t("password"))}</label><input name="password" type="password" minlength="8" required />
      ${isReg ? `
        <div class="row">
          <div><label>${esc(t("birthDate"))}</label><input name="birth_date" type="date" required /></div>
          <div><label>${esc(t("gender"))}</label>
            <select name="gender" required>
              <option value="woman">${esc(t("woman"))}</option>
              <option value="man">${esc(t("man"))}</option>
            </select>
          </div>
        </div>
        <label>${esc(t("lookingFor"))}</label>
        <div class="check-row">
          <label><input type="checkbox" name="looking" value="woman" checked /> ${esc(t("women"))}</label>
          <label><input type="checkbox" name="looking" value="man" checked /> ${esc(t("men"))}</label>
          <label><input type="checkbox" name="looking" value="any" /> ${esc(t("anyone"))}</label>
        </div>
        <label>${esc(t("ageRangeSeek"))}</label>
        <div class="row">
          <div><input name="min_age" type="range" min="18" max="70" value="25" id="minAge" /><div class="range-readout">${esc(t("min"))} <span id="minOut">25</span></div></div>
          <div><input name="max_age" type="range" min="18" max="80" value="40" id="maxAge" /><div class="range-readout">${esc(t("max"))} <span id="maxOut">40</span></div></div>
        </div>
        <label>${esc(t("bio"))}</label><textarea name="bio" placeholder="${esc(t("bioPlaceholder"))}"></textarea>
      ` : ""}
      <p class="error" id="form-error">${esc(state.error)}</p>
      <div class="actions">
        <button class="primary" type="submit">${esc(isReg ? t("createProfile") : t("enter"))}</button>
        <button class="ghost" type="button" data-go="${isReg ? "login" : "register"}">${esc(isReg ? t("haveAccount") : t("newSeeker"))}</button>
      </div>
    </form>
  </div></div>`;
}

function cardButton(c) {
  const sel = state.selected.includes(c.id);
  const dim = state.selected.length >= 3 && !sel;
  const revealed = state.revealed && sel;
  return `<button type="button" class="arcana ${sel ? "selected" : ""} ${dim ? "dim" : ""} ${revealed ? "revealed" : ""}" data-card="${c.id}" style="--card-hue:${(c.id * 17) % 360}" aria-label="${esc(cardName(c.id))}">
    <div class="face back">
      <span class="back-roman">${ROMAN[c.id]}</span>
      <div class="back-art" aria-hidden="true">${CARD_SVG[c.id]}</div>
    </div>
    <div class="face front">
      <div class="roman">${ROMAN[c.id]}</div>
      ${CARD_SVG[c.id]}
      <div class="cname">${esc(cardName(c.id))}</div>
    </div>
  </button>`;
}

function chamber() {
  const cards = state.deck.map(cardButton).join("");
  const slotKeys = ["slotPast", "slotPresent", "slotFuture"];
  const slots = slotKeys.map((key, i) => {
    const id = state.selected[i];
    const picked = id === undefined
      ? "—"
      : `<div class="slot-art">${CARD_SVG[id]}</div><div class="picked">${esc(cardName(id))}</div>`;
    return `<div class="slot"><div class="pos">${esc(t(key))}</div>${picked}</div>`;
  }).join("");
  return `${navBar()}<div class="shell">
    <p class="hero-kicker">${esc(t("chamberKicker"))}</p>
    <h1>${t("chamberTitle")}</h1>
    <p class="muted">${esc(t("chamberBody"))}</p>
    <div class="slots">${slots}</div>
    <div class="deck ${state.shuffling ? "shuffling" : ""}">${cards}</div>
    <p class="error">${esc(state.error)}</p>
    <div class="actions">
      <button class="ghost" id="shuffle">${esc(t("shuffle"))}</button>
      <button class="primary" id="draw" ${state.selected.length === 3 ? "" : "disabled"}>${esc(t("readEnergy"))}</button>
    </div>
  </div>`;
}

function readingView() {
  const r = state.reading;
  const match = state.match;
  const sig = r.energy_signature;
  return `${navBar()}<div class="shell grid-2">
    <div class="card-panel reading">
      <p class="hero-kicker">${esc(t("energySignature"))}</p>
      <h2 class="gold">${esc(sig.archetype)}</h2>
      <p>${esc(r.last_spread.profile)}</p>
      <p>${esc(r.last_spread.interpretation)}</p>
      <p class="muted">${esc(t("element"))} · ${esc(elementName(sig.element))} · ${(sig.traits || []).map(esc).join(" · ")}</p>
    </div>
    <div class="card-panel match-hero">
      ${match ? `
        <p class="hero-kicker">${esc(t("instantConnection"))}</p>
        <div class="match-top">${avatarHtml(match.partner, "avatar-lg")}<div>
          <div class="score">${Math.round(match.compatibility_score)}%</div>
          <h3>${esc(match.partner.name)}, ${match.partner.age}</h3>
        </div></div>
        <p class="insight">${esc(match.mystical_reasoning)}</p>
        <p class="muted">${esc(match.partner.bio)}</p>
        <div class="actions">
          <button class="primary" data-open-chat="${esc(match.id)}">${esc(t("openChannel"))}</button>
          <button class="ghost" data-go="discover">${esc(t("discoverMore"))}</button>
        </div>
      ` : `<p>${esc(t("noMatch"))}</p>
        <div class="actions">
          <button class="primary" data-go="discover">${esc(t("discoverMore"))}</button>
          <button class="ghost" data-go="profile">${esc(t("adjustPrefs"))}</button>
        </div>`}
    </div>
  </div>`;
}

function previewText(conv) {
  const last = conv.last_message;
  if (!last) return conv.partner?.is_bot ? t("trialBot") : "…";
  if (last.image_url && !last.content) return "📷";
  if (last.image_url) return "📷 " + last.content;
  return last.content || conv.last_preview || "…";
}

function inboxItem(conv) {
  const p = conv.partner || {};
  const active = state.match && state.match.id === conv.id;
  return `<button type="button" class="inbox-item ${active ? "on" : ""}" data-open-chat="${esc(conv.id)}">
    ${avatarHtml(p)}
    <span class="inbox-copy">
      <span class="inbox-name">${esc(p.name)}${p.is_bot ? ` <em>${esc(t("trialBot"))}</em>` : ""}</span>
      <span class="inbox-preview">${esc(previewText(conv))}</span>
    </span>
    <span class="inbox-meta">
      <span class="gold inbox-score">${Math.round(conv.compatibility_score)}%</span>
      ${unreadBadge(conv.unread)}
    </span>
  </button>`;
}

function bubbleHtml(msg) {
  const mine = msg.sender_id === state.user.id;
  const img = msg.image_url
    ? `<img class="bubble-photo" src="${esc(msg.image_url)}" alt="${esc(t("photoAlt"))}" />`
    : "";
  const text = msg.content ? `<span>${esc(msg.content)}</span>` : "";
  return `<div class="bubble ${mine ? "me" : "them"}">${img}${text}</div>`;
}

function chatView() {
  const list = state.conversations.map(inboxItem).join("") || `<p class="muted">${esc(t("inboxEmpty"))}</p>`;
  const m = state.match;
  const showThread = Boolean(m) && (state.mobileThread || window.matchMedia("(min-width: 900px)").matches);
  let thread = `<div class="card-panel thread thread-empty"><p class="muted">${esc(t("pickChat"))}</p></div>`;
  if (m && showThread) {
    const p = m.partner || {};
    const bubbles = state.messages.map(bubbleHtml).join("");
    thread = `<div class="card-panel thread">
      <div class="chat-head">
        <button type="button" class="link back-chats" id="back-chats">${esc(t("inboxTitle"))}</button>
        ${avatarHtml(p)}
        <div class="chat-head-copy">
          <strong>${esc(p.name)}</strong>
          <span class="gold">${Math.round(m.compatibility_score)}% ${esc(t("alignment"))}</span>
        </div>
        <button type="button" class="ghost small" id="unmatch">${esc(t("unmatch"))}</button>
      </div>
      <div class="pin">
        <strong>${esc(t("sharedCards"))}</strong>
        ${m.shared_spread?.cards ? `<div class="pin-cards">${m.shared_spread.cards.map((c) => `<span>${esc(c.label)}: ${esc(cardName(c.card.id))}</span>`).join(" · ")}</div>` : ""}
        <p>${esc(m.mystical_reasoning || "")}</p>
      </div>
      <div class="msgs" id="msgs">${bubbles || `<p class="muted">${esc(t("firstWord"))}</p>`}</div>
      <form class="composer" id="send-form">
        <label class="icon-btn" title="${esc(t("sendPhoto"))}">
          <input type="file" id="chat-photo" accept="image/jpeg,image/png,image/webp,image/gif" hidden />
          <span>＋</span>
        </label>
        <input name="content" autocomplete="off" placeholder="${esc(t("chatPlaceholder"))}" maxlength="2000" />
        <button class="primary" type="submit">${esc(t("send"))}</button>
      </form>
    </div>`;
  }
  return `${navBar()}<div class="shell layout-chat ${showThread ? "thread-open" : ""}">
    <div class="sidebar inbox-pane">
      <div class="card-panel inbox">
        <p class="hero-kicker">${esc(t("inboxTitle"))}</p>
        <div class="inbox-list">${list}</div>
      </div>
      ${adSlot()}
    </div>
    ${thread}
  </div>`;
}

function discoverView() {
  const cards = state.discover.map((item) => {
    const u = item.user;
    const cta = item.already_chatting ? t("openChat") : t("messageCta");
    const action = item.already_chatting && item.match_id
      ? `data-open-chat="${esc(item.match_id)}"`
      : `data-message="${esc(u.id)}"`;
    return `<article class="person-card">
      ${avatarHtml(u, "avatar-xl")}
      <div class="person-score">${Math.round(item.compatibility_score)}%</div>
      <h3>${esc(u.name)}${t("yearsOld") ? `, ${u.age} ${esc(t("yearsOld"))}` : `, ${u.age}`}</h3>
      <p class="gold">${esc(u.energy_signature?.archetype || "")}</p>
      <p class="muted person-bio">${esc(u.bio || "")}</p>
      ${u.is_bot ? `<p class="pill">${esc(t("trialBot"))}</p>` : ""}
      <button class="primary" ${action}>${esc(cta)}</button>
    </article>`;
  }).join("");
  return `${navBar()}<div class="shell">
    <p class="hero-kicker">${esc(t("discoverKicker"))}</p>
    <h1>${esc(t("discoverTitle"))}</h1>
    <p class="muted">${esc(t("discoverBody"))}</p>
    <p class="error">${esc(state.error)}</p>
    <div class="discover-grid">${cards || `<p class="muted">${esc(t("noMatch"))}</p>`}</div>
  </div>`;
}

function unionCardFace(entry, revealed) {
  const c = entry.card;
  const id = c.id;
  return `<div class="union-card ${revealed ? "revealed" : ""}" style="--card-hue:${(id * 17) % 360}">
    <div class="face back">
      <span class="back-roman">${ROMAN[id]}</span>
      <div class="back-art" aria-hidden="true">${CARD_SVG[id]}</div>
    </div>
    <div class="face front">
      <div class="roman">${ROMAN[id]}</div>
      ${CARD_SVG[id]}
      <div class="cname">${esc(cardName(id))}</div>
    </div>
  </div>
  <div class="union-meta">
    <div class="pos">${esc(entry.label)}</div>
    ${revealed ? `<div class="picked">${esc(cardName(id))}</div><p class="muted union-teach">${esc(entry.teach || "")}</p>` : `<div class="picked">…</div>`}
  </div>`;
}

function greenPathHtml(gp) {
  if (!gp) return "";
  const items = (gp.items || []).map((it) => {
    const body = it.answer || it.guidance || it.fix || it.do || it.now || "";
    return `
    <div class="green-item">
      <div class="q">${esc(it.question || "")}</div>
      ${body ? `<p class="body">${esc(body)}</p>` : ""}
    </div>`;
  }).join("");
  return `<div class="green-path">
    <h3>${esc(gp.title || t("greenPathCta"))}</h3>
    ${gp.intro ? `<p class="intro">${esc(gp.intro)}</p>` : ""}
    ${items}
  </div>`;
}

function unionView() {
  const u = state.union;
  if (!u) return discoverView();
  const spread = u.match?.shared_spread;
  const cards = (spread?.cards || []).map((entry, i) => {
    const show = u.phase === "reveal" && i < u.revealedCount;
    return `<div class="union-slot">${unionCardFace(entry, show)}</div>`;
  }).join("");
  const partner = u.match?.partner || {};
  const shuffling = u.phase === "shuffle";
  const gp = spread?.green_path;
  return `${navBar()}<div class="shell center union-shell">
    <p class="hero-kicker">${esc(t("unionTogether"))}</p>
    <h1>${esc(shuffling ? t("unionShuffling") : t("unionReveal"))}</h1>
    <div class="union-pair">
      ${avatarHtml(state.user, "avatar-lg")}
      <span class="gold union-amp">✦</span>
      ${avatarHtml(partner, "avatar-lg")}
    </div>
    <p class="muted">${esc(partner.name || "")}${partner.age ? `, ${partner.age}` : ""}</p>
    <div class="union-deck ${shuffling ? "shuffling" : ""}">${cards}</div>
    ${u.phase === "reveal" && u.revealedCount >= 3 ? `
      <div class="card-panel union-message">
        <div class="score">${Math.round(u.match.compatibility_score)}%</div>
        <p class="insight">${esc(spread?.message || u.match.mystical_reasoning || "")}</p>
        ${u.showGreen && gp ? greenPathHtml(gp) : ""}
        <div class="actions" style="justify-content:center">
          ${gp && !u.showGreen ? `<button class="ghost" id="union-green">${esc(t("greenPathCta"))}</button>` : ""}
          <button class="primary" id="union-to-chat">${esc(t("unionOpenChat"))}</button>
        </div>
      </div>
    ` : `<p class="error">${esc(state.error)}</p>`}
  </div>`;
}

function profileView() {
  const u = state.user;
  const sig = u.energy_signature;
  const genderLabel = { woman: t("woman"), man: t("man"), any: t("anyone") };
  return `${navBar()}<div class="shell grid-2">
    <div class="card-panel">
      <p class="hero-kicker">${esc(t("yourField"))}</p>
      <div class="profile-head">
        ${avatarHtml(u, "avatar-xl")}
        <div>
          <h2>${esc(u.name)}, ${u.age}</h2>
          ${sig ? `<p class="gold">${esc(sig.archetype)}</p><p class="muted">${esc((sig.traits || []).join(" · "))} · ${esc(elementName(sig.element))}</p>` : `<p class="muted">${esc(t("noReading"))}</p>`}
        </div>
      </div>
      <form id="photo-form">
        <label>${esc(u.photo_url ? t("changePhoto") : t("uploadPhoto"))}</label>
        <input type="file" id="profile-photo" accept="image/jpeg,image/png,image/webp,image/gif" />
        <p class="muted photo-hint">${esc(t("photoHint"))}</p>
      </form>
      <form id="pref-form">
        <label>${esc(t("name"))}</label><input name="name" value="${esc(u.name)}" />
        <label>${esc(t("bio"))}</label><textarea name="bio">${esc(u.bio)}</textarea>
        <label>${esc(t("ageRange"))}</label>
        <div class="row">
          <div><input name="min_age" type="range" min="18" max="70" value="${u.min_age_preference}" id="minAge" /><div class="range-readout">${esc(t("min"))} <span id="minOut">${u.min_age_preference}</span></div></div>
          <div><input name="max_age" type="range" min="18" max="80" value="${u.max_age_preference}" id="maxAge" /><div class="range-readout">${esc(t("max"))} <span id="maxOut">${u.max_age_preference}</span></div></div>
        </div>
        <label>${esc(t("lookingFor"))}</label>
        <div class="check-row">
          ${["woman","man","any"].map((g) => `<label><input type="checkbox" name="looking" value="${g}" ${u.looking_for_gender.includes(g) ? "checked" : ""} /> ${esc(genderLabel[g])}</label>`).join("")}
        </div>
        <p class="${state.error === t("saved") ? "ok" : "error"}">${esc(state.error)}</p>
        <div class="actions"><button class="primary" type="submit">${esc(t("savePrefs"))}</button></div>
      </form>
      <p class="lock-note">${esc(u.is_premium ? t("lockPremium") : t("lockFree"))}</p>
    </div>
    <div class="card-panel">
      <p class="hero-kicker">${esc(t("recalibrate"))}</p>
      <p>${esc(t("recalibrateBody"))}</p>
      <div class="actions">
        <button class="accent" id="redraw">${esc(t("redraw"))}</button>
        <button class="ghost" data-go="chamber">${esc(t("enterChamber"))}</button>
      </div>
      ${adSlot()}
    </div>
  </div>`;
}

function render() {
  applyDir();
  document.body.classList.add("app-shell");
  const map = {
    landing: landing,
    login: () => authForm("login"),
    register: () => authForm("register"),
    chamber: chamber,
    reading: readingView,
    chat: chatView,
    discover: discoverView,
    profile: profileView,
    union: unionView,
  };
  const draft = document.querySelector("#send-form input[name='content']")?.value;
  const body = (map[state.view] || landing)();
  const withTabs = state.user && !body.includes('class="tabbar"') ? `${body}${tabBar()}` : body;
  $app.innerHTML = withTabs;
  $app.classList.toggle("has-tabbar", !!state.user);
  bind();
  if (state.view === "chat" && state.match) connectWs();
  else closeWs();
  const msgs = document.getElementById("msgs");
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
  if (draft) {
    const input = document.querySelector("#send-form input[name='content']");
    if (input) input.value = draft;
  }
}

function bind() {
  $app.querySelectorAll("[data-go]").forEach((el) => {
    el.addEventListener("click", () => navigate(el.getAttribute("data-go")));
  });
  $app.querySelectorAll("[data-lang]").forEach((el) => {
    el.addEventListener("click", () => setLang(el.getAttribute("data-lang")));
  });
  $app.querySelectorAll("[data-open-chat]").forEach((el) => {
    el.addEventListener("click", () => openExistingChat(el.getAttribute("data-open-chat")));
  });
  $app.querySelectorAll("[data-message]").forEach((el) => {
    el.addEventListener("click", () => openWithPerson(el.getAttribute("data-message")));
  });
  const logout = document.getElementById("logout");
  if (logout) logout.addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST", body: "{}" });
    closeWs();
    state.user = null;
    state.match = null;
    state.conversations = [];
    state.messages = [];
    navigate("landing");
  });
  const minAge = document.getElementById("minAge");
  const maxAge = document.getElementById("maxAge");
  if (minAge && maxAge) {
    const sync = () => {
      document.getElementById("minOut").textContent = minAge.value;
      document.getElementById("maxOut").textContent = maxAge.value;
    };
    minAge.addEventListener("input", sync);
    maxAge.addEventListener("input", sync);
  }
  const form = document.getElementById("auth-form");
  if (form) form.addEventListener("submit", onAuth);
  const pref = document.getElementById("pref-form");
  if (pref) pref.addEventListener("submit", onPrefs);
  const shuffle = document.getElementById("shuffle");
  if (shuffle) shuffle.addEventListener("click", onShuffle);
  const draw = document.getElementById("draw");
  if (draw) draw.addEventListener("click", onDraw);
  $app.querySelectorAll("[data-card]").forEach((el) => {
    el.addEventListener("click", () => pickCard(Number(el.getAttribute("data-card"))));
  });
  const redraw = document.getElementById("redraw");
  if (redraw) redraw.addEventListener("click", () => openChamber());
  const send = document.getElementById("send-form");
  if (send) send.addEventListener("submit", onSend);
  const chatPhoto = document.getElementById("chat-photo");
  if (chatPhoto) chatPhoto.addEventListener("change", onChatPhoto);
  const profilePhoto = document.getElementById("profile-photo");
  if (profilePhoto) profilePhoto.addEventListener("change", onProfilePhoto);
  const unmatchBtn = document.getElementById("unmatch");
  if (unmatchBtn) unmatchBtn.addEventListener("click", onUnmatch);
  const back = document.getElementById("back-chats");
  if (back) back.addEventListener("click", () => {
    state.mobileThread = false;
    render();
  });
  const installBtn = document.getElementById("install-app");
  if (installBtn) installBtn.addEventListener("click", onInstallApp);
  const installDismiss = document.getElementById("install-dismiss");
  if (installDismiss) installDismiss.addEventListener("click", () => {
    state.showInstall = false;
    localStorage.setItem("aether_install_dismissed", "1");
    render();
  });
  const unionChat = document.getElementById("union-to-chat");
  if (unionChat) unionChat.addEventListener("click", async () => {
    if (!state.union?.match) return;
    state.match = state.union.match;
    state.union = null;
    state.mobileThread = true;
    try {
      await loadChat(state.match.id);
      await refreshInbox();
      state.view = "chat";
      render();
    } catch (err) {
      state.error = err.message;
      state.view = "discover";
      render();
    }
  });
  const unionGreen = document.getElementById("union-green");
  if (unionGreen) unionGreen.addEventListener("click", () => {
    if (!state.union) return;
    state.union.showGreen = true;
    render();
  });
}

async function onAuth(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const isReg = state.view === "register";
  try {
    if (isReg) {
      const looking = [...e.target.querySelectorAll('input[name="looking"]:checked')].map((i) => i.value);
      const body = {
        email: fd.get("email"),
        password: fd.get("password"),
        name: fd.get("name"),
        birth_date: fd.get("birth_date"),
        gender: fd.get("gender"),
        looking_for_gender: looking.length ? looking : ["any"],
        min_age_preference: Number(fd.get("min_age")),
        max_age_preference: Number(fd.get("max_age")),
        bio: fd.get("bio") || "",
      };
      const data = await api("/api/auth/register", { method: "POST", body: JSON.stringify(body) });
      state.user = data.user;
      await hydrateMe();
      state.selected = [];
      navigate("chamber");
    } else {
      const data = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ email: fd.get("email"), password: fd.get("password") }) });
      state.user = data.user;
      const me = await hydrateMe();
      if (!state.user.energy_signature) navigate("chamber");
      else if ((me.conversations || []).length) navigate("chat");
      else navigate("discover");
    }
  } catch (err) {
    state.error = err.message;
    const box = document.getElementById("form-error");
    if (box) box.textContent = state.error;
    else render();
  }
}

async function onPrefs(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const looking = [...e.target.querySelectorAll('input[name="looking"]:checked')].map((i) => i.value);
  try {
    const data = await api("/api/users/preferences", {
      method: "PUT",
      body: JSON.stringify({
        name: fd.get("name"),
        bio: fd.get("bio"),
        min_age_preference: Number(fd.get("min_age")),
        max_age_preference: Number(fd.get("max_age")),
        looking_for_gender: looking.length ? looking : ["any"],
      }),
    });
    state.user = data.user;
    state.error = t("saved");
    render();
  } catch (err) {
    state.error = err.message;
    render();
  }
}

function pickCard(id) {
  if (state.revealed) return;
  const i = state.selected.indexOf(id);
  if (i >= 0) state.selected.splice(i, 1);
  else if (state.selected.length < 3) state.selected.push(id);
  render();
}

function onShuffle() {
  shuffleDeck();
  state.shuffling = true;
  state.selected = [];
  state.revealed = false;
  render();
  setTimeout(() => {
    state.shuffling = false;
    render();
  }, 900);
}

async function onDraw() {
  if (state.selected.length !== 3) return;
  const btn = document.getElementById("draw");
  if (btn) btn.disabled = true;
  try {
    const data = await api("/api/tarot/draw", {
      method: "POST",
      body: JSON.stringify({ card_ids: state.selected, unmatch_previous: false }),
    });
    state.user = data.user;
    state.reading = data.reading;
    state.match = data.match;
    state.conversations = data.conversations || state.conversations;
    state.revealed = true;
    render();
    setTimeout(() => navigate("reading"), 700);
  } catch (err) {
    state.error = err.message;
    render();
  }
}

async function loadChat(matchId) {
  const data = await api(`/api/chat/${matchId}`);
  state.match = data.match;
  state.messages = data.messages;
}

async function refreshInbox() {
  try {
    const data = await api("/api/conversations");
    state.conversations = data.conversations || [];
    state.unreadTotal = data.unread_total || 0;
    if (state.match) {
      const still = state.conversations.find((c) => c.id === state.match.id);
      if (still) state.match = { ...state.match, ...still, partner: still.partner };
    }
  } catch {
    /* ignore poll errors */
  }
}

async function openExistingChat(matchId) {
  try {
    await loadChat(matchId);
    state.mobileThread = true;
    state.view = "chat";
    await refreshInbox();
    render();
  } catch (err) {
    state.error = err.message;
    render();
  }
}

async function openWithPerson(userId) {
  state.error = "";
  state.union = {
    phase: "shuffle",
    match: { partner: state.discover.find((p) => p.user.id === userId)?.user || { id: userId, name: "…" }, compatibility_score: 0, shared_spread: { cards: [
      { label: "…", card: { id: 0 }, teach: "" },
      { label: "…", card: { id: 1 }, teach: "" },
      { label: "…", card: { id: 2 }, teach: "" },
    ] } },
    revealedCount: 0,
  };
  state.view = "union";
  render();
  try {
    const data = await api("/api/match/open", { method: "POST", body: JSON.stringify({ user_id: userId }) });
    state.match = data.match;
    state.union.match = data.match;
    // Keep shuffling briefly, then reveal cards one by one.
    setTimeout(() => {
      if (state.view !== "union" || !state.union) return;
      state.union.phase = "reveal";
      state.union.revealedCount = 0;
      render();
      let n = 0;
      const tick = () => {
        if (state.view !== "union" || !state.union) return;
        n += 1;
        state.union.revealedCount = n;
        render();
        if (n < 3) setTimeout(tick, 450);
      };
      setTimeout(tick, 350);
    }, 1600);
  } catch (err) {
    state.error = err.message;
    state.union = null;
    state.view = "discover";
    render();
  }
}

async function loadDiscover() {
  try {
    const data = await api("/api/discover");
    state.discover = data.people || [];
    state.error = "";
    if (state.view === "discover") render();
  } catch (err) {
    state.error = err.message;
    state.discover = [];
    if (state.view === "discover") render();
  }
}

async function onSend(e) {
  e.preventDefault();
  const input = e.target.content;
  const content = input.value.trim();
  if (!content || !state.match) return;
  input.value = "";
  const data = await api("/api/chat/send", {
    method: "POST",
    body: JSON.stringify({ match_id: state.match.id, content }),
  });
  pushMessage(data.message);
  if (data.bot_message) pushMessage(data.bot_message);
  await refreshInbox();
  render();
}

function pushMessage(msg) {
  if (!msg) return;
  if (!state.messages.find((m) => m.id === msg.id)) state.messages.push(msg);
}

async function onChatPhoto(e) {
  const file = e.target.files && e.target.files[0];
  e.target.value = "";
  if (!file || !state.match) return;
  if (file.size > 5 * 1024 * 1024) {
    state.error = t("photoTooBig");
    render();
    return;
  }
  const fd = new FormData();
  fd.append("match_id", state.match.id);
  fd.append("image", file);
  const caption = document.querySelector("#send-form input[name='content']")?.value?.trim() || "";
  if (caption) fd.append("content", caption);
  try {
    const data = await api("/api/chat/image", { method: "POST", body: fd });
    const box = document.querySelector("#send-form input[name='content']");
    if (box) box.value = "";
    pushMessage(data.message);
    if (data.bot_message) pushMessage(data.bot_message);
    await refreshInbox();
    render();
  } catch (err) {
    state.error = err.message;
    render();
  }
}

async function onProfilePhoto(e) {
  const file = e.target.files && e.target.files[0];
  e.target.value = "";
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    state.error = t("photoTooBig");
    render();
    return;
  }
  const fd = new FormData();
  fd.append("photo", file);
  try {
    const data = await api("/api/users/photo", { method: "POST", body: fd });
    state.user = data.user;
    state.error = t("saved");
    render();
  } catch (err) {
    state.error = err.message;
    render();
  }
}

async function onUnmatch() {
  if (!state.match) return;
  if (!window.confirm(t("unmatchConfirm"))) return;
  try {
    await api("/api/match/unmatch", { method: "POST", body: JSON.stringify({ match_id: state.match.id }) });
    state.match = null;
    state.messages = [];
    state.mobileThread = false;
    await refreshInbox();
    render();
  } catch (err) {
    state.error = err.message;
    render();
  }
}

function closeWs() {
  if (state.ws) {
    state.ws.close();
    state.ws = null;
  }
}

function connectWs() {
  if (!state.match) return;
  if (state.ws && state.ws.readyState === WebSocket.OPEN) return;
  closeWs();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/chat/${state.match.id}`);
  state.ws = ws;
  ws.onmessage = (ev) => {
    const payload = JSON.parse(ev.data);
    if (payload.type === "message" && payload.message) {
      pushMessage(payload.message);
      render();
    }
  };
}

function startPolling() {
  if (state.pollId) return;
  state.pollId = setInterval(async () => {
    if (!state.user) return;
    const snap = JSON.stringify({
      conv: state.conversations.map((c) => [c.id, c.unread, c.last_preview, c.last_message?.id]),
      msgs: state.messages.map((m) => m.id),
    });
    try {
      await refreshInbox();
      if (state.view === "chat" && state.match) {
        const threadVisible = state.mobileThread || window.matchMedia("(min-width: 900px)").matches;
        if (threadVisible) {
          const data = await api(`/api/chat/${state.match.id}`);
          state.match = data.match;
          state.messages = data.messages;
        }
      }
    } catch {
      return;
    }
    const next = JSON.stringify({
      conv: state.conversations.map((c) => [c.id, c.unread, c.last_preview, c.last_message?.id]),
      msgs: state.messages.map((m) => m.id),
    });
    if (next !== snap && (state.view === "chat" || state.unreadTotal >= 0)) render();
  }, 3500);
}

boot().then(() => {
  if (state.view === "chat" && state.match) loadChat(state.match.id).then(render);
});

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
}

function refreshInstallVisibility() {
  if (isStandalone()) {
    state.showInstall = false;
    return;
  }
  if (localStorage.getItem("aether_install_dismissed") === "1") {
    state.showInstall = false;
    return;
  }
  // Show bar when browser can install, or on iOS/mobile where Add to Home Screen is available.
  const mobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  state.showInstall = !!(state.deferredInstall || mobile);
}

async function onInstallApp() {
  if (!state.deferredInstall) return;
  const prompt = state.deferredInstall;
  state.deferredInstall = null;
  await prompt.prompt();
  try { await prompt.userChoice; } catch { /* ignore */ }
  state.showInstall = false;
  render();
}

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  state.deferredInstall = e;
  refreshInstallVisibility();
  if (state.showInstall) render();
});

window.addEventListener("appinstalled", () => {
  state.deferredInstall = null;
  state.showInstall = false;
  localStorage.setItem("aether_install_dismissed", "1");
  render();
});

refreshInstallVisibility();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
