# Aether — Tarot Matchmaker (trial app)

דייטינג לפי אנרגיית טארוט. עכשיו כ־**אפליקציית PWA** — אפשר להתקין למסך הבית בטלפון ולהריץ כגרסת ניסיון.

## קישור לגיט

**מאגר:** https://github.com/lioraDeveloper/tarot-match  

**ענף גרסת הניסיון (PWA):** `cursor/pwa-trial-app-e53a`

```bash
git clone https://github.com/lioraDeveloper/tarot-match.git
cd tarot-match
git checkout cursor/pwa-trial-app-e53a
```

## הרצת גרסת ניסיון

### Windows

```powershell
.\scripts\start-trial.ps1
```

### Mac / Linux

```bash
chmod +x scripts/start-trial.sh
./scripts/start-trial.sh
```

או ידנית:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

פתחו במחשב: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### בטלפון (אותה רשת Wi‑Fi)

1. הריצו את הסקריפט — הוא מדפיס כתובת כמו `http://192.168.x.x:8000`
2. פתחו את הקישור בדפדפן בטלפון
3. **Android (Chrome):** תפריט ⋮ → **Install app** / הוספה למסך הבית  
   **iPhone (Safari):** שיתוף → **הוספה למסך הבית**
4. האפליקציה נפתחת במסך מלא (standalone) עם סרגל ניווט תחתון

חייבים להיות **18+**. משתמשים לדוגמה כבר קיימים במסד — אחרי הרשמה אפשר להתאים מיד.

## מה חדש באפליקציה

- מניפסט PWA + Service Worker
- אייקון והתקנה למסך הבית
- ניווט תחתון למובייל (קלפים / גילוי / צ׳אטים / פרופיל)
- באנר «גרסת ניסיון» + כפתור התקנה

## Optional LLM

Set `OPENAI_API_KEY` if you want live interpretations. Without it, the local oracle generates archetypes, profiles, and cosmic insights (keeps the draw under 3 seconds).

## Stack

- FastAPI + SQLite (schema matches the PostgreSQL blueprint: `users`, `matches`, `messages`)
- WebSocket chat at `/ws/chat/{matchId}`
- PWA: `/manifest.webmanifest`, `/sw.js`, installable shell
- `is_premium` + weekly redraw limit + `<BannerAd />` slots for later monetization
