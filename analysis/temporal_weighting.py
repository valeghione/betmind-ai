from database.database import Database
from analysis.poisson import calcular_probabilidades_partido


LEAGUE_ID = 128
SEASON_DEVELOPMENT = 2023
VENTANA = 5

ESQUEMAS = {
    "uniforme": [0.20, 0.20, 0.20, 0.20, 0.20],

    "leve": [0.30, 0.25, 0.20, 0.15, 0.10],

    "moderado": [0.40, 0.25, 0.15, 0.12, 0.08],

    "fuerte": [0.50, 0.20, 0.12, 0.10, 0.08]
}


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
    fecha_hasta,
    pesos
):

    seleccionados = obtener_ultimos_partidos(
        partidos,
        team_id,
        condicion,
        fecha_hasta
    )

    if len(seleccionados) < VENTANA:

        return None

    # Los partidos vienen del más antiguo al más reciente.
    # Los pesos están definidos de más reciente a más antiguo.
    pesos_ordenados = list(reversed(pesos))

    suma_pesos = sum(pesos_ordenados)

    if suma_pesos <= 0:

        return None

    promedio_gf = 0
    promedio_gc = 0

    for partido, peso in zip(
        seleccionados,
        pesos_ordenados
    ):

        if partido["home_team_id"] == team_id:

            goles_favor = partido["goles_local"]
            goles_contra = partido["goles_visitante"]

        else:

            goles_favor = partido["goles_visitante"]
            goles_contra = partido["goles_local"]

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
    partidos,
    pesos
):

    fecha_hasta = partido["fecha"]

    forma_local = calcular_forma_ponderada(
        partidos,
        partido["home_team_id"],
        "local",
        fecha_hasta,
        pesos
    )

    forma_visitante = calcular_forma_ponderada(
        partidos,
        partido["away_team_id"],
        "visitante",
        fecha_hasta,
        pesos
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


def evaluar_esquema(
    partidos,
    pesos
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
            pesos
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
        "partidos": len(resultados),
        "descartados": descartados,
        "aciertos": aciertos,
        "accuracy": accuracy,
        "brier": brier
    }


def main():

    partidos = obtener_partidos()

    print("=" * 75)
    print("PONDERACIÓN TEMPORAL — DESARROLLO 2023")
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

    for nombre, pesos in ESQUEMAS.items():

        resultado = evaluar_esquema(
            partidos,
            pesos
        )

        if resultado is None:

            continue

        resultados.append({
            "nombre": nombre,
            "pesos": pesos,
            **resultado
        })

    print(
        f"{'Esquema':<14}"
        f"{'Partidos':<12}"
        f"{'Accuracy':<15}"
        f"{'Brier':<12}"
    )

    print("-" * 75)

    for resultado in resultados:

        print(
            f"{resultado['nombre']:<14}"
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

    print("MEJOR ESQUEMA POR BRIER")

    print(
        f"Esquema: "
        f"{mejor_brier['nombre']}"
    )

    print(
        f"Pesos: "
        f"{mejor_brier['pesos']}"
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

    print("MEJOR ESQUEMA POR ACCURACY")

    print(
        f"Esquema: "
        f"{mejor_accuracy['nombre']}"
    )

    print(
        f"Pesos: "
        f"{mejor_accuracy['pesos']}"
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