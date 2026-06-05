from telegram import InlineKeyboardButton, InlineKeyboardMarkup

QUESTIONS = [
    {
        "id": 0,
        "text": "Какой преобладал тип мыслей последние 15 минут?",
        "options": [
            {"label": "😊 Позитивные", "value": "positive"},
            {"label": "😔 Негативные", "value": "negative"},
            {"label": "😐 Нейтральные", "value": "neutral"},
            {"label": "🌀 Смешанные", "value": "mixed"},
        ]
    },
    {
        "id": 1,
        "text": "Хотел бы ты, чтобы мысли последних 15 минут стали твоей реальностью?",
        "options": [
            {"label": "✅ Да, с удовольствием", "value": "yes"},
            {"label": "🤔 Частично", "value": "partly"},
            {"label": "❌ Нет", "value": "no"},
            {"label": "⚪ Нейтрально / не относится", "value": "neutral"},
        ]
    },
    {
        "id": 2,
        "text": "Как приходили мысли?",
        "options": [
            {"label": "🎯 Осознанно — я направлял мысли", "value": "conscious"},
            {"label": "🌊 Сами по себе — приятно", "value": "flow_positive"},
            {"label": "🌀 Сами по себе — неприятно", "value": "flow_negative"},
            {"label": "〰️ Сами по себе — нейтрально", "value": "flow_neutral"},
        ]
    },
    {
        "id": 3,
        "text": "Насколько ты управлял своими мыслями?",
        "options": [
            {"label": "1 — Мысли сами по себе", "value": "1"},
            {"label": "2", "value": "2"},
            {"label": "3 — Средне", "value": "3"},
            {"label": "4", "value": "4"},
            {"label": "5 — Я управлял", "value": "5"},
        ]
    },
    {
        "id": 4,
        "text": "Было ли желание избежать каких-то мыслей?",
        "options": [
            {"label": "😬 Да", "value": "yes"},
            {"label": "🙂 Нет", "value": "no"},
            {"label": "🤷 Не заметил", "value": "unnoticed"},
        ]
    },
    {
        "id": 5,
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
