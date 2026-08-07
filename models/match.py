from dataclasses import dataclass


@dataclass
class Match:

    liga: str
    local: str
    visitante: str
    estadio: str
    ciudad: str
    arbitro: str | None