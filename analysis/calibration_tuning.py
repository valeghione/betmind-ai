from database.database import Database
from analysis.backtest import ejecutar_backtest


VENTANA = 5

SEASON_TRAIN = 2023
SEASON_TEST = 2024

RESULTADOS = [
    "local",
    "empate",
    "visitante"
]

SMOOTHINGS = [
    1,
    5,
    10,
    20,
    30
]

NUM_BINS = 10


def obtener_partidos_historicos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


def crear_bins():

    bins = []

    for i in range(NUM_BINS):

        bins.append({
            "inferior": i / NUM_BINS,
            "superior": (i + 1) / NUM_BINS,
            "cantidad": 0,
            "suma_probabilidad": 0.0,
            "aciertos": 0
        })

    return bins


def obtener_bin(
    bins,
    probabilidad
):

    for i, bin_data in enumerate(bins):

        inferior = bin_data["inferior"]
        superior = bin_data["superior"]

        if i == NUM_BINS - 1:

            if (
                probabilidad >= inferior
                and
                probabilidad <= superior
            ):

                return bin_data

        else:

            if (
                probabilidad >= inferior
                and
                probabilidad < superior
            ):

                return bin_data

    return None


def construir_calibracion(
    resultados,
    resultado_objetivo
):

    bins = crear_bins()

    for resultado in resultados:

        probabilidades = (
            resultado["probabilidades"]
        )

        probabilidad = probabilidades[
            resultado_objetivo
        ]

        bin_data = obtener_bin(
            bins,
            probabilidad
        )

        if bin_data is None:

            continue

        bin_data["cantidad"] += 1

        bin_data["suma_probabilidad"] += (
            probabilidad
        )

        if (
            resultado["resultado_real"]
            ==
            resultado_objetivo
        ):

            bin_data["aciertos"] += 1

    return bins


def obtener_correccion(
    bins,
    probabilidad,
    smoothing
):

    bin_data = obtener_bin(
        bins,
        probabilidad
    )

    if bin_data is None:

        return probabilidad

    cantidad = bin_data["cantidad"]

    if cantidad == 0:

        return probabilidad

    promedio_modelo = (
        bin_data["suma_probabilidad"]
        /
        cantidad
    )

    frecuencia_real = (
        bin_data["aciertos"]
        /
        cantidad
    )

    peso_datos = (
        cantidad
        /
        (
            cantidad
            +
            smoothing
        )
    )

    probabilidad_calibrada = (
        peso_datos * frecuencia_real
        +
        (1 - peso_datos)
        * promedio_modelo
    )

    return probabilidad_calibrada


def calibrar_probabilidades(
    probabilidades,
    calibradores,
    smoothing
):

    calibradas = {}

    for resultado_objetivo in RESULTADOS:

        probabilidad = probabilidades[
            resultado_objetivo
        ]

        bins = calibradores[
            resultado_objetivo
        ]

        calibradas[
            resultado_objetivo
        ] = obtener_correccion(
            bins,
            probabilidad,
            smoothing
        )

    suma = sum(
        calibradas[resultado]
        for resultado in RESULTADOS
    )

    if suma <= 0:

        return probabilidades

    for resultado in RESULTADOS:

        calibradas[resultado] /= suma

    return calibradas


def separar_temporadas(resultados):

    train = []
    test = []

    for resultado in resultados:

        partido = resultado["partido"]

        temporada = partido["season"]

        if temporada == SEASON_TRAIN:

            train.append(resultado)

        elif temporada == SEASON_TEST:

            test.append(resultado)

    return train, test


def calcular_brier(resultados):

    if not resultados:

        return None

    suma = 0.0

    for resultado in resultados:

        probabilidades = (
            resultado["probabilidades"]
        )

        if (
            resultado["resultado_real"]
            ==
            "local"
        ):

            objetivo = [1, 0, 0]

        elif (
            resultado["resultado_real"]
            ==
            "empate"
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
                -
                objetivo[i]
            ) ** 2
            for i in range(3)
        )

    return suma / len(resultados)


def calcular_accuracy(resultados):

    if not resultados:

        return None

    aciertos = 0

    for resultado in resultados:

        probabilidades = (
            resultado["probabilidades"]
        )

        prob_local = probabilidades["local"]
        prob_empate = probabilidades["empate"]
        prob_visitante = probabilidades["visitante"]

        if (
            prob_local >= prob_empate
            and
            prob_local >= prob_visitante
        ):

            prediccion = "local"

        elif (
            prob_empate >= prob_local
            and
            prob_empate >= prob_visitante
        ):

            prediccion = "empate"

        else:

            prediccion = "visitante"

        if (
            prediccion
            ==
            resultado["resultado_real"]
        ):

            aciertos += 1

    return aciertos / len(resultados)


