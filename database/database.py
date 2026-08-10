import sqlite3
from datetime import datetime

from models.match import Match


class Database:

    HISTORICAL_LEAGUE_ID = 128
    FINAL_STATUSES = {"FT", "AET", "PEN"}

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

                fecha TEXT,
                estado TEXT,

                goles_local INTEGER,
                goles_visitante INTEGER,

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
                fecha,
                estado,
                goles_local,
                goles_visitante,
                liga,
                local,
                visitante,
                estadio,
                ciudad,
                arbitro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match.fixture_id,
            match.league_id,
            match.season,
            match.home_team_id,
            match.away_team_id,
            match.fecha,
            match.estado,
            match.goles_local,
            match.goles_visitante,
            match.liga,
            match.local,
            match.visitante,
            match.estadio,
            match.ciudad,
            match.arbitro
        ))

        self.connection.commit()

    def guardar_partido_historico(self, match: Match):

        """Persist a validated, finished Argentina Primera LPF fixture.

        Live and future fixtures intentionally use no persistence path into
        ``matches``.  This table feeds the historical model.
        """

        if not self.es_partido_historico_valido(match):

            raise ValueError(
                "El partido no es un histórico finalizado válido de "
                "Argentina Primera LPF."
            )

        self.guardar_partido(match)

    @classmethod
    def es_partido_historico_valido(cls, match: Match):

        try:
            fixture_id_valido = int(match.fixture_id) > 0
        except (TypeError, ValueError):
            fixture_id_valido = False

        if not fixture_id_valido:
            return False

        if match.league_id != cls.HISTORICAL_LEAGUE_ID:
            return False

        if match.estado not in cls.FINAL_STATUSES:
            return False

        if (
            match.goles_local is None
            or match.goles_visitante is None
        ):
            return False

        if not match.fecha:
            return False

        try:
            datetime.fromisoformat(
                str(match.fecha).replace("Z", "+00:00")
            )
        except ValueError:
            return False

        return True

    def obtener_partidos(self):

        self.cursor.execute("""
            SELECT *
            FROM matches
        """)

        return self.cursor.fetchall()

    def obtener_partido(self, fixture_id):

        self.cursor.execute("""
            SELECT *
            FROM matches
            WHERE fixture_id = ?
        """, (
            fixture_id,
        ))

        return self.cursor.fetchone()

    def obtener_ultimos_partidos_equipo(
        self,
        team_id,
        limite=5,
        condicion=None,
        fecha_hasta=None
    ):

        condiciones = []
        parametros = []

        if condicion == "local":

            condiciones.append("home_team_id = ?")
            parametros.append(team_id)

        elif condicion == "visitante":

            condiciones.append("away_team_id = ?")
            parametros.append(team_id)

        else:

            condiciones.append(
                "(home_team_id = ? OR away_team_id = ?)"
            )

            parametros.extend([
                team_id,
                team_id
            ])

        if fecha_hasta is not None:

            condiciones.append("fecha < ?")
            parametros.append(fecha_hasta)

        where = " AND ".join(condiciones)

        query = f"""
            SELECT *
            FROM matches
            WHERE {where}
            ORDER BY fecha DESC
            LIMIT ?
        """

        parametros.append(limite)

        self.cursor.execute(
            query,
            parametros
        )

        return self.cursor.fetchall()

    def cerrar(self):

        self.connection.close()
