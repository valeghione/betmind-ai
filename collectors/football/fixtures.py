from .client import FootballAPIClient
from models.match import Match
from database.database import Database


def obtener_partidos():

    print("Obteniendo partidos...\n")

    api = FootballAPIClient()

    db = Database()
    db.crear_tabla_partidos()

    data = api.get_live_fixtures()

    print("Cantidad de partidos:", data["results"])
    print()

    matches = []

    for partido in data["response"]:

        match = Match(

            fixture_id=partido["fixture"]["id"],

            league_id=partido["league"]["id"],
            season=partido["league"]["season"],

            home_team_id=partido["teams"]["home"]["id"],
            away_team_id=partido["teams"]["away"]["id"],

            liga=partido["league"]["name"],
            local=partido["teams"]["home"]["name"],
            visitante=partido["teams"]["away"]["name"],

            estadio=partido["fixture"]["venue"]["name"],
            ciudad=partido["fixture"]["venue"]["city"],
            arbitro=partido["fixture"]["referee"],
        )

        matches.append(match)

        db.guardar_partido(match)

    return matches


def mostrar_partidos(matches):

    for match in matches:

        print("=" * 40)
        print(f"Fixture ID: {match.fixture_id}")
        print(f"League ID : {match.league_id}")
        print(f"Season    : {match.season}")
        print(f"Home ID   : {match.home_team_id}")
        print(f"Away ID   : {match.away_team_id}")
        print()

        print(f"Liga: {match.liga}")
        print(f"Partido: {match.local} vs {match.visitante}")
        print(f"Estadio: {match.estadio}")
        print(f"Ciudad: {match.ciudad}")
        print(f"Árbitro: {match.arbitro}")
        print("=" * 40)
        print()


def main():

    partidos = obtener_partidos()

    mostrar_partidos(partidos)

    db = Database()

    registros = db.obtener_partidos()

    print(f"\nHay {len(registros)} partidos guardados en SQLite.")

    db.cerrar()


if __name__ == "__main__":
    main()