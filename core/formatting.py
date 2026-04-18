# core/formatting.py
"""
Unified formatting layer for The Edge Equation.

All public-facing text blocks for:
- Premium daily modes (Spotlight, Smash, Outlier, Sharp, POTD, GOTD, FIPOTD)
- Edges mode
- Facts mode
- Results mode (full premium breakdown)

Every formatter:
- Accepts a dict payload
- Returns a single formatted string
- Is mobile-safe and brand-consistent
- Ends with the global tagline: "Facts. Not Feelings."
"""

from typing import List, Dict, Any


TAGLINE = "Facts. Not Feelings."
DEFAULT_HASHTAGS = "#MLB #NBA #NFL #FactsNotFeelings"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _safe_date_from_timestamp(ts: str | None) -> str:
    if not ts:
        return ""
    return ts[:10]


def _join_bullets(lines: List[str]) -> str:
    return "\n".join(lines)


def _append_footer(body: str, extra_hashtags: str | None = None) -> str:
    hashtags = extra_hashtags if extra_hashtags is not None else DEFAULT_HASHTAGS
    footer_lines = [
        "",
        hashtags,
        TAGLINE,
    ]
    return f"{body}\n\n" + "\n".join(footer_lines)


# ---------------------------------------------------------------------------
# Spotlight Mode
# ---------------------------------------------------------------------------

def format_spotlight_block(payload: Dict[str, Any]) -> str:
    """
    Premium Spotlight formatter.
    Uses 7-bullet elite analytics structure.
    """

    player = payload.get("player")
    line = payload.get("line")
    side = payload.get("side", "").upper()
    sport = payload.get("sport")
    market = payload.get("market")
    model_prob = payload.get("model_prob")
    edge_ev = payload.get("edge_ev")
    reason = payload.get("reason")
    ts = payload.get("timestamp")

    header = f"🔦 Spotlight Insight — {_safe_date_from_timestamp(ts)}\n"

    bullets = [
        f"• **Play:** {player} — {side} {line}",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}" if model_prob is not None else "• **Model Probability:** N/A",
        f"• **Edge EV:** {edge_ev:.2f}" if edge_ev is not None else "• **Edge EV:** N/A",
        f"• **Why It Pops:** {reason}",
        f"• **Confidence Signal:** Model-driven, matchup-validated",
    ]

    body = header + _join_bullets(bullets)
    return _append_footer(body)


# ---------------------------------------------------------------------------
# Smash of the Day
# ---------------------------------------------------------------------------

def format_smash_block(payload: Dict[str, Any]) -> str:
    """
    Premium Smash of the Day formatter.
    """

    team = payload.get("team")
    sport = payload.get("sport")
    market = payload.get("market")
    model_prob = payload.get("model_prob")
    edge_ev = payload.get("edge_ev")
    reason = payload.get("reason")
    ts = payload.get("timestamp")

    header = f"💥 Smash of the Day — {_safe_date_from_timestamp(ts)}\n"

    bullets = [
        f"• **Play:** {team} ML",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}" if model_prob is not None else "• **Model Probability:** N/A",
        f"• **Edge EV:** {edge_ev:.2f}" if edge_ev is not None else "• **Edge EV:** N/A",
        f"• **Why It Pops:** {reason}",
        f"• **Confidence Signal:** High-grade model alignment",
    ]

    body = header + _join_bullets(bullets)
    return _append_footer(body)


# ---------------------------------------------------------------------------
# Outlier of the Day
# ---------------------------------------------------------------------------

