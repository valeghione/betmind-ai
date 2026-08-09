from database.database import Database
from analysis.poisson_tuning import (
    obtener_forma,
    calcular_goles_esperados,
    probabilidades_dixon_coles,
    convertir_a_1x2
)

VENTANA = 5
RHO = -0.20

SEASON_TRAIN = 2023
SEASON_TEST = 2024

BINS = 10
SMOOTHING = 1


def obtener_partidos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


def predecir_partido(
    partido,
    partidos
):

    fecha_hasta = partido["fecha"]

    forma_local = obtener_forma(
        partidos,
        partido["home_team_id"],
        "local",
        fecha_hasta
    )

    forma_visitante = obtener_forma(
        partidos,
        partido["away_team_id"],
        "visitante",
        fecha_hasta
    )

    if forma_local is None:
        return None

    if forma_visitante is None:
        return None

    lambda_local, lambda_visitante = (
        calcular_goles_esperados(
            forma_local,
            forma_visitante
        )
    )

    matriz = probabilidades_dixon_coles(
        lambda_local,
        lambda_visitante,
        RHO
    )

    if matriz is None:
        return None

    probabilidades = convertir_a_1x2(
        matriz
    )

    return probabilidades


def resultado_real(partido):

    if (
        partido["goles_local"]
        >
        partido["goles_visitante"]
    ):

        return "local"

    if (
        partido["goles_local"]
        ==
        partido["goles_visitante"]
    ):

        return "empate"

    return "visitante"


def generar_resultados(
    partidos,
    temporada
):

    resultados = []
    descartados = 0

    for partido in partidos:

        if partido["season"] != temporada:
            continue

        probabilidades = predecir_partido(
            partido,
            partidos
        )

        if probabilidades is None:

            descartados += 1
            continue

        real = resultado_real(partido)

        prediccion = max(
            probabilidades,
            key=probabilidades.get
        )

        resultados.append({
            "partido": partido,
            "probabilidades": probabilidades,
            "resultado_real": real,
            "prediccion": prediccion,
            "acierto": (
                prediccion == real
            )
        })

    return resultados, descartados


# ============================================================
# CALIBRACIÓN
# ============================================================

