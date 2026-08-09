from database.database import Database
from analysis.analyzer import analizar_forma_equipo
from analysis.match_analyzer import calcular_goles_esperados
from analysis.poisson import calcular_probabilidades_partido


# ============================================================
# CONFIGURACIÓN V2 — CONGELADA
# ============================================================

VENTANA = 5
SMOOTHING = 1
BINS = 10
CAP = None


RESULTADOS = [
    "local",
    "empate",
    "visitante"
]


# ============================================================
# DATOS
# ============================================================

def obtener_partidos():

    db = Database()

    partidos = db.obtener_partidos()

    db.cerrar()

    return partidos


# ============================================================
# MODELO BASE
# ============================================================

def generar_probabilidades_base(
    partido,
    partidos
):

    fecha_hasta = partido["fecha"]

    forma_local = analizar_forma_equipo(
        partido["home_team_id"],
        limite=VENTANA,
        condicion="local",
        fecha_hasta=fecha_hasta
    )

    forma_visitante = analizar_forma_equipo(
        partido["away_team_id"],
        limite=VENTANA,
        condicion="visitante",
        fecha_hasta=fecha_hasta
    )

    if forma_local is None:
        return None

    if forma_visitante is None:
        return None

    if forma_local["partidos"] < VENTANA:
        return None

    if forma_visitante["partidos"] < VENTANA:
        return None

    goles_esperados = calcular_goles_esperados(
        forma_local,
        forma_visitante
    )

    probabilidades = calcular_probabilidades_partido(
        goles_esperados["local"],
        goles_esperados["visitante"]
    )

    return {
        "local": probabilidades["local"],
        "empate": probabilidades["empate"],
        "visitante": probabilidades["visitante"]
    }


# ============================================================
# CALIBRACIÓN
# ============================================================

def crear_bins():

    bins = []

    for i in range(BINS):

        bins.append({
            "inferior":
                i / BINS,

            "superior":
                (i + 1) / BINS,

            "cantidad": 0,

            "suma_probabilidad": 0.0,

            "aciertos": 0
        })

    return bins


def obtener_bin(
    bins,
    probabilidad
):

    for i, bin_data in enumerate(bins):

        inferior = bin_data["inferior"]
        superior = bin_data["superior"]

        if i == BINS - 1:

            if (
                probabilidad >= inferior
                and
                probabilidad <= superior
            ):

                return bin_data

        else:

            if (
                probabilidad >= inferior
                and
                probabilidad < superior
            ):

                return bin_data

    return None


def construir_calibrador(
    resultados,
    resultado_objetivo
):

    bins = crear_bins()

    for resultado in resultados:

        probabilidad = (
            resultado["probabilidades"]
            [resultado_objetivo]
        )

        bin_data = obtener_bin(
            bins,
            probabilidad
        )

        if bin_data is None:
            continue

        bin_data["cantidad"] += 1

        bin_data[
            "suma_probabilidad"
        ] += probabilidad

        if (
            resultado["resultado_real"]
            ==
            resultado_objetivo
        ):

            bin_data["aciertos"] += 1

    return bins


def construir_calibradores(
    resultados
):

    calibradores = {}

    for resultado_objetivo in RESULTADOS:

        calibradores[
            resultado_objetivo
        ] = construir_calibrador(
            resultados,
            resultado_objetivo
        )

    return calibradores


def calibrar_probabilidad(
    bins,
    probabilidad
):

    bin_data = obtener_bin(
        bins,
        probabilidad
    )

    if bin_data is None:
        return probabilidad

    cantidad = bin_data["cantidad"]
    aciertos = bin_data["aciertos"]

    # Smoothing = 1
    calibrada = (
        aciertos + SMOOTHING
    ) / (
        cantidad
        +
        2 * SMOOTHING
    )

    return calibrada


def aplicar_calibracion(
    probabilidades,
    calibradores
):

    nuevas = {}

    for resultado_objetivo in RESULTADOS:

        nuevas[
            resultado_objetivo
        ] = calibrar_probabilidad(
            calibradores[
                resultado_objetivo
            ],
            probabilidades[
                resultado_objetivo
            ]
        )

    suma = sum(
        nuevas.values()
    )

    if suma <= 0:

        return probabilidades

    for resultado_objetivo in nuevas:

        nuevas[
            resultado_objetivo
        ] /= suma

    return nuevas


# ============================================================
# RESULTADO REAL
# ============================================================

def obtener_resultado_real(
    partido
):

    if (
        partido["goles_local"]
        >
        partido["goles_visitante"]
    ):

        return "local"

    if (
        partido["goles_local"]
        ==
        partido["goles_visitante"]
    ):

        return "empate"

    return "visitante"


# ============================================================
# ENTRENAR CALIBRACIÓN
# ============================================================

def entrenar():

    partidos = obtener_partidos()

    resultados = []

    for partido in partidos:

        # La calibración se entrena únicamente
        # con la temporada 2023.
        if partido["season"] != 2023:
            continue

        probabilidades = generar_probabilidades_base(
            partido,
            partidos
        )

        if probabilidades is None:
            continue

        resultados.append({
            "probabilidades":
                probabilidades,

            "resultado_real":
                obtener_resultado_real(
                    partido
                )
        })

    calibradores = construir_calibradores(
        resultados
    )

    return calibradores


# ============================================================
# PREDECIR
# ============================================================

def predecir(
    partido
):

    partidos = obtener_partidos()

    probabilidades_base = (
        generar_probabilidades_base(
            partido,
            partidos
        )
    )

    if probabilidades_base is None:

        return None

    calibradores = entrenar()

    probabilidades = aplicar_calibracion(
        probabilidades_base,
        calibradores
    )

    prediccion = max(
        probabilidades,
        key=probabilidades.get
    )

    return {
        "probabilidades_base":
            probabilidades_base,

        "probabilidades":
            probabilidades,

        "prediccion":
            prediccion
    }