def format_outlier_block(payload: Dict[str, Any]) -> str:
    """
    Premium Outlier of the Day formatter.
    """

    player = payload.get("player")
    line = payload.get("line")
    side = payload.get("side", "").upper()
    sport = payload.get("sport")
    market = payload.get("market")
    model_prob = payload.get("model_prob")
    edge_ev = payload.get("edge_ev")
    reason = payload.get("reason")
    ts = payload.get("timestamp")

    header = f"📈 Outlier of the Day — {_safe_date_from_timestamp(ts)}\n"

    bullets = [
        f"• **Play:** {player} — {side} {line}",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}" if model_prob is not None else "• **Model Probability:** N/A",
        f"• **Edge EV:** {edge_ev:.2f}" if edge_ev is not None else "• **Edge EV:** N/A",
        f"• **Why It Pops:** {reason}",
        f"• **Mismatch Signal:** Largest model-vs-market gap today",
    ]

    body = header + _join_bullets(bullets)
    return _append_footer(body)


# ---------------------------------------------------------------------------
# Sharp Signal
# ---------------------------------------------------------------------------

def format_sharp_block(payload: Dict[str, Any]) -> str:
    """
    Premium Sharp Signal formatter.
    """

    team = payload.get("team")
    side = payload.get("side")
    sport = payload.get("sport")
    market = payload.get("market")
    model_prob = payload.get("model_prob")
    edge_ev = payload.get("edge_ev")
    reason = payload.get("reason")
    ts = payload.get("timestamp")

    header = f"📊 Sharp Signal — {_safe_date_from_timestamp(ts)}\n"

    bullets = [
        f"• **Play:** {team} {side}",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}" if model_prob is not None else "• **Model Probability:** N/A",
        f"• **Edge EV:** {edge_ev:.2f}" if edge_ev is not None else "• **Edge EV:** N/A",
        f"• **Why It Pops:** {reason}",
        f"• **Alignment Signal:** Model + matchup + movement agree",
    ]

    body = header + _join_bullets(bullets)
    return _append_footer(body)


# ---------------------------------------------------------------------------
# Prop of the Day (POTD)
# ---------------------------------------------------------------------------

def format_potd_block(payload: Dict[str, Any]) -> str:
    """
    Premium Prop of the Day formatter.
    """

    player = payload.get("player")
    line = payload.get("line")
    side = payload.get("side", "").upper()
    sport = payload.get("sport")
    market = payload.get("market")
    model_prob = payload.get("model_prob")
    edge_ev = payload.get("edge_ev")
    reason = payload.get("reason")
    ts = payload.get("timestamp")

    header = f"🎯 Prop of the Day — {_safe_date_from_timestamp(ts)}\n"

    bullets = [
        f"• **Play:** {player} — {side} {line}",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}" if model_prob is not None else "• **Model Probability:** N/A",
        f"• **Edge EV:** {edge_ev:.2f}" if edge_ev is not None else "• **Edge EV:** N/A",
        f"• **Why It Pops:** {reason}",
        f"• **Signal Strength:** High-confidence model projection",
    ]

    body = header + _join_bullets(bullets)
    return _append_footer(body)


# ---------------------------------------------------------------------------
# Game of the Day (GOTD)
# ---------------------------------------------------------------------------

def format_gotd_block(payload: Dict[str, Any]) -> str:
    """
    Premium Game of the Day formatter.
    """

    team = payload.get("team")
    home = payload.get("home_team")
    away = payload.get("away_team")
    sport = payload.get("sport")
    market = payload.get("market")
    model_prob = payload.get("model_prob")
    edge_ev = payload.get("edge_ev")
    reason = payload.get("reason")
    context = payload.get("context")
    ts = payload.get("timestamp")

    header = f"🏆 Game of the Day — {_safe_date_from_timestamp(ts)}\n"

    bullets = [
        f"• **Matchup:** {away} @ {home}",
        f"• **Play:** {team} ML",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}" if model_prob is not None else "• **Model Probability:** N/A",
        f"• **Edge EV:** {edge_ev:.2f}" if edge_ev is not None else "• **Edge EV:** N/A",
        f"• **Matchup Context:** {context}",
        f"• **Why It Pops:** {reason}",
    ]

    body = header + _join_bullets(bullets)
    return _append_footer(body)


# ---------------------------------------------------------------------------
# First Inning Prop of the Day (FIPOTD) - scaffolded
# ---------------------------------------------------------------------------

