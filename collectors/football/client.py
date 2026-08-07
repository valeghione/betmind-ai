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
