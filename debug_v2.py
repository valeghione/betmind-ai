from database.database import Database

from analysis.model_v2 import (
    obtener_partidos,
    generar_probabilidades_base,
    entrenar,
    aplicar_calibracion,
    obtener_resultado_real
)

from analysis.analyzer import analizar_forma_equipo
from analysis.match_analyzer import calcular_goles_esperados


# ============================================================
# CONFIGURACIÓN
# ============================================================

FIXTURE_ID = 1158667


# ============================================================
# OBTENER PARTIDO
# ============================================================

def obtener_partido(fixture_id):

    db = Database()

    partido = db.obtener_partido(
        fixture_id
    )

    db.cerrar()

    return partido


# ============================================================
# MOSTRAR BINS DE CALIBRACIÓN
# ============================================================

def mostrar_calibradores(calibradores):

    print()
    print("=" * 80)
    print("CALIBRADORES V2 — ENTRENAMIENTO 2023")
    print("=" * 80)

    for resultado in [
        "local",
        "empate",
        "visitante"
    ]:

        print()
        print(
            f"RESULTADO: {resultado.upper()}"
        )

        print(
            f"{'BIN':<8}"
            f"{'RANGO':<15}"
            f"{'N':<8}"
            f"{'MEDIA P':<12}"
            f"{'ACIER.':<10}"
            f"{'CALIB.':<10}"
        )

        print("-" * 70)

        bins = calibradores[
            resultado
        ]

        for i, bin_data in enumerate(bins):

            cantidad = (
                bin_data["cantidad"]
            )

            suma_probabilidad = (
                bin_data[
                    "suma_probabilidad"
                ]
            )

            aciertos = (
                bin_data["aciertos"]
            )

            if cantidad > 0:

                media_probabilidad = (
                    suma_probabilidad
                    /
                    cantidad
                )

                calibrada = (
                    aciertos + 1
                ) / (
                    cantidad + 2
                )

                print(
                    f"{i:<8}"
                    f"{bin_data['inferior']:.1f}"
                    f" - "
                    f"{bin_data['superior']:.1f}"
                    f"{cantidad:<8}"
                    f"{media_probabilidad:<12.4f}"
                    f"{aciertos:<10}"
                    f"{calibrada:<10.4f}"
                )


# ============================================================
# MOSTRAR FORMA
# ============================================================

