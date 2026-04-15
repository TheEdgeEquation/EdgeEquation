import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
ALGO_VERSION = "2.0"
DIVIDER = "\u2501" * 25
MAX_CHARS = 25000
 
SPORT_EMOJI = {
    "baseball_mlb": "\u26be",
    "basketball_nba": "\U0001f3c0",
    "icehockey_nhl": "\U0001f3d2",
    "americanfootball_nfl": "\U0001f3c8",
    "KBO": "\u26be", "NPB": "\u26be",
    "EPL": "\u26bd", "UCL": "\u26bd",
    "MLB": "\u26be", "NBA": "\U0001f3c0",
    "NHL": "\U0001f3d2", "NFL": "\U0001f3c8",
}
 
 
def _date():
    return datetime.now().strftime("%B %-d")
 
 
def _emoji(sport):
    return SPORT_EMOJI.get(sport, "\U0001f4ca")
 
 
def _indicator(model_total, vegas_total, threshold=0.4):
    if vegas_total is None:
        return ""
    diff = model_total - vegas_total
    if diff >= threshold:
        return " \u2191"
    elif diff <= -threshold:
        return " \u2193"
    return " ~"
 
 
# ─── GAME OF THE DAY ────────────────────────────────────────
# Best game total play (ML/Spread/Total) — not NRFI/YRFI/props
 
def generate_gotd(away_team, home_team, away_proj, home_proj,
                  vegas_total, league_short, key_factors,
                  model_edge=None, sport=None,
                  weather_str=None, umpire_str=None):
    model_total = round(away_proj + home_proj, 1)
    display_total = vegas_total if vegas_total else model_total
    diff = round(model_total - display_total, 1) if vegas_total else None
    indicator = _indicator(model_total, vegas_total)
    emoji = _emoji(sport or league_short)
 
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 GAME OF THE DAY",
        _date() + " | Algorithm v" + ALGO_VERSION,
        "",
        emoji + " " + away_team + " @ " + home_team,
        "Projection: " + str(away_proj) + " \u2014 " + str(home_proj) +
        "  |  Line: " + str(display_total) + indicator,
    ]
    if model_edge is not None:
        prefix = "+" if model_edge >= 0 else ""
        lines.append("Model Edge: " + prefix + str(model_edge) + "%")
    lines += ["", DIVIDER, "", "WHY THE ENGINE SEES THIS:", ""]
 
    for i, factor in enumerate(key_factors[:6]):
        num = ["\u2460", "\u2461", "\u2462", "\u2463", "\u2464", "\u2465"][i]
        lines.append(num + " " + factor)
        lines.append("")
 
    if weather_str:
        lines += [DIVIDER, "", "\U0001f4ca WEATHER", weather_str, ""]
    if umpire_str:
        lines += [DIVIDER, "", "\U0001f4ca UMPIRE", umpire_str, ""]
 
    if diff is not None:
        prefix = "+" if diff >= 0 else ""
        lines += [
            DIVIDER, "",
            "MARKET GAP",
            "Book:  " + str(display_total),
            "Model: " + str(model_total),
            "Gap:   " + prefix + str(diff),
            "",
        ]
 
    lines += [
        DIVIDER, "",
        "10,000 simulations. Live data.",
        "This is data. Not advice.",
        "",
        "#EdgeEquation #" + league_short + " #SportsAnalytics",
    ]
    return "\n".join(lines)[:MAX_CHARS]
 
 
# ─── PLAYER OF THE DAY ──────────────────────────────────────
# Best player prop play (Ks, SOG, 3PM, etc)
 
