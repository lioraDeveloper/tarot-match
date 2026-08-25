# Aether — Tarot Matchmaker

Free dating platform where a 3-card Major Arcana reading becomes an energy signature, then an instant chat with the most compatible active seeker.

## Run locally

```powershell
cd C:\Users\Moshik\Projects\tarot-match
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

You must be **18+**. Seeded demo seekers already have energy signatures so a new registration can match immediately.

## Optional LLM

Set `OPENAI_API_KEY` if you want live interpretations. Without it, the local oracle generates archetypes, profiles, and cosmic insights (keeps the draw under 3 seconds).

## Stack

- FastAPI + SQLite (schema matches the PostgreSQL blueprint: `users`, `matches`, `messages`)
- WebSocket chat at `/ws/chat/{matchId}`
- `is_premium` + weekly redraw limit + `<BannerAd />` slots for later monetization
