import math


def probabilidad_goles(media, goles):

    return (
        math.exp(-media)
        * media ** goles
        / math.factorial(goles)
    )


def probabilidades_equipo(media, max_goles=10):

    probabilidades = {}

    for goles in range(max_goles + 1):

        probabilidades[goles] = probabilidad_goles(
            media,
            goles
        )

    return probabilidades


def calcular_probabilidades_partido(
    media_local,
    media_visitante,
    max_goles=10
):

    probabilidades_local = probabilidades_equipo(
        media_local,
        max_goles
    )

    probabilidades_visitante = probabilidades_equipo(
        media_visitante,
        max_goles
    )

    prob_local = 0
    prob_empate = 0
    prob_visitante = 0

    prob_over_0_5 = 0
    prob_over_1_5 = 0
    prob_over_2_5 = 0
    prob_over_3_5 = 0

    prob_btts = 0

    for goles_local in probabilidades_local:

        for goles_visitante in probabilidades_visitante:

            probabilidad = (
                probabilidades_local[goles_local]
                * probabilidades_visitante[goles_visitante]
            )

            goles_totales = (
                goles_local + goles_visitante
            )

            if goles_local > goles_visitante:

                prob_local += probabilidad

            elif goles_local == goles_visitante:

                prob_empate += probabilidad

            else:

                prob_visitante += probabilidad

            if goles_totales > 0:

                prob_over_0_5 += probabilidad

            if goles_totales > 1:

                prob_over_1_5 += probabilidad

            if goles_totales > 2:

                prob_over_2_5 += probabilidad

            if goles_totales > 3:

                prob_over_3_5 += probabilidad

            if goles_local > 0 and goles_visitante > 0:

                prob_btts += probabilidad

    return {

        "local": prob_local,
        "empate": prob_empate,
        "visitante": prob_visitante,

        "over_0_5": prob_over_0_5,
        "over_1_5": prob_over_1_5,
        "over_2_5": prob_over_2_5,
        "over_3_5": prob_over_3_5,

        "under_0_5": 1 - prob_over_0_5,
        "under_1_5": 1 - prob_over_1_5,
        "under_2_5": 1 - prob_over_2_5,
        "under_3_5": 1 - prob_over_3_5,

        "btts": prob_btts,
        "no_btts": 1 - prob_btts
    }