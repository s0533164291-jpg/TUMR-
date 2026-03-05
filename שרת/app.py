from flask import Flask, request, jsonify
import requests
import json
import os
import hmac

app = Flask(__name__)
app.json.ensure_ascii = False

# ---- מפתחות ----
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# מפתח לקוח — Word ישלח אותו בכל בקשה בתוך Header
# תגדיר אותו ב-Cloud Run כ-Environment Variable בשם CLIENT_API_KEY
CLIENT_API_KEY = os.environ.get("CLIENT_API_KEY", "")

# ---- הגדרות Gemini ----
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def check_client_key():
    """
    בודק שה-Header מכיל מפתח לקוח תקין.
    מחזיר None אם הכול תקין, או response שגיאה אם לא.
    """
    if not CLIENT_API_KEY:
        # אם לא הוגדר מפתח בשרת — נאפשר גישה (מצב פיתוח)
        return None

    incoming_key = request.headers.get("X-Client-Key", "")
    # hmac.compare_digest מגן מפני timing attacks
    if not hmac.compare_digest(incoming_key, CLIENT_API_KEY):
        return jsonify({"error": "גישה נדחתה — מפתח לקוח לא תקין"}), 401

    return None


@app.route("/vocabulary", methods=["POST"])
def vocabulary():
    # ---- בדיקת מפתח לקוח ----
    auth_error = check_client_key()
    if auth_error:
        return auth_error

    try:
        data = request.get_json(silent=True)
        if not data or "word" not in data or "paragraph" not in data:
            return jsonify({"error": "חסרים שדות 'word' או 'paragraph'"}), 400

        word = str(data["word"]).strip()
        paragraph = str(data["paragraph"]).strip()

        if not word:
            return jsonify({"error": "לא התקבלה מילה"}), 400

        if not paragraph:
            return jsonify({"error": "לא התקבלה פסקה"}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "מפתח Gemini לא הוגדר בשרת"}), 500

        prompt = f"""אתה עורך ספרותי מקצועי בעברית. המשתמש מחפש חלופות למילה מסוימת.

הפסקה המלאה (להבנת ההקשר, הנושא והסגנון):
\"\"\"{paragraph}\"\"\"

המילה שהמשתמש רוצה להחליף: "{word}"

המשימה:
- הצע 6 עד 8 מילים חלופיות למילה "{word}"
- החלופות חייבות להתאים לנושא הפסקה ולסגנון הכתיבה שלה
- אל תציע מילים גנריות שלא מתאימות להקשר
- שמור על אותו זמן פועל / מין / יחיד-רבים כמו המקור

החזר JSON בדיוק בפורמט הזה, ללא טקסט נוסף:
{{"alternatives": ["מילה1", "מילה2", "מילה3", "מילה4", "מילה5", "מילה6"]}}"""

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        resp = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            headers=headers,
            json=payload,
            timeout=(5, 25)
        )

        if resp.status_code != 200:
            # לוגים לשרת בלבד — לא חושפים פרטים ללקוח
            try:
                err_detail = resp.json()
            except Exception:
                err_detail = resp.text
            print(f"[Gemini Error] status={resp.status_code} detail={err_detail}")
            return jsonify({"error": f"שגיאת Gemini ({resp.status_code}) — בדוק לוגי שרת"}), 500

        api_result = resp.json()

        candidates = api_result.get("candidates", [])
        if not candidates:
            return jsonify({"error": "לא התקבלה תשובה מהמודל"}), 500

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        raw = "".join(p.get("text", "") for p in parts).strip()

        if not raw:
            return jsonify({"error": "תשובת המודל ריקה"}), 500

        # ניקוי markdown fences
        if raw.startswith("```"):
            chunks = raw.split("```")
            if len(chunks) >= 2:
                raw = chunks[1]
                if raw.lower().startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

        result = json.loads(raw)

        alts = result.get("alternatives")
        if not isinstance(alts, list):
            return jsonify({"error": "פורמט תשובה לא תקין מהמודל"}), 500

        result["alternatives"] = [str(x).strip() for x in alts if str(x).strip()]

        return jsonify(result)

    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout מול Gemini"}), 504

    except requests.exceptions.SSLError as e:
        return jsonify({"error": f"שגיאת SSL מול Gemini: {str(e)}"}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"שגיאת רשת מול Gemini: {str(e)}"}), 500

    except json.JSONDecodeError:
        return jsonify({"error": "שגיאה בפענוח תגובת ה-AI"}), 500

    except Exception as e:
        return jsonify({"error": f"שגיאת שרת: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # רק לפיתוח מקומי — ב-Cloud Run רץ gunicorn
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
