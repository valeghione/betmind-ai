from database.database import Database


def main():

    db = Database()

    db.cursor.execute("""
        SELECT
            fixture_id,
            local,
            visitante,
            fecha,
            estado
        FROM matches
        WHERE fecha > datetime('now')
        ORDER BY fecha ASC
        LIMIT 20
    """)

    partidos = db.cursor.fetchall()

    db.cerrar()

    print("=" * 70)
    print("PRÓXIMOS PARTIDOS EN SQLITE")
    print("=" * 70)

    print()

    if not partidos:

        print(
            "No hay partidos futuros en la base de datos."
        )

        return

    print(
        f"Partidos encontrados: {len(partidos)}"
    )

    print()

    for partido in partidos:

        print(
            f"Fixture ID: {partido['fixture_id']}"
        )

        print(
            f"{partido['local']} "
            f"vs "
            f"{partido['visitante']}"
        )

        print(
            f"Fecha: {partido['fecha']}"
        )

        print(
            f"Estado: {partido['estado']}"
        )

        print("-" * 70)


if __name__ == "__main__":
    main()