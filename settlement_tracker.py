import os
import requests

from dotenv import load_dotenv

from database.database import Database

from database.odds_repository import (
    guardar_resultado,
    obtener_values,
    actualizar_value
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

EVENTS_URL = (
    "https://api.odds-api.io/v3/events"
)

SPORT = "football"

LEAGUE = (
    "argentina-primera-lpf-clausura"
)


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
# DETERMINAR RESULTADO
# ============================================================

def determinar_resultado(
    goles_local,
    goles_visitante
):

    if goles_local > goles_visitante:

        return "local"

    if goles_local == goles_visitante:

        return "empate"

    return "visitante"


# ============================================================
# OBTENER RESULTADO DEL EVENTO
# ============================================================

def obtener_resultado_evento(
    evento
):

    status = str(
        evento.get(
            "status",
            ""
        )
    ).lower()

    estados_finales = (
        "settled",
        "finished",
        "completed"
    )

    if status not in estados_finales:

        return None

    scores = evento.get(
        "scores"
    )

    if not scores:

        return None

    ft = scores.get(
        "ft"
    )

    if not ft:

        return None

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

        return None

    return {
        "goles_local":
            goles_local,

        "goles_visitante":
            goles_visitante,

        "resultado":
            determinar_resultado(
                goles_local,
                goles_visitante
            )
    }


# ============================================================
# CALCULAR GANANCIA
# ============================================================

def calcular_ganancia(
    mercado,
    resultado_real,
    cuota
):

    # Apuesta hipotética de 1 unidad.

    if mercado == resultado_real:

        return cuota - 1.0

    return -1.0


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print(
        "BETMIND AI — SETTLEMENT TRACKER"
    )
    print("=" * 80)

    print()

    try:

        eventos = obtener_eventos()

    except Exception as error:

        print(
            "ERROR OBTENIENDO EVENTOS:"
        )

        print(error)

        return

    eventos_map = {}

    for evento in eventos:

        eventos_map[
            evento["id"]
        ] = evento

    values = obtener_values()

    print(
        f"Eventos recibidos: "
        f"{len(eventos)}"
    )

    print(
        f"Values registrados: "
        f"{len(values)}"
    )

    print()

    procesados = 0
    pendientes = 0
    liquidados = 0
    no_encontrados = 0
    errores = 0

    # ========================================================
    # PROCESAR VALUES
    # ========================================================

    for value in values:

        # Ya liquidado

        if value["resultado"] is not None:

            continue

        procesados += 1

        event_id = value["event_id"]

        evento = eventos_map.get(
            event_id
        )

        if evento is None:

            print(
                f"[{event_id}] "
                f"No está en eventos actuales"
            )

            no_encontrados += 1

            continue

        print(
            f"[{event_id}] "
            f"{value['local']} vs "
            f"{value['visitante']}"
        )

        resultado_evento = (
            obtener_resultado_evento(
                evento
            )
        )

        if resultado_evento is None:

            print(
                "  → PENDIENTE"
            )

            pendientes += 1

            continue

        resultado_real = (
            resultado_evento[
                "resultado"
            ]
        )

        goles_local = (
            resultado_evento[
                "goles_local"
            ]
        )

        goles_visitante = (
            resultado_evento[
                "goles_visitante"
            ]
        )

        # ----------------------------------------------------
        # GANANCIA
        # ----------------------------------------------------

        ganancia = calcular_ganancia(

            value["mercado"],

            resultado_real,

            value["cuota"]
        )

        if value["mercado"] == resultado_real:

            estado = "WIN"

        else:

            estado = "LOSS"

        actualizar_value(

            value_id=value["id"],

            resultado=estado,

            ganancia=ganancia
        )

        print(
            f"  Resultado: "
            f"{goles_local}-"
            f"{goles_visitante}"
        )

        print(
            f"  Mercado: "
            f"{value['mercado']}"
        )

        print(
            f"  Cuota: "
            f"{value['cuota']:.2f}"
        )

        print(
            f"  EV registrado: "
            f"{value['ev'] * 100:.2f}%"
        )

        print(
            f"  → {estado}"
        )

        print(
            f"  Ganancia: "
            f"{ganancia:+.2f} unidades"
        )

        print()

        liquidados += 1

        # Guardamos también resultado general

        try:

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

        except Exception as error:

            print(
                f"  WARNING resultado: "
                f"{error}"
            )

            errores += 1

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    db = Database()

    db.cursor.execute("""
        SELECT
            COUNT(*) AS total,

            SUM(
                CASE
                    WHEN resultado = 'WIN'
                    THEN 1
                    ELSE 0
                END
            ) AS wins,

            SUM(
                CASE
                    WHEN resultado = 'LOSS'
                    THEN 1
                    ELSE 0
                END
            ) AS losses,

            COALESCE(
                SUM(ganancia),
                0
            ) AS ganancia

        FROM value_opportunities
        WHERE resultado IS NOT NULL
    """)

    estadisticas = (
        db.cursor.fetchone()
    )

    db.cerrar()

    total = (
        estadisticas["total"]
        or 0
    )

    wins = (
        estadisticas["wins"]
        or 0
    )

    losses = (
        estadisticas["losses"]
        or 0
    )

    ganancia_total = (
        estadisticas["ganancia"]
        or 0.0
    )

    if total > 0:

        winrate = (
            wins / total
        )

        roi = (
            ganancia_total / total
        )

    else:

        winrate = 0.0
        roi = 0.0

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print("=" * 80)
    print("RESUMEN DE SETTLEMENT")
    print("=" * 80)

    print()

    print(
        f"Values procesados: "
        f"{procesados}"
    )

    print(
        f"Liquidaciones nuevas: "
        f"{liquidados}"
    )

    print(
        f"Pendientes: "
        f"{pendientes}"
    )

    print(
        f"No encontrados: "
        f"{no_encontrados}"
    )

    print(
        f"Errores: "
        f"{errores}"
    )

    print()

    print(
        "========================================"
    )

    print(
        f"Apuestas liquidadas: "
        f"{total}"
    )

    print(
        f"WIN:                  "
        f"{wins}"
    )

    print(
        f"LOSS:                 "
        f"{losses}"
    )

    print(
        f"Win rate:             "
        f"{winrate * 100:.2f}%"
    )

    print(
        f"Ganancia:             "
        f"{ganancia_total:+.2f} u."
    )

    print(
        f"ROI:                  "
        f"{roi * 100:+.2f}%"
    )

    print(
        "========================================"
    )

    print()


if __name__ == "__main__":

    main()