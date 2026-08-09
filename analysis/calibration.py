from database.database import Database
from analysis.backtest import ejecutar_backtest


VENTANA = 5
NUM_BINS = 10

RESULTADOS = [
    "local",
    "empate",
    "visitante"
]


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
            "suma_probabilidad": 0,
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
                and probabilidad <= superior
            ):
                return bin_data

        else:

            if (
                probabilidad >= inferior
                and probabilidad < superior
            ):
                return bin_data

    return None


def construir_calibracion(
    resultados,
    resultado_objetivo
):

    bins = crear_bins()

    for resultado in resultados:

        probabilidades = resultado["probabilidades"]

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

        bin_data["suma_probabilidad"] += probabilidad

        if resultado["resultado_real"] == resultado_objetivo:

            bin_data["aciertos"] += 1

    return bins


def calcular_ece(bins, cantidad_total):

    if cantidad_total == 0:

        return None

    ece = 0

    for bin_data in bins:

        cantidad = bin_data["cantidad"]

        if cantidad == 0:

            continue

        promedio_probabilidad = (
            bin_data["suma_probabilidad"]
            / cantidad
        )

        frecuencia_real = (
            bin_data["aciertos"]
            / cantidad
        )

        peso = cantidad / cantidad_total

        ece += peso * abs(
            promedio_probabilidad
            - frecuencia_real
        )

    return ece


def mostrar_calibracion(
    resultado_objetivo,
    bins,
    cantidad_total
):

    print()
    print("=" * 70)

    print(
        f"CALIBRACIÓN — {resultado_objetivo.upper()}"
    )

    print("=" * 70)

    print()

    print(
        f"{'Rango':<12}"
        f"{'Partidos':<12}"
        f"{'Prob. modelo':<18}"
        f"{'Frecuencia real':<18}"
    )

    print("-" * 70)

    for bin_data in bins:

        cantidad = bin_data["cantidad"]

        if cantidad == 0:

            continue

        promedio_probabilidad = (
            bin_data["suma_probabilidad"]
            / cantidad
        )

        frecuencia_real = (
            bin_data["aciertos"]
            / cantidad
        )

        rango = (
            f"{bin_data['inferior'] * 100:.0f}%"
            f"-"
            f"{bin_data['superior'] * 100:.0f}%"
        )

        print(
            f"{rango:<12}"
            f"{cantidad:<12}"
            f"{promedio_probabilidad * 100:>6.2f}%"
            f"{'':<11}"
            f"{frecuencia_real * 100:>6.2f}%"
        )

    ece = calcular_ece(
        bins,
        cantidad_total
    )

    print()

    print("-" * 70)

    print(
        f"ECE: {ece:.4f}"
    )

    print()

    print(
        "Interpretación:"
    )

    print(
        "Cuanto más cerca de 0 esté el ECE, "
        "mejor calibradas están las probabilidades."
    )

    print()

    print("=" * 70)


def main():

    partidos = obtener_partidos_historicos()

    print(
        f"Partidos disponibles: "
        f"{len(partidos)}"
    )

    print()

    print(
        f"Ejecutando backtest con ventana "
        f"de {VENTANA}..."
    )

    resultados, descartados = ejecutar_backtest(
        partidos,
        ventana=VENTANA
    )

    print()

    print(
        f"Partidos válidos: "
        f"{len(resultados)}"
    )

    print(
        f"Partidos descartados: "
        f"{descartados}"
    )

    if not resultados:

        print(
            "No hay suficientes resultados."
        )

        return

    eces = []

    for resultado_objetivo in RESULTADOS:

        bins = construir_calibracion(
            resultados,
            resultado_objetivo
        )

        mostrar_calibracion(
            resultado_objetivo,
            bins,
            len(resultados)
        )

        ece = calcular_ece(
            bins,
            len(resultados)
        )

        eces.append(ece)

    print()
    print("=" * 70)
    print("RESUMEN DE CALIBRACIÓN")
    print("=" * 70)

    for resultado_objetivo, ece in zip(
        RESULTADOS,
        eces
    ):

        print(
            f"{resultado_objetivo.capitalize():<12}"
            f"ECE: {ece:.4f}"
        )

    ece_promedio = sum(eces) / len(eces)

    print()

    print(
        f"ECE promedio: "
        f"{ece_promedio:.4f}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()