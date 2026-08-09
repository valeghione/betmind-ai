from database.database import Database
from analysis.backtest import ejecutar_backtest


VENTANA = 5
NUM_BINS = 10

SEASON_TRAIN = 2023
SEASON_TEST = 2024

RESULTADOS = [
    "local",
    "empate",
    "visitante"
]

SMOOTHING = 1


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

    probabilidad_calibrada = (
        peso_datos * frecuencia_real
        +
        (1 - peso_datos)
        * promedio_modelo
    )

    return probabilidad_calibrada


def calibrar_probabilidades(
    probabilidades,
    calibradores
):

    probabilidades_calibradas = {}

    for resultado_objetivo in RESULTADOS:

        probabilidad = probabilidades[
            resultado_objetivo
        ]

        bins = calibradores[
            resultado_objetivo
        ]

        probabilidades_calibradas[
            resultado_objetivo
        ] = obtener_correccion(
            bins,
            probabilidad
        )

    suma = sum(
        probabilidades_calibradas[
            resultado
        ]
        for resultado in RESULTADOS
    )

    if suma <= 0:

        return probabilidades

    for resultado in RESULTADOS:

        probabilidades_calibradas[
            resultado
        ] /= suma

    return probabilidades_calibradas


def separar_temporadas(resultados):

    resultados_train = []
    resultados_test = []

    for resultado in resultados:

        partido = resultado["partido"]

        temporada = partido["season"]

        if temporada == SEASON_TRAIN:

            resultados_train.append(
                resultado
            )

        elif temporada == SEASON_TEST:

            resultados_test.append(
                resultado
            )

    return (
        resultados_train,
        resultados_test
    )


def calcular_brier(resultados):

    if not resultados:

        return None

    suma = 0.0

    for resultado in resultados:

        probabilidades = resultado[
            "probabilidades"
        ]

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

        probabilidades = resultado[
            "probabilidades"
        ]

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

    return (
        aciertos
        /
        len(resultados)
    )


def calcular_ece(
    resultados,
    resultado_objetivo
):

    if not resultados:

        return None

    bins = construir_calibracion(
        resultados,
        resultado_objetivo
    )

    ece = 0.0

    cantidad_total = len(resultados)

    for bin_data in bins:

        cantidad = bin_data["cantidad"]

        if cantidad == 0:

            continue

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

        peso = (
            cantidad
            /
            cantidad_total
        )

        ece += (
            peso
            *
            abs(
                promedio_modelo
                -
                frecuencia_real
            )
        )

    return ece


def mostrar_calibradores(
    calibradores
):

    print()
    print("=" * 75)
    print("CALIBRADORES APRENDIDOS EN 2023")
    print("=" * 75)

    for resultado_objetivo in RESULTADOS:

        print()
        print(
            resultado_objetivo.upper()
        )

        print(
            f"{'Rango':<12}"
            f"{'N':<8}"
            f"{'Modelo':<14}"
            f"{'Real':<14}"
            f"{'Calibrado':<14}"
        )

        print("-" * 65)

        bins = calibradores[
            resultado_objetivo
        ]

        for bin_data in bins:

            cantidad = bin_data["cantidad"]

            if cantidad == 0:

                continue

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

            correccion = obtener_correccion(
                bins,
                promedio_modelo
            )

            rango = (
                f"{bin_data['inferior'] * 100:.0f}%"
                "-"
                f"{bin_data['superior'] * 100:.0f}%"
            )

            print(
                f"{rango:<12}"
                f"{cantidad:<8}"
                f"{promedio_modelo * 100:>6.2f}%"
                f"{'':<7}"
                f"{frecuencia_real * 100:>6.2f}%"
                f"{'':<7}"
                f"{correccion * 100:>6.2f}%"
            )


def aplicar_calibracion(
    resultados,
    calibradores
):

    resultados_calibrados = []

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

        nuevo_resultado = {
            "partido": resultado["partido"],
            "resultado_real":
                resultado["resultado_real"],
            "prediccion":
                resultado["prediccion"],
            "acierto":
                resultado["acierto"],
            "probabilidades":
                probabilidades_calibradas,
            "probabilidades_originales":
                probabilidades_originales
        }

        resultados_calibrados.append(
            nuevo_resultado
        )

    return resultados_calibrados