def mostrar_forma(
    titulo,
    forma
):

    print()
    print(titulo)
    print("-" * 80)

    if forma is None:

        print(
            "SIN DATOS"
        )

        return

    print(
        f"Partidos: "
        f"{forma['partidos']}"
    )

    print(
        f"Victorias: "
        f"{forma['victorias']}"
    )

    print(
        f"Empates: "
        f"{forma['empates']}"
    )

    print(
        f"Derrotas: "
        f"{forma['derrotas']}"
    )

    print()

    print(
        f"Goles a favor: "
        f"{forma['goles_favor']}"
    )

    print(
        f"Goles en contra: "
        f"{forma['goles_contra']}"
    )

    print()

    print(
        f"Promedio GF: "
        f"{forma['promedio_gf']:.4f}"
    )

    print(
        f"Promedio GC: "
        f"{forma['promedio_gc']:.4f}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("BETMIND AI — DEBUG V2")
    print("=" * 80)

    print()

    try:

        fixture_id = int(
            input(
                f"Fixture ID "
                f"[ENTER = {FIXTURE_ID}]: "
            )
            or FIXTURE_ID
        )

    except ValueError:

        print(
            "Fixture ID inválido."
        )

        return

    # ========================================================
    # PARTIDO
    # ========================================================

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
    print("=" * 80)
    print("PARTIDO")
    print("=" * 80)

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
        f"Temporada: "
        f"{partido['season']}"
    )

    print(
        f"Home ID: "
        f"{partido['home_team_id']}"
    )

    print(
        f"Away ID: "
        f"{partido['away_team_id']}"
    )

    # ========================================================
    # FORMA
    # ========================================================

    forma_local = analizar_forma_equipo(
        partido["home_team_id"],
        limite=5,
        condicion="local",
        fecha_hasta=partido["fecha"]
    )

    forma_visitante = analizar_forma_equipo(
        partido["away_team_id"],
        limite=5,
        condicion="visitante",
        fecha_hasta=partido["fecha"]
    )

    mostrar_forma(
        "FORMA LOCAL — ÚLTIMOS 5 COMO LOCAL",
        forma_local
    )

    mostrar_forma(
        "FORMA VISITANTE — ÚLTIMOS 5 COMO VISITANTE",
        forma_visitante
    )

    if (
        forma_local is None
        or
        forma_visitante is None
    ):

        print()
        print(
            "No hay suficiente información "
            "para continuar."
        )

        return

    # ========================================================
    # GOLES ESPERADOS
    # ========================================================

    goles_esperados = calcular_goles_esperados(
        forma_local,
        forma_visitante
    )

    print()
    print("=" * 80)
    print("GOLES ESPERADOS")
    print("=" * 80)

    print()

    print(
        f"Local:      "
        f"{goles_esperados['local']:.4f}"
    )

    print(
        f"Visitante:  "
        f"{goles_esperados['visitante']:.4f}"
    )

    print(
        f"Total:      "
        f"{goles_esperados['total']:.4f}"
    )

    # ========================================================
    # PROBABILIDADES BASE
    # ========================================================

    partidos = obtener_partidos()

    probabilidades_base = (
        generar_probabilidades_base(
            partido,
            partidos
        )
    )

    if probabilidades_base is None:

        print()
        print(
            "No se pudieron generar "
            "probabilidades base."
        )

        return

    print()
    print("=" * 80)
    print("PROBABILIDADES BASE")
    print("=" * 80)

    print()

    for resultado in [
        "local",
        "empate",
        "visitante"
    ]:

        print(
            f"{resultado.capitalize():<12}"
            f"{probabilidades_base[resultado] * 100:.4f}%"
        )

    print()

    print(
        f"Suma: "
        f"{sum(probabilidades_base.values()):.6f}"
    )

    # ========================================================
    # CALIBRADORES
    # ========================================================

    print()
    print(
        "Construyendo calibradores..."
    )

    calibradores = entrenar()

    mostrar_calibradores(
        calibradores
    )

    # ========================================================
    # CALIBRACIÓN
    # ========================================================

    probabilidades_calibradas = (
        aplicar_calibracion(
            probabilidades_base,
            calibradores
        )
    )

    print()
    print("=" * 80)
    print("PROBABILIDADES V2 CALIBRADAS")
    print("=" * 80)

    print()

    for resultado in [
        "local",
        "empate",
        "visitante"
    ]:

        probabilidad_base = (
            probabilidades_base[
                resultado
            ]
        )

        probabilidad_final = (
            probabilidades_calibradas[
                resultado
            ]
        )

        cambio = (
            probabilidad_final
            -
            probabilidad_base
        )

        print(
            f"{resultado.capitalize():<12}"
            f"Base: "
            f"{probabilidad_base * 100:>7.3f}%   "
            f"Final: "
            f"{probabilidad_final * 100:>7.3f}%   "
            f"Cambio: "
            f"{cambio * 100:>+7.3f} puntos"
        )

    print()

    print(
        f"Suma final: "
        f"{sum(probabilidades_calibradas.values()):.6f}"
    )

    # ========================================================
    # PREDICCIÓN
    # ========================================================

    prediccion = max(
        probabilidades_calibradas,
        key=probabilidades_calibradas.get
    )

    print()
    print("=" * 80)
    print("PREDICCIÓN FINAL")
    print("=" * 80)

    print()

    print(
        f"→ {prediccion.upper()}"
    )

    # ========================================================
    # RESULTADO REAL
    # ========================================================

    if (
        partido["goles_local"]
        is not None
        and
        partido["goles_visitante"]
        is not None
    ):

        resultado_real = (
            obtener_resultado_real(
                partido
            )
        )

        print()

        print(
            f"Resultado real: "
            f"{resultado_real.upper()}"
        )

        print(
            f"Marcador: "
            f"{partido['goles_local']} - "
            f"{partido['goles_visitante']}"
        )

    print()
    print("=" * 80)


if __name__ == "__main__":

    main()