import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, date, timedelta
from typing import Optional

BG_COLOR = '#FFF8F0'
TEXT_COLOR = '#3D3548'
MUTED_COLOR = '#9B8DA8'
GRID_COLOR = '#E8DFF0'

STATE_COLORS = ['#FFB4A2', '#A8DADC', '#B8E0D2']  # thinking, doing, present
CHARGE_COLORS = ['#95D5B2', '#FFD6A5']  # positive, neutral/no
LINE_COLOR = '#FF8FA3'
LINE_FILL = '#FFD6E0'

STATE_LABELS_LEGEND = ['В мыслях', 'В деле', 'В моменте']
CHARGE_LABELS_LEGEND = ['Заряжали', 'Нейтрально/нет']


def charge_score(c):
    return {"yes": 1.0, "neutral": 0.5, "no": 0.0}.get(c, 0.5)


def aware_score(a):
    return {"conscious": 1.0, "partial": 0.5, "unaware": 0.0}.get(a, 0.5)


def setup_style():
    plt.rcParams.update({
        'figure.facecolor': BG_COLOR,
        'axes.facecolor': '#FFFFFF',
        'text.color': TEXT_COLOR,
        'font.family': 'sans-serif',
    })


def add_card_bg(ax):
    ax.set_facecolor('#FFFFFF')
    for spine in ax.spines.values():
        spine.set_visible(False)


def draw_donut(ax, values, colors, center_label, title, legend_labels):
    wedges, texts, autotexts = ax.pie(
        values, colors=colors, autopct='%1.0f%%', startangle=90,
        pctdistance=0.78,
        wedgeprops={'edgecolor': 'white', 'linewidth': 4, 'width': 0.45},
        textprops={'fontsize': 12, 'fontweight': 'bold', 'color': TEXT_COLOR}
    )
    ax.text(0, 0, center_label, fontsize=20, ha='center', va='center', fontweight='bold', color=TEXT_COLOR)
    ax.set_title(title, fontsize=15, fontweight='bold', color=TEXT_COLOR, pad=15)
    ax.legend(legend_labels, loc='upper center', bbox_to_anchor=(0.5, -0.05),
              ncol=len(legend_labels), frameon=False, fontsize=9)


def draw_summary_card(ax, title, stats_data):
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=15, fontweight='bold', color=TEXT_COLOR, pad=15, loc='center')

    y_pos = 0.85
    step = 0.85 / max(len(stats_data), 1)
    for label, value, color in stats_data:
        ax.add_patch(plt.Circle((0.06, y_pos), 0.025, color=color, transform=ax.transAxes))
        ax.text(0.14, y_pos, label, fontsize=11.5, va='center', color=TEXT_COLOR, transform=ax.transAxes)
        ax.text(0.92, y_pos, value, fontsize=13, va='center', ha='right',
                fontweight='bold', color=color, transform=ax.transAxes)
        y_pos -= step


