from database.database import Database


def main():

    db = Database()

    print("=" * 60)
    print("DIAGNÓSTICO DE BASE DE DATOS")
    print("=" * 60)

    # =========================================================
    # 1. MOSTRAR ESTRUCTURA REAL DE LA TABLA
    # =========================================================

    db.cursor.execute("""
        PRAGMA table_info(matches)
    """)

    columnas = db.cursor.fetchall()

    print()
    print("=" * 60)
    print("COLUMNAS DE LA TABLA matches")
    print("=" * 60)

    nombres_columnas = []

    for columna in columnas:

        # PRAGMA devuelve:
        # cid, name, type, notnull, dflt_value, pk

        nombre = columna[1]
        tipo = columna[2]

        nombres_columnas.append(nombre)

        print(
            f"{nombre:<25} {tipo}"
        )

    # =========================================================
    # 2. PARTIDOS 2023 FT
    # =========================================================

    db.cursor.execute("""
        SELECT COUNT(*)
        FROM matches
        WHERE league_id = 128
          AND season = 2023
          AND estado = 'FT'
    """)

    partidos_2023_ft = db.cursor.fetchone()[0]

    print()
    print(
        f"2023 FT: {partidos_2023_ft}"
    )

    # =========================================================
    # 3. PARTIDOS 2023 CON GOLES
    # =========================================================

    db.cursor.execute("""
        SELECT COUNT(*)
        FROM matches
        WHERE league_id = 128
          AND season = 2023
          AND estado = 'FT'
          AND goles_local IS NOT NULL
          AND goles_visitante IS NOT NULL
    """)

    partidos_2023_goles = db.cursor.fetchone()[0]

    print(
        f"2023 con goles: {partidos_2023_goles}"
    )

    # =========================================================
    # 4. TOTAL DE PARTIDOS
    # =========================================================

    db.cursor.execute("""
        SELECT COUNT(*)
        FROM matches
        WHERE league_id = 128
    """)

    total_partidos = db.cursor.fetchone()[0]

    print(
        f"Partidos cargados: {total_partidos}"
    )

    # =========================================================
    # 5. PRIMER PARTIDO
    #
    # NO asumimos nombres de columnas de equipos.
    # Buscamos automáticamente columnas posibles.
    # =========================================================

    posibles_local = [
        "home_team",
        "local_team",
        "equipo_local",
        "home_name",
        "local_name"
    ]

    posibles_visitante = [
        "away_team",
        "visitante_team",
        "equipo_visitante",
        "away_name",
        "visitante_name"
    ]

    columna_local = None
    columna_visitante = None

    for nombre in posibles_local:

        if nombre in nombres_columnas:

            columna_local = nombre
            break

    for nombre in posibles_visitante:

        if nombre in nombres_columnas:

            columna_visitante = nombre
            break

    print()
    print("=" * 60)
    print("PRIMER PARTIDO")
    print("=" * 60)

    if (
        columna_local is not None
        and
        columna_visitante is not None
    ):

        consulta = f"""
            SELECT
                fecha,
                {columna_local},
                {columna_visitante}
            FROM matches
            WHERE league_id = 128
            ORDER BY fecha ASC
            LIMIT 1
        """

        db.cursor.execute(consulta)

        primer_partido = db.cursor.fetchone()

        if primer_partido:

            print(
                f"Fecha: {primer_partido[0]}"
            )

            print(
                f"Local: {primer_partido[1]}"
            )

            print(
                f"Visitante: {primer_partido[2]}"
            )

    else:

        print(
            "No se identificaron automáticamente "
            "las columnas de equipos."
        )

        print(
            "No pasa nada: las columnas reales "
            "aparecen arriba."
        )

    # =========================================================
    # 6. PARTIDOS POR TEMPORADA
    # =========================================================

    db.cursor.execute("""
        SELECT
            season,
            COUNT(*)
        FROM matches
        WHERE league_id = 128
        GROUP BY season
        ORDER BY season
    """)

    temporadas = db.cursor.fetchall()

    print()
    print("=" * 60)
    print("PARTIDOS POR TEMPORADA")
    print("=" * 60)

    if temporadas:

        for temporada, cantidad in temporadas:

            print(
                f"Temporada {temporada}: "
                f"{cantidad} partidos"
            )

    else:

        print(
            "No se encontraron temporadas."
        )

    # =========================================================
    # 7. PARTIDOS FT POR TEMPORADA
    # =========================================================

    db.cursor.execute("""
        SELECT
            season,
            COUNT(*)
        FROM matches
        WHERE league_id = 128
          AND estado = 'FT'
        GROUP BY season
        ORDER BY season
    """)

    temporadas_ft = db.cursor.fetchall()

    print()
    print("=" * 60)
    print("PARTIDOS FT POR TEMPORADA")
    print("=" * 60)

    if temporadas_ft:

        for temporada, cantidad in temporadas_ft:

            print(
                f"Temporada {temporada}: "
                f"{cantidad} FT"
            )

    else:

        print(
            "No se encontraron partidos FT."
        )

    # =========================================================
    # 8. PARTIDOS CON GOLES POR TEMPORADA
    # =========================================================

    db.cursor.execute("""
        SELECT
            season,
            COUNT(*)
        FROM matches
        WHERE league_id = 128
          AND estado = 'FT'
          AND goles_local IS NOT NULL
          AND goles_visitante IS NOT NULL
        GROUP BY season
        ORDER BY season
    """)

    temporadas_goles = db.cursor.fetchall()

    print()
    print("=" * 60)
    print("PARTIDOS CON GOLES POR TEMPORADA")
    print("=" * 60)

    if temporadas_goles:

        for temporada, cantidad in temporadas_goles:

            print(
                f"Temporada {temporada}: "
                f"{cantidad} con goles"
            )

    else:

        print(
            "No se encontraron partidos con goles."
        )

    # =========================================================
    # 9. DIAGNÓSTICO RELATIVE STRENGTH 2023
    # =========================================================

    db.cursor.execute("""
        SELECT COUNT(*)
        FROM matches
        WHERE league_id = 128
          AND season = 2023
    """)

    partidos_2023 = db.cursor.fetchone()[0]

    print()
    print("=" * 60)
    print("DIAGNÓSTICO RELATIVE STRENGTH")
    print("=" * 60)

    print(
        f"Partidos 2023: {partidos_2023}"
    )

    # =========================================================
    # 10. PROMEDIO DE LIGA ANTES DEL PRIMER PARTIDO 2023
    # =========================================================

    db.cursor.execute("""
        SELECT AVG(goles_local)
        FROM matches
        WHERE league_id = 128
          AND season = 2023
          AND estado = 'FT'
          AND fecha < (
              SELECT MIN(fecha)
              FROM matches
              WHERE league_id = 128
                AND season = 2023
          )
    """)

    promedio_liga = db.cursor.fetchone()[0]

    print(
        f"Promedio liga antes del primer partido: "
        f"{promedio_liga}"
    )

    # =========================================================
    # 11. CERRAR
    # =========================================================

    db.cerrar()

    print()
    print("=" * 60)
    print("DIAGNÓSTICO FINALIZADO")
    print("=" * 60)


if __name__ == "__main__":

    main()