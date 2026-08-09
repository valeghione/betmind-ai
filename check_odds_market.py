import os
import json
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN
# ============================================================

EVENT_ID = 73265136
BOOKMAKER = "Bet365"


# ============================================================
# OBTENER CUOTAS
# ============================================================

def obtener_cuotas():

    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:
        print(
            "ERROR: no se encontró ODDS_API_KEY "
            "en el archivo .env"
        )
        return None

    url = "https://api.odds-api.io/v3/odds"

    params = {
        "apiKey": api_key,
        "eventId": EVENT_ID,
        "bookmakers": BOOKMAKER
    }

    try:

        respuesta = requests.get(
            url,
            params=params,
            timeout=15
        )

    except requests.exceptions.RequestException as error:

        print()
        print("ERROR DE CONEXIÓN:")
        print(error)

        return None

    print()
    print(
        f"HTTP STATUS: {respuesta.status_code}"
    )

    if respuesta.status_code != 200:

        print()
        print("ERROR DE LA API:")
        print(
            respuesta.text[:5000]
        )

        return None

    try:

        return respuesta.json()

    except ValueError:

        print()
        print(
            "ERROR: la API no devolvió "
            "JSON válido."
        )

        print(
            respuesta.text[:5000]
        )

        return None


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def main():

    print("=" * 70)
    print("BETMIND — CUOTAS DEL EVENTO")
    print("=" * 70)

    print()
    print(
        "Evento:"
    )

    print(
        "CA San Lorenzo de Almagro "
        "vs "
        "CA Huracan"
    )

    print()
    print(
        f"Event ID: {EVENT_ID}"
    )

    print(
        f"Bookmaker: {BOOKMAKER}"
    )

    datos = obtener_cuotas()

    if datos is None:

        print()
        print(
            "No se pudieron obtener las cuotas."
        )

        return

    print()
    print("RESPUESTA DE LA API")
    print("-" * 70)

    print(
        json.dumps(
            datos,
            indent=4,
            ensure_ascii=False
        )[:20000]
    )

    print()
    print("=" * 70)


if __name__ == "__main__":

    main()