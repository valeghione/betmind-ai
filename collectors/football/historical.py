import sys

from .client import FootballAPIClient
from models.match import Match
from database.database import Database


def obtener_historico(league_id, season):

    print("Obteniendo histórico...")
    print()
    print(f"Liga ID: {league_id}")
    print(f"Temporada: {season}")
    print()

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

    for partido in data["response"]:

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

    return partidos


def guardar_historico(partidos):

    db = Database()

    db.crear_tabla_partidos()

    for partido in partidos:

        db.guardar_partido(partido)

    db.cerrar()


def main():

    league_id = 128

    if len(sys.argv) > 1:

        season = int(sys.argv[1])

    else:

        season = 2024

    partidos = obtener_historico(
        league_id=league_id,
        season=season
    )

    print(
        f"Partidos procesados: {len(partidos)}"
    )

    if partidos:

        guardar_historico(partidos)

        print()
        print(
            "Histórico guardado correctamente en SQLite."
        )

        print()
        print("Primer partido:")

        primer_partido = partidos[0]

        print(
            f"{primer_partido.local} "
            f"vs "
            f"{primer_partido.visitante}"
        )

        print(
            f"Fecha: {primer_partido.fecha}"
        )

    else:

        print()
        print("No se guardaron partidos.")


if __name__ == "__main__":
    main()