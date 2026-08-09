import math

from database.database import Database


VENTANA = 5

SEASON_DEVELOPMENT = 2023
SEASON_TEST = 2024

MAX_GOLES = 10

# rho = 0 equivale al Poisson independiente actual.
# Los valores negativos son los habituales en una corrección
# tipo Dixon-Coles.
RHO_VALUES = [
    0.00,
    -0.02,
    -0.05,
    -0.08,
    -0.10,
    -0.12,
    -0.15,
    -0.20
]


# ============================================================
# DATOS
# ============================================================

def obtener_partidos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


# ============================================================
# FORMA
# ============================================================

def obtener_forma(
    partidos,
    team_id,
    condicion,
    fecha_hasta
):

    seleccionados = []

    for partido in partidos:

        if partido["fecha"] >= fecha_hasta:
            continue

        if partido["estado"] != "FT":
            continue

        if condicion == "local":

            if partido["home_team_id"] != team_id:
                continue

        elif condicion == "visitante":

            if partido["away_team_id"] != team_id:
                continue

        seleccionados.append(partido)

    seleccionados.sort(
        key=lambda x: x["fecha"],
        reverse=True
    )

    seleccionados = seleccionados[:VENTANA]

    if len(seleccionados) < VENTANA:

        return None

    goles_favor = 0
    goles_contra = 0

    for partido in seleccionados:

        if condicion == "local":

            goles_favor += partido["goles_local"]
            goles_contra += partido["goles_visitante"]

        else:

            goles_favor += partido["goles_visitante"]
            goles_contra += partido["goles_local"]

    cantidad = len(seleccionados)

    return {
        "partidos": cantidad,
        "promedio_gf": goles_favor / cantidad,
        "promedio_gc": goles_contra / cantidad
    }


# ============================================================
# GOLES ESPERADOS
# ============================================================

def calcular_goles_esperados(
    forma_local,
    forma_visitante
):

    lambda_local = (
        forma_local["promedio_gf"]
        +
        forma_visitante["promedio_gc"]
    ) / 2

    lambda_visitante = (
        forma_visitante["promedio_gf"]
        +
        forma_local["promedio_gc"]
    ) / 2

    return (
        lambda_local,
        lambda_visitante
    )


# ============================================================
# POISSON
# ============================================================

def probabilidad_poisson(
    media,
    goles
):

    return (
        math.exp(-media)
        *
        media ** goles
        /
        math.factorial(goles)
    )


# ============================================================
# POISSON INDEPENDIENTE
# ============================================================

def probabilidades_poisson(
    lambda_local,
    lambda_visitante
):

    matriz = {}

    for goles_local in range(MAX_GOLES + 1):

        for goles_visitante in range(
            MAX_GOLES + 1
        ):

            probabilidad = (
                probabilidad_poisson(
                    lambda_local,
                    goles_local
                )
                *
                probabilidad_poisson(
                    lambda_visitante,
                    goles_visitante
                )
            )

            matriz[
                (goles_local, goles_visitante)
            ] = probabilidad

    return matriz


# ============================================================
# CORRECCIÓN DIXON-COLES
# ============================================================

def factor_dixon_coles(
    goles_local,
    goles_visitante,
    lambda_local,
    lambda_visitante,
    rho
):

    # 0-0
    if (
        goles_local == 0
        and
        goles_visitante == 0
    ):

        return (
            1
            -
            lambda_local
            *
            lambda_visitante
            *
            rho
        )

    # 0-1
    if (
        goles_local == 0
        and
        goles_visitante == 1
    ):

        return (
            1
            +
            lambda_local
            *
            rho
        )

    # 1-0
    if (
        goles_local == 1
        and
        goles_visitante == 0
    ):

        return (
            1
            +
            lambda_visitante
            *
            rho
        )

    # 1-1
    if (
        goles_local == 1
        and
        goles_visitante == 1
    ):

        return (
            1
            -
            rho
        )

    return 1.0


def probabilidades_dixon_coles(
    lambda_local,
    lambda_visitante,
    rho
):

    matriz = {}

    suma = 0.0

    for goles_local in range(
        MAX_GOLES + 1
    ):

        for goles_visitante in range(
            MAX_GOLES + 1
        ):

            poisson = (
                probabilidad_poisson(
                    lambda_local,
                    goles_local
                )
                *
                probabilidad_poisson(
                    lambda_visitante,
                    goles_visitante
                )
            )

            tau = factor_dixon_coles(
                goles_local,
                goles_visitante,
                lambda_local,
                lambda_visitante,
                rho
            )

            probabilidad = (
                poisson * tau
            )

            # Evitamos probabilidades negativas
            if probabilidad < 0:

                probabilidad = 0

            matriz[
                (goles_local, goles_visitante)
            ] = probabilidad

            suma += probabilidad

    # Normalización por el truncamiento
    if suma <= 0:

        return None

    for marcador in matriz:

        matriz[marcador] /= suma

    return matriz


# ============================================================
# CONVERTIR MATRIZ A 1X2
# ============================================================

def convertir_a_1x2(
    matriz
):

    prob_local = 0.0
    prob_empate = 0.0
    prob_visitante = 0.0

    for (
        goles_local,
        goles_visitante
    ), probabilidad in matriz.items():

        if goles_local > goles_visitante:

            prob_local += probabilidad

        elif goles_local == goles_visitante:

            prob_empate += probabilidad

        else:

            prob_visitante += probabilidad

    return {
        "local": prob_local,
        "empate": prob_empate,
        "visitante": prob_visitante
    }


# ============================================================
# PREDICCIÓN
# ============================================================

