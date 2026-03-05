# vocabulary-server — הוראות העלאה ל-Cloud Run

## מה יש כאן

| קובץ | תפקיד |
|---|---|
| app.py | השרת עצמו (Flask) |
| requirements.txt | רשימת ספריות Python |
| Dockerfile | מתכון לבניית הקונטיינר |

---

## שלב 1 — הכן שני מפתחות

לפני הכל תצטרך שני ערכים:

**GEMINI_API_KEY** — המפתח שיש לך מ-Google AI Studio

**CLIENT_API_KEY** — מפתח שאתה ממציא עכשיו בעצמך.
  זה הסיסמה שה-VBA שלך ישלח בכל בקשה.
  אפשר ליצור אחד חזק כאן: https://generate-random.org/api-key-generator
  לדוגמה: voc-a7f3k9m2p1x8z5q4

שמור את שניהם במקום בטוח.

---

## שלב 2 — העלה את הקבצים ל-Cloud Run

1. פתח: https://console.cloud.google.com/run
2. לחץ "Create Service"
3. בחר "Continuously deploy from a repository" אם יש לך GitHub,
   או "Deploy one revision from an existing container image" — ואז בחר "Build from source"
4. העלה את תיקיית הפרויקט (שלושת הקבצים)
5. הגדר:
   - Region: europe-west1 (אירופה — קרוב לישראל)
   - Authentication: Allow unauthenticated invocations (חשוב! כדי ש-Word יוכל לגשת)
   - Minimum instances: 1 (כדי שלא יהיה cold start)
   - Memory: 512MB
   - CPU: 1

---

## שלב 3 — הגדר את המפתחות כ-Environment Variables

בדף ה-Cloud Run Service, תחת "Variables & Secrets":

```
GEMINI_API_KEY = המפתח שלך מגוגל
CLIENT_API_KEY = המפתח שהמצאת בשלב 1
```

**חשוב: לעולם אל תשים מפתחות בתוך הקוד עצמו.**

---

## שלב 4 — עדכן את ה-VBA

אחרי שה-Deploy הצליח, תקבל URL שנראה כך:
`https://vocabulary-server-xxxxxxxx-ew.a.run.app`

בקוד ה-VBA שלך, שנה:
- את ה-URL מ-`http://127.0.0.1:5000/vocabulary` לכתובת החדשה
- הוסף Header: `X-Client-Key: המפתח שהמצאת`

---

## בדיקה מהירה

אחרי העלאה, תוכל לבדוק שהשרת חי:
```
https://YOUR-URL.a.run.app/health
```
אמור להחזיר: `{"status": "ok"}`
