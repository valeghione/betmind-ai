from database.database import Database


ALPHA = 1.0


def obtener_partidos_historicos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


def calcular_frecuencias_suavizadas(
    partidos,
    fecha_hasta
):

    local = 0
    empate = 0
    visitante = 0

    total = 0

    for partido in partidos:

        if partido["fecha"] >= fecha_hasta:
            continue

        goles_local = partido["goles_local"]
        goles_visitante = partido["goles_visitante"]

        if goles_local > goles_visitante:

            local += 1

        elif goles_local == goles_visitante:

            empate += 1

        else:

            visitante += 1

        total += 1

    denominador = total + (3 * ALPHA)

    return {
        "local": (local + ALPHA) / denominador,
        "empate": (empate + ALPHA) / denominador,
        "visitante": (visitante + ALPHA) / denominador
    }


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


def ejecutar_baseline(partidos):

    resultados = []

    for partido in partidos:

        probabilidades = calcular_frecuencias_suavizadas(
            partidos,
            partido["fecha"]
        )

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

    return resultados


def mostrar_resultados(resultados):

    print()
    print("=" * 60)
    print("BASELINE HISTÓRICO SUAVIZADO")
    print("=" * 60)

    print()

    print(
        f"Alpha utilizado: "
        f"{ALPHA}"
    )

    print(
        f"Partidos analizados: "
        f"{len(resultados)}"
    )

    if not resultados:

        print("No hay resultados.")

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
    print("-" * 60)
    print("PRIMEROS RESULTADOS")
    print("-" * 60)

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
    print("=" * 60)


def main():

    partidos = obtener_partidos_historicos()

    print(
        f"Partidos disponibles: "
        f"{len(partidos)}"
    )

    resultados = ejecutar_baseline(
        partidos
    )

    mostrar_resultados(
        resultados
    )


if __name__ == "__main__":
    main()