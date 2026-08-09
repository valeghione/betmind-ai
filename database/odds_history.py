from database.database import Database


def crear_tablas_odds():

    db = Database()

    # ========================================================
    # SNAPSHOTS DE CUOTAS
    # ========================================================

    db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS odds_snapshots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id INTEGER NOT NULL,

            fecha_evento TEXT,

            local TEXT,

            visitante TEXT,

            bookmaker TEXT,

            cuota_local REAL,

            cuota_empate REAL,

            cuota_visitante REAL,

            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================================
    # RESULTADOS DE EVENTOS
    # ========================================================

    db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS odds_results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id INTEGER UNIQUE NOT NULL,

            fecha_evento TEXT,

            local TEXT,

            visitante TEXT,

            goles_local INTEGER,

            goles_visitante INTEGER,

            resultado TEXT,

            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================================
    # OPORTUNIDADES DE VALUE
    # ========================================================

    db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS value_opportunities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id INTEGER NOT NULL,

            fecha_evento TEXT,

            local TEXT,

            visitante TEXT,

            mercado TEXT,

            probabilidad_modelo REAL,

            cuota REAL,

            cuota_justa REAL,

            ev REAL,

            prediccion TEXT,

            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,

            resultado TEXT,

            ganancia REAL

        )
    """)

    db.connection.commit()

    db.cerrar()


if __name__ == "__main__":

    crear_tablas_odds()

    print(
        "Tablas odds creadas correctamente."
    )