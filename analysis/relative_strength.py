from database.database import Database
from analysis.poisson import calcular_probabilidades_partido


LEAGUE_ID = 128
SEASON_DEVELOPMENT = 2023
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


def obtener_promedios_liga(
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

        return None

    return {
        "promedio_local": (
            goles_local / cantidad
        ),
        "promedio_visitante": (
            goles_visitante / cantidad
        ),
        "partidos": cantidad
    }


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


def calcular_forma(
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

    goles_favor = 0
    goles_contra = 0

    for partido in seleccionados:

        if partido["home_team_id"] == team_id:

            goles_favor += partido["goles_local"]
            goles_contra += partido["goles_visitante"]

        else:

            goles_favor += partido["goles_visitante"]
            goles_contra += partido["goles_local"]

    return {
        "partidos": len(seleccionados),
        "promedio_gf": (
            goles_favor
            /
            len(seleccionados)
        ),
        "promedio_gc": (
            goles_contra
            /
            len(seleccionados)
        )
    }


def predecir_partido(
    partido,
    partidos
):

    fecha_hasta = partido["fecha"]

    forma_local = calcular_forma(
        partidos,
        partido["home_team_id"],
        "local",
        fecha_hasta
    )

    forma_visitante = calcular_forma(
        partidos,
        partido["away_team_id"],
        "visitante",
        fecha_hasta
    )

    if forma_local is None:
        return None

    if forma_visitante is None:
        return None

    promedios_liga = obtener_promedios_liga(
        partidos,
        fecha_hasta
    )

    if promedios_liga is None:
        return None

    promedio_local = (
        promedios_liga["promedio_local"]
    )

    promedio_visitante = (
        promedios_liga["promedio_visitante"]
    )

    if promedio_local <= 0:
        return None

    if promedio_visitante <= 0:
        return None

    # Fuerza ofensiva relativa del local
    ataque_local = (
        forma_local["promedio_gf"]
        /
        promedio_local
    )

    # Fuerza defensiva relativa del local.
    # < 1 significa que concede menos que
    # el promedio de la liga.
    defensa_local = (
        forma_local["promedio_gc"]
        /
        promedio_visitante
    )

    # Fuerza ofensiva relativa del visitante
    ataque_visitante = (
        forma_visitante["promedio_gf"]
        /
        promedio_visitante
    )

    # Fuerza defensiva relativa del visitante
    defensa_visitante = (
        forma_visitante["promedio_gc"]
        /
        promedio_local
    )

    # Goles esperados del local
    lambda_local = (
        promedio_local
        *
        ataque_local
        *
        defensa_visitante
    )

    # Goles esperados del visitante
    lambda_visitante = (
        promedio_visitante
        *
        ataque_visitante
        *
        defensa_local
    )

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
                prediccion[i]
                -
                objetivo[i]
            ) ** 2
            for i in range(3)
        )

    return suma / len(resultados)


def ejecutar_backtest(
    partidos
):

    partidos_test = [
        partido
        for partido in partidos
        if partido["season"]
        == SEASON_DEVELOPMENT
    ]

    resultados = []

    descartados = 0

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
            "probabilidades":
                probabilidades,
            "resultado_real":
                evaluacion["resultado_real"],
            "acierto":
                evaluacion["acierto"]
        })

    return resultados, descartados


def main():

    partidos = obtener_partidos()

    print("=" * 75)
    print(
        "FUERZAS RELATIVAS — DESARROLLO 2023"
    )
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

    resultados, descartados = (
        ejecutar_backtest(partidos)
    )

    print(
        f"Partidos válidos: "
        f"{len(resultados)}"
    )

    print(
        f"Partidos descartados: "
        f"{descartados}"
    )

    if not resultados:

        print("No hay resultados.")

        return

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
    print("-" * 75)
    print("PRIMEROS 10 RESULTADOS")
    print("-" * 75)

    for resultado in resultados[:10]:

        probabilidades = (
            resultado["probabilidades"]
        )

        print()

        print(
            f"Probabilidades: "
            f"L {probabilidades['local'] * 100:.1f}% | "
            f"E {probabilidades['empate'] * 100:.1f}% | "
            f"V {probabilidades['visitante'] * 100:.1f}%"
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
    print("=" * 75)


if __name__ == "__main__":
    main()