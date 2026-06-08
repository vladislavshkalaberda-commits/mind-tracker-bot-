import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, date, timedelta
from typing import Optional

COLORS = {
    "bg": "#0F0F1A",
    "card": "#1A1A2E",
    "text": "#E0E0E0",
    "accent": "#7C4DFF",
    "positive": "#4CAF50",
    "neutral": "#9E9E9E",
    "negative": "#F44336",
    "thinking": "#7C4DFF",
    "doing": "#2196F3",
    "present": "#4CAF50",
}

# q1: где был
STATE_LABELS = {
    "thinking": "🧠 В мыслях",
    "doing": "🎯 В деле",
    "present": "😶 В моменте",
}

# q2: мысли строят жизнь?
CHARGE_LABELS = {
    "yes": "🔥 Да",
    "neutral": "〰️ Нейтрально",
    "no": "❌ Нет",
}

CHARGE_COLORS = {
    "yes": "#4CAF50",
    "neutral": "#9E9E9E",
    "no": "#F44336",
}

# q3: осознанность
AWARE_LABELS = {
    "conscious": "👁️ Осознавал",
    "partial": "〰️ Частично",
    "unaware": "🌀 Не заметил",
}

def charge_score(c):
    return {"yes": 1.0, "neutral": 0.5, "no": 0.0}.get(c, 0.5)

