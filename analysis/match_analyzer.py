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


def analizar_ventana(team_id, limite, condicion):

    return analizar_forma_equipo(
        team_id,
        limite=limite,
        condicion=condicion
    )


def analizar_partido(fixture_id):

    db = Database()

    partido = db.obtener_partido(fixture_id)

    db.cerrar()

    if partido is None:

        print("No se encontró el partido.")

        return None

    local_id = partido["home_team_id"]
    visitante_id = partido["away_team_id"]

    analisis_ventanas = {}

    for ventana in VENTANAS:

        forma_local = analizar_ventana(
            local_id,
            ventana,
            "local"
        )

        forma_visitante = analizar_ventana(
            visitante_id,
            ventana,
            "visitante"
        )

        if forma_local is None or forma_visitante is None:

            continue

        goles_esperados = calcular_goles_esperados(
            forma_local,
            forma_visitante
        )

        probabilidades = calcular_probabilidades_partido(
            goles_esperados["local"],
            goles_esperados["visitante"]
        )

        analisis_ventanas[ventana] = {
            "forma_local": forma_local,
            "forma_visitante": forma_visitante,
            "goles_esperados": goles_esperados,
            "probabilidades": probabilidades
        }

    return {
        "partido": partido,
        "ventanas": analisis_ventanas
    }


def mostrar_analisis(analisis):

    if analisis is None:
        return

    partido = analisis["partido"]
    ventanas = analisis["ventanas"]

    print()
    print("=" * 60)
    print("ANÁLISIS MULTIVENTANA")
    print("=" * 60)

    print()
    print(
        f"{partido['local']} vs {partido['visitante']}"
    )

    print(f"Liga: {partido['liga']}")
    print(f"Fecha: {partido['fecha']}")

    for ventana, datos in ventanas.items():

        forma_local = datos["forma_local"]
        forma_visitante = datos["forma_visitante"]
        goles = datos["goles_esperados"]
        probabilidades = datos["probabilidades"]

        print()
        print("-" * 60)
        print(f"ÚLTIMOS {ventana}")
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
        print("GOLES")

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
            f"TOTAL: "
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
            f"Over 2.5: "
            f"{probabilidades['over_2_5'] * 100:.1f}%"
        )

        print(
            f"BTTS: "
            f"{probabilidades['btts'] * 100:.1f}%"
        )

    print()
    print("=" * 60)


def main():

    fixture_id = 1158667

    analisis = analizar_partido(fixture_id)

    mostrar_analisis(analisis)


if __name__ == "__main__":
    main()