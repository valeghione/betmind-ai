import os
import time
import requests

from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN
# ============================================================

BOOKMAKER = "Bet365"
LEAGUE = "argentina-primera-lpf-clausura"

API_URL = "https://api.odds-api.io/v3/events"
ODDS_URL = "https://api.odds-api.io/v3/odds"

TIMEOUT = 15

# Espera normal entre requests
REQUEST_DELAY = 1.0

# Reintentos ante errores temporales
MAX_RETRIES = 4

# Backoff:
# intento 1 -> 2 segundos
# intento 2 -> 4 segundos
# intento 3 -> 8 segundos
# intento 4 -> 16 segundos
BACKOFF_BASE = 2


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
# REQUEST ROBUSTA
# ============================================================

def request_get(
    url,
    params,
    max_retries=MAX_RETRIES
):

    ultimo_error = None

    for intento in range(max_retries + 1):

        try:

            respuesta = requests.get(
                url,
                params=params,
                timeout=TIMEOUT
            )

            # ------------------------------------------------
            # OK
            # ------------------------------------------------

            if respuesta.status_code == 200:

                return respuesta

            # ------------------------------------------------
            # RATE LIMIT — 429
            # ------------------------------------------------

            if respuesta.status_code == 429:

                retry_after = respuesta.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    try:

                        espera = float(
                            retry_after
                        )

                    except ValueError:

                        espera = (
                            BACKOFF_BASE
                            ** (intento + 1)
                        )

                else:

                    espera = (
                        BACKOFF_BASE
                        ** (intento + 1)
                    )

                if intento >= max_retries:

                    respuesta.raise_for_status()

                print(
                    f"    429 Too Many Requests "
                    f"→ esperando {espera:.1f}s "
                    f"(reintento {intento + 1}/{max_retries})"
                )

                time.sleep(
                    espera
                )

                continue

            # ------------------------------------------------
            # OTROS ERRORES HTTP
            # ------------------------------------------------

            respuesta.raise_for_status()

            return respuesta

        except requests.exceptions.RequestException as error:

            ultimo_error = error

            if intento >= max_retries:

                raise

            espera = (
                BACKOFF_BASE
                ** (intento + 1)
            )

            print(
                f"    Error temporal de API "
                f"→ esperando {espera:.1f}s "
                f"(reintento {intento + 1}/{max_retries})"
            )

            time.sleep(
                espera
            )

    if ultimo_error:

        raise ultimo_error

    raise RuntimeError(
        "No se pudo completar la request."
    )


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

    respuesta = request_get(
        API_URL,
        params
    )

    return respuesta.json()


# ============================================================
# OBTENER CUOTAS DE UN EVENTO
# ============================================================

def obtener_cuotas_evento(
    event_id
):

    api_key = obtener_api_key()

    params = {
        "apiKey": api_key,
        "eventId": event_id,
        "bookmakers": BOOKMAKER
    }

    respuesta = request_get(
        ODDS_URL,
        params
    )

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
            "local": float(
                cuota["home"]
            ),

            "empate": float(
                cuota["draw"]
            ),

            "visitante": float(
                cuota["away"]
            )
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

    local_busqueda = (
        local.lower()
    )

    visitante_busqueda = (
        visitante.lower()
    )

    for evento in eventos:

        home = str(
            evento.get(
                "home",
                ""
            )
        ).lower()

        away = str(
            evento.get(
                "away",
                ""
            )
        ).lower()

        if (
            local_busqueda in home
            and
            visitante_busqueda in away
        ):

            return evento

    return None


# ============================================================
# OBTENER CUOTAS POR EVENT ID
# ============================================================

def obtener_cuotas_por_event_id(
    event_id
):

    datos = obtener_cuotas_evento(
        event_id
    )

    cuotas = extraer_1x2(
        datos
    )

    if cuotas is None:

        return None

    return cuotas


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

    cuotas = obtener_cuotas_evento(
        evento["id"]
    )

    cuotas_1x2 = extraer_1x2(
        cuotas
    )

    if cuotas_1x2 is None:

        return None

    return {
        "event_id": evento["id"],
        "local": evento["home"],
        "visitante": evento["away"],
        "fecha": evento["date"],
        "estado": evento["status"],
        "bookmaker": BOOKMAKER,
        "cuotas": cuotas_1x2
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

    cuotas = resultado[
        "cuotas"
    ]

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
        f"Bookmaker: "
        f"{resultado['bookmaker']}"
    )

    print()
    print("CUOTAS 1X2")

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

    print("-" * 70)


if __name__ == "__main__":

    main()