def aware_score(a):
    return {"conscious": 1.0, "partial": 0.5, "unaware": 0.0}.get(a, 0.5)

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

    total = len(responses)
    thinking = [r for r in responses if r.get("q1") == "thinking"]

    # Chart 1: Где был — pie
    ax1 = axes[0, 0]
    state_counts = {}
    for r in responses:
        s = r.get("q1", "thinking")
        state_counts[s] = state_counts.get(s, 0) + 1
    labels = [STATE_LABELS.get(k, k) for k in state_counts]
    sizes = list(state_counts.values())
    colors_pie = [COLORS.get(k, COLORS["neutral"]) for k in state_counts]
    ax1.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.0f%%',
            textprops={'color': COLORS["text"], 'fontsize': 9}, startangle=90)
    ax1.set_title("Где ты был?", color=COLORS["text"], fontsize=11)

    # Chart 2: Заряд мыслей (только thinking)
    ax2 = axes[0, 1]
    if thinking:
        charge_counts = {}
        for r in thinking:
            c = r.get("q2", "neutral")
            charge_counts[c] = charge_counts.get(c, 0) + 1
        labels2 = [CHARGE_LABELS.get(k, k) for k in charge_counts]
        sizes2 = list(charge_counts.values())
        colors2 = [CHARGE_COLORS.get(k, COLORS["neutral"]) for k in charge_counts]
        ax2.pie(sizes2, labels=labels2, colors=colors2, autopct='%1.0f%%',
                textprops={'color': COLORS["text"], 'fontsize': 9}, startangle=90)
        ax2.set_title("Мысли строят жизнь?", color=COLORS["text"], fontsize=11)
    else:
        ax2.text(0.5, 0.5, "Нет данных\nо мыслях", ha='center', va='center',
                color=COLORS["text"], fontsize=12, transform=ax2.transAxes)
        ax2.set_title("Мысли строят жизнь?", color=COLORS["text"], fontsize=11)

    # Chart 3: Осознанность по времени
    ax3 = axes[1, 0]
    if thinking:
        times = []
        scores = []
        for r in thinking:
            try:
                dt = datetime.fromisoformat(r["timestamp"])
                times.append(dt.strftime("%H:%M"))
                scores.append(aware_score(r.get("q3", "partial")))
            except:
                pass
        if scores:
            ax3.fill_between(range(len(times)), scores, alpha=0.3, color=COLORS["accent"])
            ax3.plot(range(len(times)), scores, color=COLORS["accent"], linewidth=2, marker='o', markersize=6)
            ax3.set_xticks(range(len(times)))
            ax3.set_xticklabels(times, rotation=45, fontsize=7)
            ax3.set_ylim(-0.1, 1.1)
            ax3.set_yticks([0, 0.5, 1])
            ax3.set_yticklabels(["Не заметил", "Частично", "Осознавал"], fontsize=8)
    ax3.set_title("Осознанность мышления", color=COLORS["text"], fontsize=11)
    ax3.grid(True, alpha=0.3)

    # Chart 4: Ключевые цифры дня
    ax4 = axes[1, 1]
    ax4.axis('off')

    thinking_pct = int(len(thinking) / total * 100) if total else 0
    present_pct = int(sum(1 for r in responses if r.get("q1") == "present") / total * 100) if total else 0
    doing_pct = int(sum(1 for r in responses if r.get("q1") == "doing") / total * 100) if total else 0

    if thinking:
        positive_pct = int(sum(1 for r in thinking if r.get("q2") == "yes") / len(thinking) * 100)
        aware_pct = int(np.mean([aware_score(r.get("q3", "partial")) for r in thinking]) * 100)
    else:
        positive_pct = 0
        aware_pct = 0

    summary = (
        f"📋 Пройдено опросов: {total}\n\n"
        f"🧠 В мыслях: {thinking_pct}%\n"
        f"🎯 В деле: {doing_pct}%\n"
        f"😶 В моменте: {present_pct}%\n\n"
        f"🔥 Мысли строят жизнь: {positive_pct}%\n"
        f"👁️ Осознанность: {aware_pct}%"
    )
    ax4.text(0.1, 0.9, summary, transform=ax4.transAxes,
             color=COLORS["text"], fontsize=11, va='top', linespacing=1.8)
    ax4.set_title("Итоги дня", color=COLORS["text"], fontsize=11)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
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

    # Chart 1: % позитивных мыслей по дням
    ax1 = axes[0]
    pos_pct = []
    for d in days:
        thinking = [r for r in by_date[d] if r.get("q1") == "thinking"]
        if thinking:
            pct = sum(1 for r in thinking if r.get("q2") == "yes") / len(thinking)
        else:
            pct = 0
        pos_pct.append(pct)
    bar_colors = [COLORS["positive"] if v > 0.6 else COLORS["negative"] if v < 0.35 else COLORS["neutral"] for v in pos_pct]
    ax1.bar(days, pos_pct, color=bar_colors, alpha=0.85)
    ax1.plot(days, pos_pct, color='white', linewidth=1.5, linestyle='--', alpha=0.5)
    ax1.set_ylim(0, 1.1)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax1.set_title("Мысли строят жизнь", color=COLORS["text"], fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')

    # Chart 2: Осознанность по дням
    ax2 = axes[1]
    aware_pct = []
    for d in days:
        thinking = [r for r in by_date[d] if r.get("q1") == "thinking"]
        if thinking:
            pct = np.mean([aware_score(r.get("q3", "partial")) for r in thinking])
        else:
            pct = 0
        aware_pct.append(pct)
    ax2.fill_between(range(len(days)), aware_pct, alpha=0.2, color=COLORS["accent"])
    ax2.plot(range(len(days)), aware_pct, color=COLORS["accent"], linewidth=2.5, marker='o', markersize=8)
    ax2.set_xticks(range(len(days)))
    ax2.set_xticklabels(days, rotation=45)
    ax2.set_ylim(0, 1.1)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax2.set_title("Осознанность", color=COLORS["text"], fontsize=12)
    ax2.grid(True, alpha=0.3)

    if len(aware_pct) >= 2:
        trend = aware_pct[-1] - aware_pct[0]
        trend_text = "↑ Растёт" if trend > 0.05 else "↓ Снижается" if trend < -0.05 else "→ Стабильно"
        trend_color = COLORS["positive"] if trend > 0.05 else COLORS["negative"] if trend < -0.05 else COLORS["neutral"]
        ax2.text(0.5, 0.05, trend_text, transform=ax2.transAxes,
                ha='center', fontsize=12, color=trend_color, fontweight='bold')

    # Chart 3: Где был по дням (stacked bar)
    ax3 = axes[2]
    thinking_pcts = []
    doing_pcts = []
    present_pcts = []
    for d in days:
        total = len(by_date[d])
        thinking_pcts.append(sum(1 for r in by_date[d] if r.get("q1") == "thinking") / total)
        doing_pcts.append(sum(1 for r in by_date[d] if r.get("q1") == "doing") / total)
        present_pcts.append(sum(1 for r in by_date[d] if r.get("q1") == "present") / total)

    x = range(len(days))
    ax3.bar(days, thinking_pcts, label="🧠 В мыслях", color=COLORS["thinking"], alpha=0.85)
    ax3.bar(days, doing_pcts, bottom=thinking_pcts, label="🎯 В деле", color=COLORS["doing"], alpha=0.85)
    ax3.bar(days, present_pcts, bottom=[t+d for t,d in zip(thinking_pcts, doing_pcts)],
            label="😶 В моменте", color=COLORS["present"], alpha=0.85)
    ax3.set_ylim(0, 1.1)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax3.set_title("Где ты был", color=COLORS["text"], fontsize=12)
    ax3.tick_params(axis='x', rotation=45)
    ax3.legend(fontsize=8, facecolor=COLORS["card"], labelcolor=COLORS["text"])

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
            week = f"Нед.{dt.isocalendar()[1]}"
            if week not in by_week:
                by_week[week] = []
            by_week[week].append(r)
        except:
            pass

    if len(by_week) < 2:
        return None

    weeks = sorted(by_week.keys())
    setup_dark()
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.patch.set_facecolor(COLORS["bg"])
    fig.suptitle("📅 Статистика за месяц", color=COLORS["text"], fontsize=16, fontweight='bold')

    # Chart 1: % позитивных мыслей по неделям
    ax1 = axes[0]
    pos_pct = []
    for w in weeks:
        thinking = [r for r in by_week[w] if r.get("q1") == "thinking"]
        pct = sum(1 for r in thinking if r.get("q2") == "yes") / len(thinking) if thinking else 0
        pos_pct.append(pct)
    ax1.fill_between(range(len(weeks)), pos_pct, alpha=0.2, color=COLORS["positive"])
    ax1.plot(range(len(weeks)), pos_pct, color=COLORS["positive"], linewidth=2.5, marker='o', markersize=8)
    ax1.set_xticks(range(len(weeks)))
    ax1.set_xticklabels(weeks)
    ax1.set_ylim(0, 1.1)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax1.set_title("Мысли строят жизнь", color=COLORS["text"], fontsize=12)
    ax1.grid(True, alpha=0.3)

    if len(pos_pct) >= 2:
        trend = pos_pct[-1] - pos_pct[0]
        trend_text = "↑ Растёт" if trend > 0.05 else "↓ Снижается" if trend < -0.05 else "→ Стабильно"
        trend_color = COLORS["positive"] if trend > 0.05 else COLORS["negative"] if trend < -0.05 else COLORS["neutral"]
        ax1.text(0.5, 0.05, trend_text, transform=ax1.transAxes,
                ha='center', fontsize=12, color=trend_color, fontweight='bold')

    # Chart 2: Осознанность по неделям
    ax2 = axes[1]
    aware_pct = []
    for w in weeks:
        thinking = [r for r in by_week[w] if r.get("q1") == "thinking"]
        pct = np.mean([aware_score(r.get("q3", "partial")) for r in thinking]) if thinking else 0
        aware_pct.append(pct)
    ax2.fill_between(range(len(weeks)), aware_pct, alpha=0.2, color=COLORS["accent"])
    ax2.plot(range(len(weeks)), aware_pct, color=COLORS["accent"], linewidth=2.5, marker='o', markersize=8)
    ax2.set_xticks(range(len(weeks)))
    ax2.set_xticklabels(weeks)
    ax2.set_ylim(0, 1.1)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax2.set_title("Осознанность", color=COLORS["text"], fontsize=12)
    ax2.grid(True, alpha=0.3)

    # Chart 3: Где был по неделям
    ax3 = axes[2]
    thinking_pcts = []
    doing_pcts = []
    present_pcts = []
    for w in weeks:
        total = len(by_week[w])
        thinking_pcts.append(sum(1 for r in by_week[w] if r.get("q1") == "thinking") / total)
        doing_pcts.append(sum(1 for r in by_week[w] if r.get("q1") == "doing") / total)
        present_pcts.append(sum(1 for r in by_week[w] if r.get("q1") == "present") / total)
    ax3.bar(weeks, thinking_pcts, label="🧠 В мыслях", color=COLORS["thinking"], alpha=0.85)
    ax3.bar(weeks, doing_pcts, bottom=thinking_pcts, label="🎯 В деле", color=COLORS["doing"], alpha=0.85)
    ax3.bar(weeks, present_pcts, bottom=[t+d for t,d in zip(thinking_pcts, doing_pcts)],
            label="😶 В моменте", color=COLORS["present"], alpha=0.85)
    ax3.set_ylim(0, 1.1)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x*100)}%'))
    ax3.set_title("Где ты был", color=COLORS["text"], fontsize=12)
    ax3.legend(fontsize=8, facecolor=COLORS["card"], labelcolor=COLORS["text"])

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = f"/tmp/stats_monthly_{chat_id}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=COLORS["bg"])
    plt.close()
    return path
