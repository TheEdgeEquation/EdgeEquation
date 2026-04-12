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
        "/usr/share/fonts/truetype/liberati
