from datetime import datetime, date
from typing import List, Dict, Optional
 
 
def choose_slate_type(
    now: datetime,
    game_date: date,
    *,
    is_night_slate: bool = False,
    force: Optional[str] = None,
) -> str:
    allowed = {
        "Scheduled Games",
        "Today's Slate",
        "Tonight's Slate",
        "Tomorrow's Slate",
    }
    if force:
        if force not in allowed:
            raise ValueError(f"Invalid forced slate_type: {force}")
        return force
    today = now.date()
    if game_date == today:
        if is_night_slate:
            return "Tonight's Slate"
        return "Today's Slate"
    if (game_date - today).days == 1:
        return "Tomorrow's Slate"
    return "Scheduled Games"
 
 
def format_edge_equation_post(
    *,
    league_short: str,
    league_full_name: str,
    date_str: str,
    algo_version: str,
    slate_type: str,
    games: List[Dict[str, float]],
    league_full_hashtag: Optional[str] = None,
) -> str:
    allowed_slate_types = {
        "Scheduled Games",
        "Today's Slate",
        "Tonight's Slate",
        "Tomorrow's Slate",
    }
    if slate_type not in allowed_slate_types:
        raise ValueError(f"Invalid slate_type: {slate_type}")
    league_full_hashtag = league_full_hashtag or league_full_name.replace(" ", "")
    hashtag_line = f"#{league_short} #{league_full_hashtag}"
    lines = [
        f"EDGE EQUATION — {league_short} PROJECTIONS",
        f"{date_str} | Algorithm v{algo_version}",
        f"{league_full_name} | {slate_type}",
        "",
    ]
    for g in games:
        line = (
            f"{g['team_a']} @ {g['team_b']}: "
            f"{float(g['a_score']):.1f} — {float(g['b_score']):.1f} | "
            f"Total: {float(g['total']):.1f}"
        )
        lines.append(line)
    lines.append("")
    lines.append("This is data. Not advice.")
    lines.append(f"Books are soft on {league_short}. The math shows why.")
    lines.append(hashtag_line)
    return "\n".join(lines)
 
 
def build_edge_equation_post(
    *,
    league_short: str,
    league_full_name: str,
    algo_version: str,
    games: List[Dict[str, float]],
    game_date: date,
    now: Optional[datetime] = None,
    is_night_slate: bool = False,
    force_slate: Optional[str] = None,
    league_full_hashtag: Optional[str] = None,
) -> str:
    now = now or datetime.now()
    slate_type = choose_slate_type(
        now=now,
        game_date=game_date,
        is_night_slate=is_night_slate,
        force=force_slate,
    )
    date_str = now.strftime("%B %-d") if hasattr(now, "strftime") else "Unknown Date"
    return format_edge_equation_post(
        league_short=league_short,
        league_full_name=league_full_name,
        date_str=date_str,
        algo_version=algo_version,
        slate_type=slate_type,
        games=games,
        league_full_hashtag=league_full_hashtag,
    )
 
 
if __name__ == "__main__":
    example_games = [
        {
            "team_a": "Samsung Lions",
            "team_b": "Hanwha Eagles",
            "a_score": 5.0,
            "b_score": 5.4,
            "total": 10.4,
        }
    ]
    post = build_edge_equation_post(
        league_short="KBO",
        league_full_name="Korean Baseball",
        algo_version="2.0",
        games=example_games,
        game_date=date(2026, 4, 15),
        league_full_hashtag="KoreanBaseball",
    )
    print(post)
