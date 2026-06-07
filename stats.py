import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

COLORS = {
    "energized": "#FF6B35",
    "light": "#4CAF50",
    "calm": "#2196F3",
    "neutral": "#9E9E9E",
    "sad": "#7986CB",
    "anxious": "#FF9800",
    "angry": "#F44336",
    "drained": "#607D8B",
    "bg": "#0F0F1A",
    "card": "#1A1A2E",
    "text": "#E0E0E0",
    "accent": "#7C4DFF",
    "positive": "#4CAF50",
    "negative": "#F44336",
}

FEELING_LABELS = {
    "energized": "🔥 Заряжен",
    "light": "😊 Легко",
    "calm": "😌 Спокоен",
    "neutral": "⚪ Нейтрально",
    "sad": "😔 Грустно",
    "anxious": "😰 Тревожно",
    "angry": "😤 Злость",
    "drained": "🌫️ Подавлен",
}

TOPIC_LABELS = {
    "future": "🔮 Будущее",
    "past": "🔄 Прошлое",
    "hypothetical": "💬 Сценарий",
    "abstract": "📚 Абстрактное",
    "work": "💼 Работа",
    "self": "👤 Самоанализ",
    "wandering": "🌐 Блуждание",
}

POSITIVE_FEELINGS = {"energized", "light", "calm"}
NEGATIVE_FEELINGS = {"sad", "anxious", "angry", "drained"}

def feeling_score(f):
    return {"energized": 1.0, "light": 0.8, "calm": 0.6, "neutral": 0.5,
            "sad": 0.3, "anxious": 0.2, "angry": 0.1, "drained": 0.0}.get(f, 0.5)

def control_score(c):
    return {"conscious": 1.0, "partial": 0.5, "uncontrolled": 0.0}.get(c, 0.5)

def setup_dark():
    plt.rcParams.update({
        'figure.facecolor': COLORS["bg"],
        'axes.facecolor': COLORS["card"],
        'axes.edgecolor': '#2A2A3E',
        'axes.labelcolor': COLORS["text"],
        'xtick.color': COLORS["text"],
        'ytick.color': COLORS["text"],
        'text.color': COLORS["text"],
        'grid.color': '#2A2A3E',
        'grid.alpha': 0.5,
    })


def generate_daily_stats(chat_id: str, db) -> Optional[str]:
    responses = db.get_responses_today(chat_id)
    if len(responses) < 3:
        return None

    setup_dark()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.patch.set_facecolor(COLORS["bg"])
    fig.suptitle(f"📊 Итоги дня — {datetime.now().strftime('%d.%m.%Y')}",
                 color=COLORS["text"], fontsize=16, fontweight='bold')

    times = []
    for r in responses:
        try:
            dt = datetime.fromisoformat(r["timestamp"])
            times.append(dt.strftime("%H:%M"))
        except:
            times.append("")

    # Chart 1: Feeling over time
    ax1 = axes[0, 0]
    scores = [feeling_score(r.get("q5", "neutral")) for r in responses]
    colors = [COLORS.get(r.get("q5", "neutral"), COLORS["neutral"]) for r in responses]
    ax1.plot(range(len(times)), scores, color=COLORS["accent"], linewidth=2, zorder=2)
    ax1.scatter(range(len(times)), scores, c=colors, s=80, zorder=3)
    ax1.set_xticks(range(len(times)))
    ax1.set_xticklabels(times, rotation=45, fontsize=7)
    ax1.set_ylim(-0.1, 1.1)
    ax1.set_yticks([0, 0.5, 1])
    ax1.set_yticklabels(["Негат.", "Нейтр.", "Позит."], fontsize=8)
    ax1.set_title("Ощущения в течение дня", color=COLORS["text"], fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Chart 2: Control over time
    ax2 = axes[0, 1]
    ctrl = [control_score(r.get("q3", "partial")) for r in responses]
    ax2.fill_between(range(len(times)), ctrl, alpha=0.3, color=COLORS["accent"])
    ax2.plot(range(len(times)), ctrl, color=COLORS["accent"], linewidth=2)
    ax2.set_xticks(range(len(times)))
    ax2.set_xticklabels(times, rotation=45, fontsize=7)
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_yticks([0, 0.5, 1])
    ax2.set_yticklabels(["Не управлял", "Частично", "Осознанно"], fontsize=8)
    ax2.set_title("Осознанность мышления", color=COLORS["text"], fontsize=11)
    ax2.grid(True, alpha=0.3)

    # Chart 3: Topics pie
    ax3 = axes[1, 0]
    topic_counts = {}
    for r in responses:
        t = r.get("q1", "wandering")
        topic_counts[t] = topic_counts.get(t, 0) + 1
    if topic_counts:
        labels = [TOPIC_LABELS.get(k, k) for k in topic_counts]
        sizes = list(topic_counts.values())
        ax3.pie(sizes, labels=labels, autopct='%1.0f%%',
                textprops={'color': COLORS["text"], 'fontsize': 8},
                startangle=90)
        ax3.set_title("Темы мыслей", color=COLORS["text"], fontsize=11)

    # Chart 4: Positive vs Negative charge
    ax4 = axes[1, 1]
    charged = sum(1 for r in responses if r.get("q2") == "charged")
    neutral_q2 = sum(1 for r in responses if r.get("q2") == "neutral")
    negative_q2 = sum(1 for r in responses if r.get("q2") == "negative")
    skipped = len(responses) - charged - neutral_q2 - negative_q2

    labels = ["🔥 Заряжены", "😌 Нейтрально", "😔 Тянули вниз", "💼 Н/П"]
    values = [charged, neutral_q2, negative_q2, skipped]
    colors_bar = [COLORS["positive"], COLORS["neutral"], COLORS["negative"], "#555"]
    bars = ax4.bar(labels, values, color=colors_bar, alpha=0.85)
    for bar, val in zip(bars, values):
        if val > 0:
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(val), ha='center', color=COLORS["text"], fontsize=9)
    ax4.set_title("Заряд мыслей", color=COLORS["text"], fontsize=11)
    ax4.tick_params(axis='x', labelsize=7)
    ax4.grid(True, alpha=0.3, axis='y')

    # Summary text
    total = len(responses)
    pos_pct = int((charged / total) * 100) if total else 0
    ctrl_avg = np.mean(ctrl) if ctrl else 0
    ctrl_pct = int(ctrl_avg * 100)

    fig.text(0.5, 0.01,
             f"Пройдено опросов: {total}  |  Позитивный заряд: {pos_pct}%  |  Осознанность: {ctrl_pct}%",
             ha='center', color=COLORS["text"], fontsize=10)

    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    path = f"/tmp/stats_daily_{chat_id}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=COLORS["bg"])
    plt.close()
    return path


