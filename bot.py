import logging
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from database import Database
from questions import QUESTIONS, SKIP_Q2, STOP_AFTER_Q1, STOP_AFTER_Q1
from stats import generate_daily_stats, generate_weekly_stats, generate_monthly_stats
import os
from datetime import datetime, timedelta
import pytz

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
TZ = pytz.timezone("Europe/Paris")

db = Database()
current_session = {}
bot_instance = None
scheduler = None

SURVEYS_PER_DAY = 30
MIN_GAP_MINUTES = 15


def get_chat_id():
    if CHAT_ID:
        return CHAT_ID
    try:
        with open("chat_id.txt", "r") as f:
            return f.read().strip()
    except:
        return None


def generate_random_times(n, start_hour=9, end_hour=22, min_gap=15):
    total_minutes = (end_hour - start_hour) * 60
    times = []
    attempts = 0
    while len(times) < n and attempts < 10000:
        attempts += 1
        candidate = random.randint(0, total_minutes)
        if all(abs(candidate - t) >= min_gap for t in times):
            times.append(candidate)
    return sorted(times)


def schedule_random_surveys():
    global scheduler
    now = datetime.now(TZ)
    today = now.date()
    start = TZ.localize(datetime(today.year, today.month, today.day, 9, 0))
    offsets = generate_random_times(SURVEYS_PER_DAY, min_gap=MIN_GAP_MINUTES)
    count = 0
    for offset_minutes in offsets:
        send_time = start + timedelta(minutes=offset_minutes)
        if send_time > now:
            try:
                scheduler.add_job(
                    scheduled_job,
                    trigger=DateTrigger(run_date=send_time),
                    id=f"survey_{offset_minutes}_{today}"
                )
                count += 1
            except:
                pass
    logger.info(f"✅ Scheduled {count} random surveys for today")


def get_next_question_index(session):
    current = session["question_index"]
    if current == 1:
        topic = session["answers"].get("q1", "")
        if topic in STOP_AFTER_Q1:
            return len(QUESTIONS)
        if topic in SKIP_Q2:
            return 2
    return current


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db.register_user(chat_id)
    with open("chat_id.txt", "w") as f:
        f.write(chat_id)
    await update.message.reply_text(
        "🧠 *Mind Tracker запущен!*\n\n"
        "До 30 опросов в день в случайные моменты с 9:00 до 22:00.\n"
        "Минимум 15 минут между опросами.\n\n"
        "Автоматическая статистика:\n"
        "• Каждый день в 22:30\n"
        "• Каждое воскресенье\n"
        "• Каждое 1-е число месяца\n\n"
        "Команды:\n"
        "/survey — опрос прямо сейчас\n"
        "/stats — статистика за сегодня\n"
        "/week — статистика за неделю\n"
        "/month — статистика за месяц",
        parse_mode="Markdown"
    )


async def send_question(chat_id, bot, question_index, edit_message=None):
    from questions import get_keyboard
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

    if data == "start_survey":
        current_session[chat_id] = {
            "answers": {},
            "timestamp": datetime.now().isoformat(),
            "question_index": 0
        }
        await send_question(chat_id, context.bot, 0, edit_message=query.message)
        return

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
        if session["question_index"] != q_index:
            return

        question = QUESTIONS[q_index]
        selected_label = next((opt["label"] for opt in question["options"] if opt["value"] == value), value)
        session["answers"][f"q{q_index + 1}"] = value
        session["question_index"] += 1

        await query.edit_message_text(
            f"✅ *{question['text']}*\n→ {selected_label}",
            parse_mode="Markdown"
        )

        # Check if we need to skip q2
        next_index = get_next_question_index(session)
        session["question_index"] = next_index

        if next_index >= len(QUESTIONS):
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
        await update.message.reply_text("Пока недостаточно данных. Пройди хотя бы 3 опроса!")


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text("📈 Генерирую статистику за неделю...")
    img_path = generate_weekly_stats(chat_id, db)
    if img_path:
        with open(img_path, "rb") as f:
            await update.message.reply_photo(f, caption="📈 Статистика за неделю")
    else:
        await update.message.reply_text("Пока недостаточно данных. Нужна хотя бы пара дней!")


async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text("📅 Генерирую статистику за месяц...")
    img_path = generate_monthly_stats(chat_id, db)
    if img_path:
        with open(img_path, "rb") as f:
            await update.message.reply_photo(f, caption="📅 Статистика за месяц")
    else:
        await update.message.reply_text("Пока недостаточно данных. Нужен хотя бы месяц!")


async def send_auto_stats(period: str):
    global bot_instance
    chat_id = get_chat_id()
    if not chat_id or not bot_instance:
        return
    if period == "daily":
        img_path = generate_daily_stats(chat_id, db)
        caption = "📊 Итоги дня"
    elif period == "weekly":
        img_path = generate_weekly_stats(chat_id, db)
        caption = "📈 Итоги недели"
    elif period == "monthly":
        img_path = generate_monthly_stats(chat_id, db)
        caption = "📅 Итоги месяца"
    else:
        return

    if img_path:
        try:
            with open(img_path, "rb") as f:
                await bot_instance.send_photo(chat_id=chat_id, photo=f, caption=caption)
        except Exception as e:
            logger.error(f"Failed to send auto stats: {e}")


async def scheduled_job():
    global bot_instance
    if bot_instance is None:
        return
    chat_id = get_chat_id()
    if not chat_id:
        logger.warning("No chat_id found, skipping survey")
        return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 Пройти опрос", callback_data="start_survey")
    ]])
    try:
        await bot_instance.send_message(
            chat_id=chat_id,
            text="🔔 *Время опроса!*\n\nКак твои мысли последние 15 минут?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"✅ Survey sent to {chat_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send survey: {e}")


async def main():
    global bot_instance, scheduler

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("survey", survey_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("week", week_command))
    app.add_handler(CommandHandler("month", month_command))
    app.add_handler(CallbackQueryHandler(handle_callback))

    await app.initialize()
    bot_instance = app.bot
    logger.info("✅ Bot initialized")

    scheduler = AsyncIOScheduler(timezone=TZ)

    # Random surveys
    schedule_random_surveys()

    # Reschedule every day at 00:01
    scheduler.add_job(schedule_random_surveys, trigger="cron", hour=0, minute=1)

    # Auto stats
    scheduler.add_job(lambda: asyncio.create_task(send_auto_stats("daily")),
                      trigger="cron", hour=22, minute=30)
    scheduler.add_job(lambda: asyncio.create_task(send_auto_stats("weekly")),
                      trigger="cron", day_of_week="sun", hour=21, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(send_auto_stats("monthly")),
                      trigger="cron", day=1, hour=21, minute=0)

    scheduler.start()
    logger.info("✅ Scheduler started")

    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("✅ Bot is polling!")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
