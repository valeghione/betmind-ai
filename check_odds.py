import os
import requests

from dotenv import load_dotenv

from odds import obtener_cuotas_evento, extraer_1x2


# ============================================================
# CONFIGURACIÓN
# ============================================================

EVENT_ID = 73265148


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
# OBTENER EVENTO
# ============================================================

def obtener_evento(event_id):

    api_key = obtener_api_key()

    url = "https://api.odds-api.io/v3/events"

    params = {
        "apiKey": api_key,
        "sport": "football",
        "league":
            "argentina-primera-lpf-clausura",
        "limit": 50
    }

    respuesta = requests.get(
        url,
        params=params,
        timeout=15
    )

    respuesta.raise_for_status()

    eventos = respuesta.json()

    for evento in eventos:

        if int(evento["id"]) == int(event_id):

            return evento

    return None


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("BETMIND AI — CHECK ODDS")
    print("=" * 75)

    print()

    print(
        f"Event ID: {EVENT_ID}"
    )

    # --------------------------------------------------------
    # EVENTO
    # --------------------------------------------------------

    evento = obtener_evento(
        EVENT_ID
    )

    if evento is None:

        print()
        print(
            "No se encontró el evento."
        )

        return

    print()

    print(
        f"Partido: "
        f"{evento['home']} "
        f"vs "
        f"{evento['away']}"
    )

    print(
        f"Fecha: "
        f"{evento['date']}"
    )

    print(
        f"Estado: "
        f"{evento['status']}"
    )

    # --------------------------------------------------------
    # CUOTAS CRUDAS
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("RESPUESTA DE ODDS-API")
    print("=" * 75)

    try:

        datos_odds = obtener_cuotas_evento(
            EVENT_ID
        )

    except Exception as error:

        print()
        print(
            "ERROR:"
        )

        print(error)

        return

    if not datos_odds:

        print()
        print(
            "No se recibieron cuotas."
        )

        return

    print()

    print(
        "Tipo de respuesta:",
        type(datos_odds).__name__
    )

    print()

    print(
        datos_odds
    )

    # --------------------------------------------------------
    # EXTRAER 1X2
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("MERCADO 1X2 EXTRAÍDO")
    print("=" * 75)

    try:

        cuotas = extraer_1x2(
            datos_odds
        )

    except Exception as error:

        print()
        print(
            "ERROR EXTRAYENDO 1X2:"
        )

        print(error)

        return

    print()

    if cuotas is None:

        print(
            "No se encontró mercado 1X2."
        )

        return

    print(
        f"Local:      "
        f"{cuotas['local']:.2f}"
    )

    print(
        f"Empate:     "
        f"{cuotas['empate']:.2f}"
    )

    print(
        f"Visitante:  "
        f"{cuotas['visitante']:.2f}"
    )

    # --------------------------------------------------------
    # PROBABILIDADES IMPLÍCITAS
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("PROBABILIDADES IMPLÍCITAS")
    print("=" * 75)

    for nombre in (
        "local",
        "empate",
        "visitante"
    ):

        cuota = cuotas[nombre]

        probabilidad = 1 / cuota

        print(
            f"{nombre.capitalize():<12}"
            f"{probabilidad * 100:.2f}%"
        )

    # --------------------------------------------------------
    # CUOTA MÍNIMA PARA EV 0
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("VERIFICACIÓN")
    print("=" * 75)

    print()

    print(
        "Las cuotas anteriores son "
        "las que extrae actualmente "
        "BetMind del evento."
    )

    print(
        "Ahora compararemos estos valores "
        "contra la respuesta cruda de la API."
    )

    print()
    print("=" * 75)


if __name__ == "__main__":

    main()