from database.database import Database

from analysis.backtest import ejecutar_backtest

from analysis.relative_strength import (
    obtener_partidos,
    predecir_partido
)


VENTANA = 5

SMOOTHING = 1
NUM_BINS = 10

SEASON_TRAIN = 2023
SEASON_TEST = 2024

TRAIN_RATIO = 0.75

PESOS_RS = [
    0.00,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50
]

RESULTADOS = [
    "local",
    "empate",
    "visitante"
]


# ============================================================
# CALIBRACIÓN
# ============================================================

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


# ============================================================
# MÉTRICAS
# ============================================================

def calcular_accuracy(resultados):

    if not resultados:
        return 0.0

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
        return 0.0

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


# ============================================================
# RELATIVE STRENGTH
# ============================================================

def construir_relative_strength(
    partidos,
    resultados_base
):

    por_fixture = {}

    for resultado in resultados_base:

        partido = resultado["partido"]

        fixture_id = partido["fixture_id"]

        probabilidades_rs = predecir_partido(
            partido,
            partidos
        )

        if probabilidades_rs is None:
            continue

        por_fixture[fixture_id] = (
            probabilidades_rs
        )

    return por_fixture


# ============================================================
# COMBINACIÓN V2 + RELATIVE STRENGTH
# ============================================================

def combinar_probabilidades(
    probabilidades_v2,
    probabilidades_rs,
    peso_rs
):

    probabilidades = {}

    for resultado in RESULTADOS:

        probabilidades[resultado] = (
            (1 - peso_rs)
            *
            probabilidades_v2[resultado]
            +
            peso_rs
            *
            probabilidades_rs[resultado]
        )

    suma = sum(
        probabilidades[resultado]
        for resultado in RESULTADOS
    )

    if suma <= 0:
        return probabilidades

    for resultado in RESULTADOS:

        probabilidades[resultado] /= suma

    return probabilidades


def combinar_resultados(
    resultados_base,
    calibradores,
    probabilidades_rs,
    peso_rs
):

    nuevos = []

    for resultado in resultados_base:

        fixture_id = resultado[
            "partido"
        ]["fixture_id"]

        if fixture_id not in probabilidades_rs:
            continue

        probabilidades_v2 = (
            calibrar_probabilidades(
                resultado["probabilidades"],
                calibradores
            )
        )

        probabilidades_finales = (
            combinar_probabilidades(
                probabilidades_v2,
                probabilidades_rs[
                    fixture_id
                ],
                peso_rs
            )
        )

        nuevos.append({

            "partido":
                resultado["partido"],

            "resultado_real":
                resultado["resultado_real"],

            "probabilidades":
                probabilidades_finales

        })

    return nuevos


