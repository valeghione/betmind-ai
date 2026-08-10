import os
import re
import time
import unicodedata
import requests

from dotenv import load_dotenv

from database.database import Database

from database.odds_repository import (
    guardar_snapshot,
    guardar_value
)

from analysis.model_v2 import predecir

from odds import (
    obtener_cuotas_evento,
    extraer_1x2
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

EVENTS_URL = (
    "https://api.odds-api.io/v3/events"
)

SPORT = "football"

LEAGUE = (
    "argentina-primera-lpf-clausura"
)

MIN_EV = 0.00

# Espera entre consultas de cuotas
ODDS_DELAY = 1.5


# ============================================================
# API KEY
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

        "ca aldosivi":
            "aldosivi",

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
# EVENTOS
# ============================================================

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

    eventos = respuesta.json()

    return [
        evento
        for evento in eventos
        if str(
            evento.get(
                "status",
                ""
            )
        ).lower() == "pending"
    ]


# ============================================================
# MAPA DE EQUIPOS
# ============================================================

def cargar_mapa_equipos():

    db = Database()

    db.cursor.execute("""
        SELECT
            home_team_id,
            local
        FROM matches
        WHERE local IS NOT NULL
    """)

    locales = db.cursor.fetchall()

    db.cursor.execute("""
        SELECT
            away_team_id,
            visitante
        FROM matches
        WHERE visitante IS NOT NULL
    """)

    visitantes = db.cursor.fetchall()

    db.cerrar()

    mapa = {}

    for fila in locales:

        nombre = normalizar_nombre(
            fila["local"]
        )

        if nombre:

            mapa[nombre] = (
                fila["home_team_id"]
            )

    for fila in visitantes:

        nombre = normalizar_nombre(
            fila["visitante"]
        )

        if nombre:

            mapa[nombre] = (
                fila["away_team_id"]
            )

    return mapa


# ============================================================
# BUSCAR EQUIPO
# ============================================================

def buscar_equipo_id(
    nombre,
    mapa
):

    objetivo = normalizar_nombre(
        nombre
    )

    if objetivo in mapa:

        return mapa[
            objetivo
        ]

    for (
        nombre_mapa,
        team_id
    ) in mapa.items():

        if (
            objetivo in nombre_mapa
            or
            nombre_mapa in objetivo
        ):

            return team_id

    return None


# ============================================================
# CONSTRUIR PARTIDO
# ============================================================

def construir_partido(
    evento,
    mapa
):

    local_id = buscar_equipo_id(
        evento["home"],
        mapa
    )

    visitante_id = buscar_equipo_id(
        evento["away"],
        mapa
    )

    if local_id is None:

        return None, (
            f"No se encontró: "
            f"{evento['home']}"
        )

    if visitante_id is None:

        return None, (
            f"No se encontró: "
            f"{evento['away']}"
        )

    partido = {

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
            evento["home"],

        "visitante":
            evento["away"],

        "liga":
            evento["league"]["name"],

        "goles_local":
            None,

        "goles_visitante":
            None
    }

    return partido, None


# ============================================================
# ANALIZAR VALUE
# ============================================================

def analizar_value(
    evento,
    resultado_v2,
    cuotas
):

    probabilidades = (
        resultado_v2[
            "probabilidades"
        ]
    )

    mercados = []

    for nombre in (
        "local",
        "empate",
        "visitante"
    ):

        probabilidad = (
            probabilidades[
                nombre
            ]
        )

        cuota = cuotas.get(
            nombre
        )

        if cuota is None:

            continue

        if probabilidad <= 0:

            continue

        cuota_justa = (
            1 / probabilidad
        )

        ev = (
            probabilidad * cuota
        ) - 1

        mercados.append({

            "evento_id":
                evento["id"],

            "local":
                evento["home"],

            "visitante":
                evento["away"],

            "fecha":
                evento["date"],

            "mercado":
                nombre,

            "probabilidad":
                probabilidad,

            "cuota":
                cuota,

            "cuota_justa":
                cuota_justa,

            "ev":
                ev,

            "prediccion":
                resultado_v2[
                    "prediccion"
                ]
        })

    return mercados


# ============================================================
# GUARDAR SNAPSHOT
# ============================================================

def guardar_odds_snapshot(
    evento,
    cuotas
):

    try:

        guardado = guardar_snapshot(

            event_id=
                evento["id"],

            fecha_evento=
                evento["date"],

            local=
                evento["home"],

            visitante=
                evento["away"],

            bookmaker=
                "Bet365",

            cuota_local=
                cuotas.get(
                    "local"
                ),

            cuota_empate=
                cuotas.get(
                    "empate"
                ),

            cuota_visitante=
                cuotas.get(
                    "visitante"
                )
        )

        return guardado

    except Exception as error:

        print(
            f"  SNAPSHOT: ERROR — "
            f"{error}"
        )

        return False


# ============================================================
# GUARDAR VALUE
# ============================================================

def guardar_values(
    mercados
):

    guardados = 0
    duplicados = 0

    for mercado in mercados:

        try:

            guardado = guardar_value(

                event_id=
                    mercado[
                        "evento_id"
                    ],

                fecha_evento=
                    mercado[
                        "fecha"
                    ],

                local=
                    mercado[
                        "local"
                    ],

                visitante=
                    mercado[
                        "visitante"
                    ],

                mercado=
                    mercado[
                        "mercado"
                    ],

                probabilidad_modelo=
                    mercado[
                        "probabilidad"
                    ],

                cuota=
                    mercado[
                        "cuota"
                    ],

                cuota_justa=
                    mercado[
                        "cuota_justa"
                    ],

                ev=
                    mercado[
                        "ev"
                    ],

                prediccion=
                    mercado[
                        "prediccion"
                    ]
            )

            if guardado:

                guardados += 1

            else:

                duplicados += 1

        except Exception as error:

            print(
                f"  VALUE SAVE: ERROR — "
                f"{error}"
            )

    return guardados, duplicados


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)

    print(
        "BETMIND AI — VALUE SCANNER MASIVO"
    )

    print("=" * 80)

    print()

    # ========================================================
    # OBTENER EVENTOS
    # ========================================================

    try:

        eventos = obtener_eventos()

        # ----------------------------------------------------
        # PRUEBA TEMPORAL
        # Procesar solamente 3 eventos.
        #
        # Cuando confirmemos que todo funciona,
        # eliminamos esta línea para volver a los 45/50.
        # ----------------------------------------------------



    except Exception as error:

        print(
            "ERROR OBTENIENDO EVENTOS:"
        )

        print(error)

        return

    print(
        f"Eventos pendientes: "
        f"{len(eventos)}"
    )

    print()

    # ========================================================
    # CARGAR EQUIPOS
    # ========================================================

    print(
        "Cargando equipos históricos..."
    )

    mapa = cargar_mapa_equipos()

    print(
        f"Equipos encontrados: "
        f"{len(mapa)}"
    )

    print()

    # ========================================================
    # CONTADORES
    # ========================================================

    resultados = []

    sin_matching = 0
    sin_v2 = 0
    sin_cuotas = 0
    errores = 0

    snapshots_guardados = 0
    values_guardados = 0

    # ========================================================
    # PROCESAR EVENTOS
    # ========================================================

    for indice, evento in enumerate(
        eventos,
        start=1
    ):

        print(
            f"[{indice}/{len(eventos)}] "
            f"{evento['home']} "
            f"vs "
            f"{evento['away']}"
        )

        print(
            f"EVENT ID: {evento['id']}"
        )

        # ====================================================
        # MATCHING
        # ====================================================

        partido, error = construir_partido(
            evento,
            mapa
        )

        if partido is None:

            print(
                f"MATCHING: ERROR — "
                f"{error}"
            )

            sin_matching += 1

            print()

            continue

        print(
            "MATCHING: OK"
        )

        # ====================================================
        # V2
        # ====================================================

        try:

            resultado_v2 = predecir(
                partido
            )

        except Exception as error:

            print(
                f"V2: ERROR — "
                f"{error}"
            )

            errores += 1

            print()

            continue

        if resultado_v2 is None:

            print(
                "V2: sin datos suficientes"
            )

            sin_v2 += 1

            print()

            continue

        print(
            "V2: OK"
        )

        # ====================================================
        # ESPERA ANTES DE ODDS
        # ====================================================

        if indice > 1:

            print(
                f"Esperando "
                f"{ODDS_DELAY:.1f}s..."
            )

            time.sleep(
                ODDS_DELAY
            )

        # ====================================================
        # ODDS
        # ====================================================

        try:

            datos_odds = (
                obtener_cuotas_evento(
                    evento["id"]
                )
            )

        except requests.exceptions.HTTPError as error:

            print(
                f"ODDS: ERROR HTTP — "
                f"{error}"
            )

            errores += 1

            print()

            continue

        except requests.exceptions.RequestException as error:

            print(
                f"ODDS: ERROR REQUEST — "
                f"{error}"
            )

            errores += 1

            print()

            continue

        except Exception as error:

            print(
                f"ODDS: ERROR — "
                f"{error}"
            )

            errores += 1

            print()

            continue

        if not datos_odds:

            print(
                "ODDS: sin datos"
            )

            sin_cuotas += 1

            print()

            continue

        # ====================================================
        # EXTRAER 1X2
        # ====================================================

        try:

            cuotas = extraer_1x2(
                datos_odds
            )

        except Exception as error:

            print(
                f"ODDS: ERROR "
                f"extrayendo 1X2 — "
                f"{error}"
            )

            errores += 1

            print()

            continue

        if cuotas is None:

            print(
                "ODDS: no hay mercado 1X2"
            )

            sin_cuotas += 1

            print()

            continue

        print(
            "ODDS: OK — Bet365"
        )

        # ====================================================
        # SNAPSHOT
        # ====================================================

        if guardar_odds_snapshot(
            evento,
            cuotas
        ):

            snapshots_guardados += 1

            print(
                "SNAPSHOT: guardado"
            )

        else:

            print(
                "SNAPSHOT: ya existente"
            )

        # ====================================================
        # VALUE
        # ====================================================

        mercados = analizar_value(
            evento,
            resultado_v2,
            cuotas
        )

        positivos = [

            mercado

            for mercado in mercados

            if mercado[
                "ev"
            ] >= MIN_EV
        ]

        if positivos:

            print(
                f"VALUE: "
                f"{len(positivos)}"
            )

            resultados.extend(
                positivos
            )

            (
                cantidad_guardada,
                cantidad_duplicada
            ) = guardar_values(
                positivos
            )

            values_guardados += (
                cantidad_guardada
            )

            print(
                f"VALUE SNAPSHOT: "
                f"{cantidad_guardada} nuevos"
            )

            if cantidad_duplicada > 0:

                print(
                    f"VALUE DUPLICADO: "
                    f"{cantidad_duplicada}"
                )

        else:

            print(
                "VALUE: ninguno"
            )

        print()

    # ========================================================
    # ORDENAR
    # ========================================================

    resultados.sort(
        key=lambda x: x["ev"],
        reverse=True
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print("=" * 80)

    print(
        "RESUMEN"
    )

    print("=" * 80)

    print()

    print(
        f"Eventos pendientes: "
        f"{len(eventos)}"
    )

    print(
        f"VALUE positivo: "
        f"{len(resultados)}"
    )

    print(
        f"Snapshots guardados: "
        f"{snapshots_guardados}"
    )

    print(
        f"Values guardados: "
        f"{values_guardados}"
    )

    print(
        f"Sin matching: "
        f"{sin_matching}"
    )

    print(
        f"Sin V2: "
        f"{sin_v2}"
    )

    print(
        f"Sin cuotas 1X2: "
        f"{sin_cuotas}"
    )

    print(
        f"Errores: "
        f"{errores}"
    )

    # ========================================================
    # TOP VALUE
    # ========================================================

    print()

    print("=" * 80)

    print(
        "TOP VALUE"
    )

    print("=" * 80)

    if not resultados:

        print()

        print(
            "No se encontraron apuestas "
            "con EV positivo."
        )

        print()

        print("=" * 80)

        return

    print()

    print(
        f"{'#':<4}"
        f"{'Partido':<45}"
        f"{'Mercado':<12}"
        f"{'Prob.':<9}"
        f"{'Cuota':<8}"
        f"{'Justa':<8}"
        f"EV"
    )

    print(
        "-" * 100
    )

    for indice, resultado in enumerate(
        resultados[:20],
        start=1
    ):

        partido_nombre = (
            f"{resultado['local']} "
            f"vs "
            f"{resultado['visitante']}"
        )

        if len(partido_nombre) > 43:

            partido_nombre = (
                partido_nombre[:43]
            )

        print(
            f"{indice:<4}"
            f"{partido_nombre:<45}"
            f"{resultado['mercado']:<12}"
            f"{resultado['probabilidad'] * 100:>6.2f}% "
            f"{resultado['cuota']:<8.2f}"
            f"{resultado['cuota_justa']:<8.2f}"
            f"{resultado['ev'] * 100:>6.2f}%"
        )

    print()

    print("=" * 80)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()