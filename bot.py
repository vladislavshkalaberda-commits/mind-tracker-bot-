import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import Database
from questions import QUESTIONS, get_keyboard
from stats import generate_daily_stats, generate_weekly_stats
import os
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "8879712863:AAHgr7_jeg0KYni5wDyXKThsPet3VBF1j4g")
CHAT_ID = os.getenv("CHAT_ID", "")

db = Database()

# Conversation states
Q1, Q2, Q3, Q4, Q5, Q6 = range(6)
STATES = [Q1, Q2, Q3, Q4, Q5, Q6]

current_session = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db.register_user(chat_id)

    # Save chat_id to file for scheduler
    with open("chat_id.txt", "w") as f:
        f.write(chat_id)

    await update.message.reply_text(
        "🧠 *Mind Tracker запущен!*\n\n"
        "Я буду отправлять тебе опросы 10–15 раз в день с 9:00 до 22:00.\n\n"
        "Каждый опрос занимает ~30 секунд. Со временем ты увидишь, "
        "как меняется качество твоих мыслей.\n\n"
        "Команды:\n"
        "/survey — пройти опрос прямо сейчас\n"
        "/stats — статистика за сегодня\n"
        "/week — статистика за неделю\n"
        "/stop — остановить опросы",
        parse_mode="Markdown"
    )


async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    current_session[chat_id] = {
        "answers": {},
        "timestamp": datetime.now().isoformat(),
        "question_index": 0
    }

    question = QUESTIONS[0]
    keyboard = get_keyboard(0)

    if update.callback_query:
        await update.callback_query.message.reply_text(
            f"📋 *Опрос* — {datetime.now().strftime('%H:%M')}\n\n"
            f"*{question['text']}*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"📋 *Опрос* — {datetime.now().strftime('%H:%M')}\n\n"
            f"*{question['text']}*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    return Q1


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = str(query.from_user.id)
    data = query.data

    if chat_id not in current_session:
        await query.message.reply_text("Нажми /survey чтобы начать новый опрос.")
        return ConversationHandler.END

    q_index = current_session[chat_id]["question_index"]
    current_session[chat_id]["answers"][f"q{q_index + 1}"] = data
    current_session[chat_id]["question_index"] += 1

    next_index = current_session[chat_id]["question_index"]

    # Edit the message to show selected answer
    question = QUESTIONS[q_index]
    selected_label = next((opt["label"] for opt in question["options"] if opt["value"] == data), data)
    await query.edit_message_text(
        f"✅ *{question['text']}*\n→ {selected_label}",
        parse_mode="Markdown"
    )

    if next_index >= len(QUESTIONS):
        # Survey complete
        answers = current_session[chat_id]["answers"]
        timestamp = current_session[chat_id]["timestamp"]
        db.save_response(chat_id, answers, timestamp)
        del current_session[chat_id]

        await query.message.reply_text(
            "✨ *Записано!*\n\nКаждый ответ — шаг к более осознанному мышлению.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    else:
        # Next question
        next_question = QUESTIONS[next_index]
        keyboard = get_keyboard(next_index)
        await query.message.reply_text(
            f"*{next_question['text']}*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return STATES[next_index]


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text("📊 Генерирую статистику за сегодня...")

    img_path = generate_daily_stats(chat_id, db)
    if img_path:
        with open(img_path, "rb") as f:
            await update.message.reply_photo(f, caption="📊 Статистика за сегодня")
    else:
        await update.message.reply_text(
            "Пока недостаточно данных. Пройди хотя бы 3–4 опроса!"
        )


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text("📈 Генерирую статистику за неделю...")

    img_path = generate_weekly_stats(chat_id, db)
    if img_path:
        with open(img_path, "rb") as f:
            await update.message.reply_photo(f, caption="📈 Статистика за неделю")
    else:
        await update.message.reply_text(
            "Пока недостаточно данных. Нужна хотя бы пара дней!"
        )


async def send_scheduled_survey(bot, chat_id: str):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 Пройти опрос", callback_data="start_survey")
    ]])
    try:
        await bot.send_message(
            chat_id=chat_id,
            text="🔔 *Время опроса!*\n\nКак твои мысли последние 15 минут?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send survey: {e}")


async def inline_start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "start_survey":
        await start_survey(update, context)


def get_chat_id():
    if CHAT_ID:
        return CHAT_ID
    try:
        with open("chat_id.txt", "r") as f:
            return f.read().strip()
    except:
        return None


def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("survey", start_survey),
            CallbackQueryHandler(start_survey, pattern="^start_survey$")
        ],
        states={
            Q1: [CallbackQueryHandler(handle_answer, pattern="^q0_")],
            Q2: [CallbackQueryHandler(handle_answer, pattern="^q1_")],
            Q3: [CallbackQueryHandler(handle_answer, pattern="^q2_")],
            Q4: [CallbackQueryHandler(handle_answer, pattern="^q3_")],
            Q5: [CallbackQueryHandler(handle_answer, pattern="^q4_")],
            Q6: [CallbackQueryHandler(handle_answer, pattern="^q5_")],
        },
        fallbacks=[CommandHandler("survey", start_survey)],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("week", week_command))
    app.add_handler(conv_handler)

    # Scheduler
    scheduler = AsyncIOScheduler()

    # 12 surveys from 9:00 to 22:00
    survey_times = [
        "09:00", "10:15", "11:30", "12:45", "14:00",
        "15:15", "16:30", "17:45", "19:00", "20:00",
        "21:00", "22:00"
    ]

    for time_str in survey_times:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(
            lambda h=hour, m=minute: asyncio.create_task(
                send_scheduled_survey(app.bot, get_chat_id() or "")
            ),
            trigger="cron",
            hour=hour,
            minute=minute
        )

    scheduler.start()

    logger.info("Mind Tracker Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
