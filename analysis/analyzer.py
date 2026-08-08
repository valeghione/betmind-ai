from database.database import Database


def analizar_forma_equipo(team_id, limite=5, condicion=None):

    db = Database()

    partidos = db.obtener_ultimos_partidos_equipo(
        team_id,
        limite,
        condicion
    )

    db.cerrar()

    if not partidos:
        return None

    victorias = 0
    empates = 0
    derrotas = 0

    goles_favor = 0
    goles_contra = 0

    partidos_over_1_5 = 0
    partidos_over_2_5 = 0
    partidos_btts = 0

    for partido in partidos:

        goles_local = partido["goles_local"]
        goles_visitante = partido["goles_visitante"]

        if partido["home_team_id"] == team_id:

            goles_favor += goles_local
            goles_contra += goles_visitante

            if goles_local > goles_visitante:
                victorias += 1

            elif goles_local == goles_visitante:
                empates += 1

            else:
                derrotas += 1

        else:

            goles_favor += goles_visitante
            goles_contra += goles_local

            if goles_visitante > goles_local:
                victorias += 1

            elif goles_visitante == goles_local:
                empates += 1

            else:
                derrotas += 1

        goles_totales = goles_local + goles_visitante

        if goles_totales > 1:
            partidos_over_1_5 += 1

        if goles_totales > 2:
            partidos_over_2_5 += 1

        if goles_local > 0 and goles_visitante > 0:
            partidos_btts += 1

    cantidad = len(partidos)

    return {
        "partidos": cantidad,

        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,

        "goles_favor": goles_favor,
        "goles_contra": goles_contra,

        "promedio_gf": goles_favor / cantidad,
        "promedio_gc": goles_contra / cantidad,

        "over_1_5": partidos_over_1_5 / cantidad,
        "over_2_5": partidos_over_2_5 / cantidad,
        "btts": partidos_btts / cantidad,
    }


def mostrar_forma(titulo, estadisticas):

    print()
    print("=" * 40)
    print(titulo)
    print("=" * 40)

    if estadisticas is None:

        print("No hay partidos disponibles.")
        return

    print(f"Partidos analizados: {estadisticas['partidos']}")

    print()
    print(f"Victorias: {estadisticas['victorias']}")
    print(f"Empates: {estadisticas['empates']}")
    print(f"Derrotas: {estadisticas['derrotas']}")

    print()
    print(f"Goles a favor: {estadisticas['goles_favor']}")
    print(f"Goles en contra: {estadisticas['goles_contra']}")

    print()
    print(f"Promedio GF: {estadisticas['promedio_gf']:.2f}")
    print(f"Promedio GC: {estadisticas['promedio_gc']:.2f}")

    print()
    print(f"Over 1.5: {estadisticas['over_1_5'] * 100:.1f}%")
    print(f"Over 2.5: {estadisticas['over_2_5'] * 100:.1f}%")
    print(f"BTTS: {estadisticas['btts'] * 100:.1f}%")

    print("=" * 40)


def main():

    team_id = 474

    forma_general = analizar_forma_equipo(
        team_id,
        limite=5
    )

    forma_local = analizar_forma_equipo(
        team_id,
        limite=5,
        condicion="local"
    )

    forma_visitante = analizar_forma_equipo(
        team_id,
        limite=5,
        condicion="visitante"
    )

    mostrar_forma(
        "FORMA GENERAL - SARMIENTO",
        forma_general
    )

    mostrar_forma(
        "FORMA COMO LOCAL - SARMIENTO",
        forma_local
    )

    mostrar_forma(
        "FORMA COMO VISITANTE - SARMIENTO",
        forma_visitante
    )


if __name__ == "__main__":
    main()