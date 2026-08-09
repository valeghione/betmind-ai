from database.database import Database
from analysis.analyzer import analizar_forma_equipo
from analysis.match_analyzer import calcular_goles_esperados
from analysis.poisson import calcular_probabilidades_partido


MINIMO_PARTIDOS = 5
VENTANAS = [5, 10, 15]


def obtener_partidos_historicos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


def predecir_partido(partido, ventana):

    local_id = partido["home_team_id"]
    visitante_id = partido["away_team_id"]

    fecha_hasta = partido["fecha"]

    forma_local = analizar_forma_equipo(
        local_id,
        limite=ventana,
        condicion="local",
        fecha_hasta=fecha_hasta
    )

    forma_visitante = analizar_forma_equipo(
        visitante_id,
        limite=ventana,
        condicion="visitante",
        fecha_hasta=fecha_hasta
    )

    if forma_local is None or forma_visitante is None:
        return None

    if forma_local["partidos"] < ventana:
        return None

    if forma_visitante["partidos"] < ventana:
        return None

    goles_esperados = calcular_goles_esperados(
        forma_local,
        forma_visitante
    )

    probabilidades = calcular_probabilidades_partido(
        goles_esperados["local"],
        goles_esperados["visitante"]
    )

    return probabilidades


def evaluar_resultado(partido, probabilidades):

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

    acierto = prediccion == resultado_real

    return {
        "resultado_real": resultado_real,
        "prediccion": prediccion,
        "acierto": acierto
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


def ejecutar_backtest(partidos, ventana):

    resultados = []

    descartados = 0

    for partido in partidos:

        probabilidades = predecir_partido(
            partido,
            ventana
        )

        if probabilidades is None:

            descartados += 1

            continue

        evaluacion = evaluar_resultado(
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


def mostrar_resumen(
    ventana,
    resultados,
    descartados
):

    cantidad = len(resultados)

    print()
    print("=" * 60)
    print(f"VENTANA DE {ventana} PARTIDOS")
    print("=" * 60)

    print()

    print(
        f"Partidos válidos: {cantidad}"
    )

    print(
        f"Partidos descartados: {descartados}"
    )

    if cantidad == 0:

        print("No hay suficientes datos.")

        return

    aciertos = sum(
        1
        for resultado in resultados
        if resultado["acierto"]
    )

    accuracy = aciertos / cantidad

    brier = calcular_brier(resultados)

    print(
        f"Aciertos 1X2: {aciertos}"
    )

    print(
        f"Accuracy 1X2: "
        f"{accuracy * 100:.2f}%"
    )

    print(
        f"Brier Score: "
        f"{brier:.4f}"
    )


def main():

    partidos = obtener_partidos_historicos()

    print("=" * 60)
    print("COMPARACIÓN DE VENTANAS")
    print("=" * 60)

    print()
    print(
        f"Partidos disponibles en SQLite: "
        f"{len(partidos)}"
    )

    for ventana in VENTANAS:

        print()
        print(
            f"Ejecutando ventana de "
            f"{ventana} partidos..."
        )

        resultados, descartados = ejecutar_backtest(
            partidos,
            ventana
        )

        mostrar_resumen(
            ventana,
            resultados,
            descartados
        )

    print()
    print("=" * 60)
    print("FIN DEL BACKTEST")
    print("=" * 60)


if __name__ == "__main__":
    main()