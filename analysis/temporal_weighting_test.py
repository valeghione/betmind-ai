from database.database import Database
from analysis.poisson import calcular_probabilidades_partido


LEAGUE_ID = 128
SEASON_TEST = 2024
VENTANA = 5

PESOS_FUERTE = [
    0.50,
    0.20,
    0.12,
    0.10,
    0.08
]


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


def obtener_ultimos_partidos(
    partidos,
    team_id,
    condicion,
    fecha_hasta
):

    seleccionados = []

    for partido in partidos:

        if partido["fecha"] >= fecha_hasta:
            continue

        if condicion == "local":

            if partido["home_team_id"] != team_id:
                continue

        elif condicion == "visitante":

            if partido["away_team_id"] != team_id:
                continue

        else:

            if (
                partido["home_team_id"] != team_id
                and
                partido["away_team_id"] != team_id
            ):
                continue

        seleccionados.append(partido)

    return seleccionados[-VENTANA:]


def calcular_forma_ponderada(
    partidos,
    team_id,
    condicion,
    fecha_hasta
):

    seleccionados = obtener_ultimos_partidos(
        partidos,
        team_id,
        condicion,
        fecha_hasta
    )

    if len(seleccionados) < VENTANA:

        return None

    # Los partidos vienen del más antiguo
    # al más reciente.
    #
    # Los pesos están definidos desde
    # el más reciente al más antiguo.

    pesos_ordenados = list(
        reversed(PESOS_FUERTE)
    )

    suma_pesos = sum(
        pesos_ordenados
    )

    promedio_gf = 0
    promedio_gc = 0

    for partido, peso in zip(
        seleccionados,
        pesos_ordenados
    ):

        if partido["home_team_id"] == team_id:

            goles_favor = (
                partido["goles_local"]
            )

            goles_contra = (
                partido["goles_visitante"]
            )

        else:

            goles_favor = (
                partido["goles_visitante"]
            )

            goles_contra = (
                partido["goles_local"]
            )

        promedio_gf += (
            goles_favor * peso
        )

        promedio_gc += (
            goles_contra * peso
        )

    promedio_gf /= suma_pesos
    promedio_gc /= suma_pesos

    return {
        "partidos": len(seleccionados),
        "promedio_gf": promedio_gf,
        "promedio_gc": promedio_gc
    }


def predecir_partido(
    partido,
    partidos
):

    fecha_hasta = partido["fecha"]

    forma_local = calcular_forma_ponderada(
        partidos,
        partido["home_team_id"],
        "local",
        fecha_hasta
    )

    forma_visitante = calcular_forma_ponderada(
        partidos,
        partido["away_team_id"],
        "visitante",
        fecha_hasta
    )

    if forma_local is None:

        return None

    if forma_visitante is None:

        return None

    lambda_local = (
        forma_local["promedio_gf"]
        +
        forma_visitante["promedio_gc"]
    ) / 2

    lambda_visitante = (
        forma_visitante["promedio_gf"]
        +
        forma_local["promedio_gc"]
    ) / 2

    return calcular_probabilidades_partido(
        lambda_local,
        lambda_visitante
    )


def evaluar_partido(
    partido,
    probabilidades
):

    goles_local = (
        partido["goles_local"]
    )

    goles_visitante = (
        partido["goles_visitante"]
    )

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
        "acierto": (
            prediccion == resultado_real
        )
    }


def calcular_brier(resultados):

    if not resultados:

        return None

    suma = 0

    for resultado in resultados:

        probabilidades = (
            resultado["probabilidades"]
        )

        if (
            resultado["resultado_real"]
            == "local"
        ):

            objetivo = [1, 0, 0]

        elif (
            resultado["resultado_real"]
            == "empate"
        ):

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
                prediccion[i]
                - objetivo[i]
            ) ** 2
            for i in range(3)
        )

    return suma / len(resultados)


def ejecutar_test(partidos):

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
    print("=" * 70)
    print(
        "TEST TEMPORAL — PONDERACIÓN FUERTE"
    )
    print("=" * 70)

    print()

    print(
        "Pesos utilizados:"
    )

    print(
        "[0.50, 0.20, 0.12, 0.10, 0.08]"
    )

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
        print(
            "No hay suficientes datos."
        )

        return

    aciertos = sum(
        1
        for resultado in resultados
        if resultado["acierto"]
    )

    cantidad = len(resultados)

    accuracy = (
        aciertos
        /
        cantidad
    )

    brier = calcular_brier(
        resultados
    )

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
    print("-" * 70)
    print("PRIMEROS 10 RESULTADOS")
    print("-" * 70)

    for resultado in resultados[:10]:

        partido = resultado["partido"]

        probabilidades = (
            resultado["probabilidades"]
        )

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
    print("=" * 70)


def main():

    partidos = obtener_partidos()

    print("=" * 70)
    print(
        "BACKTEST TEMPORAL — PONDERACIÓN"
    )
    print("=" * 70)

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

    resultados, descartados = (
        ejecutar_test(partidos)
    )

    mostrar_resultados(
        resultados,
        descartados
    )


if __name__ == "__main__":

    main()