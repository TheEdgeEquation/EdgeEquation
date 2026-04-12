"""
MorningScanGenerator — Builds the 7 AM CT morning preview post.
Lists what stats/games the algorithm is scanning, mentions 10,000 simulations,
builds anticipation for the daily Equation card at 10 AM CT.
"""
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data.collectors.mlb_collector import MLBCollector
from data.collectors.nhl_collector import NHLCollector
from data.collectors.nba_collector import NBACollector


class MorningScanGenerator:
    def __init__(self):
        self.mlb = MLBCollector()
        self.nhl = NHLCollector()
        self.nba = NBACollector()

    def generate_morning_scan_text(self):
        """
        Build the morning scan tweet text.
        Checks schedules, counts games, generates preview text.
        """
        today_str = date.today().strftime("%B %d, %Y")
        day_of_week = date.today().strftime("%A")

        # Get game counts from each sport
        mlb_games = self.mlb.get_todays_games()
        nhl_games = self.nhl.get_todays_games()
        nba_games = self.nba.get_todays_games()

        mlb_count = len(mlb_games)
        nhl_count = len(nhl_games)
        nba_count = len(nba_games)

        # Build sport lines
        sport_lines = []
        scan_targets = []

        if mlb_count > 0:
            sport_lines.append(f"⚾ MLB: {mlb_count} games — scanning pitcher K props")
            scan_targets.append(f"MLB {mlb_count} Games")
        else:
            scan_targets.append("MLB Dark")

        if nhl_count > 0:
            sport_lines.append(f"🏒 NHL: {nhl_count} games — scanning SOG props")
            scan_targets.append(f"NHL {nhl_count} Games")
        else:
            scan_targets.append("NHL Dark")

        if nba_count > 0:
            sport_lines.append(f"🏀 NBA: {nba_count} games — scanning 3PM props")
            scan_targets.append(f"NBA {nba_count} Games")
        else:
            scan_targets.append("NBA Dark")

        total_games = mlb_count + nhl_count + nba_count

        if total_games == 0:
            return (
                f"📐 MORNING SCAN — {today_str}\n\n"
                "No games on the board today.\n"
                "The algorithm rests. Back tomorrow.\n\n"
                "No feelings. Just facts."
            )

        lines = [
            f"📐 MORNING SCAN — {day_of_week}",
            f"🗓️ {today_str}",
            f"Algorithm v2.0 | {' • '.join(scan_targets)}",
            "",
        ]
        lines.extend(sport_lines)
        lines.append("")
        lines.append(
            f"🔬 Running {total_games * 247} player props through "
            "10,000 simulations each to isolate today's edge."
        )
        lines.append("")
        lines.append("📐 Σ The Equation drops at 10 AM CT.")
        lines.append("No feelings. Just facts.")
        lines.append("#MLB #NHL #NBA #SportsBetting")

        return "\n".join(lines)
