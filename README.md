# 💜 Lexy Userbot

מנוע יוזרבוט מבוסס Pyrogram (Pyrofork) עם פלאגינים לניהול ושימוש יומיומי.

## 🚀 התקנה מהירה

1. שכפל את הריפו:
   ```bash
   git clone https://github.com/Tj-Bots/lexy-userbot.git
   cd lexy-userbot
   ```

2. התקן דרישות:
   ```bash
   pip install -r requirements.txt
   ```

3. הגדר משתני סביבה:
   צור קובץ `.env` מתוך `.env.example` ומלא את הפרטים:
   - `API_ID`
   - `API_HASH`
   - `SESSION_STRING`

4. הרץ:
   ```bash
   python lexy_main.py
   ```

## 🐳 Docker
ניתן להריץ גם באמצעות Docker:
```bash
docker build -t lexy-userbot .
docker run -d --env-file .env lexy-userbot
```

## 🛠 פלאגינים
היוזרבוט כולל פלאגינים בתיקייה `userbot/`:
- `tools.py` - כלי עזר (ID, JSON, Shortener).
- `translate.py` - תרגום הודעות.
- `tts.py` - טקסט לדיבור.
- `managroup.py` - ניהול קבוצות.
- ועוד...

---
**פותח עבור לקסי 💜**
