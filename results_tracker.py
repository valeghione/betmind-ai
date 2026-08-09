import os
import requests

from dotenv import load_dotenv

from database.odds_repository import (
    guardar_resultado,
    obtener_snapshots
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

EVENTS_URL = "https://api.odds-api.io/v3/events"

SPORT = "football"

LEAGUE = "argentina-primera-lpf-clausura"


# ============================================================
# API KEY
# ============================================================

def obtener_api_key():

    load_dotenv()

    api_key = os.getenv(
        "ODDS_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "No se encontró ODDS_API_KEY en .env"
        )

    return api_key


# ============================================================
# OBTENER EVENTOS
# ============================================================

def obtener_eventos():

    api_key = obtener_api_key()

    respuesta = requests.get(
        EVENTS_URL,
        params={
            "apiKey": api_key,
            "sport": SPORT,
            "league": LEAGUE,
            "limit": 50
        },
        timeout=15
    )

    respuesta.raise_for_status()

    return respuesta.json()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("BETMIND AI — RESULTS TRACKER")
    print("=" * 80)

    print()

    snapshots = obtener_snapshots()

    if not snapshots:

        print(
            "No hay snapshots almacenados."
        )

        return

    # ========================================================
    # EVENTOS
    # ========================================================

    print(
        "Consultando eventos..."
    )

    try:

        eventos = obtener_eventos()

    except Exception as error:

        print(
            "ERROR obteniendo eventos:"
        )

        print(error)

        return

    # ========================================================
    # MAPA
    # ========================================================

    eventos_map = {}

    for evento in eventos:

        eventos_map[
            evento["id"]
        ] = evento

    print(
        f"Eventos recibidos: "
        f"{len(eventos)}"
    )

    print(
        f"Snapshots almacenados: "
        f"{len(snapshots)}"
    )

    print()

    encontrados = 0
    guardados = 0
    pendientes = 0
    errores = 0

    procesados = set()

    # ========================================================
    # PROCESAR
    # ========================================================

    for snapshot in snapshots:

        event_id = snapshot["event_id"]

        # Evitar procesar varias veces
        # el mismo evento.

        if event_id in procesados:

            continue

        procesados.add(event_id)

        evento = eventos_map.get(
            event_id
        )

        if evento is None:

            print(
                f"[{event_id}] "
                f"No encontrado en eventos actuales"
            )

            continue

        encontrados += 1

        estado = str(
            evento.get(
                "status",
                ""
            )
        ).lower()

        print(
            f"[{event_id}] "
            f"{evento['home']} vs "
            f"{evento['away']}"
        )

        # ====================================================
        # TERMINADO
        # ====================================================

        if estado in (
            "settled",
            "finished",
            "completed"
        ):

            scores = evento.get(
                "scores"
            )

            if not scores:

                print(
                    "  RESULTADO: "
                    "sin marcador"
                )

                errores += 1

                continue

            ft = scores.get(
                "ft"
            )

            if not ft:

                print(
                    "  RESULTADO: "
                    "sin FT"
                )

                errores += 1

                continue

            goles_local = ft.get(
                "home"
            )

            goles_visitante = ft.get(
                "away"
            )

            if (
                goles_local is None
                or
                goles_visitante is None
            ):

                print(
                    "  RESULTADO: "
                    "marcador inválido"
                )

                errores += 1

                continue

            guardar_resultado(

                event_id=event_id,

                fecha_evento=
                    evento["date"],

                local=
                    evento["home"],

                visitante=
                    evento["away"],

                goles_local=
                    goles_local,

                goles_visitante=
                    goles_visitante
            )

            resultado = (
                "LOCAL"
                if goles_local > goles_visitante
                else
                "EMPATE"
                if goles_local == goles_visitante
                else
                "VISITANTE"
            )

            print(
                f"  RESULTADO: "
                f"{goles_local}-{goles_visitante}"
            )

            print(
                f"  → {resultado}"
            )

            guardados += 1

        else:

            print(
                f"  Estado: {estado}"
            )

            print(
                "  → Todavía pendiente"
            )

            pendientes += 1

    # ========================================================
    # RESUMEN
    # ========================================================

    print()

    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)

    print()

    print(
        f"Snapshots:     {len(snapshots)}"
    )

    print(
        f"Encontrados:   {encontrados}"
    )

    print(
        f"Resultados:    {guardados}"
    )

    print(
        f"Pendientes:    {pendientes}"
    )

    print(
        f"Errores:       {errores}"
    )

    print()

    print("=" * 80)


if __name__ == "__main__":

    main()