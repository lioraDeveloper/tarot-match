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
כרגע חלק מהטקסטים האמיתיים עדיין יושבים ב־`app/tarot.py`  
(למשל `love_long`, `green_path` של השוטה/הקוסם).

**לפני מסירה למתכנת:** להוציא אותם לכספת ולהשאיר ב־`tarot.py` רק טעינה מ־samples או מנתיב סביבה.

משתנה מוצע בהמשך:
```bash
AETHER_CONTENT_PATH=/secure/path/cards.json
```

## בדיקה מהירה לפני שליחה
```bash
# חייב להיכשל / לא להימצא אצל המתכנת:
test ! -d content/vault && echo "vault absent OK" || echo "REMOVE VAULT BEFORE SHARE"
rg -n "love_long|green_path|חוברת לימוד" app/ || true
```
