import os
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN
# ============================================================

BOOKMAKER = "Bet365"
LEAGUE = "argentina-primera-lpf-clausura"

API_URL = "https://api.odds-api.io/v3/events"
ODDS_URL = "https://api.odds-api.io/v3/odds"


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
# BUSCAR EVENTOS
# ============================================================

def obtener_eventos():

    api_key = obtener_api_key()

    params = {
        "apiKey": api_key,
        "sport": "football",
        "league": LEAGUE,
        "limit": 50
    }

    respuesta = requests.get(
        API_URL,
        params=params,
        timeout=15
    )

    respuesta.raise_for_status()

    return respuesta.json()


# ============================================================
# OBTENER CUOTAS DE UN EVENTO
# ============================================================

def obtener_cuotas_evento(event_id):

    api_key = obtener_api_key()

    params = {
        "apiKey": api_key,
        "eventId": event_id,
        "bookmakers": BOOKMAKER
    }

    respuesta = requests.get(
        ODDS_URL,
        params=params,
        timeout=15
    )

    respuesta.raise_for_status()

    return respuesta.json()


# ============================================================
# EXTRAER MERCADO 1X2
# ============================================================

def extraer_1x2(datos):

    bookmakers = datos.get(
        "bookmakers",
        {}
    )

    bookmaker = bookmakers.get(
        BOOKMAKER,
        []
    )

    for mercado in bookmaker:

        if mercado.get("name") != "ML":
            continue

        cuotas = mercado.get(
            "odds",
            []
        )

        if not cuotas:
            continue

        cuota = cuotas[0]

        if not all(
            clave in cuota
            for clave in (
                "home",
                "draw",
                "away"
            )
        ):
            continue

        return {
            "local": float(cuota["home"]),
            "empate": float(cuota["draw"]),
            "visitante": float(cuota["away"])
        }

    return None


# ============================================================
# BUSCAR EVENTO POR EQUIPOS
# ============================================================

def buscar_evento(
    local,
    visitante
):

    eventos = obtener_eventos()

    local_busqueda = local.lower()
    visitante_busqueda = visitante.lower()

    for evento in eventos:

        home = str(
            evento.get("home", "")
        ).lower()

        away = str(
            evento.get("away", "")
        ).lower()

        if (
            local_busqueda in home
            and
            visitante_busqueda in away
        ):

            return evento

    return None


# ============================================================
# OBTENER CUOTAS POR EQUIPOS
# ============================================================

def obtener_cuotas_partido(
    local,
    visitante
):

    evento = buscar_evento(
        local,
        visitante
    )

    if evento is None:
        return None

    datos = obtener_cuotas_evento(
        evento["id"]
    )

    cuotas = extraer_1x2(
        datos
    )

    if cuotas is None:
        return None

    return {
        "event_id": evento["id"],
        "local": evento["home"],
        "visitante": evento["away"],
        "fecha": evento["date"],
        "estado": evento["status"],
        "bookmaker": BOOKMAKER,
        "cuotas": cuotas
    }


# ============================================================
# PRUEBA
# ============================================================

def main():

    print("=" * 70)
    print("BETMIND — ODDS MODULE")
    print("=" * 70)

    local = input(
        "Equipo local: "
    ).strip()

    visitante = input(
        "Equipo visitante: "
    ).strip()

    try:

        resultado = obtener_cuotas_partido(
            local,
            visitante
        )

    except requests.exceptions.RequestException as error:

        print()
        print("ERROR DE API:")
        print(error)

        return

    except Exception as error:

        print()
        print("ERROR:")
        print(error)

        return

    if resultado is None:

        print()
        print(
            "No se encontraron cuotas 1X2."
        )

        return

    cuotas = resultado["cuotas"]

    print()
    print("-" * 70)

    print(
        f"{resultado['local']} "
        f"vs "
        f"{resultado['visitante']}"
    )

    print(
        f"Fecha: {resultado['fecha']}"
    )

    print(
        f"Estado: {resultado['estado']}"
    )

    print(
        f"Bookmaker: {resultado['bookmaker']}"
    )

    print()
    print("CUOTAS 1X2")

    print(
        f"Local:      {cuotas['local']:.2f}"
    )

    print(
        f"Empate:     {cuotas['empate']:.2f}"
    )

    print(
        f"Visitante:  {cuotas['visitante']:.2f}"
    )

    print("-" * 70)


if __name__ == "__main__":
    main()