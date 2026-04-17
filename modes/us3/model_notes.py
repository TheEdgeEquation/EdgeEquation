import logging
from engine.stats_tracker import build_weekly_stats, build_all_time_stats

logger = logging.getLogger(__name__)

def run_model_notes():
    logger.info("MODE: model_notes")

    weekly = build_weekly_stats(style="ee")
    all_time = build_all_time_stats(style="ee")

    caption = "\n".join([
        "EDGE EQUATION 3.0 — MODEL NOTES",
        "",
        f"Weekly volume: {weekly.get('total', 0)} graded outputs",
        f"All-time volume: {all_time.get('total', 0)} graded outputs",
        "",
        "Model continues to scan:",
        "• Scoring environments",
        "• Pace and shot volume",
        "• Volatility and late-game drift",
        "",
        "Always learning. Always refining.",
        "#EdgeEquation",
    ])

    logger.info(caption)
