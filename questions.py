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
        ]
    },
    {
        "id": 2,
        "text": "Были ли мысли цикличными? (возвращался к одному и тому же)",
        "options": [
            {"label": "🔁 Да, сильно", "value": "strong"},
            {"label": "〰️ Немного", "value": "little"},
            {"label": "✨ Нет", "value": "no"},
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
        "text": "Общее состояние прямо сейчас?",
        "options": [
            {"label": "😄 Хорошо", "value": "good"},
            {"label": "😐 Нормально", "value": "normal"},
            {"label": "😔 Плохо", "value": "bad"},
            {"label": "😤 Раздражён", "value": "irritated"},
            {"label": "😴 Устал", "value": "tired"},
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
            callback_data=f"q{q_id}_{opt['value']}"
        )])

    return InlineKeyboardMarkup(buttons)
