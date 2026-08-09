from analysis.model_v2 import (
    obtener_partidos,
    generar_probabilidades_base,
    obtener_resultado_real,
    RESULTADOS
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

SEASON = 2023

BINS_PROBAR = [5, 10]

SMOOTHING_PROBAR = [1, 2, 5, 10]

PORCENTAJE_TRAIN = 0.75


# ============================================================
# BINS
# ============================================================

def crear_bins(cantidad_bins):

    bins = []

    for i in range(cantidad_bins):

        bins.append({
            "inferior": i / cantidad_bins,
            "superior": (i + 1) / cantidad_bins,
            "cantidad": 0,
            "suma_probabilidad": 0.0,
            "aciertos": 0
        })

    return bins


def obtener_bin(bins, probabilidad):

    cantidad_bins = len(bins)

    for i, bin_data in enumerate(bins):

        inferior = i / cantidad_bins
        superior = (i + 1) / cantidad_bins

        if i == cantidad_bins - 1:

            if inferior <= probabilidad <= superior:
                return bin_data

        else:

            if inferior <= probabilidad < superior:
                return bin_data

    return None


# ============================================================
# CONSTRUIR CALIBRADOR
# ============================================================

def construir_calibradores(
    resultados,
    cantidad_bins
):

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        bins = crear_bins(
            cantidad_bins
        )

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
    aciertos = bin_data["aciertos"]

    return (
        aciertos + smoothing
    ) / (
        cantidad + 2 * smoothing
    )


def aplicar_calibracion(
    probabilidades,
    calibradores,
    smoothing
):

    nuevas = {}

    for resultado in RESULTADOS:

        nuevas[resultado] = (
            calibrar_probabilidad(
                calibradores[resultado],
                probabilidades[resultado],
                smoothing
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
# BRIER
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

        real = resultado[
            "resultado_real"
        ]

        if real == "local":

            objetivo = [1, 0, 0]

        elif real == "empate":

            objetivo = [0, 1, 0]

        else:

            objetivo = [0, 0, 1]

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
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("BETMIND AI — TUNING CALIBRACIÓN")
    print("=" * 80)

    print()

    partidos = obtener_partidos()

    resultados = []

    print(
        "Construyendo probabilidades base 2023..."
    )

    for partido in partidos:

        if partido["season"] != SEASON:
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

    print()

    print(
        f"Resultados 2023: "
        f"{len(resultados)}"
    )

    # ========================================================
    # TRAIN / VALIDACIÓN
    # ========================================================

    cantidad_train = int(
        len(resultados)
        * PORCENTAJE_TRAIN
    )

    train = resultados[
        :cantidad_train
    ]

    validacion = resultados[
        cantidad_train:
    ]

    print(
        f"Entrenamiento 2023: "
        f"{len(train)}"
    )

    print(
        f"Validación 2023: "
        f"{len(validacion)}"
    )

    print()

    # ========================================================
    # TUNING
    # ========================================================

    print(
        f"{'Bins':<10}"
        f"{'Smoothing':<12}"
        f"{'Partidos':<12}"
        f"{'Accuracy':<14}"
        f"Brier"
    )

    print("-" * 65)

    mejor = None

    for cantidad_bins in BINS_PROBAR:

        calibradores = (
            construir_calibradores(
                train,
                cantidad_bins
            )
        )

        for smoothing in SMOOTHING_PROBAR:

            probabilidades_validacion = []

            for resultado in validacion:

                calibradas = (
                    aplicar_calibracion(
                        resultado[
                            "probabilidades"
                        ],
                        calibradores,
                        smoothing
                    )
                )

                probabilidades_validacion.append(
                    calibradas
                )

            accuracy = (
                calcular_accuracy(
                    validacion,
                    probabilidades_validacion
                )
            )

            brier = (
                calcular_brier(
                    validacion,
                    probabilidades_validacion
                )
            )

            print(
                f"{cantidad_bins:<10}"
                f"{smoothing:<12}"
                f"{len(validacion):<12}"
                f"{accuracy * 100:>8.2f}%      "
                f"{brier:.4f}"
            )

            if (
                mejor is None
                or
                brier < mejor["brier"]
            ):

                mejor = {

                    "bins":
                        cantidad_bins,

                    "smoothing":
                        smoothing,

                    "accuracy":
                        accuracy,

                    "brier":
                        brier
                }

    # ========================================================
    # RESULTADO
    # ========================================================

    print()
    print("=" * 80)
    print("MEJOR CONFIGURACIÓN — VALIDACIÓN 2023")
    print("=" * 80)

    print()

    print(
        f"Bins:       "
        f"{mejor['bins']}"
    )

    print(
        f"Smoothing:  "
        f"{mejor['smoothing']}"
    )

    print(
        f"Accuracy:   "
        f"{mejor['accuracy'] * 100:.2f}%"
    )

    print(
        f"Brier:      "
        f"{mejor['brier']:.4f}"
    )

    print()

    print(
        "2024 NO fue utilizado."
    )

    print(
        "La selección se hizo únicamente "
        "con validación 2023."
    )

    print()
    print("=" * 80)


if __name__ == "__main__":

    main()