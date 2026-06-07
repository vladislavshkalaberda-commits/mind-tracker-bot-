from telegram import InlineKeyboardButton, InlineKeyboardMarkup

QUESTIONS = [
    {
        "id": 0,
        "text": "О чём были мысли последние 15 минут?",
        "options": [
            {"label": "🔮 О будущем / мечты / планы", "value": "future"},
            {"label": "🔄 Прокручивал прошлую ситуацию", "value": "past"},
            {"label": "💬 Гипотетический сценарий", "value": "hypothetical"},
            {"label": "📚 Информация / абстрактное", "value": "abstract"},
            {"label": "💼 Рабочая задача", "value": "work"},
            {"label": "👤 О себе / самоанализ", "value": "self"},
            {"label": "🌐 Блуждание / ни о чём конкретном", "value": "wandering"},
            {"label": "🗣️ Разговаривал / общался", "value": "talking"},
            {"label": "🎯 В потоке / полностью в деле", "value": "flow"},
            {"label": "😶 Практически без мыслей / в моменте", "value": "present"},
        ]
    },
    {
        "id": 1,
        "text": "Эти мысли были заряжены позитивно?",
        "options": [
            {"label": "🔥 Да — воодушевляли и заряжали", "value": "charged"},
            {"label": "😌 Нейтрально — без особого заряда", "value": "neutral"},
            {"label": "😔 Нет — тянули вниз или тревожили", "value": "negative"},
        ]
    },
    {
        "id": 2,
        "text": "Как ты управлял мыслями?",
        "options": [
            {"label": "🎯 Осознанно — я направлял", "value": "conscious"},
            {"label": "〰️ Частично — иногда уплывал", "value": "partial"},
            {"label": "🌀 Не управлял — мысли сами по себе", "value": "uncontrolled"},
        ]
    },
    {
        "id": 3,
        "text": "Было ли желание избежать каких-то мыслей?",
        "options": [
            {"label": "😬 Да", "value": "yes"},
            {"label": "🙂 Нет", "value": "no"},
            {"label": "🤷 Не заметил", "value": "unnoticed"},
        ]
    },
    {
        "id": 4,
        "text": "Какое ощущение дали тебе эти мысли?",
        "options": [
            {"label": "🔥 Заряжен / вдохновлён", "value": "energized"},
            {"label": "😊 Легко / радостно", "value": "light"},
            {"label": "😌 Спокоен / умиротворён", "value": "calm"},
            {"label": "⚪ Нейтрально", "value": "neutral"},
            {"label": "😔 Грустно / расстроен", "value": "sad"},
            {"label": "😰 Тревожно / беспокойно", "value": "anxious"},
            {"label": "😤 Злость / раздражение", "value": "angry"},
            {"label": "🌫️ Подавлен / опустошён", "value": "drained"},
        ]
    },
]

# Topics where q2 is skipped (no emotional charge question)
SKIP_Q2 = {"abstract", "work"}

# Topics where entire survey ends after q1
STOP_AFTER_Q1 = {"talking", "flow", "present"}


def get_keyboard(question_index: int) -> InlineKeyboardMarkup:
    question = QUESTIONS[question_index]
    q_id = question["id"]
    buttons = []
    for opt in question["options"]:
        buttons.append([InlineKeyboardButton(
            opt["label"],
            callback_data=f"ans_{q_id}_{opt['value']}"
        )])
    return InlineKeyboardMarkup(buttons)
