import unittest

from collectors.football.historical import (
    ARGENTINA_PRIMERA_LPF_LEAGUE_ID,
    es_fixture_historico_valido,
)


def fixture(status="FT", league_id=128, home_goals=1, away_goals=0):

    return {
        "fixture": {
            "id": 123,
            "date": "2025-05-01T20:00:00+00:00",
            "status": {"short": status},
        },
        "league": {"id": league_id},
        "goals": {"home": home_goals, "away": away_goals},
    }


class HistoricalIngestionTests(unittest.TestCase):

    def test_accepts_finished_argentina_fixture(self):

        self.assertTrue(
            es_fixture_historico_valido(
                fixture(),
                ARGENTINA_PRIMERA_LPF_LEAGUE_ID,
            )
        )

    def test_rejects_live_and_future_statuses(self):

        for status in ("NS", "1H", "HT", "2H", "PST"):
            with self.subTest(status=status):
                self.assertFalse(
                    es_fixture_historico_valido(
                        fixture(status=status),
                        ARGENTINA_PRIMERA_LPF_LEAGUE_ID,
                    )
                )

    def test_rejects_other_league_and_missing_scores(self):

        self.assertFalse(
            es_fixture_historico_valido(
                fixture(league_id=39),
                ARGENTINA_PRIMERA_LPF_LEAGUE_ID,
            )
        )

    def test_rejects_invalid_fixture_id(self):

        partido = fixture()
        partido["fixture"]["id"] = "no-es-un-id"

        self.assertFalse(
            es_fixture_historico_valido(
                partido,
                ARGENTINA_PRIMERA_LPF_LEAGUE_ID,
            )
        )
        self.assertFalse(
            es_fixture_historico_valido(
                fixture(home_goals=None),
                ARGENTINA_PRIMERA_LPF_LEAGUE_ID,
            )
        )
