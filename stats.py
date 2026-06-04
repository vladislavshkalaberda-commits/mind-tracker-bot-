import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
import os

# Color palette
COLORS = {
    "positive": "#4CAF50",
    "negative": "#F44336",
    "neutral": "#9E9E9E",
    "mixed": "#FF9800",
    "yes": "#4CAF50",
    "partly": "#FF9800",
    "no": "#F44336",
    "bg": "#0F0F1A",
    "card": "#1A1A2E",
    "text": "#E0E0E0",
    "accent": "#7C4DFF",
}

MOOD_LABELS = {
    "positive": "😊 Позитивные",
    "negative": "😔 Негативные",
    "neutral": "😐 Нейтральные",
    "mixed": "🌀 Смешанные",
}

REALITY_LABELS = {
    "yes": "✅ Да",
    "partly": "🤔 Частично",
    "no": "❌ Нет",
}

STATE_LABELS = {
    "good": "😄 Хорошо",
    "normal": "😐 Нормально",
    "bad": "😔 Плохо",
    "irritated": "😤 Раздражён",
    "tired": "😴 Устал",
}

STATE_COLORS = {
    "good": "#4CAF50",
    "normal": "#2196F3",
    "bad": "#F44336",
    "irritated": "#FF5722",
    "tired": "#9C27B0",
}


def setup_dark_style():
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
        'font.family': 'DejaVu Sans',
    })


def mood_to_score(mood: str) -> float:
    return {"positive": 1.0, "mixed": 0.5, "neutral": 0.3, "negative": 0.0}.get(mood, 0.5)


def reality_to_score(r: str) -> float:
    return {"yes": 1.0, "partly": 0.5, "no": 0.0}.get(r, 0.5)


def generate_daily_stats(chat_id: str, db) -> Optional[str]:
    responses = db.get_responses_today(chat_id)
    if len(responses) < 2:
        return None

    setup_dark_style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.patch.set_facecolor(COLORS["bg"])
    fig.suptitle(
        f"📊 Mind Tracker — {datetime.now().strftime('%d.%m.%Y')}",
        color=COLORS["text"], fontsize=16, fontweight='bold', y=0.98
    )

    times = []
    for r in responses:
        try:
            dt = datetime.fromisoformat(r["timestamp"])
            times.append(dt.strftime("%H:%M"))
        except:
            times.append("")

    # Chart 1: Mood over time
    ax1 = axes[0, 0]
    mood_scores = [mood_to_score(r["q1"]) for r in responses]
    mood_colors = [COLORS.get(r["q1"], COLORS["neutral"]) for r in responses]
    ax1.plot(range(len(times)), mood_scores, color=COLORS["accent"], linewidth=2, zorder=2)
    ax1.scatter(range(len(times)), mood_scores, c=mood_colors, s=80, zorder=3)
    ax1.set_xticks(range(len(times)))
    ax1.set_xticklabels(times, rotation=45, fontsize=8)
    ax1.set_ylim(-0.1, 1.1)
    ax1.set_yticks([0, 0.5, 1])
    ax1.set_yticklabels(["Негат.", "Нейтр.", "Позит."], fontsize=8)
    ax1.set_title("Тип мыслей по времени", color=COLORS["text"], fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Chart 2: Reality alignment
    ax2 = axes[0, 1]
    reality_scores = [reality_to_score(r["q2"]) for r in responses]
    bar_colors = [COLORS.get(r["q2"], COLORS["neutral"]) for r in responses]
    ax2.bar(range(len(times)), reality_scores, color=bar_colors, alpha=0.85)
    avg = np.mean(reality_scores)
    ax2.axhline(avg, color='white', linestyle='--', alpha=0.5, linewidth=1)
    ax2.text(len(times) - 0.5, avg + 0.03, f'среднее: {avg:.0%}', color='white', fontsize=8, ha='right')
    ax2.set_xticks(range(len(times)))
    ax2.set_xticklabels(times, rotation=45, fontsize=8)
    ax2.set_ylim(0, 1.2)
    ax2.set_yticks([0, 0.5, 1])
    ax2.set_yticklabels(["Нет", "Частично", "Да"], fontsize=8)
    ax2.set_title("Хотел бы эти мысли в реальность?", color=COLORS["text"], fontsize=11)
    ax2.grid(True, alpha=0.3)

    # Chart 3: Control over thoughts
    ax3 = axes[1, 0]
    control = [int(r["q4"]) if r["q4"].isdigit() else 3 for r in responses]
    ax3.fill_between(range(len(times)), control, alpha=0.3, color=COLORS["accent"])
    ax3.plot(range(len(times)), control, color=COLORS["accent"], linewidth=2)
    ax3.set_xticks(range(len(times)))
    ax3.set_xticklabels(times, rotation=45, fontsize=8)
    ax3.set_ylim(0.5, 5.5)
    ax3.set_yticks([1, 2, 3, 4, 5])
    ax3.set_title("Контроль над мыслями", color=COLORS["text"], fontsize=11)
    ax3.grid(True, alpha=0.3)

    # Chart 4: State distribution (pie)
    ax4 = axes[1, 1]
    state_counts = {}
    for r in responses:
        s = r["q6"]
        state_counts[s] = state_counts.get(s, 0) + 1

    if state_counts:
        labels = [STATE_LABELS.get(k, k) for k in state_counts.keys()]
        sizes = list(state_counts.values())
        colors_pie = [STATE_COLORS.get(k, "#888") for k in state_counts.keys()]
        ax4.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.0f%%',
                textprops={'color': COLORS["text"], 'fontsize': 9},
                pctdistance=0.8, startangle=90)
        ax4.set_title("Состояние сегодня", color=COLORS["text"], fontsize=11)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    path = f"/tmp/stats_daily_{chat_id}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=COLORS["bg"])
    plt.close()
    return path


