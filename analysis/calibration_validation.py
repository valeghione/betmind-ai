from database.database import Database
from analysis.backtest import ejecutar_backtest


VENTANA = 5

SEASON_TRAIN = 2023
SEASON_TEST = 2024

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

SMOOTHING = 1

TRAIN_RATIO = 0.75


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


def obtener_bin(bins, probabilidad):

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

        probabilidades = resultado[
            "probabilidades"
        ]

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


def dividir_train_validacion(resultados):

    cantidad = len(resultados)

    punto_corte = int(
        cantidad * TRAIN_RATIO
    )

    train = resultados[
        :punto_corte
    ]

    validacion = resultados[
        punto_corte:
    ]

    return train, validacion


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

        prob_local = probabilidades[
            "local"
        ]

        prob_empate = probabilidades[
            "empate"
        ]

        prob_visitante = probabilidades[
            "visitante"
        ]

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

    return (
        aciertos
        /
        len(resultados)
    )


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

    return (
        suma
        /
        len(resultados)
    )


def evaluar_configuracion(
    train,
    validacion,
    num_bins
):

    calibradores = construir_calibradores(
        train,
        num_bins
    )

    resultados_validacion = (
        aplicar_calibracion(
            validacion,
            calibradores
        )
    )

    accuracy = calcular_accuracy(
        resultados_validacion
    )

    brier = calcular_brier(
        resultados_validacion
    )

    return accuracy, brier


def main():

    partidos = obtener_partidos_historicos()

    print("=" * 75)
    print(
        "VALIDACIÓN TEMPORAL DE CALIBRACIÓN"
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

    print(
        f"Smoothing: {SMOOTHING}"
    )

    print(
        f"Train ratio: "
        f"{TRAIN_RATIO * 100:.0f}%"
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

    resultados_2023, resultados_2024 = (
        separar_temporadas(
            resultados
        )
    )

    print()

    print(
        f"Resultados 2023: "
        f"{len(resultados_2023)}"
    )

    print(
        f"Resultados 2024: "
        f"{len(resultados_2024)}"
    )

    if not resultados_2023:

        print(
            "No hay resultados de 2023."
        )

        return

    if not resultados_2024:

        print(
            "No hay resultados de 2024."
        )

        return

    # ========================================================
    # DIVISIÓN TEMPORAL DE 2023
    # ========================================================

    train_2023, validacion_2023 = (
        dividir_train_validacion(
            resultados_2023
        )
    )

    print()

    print(
        f"Entrenamiento 2023: "
        f"{len(train_2023)}"
    )

    print(
        f"Validación 2023: "
        f"{len(validacion_2023)}"
    )

    # ========================================================
    # TUNING SOBRE VALIDACIÓN
    # ========================================================

    print()
    print("=" * 75)
    print(
        "SELECCIÓN DE BINS — VALIDACIÓN 2023"
    )
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

        accuracy, brier = (
            evaluar_configuracion(
                train_2023,
                validacion_2023,
                num_bins
            )
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

    # ========================================================
    # SELECCIÓN
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
    print(
        "MEJOR CONFIGURACIÓN POR BRIER"
    )
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
    print(
        "MEJOR CONFIGURACIÓN POR ACCURACY"
    )
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
    # RECALIBRAR TODO 2023
    # ========================================================

    bins_seleccionados = (
        mejor_brier["bins"]
    )

    calibradores_finales = (
        construir_calibradores(
            resultados_2023,
            bins_seleccionados
        )
    )

    # ========================================================
    # TEST FINAL 2024
    # ========================================================

    resultados_calibrados_2024 = (
        aplicar_calibracion(
            resultados_2024,
            calibradores_finales
        )
    )

    accuracy_original = (
        calcular_accuracy(
            resultados_2024
        )
    )

    brier_original = (
        calcular_brier(
            resultados_2024
        )
    )

    accuracy_calibrado = (
        calcular_accuracy(
            resultados_calibrados_2024
        )
    )

    brier_calibrado = (
        calcular_brier(
            resultados_calibrados_2024
        )
    )

    print()
    print("=" * 75)
    print(
        "TEST FINAL 2024"
    )
    print("=" * 75)

    print()

    print(
        f"{'Modelo':<30}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 60)

    print(
        f"{'V1 original':<30}"
        f"{accuracy_original * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_original:.4f}"
    )

    print(
        f"{'V1 calibrado':<30}"
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

    print()

    print(
        f"Bins elegidos mediante validación: "
        f"{bins_seleccionados}"
    )

    print(
        "2024 NO fue utilizado para elegir "
        "la cantidad de bins."
    )

    print("=" * 75)


if __name__ == "__main__":

    main()