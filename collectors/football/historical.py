from .client import FootballAPIClient
from models.match import Match
from database.database import Database


def obtener_historico(league_id, season):

    print("Obteniendo histórico...\n")

    api = FootballAPIClient()

    data = api.get_league_fixtures(
        league_id,
        season
    )

    print("Cantidad de partidos:", data["results"])
    print()

    if data["errors"]:
        print("Errores:", data["errors"])
        return []

    partidos = []

    for partido in data["response"]:

        match = Match(

            fixture_id=partido["fixture"]["id"],

            league_id=partido["league"]["id"],
            season=partido["league"]["season"],

            home_team_id=partido["teams"]["home"]["id"],
            away_team_id=partido["teams"]["away"]["id"],

            fecha=partido["fixture"]["date"],
            estado=partido["fixture"]["status"]["short"],

            goles_local=partido["goals"]["home"],
            goles_visitante=partido["goals"]["away"],

            liga=partido["league"]["name"],
            local=partido["teams"]["home"]["name"],
            visitante=partido["teams"]["away"]["name"],

            estadio=partido["fixture"]["venue"]["name"],
            ciudad=partido["fixture"]["venue"]["city"],
            arbitro=partido["fixture"]["referee"],
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

    partidos = obtener_historico(
        league_id=128,
        season=2024
    )

    print("Partidos procesados:", len(partidos))

    guardar_historico(partidos)

    print()
    print("Histórico guardado correctamente en SQLite.")


if __name__ == "__main__":
    main()