def aplicar_calibracion(
    resultados,
    calibradores,
    smoothing
):

    calibrados = []

    for resultado in resultados:

        probabilidades_originales = (
            resultado["probabilidades"]
        )

        probabilidades_calibradas = (
            calibrar_probabilidades(
                probabilidades_originales,
                calibradores,
                smoothing
            )
        )

        calibrados.append({
            "partido": resultado["partido"],
            "resultado_real":
                resultado["resultado_real"],
            "probabilidades":
                probabilidades_calibradas
        })

    return calibrados


def construir_calibradores(
    resultados_train
):

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        calibradores[
            resultado_objetivo
        ] = construir_calibracion(
            resultados_train,
            resultado_objetivo
        )

    return calibradores


def evaluar_smoothing(
    resultados_train,
    smoothing
):

    calibradores = construir_calibradores(
        resultados_train
    )

    calibrados = aplicar_calibracion(
        resultados_train,
        calibradores,
        smoothing
    )

    accuracy = calcular_accuracy(
        calibrados
    )

    brier = calcular_brier(
        calibrados
    )

    return accuracy, brier


def main():

    partidos = obtener_partidos_historicos()

    print("=" * 75)
    print(
        "TUNING DE SUAVIZADO — DESARROLLO 2023"
    )
    print("=" * 75)

    print()

    print(
        f"Partidos históricos disponibles: "
        f"{len(partidos)}"
    )

    print(
        f"Ventana: {VENTANA}"
    )

    print()

    print(
        "Ejecutando backtest V1..."
    )

    resultados, descartados = (
        ejecutar_backtest(
            partidos,
            ventana=VENTANA
        )
    )

    print()

    print(
        f"Resultados generados: "
        f"{len(resultados)}"
    )

    print(
        f"Partidos descartados: "
        f"{descartados}"
    )

    resultados_train, resultados_test = (
        separar_temporadas(
            resultados
        )
    )

    print()

    print(
        f"Resultados 2023: "
        f"{len(resultados_train)}"
    )

    print(
        f"Resultados 2024: "
        f"{len(resultados_test)}"
    )

    if not resultados_train:

        print(
            "No hay resultados de 2023."
        )

        return

    # ========================================================
    # TUNING SOLO EN 2023
    # ========================================================

    print()
    print("=" * 75)
    print(
        "RESULTADOS DEL TUNING — 2023"
    )
    print("=" * 75)

    print()

    print(
        f"{'Smoothing':<15}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 45)

    resultados_tuning = []

    for smoothing in SMOOTHINGS:

        accuracy, brier = evaluar_smoothing(
            resultados_train,
            smoothing
        )

        resultados_tuning.append({
            "smoothing": smoothing,
            "accuracy": accuracy,
            "brier": brier
        })

        print(
            f"{smoothing:<15}"
            f"{accuracy * 100:>7.2f}%"
            f"{'':<8}"
            f"{brier:.4f}"
        )

    # ========================================================
    # ELEGIR POR BRIER
    # ========================================================

    mejor_brier = min(
        resultados_tuning,
        key=lambda x: x["brier"]
    )

    mejor_accuracy = max(
        resultados_tuning,
        key=lambda x: x["accuracy"]
    )

    print()
    print("=" * 75)
    print("MEJOR SMOOTHING POR BRIER")
    print("=" * 75)

    print(
        f"Smoothing: "
        f"{mejor_brier['smoothing']}"
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
    print("=" * 75)
    print("MEJOR SMOOTHING POR ACCURACY")
    print("=" * 75)

    print(
        f"Smoothing: "
        f"{mejor_accuracy['smoothing']}"
    )

    print(
        f"Accuracy: "
        f"{mejor_accuracy['accuracy'] * 100:.2f}%"
    )

    print(
        f"Brier: "
        f"{mejor_accuracy['brier']:.4f}"
    )

    # ========================================================
    # NO TOCAR 2024
    # ========================================================

    print()
    print("=" * 75)
    print(
        "IMPORTANTE: 2024 NO SE UTILIZÓ "
        "PARA ELEGIR EL SMOOTHING"
    )
    print("=" * 75)

    print()
    print(
        "El mejor smoothing queda seleccionado "
        "exclusivamente con 2023."
    )

    print(
        f"Smoothing seleccionado por Brier: "
        f"{mejor_brier['smoothing']}"
    )

    print()
    print(
        "El siguiente paso será aplicar "
        "este único smoothing a 2024."
    )

    print("=" * 75)


if __name__ == "__main__":

    main()