# ============================================================
# SEPARACIÓN TEMPORAL
# ============================================================

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


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("TUNING RELATIVE STRENGTH — V3")
    print("=" * 75)

    print()

    print(
        "Configuración V2 congelada:"
    )

    print(
        f"Ventana: {VENTANA}"
    )

    print(
        f"Smoothing: {SMOOTHING}"
    )

    print(
        f"Bins: {NUM_BINS}"
    )

    print(
        "Límite: ninguno"
    )

    print()

    # ========================================================
    # CARGAR PARTIDOS
    # ========================================================

    partidos = obtener_partidos()

    print(
        f"Partidos históricos: "
        f"{len(partidos)}"
    )

    # ========================================================
    # BACKTEST BASE V1
    # ========================================================

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

    # ========================================================
    # RELATIVE STRENGTH
    # ========================================================

    print()

    print(
        "Calculando Relative Strength..."
    )

    probabilidades_rs = (
        construir_relative_strength(
            partidos,
            resultados
        )
    )

    print(
        f"Partidos con Relative Strength: "
        f"{len(probabilidades_rs)}"
    )

    # ========================================================
    # DIVISIÓN TEMPORAL 2023
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
    # CALIBRADOR V2 PARA DESARROLLO
    # ========================================================

    calibradores_train = (
        construir_calibradores(
            train_2023
        )
    )

    # ========================================================
    # BASE V2 EN VALIDACIÓN
    # ========================================================

    print()
    print("=" * 75)
    print("DESARROLLO — VALIDACIÓN 2023")
    print("=" * 75)

    print()

    print(
        f"{'Peso RS':<12}"
        f"{'Partidos':<12}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 54)

    resultados_tuning = []

    for peso_rs in PESOS_RS:

        combinados = combinar_resultados(
            validacion_2023,
            calibradores_train,
            probabilidades_rs,
            peso_rs
        )

        accuracy = calcular_accuracy(
            combinados
        )

        brier = calcular_brier(
            combinados
        )

        resultados_tuning.append({

            "peso": peso_rs,

            "partidos": len(
                combinados
            ),

            "accuracy": accuracy,

            "brier": brier

        })

        print(
            f"{peso_rs:<12.2f}"
            f"{len(combinados):<12}"
            f"{accuracy * 100:>7.2f}%"
            f"{'':<8}"
            f"{brier:.4f}"
        )

    # ========================================================
    # MEJOR PESO
    # ========================================================

    mejor = min(
        resultados_tuning,
        key=lambda x: x["brier"]
    )

    print()

    print("=" * 75)
    print("MEJOR PESO POR BRIER")
    print("=" * 75)

    print(
        f"Peso Relative Strength: "
        f"{mejor['peso']:.2f}"
    )

    print(
        f"Accuracy: "
        f"{mejor['accuracy'] * 100:.2f}%"
    )

    print(
        f"Brier: "
        f"{mejor['brier']:.4f}"
    )

    # ========================================================
    # CALIBRADOR FINAL — TODO 2023
    # ========================================================

    calibradores_finales = (
        construir_calibradores(
            resultados_2023
        )
    )

    # ========================================================
    # TEST 2024
    # ========================================================

    resultados_v2_2024 = (
        combinar_resultados(
            resultados_2024,
            calibradores_finales,
            probabilidades_rs,
            0.00
        )
    )

    resultados_v3_2024 = (
        combinar_resultados(
            resultados_2024,
            calibradores_finales,
            probabilidades_rs,
            mejor["peso"]
        )
    )

    accuracy_v2 = calcular_accuracy(
        resultados_v2_2024
    )

    brier_v2 = calcular_brier(
        resultados_v2_2024
    )

    accuracy_v3 = calcular_accuracy(
        resultados_v3_2024
    )

    brier_v3 = calcular_brier(
        resultados_v3_2024
    )

    print()
    print("=" * 75)
    print("TEST FINAL 2024")
    print("=" * 75)

    print()

    print(
        f"{'Modelo':<30}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 60)

    print(
        f"{'V2 calibrada':<30}"
        f"{accuracy_v2 * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_v2:.4f}"
    )

    print(
        f"{'V3 + Relative Strength':<30}"
        f"{accuracy_v3 * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_v3:.4f}"
    )

    print()

    print(
        f"Diferencia Accuracy: "
        f"{(accuracy_v3 - accuracy_v2) * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier: "
        f"{brier_v3 - brier_v2:+.4f}"
    )

    print()

    if brier_v3 < brier_v2:

        print(
            "RESULTADO: "
            "RELATIVE STRENGTH MEJORA V2."
        )

    elif brier_v3 > brier_v2:

        print(
            "RESULTADO: "
            "RELATIVE STRENGTH EMPEORA V2."
        )

    else:

        print(
            "RESULTADO: "
            "RELATIVE STRENGTH NO CAMBIA V2."
        )

    print()

    print(
        f"Peso seleccionado en 2023: "
        f"{mejor['peso']:.2f}"
    )

    print(
        "2024 fue utilizado únicamente "
        "como TEST."
    )

    print("=" * 75)


if __name__ == "__main__":

    main()