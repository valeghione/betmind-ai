from analysis.model_v2 import (
    obtener_partidos,
    generar_probabilidades_base,
    obtener_resultado_real,
    RESULTADOS
)


# ============================================================
# CONFIGURACIÓN CONGELADA
# ============================================================

SEASON_TRAIN = 2023
SEASON_TEST = 2024

BINS = 10
SMOOTHING = 1


# ============================================================
# BINS
# ============================================================

def crear_bins():

    bins = []

    for i in range(BINS):

        bins.append({
            "inferior": i / BINS,
            "superior": (i + 1) / BINS,
            "cantidad": 0,
            "suma_probabilidad": 0.0,
            "aciertos": 0
        })

    return bins


def obtener_bin(bins, probabilidad):

    for i, bin_data in enumerate(bins):

        inferior = bin_data["inferior"]
        superior = bin_data["superior"]

        if i == BINS - 1:

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


# ============================================================
# CONSTRUIR CALIBRADORES
# ============================================================

def construir_calibradores(resultados):

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        bins = crear_bins()

        for resultado in resultados:

            probabilidad = (
                resultado["probabilidades"][
                    resultado_objetivo
                ]
            )

            bin_data = obtener_bin(
                bins,
                probabilidad
            )

            if bin_data is None:
                continue

            bin_data["cantidad"] += 1

            bin_data[
                "suma_probabilidad"
            ] += probabilidad

            if (
                resultado["resultado_real"]
                ==
                resultado_objetivo
            ):

                bin_data["aciertos"] += 1

        calibradores[
            resultado_objetivo
        ] = bins

    return calibradores


# ============================================================
# APLICAR CALIBRACIÓN
# ============================================================

def calibrar_probabilidad(
    bins,
    probabilidad
):

    bin_data = obtener_bin(
        bins,
        probabilidad
    )

    if bin_data is None:

        return probabilidad

    cantidad = (
        bin_data["cantidad"]
    )

    aciertos = (
        bin_data["aciertos"]
    )

    return (
        aciertos + SMOOTHING
    ) / (
        cantidad
        +
        2 * SMOOTHING
    )


def aplicar_calibracion(
    probabilidades,
    calibradores
):

    nuevas = {}

    for resultado in RESULTADOS:

        nuevas[resultado] = (
            calibrar_probabilidad(
                calibradores[resultado],
                probabilidades[resultado]
            )
        )

    suma = sum(
        nuevas.values()
    )

    if suma <= 0:

        return probabilidades

    for resultado in nuevas:

        nuevas[resultado] /= suma

    return nuevas


# ============================================================
# BRIER SCORE
# ============================================================

def calcular_brier(
    resultados,
    probabilidades
):

    suma = 0

    for resultado, prediccion in zip(
        resultados,
        probabilidades
    ):

        resultado_real = (
            resultado["resultado_real"]
        )

        if resultado_real == "local":

            objetivo = [
                1,
                0,
                0
            ]

        elif resultado_real == "empate":

            objetivo = [
                0,
                1,
                0
            ]

        else:

            objetivo = [
                0,
                0,
                1
            ]

        valores = [
            prediccion["local"],
            prediccion["empate"],
            prediccion["visitante"]
        ]

        suma += sum(
            (
                valores[i]
                -
                objetivo[i]
            ) ** 2
            for i in range(3)
        )

    return suma / len(resultados)


# ============================================================
# ACCURACY
# ============================================================

def calcular_accuracy(
    resultados,
    probabilidades
):

    aciertos = 0

    for resultado, prediccion in zip(
        resultados,
        probabilidades
    ):

        elegido = max(
            prediccion,
            key=prediccion.get
        )

        if (
            elegido
            ==
            resultado["resultado_real"]
        ):

            aciertos += 1

    return aciertos / len(resultados)


# ============================================================
# CONSTRUIR DATASET
# ============================================================

