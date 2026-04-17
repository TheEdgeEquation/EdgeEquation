# core/formatting.py

from datetime import datetime

# ---------------------------------------------------------
# Helper: Convert timestamp to YYYY-MM-DD
# ---------------------------------------------------------
def _fmt_date(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts.replace("Z", "")).strftime("%Y-%m-%d")
    except:
        return ts  # fallback if timestamp is already formatted


# ---------------------------------------------------------
# 1. MLB + KBO/NPB INSIGHT FORMATTER (7-BULLET PREMIUM)
# ---------------------------------------------------------
def format_insight_block(label: str, insight: dict) -> str:
    """
    label: 'MLB Insight' or 'KBO/NPB Insight'
    insight dict must contain:
      timestamp, key_metric, context, model_signal,
      trend, matchup_delta, historical_comp, edge_summary
    """

    date_str = _fmt_date(insight.get("timestamp", ""))

    lines = [
        f"📊 {label} — {date_str}",
        "",
        f"• Key Metric: {insight.get('key_metric', 'N/A')}",
        f"• Context: {insight.get('context', 'N/A')}",
        f"• Model Signal: {insight.get('model_signal', 'N/A')}",
        f"• Trend: {insight.get('trend', 'N/A')}",
        f"• Matchup Delta: {insight.get('matchup_delta', 'N/A')}",
        f"• Historical Comparison: {insight.get('historical_comp', 'N/A')}",
        f"• Edge Summary: {insight.get('edge_summary', 'N/A')}",
        "",
        "#AnalyticsNotFeelings",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------
# 2. EDGES FORMATTER (PREMIUM MULTI-TEAM ANALYTICS)
# ---------------------------------------------------------
def format_edges_block(payload: dict) -> str:
    """
    payload structure:
    {
      'timestamp': ...,
      'edges': [
         {
           'team': 'Yankees',
           'confidence': 0.62,
           'key_metric': '31% K-rate vs LHP',
           'context': 'Lineup whiff rate 27%',
           'trend': 'Bullpen +0.18 WPA last 14 days',
           'matchup_delta': '+0.12 expected runs vs SP',
           'historical_comp': 'Similar matchup: +0.09 EV',
           'edge_summary': 'Model favors NYY early'
         },
         ...
      ]
    }
    """

    date_str = _fmt_date(payload.get("timestamp", ""))

    header = f"📈 Edges — {date_str}\n"
    blocks = [header]

    for e in payload.get("edges", []):
        blocks.append(
            f"\n{e.get('team', 'Team')} — {round(e.get('confidence', 0)*100)}%\n"
            f"• Key Metric: {e.get('key_metric', 'N/A')}\n"
            f"• Context: {e.get('context', 'N/A')}\n"
            f"• Trend: {e.get('trend', 'N/A')}\n"
            f"• Matchup Delta: {e.get('matchup_delta', 'N/A')}\n"
            f"• Historical Comparison: {e.get('historical_comp', 'N/A')}\n"
            f"• Edge Summary: {e.get('edge_summary', 'N/A')}\n"
        )

    blocks.append("#AnalyticsNotFeelings")

    return "\n".join(blocks)


# ---------------------------------------------------------
# 3. SPOTLIGHT FORMATTER (PREMIUM CROSS-SPORT HERO POST)
# ---------------------------------------------------------
def format_spotlight_block(payload: dict) -> str:
    """
    payload structure:
    {
      'timestamp': ...,
      'sport': 'NBA',
      'player': 'Luka Doncic',
      'prop': 'Over 8.5 assists',
      'confidence': 0.63,
      'key_metric': ...,
      'context': ...,
      'model_signal': ...,
      'trend': ...,
      'matchup_delta': ...,
      'historical_comp': ...,
      'edge_summary': ...
    }
    """

    date_str = _fmt_date(payload.get("timestamp", ""))

    lines = [
        f"🔦 Spotlight Insight — {date_str}",
        "",
        f"{payload.get('sport', 'Sport')} — {payload.get('player', 'Player')} {payload.get('prop', '')} ({round(payload.get('confidence', 0)*100)}%)",
        "",
        f"• Key Metric: {payload.get('key_metric', 'N/A')}",
        f"• Context: {payload.get('context', 'N/A')}",
        f"• Model Signal: {payload.get('model_signal', 'N/A')}",
        f"• Trend: {payload.get('trend', 'N/A')}",
        f"• Matchup Delta: {payload.get('matchup_delta', 'N/A')}",
        f"• Historical Comparison: {payload.get('historical_comp', 'N/A')}",
        f"• Edge Summary: {payload.get('edge_summary', 'N/A')}",
        "",
        "#AnalyticsNotFeelings",
    ]

    return "\n".join(lines)

# ---------------------------------------------------------
# 4. RESULTS FORMATTER (FULL PREMIUM BREAKDOWN)
# ---------------------------------------------------------
def format_results_block(payload: dict) -> str:
    """
    payload structure:
    {
      'timestamp': ...,
      'results': [
         {
           'label': 'Yankees ML',
           'outcome': 'HIT' or 'MISS',
           'key_metric': ...,
           'context': ...,
           'model_signal': ...,
           'trend': ...,
           'matchup_delta': ...,
           'historical_comp': ...,
           'final_score': '5–2',
         },
         ...
      ],
      'totals': {
         'correct': 8,
         'total': 12,
         'ev_delta': 1.14
      }
    }
    """

    date_str = _fmt_date(payload.get("timestamp", ""))

    lines = [f"📊 Results — {date_str}", ""]

    # Game-by-game breakdown
    for r in payload.get("results", []):
        lines.append(f"{r.get('label', 'Pick')} — {r.get('outcome', 'N/A')}")
        lines.append(f"• Key Metric: {r.get('key_metric', 'N/A')}")
        lines.append(f"• Context: {r.get('context', 'N/A')}")
        lines.append(f"• Model Signal: {r.get('model_signal', 'N/A')}")
        lines.append(f"• Trend: {r.get('trend', 'N/A')}")
        lines.append(f"• Matchup Delta: {r.get('matchup_delta', 'N/A')}")
        lines.append(f"• Historical Comparison: {r.get('historical_comp', 'N/A')}")
        lines.append(f"• Outcome: {r.get('final_score', 'N/A')}")
        lines.append("")

    # Totals
    totals = payload.get("totals", {})
    correct = totals.get("correct", 0)
    total = totals.get("total", 0)
    ev_delta = totals.get("ev_delta", 0)

    lines.append("Totals:")
    lines.append(f"• Correct: {correct} of {total} ({round((correct/total)*100) if total else 0}%)")
    lines.append(f"• EV Delta: {ev_delta:+.2f} units")
    lines.append("")
    lines.append("#AnalyticsNotFeelings")

    return "\n".join(lines)

