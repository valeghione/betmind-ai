import sqlite3

from models.match import Match


class Database:

    def __init__(self):

        self.connection = sqlite3.connect("betmind.db")

        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

    def crear_tabla_partidos(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                liga TEXT,

                local TEXT,

                visitante TEXT,

                estadio TEXT,

                ciudad TEXT,

                arbitro TEXT

            )
        """)

        self.connection.commit()

    def guardar_partido(self, match: Match):

        self.cursor.execute("""
            INSERT INTO matches (
                liga,
                local,
                visitante,
                estadio,
                ciudad,
                arbitro
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (

            match.liga,
            match.local,
            match.visitante,
            match.estadio,
            match.ciudad,
            match.arbitro

        ))

        self.connection.commit()

    def obtener_partidos(self):

        self.cursor.execute("SELECT * FROM matches")

        return self.cursor.fetchall()

    def cerrar(self):

        self.connection.close()