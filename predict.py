from database.database import Database
from analysis.model_v2 import predecir
from value import analizar_apuesta, mostrar_apuesta


def obtener_partido(fixture_id):

    db = Database()

    partido = db.obtener_partido(fixture_id)

    db.cerrar()

    return partido


def mostrar_prediccion(resultado):

    if resultado is None:

        print()
        print("No fue posible generar la predicción.")
        print(
            "El partido no tiene suficientes datos "
            "históricos."
        )

        return

    probabilidades_base = (
        resultado["probabilidades_base"]
    )

    probabilidades = (
        resultado["probabilidades"]
    )

    prediccion = resultado["prediccion"]

    print()
    print("=" * 70)
    print("BETMIND AI — PREDICCIÓN V2")
    print("=" * 70)

    print()

    print("PROBABILIDADES BASE")
    print("-" * 70)

    print(
        f"Local:      "
        f"{probabilidades_base['local'] * 100:.2f}%"
    )

    print(
        f"Empate:     "
        f"{probabilidades_base['empate'] * 100:.2f}%"
    )

    print(
        f"Visitante:  "
        f"{probabilidades_base['visitante'] * 100:.2f}%"
    )

    print()

    print("PROBABILIDADES V2 CALIBRADAS")
    print("-" * 70)

    print(
        f"Local:      "
        f"{probabilidades['local'] * 100:.2f}%"
    )

    print(
        f"Empate:     "
        f"{probabilidades['empate'] * 100:.2f}%"
    )

    print(
        f"Visitante:  "
        f"{probabilidades['visitante'] * 100:.2f}%"
    )

    print()

    print("CUOTAS JUSTAS")
    print("-" * 70)

    for resultado_nombre in [
        "local",
        "empate",
        "visitante"
    ]:

        probabilidad = (
            probabilidades[
                resultado_nombre
            ]
        )

        cuota_justa = 1 / probabilidad

        print(
            f"{resultado_nombre.capitalize():<12}"
            f"{cuota_justa:.2f}"
        )

    print()

    print("PREDICCIÓN")
    print("-" * 70)

    if prediccion == "local":

        print("→ LOCAL")

    elif prediccion == "empate":

        print("→ EMPATE")

    else:

        print("→ VISITANTE")

    # ========================================================
    # ANÁLISIS DE CUOTAS
    # ========================================================

    print()
    print("=" * 70)
    print("ANÁLISIS DE VALOR")
    print("=" * 70)

    print()

    print(
        "Ingresá las cuotas disponibles."
    )

    print(
        "Si no querés analizar un mercado, "
        "presioná ENTER."
    )

    print()

    cuotas = {}

    for resultado_nombre in [
        "local",
        "empate",
        "visitante"
    ]:

        texto = input(
            f"Cuota {resultado_nombre}: "
        ).strip()

        if texto == "":
            continue

        try:

            cuota = float(
                texto.replace(",", ".")
            )

        except ValueError:

            print(
                "Cuota inválida. Se omite."
            )

            continue

        if cuota <= 1:

            print(
                "La cuota debe ser mayor que 1."
            )

            continue

        cuotas[
            resultado_nombre
        ] = cuota

    for resultado_nombre, cuota in cuotas.items():

        datos = analizar_apuesta(
            probabilidades[
                resultado_nombre
            ],
            cuota
        )

        mostrar_apuesta(
            resultado_nombre.upper(),
            datos
        )

    print()
    print("=" * 70)


def main():

    try:

        fixture_id = int(
            input(
                "Ingresá el fixture_id: "
            )
        )

    except ValueError:

        print()
        print(
            "El fixture_id debe ser un número."
        )

        return

    partido = obtener_partido(
        fixture_id
    )

    if partido is None:

        print()
        print(
            "No se encontró el partido."
        )

        return

    print()
    print("=" * 70)
    print("PARTIDO")
    print("=" * 70)

    print()

    print(
        f"{partido['local']} "
        f"vs "
        f"{partido['visitante']}"
    )

    print(
        f"Fecha: {partido['fecha']}"
    )

    print(
        f"Liga: {partido['liga']}"
    )

    resultado = predecir(
        partido
    )

    mostrar_prediccion(
        resultado
    )


if __name__ == "__main__":

    main()