def draw_line_chart(ax, x_labels, values, title, y_labels=("Низкая", "Средняя", "Высокая")):
    add_card_bg(ax)
    ax.plot(range(len(x_labels)), values, color=LINE_COLOR, linewidth=3.5,
            marker='o', markersize=10, markerfacecolor=LINE_FILL,
            markeredgecolor=LINE_COLOR, markeredgewidth=2, zorder=3)
    ax.fill_between(range(len(x_labels)), values, alpha=0.2, color=LINE_COLOR, zorder=1)
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=0, fontsize=9, color=MUTED_COLOR)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0, 0.5, 1])
    ax.set_yticklabels(y_labels, fontsize=9, color=MUTED_COLOR)
    ax.grid(True, alpha=0.4, color=GRID_COLOR, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color(GRID_COLOR)
    ax.set_title(title, fontsize=15, fontweight='bold', color=TEXT_COLOR, pad=15)


def generate_daily_stats(chat_id: str, db) -> Optional[str]:
    responses = db.get_responses_today(chat_id)
    if len(responses) < 3:
        return None

    setup_style()
    fig = plt.figure(figsize=(13, 9))
    fig.patch.set_facecolor(BG_COLOR)
    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.3, left=0.06, right=0.96, top=0.86, bottom=0.06)

    fig.suptitle('Итоги дня', color=TEXT_COLOR, fontsize=24, fontweight='bold', y=0.96)
    fig.text(0.5, 0.905, datetime.now().strftime('%d.%m.%Y'), color=MUTED_COLOR, fontsize=13, ha='center')

    total = len(responses)
    thinking = [r for r in responses if r.get("q1") == "thinking"]
    doing_n = sum(1 for r in responses if r.get("q1") == "doing")
    present_n = sum(1 for r in responses if r.get("q1") == "present")
    thinking_n = len(thinking)

    # Card 1: Где был
    ax1 = fig.add_subplot(gs[0, 0])
    add_card_bg(ax1)
    if total > 0:
        draw_donut(ax1, [thinking_n, doing_n, present_n], STATE_COLORS, "?",
                   "Где ты был", STATE_LABELS_LEGEND)

    # Card 2: Мысли строят жизнь
    ax2 = fig.add_subplot(gs[0, 1])
    add_card_bg(ax2)
    if thinking:
        pos_n = sum(1 for r in thinking if r.get("q2") == "yes")
        rest_n = len(thinking) - pos_n
        draw_donut(ax2, [pos_n, rest_n], CHARGE_COLORS, "+",
                   "Мысли строят жизнь?", CHARGE_LABELS_LEGEND)
    else:
        ax2.text(0.5, 0.5, "Нет данных\nо мыслях", ha='center', va='center',
                color=MUTED_COLOR, fontsize=13, transform=ax2.transAxes)
        ax2.set_title("Мысли строят жизнь?", fontsize=15, fontweight='bold', color=TEXT_COLOR, pad=15)
        ax2.axis('off')

    # Card 3: Осознанность во времени
    ax3 = fig.add_subplot(gs[1, 0])
    if thinking:
        times, scores = [], []
        for r in thinking:
            try:
                dt = datetime.fromisoformat(r["timestamp"])
                times.append(dt.strftime("%H:%M"))
                scores.append(aware_score(r.get("q3", "partial")))
            except:
                pass
        if scores:
            draw_line_chart(ax3, times, scores, "Осознанность в течение дня")
        else:
            ax3.axis('off')
    else:
        ax3.axis('off')

    # Card 4: Сводка
    ax4 = fig.add_subplot(gs[1, 1])
    thinking_pct = int(thinking_n / total * 100) if total else 0
    doing_pct = int(doing_n / total * 100) if total else 0
    present_pct = int(present_n / total * 100) if total else 0
    pos_pct = int(sum(1 for r in thinking if r.get("q2") == "yes") / len(thinking) * 100) if thinking else 0
    aware_pct = int(np.mean([aware_score(r.get("q3", "partial")) for r in thinking]) * 100) if thinking else 0

    stats_data = [
        ("Опросов пройдено", str(total), TEXT_COLOR),
        ("В мыслях", f"{thinking_pct}%", STATE_COLORS[0]),
        ("В деле", f"{doing_pct}%", STATE_COLORS[1]),
        ("В моменте", f"{present_pct}%", STATE_COLORS[2]),
        ("Позитивный заряд", f"{pos_pct}%", CHARGE_COLORS[0]),
        ("Осознанность", f"{aware_pct}%", LINE_COLOR),
    ]
    draw_summary_card(ax4, "Сводка", stats_data)

    path = f"/tmp/stats_daily_{chat_id}.png"
    plt.savefig(path, dpi=150, facecolor=BG_COLOR, bbox_inches='tight')
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
            by_date.setdefault(day, []).append(r)
        except:
            pass

    if len(by_date) < 2:
        return None

    days = sorted(by_date.keys())
    setup_style()
    fig = plt.figure(figsize=(14, 5))
    fig.patch.set_facecolor(BG_COLOR)
    gs = fig.add_gridspec(1, 3, wspace=0.35, left=0.05, right=0.97, top=0.8, bottom=0.15)

    fig.suptitle('Статистика за неделю', color=TEXT_COLOR, fontsize=20, fontweight='bold', y=0.96)

    # Chart 1: позитив по дням
    ax1 = fig.add_subplot(gs[0])
    pos_pct = []
    for d in days:
        thinking = [r for r in by_date[d] if r.get("q1") == "thinking"]
        pct = sum(1 for r in thinking if r.get("q2") == "yes") / len(thinking) if thinking else 0
        pos_pct.append(pct)
    draw_line_chart(ax1, days, pos_pct, "Мысли строят жизнь")

    # Chart 2: осознанность по дням
    ax2 = fig.add_subplot(gs[1])
    aware_pct = []
    for d in days:
        thinking = [r for r in by_date[d] if r.get("q1") == "thinking"]
        pct = np.mean([aware_score(r.get("q3", "partial")) for r in thinking]) if thinking else 0
        aware_pct.append(pct)
    draw_line_chart(ax2, days, aware_pct, "Осознанность")

    # Chart 3: где был - stacked bar
    ax3 = fig.add_subplot(gs[2])
    add_card_bg(ax3)
    thinking_pcts, doing_pcts, present_pcts = [], [], []
    for d in days:
        total = len(by_date[d])
        thinking_pcts.append(sum(1 for r in by_date[d] if r.get("q1") == "thinking") / total)
        doing_pcts.append(sum(1 for r in by_date[d] if r.get("q1") == "doing") / total)
        present_pcts.append(sum(1 for r in by_date[d] if r.get("q1") == "present") / total)

    ax3.bar(days, thinking_pcts, color=STATE_COLORS[0], alpha=0.9, label='В мыслях')
    ax3.bar(days, doing_pcts, bottom=thinking_pcts, color=STATE_COLORS[1], alpha=0.9, label='В деле')
    ax3.bar(days, present_pcts, bottom=[t+d for t,d in zip(thinking_pcts, doing_pcts)],
            color=STATE_COLORS[2], alpha=0.9, label='В моменте')
    ax3.set_ylim(0, 1.1)
    ax3.set_title("Где ты был", fontsize=15, fontweight='bold', color=TEXT_COLOR, pad=15)
    ax3.tick_params(axis='x', colors=MUTED_COLOR)
    ax3.tick_params(axis='y', colors=MUTED_COLOR)
    ax3.legend(fontsize=8, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3)
    for spine in ax3.spines.values():
        spine.set_visible(False)

    path = f"/tmp/stats_weekly_{chat_id}.png"
    plt.savefig(path, dpi=150, facecolor=BG_COLOR, bbox_inches='tight')
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
            by_week.setdefault(week, []).append(r)
        except:
            pass

    if len(by_week) < 2:
        return None

    weeks = sorted(by_week.keys())
    setup_style()
    fig = plt.figure(figsize=(14, 5))
    fig.patch.set_facecolor(BG_COLOR)
    gs = fig.add_gridspec(1, 3, wspace=0.35, left=0.05, right=0.97, top=0.8, bottom=0.15)

    fig.suptitle('Статистика за месяц', color=TEXT_COLOR, fontsize=20, fontweight='bold', y=0.96)

    ax1 = fig.add_subplot(gs[0])
    pos_pct = []
    for w in weeks:
        thinking = [r for r in by_week[w] if r.get("q1") == "thinking"]
        pct = sum(1 for r in thinking if r.get("q2") == "yes") / len(thinking) if thinking else 0
        pos_pct.append(pct)
    draw_line_chart(ax1, weeks, pos_pct, "Мысли строят жизнь")

    ax2 = fig.add_subplot(gs[1])
    aware_pct = []
    for w in weeks:
        thinking = [r for r in by_week[w] if r.get("q1") == "thinking"]
        pct = np.mean([aware_score(r.get("q3", "partial")) for r in thinking]) if thinking else 0
        aware_pct.append(pct)
    draw_line_chart(ax2, weeks, aware_pct, "Осознанность")

    ax3 = fig.add_subplot(gs[2])
    add_card_bg(ax3)
    thinking_pcts, doing_pcts, present_pcts = [], [], []
    for w in weeks:
        total = len(by_week[w])
        thinking_pcts.append(sum(1 for r in by_week[w] if r.get("q1") == "thinking") / total)
        doing_pcts.append(sum(1 for r in by_week[w] if r.get("q1") == "doing") / total)
        present_pcts.append(sum(1 for r in by_week[w] if r.get("q1") == "present") / total)
    ax3.bar(weeks, thinking_pcts, color=STATE_COLORS[0], alpha=0.9, label='В мыслях')
    ax3.bar(weeks, doing_pcts, bottom=thinking_pcts, color=STATE_COLORS[1], alpha=0.9, label='В деле')
    ax3.bar(weeks, present_pcts, bottom=[t+d for t,d in zip(thinking_pcts, doing_pcts)],
            color=STATE_COLORS[2], alpha=0.9, label='В моменте')
    ax3.set_ylim(0, 1.1)
    ax3.set_title("Где ты был", fontsize=15, fontweight='bold', color=TEXT_COLOR, pad=15)
    ax3.tick_params(axis='x', colors=MUTED_COLOR)
    ax3.tick_params(axis='y', colors=MUTED_COLOR)
    ax3.legend(fontsize=8, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3)
    for spine in ax3.spines.values():
        spine.set_visible(False)

    path = f"/tmp/stats_monthly_{chat_id}.png"
    plt.savefig(path, dpi=150, facecolor=BG_COLOR, bbox_inches='tight')
    plt.close()
    return path
