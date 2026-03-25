# Workflow: הרצת אפליקציית הלמידה

## Objective
הפעל את אפליקציית הלמידה העברית של Claude Code ופתח אותה בדפדפן.

## Inputs Required
- `ANTHROPIC_API_KEY` מוגדר בקובץ `.env`
- Python 3.9+ מותקן
- ספריות pip: `flask`, `anthropic`, `python-dotenv`

## Steps

### 1. וודא שהמפתח מוגדר
```
# בדוק שהקובץ .env מכיל:
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 2. התקן תלויות (פעם ראשונה בלבד)
```bash
pip install -r requirements.txt
```

### 3. הרץ את השרת
```bash
python tools/app.py
```

### 4. פתח בדפדפן
```
http://localhost:5000
```

## Expected Output
- האפליקציה נטענת עם 4 מודולים בעברית
- ניווט RTL תקין
- כפתורי "דמו חי" עובדים (מחייב ANTHROPIC_API_KEY תקין)
- הגשת תרגיל מחזירה משוב מ-Claude בעברית

## Edge Cases

| בעיה | פתרון |
|------|-------|
| `ANTHROPIC_API_KEY is not set` | הוסף את המפתח ל-.env ב-root הפרויקט |
| Port 5000 תפוס | הוסף `PORT=5001` ל-.env |
| תגובות האפליקציה איטיות | זה נורמלי — קריאות API לוקחות 2-5 שניות |
| `ModuleNotFoundError: flask` | הרץ `pip install -r requirements.txt` שוב |

## Notes
- התקדמות נשמרת ב-`.tmp/progress.json` — אפשר למחוק לאיפוס
- לוג Flask מופיע בטרמינל — שימושי לדיבאג
