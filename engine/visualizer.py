import os
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config.settings import (
    GRAPHIC_WIDTH, GRAPHIC_HEIGHT, OUTPUT_DIR,
    EE_TAGLINE, CBC_TAGLINE, ALGO_VERSION,
)

logger = logging.getLogger(__name__)

EE_COLORS = {
    "bg": (18, 28, 22), "bg2": (26, 40, 32), "grid": (35, 55, 42),
    "accent": (52, 168, 100), "text_primary": (230, 240, 232),
    "text_muted": (140, 170, 150), "grade_ap": (255, 215, 0),
    "grade_a": (52, 168, 100), "grade_am": (100, 200, 160),
    "border": (60, 90, 70), "score_bg": (36, 56, 44),
}

CBC_COLORS = {
    "bg": (20, 14, 8), "bg2": (35, 22, 12), "grid": (50, 35, 20),
    "accent": (255, 165, 0), "text_primary": (255, 240, 210),
    "text_muted": (180, 140, 90), "grade_ap": (255, 215, 0),
    "grade_a": (255, 165, 0), "grade_am": (200, 130, 60),
    "border": (80, 50, 25), "score_bg": (45, 28, 14),
}


def _get_colors(style: str) -> dict:
    return CBC_COLORS if style == "cbc" else EE_COLORS


def _load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_grid(draw, w, h, colors):
    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=colors["grid"], width=1)
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=colors["grid"], width=1)


def _draw_watermark(draw, w, h, colors):
    font = _load_font(13)
    snippets = ["P(X>k) = Σ e^-λ·λ^x/x!", "λ = E[X]", "EV = p·b - (1-p)",
                "n=10,000", "P(Over) = sim/n", "edge = p_sim - p_imp"]
    positions = [(30, 60), (200, 120), (500, 80), (800, 50), (100, 500), (400, 560)]
    for i, (x, y) in enumerate(positions):
        draw.text((x, y), snippets[i % len(snippets)], fill=colors["grid"], font=font)


def _grade_color(grade, colors):
    return {"A+": colors["grade_ap"], "A": colors["grade_a"], "A-": colors["grade_am"]}.get(grade, colors["text_primary"])


