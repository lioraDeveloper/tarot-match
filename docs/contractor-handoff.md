# מסירת עבודה למתכנת (בלי לחשוף תוכן סודי)

## לפני שנותנים גישה

1. חתמו **NDA** (סודיות על תוכן קלפים, מסרים, מסלול ירוק, חוברת לימוד).
2. קראי: `docs/content-vault-architecture.md`.

## מה לשלוח למתכנת

שלחי **עץ קוד בלי כספת**:

```bash
# דוגמה: ארכיון בטוח (בלי content/vault)
git archive -o aether-for-contractor.zip HEAD \
  --prefix=aether/ \
  ':(exclude)content/vault'
```

או ריפו נפרד שמכיל הכול חוץ מ־`content/vault/`.

## מה המתכנת מקבל
- `app/`, `static/`, בדיקות, README
- `content/schema/` — מבנה שדות
- `content/samples/` — תוכן מזויף לפיתוח

## מה המתכנת לא מקבל
- `content/vault/`
- צילומי ספר
- סיכומי לימוד
- טקסטים אמיתיים של מסלול ירוק / love_long

## הערה חשובה על המצב הנוכחי

הטקסטים הארוכים / מסלול ירוק של השוטה והקוסם הועברו ל־`content/vault/published/`.  
`app/tarot.py` מחזיק רק שלד ציבורי וטוען תוכן דרך `app/content_loader.py`.

לפני מסירה למתכנת: אל תשליחי את `content/vault/` (ראה ארכיון למטה).

משתנה אופציונלי:
```bash
AETHER_CONTENT_PATH=/secure/path/to/content-dir
```
(תיקייה עם `cards.he.json` / `cards.en.json`)

## בדיקה מהירה לפני שליחה
```bash
# חייב להיכשל / לא להימצא אצל המתכנת:
test ! -d content/vault && echo "vault absent OK" || echo "REMOVE VAULT BEFORE SHARE"
# שלד הקוד לא אמור להכיל love_long / green_path מוטמעים:
rg -n "love_long|green_path" app/tarot.py && echo "FAIL: secrets still in tarot.py" || echo "tarot.py clean OK"
```
