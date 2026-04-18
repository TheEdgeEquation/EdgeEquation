def format_smash_block(payload: dict) -> str:
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

    header = f"💥 Smash of the Day — {ts[:10]}\n"

    bullets = [
        f"• **Play:** {team} ML",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}",
        f"• **Edge EV:** {edge_ev:.2f}",
        f"• **Why It Pops:** {reason}",
        f"• **Confidence Signal:** High‑grade model alignment",
    ]

    body = "\n".join(bullets)

    footer = "\n\n#MLB #NBA #NFL #AnalyticsNotFeelings"

    return f"{header}\n{body}{footer}"
