from database.database import Database
from analysis.backtest import ejecutar_backtest
from analysis.poisson import calcular_probabilidades_partido


VENTANA = 5

SEASON_DEVELOPMENT = 2023
SEASON_TEST = 2024

PESOS = [
    0.00,
    0.25,
    0.50,
    0.75,
    1.00
]


# ============================================================
# DATOS
# ============================================================

def obtener_partidos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


def obtener_promedio_liga(
    partidos,
    fecha_hasta
):

    goles_local = 0
    goles_visitante = 0
    cantidad = 0

    for partido in partidos:

        if partido["fecha"] >= fecha_hasta:
            continue

        if partido["estado"] != "FT":
            continue

        if (
            partido["goles_local"] is None
            or
            partido["goles_visitante"] is None
        ):
            continue

        goles_local += partido["goles_local"]
        goles_visitante += partido["goles_visitante"]

        cantidad += 1

    if cantidad == 0:

        return None

    return {
        "promedio_local":
            goles_local / cantidad,

        "promedio_visitante":
            goles_visitante / cantidad,

        "partidos":
            cantidad
    }


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

    seleccionados = seleccionados[
        :VENTANA
    ]

    if len(seleccionados) < VENTANA:

        return None

    goles_favor = 0
    goles_contra = 0

    for partido in seleccionados:

        if condicion == "local":

            goles_favor += (
                partido["goles_local"]
            )

            goles_contra += (
                partido["goles_visitante"]
            )

        else:

            goles_favor += (
                partido["goles_visitante"]
            )

            goles_contra += (
                partido["goles_local"]
            )

    cantidad = len(seleccionados)

    return {
        "partidos": cantidad,

        "promedio_gf":
            goles_favor / cantidad,

        "promedio_gc":
            goles_contra / cantidad
    }


# ============================================================
# MODELO A
# ============================================================

