"""
engine/visualizer.py
Generates all graphic types for both brands using Pillow.
Styles: 'ee' (Edge Equation chalkboard) and 'cbc' (Cash Before Coffee fun).
"""
import os
import io
import logging
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config.settings import (
    GRAPHIC_WIDTH, GRAPHIC_HEIGHT, OUTPUT_DIR,
    EE_TAGLINE, CBC_TAGLINE, ALGO_VERSION,
)

logger = logging.getLogger(__name__)

EE_COLORS = {
    "bg":          (18, 28, 22),
    "bg2":         (26, 40, 32),
    "grid":        (35, 55, 42),
    "accent":      (52, 168, 100),
    "text_primary":(230, 240, 232),
    "text_muted":  (140, 170, 150),
    "grade_ap":    (255, 215, 0),
    "grade_a":     (52, 168, 100),
    "grade_am":    (100, 200, 160),
    "border":      (60, 90, 70),
    "score_bg":    (36, 56, 44),
