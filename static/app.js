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
    "Sign in to enter the chamber.": {
      he: "יש להיכנס כדי להיכנס לחדר.",
    },
    "Session expired.": { he: "פג תוקף החיבור." },
    "Birth date must be YYYY-MM-DD.": { he: "תאריך לידה בפורמט YYYY-MM-DD." },
    "You must be 18 or older to join.": { he: "יש להיות בני 18 ומעלה כדי להצטרף." },
    "Birth date cannot be in the future.": { he: "תאריך לידה לא יכול להיות בעתיד." },
    "Age range is inverted.": { he: "טווח הגילים הפוך." },
    "That email already has a profile.": { he: "לאימייל הזה כבר יש פרופיל." },
    "Email or password did not match.": { he: "אימייל או סיסמה לא התאימו." },
    "Select exactly three distinct Major Arcana cards.": { he: "יש לבחור בדיוק שלושה קלפי ארקנה ראשית שונים." },
    "Thread not found.": { he: "השרשור לא נמצא." },
    "This connection is closed.": { he: "החיבור הזה נסגר." },
    "Not your thread.": { he: "זה לא השרשור שלך." },
  };
  if (state.lang === "he" && map[msg]?.he) return map[msg].he;
  if (state.lang === "he" && msg && msg.startsWith("Free seekers may redraw")) {
    return msg
      .replace("Free seekers may redraw once per week. Next opening in ~", "מחפשים חופשיים יכולים למשוך מחדש פעם בשבוע. הפתיחה הבאה בעוד כ־")
      .replace("h. Premium unlocks unlimited rituals.", " שעות. פרימיום פותח טקסים ללא הגבלה.");
  }
  return msg;
}

function navigate(view) {
  state.view = view;
  state.error = "";
  render();
}

async function setLang(lang) {
  state.lang = lang;
  localStorage.setItem(LANG_KEY, lang);
  applyDir();
  if (state.user) {
    try {
      const me = await api("/api/me");
      state.user = me.user;
      state.match = me.active_match;
      if (state.reading && state.user.last_spread) {
        state.reading = {
          energy_signature: state.user.energy_signature,
          last_spread: state.user.last_spread,
        };
      }
      if (state.view === "chat" && state.match) await loadChat(state.match.id);
    } catch {
      /* stay on current view */
    }
  }
  render();
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-Lang": state.lang,
      ...(opts.headers || {}),
    },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    const raw = typeof detail === "string" ? detail : (detail && JSON.stringify(detail)) || t("veilFailed");
    throw new Error(localizeError(raw));
  }
  return data;
}