def generate_weekly_stats(chat_id: str, db) -> Optional[str]:
    responses = db.get_responses_last_days(chat_id, days=7)
    if len(responses) < 5:
        return None

    # Group by date
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

    setup_dark_style()
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.patch.set_facecolor(COLORS["bg"])
    fig.suptitle("📈 Mind Tracker — Статистика за неделю",
                 color=COLORS["text"], fontsize=16, fontweight='bold')

    # Chart 1: Average mood per day
    ax1 = axes[0]
    avg_mood = [np.mean([mood_to_score(r["q1"]) for r in by_date[d]]) for d in days]
    bar_colors = [COLORS["positive"] if v > 0.6 else COLORS["negative"] if v < 0.35 else COLORS["neutral"]
                  for v in avg_mood]
    ax1.bar(days, avg_mood, color=bar_colors, alpha=0.85)
    ax1.plot(days, avg_mood, color='white', linewidth=1.5, linestyle='--', alpha=0.5)
    ax1.set_ylim(0, 1.1)
    ax1.set_yticks([0, 0.5, 1])
    ax1.set_yticklabels(["Негат.", "Нейтр.", "Позит."])
    ax1.set_title("Средний тон мыслей", color=COLORS["text"], fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')

    # Chart 2: Reality alignment trend
    ax2 = axes[1]
    avg_reality = [np.mean([reality_to_score(r["q2"]) for r in by_date[d]]) for d in days]
    ax2.fill_between(range(len(days)), avg_reality, alpha=0.2, color=COLORS["accent"])
    ax2.plot(range(len(days)), avg_reality, color=COLORS["accent"], linewidth=2.5, marker='o', markersize=8)
    ax2.set_xticks(range(len(days)))
    ax2.set_xticklabels(days, rotation=45)
    ax2.set_ylim(0, 1.1)
    ax2.set_yticks([0, 0.5, 1])
    ax2.set_yticklabels(["Нет", "Частично", "Да"])
    ax2.set_title("Мысли → в реальность?", color=COLORS["text"], fontsize=12)
    ax2.grid(True, alpha=0.3)

    # Add trend arrow
    if len(avg_reality) >= 2:
        trend = avg_reality[-1] - avg_reality[0]
        trend_text = "↑ Растёт" if trend > 0.1 else "↓ Снижается" if trend < -0.1 else "→ Стабильно"
        trend_color = COLORS["positive"] if trend > 0.1 else COLORS["negative"] if trend < -0.1 else COLORS["neutral"]
        ax2.text(0.5, 0.05, trend_text, transform=ax2.transAxes,
                 ha='center', fontsize=12, color=trend_color, fontweight='bold')

    # Chart 3: Activity (surveys completed per day)
    ax3 = axes[2]
    counts = [len(by_date[d]) for d in days]
    ax3.bar(days, counts, color=COLORS["accent"], alpha=0.7)
    ax3.axhline(12, color='white', linestyle='--', alpha=0.4, linewidth=1)
    ax3.text(0, 12.2, 'цель: 12', color='white', fontsize=8, alpha=0.6)
    ax3.set_title("Пройдено опросов", color=COLORS["text"], fontsize=12)
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    path = f"/tmp/stats_weekly_{chat_id}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=COLORS["bg"])
    plt.close()
    return path
