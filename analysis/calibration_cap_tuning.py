from database.database import Database
from analysis.backtest import ejecutar_backtest


VENTANA = 5

SEASON_TRAIN = 2023
SEASON_TEST = 2024

NUM_BINS = 10

RESULTADOS = [
    "local",
    "empate",
    "visitante"
]

SMOOTHING = 1

CAPS = [
    0.05,
    0.10,
    0.15,
    None
]


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


def obtener_bin(bins, probabilidad):

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


def construir_calibradores(
    resultados
):

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        calibradores[
            resultado_objetivo
        ] = construir_calibracion(
            resultados,
            resultado_objetivo
        )

    return calibradores


def aplicar_cap(
    original,
    calibrada,
    cap
):

    if cap is None:

        return calibrada

    diferencia = calibrada - original

    if diferencia > cap:

        return original + cap

    if diferencia < -cap:

        return original - cap

    return calibrada


def calibrar_probabilidades(
    probabilidades,
    calibradores,
    cap
):

    calibradas = {}

    for resultado_objetivo in RESULTADOS:

        original = probabilidades[
            resultado_objetivo
        ]

        calibrada = obtener_correccion(
            calibradores[
                resultado_objetivo
            ],
            original
        )

        calibradas[
            resultado_objetivo
        ] = aplicar_cap(
            original,
            calibrada,
            cap
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


def calcular_accuracy(resultados):

    if not resultados:

        return None

    aciertos = 0

    for resultado in resultados:

        probabilidades = resultado[
            "probabilidades"
        ]

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

        probabilidades = resultado[
            "probabilidades"
        ]

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


def aplicar_calibracion(
    resultados,
    calibradores,
    cap
):

    nuevos = []

    for resultado in resultados:

        probabilidades = resultado[
            "probabilidades"
        ]

        calibradas = calibrar_probabilidades(
            probabilidades,
            calibradores,
            cap
        )

        nuevos.append({
            "partido": resultado["partido"],
            "resultado_real":
                resultado["resultado_real"],
            "probabilidades":
                calibradas
        })

    return nuevos


def nombre_cap(cap):

    if cap is None:

        return "Sin límite"

    return f"±{cap * 100:.0f} pp"


def main():

    partidos = obtener_partidos_historicos()

    print("=" * 75)
    print("TUNING DE LÍMITE DE CALIBRACIÓN")
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

        print("No hay resultados de 2023.")

        return

    if not resultados_test:

        print("No hay resultados de 2024.")

        return

    # ========================================================
    # APRENDER CALIBRADORES SOLO CON 2023
    # ========================================================

    calibradores = construir_calibradores(
        resultados_train
    )

    # ========================================================
    # TUNING EN 2023
    # ========================================================

    print()
    print("=" * 75)
    print("DESARROLLO 2023")
    print("=" * 75)

    print()

    print(
        f"{'Límite':<18}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 48)

    resultados_tuning = []

    for cap in CAPS:

        calibrados = aplicar_calibracion(
            resultados_train,
            calibradores,
            cap
        )

        accuracy = calcular_accuracy(
            calibrados
        )

        brier = calcular_brier(
            calibrados
        )

        resultados_tuning.append({
            "cap": cap,
            "accuracy": accuracy,
            "brier": brier
        })

        print(
            f"{nombre_cap(cap):<18}"
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
    print("MEJOR LÍMITE POR BRIER — 2023")
    print("=" * 75)

    print(
        f"Límite: "
        f"{nombre_cap(mejor_brier['cap'])}"
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
    print("MEJOR LÍMITE POR ACCURACY — 2023")
    print("=" * 75)

    print(
        f"Límite: "
        f"{nombre_cap(mejor_accuracy['cap'])}"
    )

    print(
        f"Accuracy: "
        f"{mejor_accuracy['accuracy'] * 100:.2f}%"
    )

    print(
        f"Brier: "
        f"{mejor_accuracy['brier']:.4f}"
    )

    print()
    print("=" * 75)
    print(
        "SELECCIÓN FINAL PARA TEST"
    )
    print("=" * 75)

    print()

    print(
        "El límite se selecciona exclusivamente "
        "con los datos de 2023."
    )

    print(
        f"Límite seleccionado por Brier: "
        f"{nombre_cap(mejor_brier['cap'])}"
    )

    print()

    # ========================================================
    # TEST 2024
    # ========================================================

    calibrados_2024 = aplicar_calibracion(
        resultados_test,
        calibradores,
        mejor_brier["cap"]
    )

    accuracy_original = calcular_accuracy(
        resultados_test
    )

    brier_original = calcular_brier(
        resultados_test
    )

    accuracy_calibrado = calcular_accuracy(
        calibrados_2024
    )

    brier_calibrado = calcular_brier(
        calibrados_2024
    )

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
        f"{'V1 calibrado + límite':<25}"
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
            "EL LÍMITE MEJORA EL BRIER."
        )

    elif brier_calibrado > brier_original:

        print(
            "RESULTADO: "
            "EL LÍMITE EMPEORA EL BRIER."
        )

    else:

        print(
            "RESULTADO: "
            "EL BRIER NO CAMBIA."
        )

    print("=" * 75)


if __name__ == "__main__":

    main()