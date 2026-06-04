import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
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

TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

db = Database()
current_session = {}


def get_chat_id():
    if CHAT_ID:
        return CHAT_ID
    try:
        with open("chat_id.txt", "r") as f:
            return f.read().strip()
    except:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db.register_user(chat_id)
    with open("chat_id.txt", "w") as f:
        f.write(chat_id)
    await update.message.reply_text(
        "🧠 *Mind Tracker запущен!*\n\n"
        "Я буду отправлять тебе опросы 12 раз в день с 9:00 до 22:00.\n\n"
        "Каждый опрос занимает ~30 секунд.\n\n"
        "Команды:\n"
        "/survey — пройти опрос прямо сейчас\n"
        "/stats — статистика за сегодня\n"
        "/week — статистика за неделю",
        parse_mode="Markdown"
    )


async def send_question(chat_id, bot, question_index, edit_message=None):
    question = QUESTIONS[question_index]
    keyboard = get_keyboard(question_index)
    text = f"*Вопрос {question_index + 1} из {len(QUESTIONS)}*\n\n{question['text']}"

    if edit_message:
        try:
            await edit_message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        except:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="Markdown")


async def survey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    current_session[chat_id] = {
        "answers": {},
        "timestamp": datetime.now().isoformat(),
        "question_index": 0
    }
    await send_question(chat_id, context.bot, 0)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = str(query.from_user.id)
    data = query.data

    # Start survey button
    if data == "start_survey":
        current_session[chat_id] = {
            "answers": {},
            "timestamp": datetime.now().isoformat(),
            "question_index": 0
        }
        await send_question(chat_id, context.bot, 0, edit_message=query.message)
        return

    # Answer button: format is "ans_QINDEX_VALUE"
    if data.startswith("ans_"):
        parts = data.split("_", 2)
        if len(parts) != 3:
            return

        q_index = int(parts[1])
        value = parts[2]

        if chat_id not in current_session:
            await query.message.reply_text("Нажми /survey чтобы начать новый опрос.")
            return

        session = current_session[chat_id]

        # Ignore if answer is for old question
        if session["question_index"] != q_index:
            return

        # Save answer
        question = QUESTIONS[q_index]
        selected_label = next((opt["label"] for opt in question["options"] if opt["value"] == value), value)
        session["answers"][f"q{q_index + 1}"] = value
        session["question_index"] += 1

        # Show selected
        await query.edit_message_text(
            f"✅ *{question['text']}*\n→ {selected_label}",
            parse_mode="Markdown"
        )

        next_index = session["question_index"]

        if next_index >= len(QUESTIONS):
            # Done
            db.save_response(chat_id, session["answers"], session["timestamp"])
            del current_session[chat_id]
            await query.message.reply_text(
                "✨ *Записано!*\n\nКаждый ответ — шаг к более осознанному мышлению.",
                parse_mode="Markdown"
            )
        else:
            await send_question(chat_id, context.bot, next_index)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text("📊 Генерирую статистику за сегодня...")
    img_path = generate_daily_stats(chat_id, db)
    if img_path:
        with open(img_path, "rb") as f:
            await update.message.reply_photo(f, caption="📊 Статистика за сегодня")
    else:
        await update.message.reply_text("Пока недостаточно данных. Пройди хотя бы 3–4 опроса!")


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text("📈 Генерирую статистику за неделю...")
    img_path = generate_weekly_stats(chat_id, db)
    if img_path:
        with open(img_path, "rb") as f:
            await update.message.reply_photo(f, caption="📈 Статистика за неделю")
    else:
        await update.message.reply_text("Пока недостаточно данных. Нужна хотя бы пара дней!")


async def send_scheduled_survey(bot, chat_id: str):
    if not chat_id:
        return
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


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("survey", survey_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("week", week_command))
    app.add_handler(CallbackQueryHandler(handle_callback))

    scheduler = AsyncIOScheduler(timezone="Europe/Paris")
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
            trigger="cron", hour=hour, minute=minute
        )

    scheduler.start()
    logger.info("Mind Tracker Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

