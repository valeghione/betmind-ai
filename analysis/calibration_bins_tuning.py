from database.database import Database
from analysis.backtest import ejecutar_backtest


VENTANA = 5

SEASON_TRAIN = 2023
SEASON_TEST = 2024

SMOOTHING = 1

NUM_BINS_OPTIONS = [
    5,
    8,
    10,
    15,
    20
]

RESULTADOS = [
    "local",
    "empate",
    "visitante"
]


def obtener_partidos_historicos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


def crear_bins(num_bins):

    bins = []

    for i in range(num_bins):

        bins.append({
            "inferior": i / num_bins,
            "superior": (i + 1) / num_bins,
            "cantidad": 0,
            "suma_probabilidad": 0.0,
            "aciertos": 0
        })

    return bins


def obtener_bin(
    bins,
    probabilidad
):

    num_bins = len(bins)

    for i, bin_data in enumerate(bins):

        inferior = bin_data["inferior"]
        superior = bin_data["superior"]

        if i == num_bins - 1:

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
    resultado_objetivo,
    num_bins
):

    bins = crear_bins(num_bins)

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


def construir_calibradores(
    resultados,
    num_bins
):

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        calibradores[
            resultado_objetivo
        ] = construir_calibracion(
            resultados,
            resultado_objetivo,
            num_bins
        )

    return calibradores


def obtener_correccion(
    bins,
    probabilidad
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
            SMOOTHING
        )
    )

    return (
        peso_datos * frecuencia_real
        +
        (1 - peso_datos)
        * promedio_modelo
    )


def calibrar_probabilidades(
    probabilidades,
    calibradores
):

    calibradas = {}

    for resultado_objetivo in RESULTADOS:

        original = probabilidades[
            resultado_objetivo
        ]

        calibradas[
            resultado_objetivo
        ] = obtener_correccion(
            calibradores[
                resultado_objetivo
            ],
            original
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

        temporada = resultado[
            "partido"
        ]["season"]

        if temporada == SEASON_TRAIN:

            train.append(resultado)

        elif temporada == SEASON_TEST:

            test.append(resultado)

    return train, test


def aplicar_calibracion(
    resultados,
    calibradores
):

    nuevos = []

    for resultado in resultados:

        probabilidades = (
            resultado["probabilidades"]
        )

        calibradas = calibrar_probabilidades(
            probabilidades,
            calibradores
        )

        nuevos.append({
            "partido": resultado["partido"],
            "resultado_real":
                resultado["resultado_real"],
            "probabilidades":
                calibradas
        })

    return nuevos


def calcular_accuracy(resultados):

    if not resultados:

        return None

    aciertos = 0

    for resultado in resultados:

        probabilidades = (
            resultado["probabilidades"]
        )

        prediccion = max(
            probabilidades,
            key=probabilidades.get
        )

        if (
            prediccion
            ==
            resultado["resultado_real"]
        ):

            aciertos += 1

    return aciertos / len(resultados)


def calcular_brier(resultados):

    if not resultados:

        return None

    suma = 0.0

    for resultado in resultados:

        probabilidades = (
            resultado["probabilidades"]
        )

        real = resultado[
            "resultado_real"
        ]

        if real == "local":

            objetivo = [1, 0, 0]

        elif real == "empate":

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


def evaluar(
    resultados,
    num_bins
):

    calibradores = construir_calibradores(
        resultados,
        num_bins
    )

    calibrados = aplicar_calibracion(
        resultados,
        calibradores
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
    print("TUNING DE BINS — CALIBRACIÓN")
    print("=" * 75)

    print()

    print(
        f"Partidos históricos disponibles: "
        f"{len(partidos)}"
    )

    print(
        f"Ventana: {VENTANA}"
    )

    print(
        f"Smoothing: {SMOOTHING}"
    )

    print()

    print(
        "Ejecutando backtest V1..."
    )

    resultados, descartados = ejecutar_backtest(
        partidos,
        ventana=VENTANA
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

    if not resultados_test:

        print(
            "No hay resultados de 2024."
        )

        return

    # ========================================================
    # DESARROLLO 2023
    # ========================================================

    print()
    print("=" * 75)
    print("DESARROLLO 2023")
    print("=" * 75)

    print()

    print(
        f"{'Bins':<12}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 42)

    resultados_tuning = []

    for num_bins in NUM_BINS_OPTIONS:

        accuracy, brier = evaluar(
            resultados_train,
            num_bins
        )

        resultados_tuning.append({
            "bins": num_bins,
            "accuracy": accuracy,
            "brier": brier
        })

        print(
            f"{num_bins:<12}"
            f"{accuracy * 100:>7.2f}%"
            f"{'':<8}"
            f"{brier:.4f}"
        )

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
    print("MEJOR CONFIGURACIÓN POR BRIER")
    print("=" * 75)

    print(
        f"Bins: "
        f"{mejor_brier['bins']}"
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
    print("MEJOR CONFIGURACIÓN POR ACCURACY")
    print("=" * 75)

    print(
        f"Bins: "
        f"{mejor_accuracy['bins']}"
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
    # TEST 2024
    # ========================================================

    calibradores = construir_calibradores(
        resultados_train,
        mejor_brier["bins"]
    )

    calibrados_2024 = aplicar_calibracion(
        resultados_test,
        calibradores
    )

    accuracy_original = (
        calcular_accuracy(
            resultados_test
        )
    )

    brier_original = (
        calcular_brier(
            resultados_test
        )
    )

    accuracy_calibrado = (
        calcular_accuracy(
            calibrados_2024
        )
    )

    brier_calibrado = (
        calcular_brier(
            calibrados_2024
        )
    )

    print()
    print("=" * 75)
    print("TEST 2024")
    print("=" * 75)

    print()

    print(
        f"{'Modelo':<25}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 55)

    print(
        f"{'V1 original':<25}"
        f"{accuracy_original * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_original:.4f}"
    )

    print(
        f"{'V1 calibrado':<25}"
        f"{accuracy_calibrado * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_calibrado:.4f}"
    )

    print()

    print(
        f"Diferencia Accuracy: "
        f"{(accuracy_calibrado - accuracy_original) * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier: "
        f"{brier_calibrado - brier_original:+.4f}"
    )

    print()

    if brier_calibrado < brier_original:

        print(
            "RESULTADO: "
            "LA CALIBRACIÓN MEJORA EL BRIER."
        )

    elif brier_calibrado > brier_original:

        print(
            "RESULTADO: "
            "LA CALIBRACIÓN EMPEORA EL BRIER."
        )

    else:

        print(
            "RESULTADO: "
            "EL BRIER NO CAMBIA."
        )

    print("=" * 75)


if __name__ == "__main__":

    main()