from datetime import datetime
from typing import List
from engine.playoff_engine import SeriesProjection


def format_league_overview(league: str) -> str:
    league_name = "NBA" if league == "nba" else "NHL"
    today = datetime.now().strftime("%B %d")

    return (
        f"THE EDGE EQUATION — {league_name} PLAYOFF MODEL OVERVIEW\n"
        f"{today}  |  Algorithm v2.0  |  Hybrid Model\n\n"
        "The engine has processed every matchup using team strength, efficiency profiles, "
        "and a blend of our projections with expert expectations.\n\n"
        "This is data. Not advice.\n"
        f"#SportsAnalytics #PredictiveAnalytics #{league_name} #Playoffs"
    )


def format_matchup_post(p: SeriesProjection) -> str:
    league = "NBA" if p.sport == "nba" else "NHL"

    return (
        f"{p.higher_seed} vs {p.lower_seed}\n\n"
        f"Projected Winner: {p.projected_winner}\n"
        f"Series Probability: {p.win_probability}%\n"
        f"Most Likely Result: {p.most_likely_result}\n\n"
        f"Why the model leans this way:\n{p.blurb}\n\n"
        "Follow for more model-driven playoff projections.\n"
        f"#SportsAnalytics #{league} #Playoffs #DataScience"
    )


def format_all_matchups(projections: List[SeriesProjection]) -> List[str]:
    """Returns a list of formatted posts, one per matchup."""
    posts = []
    for p in projections:
        posts.append(format_matchup_post(p))
    return posts