def goles_modelo_a(
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
# MODELO B
# ============================================================

def goles_modelo_b(
    forma_local,
    forma_visitante,
    promedio_liga
):

    media_local = (
        promedio_liga["promedio_local"]
    )

    media_visitante = (
        promedio_liga["promedio_visitante"]
    )

    if (
        media_local <= 0
        or
        media_visitante <= 0
    ):

        return None

    ataque_local = (
        forma_local["promedio_gf"]
        /
        media_local
    )

    defensa_local = (
        forma_local["promedio_gc"]
        /
        media_visitante
    )

    ataque_visitante = (
        forma_visitante["promedio_gf"]
        /
        media_visitante
    )

    defensa_visitante = (
        forma_visitante["promedio_gc"]
        /
        media_local
    )

    lambda_local = (
        media_local
        *
        ataque_local
        *
        defensa_visitante
    )

    lambda_visitante = (
        media_visitante
        *
        ataque_visitante
        *
        defensa_local
    )

    return (
        lambda_local,
        lambda_visitante
    )


# ============================================================
# PREDICCIÓN
# ============================================================

def predecir_partido(
    partido,
    partidos,
    peso
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

    promedio_liga = obtener_promedio_liga(
        partidos,
        fecha_hasta
    )

    if promedio_liga is None:
        return None

    modelo_a = goles_modelo_a(
        forma_local,
        forma_visitante
    )

    modelo_b = goles_modelo_b(
        forma_local,
        forma_visitante,
        promedio_liga
    )

    if modelo_b is None:
        return None

    lambda_a_local, lambda_a_visitante = (
        modelo_a
    )

    lambda_b_local, lambda_b_visitante = (
        modelo_b
    )

    lambda_local = (
        (1 - peso)
        *
        lambda_a_local
        +
        peso
        *
        lambda_b_local
    )

    lambda_visitante = (
        (1 - peso)
        *
        lambda_a_visitante
        +
        peso
        *
        lambda_b_visitante
    )

    probabilidades = (
        calcular_probabilidades_partido(
            lambda_local,
            lambda_visitante
        )
    )

    return probabilidades


# ============================================================
# EVALUACIÓN
# ============================================================

def evaluar_partido(
    partido,
    probabilidades
):

    goles_local = partido[
        "goles_local"
    ]

    goles_visitante = partido[
        "goles_visitante"
    ]

    if goles_local > goles_visitante:

        resultado_real = "local"

    elif goles_local == goles_visitante:

        resultado_real = "empate"

    else:

        resultado_real = "visitante"

    prediccion = max(
        {
            "local":
                probabilidades["local"],

            "empate":
                probabilidades["empate"],

            "visitante":
                probabilidades["visitante"]
        },
        key=lambda x:
            probabilidades[x]
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


def calcular_brier(resultados):

    if not resultados:

        return None

    suma = 0

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


# ============================================================
# BACKTEST
# ============================================================

def ejecutar_modelo(
    partidos,
    temporada,
    peso
):

    resultados = []

    descartados = 0

    for partido in partidos:

        if partido["season"] != temporada:
            continue

        probabilidades = predecir_partido(
            partido,
            partidos,
            peso
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
    print("TUNING DE GOLES ESPERADOS")
    print("=" * 75)

    print()

    print(
        f"Ventana: {VENTANA}"
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
        f"{'Peso Modelo B':<18}"
        f"{'Partidos':<12}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 60)

    resultados_tuning = []

    for peso in PESOS:

        resultados, descartados = (
            ejecutar_modelo(
                partidos,
                SEASON_DEVELOPMENT,
                peso
            )
        )

        accuracy = (
            sum(
                1
                for r in resultados
                if r["acierto"]
            )
            /
            len(resultados)
            if resultados
            else 0
        )

        brier = calcular_brier(
            resultados
        )

        resultados_tuning.append({
            "peso": peso,
            "accuracy": accuracy,
            "brier": brier,
            "partidos": len(resultados)
        })

        print(
            f"{peso:<18.2f}"
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
        f"MEJOR PESO: "
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
    # TEST 2024
    # ========================================================

    print()
    print("=" * 75)
    print("TEST 2024")
    print("=" * 75)

    print()

    resultados_a, descartados_a = (
        ejecutar_modelo(
            partidos,
            SEASON_TEST,
            0.00
        )
    )

    resultados_mejor, descartados_mejor = (
        ejecutar_modelo(
            partidos,
            SEASON_TEST,
            mejor["peso"]
        )
    )

    accuracy_a = (
        sum(
            1
            for r in resultados_a
            if r["acierto"]
        )
        /
        len(resultados_a)
    )

    brier_a = calcular_brier(
        resultados_a
    )

    accuracy_mejor = (
        sum(
            1
            for r in resultados_mejor
            if r["acierto"]
        )
        /
        len(resultados_mejor)
    )

    brier_mejor = calcular_brier(
        resultados_mejor
    )

    print(
        f"{'Modelo':<25}"
        f"{'Accuracy':<15}"
        f"{'Brier':<15}"
    )

    print("-" * 55)

    print(
        f"{'Modelo A actual':<25}"
        f"{accuracy_a * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_a:.4f}"
    )

    print(
        f"{'Mejor mezcla':<25}"
        f"{accuracy_mejor * 100:>7.2f}%"
        f"{'':<8}"
        f"{brier_mejor:.4f}"
    )

    print()

    print(
        f"Diferencia Accuracy: "
        f"{(accuracy_mejor - accuracy_a) * 100:+.2f} puntos"
    )

    print(
        f"Diferencia Brier: "
        f"{brier_mejor - brier_a:+.4f}"
    )

    print()

    if brier_mejor < brier_a:

        print(
            "RESULTADO: "
            "EL NUEVO MODELO MEJORA."
        )

    elif brier_mejor > brier_a:

        print(
            "RESULTADO: "
            "EL NUEVO MODELO EMPEORA."
        )

    else:

        print(
            "RESULTADO: "
            "NO HAY CAMBIO."
        )

    print()

    print(
        "2024 fue utilizado únicamente "
        "como TEST."
    )

    print("=" * 75)


if __name__ == "__main__":

    main()