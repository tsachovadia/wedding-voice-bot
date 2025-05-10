import telegram.ext
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode # Import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
import logging
import re
import os # For path manipulation and directory creation

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# מומלץ לשמור את הטוקן בקובץ הגדרות או משתנה סביבה ולא ישירות בקוד
BOT_TOKEN = "7939548555:AAFe4TZRa5S6Q7YW-HTJtb-abeC8KRtqjFI"  # החלף עם הטוקן האמיתי שלך
RECORDINGS_DIR = "eran_wedding_bot/recordings" # תיקייה לשמירת הקלטות

# Define categories as a list of dictionaries
CATEGORIES = [
    {
        "display_name": "לפני הדרופ - קריאות עידוד והתלהבות",
        "technical_name": "pre_drop",
        "explanation": "קטעים קצרים ונמרצים לבנייה של האנרגיה לקראת שיא הטראק. קריאות, עידוד, התלהבות!",
        "examples": [
            "'יאללה ערן!'",
            "'עכשיו זה מתחיל!'",
            "'תנו לו, תנו לו!'",
            "קריאות התלהבות, צעקות קצרות, מחיאות כפיים"
        ],
        "length_hint": "2-5 שניות"
    },
    {
        "display_name": "רעיונות כלליים / מה שבא לכם",
        "technical_name": "general_ideas",
        "explanation": "אם יש לכם רעיון שלא התאים לקטגוריות האחרות, או סתם משהו שאתם רוצים להגיד - זה המקום!",
        "examples": [
            "'מזל טוב!'",
            "'אוהבים אתכם!'",
            "(כל קטע קולי אחר שתרצו)"
        ],
        "length_hint": "גמיש"
    }
]

# States for conversation
(ASKING_NAME, AWAITING_START_CONFIRMATION, 
 ASKING_FOR_RECORDING, AWAITING_POST_RECORDING_CHOICE, 
 FINISHED_BUT_CAN_CONTINUE) = range(5)  # הוספת מצב חדש למצב סיום אבל עם אפשרות להמשיך

# Helper function to escape MarkdownV2 characters
def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2 format.
    See https://core.telegram.org/bots/api#markdownv2-style for the reserved characters.
    """
    if not isinstance(text, str):
        text = str(text) # Ensure text is a string
    
    # List of special characters that need to be escaped in MarkdownV2
    for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(char, f'\\{char}')
    
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the user's name."""
    user = update.message.from_user
    logger.info(f"User {user.id} ({user.first_name} {user.last_name or ''}) started the bot.")
    # Ensure recordings directory exists
    os.makedirs(RECORDINGS_DIR, exist_ok=True)

    # שליחת סרטון פתיחה
    # בדיקה אם קיים אחד מהפורמטים האפשריים
    media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
    video_paths = [
        os.path.join(media_dir, "intro_video.mp4"),
        os.path.join(media_dir, "intro_video.mov"),
        os.path.join(media_dir, "intro_video.m4v")
    ]
    
    video_path = None
    for path in video_paths:
        if os.path.exists(path):
            video_path = path
            break
    
    if video_path:
        try:
            await update.message.reply_video(
                video=open(video_path, 'rb'),
                caption="היי! אני צח, חבר של ערן. בוא נכין ביחד הפתעה לחתונה!",
                supports_streaming=True
            )
            logger.info(f"Sent intro video to user {user.id} from {video_path}")
        except Exception as e:
            logger.error(f"Failed to send intro video: {e}")
    else:
        logger.warning(f"Intro video not found in any format at {media_dir}")

    welcome_message = (
        "היי! איזה כיף שהצטרפת! אני הבוט של צח, ובאתי לעזור לאסוף הקלטות סודיות ומיוחדות לחתונה של ערן ועדי. "
        "המטרה היא להכין להם קטע טראנס קורע ומפתיע! כל מילה שלך חשובה."
    )
    await update.message.reply_text(welcome_message)
    
    important_note = (
        "⚠️ מספר דגשים חשובים ⚠️\n\n"
        "🔊 אנרגיה גבוהה: חשוב מאוד להקליט עם הרבה אנרגיה והתלהבות - זה מה שיעשה את הקטע הזה מיוחד!\n\n"
        "🎯 הדוגמאות הן המלצות בלבד: אל תרגיש מוגבל, הטקסטים שמוצגים הם רק המלצות והכי טוב לאלתר ולהיות אותנטי.\n\n"
        "🎤 איכות ההקלטה: חשוב להקליט במקום שקט, קרוב למיקרופון, עם דיבור ברור."
    )
    important_note_escaped = escape_markdown_v2(important_note)
    await update.message.reply_text(important_note_escaped, parse_mode=ParseMode.MARKDOWN_V2)
    
    await update.message.reply_text(
        "כדי שאוכל לשמור את ההקלטות שלך בצורה מסודרת, בבקשה כתוב לי את שמך באנגלית (למשל, Noam)."
    )
    
    return ASKING_NAME

