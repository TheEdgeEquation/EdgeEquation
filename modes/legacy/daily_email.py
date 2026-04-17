import logging
from engine.email_sender import send_email
from engine.email_builder import build_daily_brief
from engine.accuracy_engine import compute_full_accuracy
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props
from engine.utils import game_has_started
from engine.stats_tracker import build_all_time_stats
from engine.personal_engine import (
    build_personal_parlay,
    build_personal_prizepicks_card,
)
from engine.data_tracker import get_bankroll_summary

logger = logging.getLogger(__name__)

def _fetch_props():
    props = fetch_prizepicks_props() or []
    return props

def _load_all_today_plays():
    props = _fetch_props()
    graded = grade_all_props(props) if props else []
    nrfi = calculate_nrfi_plays() or []
    return graded + nrfi

def _sort_by_edge(plays):
    return sorted(plays, key=lambda x: -x.get("edge", 0))

def _filter_props(plays):
    return [p for p in plays if p.get("prop_label") not in ("NRFI", "YRFI")]

def run_daily_email():
    logger.info("MODE: daily_email")

    # ---------------------------------------------------------
    # ACCURACY
    # ---------------------------------------------------------
    internal_acc, public_acc = compute_full_accuracy()

    engine_accuracy_text = (
        f"MLB Games: {internal_acc['mlb_games'][0]}-{internal_acc['mlb_games'][1]}\n"
        f"Pitchers (K Props): {internal_acc['pitchers'][0]}-{internal_acc['pitchers'][1]}\n"
        f"NRFI/YRFI: {internal_acc['nrfi'][0]}-{internal_acc['nrfi'][1]}\n"
        f"Global: {internal_acc['global']}\n"
    )

    def _fmt(cat):
        h, m = public_acc.get(cat, (0, 0))
        total = h + m
        pct = (h / total * 100) if total > 0 else 0
        return f"{h}-{m} ({pct:.1f}%)"

    public_accuracy_text = "\n".join([
        f"GOTD: {_fmt('GOTD')}",
        f"POTD: {_fmt('POTD')}",
        f"First Inning POTD: {_fmt('FIRST_INNING_POTD')}",
        f"NRFI/YRFI: {_fmt('NRFI')}",
        f"HR Props: {_fmt('HR')}",
        f"Smash: {_fmt('SMASH')}",
        f"Outlier: {_fmt('OUTLIER')}",
        f"Sharp Signal: {_fmt('SHARP_SIGNAL')}",
    ])

    # ---------------------------------------------------------
    # NRFI/YRFI + PERSONALIZATION
    # ---------------------------------------------------------
    nrfi_plays = calculate_nrfi_plays() or []

    personal_parlay = build_personal_parlay()
    personal_pp = build_personal_prizepicks_card()
    bankroll = get_bankroll_summary()
    all_time = build_all_time_stats(style="ee")

    # ---------------------------------------------------------
    # GRAPHIC PROMPT
    # ---------------------------------------------------------
    first_inning_lines = []
    for p in nrfi_plays:
        label = p.get("prop_label")
        book = p.get("book", "PrizePicks")
        team = p.get("team") or p.get("game_id", "Unknown game")
        edge = p.get("edge", 0)
        first_inning_lines.append(
            f"{label} | {team} | {book} | edge={edge:.3f}"
        )

    graphic_picks_text = "\n".join(first_inning_lines)

    graphic_prompt_text = "\n".join([
        "EDGE EQUATION — DAILY",
        "",
        "Sections:",
        "• First Inning Plays (NRFI/YRFI)",
        "• Long Ball Alerts (HR props)",
        "• The Outlier",
        "• Smash of the Day",
        "• Sharp Signal",
        "",
        "Use the picks listed below to populate each section.",
    ])

    # ---------------------------------------------------------
    # PERSONAL TOP 10
    # ---------------------------------------------------------
    all_plays = _sort_by_edge(_load_all_today_plays())
    personal_top10 = all_plays[:10]

    def _grade(edge):
        if edge >= 0.12: return "A"
        if edge >= 0.08: return "B"
        if edge >= 0.05: return "C"
        if edge >= 0.02: return "D"
        return "F"

    personal_top10_text = "\n".join([
        f"{i}. {(p.get('description') or p.get('prop_label'))} — edge={p.get('edge',0):.3f} — Grade {_grade(p.get('edge',0))}"
        for i, p in enumerate(personal_top10, start=1)
    ])

    # ---------------------------------------------------------
    # PROP TOP 10
    # ---------------------------------------------------------
    prop_plays = _filter_props(all_plays)
    top10_props = prop_plays[:10]

    prop_top10_text = "\n".join([
        f"{i}. {(p.get('description') or p.get('prop_label'))} — edge={p.get('edge',0):.3f} — Grade {_grade(p.get('edge',0))}"
        for i, p in enumerate(top10_props, start=1)
    ])

    # ---------------------------------------------------------
    # PUBLIC CARD
    # ---------------------------------------------------------
    public_card_text = "\n".join([
        f"{(p.get('description') or p.get('prop_label'))} — edge={p.get('edge',0):.3f}"
        for p in personal_top10
    ])

    # ---------------------------------------------------------
    # BUILD EMAIL
    # ---------------------------------------------------------
    body = build_daily_brief(
        graphic_prompt_text=graphic_prompt_text,
        graphic_picks_text=graphic_picks_text,
        engine_accuracy_text=engine_accuracy_text,
        public_accuracy_text=public_accuracy_text,
        personal_parlay_text=str(personal_parlay),
        personal_top10_text=personal_top10_text,
        prop_top10_text=prop_top10_text,
        public_card_text=public_card_text,
    )

    send_email(
        subject="Edge Equation — Daily Intelligence Brief",
        body=body,
    )

    logger.info("Daily intelligence brief email sent")
