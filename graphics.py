# graphics.py

import os
from typing import List
from PIL import Image, ImageDraw, ImageFont  # pillow

from config import OUTPUT_DIR, OUTPUT_IMAGE_NAME, BRAND_NAME, TAGLINE, today_stamp
from picks import Pick
from facts import get_core_facts

WIDTH = 1600
HEIGHT = 900
BG_COLOR = (6, 10, 24)
CARD_COLOR = (18, 24, 48)
TEXT_COLOR = (240, 240, 240)
ACCENT_COLOR = (0, 186, 255)

def _ensure_output_dir() -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, OUTPUT_IMAGE_NAME)

def render_daily_card(picks: List[Pick]) -> str:
    path = _ensure_output_dir()
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Fonts – you can swap these for your preferred ones
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

    # Header
    draw.text((60, 40), f"{BRAND_NAME}", font=title_font, fill=TEXT_COLOR)
    draw.text((60, 80), TAGLINE, font=body_font, fill=ACCENT_COLOR)
    draw.text((WIDTH - 300, 40), today_stamp(), font=body_font, fill=TEXT_COLOR)

    # Picks section
    y = 160
    for pick in picks:
        block = f"{pick.label}: {pick.matchup}"
        if pick.player:
            block += f" — {pick.player}"
        block += f" ({pick.line})"
        if pick.note:
            block += f" | {pick.note}"
        draw.text((80, y), block, font=body_font, fill=TEXT_COLOR)
        y += 40

    # Facts strip
    facts = get_core_facts()[:3]
    fy = HEIGHT - 140
    draw.text((60, fy), "Core Facts:", font=body_font, fill=ACCENT_COLOR)
    fy += 30
    for fact in facts:
        draw.text((80, fy), f"• {fact}", font=body_font, fill=TEXT_COLOR)
        fy += 24

    img.save(path, format="PNG")
    return path