async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name_input = update.message.text
    if not re.fullmatch(r"^[a-zA-Z\s]+$", user_name_input):
        await update.message.reply_text("השם שהזנת אינו תקין. הוא צריך להכיל רק אותיות באנגלית ורווחים. נסה שוב בבקשה.")
        return ASKING_NAME

    user_name = user_name_input.strip().replace(" ", "_")
    context.user_data['name'] = user_name
    context.user_data['user_recordings_dir'] = os.path.join(RECORDINGS_DIR, user_name)
    os.makedirs(context.user_data['user_recordings_dir'], exist_ok=True)
    
    logger.info(f"User {update.message.from_user.id} entered valid name: {user_name}. Directory created: {context.user_data['user_recordings_dir']}")
    
    reply_text = escape_markdown_v2(
        f"מעולה {user_name}, תודה! אנחנו הולכים לעבור על כמה סוגי הקלטות. "
        "לכל קטגוריה אתן לך הסבר ודוגמאות, אבל הכי טוב אם תחשוב על משהו אישי משלך. "
        "מוכן להתחיל עם הקטגוריה הראשונה?"
    )
    
    keyboard = [[InlineKeyboardButton("כן, בוא נתחיל!", callback_data='start_categories')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN_V2)
    await update.message.reply_text("לחץ על הכפתור כדי להתחיל:", reply_markup=reply_markup)
    return AWAITING_START_CONFIRMATION

async def start_categories_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'start_categories' button press and presents the first category."""
    query = update.callback_query
    await query.answer()
    user_name = context.user_data.get('name', 'משתמש')

    logger.info(f"User {user_name} ({query.from_user.id}) confirmed to start categories.")
    message_text = escape_markdown_v2(f"נהדר {user_name}! מתחילים...")
    await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)

    context.user_data['current_category_index'] = 0
    context.user_data['current_take_number'] = 1
    return await present_category(update, context)

async def present_category(update: Update, context: ContextTypes.DEFAULT_TYPE, is_retry: bool = False) -> int:
    """Presents the current category to the user."""
    category_index = context.user_data.get('current_category_index', 0)
    user_name = context.user_data.get('name', 'משתמש')

    if category_index >= len(CATEGORIES):
        # הגענו לקטגוריה האחרונה - מציגים הודעת סיום עם אפשרות לחזור
        final_message = escape_markdown_v2(f"סיימת את כל הקטגוריות! כל הכבוד ותודה רבה!\nהכל נשמר אצלי לסודי סודות.")
        target_message = update.callback_query.message if update.callback_query else update.message
        if target_message:
            await target_message.reply_text(final_message, parse_mode=ParseMode.MARKDOWN_V2)
            
            # הצגת כפתורים לחזרה או לסיום סופי
            keyboard = [
                [InlineKeyboardButton("רוצה לחזור להקליט בקטגוריה אחרת", callback_data='select_category')],
                [InlineKeyboardButton("סיימתי סופית", callback_data='final_finish')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await target_message.reply_text("אפשר לסיים או לחזור להקליט בקטגוריות אחרות:", reply_markup=reply_markup)
            
        logger.info(f"User {user_name} reached end of categories.")
        # לא מנקים את המידע כדי שנוכל לחזור אחורה בהמשך
        return FINISHED_BUT_CAN_CONTINUE

    current_category = CATEGORIES[category_index]
    
    # בנייה של הודעת הסבר הקטגוריה
    text = f"יאללה {user_name}!\n"
    if is_retry:
        text += f"קטגוריה נוכחית: *{current_category['display_name']}*.\n"
    else:
        text += f"הקטגוריה הבאה היא: *{current_category['display_name']}*\n\n"
    
    text += f"{current_category['explanation']}\n"
    
    # הוספת דוגמאות אם קיימות
    if current_category['examples']:
        text += "\nדוגמאות:\n"
        for example in current_category['examples']:
            text += f"- {example}\n"
    
    # הוספת מידע על אורך אם קיים
    if current_category['length_hint']:
        text += f"\nאורך רצוי: {current_category['length_hint']}.\n"
    
    text += "\nאנא הקלט לפחות שתיים או שלוש הקלטות בכל קטגוריה. אל תפחד לאלתר! מה הדבר הראשון שהיית אומר? שלח לי הקלטה קולית."

    # שליחת ההודעה - עטוף את כל הטקסט ב-escape_markdown_v2
    escaped_text = escape_markdown_v2(text)
    target_message_reply_func = None
    if update.callback_query:
        target_message_reply_func = update.callback_query.message.reply_text 
    elif update.message:
        target_message_reply_func = update.message.reply_text
    
    if target_message_reply_func:
        await target_message_reply_func(escaped_text, parse_mode=ParseMode.MARKDOWN_V2)
        
        # מציג גם כפתורי ניווט כדי לאפשר מעבר בין קטגוריות גם בלי הקלטה
        keyboard = []
        
        # כפתור להקלטה
        keyboard.append([InlineKeyboardButton("רוצה להקליט כאן", callback_data='stay_and_record')])
        
        # כפתורי ניווט קדימה ואחורה
        navigation_row = []
        if category_index > 0:
            navigation_row.append(InlineKeyboardButton("⏮️ קטגוריה קודמת", callback_data='previous_category_no_rec'))
        
        if category_index < len(CATEGORIES) - 1:
            navigation_row.append(InlineKeyboardButton("קטגוריה הבאה ⏭️", callback_data='next_category_no_rec'))
        
        if navigation_row:
            keyboard.append(navigation_row)
        
        # כפתור סיום רק אם זו הקטגוריה האחרונה
        if category_index == len(CATEGORIES) - 1:
            keyboard.append([InlineKeyboardButton("סיימתי להקליט", callback_data='finish_recording')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await target_message_reply_func("אתה יכול לשלוח הקלטה קולית או לבחור אחת מהאפשרויות:", reply_markup=reply_markup)
    
    return ASKING_FOR_RECORDING

async def received_voice_recording(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the voice recording sent by the user."""
    user = update.message.from_user
    user_name = context.user_data.get('name', 'unknown_user')
    user_recordings_dir = context.user_data.get('user_recordings_dir', RECORDINGS_DIR) # Fallback, but should be set
    category_index = context.user_data.get('current_category_index', 0)
    current_category = CATEGORIES[category_index]
    category_name_technical = current_category['technical_name']
    take_number = context.user_data.get('current_take_number', 1)

    voice = update.message.voice
    if not voice:
        await update.message.reply_text("אופס, נראה שזו לא הקלטה קולית. נסה לשלוח הקלטה בבקשה.")
        return ASKING_FOR_RECORDING

    try:
        # קבלת הקובץ מטלגרם
        file = await voice.get_file()
        
        # יצירת שם קובץ
        ogg_filename = f"{user_name}_{category_name_technical}_take{take_number}.ogg"
        
        # וידוא שהתיקייה קיימת
        os.makedirs(user_recordings_dir, exist_ok=True)
        
        # נתיב מלא לקובץ
        ogg_path = os.path.join(user_recordings_dir, ogg_filename)
        
        # הורדת הקובץ
        await file.download_to_drive(ogg_path)
        
        logger.info(f"Recording saved: {ogg_path} from user {user_name} ({user.id})")
        
        message_text = escape_markdown_v2(f"אדיר {user_name}! הקלטה מעולה נשמרה ({ogg_filename}).")
        await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN_V2)
        
        # Prepare for next action
        keyboard = [
            [InlineKeyboardButton("טייק נוסף לאותה קטגוריה", callback_data='take_again')],
            [InlineKeyboardButton("המשך לקטגוריה הבאה", callback_data='next_category')]
        ]
        
        # כפתור קטגוריה קודמת רק אם לא בקטגוריה הראשונה
        if category_index > 0:
            keyboard.append([InlineKeyboardButton("חזור לקטגוריה הקודמת", callback_data='previous_category')])
        
        # כפתור סיום רק אם זו הקטגוריה האחרונה
        if category_index == len(CATEGORIES) - 1:
            keyboard.append([InlineKeyboardButton("סיימתי להקליט", callback_data='finish_recording')])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("מה תרצה לעשות עכשיו?", reply_markup=reply_markup)
        
        return AWAITING_POST_RECORDING_CHOICE

    except Exception as e:
        logger.error(f"Error saving recording for user {user_name}: {e}", exc_info=True)
        await update.message.reply_text("אוי, קרתה תקלה בשמירת ההקלטה. תוכל לנסות לשלוח שוב? אם הבעיה חוזרת, אנא הודע לצח.")
        return ASKING_FOR_RECORDING # Stay in the same state to allow retry