def crear_bins():

    bins = []

    for i in range(BINS):

        bins.append({
            "inferior":
                i / BINS,

            "superior":
                (i + 1) / BINS,

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


def construir_calibrador(
    resultados,
    objetivo
):

    bins = crear_bins()

    for resultado in resultados:

        probabilidad = (
            resultado["probabilidades"]
            [objetivo]
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
            objetivo
        ):

            bin_data["aciertos"] += 1

    return bins


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

    cantidad = bin_data["cantidad"]

    aciertos = bin_data["aciertos"]

    # Suavizado Laplace.
    #
    # Para mantener consistencia con el experimento
    # anterior usamos smoothing = 1.
    calibrada = (
        aciertos + SMOOTHING
    ) / (
        cantidad
        +
        2 * SMOOTHING
    )

    return calibrada


def construir_calibradores(
    resultados_train
):

    calibradores = {}

    for objetivo in [
        "local",
        "empate",
        "visitante"
    ]:

        calibradores[objetivo] = (
            construir_calibrador(
                resultados_train,
                objetivo
            )
        )

    return calibradores


def aplicar_calibracion(
    probabilidades,
    calibradores
):

    nuevas = {}

    for objetivo in [
        "local",
        "empate",
        "visitante"
    ]:

        nuevas[objetivo] = (
            calibrar_probabilidad(
                calibradores[objetivo],
                probabilidades[objetivo]
            )
        )

    # Normalizamos para que vuelvan a sumar 1.
    suma = sum(nuevas.values())

    if suma <= 0:

        return probabilidades

    for objetivo in nuevas:

        nuevas[objetivo] /= suma

    return nuevas


# ============================================================
# MÉTRICAS
# ============================================================

def calcular_accuracy(
    resultados
):

    if not resultados:
        return 0

    return (
        sum(
            1
            for r in resultados
            if r["acierto"]
        )
        /
        len(resultados)
    )


def calcular_brier(
    resultados
):

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
        suma / len(resultados)
    )


def recalibrar_resultados(
    resultados,
    calibradores
):

    nuevos = []

    for resultado in resultados:

        probabilidades = (
            aplicar_calibracion(
                resultado["probabilidades"],
                calibradores
            )
        )

        prediccion = max(
            probabilidades,
            key=probabilidades.get
        )

        nuevos.append({
            "partido":
                resultado["partido"],

            "probabilidades":
                probabilidades,

            "resultado_real":
                resultado["resultado_real"],

            "prediccion":
                prediccion,

            "acierto":
                prediccion
                ==
                resultado["resultado_real"]
        })

    return nuevos


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("BACKTEST V3 — DIXON-COLES + CALIBRACIÓN")
    print("=" * 75)

    print()

    print(
        f"Ventana: {VENTANA}"
    )

    print(
        f"Rho: {RHO}"
    )

    print(
        f"Bins: {BINS}"
    )

    print(
        f"Smoothing: {SMOOTHING}"
    )

    print(
        f"Train: {SEASON_TRAIN}"
    )

    print(
        f"Test: {SEASON_TEST}"
    )

    print()

    partidos = obtener_partidos()

    print(
        f"Partidos históricos: "
        f"{len(partidos)}"
    )

    # ========================================================
    # GENERACIÓN
    # ========================================================

    print()
    print("=" * 75)
    print("GENERANDO RESULTADOS")
    print("=" * 75)

    resultados_train, descartados_train = (
        generar_resultados(
            partidos,
            SEASON_TRAIN
        )
    )

    resultados_test, descartados_test = (
        generar_resultados(
            partidos,
            SEASON_TEST
        )
    )

    print()

    print(
        f"Resultados 2023: "
        f"{len(resultados_train)}"
    )

    print(
        f"Descartados 2023: "
        f"{descartados_train}"
    )

    print(
        f"Resultados 2024: "
        f"{len(resultados_test)}"
    )

    print(
        f"Descartados 2024: "
        f"{descartados_test}"
    )

    # ========================================================
    # CALIBRADORES
    # ========================================================

    print()
    print("=" * 75)
    print("CONSTRUYENDO CALIBRADORES CON 2023")
    print("=" * 75)

    calibradores = construir_calibradores(
        resultados_train
    )

    print()
    print(
        "Calibradores construidos."
    )

    print(
        "2024 permanece fuera "
        "del entrenamiento."
    )

    # ========================================================
    # TEST ORIGINAL DC
    # ========================================================

    accuracy_dc = calcular_accuracy(
        resultados_test
    )

    brier_dc = calcular_brier(
        resultados_test
    )

    # ========================================================
    # TEST DC + CALIBRACIÓN
    # ========================================================

    resultados_calibrados = (
        recalibrar_resultados(
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
    print("=" * 75)
    print("RESULTADO FINAL")
    print("=" * 75)

    print()

    print(
        f"{'Modelo':<32}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 62)

    print(
        f"{'Dixon-Coles sin calibrar':<32}"
        f"{accuracy_dc * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_dc:.4f}"
    )

    print(
        f"{'Dixon-Coles + calibración':<32}"
        f"{accuracy_calibrado * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_calibrado:.4f}"
    )

    print()

    print(
        f"Diferencia Accuracy: "
        f"{(accuracy_calibrado - accuracy_dc) * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier: "
        f"{brier_calibrado - brier_dc:+.4f}"
    )

    print()

    # ========================================================
    # COMPARACIÓN CON V2
    # ========================================================

    V2_ACCURACY = 0.4441
    V2_BRIER = 0.6383

    print("=" * 75)
    print("COMPARACIÓN CONTRA V2")
    print("=" * 75)

    print()

    print(
        f"{'Modelo':<32}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 62)

    print(
        f"{'V2 Poisson + calibración':<32}"
        f"{V2_ACCURACY * 100:>7.2f}%"
        f"{'':<8}"
        f"{V2_BRIER:.4f}"
    )

    print(
        f"{'V3 Dixon-Coles + calibración':<32}"
        f"{accuracy_calibrado * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_calibrado:.4f}"
    )

    print()

    diferencia_accuracy = (
        accuracy_calibrado
        -
        V2_ACCURACY
    )

    diferencia_brier = (
        brier_calibrado
        -
        V2_BRIER
    )

    print(
        f"Diferencia Accuracy vs V2: "
        f"{diferencia_accuracy * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier vs V2: "
        f"{diferencia_brier:+.4f}"
    )

    print()

    if brier_calibrado < V2_BRIER:

        print(
            "RESULTADO: "
            "V3 SUPERA A V2 POR BRIER."
        )

    elif brier_calibrado > V2_BRIER:

        print(
            "RESULTADO: "
            "V3 NO SUPERA A V2."
        )

    else:

        print(
            "RESULTADO: "
            "V3 IGUALA A V2."
        )

    print()

    print(
        "Configuración:"
    )

    print(
        f"Ventana = {VENTANA}"
    )

    print(
        f"Rho = {RHO}"
    )

    print(
        f"Bins = {BINS}"
    )

    print(
        f"Smoothing = {SMOOTHING}"
    )

    print(
        "2024 utilizado únicamente "
        "como TEST."
    )

    print("=" * 75)


if __name__ == "__main__":

    main()