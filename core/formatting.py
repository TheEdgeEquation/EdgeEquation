def format_spotlight_block(payload: dict) -> str:
    """
    Premium Spotlight formatter.
    Uses the 7‑bullet elite analytics structure.
    Compatible with results engine + WAL schema.
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

    header = f"🔦 Spotlight Insight — {ts[:10]}\n"

    bullets = [
        f"• **Play:** {player} — {side} {line}",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}",
        f"• **Edge EV:** {edge_ev:.2f}",
        f"• **Why It Pops:** {reason}",
        f"• **Confidence Signal:** Model‑driven, matchup‑validated",
    ]

    body = "\n".join(bullets)

    footer = "\n\n#MLB #NBA #NFL #AnalyticsNotFeelings"

    return f"{header}\n{body}{footer}"
