import os

import requests
from dotenv import load_dotenv


load_dotenv()


class FootballAPIClient:

    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):

        self.api_key = os.getenv("API_FOOTBALL_KEY")

        self.headers = {
            "x-apisports-key": self.api_key
        }

    def get(self, endpoint, params=None):

        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            headers=self.headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_live_fixtures(self):

        return self.get(
            "fixtures",
            params={
                "live": "all"
            }
        )

    def get_standings(self, league_id, season):

        return self.get(
            "standings",
            params={
                "league": league_id,
                "season": season
            }
        )

    def get_league(self, league_id, season):

        return self.get(
            "leagues",
            params={
                "id": league_id,
                "season": season
            }
        )

    def get_team_fixtures(self, team_id, last=10):

        return self.get(
            "fixtures",
            params={
                "team": team_id,
                "last": last
            }
        )

    def get_league_fixtures(self, league_id, season):

        return self.get(
            "fixtures",
            params={
                "league": league_id,
                "season": season
            }
        )