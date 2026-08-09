import os
import requests
from dotenv import load_dotenv

from database.database import Database


LEAGUE = "argentina-primera-lpf-clausura"


def obtener_eventos():

    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:
        print("ERROR: no se encontró ODDS_API_KEY en .env")
        return None

    url = "https://api.odds-api.io/v3/events"

    params = {
        "apiKey": api_key,
        "sport": "football",
        "league": LEAGUE,
        "limit": 50
    }

    respuesta = requests.get(
        url,
        params=params,
        timeout=15
    )

    print(
        f"HTTP STATUS: {respuesta.status_code}"
    )

    if respuesta.status_code != 200:

        print(
            respuesta.text[:5000]
        )

        return None

    return respuesta.json()


def mostrar_eventos(eventos):

    print()
    print("=" * 70)
    print("PRÓXIMOS EVENTOS ODDS-API")
    print("=" * 70)

    encontrados = 0

    for evento in eventos:

        estado = str(
            evento.get("status", "")
        ).lower()

        if estado not in (
            "pending",
            "scheduled",
            "upcoming"
        ):
            continue

        print()
        print(
            f"Odds Event ID: {evento.get('id')}"
        )

        print(
            f"{evento.get('home')} "
            f"vs "
            f"{evento.get('away')}"
        )

        print(
            f"Fecha: {evento.get('date')}"
        )

        print(
            f"Estado: {evento.get('status')}"
        )

        encontrados += 1

    print()

    print(
        f"Eventos futuros encontrados: "
        f"{encontrados}"
    )


def main():

    print("=" * 70)
    print("BETMIND — ACTUALIZAR FIXTURES")
    print("=" * 70)

    eventos = obtener_eventos()

    if eventos is None:
        return

    print(
        f"Eventos recibidos: {len(eventos)}"
    )

    mostrar_eventos(eventos)


if __name__ == "__main__":
    main()