def format_fipotd_block(payload: Dict[str, Any]) -> str:
    """
    First Inning Prop of the Day formatter.
    MLB-specific, high-engagement mode.
    """

    matchup = payload.get("matchup")  # e.g., "Yankees @ Red Sox"
    market = payload.get("market")    # e.g., "YRFI" or "NRFI"
    side = payload.get("side", "").upper()
    model_prob = payload.get("model_prob")
    edge_ev = payload.get("edge_ev")
    reason = payload.get("reason")
    ts = payload.get("timestamp")

    header = f"⏱️ First Inning Prop of the Day — {_safe_date_from_timestamp(ts)}\n"

    bullets = [
        f"• **Matchup:** {matchup}",
        f"• **Play:** {market} — {side}",
        f"• **Model Probability:** {model_prob:.2f}" if model_prob is not None else "• **Model Probability:** N/A",
        f"• **Edge EV:** {edge_ev:.2f}" if edge_ev is not None else "• **Edge EV:** N/A",
        f"• **Why It Pops:** {reason}",
        f"• **Inning Signal:** Early-game volatility, model-calibrated",
    ]

    body = header + _join_bullets(bullets)
    return _append_footer(body, extra_hashtags="#MLB #NRFI #YRFI #FactsNotFeelings")


# ---------------------------------------------------------------------------
# Edges Mode
# ---------------------------------------------------------------------------

def format_edges_block(payload: Dict[str, Any]) -> str:
    """
    Edges Mode formatter.
    Expects payload with a list of edges under 'edges'.
    Each edge is a dict with keys like:
    - sport, league, market, team/player, line, side, model_prob, edge_ev, reason
    """

    ts = payload.get("timestamp")
    edges: List[Dict[str, Any]] = payload.get("edges", [])

    header = f"📊 Edges Board — {_safe_date_from_timestamp(ts)}\n"

    lines: List[str] = []
    if not edges:
        lines.append("• No qualified edges today based on current model filters.")
    else:
        for idx, edge in enumerate(edges, start=1):
            label = edge.get("label")
            sport = edge.get("sport")
            market = edge.get("market")
            model_prob = edge.get("model_prob")
            edge_ev = edge.get("edge_ev")
            reason = edge.get("reason")

            lines.append(
                f"{idx}) {label} "
                f"(Sport: {sport}, Market: {market}, "
                f"Prob: {model_prob:.2f} EV: {edge_ev:.2f})"
                if model_prob is not None and edge_ev is not None
                else f"{idx}) {label} (Sport: {sport}, Market: {market})"
            )
            if reason:
                lines.append(f"   • Why: {reason}")

    body = header + "\n".join(lines)
    return _append_footer(body)


# ---------------------------------------------------------------------------
# Facts Mode
# ---------------------------------------------------------------------------

def format_facts_block(payload: Dict[str, Any]) -> str:
    """
    Facts Mode formatter.
    Expects payload with a list of 'facts', each a short, sharp data point.
    """

    ts = payload.get("timestamp")
    facts: List[str] = payload.get("facts", [])

    header = f"📚 Facts Mode — {_safe_date_from_timestamp(ts)}\n"

    if not facts:
        lines = ["• No facts loaded for this slate yet."]
    else:
        lines = [f"• {fact}" for fact in facts]

    body = header + "\n".join(lines)
    return _append_footer(body, extra_hashtags="#SportsData #Trends #FactsNotFeelings")


# ---------------------------------------------------------------------------
# Results Mode - Premium Breakdown
# ---------------------------------------------------------------------------

