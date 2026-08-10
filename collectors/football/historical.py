import sys

from models.match import Match
from database.database import Database


ARGENTINA_PRIMERA_LPF_LEAGUE_ID = 128
FINAL_STATUSES = {"FT", "AET", "PEN"}
SUPPORTED_SEASONS = (2023, 2024, 2025, 2026)


def es_fixture_historico_valido(partido, league_id):

    fixture = partido.get("fixture") or {}
    league = partido.get("league") or {}
    goals = partido.get("goals") or {}
    status = fixture.get("status") or {}

    fixture_id = fixture.get("id")
    fecha = fixture.get("date")
    estado = status.get("short")

    if league.get("id") != league_id:
        return False

    if estado not in FINAL_STATUSES:
        return False

    try:
        fixture_id_valido = int(fixture_id) > 0
    except (TypeError, ValueError):
        fixture_id_valido = False

    if not fixture_id_valido:
        return False

    if not fecha:
        return False

    return (
        goals.get("home") is not None
        and goals.get("away") is not None
    )


def obtener_historico(league_id, season):

    print("Obteniendo histórico...")
    print()
    print(f"Liga ID: {league_id}")
    print(f"Temporada: {season}")
    print()

    from .client import FootballAPIClient

    api = FootballAPIClient()

    data = api.get_league_fixtures(
        league_id,
        season
    )

    print("Cantidad de partidos:", data["results"])
    print()

    if data["errors"]:

        print("Errores de la API:")
        print(data["errors"])

        return []

    partidos = []

    descartados = 0

    for partido in data["response"]:

        if not es_fixture_historico_valido(
            partido,
            league_id
        ):

            descartados += 1
            continue

        fixture = partido["fixture"]
        league = partido["league"]
        teams = partido["teams"]
        goals = partido["goals"]

        venue = fixture["venue"]

        match = Match(

            fixture_id=fixture["id"],

            league_id=league["id"],
            season=league["season"],

            home_team_id=teams["home"]["id"],
            away_team_id=teams["away"]["id"],

            fecha=fixture["date"],
            estado=fixture["status"]["short"],

            goles_local=goals["home"],
            goles_visitante=goals["away"],

            liga=league["name"],
            local=teams["home"]["name"],
            visitante=teams["away"]["name"],

            estadio=venue["name"],
            ciudad=venue["city"],
            arbitro=fixture["referee"],
        )

        partidos.append(match)

    print(
        f"Históricos finalizados válidos: {len(partidos)}"
    )

    print(
        f"Fixtures descartados: {descartados}"
    )

    return partidos


def guardar_historico(partidos):

    db = Database()

    db.crear_tabla_partidos()

    for partido in partidos:

        db.guardar_partido_historico(partido)

    db.cerrar()


def main():

    if len(sys.argv) > 1:

        seasons = [int(season) for season in sys.argv[1:]]

    else:

        seasons = list(SUPPORTED_SEASONS)

    invalidas = [
        season
        for season in seasons
        if season not in SUPPORTED_SEASONS
    ]

    if invalidas:

        print(
            "Temporadas no soportadas: "
            + ", ".join(map(str, invalidas))
        )

        return

    for season in seasons:

        partidos = obtener_historico(
            league_id=ARGENTINA_PRIMERA_LPF_LEAGUE_ID,
            season=season
        )

        print(
            f"Partidos procesados ({season}): {len(partidos)}"
        )

        if not partidos:

            print("No se guardaron partidos.")

            continue

        guardar_historico(partidos)

        print(
            "Histórico guardado correctamente en SQLite."
        )


if __name__ == "__main__":
    main()
