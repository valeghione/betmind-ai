from database.database import Database
from analysis.analyzer import analizar_forma_equipo
from analysis.poisson_v2 import calcular_probabilidades_partido


LEAGUE_ID = 128
SEASON_DEVELOPMENT = 2023
VENTANA = 5

FACTORES = [
     0.00,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    1.00
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


def calcular_ventaja_local_base(
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

        goles_local += partido["goles_local"]
        goles_visitante += partido["goles_visitante"]

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

    return (
        promedio_local
        /
        promedio_visitante
    )


def predecir_partido(
    partido,
    partidos,
    factor_localia
):

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

    ventaja_base = calcular_ventaja_local_base(
        partidos,
        fecha_hasta
    )

    # En lugar de aplicar toda la ventaja histórica,
    # controlamos su intensidad mediante el factor.
    ventaja_controlada = (
        1.0
        +
        (
            ventaja_base - 1.0
        )
        *
        factor_localia
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

    lambda_local *= ventaja_controlada

    return calcular_probabilidades_partido(
        lambda_local,
        lambda_visitante
    )


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


def evaluar_factor(
    partidos,
    factor_localia
):

    partidos_desarrollo = [
        partido
        for partido in partidos
        if partido["season"] == SEASON_DEVELOPMENT
    ]

    resultados = []

    descartados = 0

    for partido in partidos_desarrollo:

        probabilidades = predecir_partido(
            partido,
            partidos,
            factor_localia
        )

        if probabilidades is None:

            descartados += 1

            continue

        evaluacion = evaluar_partido(
            partido,
            probabilidades
        )

        resultados.append({
            "probabilidades": probabilidades,
            "resultado_real":
                evaluacion["resultado_real"],
            "acierto":
                evaluacion["acierto"]
        })

    if not resultados:

        return None

    aciertos = sum(
        1
        for resultado in resultados
        if resultado["acierto"]
    )

    accuracy = (
        aciertos
        /
        len(resultados)
    )

    brier = calcular_brier(
        resultados
    )

    return {
        "factor": factor_localia,
        "partidos": len(resultados),
        "descartados": descartados,
        "aciertos": aciertos,
        "accuracy": accuracy,
        "brier": brier
    }


def main():

    partidos = obtener_partidos()

    print("=" * 75)
    print("TUNING DE LOCALÍA — DESARROLLO 2023")
    print("=" * 75)

    print()

    print(
        f"Partidos históricos disponibles: "
        f"{len(partidos)}"
    )

    print(
        f"Liga: {LEAGUE_ID}"
    )

    print(
        f"Temporada de desarrollo: "
        f"{SEASON_DEVELOPMENT}"
    )

    print(
        f"Ventana: {VENTANA}"
    )

    print()

    resultados = []

    for factor in FACTORES:

        resultado = evaluar_factor(
            partidos,
            factor
        )

        if resultado is None:
            continue

        resultados.append(resultado)

    print(
        f"{'Factor':<12}"
        f"{'Partidos':<12}"
        f"{'Accuracy':<15}"
        f"{'Brier':<12}"
    )

    print("-" * 75)

    for resultado in resultados:

        print(
            f"{resultado['factor']:<12.2f}"
            f"{resultado['partidos']:<12}"
            f"{resultado['accuracy'] * 100:>7.2f}%"
            f"{'':<7}"
            f"{resultado['brier']:.4f}"
        )

    if not resultados:

        print()
        print("No se obtuvieron resultados.")

        return

    mejor_brier = min(
        resultados,
        key=lambda x: x["brier"]
    )

    mejor_accuracy = max(
        resultados,
        key=lambda x: x["accuracy"]
    )

    print()
    print("=" * 75)

    print(
        "MEJOR FACTOR POR BRIER"
    )

    print(
        f"Factor: "
        f"{mejor_brier['factor']:.2f}"
    )

    print(
        f"Accuracy: "
        f"{mejor_brier['accuracy'] * 100:.2f}%"
    )

    print(
        f"Brier: "
        f"{mejor_brier['brier']:.4f}"
    )

    print()

    print(
        "MEJOR FACTOR POR ACCURACY"
    )

    print(
        f"Factor: "
        f"{mejor_accuracy['factor']:.2f}"
    )

    print(
        f"Accuracy: "
        f"{mejor_accuracy['accuracy'] * 100:.2f}%"
    )

    print(
        f"Brier: "
        f"{mejor_accuracy['brier']:.4f}"
    )

    print("=" * 75)


if __name__ == "__main__":
    main()