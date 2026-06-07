from telegram import InlineKeyboardButton, InlineKeyboardMarkup

QUESTIONS = [
    {
        "id": 0,
        "text": "Где ты был последние 15 минут?",
        "options": [
            {"label": "🧠 В мыслях", "value": "thinking"},
            {"label": "🎯 В деле / действии / контент", "value": "doing"},
            {"label": "😶 В моменте / без мыслей", "value": "present"},
        ]
    },
    {
        "id": 1,
        "text": "Эти мысли строят твою желаемую жизнь?",
        "options": [
            {"label": "🔥 Да — заряжают и ведут вперёд", "value": "yes"},
            {"label": "〰️ Нейтрально", "value": "neutral"},
            {"label": "❌ Нет — уводят в сторону", "value": "no"},
        ]
    },
    {
        "id": 2,
        "text": "Ты осознавал свои мысли в моменте?",
        "options": [
            {"label": "👁️ Да — наблюдал и осознавал", "value": "conscious"},
            {"label": "〰️ Частично", "value": "partial"},
            {"label": "🌀 Нет — заметил только сейчас", "value": "unaware"},
        ]
    },
]

# If first answer is not "thinking" — end survey after q1
STOP_AFTER_Q1 = {"doing", "present"}


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
