from database.odds_repository import guardar_snapshot
from database.odds_repository import obtener_snapshots


def main():

    guardar_snapshot(
        event_id=73265148,
        fecha_evento="2026-08-09T20:45:00Z",
        local="Defensa y Justicia",
        visitante="Newell's Old Boys",
        bookmaker="Bet365",
        cuota_local=2.05,
        cuota_empate=3.10,
        cuota_visitante=4.20
    )

    snapshots = obtener_snapshots()

    print()
    print("=" * 70)
    print("ODDS SNAPSHOTS")
    print("=" * 70)

    for snapshot in snapshots:

        print()
        print(f"ID:              {snapshot['id']}")
        print(f"Event ID:        {snapshot['event_id']}")
        print(f"Fecha evento:    {snapshot['fecha_evento']}")
        print(f"Local:           {snapshot['local']}")
        print(f"Visitante:       {snapshot['visitante']}")
        print(f"Bookmaker:       {snapshot['bookmaker']}")
        print(f"Cuota local:     {snapshot['cuota_local']}")
        print(f"Cuota empate:    {snapshot['cuota_empate']}")
        print(f"Cuota visitante: {snapshot['cuota_visitante']}")
        print(f"Guardado:        {snapshot['timestamp']}")

    print()
    print("=" * 70)
    print(
        f"Snapshots almacenados: {len(snapshots)}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()