def predecir_partido(
    partido,
    partidos,
    rho
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

    (
        lambda_local,
        lambda_visitante
    ) = calcular_goles_esperados(
        forma_local,
        forma_visitante
    )

    if rho == 0:

        matriz = probabilidades_poisson(
            lambda_local,
            lambda_visitante
        )

    else:

        matriz = probabilidades_dixon_coles(
            lambda_local,
            lambda_visitante,
            rho
        )

    if matriz is None:

        return None

    probabilidades = convertir_a_1x2(
        matriz
    )

    return probabilidades


# ============================================================
# EVALUACIÓN
# ============================================================

def evaluar_partido(
    partido,
    probabilidades
):

    goles_local = partido["goles_local"]
    goles_visitante = partido["goles_visitante"]

    if goles_local > goles_visitante:

        resultado_real = "local"

    elif goles_local == goles_visitante:

        resultado_real = "empate"

    else:

        resultado_real = "visitante"

    prediccion = max(
        probabilidades,
        key=probabilidades.get
    )

    return {
        "resultado_real":
            resultado_real,

        "prediccion":
            prediccion,

        "acierto":
            prediccion == resultado_real,

        "probabilidades":
            probabilidades
    }


# ============================================================
# BRIER
# ============================================================

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

    return suma / len(resultados)


# ============================================================
# EJECUTAR BACKTEST
# ============================================================

def ejecutar_modelo(
    partidos,
    temporada,
    rho
):

    resultados = []
    descartados = 0

    for partido in partidos:

        if partido["season"] != temporada:

            continue

        probabilidades = predecir_partido(
            partido,
            partidos,
            rho
        )

        if probabilidades is None:

            descartados += 1

            continue

        evaluacion = evaluar_partido(
            partido,
            probabilidades
        )

        resultados.append(
            evaluacion
        )

    return (
        resultados,
        descartados
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("TUNING POISSON / DIXON-COLES")
    print("=" * 75)

    print()

    print(
        f"Ventana: {VENTANA}"
    )

    print(
        f"Max goles: {MAX_GOLES}"
    )

    print(
        f"Desarrollo: {SEASON_DEVELOPMENT}"
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
    # DESARROLLO 2023
    # ========================================================

    print()
    print("=" * 75)
    print("DESARROLLO 2023")
    print("=" * 75)

    print()

    print(
        f"{'Rho':<12}"
        f"{'Partidos':<12}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 55)

    resultados_tuning = []

    for rho in RHO_VALUES:

        resultados, descartados = (
            ejecutar_modelo(
                partidos,
                SEASON_DEVELOPMENT,
                rho
            )
        )

        if not resultados:

            continue

        aciertos = sum(
            1
            for resultado in resultados
            if resultado["acierto"]
        )

        accuracy = (
            aciertos
            /
            len(resultados)
        )

        brier = calcular_brier(
            resultados
        )

        resultados_tuning.append({
            "rho": rho,
            "partidos": len(resultados),
            "accuracy": accuracy,
            "brier": brier
        })

        print(
            f"{rho:<12.2f}"
            f"{len(resultados):<12}"
            f"{accuracy * 100:>7.2f}%"
            f"{'':<8}"
            f"{brier:.4f}"
        )

    mejor = min(
        resultados_tuning,
        key=lambda x: x["brier"]
    )

    print()

    print("=" * 75)

    print(
        f"MEJOR RHO POR BRIER: "
        f"{mejor['rho']:.2f}"
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
    # TEST 2024
    # ========================================================

    print()
    print("=" * 75)
    print("TEST 2024")
    print("=" * 75)

    print()

    # Poisson original
    resultados_original, _ = (
        ejecutar_modelo(
            partidos,
            SEASON_TEST,
            0.00
        )
    )

    # Mejor rho encontrado solamente
    # usando 2023.
    resultados_dixon, _ = (
        ejecutar_modelo(
            partidos,
            SEASON_TEST,
            mejor["rho"]
        )
    )

    accuracy_original = (
        sum(
            1
            for resultado in resultados_original
            if resultado["acierto"]
        )
        /
        len(resultados_original)
    )

    brier_original = calcular_brier(
        resultados_original
    )

    accuracy_dixon = (
        sum(
            1
            for resultado in resultados_dixon
            if resultado["acierto"]
        )
        /
        len(resultados_dixon)
    )

    brier_dixon = calcular_brier(
        resultados_dixon
    )

    print(
        f"{'Modelo':<28}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 58)

    print(
        f"{'Poisson original':<28}"
        f"{accuracy_original * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_original:.4f}"
    )

    print(
        f"{'Dixon-Coles':<28}"
        f"{accuracy_dixon * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_dixon:.4f}"
    )

    print()

    print(
        f"Diferencia Accuracy: "
        f"{(accuracy_dixon - accuracy_original) * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier: "
        f"{brier_dixon - brier_original:+.4f}"
    )

    print()

    if brier_dixon < brier_original:

        print(
            "RESULTADO: "
            "DIXON-COLES MEJORA EL BRIER."
        )

    elif brier_dixon > brier_original:

        print(
            "RESULTADO: "
            "DIXON-COLES EMPEORA EL BRIER."
        )

    else:

        print(
            "RESULTADO: "
            "NO HAY CAMBIO."
        )

    print()

    print(
        "IMPORTANTE:"
    )

    print(
        "El rho fue seleccionado "
        "exclusivamente con 2023."
    )

    print(
        "2024 fue utilizado únicamente "
        "como TEST."
    )

    print("=" * 75)


if __name__ == "__main__":

    main()