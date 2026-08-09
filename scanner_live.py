import os
import re
import unicodedata
import requests

from dotenv import load_dotenv

from database.database import Database
from analysis.model_v2 import predecir
from odds import obtener_cuotas_evento, extraer_1x2


# ============================================================
# CONFIGURACIÓN
# ============================================================

EVENTS_URL = "https://api.odds-api.io/v3/events"

SPORT = "football"

LEAGUE = "argentina-primera-lpf-clausura"


# ============================================================
# API KEY
# ============================================================

def obtener_api_key():

    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:

        raise RuntimeError(
            "No se encontró ODDS_API_KEY en .env"
        )

    return api_key


# ============================================================
# NORMALIZAR NOMBRES
# ============================================================

def normalizar_nombre(nombre):

    if not nombre:
        return ""

    nombre = str(nombre).lower().strip()

    # --------------------------------------------------------
    # Eliminar acentos
    # --------------------------------------------------------

    nombre = unicodedata.normalize(
        "NFD",
        nombre
    )

    nombre = "".join(
        caracter
        for caracter in nombre
        if unicodedata.category(caracter) != "Mn"
    )

    # --------------------------------------------------------
    # Apóstrofes
    # --------------------------------------------------------

    nombre = nombre.replace(
        "'",
        ""
    )

    nombre = nombre.replace(
        "’",
        ""
    )

    nombre = nombre.replace(
        "`",
        ""
    )

    # --------------------------------------------------------
    # Eliminar prefijos habituales
    # --------------------------------------------------------

    prefijos = [
        "ca ",
        "club atletico ",
        "club atletico",
        "club ",
        "atletico ",
    ]

    cambio = True

    while cambio:

        cambio = False

        for prefijo in prefijos:

            if nombre.startswith(prefijo):

                nombre = nombre[
                    len(prefijo):
                ]

                cambio = True

                break

    # --------------------------------------------------------
    # Equivalencias conocidas
    # --------------------------------------------------------

    reemplazos = {

        "newells old boys":
            "newells",

        "newells old boy":
            "newells",

        "newells":
            "newells",

        "racing club avellaneda":
            "racing club",

        "racing avellaneda":
            "racing club",

        "gimnasia y esgrima la plata":
            "gimnasia",

        "gimnasia l.p.":
            "gimnasia",

        "gimnasia l.p":
            "gimnasia",

        "gimnasia l p":
            "gimnasia",

        "gimnasia":
            "gimnasia",

        "central cordoba se":
            "central cordoba",

        "central cordoba":
            "central cordoba",

        "instituto ac cordoba":
            "instituto cordoba",

        "instituto a.c. cordoba":
            "instituto cordoba",

        "instituto cordoba":
            "instituto cordoba",

        "talleres de cordoba":
            "talleres cordoba",

        "talleres cordoba":
            "talleres cordoba",

        "belgrano de cordoba":
            "belgrano cordoba",

        "belgrano cordoba":
            "belgrano cordoba",

        "independiente avellaneda":
            "independiente",

        "independiente":
            "independiente",

        "san lorenzo de almagro":
            "san lorenzo",

        "san lorenzo":
            "san lorenzo",

        "union de santa fe":
            "union santa fe",

        "union santa fe":
            "union santa fe",

        "argentinos juniors":
            "argentinos",

        "argentinos jrs":
            "argentinos",

        "argentinos":
            "argentinos",

        "defensa y justicia":
            "defensa y justicia",

        "defensa justicia":
            "defensa y justicia",

        "rosario central":
            "rosario central",

        "ca rosario central":
            "rosario central",

        "river plate arg":
            "river plate",

        "river plate":
            "river plate",

        "boca juniors":
            "boca",

        "boca":
            "boca",

        "huracan":
            "huracan",

        "platense":
            "platense",

        "banfield":
            "banfield",

        "tigre":
            "tigre",

        "aldosivi":
            "aldosivi",

        "riestra":
            "riestra",

        "deportivo riestra afbc":
            "riestra",

        "estudiantes de la plata":
            "estudiantes",

        "estudiantes l.p.":
            "estudiantes",

        "estudiantes l p":
            "estudiantes",

        "estudiantes":
            "estudiantes",

        "velez sarsfield":
            "velez",

        "velez":
            "velez",

        "sarmiento junin":
            "sarmiento",

        "sarmiento":
            "sarmiento",

        "atletico tucuman":
            "atletico tucuman",

        "barracas central":
            "barracas",

        "barracas":
            "barracas",

        "lanus":
            "lanus",

        "independiente rivadavia":
            "independiente rivadavia",

        "instituto":
            "instituto cordoba",
    }

    if nombre in reemplazos:

        nombre = reemplazos[
            nombre
        ]

    # --------------------------------------------------------
    # Eliminar puntuación restante
    # --------------------------------------------------------

    nombre = re.sub(
        r"[^a-z0-9 ]",
        " ",
        nombre
    )

    # --------------------------------------------------------
    # Normalizar espacios
    # --------------------------------------------------------

    nombre = " ".join(
        nombre.split()
    )

    return nombre


