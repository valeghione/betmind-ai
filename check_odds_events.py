import os
import requests
from dotenv import load_dotenv


LEAGUE = "argentina-primera-lpf-clausura"


def main():

    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:
        print("ERROR: no se encontró ODDS_API_KEY")
        return

    url = "https://api.odds-api.io/v3/events"

    params = {
        "apiKey": api_key,
        "sport": "football",
        "league": LEAGUE,
        "limit": 50
    }

    print("=" * 70)
    print("PRÓXIMOS EVENTOS — ARGENTINA PRIMERA LPF")
    print("=" * 70)

    try:

        respuesta = requests.get(
            url,
            params=params,
            timeout=15
        )

        print()
        print(
            f"HTTP STATUS: {respuesta.status_code}"
        )

        if respuesta.status_code != 200:
            print(respuesta.text[:3000])
            return

        eventos = respuesta.json()

        print()
        print(
            f"Eventos recibidos: {len(eventos)}"
        )

        print()

        encontrados = 0

        for evento in eventos:

            estado = str(
                evento.get("status", "")
            ).lower()

            if estado in (
                "pending",
                "scheduled",
                "upcoming"
            ):

                print(
                    f"ID: {evento.get('id')}"
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

                print("-" * 60)

                encontrados += 1

        print()

        if encontrados == 0:
            print(
                "No se encontraron eventos futuros "
                "en la respuesta."
            )

    except requests.exceptions.RequestException as error:

        print()
        print("ERROR DE CONEXIÓN:")
        print(error)

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()