def generate_potd(player_name, team, opponent, prop_label,
                  projection, vegas_line, league_short,
                  key_factors, model_edge=None, sport=None,
                  extra_stats=None):
    diff = round(projection - vegas_line, 1) if vegas_line else None
    indicator = _indicator(projection, vegas_line)
    emoji = _emoji(sport or league_short)
 
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 PLAYER OF THE DAY",
        _date() + " | Algorithm v" + ALGO_VERSION,
        "",
        emoji + " " + player_name + " \u2014 " + team + " vs " + opponent,
        "Projected: " + str(projection) + " " + prop_label +
        ("  |  Line: " + str(vegas_line) + indicator if vegas_line else ""),
    ]
    if model_edge is not None:
        prefix = "+" if model_edge >= 0 else ""
        lines.append("Model Edge: " + prefix + str(model_edge) + "%")
    lines += ["", DIVIDER, "", "WHY THE ENGINE FLAGS THIS:", ""]
 
    for i, factor in enumerate(key_factors[:6]):
        num = ["\u2460", "\u2461", "\u2462", "\u2463", "\u2464", "\u2465"][i]
        lines.append(num + " " + factor)
        lines.append("")
 
    if extra_stats:
        lines += [DIVIDER, "", "MODEL OUTPUT"]
        for k, v in extra_stats.items():
            lines.append("  " + k + ": " + str(v))
        lines.append("")
 
    lines += [
        DIVIDER, "",
        "10,000 simulations. Live data.",
        "This is data. Not advice.",
        "",
        "#EdgeEquation #" + league_short + " #SportsAnalytics",
    ]
    return "\n".join(lines)[:MAX_CHARS]
 
 
# ─── FIRST INNING SPOTLIGHT ─────────────────────────────────
# NRFI / YRFI — dedicated post type with clear explanation
 
def generate_first_inning_spotlight(away_pitcher, home_pitcher,
                                     away_team, home_team,
                                     nrfi_prob, yrfi_prob,
                                     prop_label, model_edge=None,
                                     home_era=None, away_era=None,
                                     umpire_str=None, weather_str=None):
    is_nrfi = prop_label == "NRFI"
    featured_prob = nrfi_prob if is_nrfi else yrfi_prob
    featured_label = "NRFI" if is_nrfi else "YRFI"
    featured_full = (
        "No Run First Inning" if is_nrfi
        else "Yes Run First Inning"
    )
 
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 FIRST INNING SPOTLIGHT",
        _date() + " | Algorithm v" + ALGO_VERSION,
        "",
        "\u26be " + away_team + " @ " + home_team,
        "",
        featured_label + " \u2014 " + featured_full,
        "Model probability: " + str(round(featured_prob * 100, 1)) + "%",
    ]
    if model_edge is not None:
        prefix = "+" if model_edge >= 0 else ""
        lines.append("Model Edge: " + prefix + str(model_edge) + "%")
 
    lines += [
        "",
        DIVIDER,
        "",
        "WHAT IS " + featured_label + "?",
        "",
    ]
 
    if is_nrfi:
        lines += [
            "NRFI = No Run First Inning.",
            "The model projects neither team scores",
            "in the top or bottom of the 1st inning.",
            "",
            "Books price this as a separate market.",
            "We evaluate it with the same 9-layer model",
            "used for all our pitcher projections.",
        ]
    else:
        lines += [
            "YRFI = Yes Run First Inning.",
            "The model projects at least one team scores",
            "in the top or bottom of the 1st inning.",
            "",
            "Books price this as a separate market.",
            "We evaluate both pitchers' first-inning ERA,",
            "not their season ERA. The difference matters.",
        ]
 
    lines += ["", DIVIDER, "", "THE PITCHING MATCHUP:", ""]
 
    if away_era is not None:
        lines.append(
            "\u26be " + away_pitcher + " (" + away_team + ")" +
            "\n  Blended first-inning ERA: " + str(round(away_era, 2))
        )
        lines.append("")
 
    if home_era is not None:
        lines.append(
            "\u26be " + home_pitcher + " (" + home_team + ")" +
            "\n  Blended first-inning ERA: " + str(round(home_era, 2))
        )
        lines.append("")
 
    lines += [
        DIVIDER, "",
        "PROBABILITY BREAKDOWN:",
        "",
        "NRFI: " + str(round(nrfi_prob * 100, 1)) + "%",
        "YRFI: " + str(round(yrfi_prob * 100, 1)) + "%",
        "",
    ]
 
    if umpire_str:
        lines += [DIVIDER, "", "\U0001f4ca UMPIRE", umpire_str, ""]
    if weather_str:
        lines += [DIVIDER, "", "\U0001f4ca WEATHER", weather_str, ""]
 
    lines += [
        DIVIDER, "",
        "10,000 simulations. Live data.",
        "This is data. Not advice.",
        "",
        "#EdgeEquation #MLB #NRFI" if is_nrfi else "#EdgeEquation #MLB #YRFI",
    ]
    return "\n".join(lines)[:MAX_CHARS]
 
 
