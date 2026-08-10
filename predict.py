import os
import unicodedata
import re
import requests

from dotenv import load_dotenv

from database.database import Database
from analysis.model_v2 import predecir
from value import analizar_apuesta, mostrar_apuesta


# ============================================================
# CONFIGURACIÓN ODDS API
# ============================================================

EVENTS_URL = (
    "https://api.odds-api.io/v3/events"
)

SPORT = "football"

LEAGUE = (
    "argentina-primera-lpf-clausura"
)


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalizar_nombre(nombre):

    if not nombre:

        return ""

    nombre = str(
        nombre
    ).lower().strip()

    nombre = unicodedata.normalize(
        "NFD",
        nombre
    )

    nombre = "".join(
        caracter
        for caracter in nombre
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

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

    prefijos = [
        "ca ",
        "club atletico ",
        "club atletico",
        "club ",
        "atletico "
    ]

    cambio = True

    while cambio:

        cambio = False

        for prefijo in prefijos:

            if nombre.startswith(
                prefijo
            ):

                nombre = nombre[
                    len(prefijo):
                ]

                cambio = True

                break

    reemplazos = {

        "newells old boys":
            "newells",

        "newells old boy":
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

        "central cordoba se":
            "central cordoba",

        "instituto ac cordoba":
            "instituto cordoba",

        "instituto a.c. cordoba":
            "instituto cordoba",

        "talleres de cordoba":
            "talleres cordoba",

        "belgrano de cordoba":
            "belgrano cordoba",

        "independiente avellaneda":
            "independiente",

        "san lorenzo de almagro":
            "san lorenzo",

        "union de santa fe":
            "union santa fe",

        "argentinos juniors":
            "argentinos",

        "argentinos jrs":
            "argentinos",

        "river plate arg":
            "river plate",

        "boca juniors":
            "boca",

        "deportivo riestra afbc":
            "riestra",

        "estudiantes de la plata":
            "estudiantes",

        "estudiantes l.p.":
            "estudiantes",

        "estudiantes l p":
            "estudiantes",

        "velez sarsfield":
            "velez",

        "sarmiento junin":
            "sarmiento",

        "barracas central":
            "barracas",

        "aldosivi":
            "aldosivi"
    }

    nombre = reemplazos.get(
        nombre,
        nombre
    )

    nombre = re.sub(
        r"[^a-z0-9 ]",
        " ",
        nombre
    )

    nombre = " ".join(
        nombre.split()
    )

    return nombre


# ============================================================
# OBTENER PARTIDO SQLITE
# ============================================================

def obtener_partido(fixture_id):

    db = Database()

    partido = db.obtener_partido(
        fixture_id
    )

    db.cerrar()

    return partido


# ============================================================
# OBTENER EVENTOS ODDS API
# ============================================================

def obtener_api_key():

    load_dotenv()

    api_key = os.getenv(
        "ODDS_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "No se encontró ODDS_API_KEY en .env"
        )

    return api_key


def obtener_eventos():

    api_key = obtener_api_key()

    respuesta = requests.get(
        EVENTS_URL,
        params={
            "apiKey": api_key,
            "sport": SPORT,
            "league": LEAGUE,
            "limit": 50
        },
        timeout=15
    )

    respuesta.raise_for_status()

    return respuesta.json()


def obtener_evento_odds(event_id):

    eventos = obtener_eventos()

    for evento in eventos:

        if int(
            evento.get("id")
        ) == int(event_id):

            return evento

    return None


# ============================================================
# BUSCAR TEAM ID
# MISMA LÓGICA QUE SCANNER_ALL
# ============================================================

def buscar_team_id(
    nombre,
    campo_id,
    campo_nombre
):

    objetivo = normalizar_nombre(
        nombre
    )

    db = Database()

    db.cursor.execute(f"""
        SELECT
            {campo_id},
            {campo_nombre}
        FROM matches
        WHERE {campo_nombre} IS NOT NULL
    """)

    filas = db.cursor.fetchall()

    db.cerrar()

    # --------------------------------------------------------
    # Coincidencia exacta normalizada
    # --------------------------------------------------------

    for fila in filas:

        nombre_db = normalizar_nombre(
            fila[campo_nombre]
        )

        if nombre_db == objetivo:

            return fila[campo_id]

    # --------------------------------------------------------
    # Coincidencia parcial
    # --------------------------------------------------------

    for fila in filas:

        nombre_db = normalizar_nombre(
            fila[campo_nombre]
        )

        if (
            objetivo in nombre_db
            or
            nombre_db in objetivo
        ):

            return fila[campo_id]

    return None


# ============================================================
# CONSTRUIR PARTIDO FUTURO
# ============================================================

def construir_partido_futuro(
    evento
):

    local_id = buscar_team_id(
        evento["home"],
        "home_team_id",
        "local"
    )

    visitante_id = buscar_team_id(
        evento["away"],
        "away_team_id",
        "visitante"
    )

    if local_id is None:

        print()

        print(
            "No se encontró el equipo "
            f"local en SQLite: "
            f"{evento['home']}"
        )

        return None

    if visitante_id is None:

        print()

        print(
            "No se encontró el equipo "
            f"visitante en SQLite: "
            f"{evento['away']}"
        )

        return None

    return {

        "fixture_id":
            int(evento["id"]),

        "home_team_id":
            local_id,

        "away_team_id":
            visitante_id,

        "fecha":
            evento["date"],

        "estado":
            evento["status"],

        "goles_local":
            None,

        "goles_visitante":
            None,

        "liga":
            (
                evento
                .get("league", {})
                .get(
                    "name",
                    LEAGUE
                )
            ),

        "local":
            evento["home"],

        "visitante":
            evento["away"],

        "estadio":
            None,

        "ciudad":
            None,

        "arbitro":
            None
    }


# ============================================================
# MOSTRAR PREDICCIÓN
# ============================================================

def mostrar_prediccion(
    resultado,
    pedir_cuotas=True
):

    if resultado is None:

        print()

        print(
            "No fue posible generar "
            "la predicción."
        )

        print(
            "El partido no tiene suficientes "
            "datos históricos."
        )

        return

    probabilidades_base = (
        resultado[
            "probabilidades_base"
        ]
    )

    probabilidades = (
        resultado[
            "probabilidades"
        ]
    )

    prediccion = (
        resultado[
            "prediccion"
        ]
    )

    print()
    print("=" * 70)
    print(
        "BETMIND AI — PREDICCIÓN V2"
    )
    print("=" * 70)

    print()

    print(
        "PROBABILIDADES BASE"
    )

    print("-" * 70)

    print(
        f"Local:      "
        f"{probabilidades_base['local'] * 100:.2f}%"
    )

    print(
        f"Empate:     "
        f"{probabilidades_base['empate'] * 100:.2f}%"
    )

    print(
        f"Visitante:  "
        f"{probabilidades_base['visitante'] * 100:.2f}%"
    )

    print()

    print(
        "PROBABILIDADES V2 CALIBRADAS"
    )

    print("-" * 70)

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

    print(
        "CAMBIO POR CALIBRACIÓN"
    )

    print("-" * 70)

    for resultado_nombre in [
        "local",
        "empate",
        "visitante"
    ]:

        cambio = (
            probabilidades[
                resultado_nombre
            ]
            -
            probabilidades_base[
                resultado_nombre
            ]
        )

        print(
            f"{resultado_nombre.capitalize():<12}"
            f"{cambio * 100:+.2f} puntos"
        )

    print()

    print(
        "CUOTAS JUSTAS"
    )

    print("-" * 70)

    for resultado_nombre in [
        "local",
        "empate",
        "visitante"
    ]:

        probabilidad = (
            probabilidades[
                resultado_nombre
            ]
        )

        if probabilidad <= 0:

            continue

        cuota_justa = (
            1 / probabilidad
        )

        print(
            f"{resultado_nombre.capitalize():<12}"
            f"{cuota_justa:.2f}"
        )

    print()

    print(
        "PREDICCIÓN"
    )

    print("-" * 70)

    if prediccion == "local":

        print("→ LOCAL")

    elif prediccion == "empate":

        print("→ EMPATE")

    else:

        print("→ VISITANTE")

    # ========================================================
    # CUOTAS
    # ========================================================

    if not pedir_cuotas:

        return

    print()

    print("=" * 70)
    print(
        "ANÁLISIS DE VALOR"
    )
    print("=" * 70)

    print()

    cuotas = {}

    for resultado_nombre in [
        "local",
        "empate",
        "visitante"
    ]:

        texto = input(
            f"Cuota {resultado_nombre}: "
        ).strip()

        if texto == "":

            continue

        try:

            cuota = float(
                texto.replace(
                    ",",
                    "."
                )
            )

        except ValueError:

            print(
                "Cuota inválida."
            )

            continue

        if cuota <= 1:

            print(
                "La cuota debe ser "
                "mayor que 1."
            )

            continue

        cuotas[
            resultado_nombre
        ] = cuota

    for (
        resultado_nombre,
        cuota
    ) in cuotas.items():

        datos = analizar_apuesta(
            probabilidades[
                resultado_nombre
            ],
            cuota
        )

        mostrar_apuesta(
            resultado_nombre.upper(),
            datos
        )

    print()
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        fixture_id = int(
            input(
                "Ingresá el fixture_id "
                "o Odds Event ID: "
            )
        )

    except ValueError:

        print()

        print(
            "El ID debe ser un número."
        )

        return

    # --------------------------------------------------------
    # Primero buscamos en SQLite.
    # --------------------------------------------------------

    partido = obtener_partido(
        fixture_id
    )

    # --------------------------------------------------------
    # Si no existe, lo buscamos como Odds Event ID.
    # --------------------------------------------------------

    if partido is None:

        print()

        print(
            "No se encontró en SQLite."
        )

        print(
            "Buscando como Odds Event ID..."
        )

        try:

            evento = (
                obtener_evento_odds(
                    fixture_id
                )
            )

        except Exception as error:

            print()

            print(
                "ERROR CONSULTANDO "
                "ODDS API:"
            )

            print(error)

            return

        if evento is None:

            print()

            print(
                "No se encontró el evento "
                "en Odds API."
            )

            return

        partido = (
            construir_partido_futuro(
                evento
            )
        )

        if partido is None:

            return

        print()

        print(
            "EVENTO FUTURO ODDS API"
        )

    # ========================================================
    # MOSTRAR PARTIDO
    # ========================================================

    print()

    print("=" * 70)
    print("PARTIDO")
    print("=" * 70)

    print()

    print(
        f"{partido['local']} "
        f"vs "
        f"{partido['visitante']}"
    )

    print(
        f"Fecha: "
        f"{partido['fecha']}"
    )

    print(
        f"Liga: "
        f"{partido['liga']}"
    )

    print(
        f"Fixture/Event ID: "
        f"{partido['fixture_id']}"
    )

    # ========================================================
    # V2
    # ========================================================

    try:

        resultado = predecir(
            partido
        )

    except Exception as error:

        print()

        print(
            "ERROR EN V2:"
        )

        print(error)

        return

    mostrar_prediccion(
        resultado
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()