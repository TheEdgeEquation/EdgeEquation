"""
AFL Data Collector - Australian Football League
Used for Cash Before Coffee overnight plays
"""
import requests
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import APIS, HEADERS

class AFLCollector:
    def __init__(self):
        self.session = requests.Session()
    def get_todays_games(self, game_date=None):
        return []
    def collect_daily(self, game_date=None):
        return []
