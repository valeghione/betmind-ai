from database.database import Database


# ============================================================
# GUARDAR SNAPSHOT DE CUOTAS
# ============================================================

def guardar_snapshot(
    event_id,
    fecha_evento,
    local,
    visitante,
    bookmaker,
    cuota_local,
    cuota_empate,
    cuota_visitante
):

    db = Database()

    db.cursor.execute("""
        INSERT INTO odds_snapshots (
            event_id,
            fecha_evento,
            local,
            visitante,
            bookmaker,
            cuota_local,
            cuota_empate,
            cuota_visitante
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        fecha_evento,
        local,
        visitante,
        bookmaker,
        cuota_local,
        cuota_empate,
        cuota_visitante
    ))

    db.connection.commit()
    db.cerrar()


# ============================================================
# OBTENER SNAPSHOTS
# ============================================================

def obtener_snapshots():

    db = Database()

    db.cursor.execute("""
        SELECT *
        FROM odds_snapshots
        ORDER BY timestamp DESC
    """)

    resultados = db.cursor.fetchall()

    db.cerrar()

    return resultados


# ============================================================
# GUARDAR RESULTADO
# ============================================================

def guardar_resultado(
    event_id,
    fecha_evento,
    local,
    visitante,
    goles_local,
    goles_visitante
):

    if goles_local > goles_visitante:
        resultado = "local"

    elif goles_local == goles_visitante:
        resultado = "empate"

    else:
        resultado = "visitante"

    db = Database()

    db.cursor.execute("""
        INSERT OR REPLACE INTO odds_results (
            event_id,
            fecha_evento,
            local,
            visitante,
            goles_local,
            goles_visitante,
            resultado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        fecha_evento,
        local,
        visitante,
        goles_local,
        goles_visitante,
        resultado
    ))

    db.connection.commit()
    db.cerrar()


# ============================================================
# OBTENER RESULTADOS
# ============================================================

def obtener_resultados():

    db = Database()

    db.cursor.execute("""
        SELECT *
        FROM odds_results
        ORDER BY fecha_evento DESC
    """)

    resultados = db.cursor.fetchall()

    db.cerrar()

    return resultados


# ============================================================
# GUARDAR VALUE
# ============================================================

def guardar_value(
    event_id,
    fecha_evento,
    local,
    visitante,
    mercado,
    probabilidad_modelo,
    cuota,
    cuota_justa,
    ev,
    prediccion
):

    db = Database()

    # --------------------------------------------------------
    # Evitar duplicar exactamente la misma oportunidad
    # mientras el scanner se ejecuta varias veces.
    #
    # Si ya existe una oportunidad abierta para:
    # event_id + mercado
    #
    # no volvemos a crear otra.
    # --------------------------------------------------------

    db.cursor.execute("""
        SELECT id
        FROM value_opportunities
        WHERE event_id = ?
        AND mercado = ?
        AND resultado IS NULL
        LIMIT 1
    """, (
        event_id,
        mercado
    ))

    existente = db.cursor.fetchone()

    if existente is not None:

        db.cerrar()

        return False

    db.cursor.execute("""
        INSERT INTO value_opportunities (
            event_id,
            fecha_evento,
            local,
            visitante,
            mercado,
            probabilidad_modelo,
            cuota,
            cuota_justa,
            ev,
            prediccion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        fecha_evento,
        local,
        visitante,
        mercado,
        probabilidad_modelo,
        cuota,
        cuota_justa,
        ev,
        prediccion
    ))

    db.connection.commit()
    db.cerrar()

    return True


# ============================================================
# OBTENER VALUE
# ============================================================

def obtener_values():

    db = Database()

    db.cursor.execute("""
        SELECT *
        FROM value_opportunities
        ORDER BY timestamp DESC
    """)

    resultados = db.cursor.fetchall()

    db.cerrar()

    return resultados


# ============================================================
# ACTUALIZAR RESULTADO DE VALUE
# ============================================================

def actualizar_value(
    value_id,
    resultado,
    ganancia
):

    db = Database()

    db.cursor.execute("""
        UPDATE value_opportunities
        SET
            resultado = ?,
            ganancia = ?
        WHERE id = ?
    """, (
        resultado,
        ganancia,
        value_id
    ))

    db.connection.commit()
    db.cerrar()