from database.database import Database
from analysis.analyzer import analizar_forma_equipo
from analysis.poisson_v2 import calcular_probabilidades_partido


LEAGUE_ID = 128
SEASON_TEST = 2024
VENTANA = 5


def obtener_partidos():

    db = Database()

    db.cursor.execute("""
        SELECT *
        FROM matches
        WHERE league_id = ?
          AND estado = 'FT'
        ORDER BY fecha ASC
    """, (
        LEAGUE_ID,
    ))

    partidos = db.cursor.fetchall()

    db.cerrar()

    return partidos


def calcular_ventaja_local(
    partidos,
    fecha_hasta
):

    goles_local = 0
    goles_visitante = 0

    cantidad = 0

    for partido in partidos:

        if partido["fecha"] >= fecha_hasta:
            continue

        if partido["estado"] != "FT":
            continue

        goles_local_partido = partido["goles_local"]
        goles_visitante_partido = partido["goles_visitante"]

        goles_local += goles_local_partido
        goles_visitante += goles_visitante_partido

        cantidad += 1

    if cantidad == 0:
        return 1.0

    promedio_local = (
        goles_local / cantidad
    )

    promedio_visitante = (
        goles_visitante / cantidad
    )

    if promedio_visitante <= 0:
        return 1.0

    ventaja = (
        promedio_local
        /
        promedio_visitante
    )

    return ventaja


def predecir_partido(partido, partidos):

    fecha_hasta = partido["fecha"]

    forma_local = analizar_forma_equipo(
        partido["home_team_id"],
        limite=VENTANA,
        condicion="local",
        fecha_hasta=fecha_hasta
    )

    forma_visitante = analizar_forma_equipo(
        partido["away_team_id"],
        limite=VENTANA,
        condicion="visitante",
        fecha_hasta=fecha_hasta
    )

    if forma_local is None:
        return None

    if forma_visitante is None:
        return None

    if forma_local["partidos"] < VENTANA:
        return None

    if forma_visitante["partidos"] < VENTANA:
        return None

    ventaja_local = calcular_ventaja_local(
        partidos,
        fecha_hasta
    )

    lambda_local = (
        (
            forma_local["promedio_gf"]
            +
            forma_visitante["promedio_gc"]
        )
        /
        2
    )

    lambda_visitante = (
        (
            forma_visitante["promedio_gf"]
            +
            forma_local["promedio_gc"]
        )
        /
        2
    )

    lambda_local *= ventaja_local

    probabilidades = calcular_probabilidades_partido(
        lambda_local,
        lambda_visitante
    )

    return probabilidades


def evaluar_partido(
    partido,
    probabilidades
):

    goles_local = partido["goles_local"]
    goles_visitante = partido["goles_visitante"]

    if goles_local > goles_visitante:

        resultado_real = "local"

    elif goles_local == goles_visitante:

        resultado_real = "empate"

    else:

        resultado_real = "visitante"

    predicciones = {
        "local": probabilidades["local"],
        "empate": probabilidades["empate"],
        "visitante": probabilidades["visitante"]
    }

    prediccion = max(
        predicciones,
        key=predicciones.get
    )

    return {
        "resultado_real": resultado_real,
        "prediccion": prediccion,
        "acierto": prediccion == resultado_real
    }


def calcular_brier(resultados):

    if not resultados:
        return None

    suma = 0

    for resultado in resultados:

        probabilidades = resultado["probabilidades"]

        if resultado["resultado_real"] == "local":

            objetivo = [1, 0, 0]

        elif resultado["resultado_real"] == "empate":

            objetivo = [0, 1, 0]

        else:

            objetivo = [0, 0, 1]

        prediccion = [
            probabilidades["local"],
            probabilidades["empate"],
            probabilidades["visitante"]
        ]

        suma += sum(
            (
                prediccion[i] - objetivo[i]
            ) ** 2
            for i in range(3)
        )

    return suma / len(resultados)


def ejecutar_backtest(partidos):

    partidos_test = [
        partido
        for partido in partidos
        if partido["season"] == SEASON_TEST
    ]

    resultados = []

    descartados = 0

    print(
        f"Partidos de test "
        f"(temporada {SEASON_TEST}): "
        f"{len(partidos_test)}"
    )

    print()

    for partido in partidos_test:

        probabilidades = predecir_partido(
            partido,
            partidos
        )

        if probabilidades is None:

            descartados += 1

            continue

        evaluacion = evaluar_partido(
            partido,
            probabilidades
        )

        resultados.append({
            "partido": partido,
            "probabilidades": probabilidades,
            "resultado_real":
                evaluacion["resultado_real"],
            "prediccion":
                evaluacion["prediccion"],
            "acierto":
                evaluacion["acierto"]
        })

    return resultados, descartados


def mostrar_resultados(
    resultados,
    descartados
):

    print()
    print("=" * 65)
    print("POISSON V2 — VENTAJA DE LOCALÍA")
    print("=" * 65)

    print()

    print(
        f"Partidos válidos: "
        f"{len(resultados)}"
    )

    print(
        f"Partidos descartados: "
        f"{descartados}"
    )

    if not resultados:

        print()
        print("No hay suficientes datos.")

        return

    aciertos = sum(
        1
        for resultado in resultados
        if resultado["acierto"]
    )

    cantidad = len(resultados)

    accuracy = aciertos / cantidad

    brier = calcular_brier(resultados)

    print()

    print(
        f"Aciertos 1X2: "
        f"{aciertos}"
    )

    print(
        f"Accuracy 1X2: "
        f"{accuracy * 100:.2f}%"
    )

    print(
        f"Brier Score: "
        f"{brier:.4f}"
    )

    print()
    print("-" * 65)
    print("PRIMEROS 10 RESULTADOS")
    print("-" * 65)

    for resultado in resultados[:10]:

        partido = resultado["partido"]

        probabilidades = resultado["probabilidades"]

        print()

        print(
            f"{partido['local']} "
            f"vs "
            f"{partido['visitante']}"
        )

        print(
            f"Fecha: "
            f"{partido['fecha']}"
        )

        print(
            f"Probabilidades: "
            f"L {probabilidades['local'] * 100:.1f}% | "
            f"E {probabilidades['empate'] * 100:.1f}% | "
            f"V {probabilidades['visitante'] * 100:.1f}%"
        )

        print(
            f"Modelo: "
            f"{resultado['prediccion']}"
        )

        print(
            f"Real: "
            f"{resultado['resultado_real']}"
        )

        print(
            f"Acierto: "
            f"{'SI' if resultado['acierto'] else 'NO'}"
        )

    print()
    print("=" * 65)


def main():

    partidos = obtener_partidos()

    print("=" * 65)
    print("BACKTEST TEMPORAL V2")
    print("=" * 65)

    print()

    print(
        f"Partidos históricos disponibles: "
        f"{len(partidos)}"
    )

    print(
        f"Liga utilizada: "
        f"{LEAGUE_ID}"
    )

    print(
        f"Temporada de TEST: "
        f"{SEASON_TEST}"
    )

    print()

    resultados, descartados = ejecutar_backtest(
        partidos
    )

    mostrar_resultados(
        resultados,
        descartados
    )


if __name__ == "__main__":
    main()