def generate_weekly_stats(chat_id: str, db) -> Optional[str]:
    responses = db.get_responses_last_days(chat_id, days=7)
    if len(responses) < 5:
        return None

    by_date = {}
    for r in responses:
        try:
            dt = datetime.fromisoformat(r["timestamp"])
            day = dt.strftime("%d.%m")
            if day not in by_date:
                by_date[day] = []
            by_date[day].append(r)
        except:
            pass

    if len(by_date) < 2:
        return None

    days = sorted(by_date.keys())
    setup_dark()
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.patch.set_facecolor(COLORS["bg"])
    fig.suptitle("📈 Статистика за неделю", color=COLORS["text"], fontsize=16, fontweight='bold')

    # Chart 1: Feeling trend
    ax1 = axes[0]
    avg_feeling = [np.mean([feeling_score(r.get("q5", "neutral")) for r in by_date[d]]) for d in days]
    bar_colors = [COLORS["positive"] if v > 0.6 else COLORS["negative"] if v < 0.35 else COLORS["neutral"] for v in avg_feeling]
    ax1.bar(days, avg_feeling, color=bar_colors, alpha=0.85)
    ax1.plot(days, avg_feeling, color='white', linewidth=1.5, linestyle='--', alpha=0.5)
    ax1.set_ylim(0, 1.1)
    ax1.set_yticks([0, 0.5, 1])
    ax1.set_yticklabels(["Негат.", "Нейтр.", "Позит."])
    ax1.set_title("Ощущения по дням", color=COLORS["text"], fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')

    # Chart 2: Positive charge trend
    ax2 = axes[1]
    charge_pct = []
    for d in days:
        rr = by_date[d]
        q2_responses = [r for r in rr if r.get("q2")]
        if q2_responses:
            pct = sum(1 for r in q2_responses if r.get("q2") == "charged") / len(q2_responses)
        else:
            pct = 0
        charge_pct.append(pct)

    ax2.fill_between(range(len(days)), charge_pct, alpha=0.2, color=COLORS["accent"])
    ax2.plot(range(len(days)), charge_pct, color=COLORS["accent"], linewidth=2.5, marker='o', markersize=8)
    ax2.set_xticks(range(len(days)))
    ax2.set_xticklabels(days, rotation=45)
    ax2.set_ylim(0, 1.1)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax2.set_title("% позитивного заряда", color=COLORS["text"], fontsize=12)
    ax2.grid(True, alpha=0.3)

    if len(charge_pct) >= 2:
        trend = charge_pct[-1] - charge_pct[0]
        trend_text = "↑ Растёт" if trend > 0.05 else "↓ Снижается" if trend < -0.05 else "→ Стабильно"
        trend_color = COLORS["positive"] if trend > 0.05 else COLORS["negative"] if trend < -0.05 else COLORS["neutral"]
        ax2.text(0.5, 0.05, trend_text, transform=ax2.transAxes,
                ha='center', fontsize=12, color=trend_color, fontweight='bold')

    # Chart 3: Control trend
    ax3 = axes[2]
    avg_control = [np.mean([control_score(r.get("q3", "partial")) for r in by_date[d]]) for d in days]
    ax3.fill_between(range(len(days)), avg_control, alpha=0.2, color="#FF6B35")
    ax3.plot(range(len(days)), avg_control, color="#FF6B35", linewidth=2.5, marker='o', markersize=8)
    ax3.set_xticks(range(len(days)))
    ax3.set_xticklabels(days, rotation=45)
    ax3.set_ylim(0, 1.1)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax3.set_title("Осознанность мышления", color=COLORS["text"], fontsize=12)
    ax3.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = f"/tmp/stats_weekly_{chat_id}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=COLORS["bg"])
    plt.close()
    return path


def generate_monthly_stats(chat_id: str, db) -> Optional[str]:
    responses = db.get_responses_last_days(chat_id, days=30)
    if len(responses) < 10:
        return None

    by_week = {}
    for r in responses:
        try:
            dt = datetime.fromisoformat(r["timestamp"])
            week = f"Нед. {dt.isocalendar()[1]}"
            if week not in by_week:
                by_week[week] = []
            by_week[week].append(r)
        except:
            pass

    if len(by_week) < 2:
        return None

    weeks = sorted(by_week.keys())
    setup_dark()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.patch.set_facecolor(COLORS["bg"])
    fig.suptitle("📅 Статистика за месяц", color=COLORS["text"], fontsize=16, fontweight='bold')

    # Chart 1: Feeling by week
    ax1 = axes[0, 0]
    avg_feeling = [np.mean([feeling_score(r.get("q5", "neutral")) for r in by_week[w]]) for w in weeks]
    ax1.bar(weeks, avg_feeling, color=COLORS["accent"], alpha=0.85)
    ax1.plot(weeks, avg_feeling, color='white', linewidth=1.5, linestyle='--', alpha=0.5)
    ax1.set_ylim(0, 1.1)
    ax1.set_title("Ощущения по неделям", color=COLORS["text"], fontsize=11)
    ax1.grid(True, alpha=0.3, axis='y')

    # Chart 2: Positive charge by week
    ax2 = axes[0, 1]
    charge_pct = []
    for w in weeks:
        rr = by_week[w]
        q2_r = [r for r in rr if r.get("q2")]
        pct = sum(1 for r in q2_r if r.get("q2") == "charged") / len(q2_r) if q2_r else 0
        charge_pct.append(pct)
    ax2.fill_between(range(len(weeks)), charge_pct, alpha=0.2, color=COLORS["positive"])
    ax2.plot(range(len(weeks)), charge_pct, color=COLORS["positive"], linewidth=2.5, marker='o')
    ax2.set_xticks(range(len(weeks)))
    ax2.set_xticklabels(weeks)
    ax2.set_ylim(0, 1.1)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax2.set_title("% позитивного заряда", color=COLORS["text"], fontsize=11)
    ax2.grid(True, alpha=0.3)

    # Chart 3: Topics for whole month
    ax3 = axes[1, 0]
    topic_counts = {}
    for r in responses:
        t = r.get("q1", "wandering")
        topic_counts[t] = topic_counts.get(t, 0) + 1
    if topic_counts:
        labels = [TOPIC_LABELS.get(k, k) for k in topic_counts]
        sizes = list(topic_counts.values())
        ax3.pie(sizes, labels=labels, autopct='%1.0f%%',
                textprops={'color': COLORS["text"], 'fontsize': 8}, startangle=90)
        ax3.set_title("Темы мыслей за месяц", color=COLORS["text"], fontsize=11)

    # Chart 4: Control by week
    ax4 = axes[1, 1]
    avg_ctrl = [np.mean([control_score(r.get("q3", "partial")) for r in by_week[w]]) for w in weeks]
    ax4.fill_between(range(len(weeks)), avg_ctrl, alpha=0.2, color="#FF6B35")
    ax4.plot(range(len(weeks)), avg_ctrl, color="#FF6B35", linewidth=2.5, marker='o')
    ax4.set_xticks(range(len(weeks)))
    ax4.set_xticklabels(weeks)
    ax4.set_ylim(0, 1.1)
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax4.set_title("Осознанность по неделям", color=COLORS["text"], fontsize=11)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = f"/tmp/stats_monthly_{chat_id}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=COLORS["bg"])
    plt.close()
    return path
