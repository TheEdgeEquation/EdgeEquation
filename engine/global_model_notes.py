import logging
from datetime import datetime

logger = logging.getLogger("global_model_notes")

def generate_global_model_notes(kbo, npb, epl, ucl):
    """
    Generates a premium, institutional-style nightly model notes post
    for overseas markets.
    """

    date_str = datetime.now().strftime("%B %-d")

    # -----------------------------
    # SCORING ENVIRONMENT SUMMARY
    # -----------------------------
    def summarize_env(games, label):
        if not games:
            return f"{label}: No games on the board."

        totals = [g.get("model_total") for g in games if g.get("model_total")]
        vegas = [g.get("vegas_total") for g in games if g.get("vegas_total")]

        if not totals or not vegas:
            return f"{label}: Insufficient data."

        avg_model = sum(totals) / len(totals)
        avg_vegas = sum(vegas) / len(vegas)
        drift = round(avg_model - avg_vegas, 2)

        direction = "↑ model leaning over" if drift > 0 else "↓ model leaning under" if drift < 0 else "↔ neutral"

        return f"{label}: Avg model total {avg_model:.1f} vs Vegas {avg_vegas:.1f} ({direction}, drift {drift})."

    kbo_env = summarize_env(kbo, "KBO")
    npb_env = summarize_env(npb, "NPB")
    epl_env = summarize_env(epl, "EPL")
    ucl_env = summarize_env(ucl, "UCL")

    # -----------------------------
    # VOLATILITY SUMMARY
    # -----------------------------
    def summarize_volatility(games, label):
        if not games:
            return f"{label}: No volatility signals."

        diffs = [
            abs(g.get("model_total", 0) - g.get("vegas_total", 0))
            for g in games
            if g.get("model_total") and g.get("vegas_total")
        ]

        if not diffs:
            return f"{label}: No volatility signals."

        avg_diff = sum(diffs) / len(diffs)
        return f"{label}: Avg volatility {avg_diff:.2f} runs/goals."

    kbo_vol = summarize_volatility(kbo, "KBO")
    npb_vol = summarize_volatility(npb, "NPB")
    epl_vol = summarize_volatility(epl, "EPL")
    ucl_vol = summarize_volatility(ucl, "UCL")

    # -----------------------------
    # FINAL CAPTION
    # -----------------------------
    caption = "\n".join([
        f"EDGE EQUATION 3.0 — GLOBAL MODEL NOTES ({date_str})",
        "",
        "Overnight scoring environments:",
        kbo_env,
        npb_env,
        epl_env,
        ucl_env,
        "",
        "Volatility signals:",
        kbo_vol,
        npb_vol,
        epl_vol,
        ucl_vol,
        "",
        "The engine continues to scan:",
        "• scoring environments",
        "• pace + shot volume",
        "• volatility + drift",
        "• weather + park factors",
        "• market inefficiencies",
        "",
        "Overnight slate loading.",
        "#EdgeEquation",
    ])

    return caption
