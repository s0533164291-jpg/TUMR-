# שלב 1: בחר image בסיס — Python רשמי, גרסה קטנה וקלה
FROM python:3.11-slim

# שלב 2: הגדר תיקיית עבודה בתוך הקונטיינר
WORKDIR /app

# שלב 3: העתק requirements והתקן ספריות
# (עושים את זה לפני העתקת הקוד כדי שה-cache יעבוד טוב יותר)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# שלב 4: העתק את כל הקוד
COPY . .

# שלב 5: Cloud Run מגדיר את ה-PORT אוטומטית — gunicorn יאזין עליו
# (אל תשנה את השורה הזו)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 60 app:app
