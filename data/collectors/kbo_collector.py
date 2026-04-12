"""
KBO Data Collector — Korean Baseball Organization
Used for Cash Before Coffee overnight plays
"""
import requests
from datetime import datetime, date, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import APIS, HEADERS


class KBOCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS["default"])

    def get_todays_games(self, game_date=None):
        if game_date is None:
            # KBO games are next day in Korea time (UTC+9)
            game_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"  [i] KBO schedule for: {game_date}")
        return []

    def collect_daily(self, game_date=None):
        print(f"\n KBO Overnight - Collecting data...")
        games = self.get_todays_games(game_date)
        print(f"  Found {len(games)} games scheduled")
        return []
