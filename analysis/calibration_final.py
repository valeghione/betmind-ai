from database.database import Database
from analysis.backtest import ejecutar_backtest


VENTANA = 5
SMOOTHING = 1
NUM_BINS = 10

SEASON_TRAIN = 2023
SEASON_TEST = 2024

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

        probabilidad = resultado[
            "probabilidades"
        ][resultado_objetivo]

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


def construir_calibradores(resultados):

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        calibradores[
            resultado_objetivo
        ] = construir_calibracion(
            resultados,
            resultado_objetivo
        )

    return calibradores


def obtener_probabilidad_calibrada(
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
        / cantidad
    )

    frecuencia_real = (
        bin_data["aciertos"]
        / cantidad
    )

    peso_datos = (
        cantidad
        /
        (cantidad + SMOOTHING)
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
        ] = obtener_probabilidad_calibrada(
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


def calcular_accuracy(resultados):

    if not resultados:
        return 0.0

    aciertos = 0

    for resultado in resultados:

        probabilidades = resultado["probabilidades"]

        prob_local = probabilidades["local"]
        prob_empate = probabilidades["empate"]
        prob_visitante = probabilidades["visitante"]

        if prob_local >= prob_empate and prob_local >= prob_visitante:
            prediccion = "local"

        elif prob_empate >= prob_local and prob_empate >= prob_visitante:
            prediccion = "empate"

        else:
            prediccion = "visitante"

        resultado_real = resultado["resultado_real"]

        if prediccion == resultado_real:
            aciertos += 1

    return aciertos / len(resultados)


def calcular_brier(resultados):

    if not resultados:
        return 0

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
    calibradores
):

    nuevos = []

    for resultado in resultados:

        probabilidades_originales = (
            resultado["probabilidades"]
        )

        probabilidades_calibradas = (
            calibrar_probabilidades(
                probabilidades_originales,
                calibradores
            )
        )

        nuevos.append({

            "partido":
                resultado["partido"],

            "resultado_real":
                resultado["resultado_real"],

            "probabilidades":
                probabilidades_calibradas

        })

    return nuevos


def main():

    print("=" * 70)
    print("BACKTEST FINAL — V2 CALIBRADA")
    print("=" * 70)

    print()

    print("CONFIGURACIÓN CONGELADA")
    print("-" * 70)

    print(
        f"Ventana:       {VENTANA}"
    )

    print(
        f"Smoothing:     {SMOOTHING}"
    )

    print(
        f"Bins:          {NUM_BINS}"
    )

    print(
        "Límite:        ninguno"
    )

    print(
        f"Entrenamiento: {SEASON_TRAIN}"
    )

    print(
        f"Test:          {SEASON_TEST}"
    )

    print()

    partidos = obtener_partidos_historicos()

    print(
        f"Partidos históricos: "
        f"{len(partidos)}"
    )

    print()

    print(
        "Ejecutando backtest V1..."
    )

    resultados, descartados = ejecutar_backtest(
        partidos,
        ventana=VENTANA
    )

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
        f"Resultados entrenamiento "
        f"{SEASON_TRAIN}: "
        f"{len(resultados_train)}"
    )

    print(
        f"Resultados test "
        f"{SEASON_TEST}: "
        f"{len(resultados_test)}"
    )

    if not resultados_train:

        print(
            "ERROR: no hay resultados "
            "de entrenamiento."
        )

        return

    if not resultados_test:

        print(
            "ERROR: no hay resultados "
            "de test."
        )

        return

    # ========================================================
    # APRENDER CALIBRACIÓN ÚNICAMENTE CON 2023
    # ========================================================

    print()
    print("=" * 70)
    print(
        "APRENDIENDO CALIBRACIÓN CON 2023"
    )
    print("=" * 70)

    calibradores = construir_calibradores(
        resultados_train
    )

    print()
    print(
        "Calibradores construidos."
    )

    print(
        "2024 permanece completamente "
        "fuera del entrenamiento."
    )

    # ========================================================
    # TEST ORIGINAL
    # ========================================================

    accuracy_original = calcular_accuracy(
        resultados_test
    )

    brier_original = calcular_brier(
        resultados_test
    )

    # ========================================================
    # TEST CALIBRADO
    # ========================================================

    resultados_calibrados = (
        aplicar_calibracion(
            resultados_test,
            calibradores
        )
    )

    accuracy_calibrado = (
        calcular_accuracy(
            resultados_calibrados
        )
    )

    brier_calibrado = (
        calcular_brier(
            resultados_calibrados
        )
    )

    # ========================================================
    # RESULTADOS
    # ========================================================

    print()
    print("=" * 70)
    print("RESULTADO FINAL — TEST 2024")
    print("=" * 70)

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
        f"{'V2 calibrada':<25}"
        f"{accuracy_calibrado * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_calibrado:.4f}"
    )

    print()

    diferencia_accuracy = (
        accuracy_calibrado
        -
        accuracy_original
    )

    diferencia_brier = (
        brier_calibrado
        -
        brier_original
    )

    print(
        f"Diferencia Accuracy: "
        f"{diferencia_accuracy * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier: "
        f"{diferencia_brier:+.4f}"
    )

    print()

    if brier_calibrado < brier_original:

        print(
            "RESULTADO: "
            "V2 MEJORA EL BRIER."
        )

    elif brier_calibrado > brier_original:

        print(
            "RESULTADO: "
            "V2 EMPEORA EL BRIER."
        )

    else:

        print(
            "RESULTADO: "
            "EL BRIER NO CAMBIA."
        )

    print()

    if accuracy_calibrado > accuracy_original:

        print(
            "La Accuracy también mejora."
        )

    elif accuracy_calibrado < accuracy_original:

        print(
            "La Accuracy empeora."
        )

    else:

        print(
            "La Accuracy no cambia."
        )

    print()

    print(
        "PARÁMETROS UTILIZADOS SIN MODIFICACIÓN:"
    )

    print(
        f"Ventana = {VENTANA}"
    )

    print(
        f"Smoothing = {SMOOTHING}"
    )

    print(
        f"Bins = {NUM_BINS}"
    )

    print(
        "Cap = None"
    )

    print()

    print(
        "2024 fue utilizado únicamente "
        "como conjunto de TEST."
    )

    print("=" * 70)


if __name__ == "__main__":

    main()