from dataclasses import dataclass


@dataclass
class Match:

    fixture_id: int

    league_id: int
    season: int

    home_team_id: int
    away_team_id: int

    liga: str
    local: str
    visitante: str

    estadio: str | None
    ciudad: str | None
    arbitro: str | None