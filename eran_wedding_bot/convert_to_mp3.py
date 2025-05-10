#!/usr/bin/env python3
# coding: utf-8

import os
import glob
import argparse
import subprocess
import logging
import time
import shutil

# הגדרת לוגר
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("convert_to_mp3")

# הגדרת נתיבים
RECORDINGS_DIR = "eran_wedding_bot/recordings"
MP3_OUTPUT_DIR = "eran_wedding_bot/mp3_recordings"

def create_output_structure():
    """יצירת תיקיית הפלט אם אינה קיימת"""
    if not os.path.exists(MP3_OUTPUT_DIR):
        os.makedirs(MP3_OUTPUT_DIR)
        logger.info(f"יצרתי תיקיית פלט חדשה: {MP3_OUTPUT_DIR}")

def find_all_ogg_files(only_new=False, last_run_file=".last_conversion_time"):
    """מציאת כל קבצי ה-OGG בתיקיית ההקלטות ובתת-תיקיות
    
    Args:
        only_new (bool): אם True, ימיר רק קבצים שנוצרו מאז הריצה האחרונה
        last_run_file (str): קובץ לשמירת זמן הריצה האחרונה
    
    Returns:
        list: רשימה של נתיבים לקבצי OGG
    """
    last_run_time = 0
    if only_new and os.path.exists(last_run_file):
        with open(last_run_file, "r") as f:
            try:
                last_run_time = float(f.read().strip())
                logger.info(f"זמן המרה אחרון: {time.ctime(last_run_time)}")
            except:
                logger.warning("לא ניתן לקרוא את זמן ההמרה האחרון, ממיר את כל הקבצים")
    
    ogg_files = []
    
    # חיפוש כל קבצי ה-OGG
    search_pattern = os.path.join(RECORDINGS_DIR, "**", "*.ogg")
    all_files = glob.glob(search_pattern, recursive=True)
    
    for file_path in all_files:
        if only_new:
            file_mtime = os.path.getmtime(file_path)
            if file_mtime <= last_run_time:
                continue
        ogg_files.append(file_path)
    
    # עדכון זמן ריצה אחרון
    with open(last_run_file, "w") as f:
        f.write(str(time.time()))
    
    return ogg_files

def convert_ogg_to_mp3(ogg_file_path):
    """המרת קובץ OGG ל-MP3 ושמירה בתיקיית הפלט באמצעות ffmpeg
    
    Args:
        ogg_file_path (str): נתיב לקובץ ה-OGG להמרה
    
    Returns:
        str: נתיב הקובץ המומר, או None אם ההמרה נכשלה
    """
    try:
        # יצירת נתיב יחסי (שמירה על המבנה המקורי)
        rel_path = os.path.relpath(ogg_file_path, RECORDINGS_DIR)
        dir_name = os.path.dirname(rel_path)
        base_name = os.path.basename(rel_path)
        
        # יצירת שם קובץ ה-MP3
        mp3_filename = os.path.splitext(base_name)[0] + ".mp3"
        mp3_dir = os.path.join(MP3_OUTPUT_DIR, dir_name)
        mp3_path = os.path.join(mp3_dir, mp3_filename)
        
        # וידוא שהתיקייה קיימת
        os.makedirs(mp3_dir, exist_ok=True)
        
        # המרה באמצעות ffmpeg
        cmd = ["ffmpeg", "-i", ogg_file_path, "-y", "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            error_message = result.stderr.decode('utf-8', errors='ignore')
            logger.error(f"שגיאת ffmpeg: {error_message}")
            return None
        
        logger.info(f"הומר בהצלחה: {ogg_file_path} -> {mp3_path}")
        return mp3_path
    
    except Exception as e:
        logger.error(f"שגיאה בהמרת {ogg_file_path}: {e}")
        return None

def copy_existing_mp3_files():
    """העתקת קבצי MP3 קיימים (אם יש כאלה) לתיקיית הפלט"""
    search_pattern = os.path.join(RECORDINGS_DIR, "**", "*.mp3")
    mp3_files = glob.glob(search_pattern, recursive=True)
    
    for mp3_file in mp3_files:
        try:
            # יצירת נתיב יחסי (שמירה על המבנה המקורי)
            rel_path = os.path.relpath(mp3_file, RECORDINGS_DIR)
            dir_name = os.path.dirname(rel_path)
            
            # יצירת תיקיית היעד
            dest_dir = os.path.join(MP3_OUTPUT_DIR, dir_name)
            os.makedirs(dest_dir, exist_ok=True)
            
            # העתקת הקובץ
            dest_file = os.path.join(MP3_OUTPUT_DIR, rel_path)
            shutil.copy2(mp3_file, dest_file)
            logger.info(f"הועתק: {mp3_file} -> {dest_file}")
        
        except Exception as e:
            logger.error(f"שגיאה בהעתקת {mp3_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="המרת קבצי הקלטות OGG ל-MP3")
    parser.add_argument("--only-new", action="store_true", help="המר רק קבצים חדשים מאז הריצה האחרונה")
    parser.add_argument("--copy-existing", action="store_true", help="העתק גם קבצי MP3 קיימים (אם יש כאלה)")
    
    args = parser.parse_args()
    
    # בדיקה שיש ffmpeg מותקן במערכת
    try:
        result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error("ffmpeg לא נמצא במערכת. אנא התקן אותו כדי להשתמש בסקריפט זה.")
            return
    except FileNotFoundError:
        logger.error("ffmpeg לא נמצא במערכת. אנא התקן אותו כדי להשתמש בסקריפט זה.")
        return
    
    # יצירת מבנה תיקיות הפלט
    create_output_structure()
    
    # מציאת קבצי OGG
    ogg_files = find_all_ogg_files(only_new=args.only_new)
    
    if not ogg_files:
        logger.info("לא נמצאו קבצי OGG להמרה.")
    else:
        logger.info(f"נמצאו {len(ogg_files)} קבצי OGG להמרה.")
        
        # המרת הקבצים
        successful_conversions = 0
        for ogg_file in ogg_files:
            if convert_ogg_to_mp3(ogg_file):
                successful_conversions += 1
        
        logger.info(f"הומרו בהצלחה: {successful_conversions} מתוך {len(ogg_files)} קבצים.")
    
    # העתקת קבצי MP3 קיימים אם ביקשו
    if args.copy_existing:
        copy_existing_mp3_files()
    
    logger.info("הפעולה הסתיימה.")

if __name__ == "__main__":
    main() 