def _draw_header(draw, w, colors, style, date_str):
    title = "CASH BEFORE COFFEE" if style == "cbc" else "THE EDGE EQUATION"
    subtitle = "Powered by The Edge Equation" if style == "cbc" else f"{ALGO_VERSION}  ·  {date_str}"
    draw.rectangle([0, 0, w, 4], fill=colors["accent"])
    draw.text((w // 2, 28), title, fill=colors["accent"], font=_load_font(36, bold=True), anchor="mt")
    draw.text((w // 2, 72), subtitle, fill=colors["text_muted"], font=_load_font(14), anchor="mt")
    draw.line([(40, 96), (w - 40, 96)], fill=colors["border"], width=1)
    return 108


def _draw_footer(draw, w, h, colors, style, plays):
    now = datetime.now()
    draw.rectangle([0, h - 58, w, h], fill=colors["bg2"])
    draw.line([(0, h - 58), (w, h - 58)], fill=colors["border"], width=1)
    stats = f"Run: {now.strftime('%I:%M %p CDT')}  ·  Plays: {len(plays)}  ·  Sims: 10,000"
    draw.text((w // 2, h - 46), stats, fill=colors["text_muted"], font=_load_font(12), anchor="mt")
    tagline = CBC_TAGLINE if style == "cbc" else EE_TAGLINE
    draw.text((w // 2, h - 24), tagline, fill=colors["accent"], font=_load_font(13, bold=True), anchor="mt")


def _draw_play_card(draw, play, x, y, w, colors):
    h_card = 130
    pad = 14
    draw.rounded_rectangle([x, y, x + w, y + h_card], radius=8, fill=colors["bg2"], outline=colors["border"], width=1)
    grade = play["grade"]
    gc = _grade_color(grade, colors)
    draw.rounded_rectangle([x + pad, y + pad, x + pad + 56, y + pad + 32], radius=5, fill=gc)
    draw.text((x + pad + 28, y + pad + 6), grade, fill=(10, 10, 10), font=_load_font(15, bold=True), anchor="mt")
    score_x = x + pad + 66
    draw.rounded_rectangle([score_x, y + pad, score_x + 42, y + pad + 32], radius=5, fill=colors["score_bg"], outline=colors["border"], width=1)
    draw.text((score_x + 21, y + pad + 6), str(play["confidence_score"]), fill=colors["accent"], font=_load_font(13, bold=True), anchor="mt")
    draw.text((x + pad, y + pad + 40), play["player"], fill=colors["text_primary"], font=_load_font(17, bold=True))
    draw.text((x + pad, y + pad + 62), f"{play['display_line']} {play['prop_label']}  {play['display_odds']}  ·  {play['sport_label']}", fill=colors["text_muted"], font=_load_font(14))
    draw.text((x + pad, y + pad + 84), f"{play['team']} vs {play['opponent']}", fill=colors["text_muted"], font=_load_font(14))
    draw.text((x + w - pad, y + pad + 40), f"+{play['edge']*100:.1f}% edge", fill=gc, font=_load_font(13), anchor="ra")
    draw.text((x + w - pad, y + pad + 60), f"sim: {play['sim_prob']*100:.1f}%", fill=colors["text_muted"], font=_load_font(13), anchor="ra")
    draw.text((x + w - pad, y + pad + 82), "1u", fill=colors["accent"], font=_load_font(13, bold=True), anchor="ra")
    return h_card + 10


def generate_main_graphic(plays: list[dict], style: str = "ee") -> str | None:
    if not plays:
        return None
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    colors = _get_colors(style)
    date_str = datetime.now().strftime("%B %d, %Y")
    img = Image.new("RGB", (GRAPHIC_WIDTH, GRAPHIC_HEIGHT), colors["bg"])
    draw = ImageDraw.Draw(img)
    _draw_grid(draw, GRAPHIC_WIDTH, GRAPHIC_HEIGHT, colors)
    _draw_watermark(draw, GRAPHIC_WIDTH, GRAPHIC_HEIGHT, colors)
    y = _draw_header(draw, GRAPHIC_WIDTH, colors, style, date_str)
    col_w = (GRAPHIC_WIDTH - 80) // 2
    col1_x, col2_x = 30, 30 + col_w + 20
    y1, y2 = y + 10, y + 10
    current_col = 0
    last_grade = None
    for play in plays:
        grade = play["grade"]
        col_x = col1_x if current_col == 0 else col2_x
        col_y = y1 if current_col == 0 else y2
        if grade != last_grade:
            gc = _grade_color(grade, colors)
            draw.rectangle([col_x, col_y, col_x + col_w, col_y + 26], fill=colors["score_bg"])
            draw.line([(col_x, col_y), (col_x, col_y + 26)], fill=gc, width=3)
            draw.text((col_x + 14, col_y + 5), f"  {grade} TIER  -  {play['play_label'].upper()}", fill=gc, font=_load_font(14, bold=True))
            if current_col == 0:
                y1 += 32
            else:
                y2 += 32
            col_y = y1 if current_col == 0 else y2
            last_grade = grade
        consumed = _draw_play_card(draw, play, col_x, col_y, col_w, colors)
        if current_col == 0:
            y1 += consumed
        else:
            y2 += consumed
        if current_col == 0 and y1 > GRAPHIC_HEIGHT - 120:
            current_col = 1
        elif current_col == 1 and y2 > GRAPHIC_HEIGHT - 120:
            break
    _draw_footer(draw, GRAPHIC_WIDTH, GRAPHIC_HEIGHT, colors, style, plays)
    fname = f"{style}_daily_{datetime.now().strftime('%Y%m%d')}.png"
    fpath = os.path.join(OUTPUT_DIR, fname)
    img.save(fpath, "PNG", optimize=True)
    logger.info(f"Graphic saved: {fpath}")
    return fpath


def generate_announce_graphic(games_today: list[dict], style: str = "ee") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    colors = _get_colors(style)
    w, h = GRAPHIC_WIDTH, 400
    img = Image.new("RGB", (w, h), colors["bg"])
    draw = ImageDraw.Draw(img)
    _draw_grid(draw, w, h, colors)
    draw.rectangle([0, 0, w, 4], fill=colors["accent"])
    draw.text((w // 2, 24), "GAMES WE'RE SCANNING TODAY", fill=colors["accent"], font=_load_font(28, bold=True), anchor="mt")
    draw.text((w // 2, 62), datetime.now().strftime("%B %d, %Y"), fill=colors["text_muted"], font=_load_font(14), anchor="mt")
    draw.line([(40, 86), (w - 40, 86)], fill=colors["border"], width=1)
    y = 100
    for game in games_today[:8]:
        draw.text((w // 2, y), f"{game.get('sport_label',''):<6}  {game.get('away','')} @ {game.get('home','')}  ·  {game.get('time','')}", fill=colors["text_primary"], font=_load_font(15), anchor="mt")
        y += 30
    draw.text((w // 2, y + 14), "Scanning: Pitcher K's · Player 3's · Shots on Goal · Receptions", fill=colors["text_muted"], font=_load_font(14), anchor="mt")
    draw.rectangle([0, h - 36, w, h], fill=colors["bg2"])
    draw.text((w // 2, h - 24), EE_TAGLINE, fill=colors["accent"], font=_load_font(12, bold=True), anchor="mt")
    fpath = os.path.join(OUTPUT_DIR, f"{style}_announce_{datetime.now().strftime('%Y%m%d')}.png")
    img.save(fpath, "PNG")
    return fpath


def generate_results_graphic(results: list[dict], style: str = "ee") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    colors = _get_colors(style)
    hits = sum(1 for r in results if r.get("hit"))
    total = len(results)
    w, h = GRAPHIC_WIDTH, 500
    img = Image.new("RGB", (w, h), colors["bg"])
    draw = ImageDraw.Draw(img)
    _draw_grid(draw, w, h, colors)
    draw.rectangle([0, 0, w, 4], fill=colors["accent"])
    draw.text((w // 2, 24), "RESULTS" if style == "ee" else "OVERNIGHT RESULTS", fill=colors["accent"], font=_load_font(28, bold=True), anchor="mt")
    draw.text((w // 2, 62), datetime.now().strftime("%B %d, %Y"), fill=colors["text_muted"], font=_load_font(14), anchor="mt")
    draw.line([(40, 86), (w - 40, 86)], fill=colors["border"], width=1)
    record_color = colors["grade_ap"] if hits == total else (colors["grade_a"] if hits > total // 2 else (200, 80, 80))
    draw.text((w // 2, 110), f"{hits}/{total}", fill=record_color, font=_load_font(52, bold=True), anchor="mt")
    y = 185
    for r in results:
        hit = r.get("hit", False)
        draw.text((w // 2 - 20, y), "✓" if hit else "✗", fill=(80, 200, 120) if hit else (200, 80, 80), font=_load_font(16, bold=True), anchor="rt")
        draw.text((w // 2 - 10, y), f"{r['player']}  {r['display_line']} {r['prop_label']}  {r['display_odds']}", fill=colors["text_primary"], font=_load_font(14))
        y += 28
    draw.rectangle([0, h - 40, w, h], fill=colors["bg2"])
    draw.text((w // 2, h - 26), CBC_TAGLINE if style == "cbc" else EE_TAGLINE, fill=colors["accent"], font=_load_font(13, bold=True), anchor="mt")
    fpath = os.path.join(OUTPUT_DIR, f"{style}_results_{datetime.now().strftime('%Y%m%d')}.png")
    img.save(fpath, "PNG")
    return fpath


def generate_weekly_graphic(stats: dict) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    colors = EE_COLORS
    w, h = GRAPHIC_WIDTH, 520
    img = Image.new("RGB", (w, h), colors["bg"])
    draw = ImageDraw.Draw(img)
    _draw_grid(draw, w, h, colors)
    draw.rectangle([0, 0, w, 4], fill=colors["accent"])
    draw.text((w // 2, 22), "WEEKLY ROUNDUP", fill=colors["accent"], font=_load_font(30, bold=True), anchor="mt")
    draw.text((w // 2, 62), stats.get("week_label", ""), fill=colors["text_muted"], font=_load_font(14), anchor="mt")
    draw.line([(40, 86), (w - 40, 86)], fill=colors["border"], width=1)
    stat_items = [("WIN RATE", f"{stats.get('win_rate', 0):.1f}%"), ("RECORD", f"{stats.get('hits', 0)}-{stats.get('misses', 0)}"), ("UNITS", f"+{stats.get('units', 0):.1f}u"), ("PLAYS", str(stats.get('total', 0)))]
    block_w = (w - 80) // 4
    for i, (label, val) in enumerate(stat_items):
        bx = 40 + i * (block_w + 6)
        draw.rounded_rectangle([bx, 106, bx + block_w, 200], radius=6, fill=colors["bg2"], outline=colors["border"], width=1)
        draw.text((bx + block_w // 2, 120), label, fill=colors["text_muted"], font=_load_font(13), anchor="mt")
        draw.text((bx + block_w // 2, 148), val, fill=colors["accent"], font=_load_font(36, bold=True), anchor="mt")
    if stats.get("best_play"):
        draw.text((w // 2, 220), f"Best: {stats['best_play']}", fill=colors["grade_ap"], font=_load_font(14), anchor="mt")
    if stats.get("worst_play"):
        draw.text((w // 2, 244), f"Toughest: {stats['worst_play']}", fill=colors["text_muted"], font=_load_font(14), anchor="mt")
    draw.rectangle([0, h - 40, w, h], fill=colors["bg2"])
    draw.text((w // 2, h - 26), EE_TAGLINE, fill=colors["accent"], font=_load_font(13, bold=True), anchor="mt")
    fpath = os.path.join(OUTPUT_DIR, f"ee_weekly_{datetime.now().strftime('%Y%m%d')}.png")
    img.save(fpath, "PNG")
    return fpath


def generate_cbc_tease_graphic() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    colors = CBC_COLORS
    w, h = GRAPHIC_WIDTH, 340
    img = Image.new("RGB", (w, h), colors["bg"])
    draw = ImageDraw.Draw(img)
    _draw_grid(draw, w, h, colors)
    draw.rectangle([0, 0, w, 4], fill=colors["accent"])
    draw.text((w // 2, 40), "CASH BEFORE COFFEE", fill=colors["accent"], font=_load_font(42, bold=True), anchor="mt")
    draw.text((w // 2, 100), "drops at 10:30 PM tonight", fill=colors["text_primary"], font=_load_font(20), anchor="mt")
    draw.text((w // 2, 140), "Best overnight parlay + PrizePicks slip incoming.", fill=colors["text_muted"], font=_load_font(15), anchor="mt")
    draw.text((w // 2, 170), "The algo already ran. You just have to stay up.", fill=colors["text_muted"], font=_load_font(15), anchor="mt")
    draw.line([(w // 2 - 200, 210), (w // 2 + 200, 210)], fill=colors["border"], width=1)
    draw.text((w // 2, 226), "Powered by The Edge Equation  ·  10,000 sims per play", fill=colors["text_muted"], font=_load_font(13), anchor="mt")
    draw.rectangle([0, h - 40, w, h], fill=colors["bg2"])
    draw.text((w // 2, h - 26), CBC_TAGLINE, fill=colors["accent"], font=_load_font(13, bold=True), anchor="mt")
    fpath = os.path.join(OUTPUT_DIR, f"cbc_tease_{datetime.now().strftime('%Y%m%d')}.png")
    img.save(fpath, "PNG")
    return fpath