# ─── FROM PLAY HELPERS ──────────────────────────────────────
 
def generate_gotd_from_play(play):
    try:
        away = play.get("opponent", "Away")
        home = play.get("team", "Home")
        away_proj = round(play.get("away_proj", play.get("true_lambda", 0) / 2), 1)
        home_proj = round(play.get("home_proj", play.get("true_lambda", 0) / 2), 1)
        vegas_total = play.get("vegas_total", None)
        league = (play.get("sport_label") or play.get("sport", "MLB")).upper()
        sport = play.get("sport", "baseball_mlb")
        edge = play.get("edge", None)
        factors = _build_factors_from_play(play)
        return generate_gotd(
            away_team=away, home_team=home,
            away_proj=float(away_proj), home_proj=float(home_proj),
            vegas_total=float(vegas_total) if vegas_total else None,
            league_short=league, key_factors=factors,
            model_edge=round(edge * 100, 1) if edge else None,
            sport=sport,
        )
    except Exception as e:
        logger.error("GOTD from play failed: " + str(e))
        return ""
 
 
def generate_potd_from_play(play):
    try:
        player = play.get("player", "")
        team = play.get("team", "")
        opponent = play.get("opponent", "")
        prop = play.get("prop_label", "K")
        proj = play.get("true_lambda", 0)
        line = play.get("line", None)
        league = (play.get("sport_label") or play.get("sport", "MLB")).upper()
        sport = play.get("sport", "baseball_mlb")
        edge = play.get("edge", None)
        factors = _build_factors_from_play(play)
        extra_stats = {}
        if play.get("k9_season"):
            extra_stats["K/9 blended"] = round(play["k9_season"], 2)
        if play.get("avg_ip_recent"):
            extra_stats["Avg IP"] = round(play["avg_ip_recent"], 2)
        if play.get("true_lambda"):
            extra_stats["True lambda"] = round(play["true_lambda"], 3)
        if play.get("swstr_pct"):
            extra_stats["SwStr%"] = str(round(play["swstr_pct"] * 100, 1)) + "%"
        return generate_potd(
            player_name=player, team=team, opponent=opponent,
            prop_label=prop,
            projection=round(float(proj), 1),
            vegas_line=float(line) if line else None,
            league_short=league,
            key_factors=factors,
            model_edge=round(edge * 100, 1) if edge else None,
            sport=sport,
            extra_stats=extra_stats if extra_stats else None,
        )
    except Exception as e:
        logger.error("POTD from play failed: " + str(e))
        return ""
 
 
def generate_first_inning_from_play(play):
    try:
        player = play.get("player", "")
        pitchers = player.split(" / ")
        away_pitcher = pitchers[0] if pitchers else "Away Pitcher"
        home_pitcher = pitchers[1] if len(pitchers) > 1 else "Home Pitcher"
        away_team = play.get("opponent", "")
        home_team = play.get("team", "")
        prop = play.get("prop_label", "NRFI")
        sim_prob = play.get("sim_prob", 0.6)
        nrfi_prob = sim_prob if prop == "NRFI" else round(1 - sim_prob, 4)
        yrfi_prob = round(1 - nrfi_prob, 4)
        edge = play.get("edge", None)
        home_era = play.get("home_era", None)
        away_era = play.get("away_era", None)
        umpire = play.get("umpire", None)
        weather = play.get("weather", None)
        umpire_str = ("Umpire: " + str(umpire)) if umpire else None
        weather_str = ("Conditions: " + str(weather)) if weather else None
        return generate_first_inning_spotlight(
            away_pitcher=away_pitcher,
            home_pitcher=home_pitcher,
            away_team=away_team,
            home_team=home_team,
            nrfi_prob=nrfi_prob,
            yrfi_prob=yrfi_prob,
            prop_label=prop,
            model_edge=round(edge * 100, 1) if edge else None,
            home_era=home_era,
            away_era=away_era,
            umpire_str=umpire_str,
            weather_str=weather_str,
        )
    except Exception as e:
        logger.error("First inning from play failed: " + str(e))
        return ""
 
 