# ============================================================
# OBTENER EVENTO
# ============================================================

def obtener_evento(event_id):

    api_key = obtener_api_key()

    params = {
        "apiKey": api_key,
        "sport": SPORT,
        "league": LEAGUE,
        "limit": 50
    }

    respuesta = requests.get(
        EVENTS_URL,
        params=params,
        timeout=15
    )

    respuesta.raise_for_status()

    eventos = respuesta.json()

    for evento in eventos:

        if int(
            evento["id"]
        ) == int(event_id):

            return evento

    return None


# ============================================================
# BUSCAR EQUIPO EN SQLITE
# ============================================================

def buscar_equipo_id(nombre):

    objetivo = normalizar_nombre(
        nombre
    )

    db = Database()

    # --------------------------------------------------------
    # Todos los equipos locales
    # --------------------------------------------------------

    db.cursor.execute(
        """
        SELECT DISTINCT
            home_team_id,
            local
        FROM matches
        WHERE local IS NOT NULL
        """
    )

    locales = db.cursor.fetchall()

    # --------------------------------------------------------
    # Todos los equipos visitantes
    # --------------------------------------------------------

    db.cursor.execute(
        """
        SELECT DISTINCT
            away_team_id,
            visitante
        FROM matches
        WHERE visitante IS NOT NULL
        """
    )

    visitantes = db.cursor.fetchall()

    db.cerrar()

    # --------------------------------------------------------
    # Coincidencia exacta normalizada
    # --------------------------------------------------------

    for fila in locales:

        nombre_sqlite = normalizar_nombre(
            fila["local"]
        )

        if nombre_sqlite == objetivo:

            return fila["home_team_id"]

    for fila in visitantes:

        nombre_sqlite = normalizar_nombre(
            fila["visitante"]
        )

        if nombre_sqlite == objetivo:

            return fila["away_team_id"]

    # --------------------------------------------------------
    # Coincidencia por inclusión
    # --------------------------------------------------------

    for fila in locales:

        nombre_sqlite = normalizar_nombre(
            fila["local"]
        )

        if (
            objetivo in nombre_sqlite
            or
            nombre_sqlite in objetivo
        ):

            return fila["home_team_id"]

    for fila in visitantes:

        nombre_sqlite = normalizar_nombre(
            fila["visitante"]
        )

        if (
            objetivo in nombre_sqlite
            or
            nombre_sqlite in objetivo
        ):

            return fila["away_team_id"]

    return None


# ============================================================
# CONSTRUIR PARTIDO PARA V2
# ============================================================

