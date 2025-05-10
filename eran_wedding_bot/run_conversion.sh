#!/bin/bash

# סקריפט להפעלת המרת קבצי OGG חדשים ל-MP3

# מעבר לתיקיית הפרויקט
cd "$(dirname "$0")/.." || exit

# הפעלת הסקריפט להמרת קבצים חדשים בלבד
python3 eran_wedding_bot/convert_to_mp3.py --only-new

echo "המרת קבצים הסתיימה" 