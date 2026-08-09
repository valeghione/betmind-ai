import math


def calcular_probabilidad_poisson(
    goles,
    lambda_goles
):

    return (
        math.exp(-lambda_goles)
        * (lambda_goles ** goles)
        / math.factorial(goles)
    )


def calcular_probabilidades_partido(
    lambda_local,
    lambda_visitante
):

    max_goles = 10

    probabilidades_local = {}
    probabilidades_visitante = {}

    for goles in range(max_goles + 1):

        probabilidades_local[goles] = (
            calcular_probabilidad_poisson(
                goles,
                lambda_local
            )
        )

        probabilidades_visitante[goles] = (
            calcular_probabilidad_poisson(
                goles,
                lambda_visitante
            )
        )

    prob_local = 0
    prob_empate = 0
    prob_visitante = 0

    over_0_5 = 0
    over_1_5 = 0
    over_2_5 = 0
    over_3_5 = 0

    btts = 0

    for goles_local in range(max_goles + 1):

        for goles_visitante in range(max_goles + 1):

            probabilidad = (
                probabilidades_local[goles_local]
                *
                probabilidades_visitante[goles_visitante]
            )

            if goles_local > goles_visitante:

                prob_local += probabilidad

            elif goles_local == goles_visitante:

                prob_empate += probabilidad

            else:

                prob_visitante += probabilidad

            goles_totales = (
                goles_local
                +
                goles_visitante
            )

            if goles_totales > 0:
                over_0_5 += probabilidad

            if goles_totales > 1:
                over_1_5 += probabilidad

            if goles_totales > 2:
                over_2_5 += probabilidad

            if goles_totales > 3:
                over_3_5 += probabilidad

            if (
                goles_local > 0
                and goles_visitante > 0
            ):
                btts += probabilidad

    return {
        "local": prob_local,
        "empate": prob_empate,
        "visitante": prob_visitante,

        "over_0_5": over_0_5,
        "over_1_5": over_1_5,
        "over_2_5": over_2_5,
        "over_3_5": over_3_5,

        "under_0_5": 1 - over_0_5,
        "under_1_5": 1 - over_1_5,
        "under_2_5": 1 - over_2_5,
        "under_3_5": 1 - over_3_5,

        "btts": btts,
        "no_btts": 1 - btts
    }