async def handle_take_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['current_take_number'] = context.user_data.get('current_take_number', 0) + 1
    user_name = context.user_data.get('name', 'משתמש')
    message_text = escape_markdown_v2(f"בטח {user_name}! עוד רעיון לאותה קטגוריה...")
    await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
    return await present_category(update, context, is_retry=True)

async def handle_next_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """מעבר לקטגוריה הבאה אחרי הקלטה."""
    query = update.callback_query
    await query.answer()
    context.user_data['current_category_index'] = context.user_data.get('current_category_index', -1) + 1
    context.user_data['current_take_number'] = 1 
    user_name = context.user_data.get('name', 'משתמש')
    
    if context.user_data['current_category_index'] < len(CATEGORIES):
        message_text = escape_markdown_v2(f"מעולה {user_name}, עוברים לקטגוריה הבאה...")
        await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
    
    return await present_category(update, context)

async def handle_previous_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """מעבר לקטגוריה הקודמת אחרי הקלטה."""
    query = update.callback_query
    await query.answer()
    current_index = context.user_data.get('current_category_index', 0)
    user_name = context.user_data.get('name', 'משתמש')

    if current_index > 0:
        context.user_data['current_category_index'] = current_index - 1
        context.user_data['current_take_number'] = 1 
        message_text = escape_markdown_v2(f"אוקיי {user_name}, חוזרים לקטגוריה הקודמת...")
        await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
        return await present_category(update, context)
    else:
        message_text = escape_markdown_v2(f"אין קטגוריה קודמת, {user_name}. אנחנו כבר בקטגוריה הראשונה.")
        await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
        return await present_navigation_options(update, context)