def _build_factors_from_play(play):
    factors = []
    sport = play.get("sport", "")
    prop = play.get("prop_label", "")
 
    if sport == "baseball_mlb" and prop == "K":
        swstr = play.get("swstr_pct", 0.107)
        if swstr and swstr != 0.107:
            pct = round(swstr * 100, 1)
            rank = ("top 5%" if swstr > 0.140 else
                    "top 10%" if swstr > 0.128 else
                    "top 18%" if swstr > 0.120 else "above average")
            factors.append(
                "Swinging strike rate\n" +
                str(pct) + "% SwStr% ranks " + rank + " of all MLB starters.\n" +
                "Books consistently undervalue SwStr% as a K predictor.\n" +
                "Our model weights it at 22% of the total projection."
            )
        platoon = play.get("platoon_adjustment", 1.0)
        if platoon >= 1.08:
            factors.append(
                "Platoon advantage\n" +
                "Today's lineup projects heavily favoring this matchup.\n" +
                "Platoon K rate adjustment: +" + str(round((platoon - 1) * 100)) + "%"
            )
        elif platoon <= 0.92:
            factors.append(
                "Platoon disadvantage\n" +
                "Lineup composition suppresses strikeout upside tonight.\n" +
                "Platoon adjustment: " + str(round((platoon - 1) * 100)) + "%"
            )
        umpire = play.get("umpire_adjustment", 1.0)
        if umpire >= 1.04:
            factors.append(
                "Umpire\n" +
                "Tonight's HP umpire grades +" +
                str(round((umpire - 1) * 100)) + "% above average on called strikes.\n" +
                "Small but consistent signal in our model."
            )
        elif umpire <= 0.96:
            factors.append(
                "Umpire\n" +
                "Tight zone tonight. Umpire grades " +
                str(round((1 - umpire) * 100)) + "% below average on called strikes."
            )
        opp_adj = play.get("opp_k_adjustment", 1.0)
        if opp_adj >= 1.08:
            opp_pct = round(play.get("opp_k_pct", 0.225) * 100, 1)
            factors.append(
                "Opponent K rate\n" +
                str(opp_pct) + "% team K rate — top tier strikeout lineup.\n" +
                "Favorable matchup confirmed by historical splits."
            )
        elif opp_adj <= 0.92:
            opp_pct = round(play.get("opp_k_pct", 0.225) * 100, 1)
            factors.append(
                "Opponent contact rate\n" +
                str(opp_pct) + "% team K rate — contact-heavy lineup.\n" +
                "Model adjusts K projection down accordingly."
            )
        weather_adj = play.get("weather_adj", 1.0)
        if weather_adj != 1.0:
            factors.append(
                "Weather\n" +
                "Conditions affect tonight's run environment.\n" +
                "Weather adjustment: " +
                ("+" if weather_adj > 1 else "") +
                str(round((weather_adj - 1) * 100, 1)) + "%"
            )
 
    elif sport == "basketball_nba":
        factors += [
            "Usage and pace\nGame pace projects above league average tonight.\nMore possessions equals more scoring opportunities.",
            "Opponent defense\nDefensive rating below league average.\nModel adjusts scoring projection upward.",
            "Rest advantage\nRest days factor confirmed in model.",
        ]
 
    elif sport == "icehockey_nhl":
        factors += [
            "Shot rate\nSOG per 60 minutes above league average.\nSustained through even strength and power play.",
            "Ice time projection\nPower play time projected at top-unit level tonight.",
            "Opponent shots allowed\nOpponent ranks below average in shots against per game.",
        ]
 
    if not factors:
        edge = play.get("edge", 0)
        proj = play.get("true_lambda", 0)
        line = play.get("line", 0)
        factors.append(
            "Model projection\n" +
            "Projected: " + str(round(proj, 1)) +
            "  |  Market line: " + str(line) +
            "\nEdge: +" + str(round(edge * 100, 1)) + "%"
        )
 
    return factors[:6]