async function boot() {
  applyDir();
  try {
    const me = await api("/api/me");
    state.user = me.user;
    state.match = me.active_match;
    const deck = await api("/api/tarot/deck");
    state.deck = deck.cards;
    if (!state.user.energy_signature) navigate("chamber");
    else if (state.match) navigate("chat");
    else navigate("profile");
  } catch {
    const deck = await api("/api/tarot/deck");
    state.deck = deck.cards;
    navigate("landing");
  }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function langSwitch() {
  return `<div class="lang-switch" role="group" aria-label="Language">
    <button type="button" class="${state.lang === "en" ? "on" : ""}" data-lang="en">EN</button>
    <button type="button" class="${state.lang === "he" ? "on" : ""}" data-lang="he">עב</button>
  </div>`;
}

function navBar() {
  const links = state.user
    ? `<button class="link" data-go="chamber">${esc(t("navChamber"))}</button>
       <button class="link" data-go="profile">${esc(t("navProfile"))}</button>
       ${state.match ? `<button class="link" data-go="chat">${esc(t("navChat"))}</button>` : ""}
       <button class="link" id="logout">${esc(t("navLeave"))}</button>`
    : "";
  return `<header class="nav">
    <div class="brand">${esc(t("brand"))}</div>
    <div class="nav-end">${links}${langSwitch()}</div>
  </header>`;
}

function adSlot() {
  return `<aside class="ad-slot" data-component="BannerAd">${esc(t("adSlot"))}</aside>`;
}

function landing() {
  return `${navBar()}<div class="shell center">
    <p class="hero-kicker">${esc(t("landingKicker"))}</p>
    <h1>${t("landingTitle")}</h1>
    <p class="muted">${esc(t("landingBody"))}</p>
    <div class="actions" style="justify-content:center">
      <button class="primary" data-go="register">${esc(t("beginRitual"))}</button>
      <button class="ghost" data-go="login">${esc(t("haveKey"))}</button>
    </div>
  </div>`;
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
              <option value="nonbinary">${esc(t("nonbinary"))}</option>
            </select>
          </div>
        </div>
        <label>${esc(t("lookingFor"))}</label>
        <div class="check-row">
          <label><input type="checkbox" name="looking" value="woman" checked /> ${esc(t("women"))}</label>
          <label><input type="checkbox" name="looking" value="man" checked /> ${esc(t("men"))}</label>
          <label><input type="checkbox" name="looking" value="nonbinary" /> ${esc(t("nonbinary"))}</label>
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
  return `<button type="button" class="arcana ${sel ? "selected" : ""} ${dim ? "dim" : ""} ${revealed ? "revealed" : ""}" data-card="${c.id}" aria-label="${esc(cardName(c.id))}">
    <div class="face back"></div>
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
        <div class="score">${Math.round(match.compatibility_score)}%</div>
        <h3>${esc(match.partner.name)}, ${match.partner.age}</h3>
        <p class="insight">${esc(match.mystical_reasoning)}</p>
        <p class="muted">${esc(match.partner.bio)}</p>
        <div class="actions"><button class="primary" data-go="chat">${esc(t("openChannel"))}</button></div>
      ` : `<p>${esc(t("noMatch"))}</p>
        <button class="ghost" data-go="profile">${esc(t("adjustPrefs"))}</button>`}
    </div>
  </div>`;
}

function chatView() {
  const m = state.match;
  if (!m) return `${navBar()}<div class="shell"><p>${esc(t("noActiveMatch"))}</p></div>`;
  const bubbles = state.messages.map((msg) => {
    const mine = msg.sender_id === state.user.id;
    return `<div class="bubble ${mine ? "me" : "them"}">${esc(msg.content)}</div>`;
  }).join("");
  return `${navBar()}<div class="shell layout-chat">
    <div class="sidebar">
      <div class="card-panel">
        <p class="hero-kicker">${esc(t("boundWith"))}</p>
        <h3>${esc(m.partner.name)}</h3>
        <p class="gold">${Math.round(m.compatibility_score)}% ${esc(t("alignment"))}</p>
        <p class="muted">${esc(m.partner.energy_signature?.archetype || "")}</p>
      </div>
      ${adSlot()}
    </div>
    <div class="card-panel thread">
      <div class="pin"><strong>${esc(t("cosmicInsight"))}</strong> ${esc(m.mystical_reasoning)}</div>
      <div class="msgs" id="msgs">${bubbles || `<p class="muted">${esc(t("firstWord"))}</p>`}</div>
      <form class="composer" id="send-form">
        <input name="content" autocomplete="off" placeholder="${esc(t("chatPlaceholder"))}" maxlength="2000" />
        <button class="primary" type="submit">${esc(t("send"))}</button>
      </form>
    </div>
  </div>`;
}

function profileView() {
  const u = state.user;
  const sig = u.energy_signature;
  const genderLabel = { woman: t("woman"), man: t("man"), nonbinary: t("nonbinary"), any: t("anyone") };
  return `${navBar()}<div class="shell grid-2">
    <div class="card-panel">
      <p class="hero-kicker">${esc(t("yourField"))}</p>
      <h2>${esc(u.name)}, ${u.age}</h2>
      ${sig ? `<p class="gold">${esc(sig.archetype)}</p><p class="muted">${esc((sig.traits || []).join(" · "))} · ${esc(elementName(sig.element))}</p>` : `<p class="muted">${esc(t("noReading"))}</p>`}
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
          ${["woman","man","nonbinary","any"].map((g) => `<label><input type="checkbox" name="looking" value="${g}" ${u.looking_for_gender.includes(g) ? "checked" : ""} /> ${esc(genderLabel[g])}</label>`).join("")}
        </div>
        <p class="error">${esc(state.error)}</p>
        <div class="actions"><button class="primary" type="submit">${esc(t("savePrefs"))}</button></div>
      </form>
      <p class="lock-note">${esc(u.is_premium ? t("lockPremium") : t("lockFree"))}</p>
    </div>
    <div class="card-panel">
      <p class="hero-kicker">${esc(t("recalibrate"))}</p>
      <p>${esc(t("recalibrateBody"))}</p>
      <div class="actions">
        <button class="hebrew" id="redraw">${esc(t("redraw"))}</button>
        <button class="ghost" data-go="chamber">${esc(t("enterChamber"))}</button>
      </div>
      ${adSlot()}
    </div>
  </div>`;
}

function render() {
  applyDir();
  const map = {
    landing: landing,
    login: () => authForm("login"),
    register: () => authForm("register"),
    chamber: chamber,
    reading: readingView,
    chat: chatView,
    profile: profileView,
  };
  $app.innerHTML = (map[state.view] || landing)();
  bind();
  if (state.view === "chat") connectWs();
  else closeWs();
  const msgs = document.getElementById("msgs");
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

function bind() {
  $app.querySelectorAll("[data-go]").forEach((el) => {
    el.addEventListener("click", () => navigate(el.getAttribute("data-go")));
  });
  $app.querySelectorAll("[data-lang]").forEach((el) => {
    el.addEventListener("click", () => setLang(el.getAttribute("data-lang")));
  });
  const logout = document.getElementById("logout");
  if (logout) logout.addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST", body: "{}" });
    closeWs();
    state.user = null;
    state.match = null;
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
  if (redraw) redraw.addEventListener("click", () => {
    state.selected = [];
    state.revealed = false;
    navigate("chamber");
  });
  const send = document.getElementById("send-form");
  if (send) send.addEventListener("submit", onSend);
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
      state.selected = [];
      navigate("chamber");
    } else {
      const data = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ email: fd.get("email"), password: fd.get("password") }) });
      state.user = data.user;
      const me = await api("/api/me");
      state.match = me.active_match;
      if (!state.user.energy_signature) navigate("chamber");
      else if (state.match) {
        await loadChat(state.match.id);
        navigate("chat");
      } else navigate("profile");
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
    state.error = "";
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
      body: JSON.stringify({ card_ids: state.selected, unmatch_previous: true }),
    });
    state.user = data.user;
    state.reading = data.reading;
    state.match = data.match;
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
  if (!state.messages.find((m) => m.id === data.message.id)) {
    state.messages.push(data.message);
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
      if (!state.messages.find((m) => m.id === payload.message.id)) {
        state.messages.push(payload.message);
        render();
      }
    }
  };
}

boot().then(() => {
  if (state.view === "chat" && state.match) loadChat(state.match.id).then(render);
});
