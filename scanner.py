from database.database import Database
from analysis.model_v2 import predecir
from odds import obtener_cuotas_partido


# ============================================================
# OBTENER PARTIDO DE BETMIND
# ============================================================

def obtener_partido(fixture_id):

    db = Database()

    partido = db.obtener_partido(
        fixture_id
    )

    db.cerrar()

    return partido


# ============================================================
# CALCULAR EV
# ============================================================

def calcular_ev(
    probabilidad,
    cuota
):

    return (
        probabilidad * cuota
    ) - 1


# ============================================================
# MOSTRAR VALUE
# ============================================================

def analizar_value(
    probabilidades,
    cuotas
):

    resultados = [
        "local",
        "empate",
        "visitante"
    ]

    analisis = []

    for resultado in resultados:

        probabilidad = probabilidades[
            resultado
        ]

        cuota = cuotas[
            resultado
        ]

        cuota_justa = (
            1 / probabilidad
        )

        probabilidad_implicita = (
            1 / cuota
        )

        ev = calcular_ev(
            probabilidad,
            cuota
        )

        analisis.append({

            "resultado": resultado,

            "probabilidad":
                probabilidad,

            "cuota":
                cuota,

            "cuota_justa":
                cuota_justa,

            "probabilidad_implicita":
                probabilidad_implicita,

            "ev":
                ev
        })

    return analisis


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

def mostrar_scanner(
    partido,
    prediccion,
    cuotas_resultado
):

    probabilidades = (
        prediccion["probabilidades"]
    )

    analisis = analizar_value(
        probabilidades,
        cuotas_resultado["cuotas"]
    )

    print()
    print("=" * 75)
    print("BETMIND VALUE SCANNER")
    print("=" * 75)

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
        f"Bookmaker: "
        f"{cuotas_resultado['bookmaker']}"
    )

    print()

    # --------------------------------------------------------
    # V2
    # --------------------------------------------------------

    print("PROBABILIDADES V2")
    print("-" * 75)

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

    # --------------------------------------------------------
    # CUOTAS
    # --------------------------------------------------------

    print("CUOTAS BET365")
    print("-" * 75)

    print(
        f"Local:      "
        f"{cuotas_resultado['cuotas']['local']:.2f}"
    )

    print(
        f"Empate:     "
        f"{cuotas_resultado['cuotas']['empate']:.2f}"
    )

    print(
        f"Visitante:  "
        f"{cuotas_resultado['cuotas']['visitante']:.2f}"
    )

    print()

    # --------------------------------------------------------
    # VALUE
    # --------------------------------------------------------

    print("ANÁLISIS DE VALUE")
    print("-" * 75)

    print(
        f"{'Resultado':<12}"
        f"{'Modelo':<12}"
        f"{'Cuota':<10}"
        f"{'Justa':<10}"
        f"{'Implícita':<12}"
        f"{'EV':<10}"
        f"Estado"
    )

    print("-" * 75)

    for dato in analisis:

        resultado = dato["resultado"]

        nombre = {
            "local": "Local",
            "empate": "Empate",
            "visitante": "Visitante"
        }[resultado]

        ev = dato["ev"]

        estado = (
            "VALUE"
            if ev > 0
            else "SIN VALUE"
        )

        print(
            f"{nombre:<12}"
            f"{dato['probabilidad'] * 100:>6.2f}%   "
            f"{dato['cuota']:<10.2f}"
            f"{dato['cuota_justa']:<10.2f}"
            f"{dato['probabilidad_implicita'] * 100:>6.2f}%   "
            f"{ev * 100:>7.2f}%  "
            f"{estado}"
        )

    # --------------------------------------------------------
    # MEJOR VALUE
    # --------------------------------------------------------

    mejor = max(
        analisis,
        key=lambda x: x["ev"]
    )

    print()
    print("=" * 75)
    print("MEJOR OPORTUNIDAD")
    print("=" * 75)

    nombre_mejor = {
        "local": "LOCAL",
        "empate": "EMPATE",
        "visitante": "VISITANTE"
    }[mejor["resultado"]]

    print()

    print(
        f"→ {nombre_mejor}"
    )

    print(
        f"Probabilidad modelo: "
        f"{mejor['probabilidad'] * 100:.2f}%"
    )

    print(
        f"Cuota: "
        f"{mejor['cuota']:.2f}"
    )

    print(
        f"Cuota justa: "
        f"{mejor['cuota_justa']:.2f}"
    )

    print(
        f"EV: "
        f"{mejor['ev'] * 100:.2f}%"
    )

    if mejor["ev"] > 0:

        print(
            "→ VALUE POSITIVO"
        )

    else:

        print(
            "→ SIN VALUE"
        )

    print()

    # --------------------------------------------------------
    # PREDICCIÓN DEL MODELO
    # --------------------------------------------------------

    print("=" * 75)
    print("PREDICCIÓN V2")
    print("=" * 75)

    print()

    prediccion_nombre = {
        "local": "LOCAL",
        "empate": "EMPATE",
        "visitante": "VISITANTE"
    }[
        prediccion["prediccion"]
    ]

    print(
        f"→ {prediccion_nombre}"
    )

    print()

    print("=" * 75)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("BETMIND AI — VALUE SCANNER")
    print("=" * 75)

    print()

    try:

        fixture_id = int(
            input(
                "Ingresá el fixture_id: "
            )
        )

    except ValueError:

        print()
        print(
            "ERROR: el fixture_id "
            "debe ser numérico."
        )

        return

    # --------------------------------------------------------
    # PARTIDO
    # --------------------------------------------------------

    partido = obtener_partido(
        fixture_id
    )

    if partido is None:

        print()
        print(
            "No se encontró el partido "
            "en la base de datos."
        )

        return

    print()

    print(
        f"Partido: "
        f"{partido['local']} "
        f"vs "
        f"{partido['visitante']}"
    )

    print(
        f"Fecha: "
        f"{partido['fecha']}"
    )

    # --------------------------------------------------------
    # PREDICCIÓN V2
    # --------------------------------------------------------

    print()
    print(
        "Calculando V2..."
    )

    resultado_v2 = predecir(
        partido
    )

    if resultado_v2 is None:

        print()
        print(
            "No fue posible generar "
            "la predicción V2."
        )

        print(
            "No hay suficientes datos "
            "históricos."
        )

        return

    # --------------------------------------------------------
    # CUOTAS
    # --------------------------------------------------------

    print(
        "Buscando cuotas Bet365..."
    )

    try:

        cuotas = obtener_cuotas_partido(
            partido["local"],
            partido["visitante"]
        )

    except Exception as error:

        print()
        print(
            "ERROR AL OBTENER CUOTAS:"
        )

        print(error)

        return

    if cuotas is None:

        print()
        print(
            "No se encontraron cuotas "
            "1X2 para este partido."
        )

        return

    # --------------------------------------------------------
    # MOSTRAR
    # --------------------------------------------------------

    mostrar_scanner(
        partido,
        resultado_v2,
        cuotas
    )


if __name__ == "__main__":

    main()