async def handle_finish_recording(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_name = context.user_data.get('name', 'משתמש')
    
    final_message = escape_markdown_v2(
        f"{user_name}, תודה רבה רבה על ההקלטות המושקעות! "
        "זה הולך להיות חלק מהפתעה אדירה לערן ועדי. "
        "זכור לשמור על סודיות מוחלטת! נתראה בחתונה! צח."
    )
    await query.edit_message_text(text=final_message, parse_mode=ParseMode.MARKDOWN_V2)
    logger.info(f"User {user_name} ({query.from_user.id}) finished the recording process via button.")
    context.user_data.clear()
    return ConversationHandler.END

async def received_non_voice_in_recording_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles non-voice messages when expecting a recording."""
    user_name = context.user_data.get('name', 'משתמש')
    message_text = escape_markdown_v2(
        f"אופס {user_name}, אני מצפה להקלטה קולית בשלב זה. נסה שוב בבקשה. "
        "אם אתה צריך עזרה, תמיד אפשר לשלוח /cancel ולהתחיל מחדש."
    )
    await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN_V2)
    return ASKING_FOR_RECORDING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    user_name = context.user_data.get('name', user.first_name if user else "משתמש")
    user_name_escaped = escape_markdown_v2(user_name)
    logger.info(f"User {user_name_escaped} ({user.id if user else 'N/A'}) canceled the conversation.")
    await update.message.reply_text(
        "התהליך בוטל. אם תרצה להתחיל מחדש, פשוט שלח /start."
    )
    context.user_data.clear()
    return ConversationHandler.END

# פונקציות חדשות להצגת אפשרויות ניווט ולטיפול בניווט ללא הקלטה

async def present_navigation_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """מציג את אפשרויות הניווט בין הקטגוריות."""
    category_index = context.user_data.get('current_category_index', 0)
    
    keyboard = []
    
    # כפתור להקלטה
    keyboard.append([InlineKeyboardButton("רוצה להקליט כאן", callback_data='stay_and_record')])
    
    # כפתורי ניווט קדימה ואחורה
    navigation_row = []
    if category_index > 0:
        navigation_row.append(InlineKeyboardButton("⏮️ קטגוריה קודמת", callback_data='previous_category_no_rec'))
    
    if category_index < len(CATEGORIES) - 1:
        navigation_row.append(InlineKeyboardButton("קטגוריה הבאה ⏭️", callback_data='next_category_no_rec'))
    
    if navigation_row:
        keyboard.append(navigation_row)
    
    # כפתור סיום רק אם זו הקטגוריה האחרונה
    if category_index == len(CATEGORIES) - 1:
        keyboard.append([InlineKeyboardButton("סיימתי להקליט", callback_data='finish_recording')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    if query and query.message:
        await query.message.reply_text("מה תרצה לעשות עכשיו?", reply_markup=reply_markup)
    
    return ASKING_FOR_RECORDING

async def handle_next_category_no_rec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """מעבר לקטגוריה הבאה ללא הקלטה."""
    query = update.callback_query
    await query.answer()
    context.user_data['current_category_index'] = context.user_data.get('current_category_index', -1) + 1
    context.user_data['current_take_number'] = 1 
    user_name = context.user_data.get('name', 'משתמש')
    
    if context.user_data['current_category_index'] < len(CATEGORIES):
        message_text = escape_markdown_v2(f"מעולה {user_name}, עוברים לקטגוריה הבאה...")
        await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
    
    return await present_category(update, context)

async def handle_previous_category_no_rec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """מעבר לקטגוריה הקודמת ללא הקלטה."""
    query = update.callback_query
    await query.answer()
    current_index = context.user_data.get('current_category_index', 0)
    user_name = context.user_data.get('name', 'משתמש')

    if current_index > 0:
        context.user_data['current_category_index'] = current_index - 1
        context.user_data['current_take_number'] = 1 
        message_text = escape_markdown_v2(f"אוקיי {user_name}, חוזרים לקטגוריה הקודמת...")
        await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
        return await present_category(update, context)
    else:
        message_text = escape_markdown_v2(f"אין קטגוריה קודמת, {user_name}. אנחנו כבר בקטגוריה הראשונה.")
        await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
        return await present_navigation_options(update, context)

async def handle_stay_and_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """המשתמש בחר להישאר בקטגוריה הנוכחית ולהקליט."""
    query = update.callback_query
    await query.answer()
    current_category = CATEGORIES[context.user_data.get('current_category_index', 0)]
    message_text = escape_markdown_v2(f"מצוין! אני מחכה להקלטה שלך לקטגוריה: {current_category['display_name']}")
    await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
    return ASKING_FOR_RECORDING

async def handle_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """מציג למשתמש את כל הקטגוריות לבחירה."""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for i, category in enumerate(CATEGORIES):
        keyboard.append([InlineKeyboardButton(f"{i+1}. {category['display_name']}", callback_data=f'jump_to_category_{i}')])
    
    keyboard.append([InlineKeyboardButton("סיימתי סופית", callback_data='final_finish')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = escape_markdown_v2("בחר את הקטגוריה שתרצה לחזור אליה:")
    await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup)
    
    return FINISHED_BUT_CAN_CONTINUE

async def handle_jump_to_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """קפיצה ישירה לקטגוריה ספציפית."""
    query = update.callback_query
    await query.answer()
    
    # מחלץ את מספר הקטגוריה מה-callback_data
    category_index = int(query.data.split('_')[-1])
    context.user_data['current_category_index'] = category_index
    context.user_data['current_take_number'] = 1
    
    user_name = context.user_data.get('name', 'משתמש')
    message_text = escape_markdown_v2(f"מעולה {user_name}, קופצים לקטגוריה שבחרת...")
    await query.edit_message_text(text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
    
    return await present_category(update, context)

async def handle_final_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """סיום סופי של התהליך."""
    query = update.callback_query
    await query.answer()
    user_name = context.user_data.get('name', 'משתמש')
    
    final_message = escape_markdown_v2(
        f"{user_name}, תודה רבה רבה על ההקלטות המושקעות! "
        "זה הולך להיות חלק מהפתעה אדירה לערן ועדי. "
        "זכור לשמור על סודיות מוחלטת! נתראה בחתונה! צח."
    )
    await query.edit_message_text(text=final_message, parse_mode=ParseMode.MARKDOWN_V2)
    logger.info(f"User {user_name} ({query.from_user.id}) finished the recording process (final finish).")
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """Starts the bot."""
    # יצירת האפליקציה והעברת הטוקן של הבוט
    application = telegram.ext.Application.builder().token(BOT_TOKEN).build()

    # הגדרת ConversationHandler עבור UC1
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
            AWAITING_START_CONFIRMATION: [
                CallbackQueryHandler(start_categories_flow, pattern='^start_categories$')
            ],
            ASKING_FOR_RECORDING: [
                MessageHandler(filters.VOICE, received_voice_recording),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_non_voice_in_recording_state),
                CallbackQueryHandler(handle_next_category_no_rec, pattern='^next_category_no_rec$'),
                CallbackQueryHandler(handle_previous_category_no_rec, pattern='^previous_category_no_rec$'),
                CallbackQueryHandler(handle_stay_and_record, pattern='^stay_and_record$'),
                CallbackQueryHandler(handle_finish_recording, pattern='^finish_recording$')
            ],
            AWAITING_POST_RECORDING_CHOICE: [
                CallbackQueryHandler(handle_take_again, pattern='^take_again$'),
                CallbackQueryHandler(handle_next_category, pattern='^next_category$'),
                CallbackQueryHandler(handle_previous_category, pattern='^previous_category$'),
                CallbackQueryHandler(handle_finish_recording, pattern='^finish_recording$'),
            ],
            FINISHED_BUT_CAN_CONTINUE: [
                CallbackQueryHandler(handle_select_category, pattern='^select_category$'),
                CallbackQueryHandler(handle_final_finish, pattern='^final_finish$'),
                CallbackQueryHandler(handle_jump_to_category, pattern='^jump_to_category_\\d+$')
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # הפעלת הבוט עד שהמשתמש לוחץ Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main() 


