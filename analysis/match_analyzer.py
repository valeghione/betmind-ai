from database.database import Database
from analysis.analyzer import analizar_forma_equipo
from analysis.poisson import calcular_probabilidades_partido


VENTANAS = [5, 10, 15]


def calcular_goles_esperados(forma_local, forma_visitante):

    goles_esperados_local = (
        forma_local["promedio_gf"]
        + forma_visitante["promedio_gc"]
    ) / 2

    goles_esperados_visitante = (
        forma_visitante["promedio_gf"]
        + forma_local["promedio_gc"]
    ) / 2

    total_esperado = (
        goles_esperados_local
        + goles_esperados_visitante
    )

    return {
        "local": goles_esperados_local,
        "visitante": goles_esperados_visitante,
        "total": total_esperado
    }


def analizar_ventana(
    local_id,
    visitante_id,
    ventana,
    fecha_hasta
):

    forma_local = analizar_forma_equipo(
        local_id,
        limite=ventana,
        condicion="local",
        fecha_hasta=fecha_hasta
    )

    forma_visitante = analizar_forma_equipo(
        visitante_id,
        limite=ventana,
        condicion="visitante",
        fecha_hasta=fecha_hasta
    )

    if forma_local is None or forma_visitante is None:

        return None

    goles_esperados = calcular_goles_esperados(
        forma_local,
        forma_visitante
    )

    probabilidades = calcular_probabilidades_partido(
        goles_esperados["local"],
        goles_esperados["visitante"]
    )

    return {
        "forma_local": forma_local,
        "forma_visitante": forma_visitante,
        "goles_esperados": goles_esperados,
        "probabilidades": probabilidades
    }


def analizar_partido(fixture_id):

    db = Database()

    partido = db.obtener_partido(fixture_id)

    db.cerrar()

    if partido is None:

        print("No se encontró el partido.")

        return None

    local_id = partido["home_team_id"]
    visitante_id = partido["away_team_id"]

    fecha_hasta = partido["fecha"]

    ventanas = {}

    for ventana in VENTANAS:

        resultado = analizar_ventana(
            local_id,
            visitante_id,
            ventana,
            fecha_hasta
        )

        if resultado is not None:

            ventanas[ventana] = resultado

    return {
        "partido": partido,
        "ventanas": ventanas
    }


def mostrar_analisis(analisis):

    if analisis is None:
        return

    partido = analisis["partido"]
    ventanas = analisis["ventanas"]

    print()
    print("=" * 60)
    print("BACKTEST - ANÁLISIS HISTÓRICO")
    print("=" * 60)

    print()
    print(
        f"{partido['local']} vs {partido['visitante']}"
    )

    print(f"Liga: {partido['liga']}")
    print(f"Fecha del partido: {partido['fecha']}")

    print()
    print(
        "IMPORTANTE: solo se utilizan partidos "
        "anteriores a la fecha del encuentro."
    )

    for ventana, datos in ventanas.items():

        forma_local = datos["forma_local"]
        forma_visitante = datos["forma_visitante"]
        goles = datos["goles_esperados"]
        probabilidades = datos["probabilidades"]

        print()
        print("-" * 60)
        print(f"ÚLTIMOS {ventana} ANTERIORES AL PARTIDO")
        print("-" * 60)

        print()
        print("FORMA")

        print(
            f"{partido['local']}: "
            f"{forma_local['victorias']}G "
            f"{forma_local['empates']}E "
            f"{forma_local['derrotas']}P"
        )

        print(
            f"{partido['visitante']}: "
            f"{forma_visitante['victorias']}G "
            f"{forma_visitante['empates']}E "
            f"{forma_visitante['derrotas']}P"
        )

        print()
        print("GOLES PROMEDIO")

        print(
            f"{partido['local']} GF: "
            f"{forma_local['promedio_gf']:.2f}"
        )

        print(
            f"{partido['local']} GC: "
            f"{forma_local['promedio_gc']:.2f}"
        )

        print(
            f"{partido['visitante']} GF: "
            f"{forma_visitante['promedio_gf']:.2f}"
        )

        print(
            f"{partido['visitante']} GC: "
            f"{forma_visitante['promedio_gc']:.2f}"
        )

        print()
        print("GOLES ESPERADOS")

        print(
            f"{partido['local']}: "
            f"{goles['local']:.2f}"
        )

        print(
            f"{partido['visitante']}: "
            f"{goles['visitante']:.2f}"
        )

        print(
            f"Total: "
            f"{goles['total']:.2f}"
        )

        print()
        print("PROBABILIDADES")

        print(
            f"{partido['local']}: "
            f"{probabilidades['local'] * 100:.1f}%"
        )

        print(
            f"Empate: "
            f"{probabilidades['empate'] * 100:.1f}%"
        )

        print(
            f"{partido['visitante']}: "
            f"{probabilidades['visitante'] * 100:.1f}%"
        )

        print(
            f"Over 1.5: "
            f"{probabilidades['over_1_5'] * 100:.1f}%"
        )

        print(
            f"Over 2.5: "
            f"{probabilidades['over_2_5'] * 100:.1f}%"
        )

        print(
            f"BTTS: "
            f"{probabilidades['btts'] * 100:.1f}%"
        )

    print()
    print("=" * 60)

    print()
    print("RESULTADO REAL")
    print(
        f"{partido['local']} "
        f"{partido['goles_local']} - "
        f"{partido['goles_visitante']} "
        f"{partido['visitante']}"
    )

    print("=" * 60)


def main():

    fixture_id = 1158667

    analisis = analizar_partido(fixture_id)

    mostrar_analisis(analisis)


if __name__ == "__main__":
    main()