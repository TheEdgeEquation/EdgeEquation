def format_sharp_block(payload: dict) -> str:
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

    header = f"📊 Sharp Signal — {ts[:10]}\n"

    bullets = [
        f"• **Play:** {team} {side}",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}",
        f"• **Edge EV:** {edge_ev:.2f}",
        f"• **Why It Pops:** {reason}",
        f"• **Alignment Signal:** Model + matchup + movement agree",
    ]

    body = "\n".join(bullets)

    footer = "\n\n#MLB #NBA #NFL #AnalyticsNotFeelings"

    return f"{header}\n{body}{footer}"