def construir_resultados(
    partidos,
    temporada
):

    resultados = []

    for partido in partidos:

        if partido["season"] != temporada:
            continue

        probabilidades = (
            generar_probabilidades_base(
                partido,
                partidos
            )
        )

        if probabilidades is None:
            continue

        resultados.append({

            "probabilidades":
                probabilidades,

            "resultado_real":
                obtener_resultado_real(
                    partido
                )
        })

    return resultados


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("BETMIND AI — TEST FINAL CALIBRACIÓN 2024")
    print("=" * 80)

    print()

    print(
        "Configuración congelada:"
    )

    print(
        f"Bins:       {BINS}"
    )

    print(
        f"Smoothing:  {SMOOTHING}"
    )

    print(
        f"Train:      {SEASON_TRAIN}"
    )

    print(
        f"Test:       {SEASON_TEST}"
    )

    print()

    # ========================================================
    # DATOS
    # ========================================================

    partidos = obtener_partidos()

    print(
        f"Partidos históricos: "
        f"{len(partidos)}"
    )

    # ========================================================
    # TRAIN 2023
    # ========================================================

    print()
    print(
        "Construyendo entrenamiento 2023..."
    )

    resultados_train = construir_resultados(
        partidos,
        SEASON_TRAIN
    )

    print(
        f"Resultados entrenamiento: "
        f"{len(resultados_train)}"
    )

    if not resultados_train:

        print(
            "No hay datos de entrenamiento."
        )

        return

    # ========================================================
    # TEST 2024
    # ========================================================

    print()
    print(
        "Construyendo test 2024..."
    )

    resultados_test = construir_resultados(
        partidos,
        SEASON_TEST
    )

    print(
        f"Resultados test: "
        f"{len(resultados_test)}"
    )

    if not resultados_test:

        print(
            "No hay datos de test."
        )

        return

    # ========================================================
    # CALIBRADORES
    # ========================================================

    print()
    print(
        "Construyendo calibradores "
        "EXCLUSIVAMENTE con 2023..."
    )

    calibradores = construir_calibradores(
        resultados_train
    )

    print(
        "Calibradores construidos."
    )

    print(
        "2024 permanece completamente "
        "fuera del entrenamiento."
    )

    # ========================================================
    # BASE 2024
    # ========================================================

    probabilidades_base = []

    for resultado in resultados_test:

        probabilidades_base.append(
            resultado["probabilidades"]
        )

    # ========================================================
    # CALIBRADA 2024
    # ========================================================

    probabilidades_calibradas = []

    for resultado in resultados_test:

        calibradas = aplicar_calibracion(
            resultado["probabilidades"],
            calibradores
        )

        probabilidades_calibradas.append(
            calibradas
        )

    # ========================================================
    # MÉTRICAS
    # ========================================================

    accuracy_base = calcular_accuracy(
        resultados_test,
        probabilidades_base
    )

    brier_base = calcular_brier(
        resultados_test,
        probabilidades_base
    )

    accuracy_calibrada = calcular_accuracy(
        resultados_test,
        probabilidades_calibradas
    )

    brier_calibrada = calcular_brier(
        resultados_test,
        probabilidades_calibradas
    )

    # ========================================================
    # RESULTADOS
    # ========================================================

    print()
    print("=" * 80)
    print("RESULTADO FINAL — TEST 2024")
    print("=" * 80)

    print()

    print(
        f"{'Modelo':<30}"
        f"{'Accuracy':<15}"
        f"Brier"
    )

    print("-" * 65)

    print(
        f"{'Poisson base':<30}"
        f"{accuracy_base * 100:>8.2f}%      "
        f"{brier_base:.4f}"
    )

    print(
        f"{'V2 calibrada 10/1':<30}"
        f"{accuracy_calibrada * 100:>8.2f}%      "
        f"{brier_calibrada:.4f}"
    )

    diferencia_accuracy = (
        accuracy_calibrada
        -
        accuracy_base
    )

    diferencia_brier = (
        brier_calibrada
        -
        brier_base
    )

    print()

    print(
        f"Diferencia Accuracy: "
        f"{diferencia_accuracy * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier: "
        f"{diferencia_brier:+.4f}"
    )

    print()

    if brier_calibrada < brier_base:

        print(
            "RESULTADO: "
            "LA CALIBRACIÓN MEJORA EL BRIER."
        )

    elif brier_calibrada > brier_base:

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
        "Configuración:"
    )

    print(
        f"Bins = {BINS}"
    )

    print(
        f"Smoothing = {SMOOTHING}"
    )

    print(
        "2023 utilizado únicamente "
        "para entrenamiento."
    )

    print(
        "2024 utilizado únicamente "
        "como TEST."
    )

    print()
    print("=" * 80)


if __name__ == "__main__":

    main()