def mostrar_comparacion(
    resultados_originales,
    resultados_calibrados
):

    accuracy_original = (
        calcular_accuracy(
            resultados_originales
        )
    )

    accuracy_calibrado = (
        calcular_accuracy(
            resultados_calibrados
        )
    )

    brier_original = (
        calcular_brier(
            resultados_originales
        )
    )

    brier_calibrado = (
        calcular_brier(
            resultados_calibrados
        )
    )

    print()
    print("=" * 75)
    print("COMPARACIÓN — TEST 2024")
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


def mostrar_primeros_resultados(
    resultados_originales,
    resultados_calibrados
):

    print()
    print("=" * 75)
    print("PRIMEROS 10 RESULTADOS — TEST 2024")
    print("=" * 75)

    for original, calibrado in zip(
        resultados_originales[:10],
        resultados_calibrados[:10]
    ):

        partido = original["partido"]

        probabilidades_originales = (
            original["probabilidades"]
        )

        probabilidades_calibradas = (
            calibrado["probabilidades"]
        )

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
            "Original:   "
            f"L {probabilidades_originales['local'] * 100:.1f}% | "
            f"E {probabilidades_originales['empate'] * 100:.1f}% | "
            f"V {probabilidades_originales['visitante'] * 100:.1f}%"
        )

        print(
            "Calibrado:  "
            f"L {probabilidades_calibradas['local'] * 100:.1f}% | "
            f"E {probabilidades_calibradas['empate'] * 100:.1f}% | "
            f"V {probabilidades_calibradas['visitante'] * 100:.1f}%"
        )

        print(
            f"Real: "
            f"{original['resultado_real']}"
        )


def main():

    partidos = obtener_partidos_historicos()

    print("=" * 75)
    print(
        "CALIBRACIÓN — DESARROLLO 2023 / TEST 2024"
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

    # ========================================================
    # SEPARAR 2023 Y 2024
    # ========================================================

    resultados_train, resultados_test = (
        separar_temporadas(
            resultados
        )
    )

    print()

    print(
        f"Resultados 2023 para calibración: "
        f"{len(resultados_train)}"
    )

    print(
        f"Resultados 2024 para test: "
        f"{len(resultados_test)}"
    )

    if not resultados_train:

        print()
        print(
            "ERROR: no se encontraron "
            "resultados de 2023."
        )

        return

    if not resultados_test:

        print()
        print(
            "ERROR: no se encontraron "
            "resultados de 2024."
        )

        return

    # ========================================================
    # APRENDER CALIBRACIÓN SOLO CON 2023
    # ========================================================

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        calibradores[
            resultado_objetivo
        ] = construir_calibracion(
            resultados_train,
            resultado_objetivo
        )

    mostrar_calibradores(
        calibradores
    )

    # ========================================================
    # ECE EN 2023
    # ========================================================

    print()
    print("=" * 75)
    print("ECE — DESARROLLO 2023")
    print("=" * 75)

    eces = []

    for resultado_objetivo in RESULTADOS:

        ece = calcular_ece(
            resultados_train,
            resultado_objetivo
        )

        eces.append(ece)

        print(
            f"{resultado_objetivo.capitalize():<12}"
            f"ECE: {ece:.4f}"
        )

    ece_promedio = (
        sum(eces)
        /
        len(eces)
    )

    print()

    print(
        f"ECE promedio: "
        f"{ece_promedio:.4f}"
    )

    # ========================================================
    # APLICAR A 2024
    # ========================================================

    resultados_calibrados = (
        aplicar_calibracion(
            resultados_test,
            calibradores
        )
    )

    # ========================================================
    # COMPARACIÓN
    # ========================================================

    mostrar_comparacion(
        resultados_test,
        resultados_calibrados
    )

    # ========================================================
    # PRIMEROS RESULTADOS
    # ========================================================

    mostrar_primeros_resultados(
        resultados_test,
        resultados_calibrados
    )


if __name__ == "__main__":

    main()