def format_results_block(payload: Dict[str, Any]) -> str:
    """
    Premium Results Mode formatter.

    Expects payload with:
    - 'date': str
    - 'results': List[dict] with:
        - label, sport, market, result ("hit"/"miss"/"push"), model_prob, edge_ev, final_score, ev_delta
    - 'summary': dict with:
        - total_picks, hits, misses, pushes, accuracy, total_ev_delta,
          best_pick_label, worst_pick_label
    """

    date = payload.get("date")
    results: List[Dict[str, Any]] = payload.get("results", [])
    summary: Dict[str, Any] = payload.get("summary", {})

    header = f"📊 Results — {date}\n"

    lines: List[str] = []

    if not results:
        lines.append("• No graded picks for this date.")
    else:
        for idx, r in enumerate(results, start=1):
            label = r.get("label")
            sport = r.get("sport")
            market = r.get("market")
            result = r.get("result")  # "hit", "miss", "push"
            model_prob = r.get("model_prob")
            edge_ev = r.get("edge_ev")
            final_score = r.get("final_score")
            ev_delta = r.get("ev_delta")

            result_tag = {
                "hit": "✅ HIT",
                "miss": "❌ MISS",
                "push": "➖ PUSH",
            }.get(result, "•")

            core_line = (
                f"{idx}) {result_tag} — {label} "
                f"(Sport: {sport}, Market: {market})"
            )
            lines.append(core_line)

            detail_parts = []
            if model_prob is not None:
                detail_parts.append(f"Prob: {model_prob:.2f}")
            if edge_ev is not None:
                detail_parts.append(f"EV: {edge_ev:.2f}")
            if ev_delta is not None:
                detail_parts.append(f"EV Δ: {ev_delta:+.2f}")
            if final_score:
                detail_parts.append(f"Final: {final_score}")

            if detail_parts:
                lines.append("   • " + " | ".join(detail_parts))

    # Summary block
    total_picks = summary.get("total_picks")
    hits = summary.get("hits")
    misses = summary.get("misses")
    pushes = summary.get("pushes")
    accuracy = summary.get("accuracy")
    total_ev_delta = summary.get("total_ev_delta")
    best_pick_label = summary.get("best_pick_label")
    worst_pick_label = summary.get("worst_pick_label")

    lines.append("")
    lines.append("Summary:")
    if total_picks is not None:
        lines.append(f"• Volume: {total_picks} picks "
                     f"({hits}–{misses}" +
                     (f"–{pushes}" if pushes is not None else "") +
                     ")")
    if accuracy is not None:
        lines.append(f"• Accuracy: {accuracy:.1f}%")
    if total_ev_delta is not None:
        lines.append(f"• EV Delta: {total_ev_delta:+.2f} units")
    if best_pick_label:
        lines.append(f"• Best Edge: {best_pick_label}")
    if worst_pick_label:
        lines.append(f"• Toughest Beat: {worst_pick_label}")

    body = header + "\n".join(lines)
    return _append_footer(body, extra_hashtags="#Results #EV #FactsNotFeelings")


# ---------------------------------------------------------------------------
# Results Summary (short form)
# ---------------------------------------------------------------------------

def format_results_summary_block(payload: Dict[str, Any]) -> str:
    """
    Short-form results summary formatter.
    Ideal for quick recap posts or pinned summaries.
    """

    date = payload.get("date")
    summary: Dict[str, Any] = payload.get("summary", {})

    total_picks = summary.get("total_picks")
    hits = summary.get("hits")
    misses = summary.get("misses")
    pushes = summary.get("pushes")
    accuracy = summary.get("accuracy")
    total_ev_delta = summary.get("total_ev_delta")

    header = f"📌 Daily Recap — {date}\n"

    lines: List[str] = []

    if total_picks is None:
        lines.append("• No graded picks for this slate.")
    else:
        lines.append(
            f"• Record: {hits}–{misses}" +
            (f"–{pushes}" if pushes is not None else "") +
            f" over {total_picks} picks"
        )
        if accuracy is not None:
            lines.append(f"• Accuracy: {accuracy:.1f}%")
        if total_ev_delta is not None:
            lines.append(f"• EV Delta: {total_ev_delta:+.2f} units")

    body = header + "\n".join(lines)
    return _append_footer(body, extra_hashtags="#Results #Recap #FactsNotFeelings")
