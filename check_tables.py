from database.database import Database


def main():

    db = Database()

    db.cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    tablas = db.cursor.fetchall()

    print("=" * 60)
    print("TABLAS DE LA BASE DE DATOS")
    print("=" * 60)

    for tabla in tablas:
        print(tabla["name"])

    db.cerrar()


if __name__ == "__main__":
    main()