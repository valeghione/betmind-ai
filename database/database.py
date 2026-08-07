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

                fixture_id INTEGER PRIMARY KEY,

                league_id INTEGER,
                season INTEGER,

                home_team_id INTEGER,
                away_team_id INTEGER,

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
            INSERT OR REPLACE INTO matches (
                fixture_id,
                league_id,
                season,
                home_team_id,
                away_team_id,
                liga,
                local,
                visitante,
                estadio,
                ciudad,
                arbitro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            match.fixture_id,
            match.league_id,
            match.season,
            match.home_team_id,
            match.away_team_id,
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