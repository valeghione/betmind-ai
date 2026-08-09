import os
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN
# ============================================================

EVENT_ID = 1158667


# ============================================================
# API KEY
# ============================================================

def obtener_api_key():

    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "No se encontró ODDS_API_KEY en .env"
        )

    return api_key


# ============================================================
# PROBAR ENDPOINT
# ============================================================

def probar_endpoint(
    nombre,
    url,
    params
):

    print()
    print("=" * 80)
    print(nombre)
    print("=" * 80)

    print()
    print("URL:")
    print(url)

    print()
    print("Parámetros:")
    print(params)

    try:

        respuesta = requests.get(
            url,
            params=params,
            timeout=15
        )

        print()
        print(
            f"HTTP STATUS: "
            f"{respuesta.status_code}"
        )

        print()
        print("RESPUESTA:")

        try:
            print(
                respuesta.json()
            )

        except ValueError:
            print(
                respuesta.text
            )

    except Exception as error:

        print()
        print(
            "ERROR:"
        )

        print(error)


# ============================================================
# MAIN
# ============================================================

def main():

    api_key = obtener_api_key()

    print("=" * 80)
    print("BETMIND AI — DIAGNÓSTICO ODDS HISTÓRICAS")
    print("=" * 80)

    print()

    print(
        f"Event ID SQLite: {EVENT_ID}"
    )

    print()
    print(
        "IMPORTANTE:"
    )

    print(
        "El fixture_id de SQLite y el Odds Event ID "
        "no necesariamente son el mismo ID."
    )

    # ========================================================
    # 1. PROBAR /ODDS NORMAL
    # ========================================================

    probar_endpoint(
        "1 — ENDPOINT ACTUAL /ODDS",

        "https://api.odds-api.io/v3/odds",

        {
            "apiKey": api_key,
            "eventId": EVENT_ID,
            "bookmakers": "Bet365"
        }
    )

    # ========================================================
    # 2. PROBAR POSIBLE /HISTORICAL
    # ========================================================

    probar_endpoint(
        "2 — POSIBLE /HISTORICAL",

        "https://api.odds-api.io/v3/historical",

        {
            "apiKey": api_key,
            "eventId": EVENT_ID,
            "bookmakers": "Bet365"
        }
    )

    # ========================================================
    # 3. PROBAR POSIBLE /ODDS/HISTORICAL
    # ========================================================

    probar_endpoint(
        "3 — POSIBLE /ODDS/HISTORICAL",

        "https://api.odds-api.io/v3/odds/historical",

        {
            "apiKey": api_key,
            "eventId": EVENT_ID,
            "bookmakers": "Bet365"
        }
    )

    # ========================================================
    # 4. PROBAR POSIBLE /HISTORY
    # ========================================================

    probar_endpoint(
        "4 — POSIBLE /HISTORY",

        "https://api.odds-api.io/v3/history",

        {
            "apiKey": api_key,
            "eventId": EVENT_ID,
            "bookmakers": "Bet365"
        }
    )

    print()
    print("=" * 80)
    print("DIAGNÓSTICO FINALIZADO")
    print("=" * 80)


if __name__ == "__main__":
    main()