def construir_partido(evento):

    local = evento["home"]

    visitante = evento["away"]

    local_id = buscar_equipo_id(
        local
    )

    visitante_id = buscar_equipo_id(
        visitante
    )

    if local_id is None:

        print()
        print(
            f"NO SE ENCONTRÓ EN SQLITE: "
            f"{local}"
        )

        return None

    if visitante_id is None:

        print()
        print(
            f"NO SE ENCONTRÓ EN SQLITE: "
            f"{visitante}"
        )

        return None

    return {

        "fixture_id":
            evento["id"],

        "home_team_id":
            local_id,

        "away_team_id":
            visitante_id,

        "fecha":
            evento["date"],

        "estado":
            evento["status"],

        "local":
            local,

        "visitante":
            visitante,

        "liga":
            evento["league"]["name"],

        "goles_local":
            None,

        "goles_visitante":
            None
    }


# ============================================================
# CALCULAR EV
# ============================================================

def calcular_ev(
    probabilidad,
    cuota
):

    return (
        probabilidad * cuota
    ) - 1


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(
    evento,
    prediccion,
    cuotas
):

    probabilidades = (
        prediccion["probabilidades"]
    )

    resultados = []

    print()
    print("=" * 75)
    print("BETMIND AI — VALUE SCANNER")
    print("=" * 75)

    print()

    print(
        f"{evento['home']} "
        f"vs "
        f"{evento['away']}"
    )

    print(
        f"Fecha: {evento['date']}"
    )

    print(
        f"Estado: {evento['status']}"
    )

    print()

    # ========================================================
    # V2
    # ========================================================

    print("V2 CALIBRADA")
    print("-" * 75)

    print(
        f"Local:      "
        f"{probabilidades['local'] * 100:.2f}%"
    )

    print(
        f"Empate:     "
        f"{probabilidades['empate'] * 100:.2f}%"
    )

    print(
        f"Visitante:  "
        f"{probabilidades['visitante'] * 100:.2f}%"
    )

    print()

    # ========================================================
    # CUOTAS
    # ========================================================

    print("CUOTAS BET365")
    print("-" * 75)

    print(
        f"Local:      "
        f"{cuotas['local']:.2f}"
    )

    print(
        f"Empate:     "
        f"{cuotas['empate']:.2f}"
    )

    print(
        f"Visitante:  "
        f"{cuotas['visitante']:.2f}"
    )

    print()

    # ========================================================
    # VALUE
    # ========================================================

    print("ANÁLISIS DE VALUE")
    print("-" * 75)

    print(
        f"{'Mercado':<12}"
        f"{'Modelo':<12}"
        f"{'Cuota':<10}"
        f"{'Justa':<10}"
        f"{'EV':<10}"
        f"Estado"
    )

    print("-" * 75)

    for nombre in (
        "local",
        "empate",
        "visitante"
    ):

        probabilidad = (
            probabilidades[nombre]
        )

        cuota = cuotas[nombre]

        if probabilidad <= 0:

            continue

        cuota_justa = (
            1 / probabilidad
        )

        ev = calcular_ev(
            probabilidad,
            cuota
        )

        resultados.append({

            "nombre":
                nombre,

            "probabilidad":
                probabilidad,

            "cuota":
                cuota,

            "cuota_justa":
                cuota_justa,

            "ev":
                ev
        })

        estado = (
            "VALUE"
            if ev > 0
            else "SIN VALUE"
        )

        print(
            f"{nombre.capitalize():<12}"
            f"{probabilidad * 100:>6.2f}%   "
            f"{cuota:<10.2f}"
            f"{cuota_justa:<10.2f}"
            f"{ev * 100:>7.2f}%  "
            f"{estado}"
        )

    if not resultados:

        print()
        print(
            "No hay mercados válidos."
        )

        return

    # ========================================================
    # MEJOR VALUE
    # ========================================================

    mejor = max(
        resultados,
        key=lambda x: x["ev"]
    )

    print()
    print("=" * 75)
    print("MEJOR OPORTUNIDAD")
    print("=" * 75)

    print()

    print(
        f"→ {mejor['nombre'].upper()}"
    )

    print(
        f"Probabilidad modelo: "
        f"{mejor['probabilidad'] * 100:.2f}%"
    )

    print(
        f"Cuota: "
        f"{mejor['cuota']:.2f}"
    )

    print(
        f"Cuota justa: "
        f"{mejor['cuota_justa']:.2f}"
    )

    print(
        f"EV: "
        f"{mejor['ev'] * 100:.2f}%"
    )

    if mejor["ev"] > 0:

        print(
            "→ VALUE POSITIVO"
        )

    else:

        print(
            "→ SIN VALUE"
        )

    print()

    # ========================================================
    # PREDICCIÓN
    # ========================================================

    print("=" * 75)
    print("PREDICCIÓN V2")
    print("=" * 75)

    print()

    prediccion_nombre = {

        "local":
            "LOCAL",

        "empate":
            "EMPATE",

        "visitante":
            "VISITANTE"

    }[
        prediccion["prediccion"]
    ]

    print(
        f"→ {prediccion_nombre}"
    )

    print()

    print("=" * 75)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("BETMIND AI — SCANNER PREPARTIDO")
    print("=" * 75)

    print()

    try:

        event_id = int(
            input(
                "Ingresá el Odds Event ID: "
            )
        )

    except ValueError:

        print()
        print(
            "ERROR: el ID debe ser numérico."
        )

        return

    # ========================================================
    # EVENTO
    # ========================================================

    try:

        evento = obtener_evento(
            event_id
        )

    except Exception as error:

        print()
        print(
            "ERROR AL OBTENER EVENTO:"
        )

        print(error)

        return

    if evento is None:

        print()
        print(
            "No se encontró el evento."
        )

        return

    print()

    print(
        f"Evento encontrado: "
        f"{evento['home']} "
        f"vs "
        f"{evento['away']}"
    )

    print(
        f"Estado: "
        f"{evento['status']}"
    )

    # ========================================================
    # SOLO PREPARTIDO
    # ========================================================

    estado = str(
        evento["status"]
    ).lower()

    if estado != "pending":

        print()
        print(
            "PARTIDO NO ANALIZABLE."
        )

        print(
            f"Estado actual: {evento['status']}"
        )

        print(
            "BetMind solo analiza "
            "partidos pendientes."
        )

        return

    # ========================================================
    # CONSTRUIR PARTIDO
    # ========================================================

    print()
    print(
        "Relacionando equipos con SQLite..."
    )

    partido = construir_partido(
        evento
    )

    if partido is None:

        print()
        print(
            "No se pudo relacionar "
            "el evento con SQLite."
        )

        return

    print()

    print(
        f"SQLite → "
        f"{partido['local']} "
        f"(ID {partido['home_team_id']})"
    )

    print(
        f"SQLite → "
        f"{partido['visitante']} "
        f"(ID {partido['away_team_id']})"
    )

    # ========================================================
    # V2
    # ========================================================

    print()
    print(
        "Calculando V2..."
    )

    try:

        resultado_v2 = predecir(
            partido
        )

    except Exception as error:

        print()
        print(
            "ERROR AL CALCULAR V2:"
        )

        print(error)

        return

    if resultado_v2 is None:

        print()
        print(
            "V2 no pudo generar "
            "una predicción."
        )

        print(
            "No hay suficientes datos "
            "históricos."
        )

        return

    # ========================================================
    # CUOTAS
    # ========================================================

    print()
    print(
        "Buscando cuotas Bet365..."
    )

    try:

        datos_odds = obtener_cuotas_evento(
            evento["id"]
        )

    except Exception as error:

        print()
        print(
            "ERROR AL OBTENER CUOTAS:"
        )

        print(error)

        return

    if not datos_odds:

        print()
        print(
            "No se recibieron datos "
            "de cuotas."
        )

        return

    cuotas = extraer_1x2(
        datos_odds
    )

    if cuotas is None:

        print()
        print(
            "No se encontró mercado "
            "1X2 de Bet365."
        )

        return

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    mostrar_resultado(
        evento,
        resultado_v2,
        cuotas
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()