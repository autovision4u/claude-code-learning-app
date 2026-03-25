# Workflow: הוספת מודול לימוד חדש

## Objective
הוסף מודול לימוד חדש לאפליקציה.

## Inputs Required
- נושא המודול (כותרת עברית)
- 3-5 מושגים ללמד
- 3 שאלות חידון עם תשובות נכונות
- תרגיל מעשי אחד

## Steps

### 1. צור קובץ JSON למודול
```
data/lessons/module_N_topic.json
```
עקוב אחר הסכמה של מודולים קיימים. שדות חובה:
- `module_id`, `title_he`, `description_he`, `icon`, `order`
- `lessons[]` עם content_blocks
- `quiz` עם 3 שאלות ו-`passing_score: 2`
- `exercise` עם `system_prompt_file`

### 2. צור system prompt לתרגיל (אם שונה מהקיים)
```
data/system_prompts/exercise_feedback_N.txt
```
רוב המודולים יכולים להשתמש ב-`exercise_feedback.txt` הקיים.

### 3. בדוק את האפליקציה
```bash
python tools/app.py
```
נווט למודול החדש וודא:
- כל השיעורים נטענים
- החידון עובד וציון נשמר
- התרגיל שולח ל-Claude ומחזיר משוב בעברית

### 4. עדכן workflow זה
הוסף כל עצה, מגבלה, או גילוי חדש לסעיף "Notes" למטה.

## Content Block Types Available

| סוג | שימוש |
|-----|-------|
| `text` | פסקת הסבר בעברית |
| `code` | בלוק קוד עם caption ושפה |
| `comparison` | השוואה bad vs. good |
| `live_demo` | כפתור שקורא ל-API ומציג תגובה חיה |
| `tip` | בלוק טיפ מודגש |

## Notes
- `order` חייב להיות ייחודי — הגדל ב-1 מהמודול האחרון
- `live_demo` דורש שדות `system` ו-`prompt`
- קבצי JSON חייבים להיות UTF-8 (תמיכה בעברית)
- `lesson_loader.py` ממשיך את הכל על ידי glob על `module_*.json`
