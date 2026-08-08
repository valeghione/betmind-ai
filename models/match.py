from dataclasses import dataclass


@dataclass
class Match:

    fixture_id: int

    league_id: int
    season: int

    home_team_id: int
    away_team_id: int

    fecha: str
    estado: str

    goles_local: int | None
    goles_visitante: int | None

    liga: str
    local: str
    visitante: str

    estadio: str | None
    ciudad: str | None
    arbitro: str | None