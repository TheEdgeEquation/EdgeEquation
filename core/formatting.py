def format_outlier_block(payload: dict) -> str:
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

    header = f"📈 Outlier of the Day — {ts[:10]}\n"

    bullets = [
        f"• **Play:** {player} — {side} {line}",
        f"• **Sport:** {sport}",
        f"• **Market:** {market}",
        f"• **Model Probability:** {model_prob:.2f}",
        f"• **Edge EV:** {edge_ev:.2f}",
        f"• **Why It Pops:** {reason}",
        f"• **Mismatch Signal:** Largest model‑vs‑market gap today",
    ]

    body = "\n".join(bullets)

    footer = "\n\n#NBA #MLB #NFL #AnalyticsNotFeelings"

    return f"{header}\n{body}{footer}"
