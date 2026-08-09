def calcular_ev(probabilidad, cuota):

    return (
        probabilidad * cuota
    ) - 1


def calcular_cuota_justa(probabilidad):

    if probabilidad <= 0:
        return None

    return 1 / probabilidad


def calcular_probabilidad_implicita(cuota):

    if cuota <= 0:
        return None

    return 1 / cuota


def analizar_apuesta(
    probabilidad,
    cuota
):

    cuota_justa = calcular_cuota_justa(
        probabilidad
    )

    probabilidad_implicita = (
        calcular_probabilidad_implicita(
            cuota
        )
    )

    ev = calcular_ev(
        probabilidad,
        cuota
    )

    return {
        "probabilidad": probabilidad,
        "cuota": cuota,
        "cuota_justa": cuota_justa,
        "probabilidad_implicita":
            probabilidad_implicita,
        "ev": ev
    }


def mostrar_apuesta(
    nombre,
    datos
):

    print()
    print("-" * 60)
    print(nombre)
    print("-" * 60)

    print(
        f"Probabilidad modelo: "
        f"{datos['probabilidad'] * 100:.2f}%"
    )

    print(
        f"Probabilidad implícita: "
        f"{datos['probabilidad_implicita'] * 100:.2f}%"
    )

    print(
        f"Cuota justa: "
        f"{datos['cuota_justa']:.2f}"
    )

    print(
        f"Cuota casa: "
        f"{datos['cuota']:.2f}"
    )

    print(
        f"EV: "
        f"{datos['ev'] * 100:+.2f}%"
    )

    if datos["ev"] > 0:

        print(
            "→ VALOR POSITIVO"
        )

    else:

        print(
            "→ SIN VALOR"
        )