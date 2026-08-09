from database.odds_repository import obtener_values


def main():

    values = obtener_values()

    print("=" * 100)
    print("BETMIND AI — VALUE OPPORTUNITIES")
    print("=" * 100)

    print()

    for value in values:

        print(
            f"ID: {value['id']}"
        )

        print(
            f"Event ID: {value['event_id']}"
        )

        print(
            f"{value['local']} vs "
            f"{value['visitante']}"
        )

        print(
            f"Mercado: "
            f"{value['mercado']}"
        )

        print(
            f"Probabilidad: "
            f"{value['probabilidad_modelo'] * 100:.2f}%"
        )

        print(
            f"Cuota: "
            f"{value['cuota']:.2f}"
        )

        print(
            f"Cuota justa: "
            f"{value['cuota_justa']:.2f}"
        )

        print(
            f"EV: "
            f"{value['ev'] * 100:.2f}%"
        )

        print(
            f"Resultado: "
            f"{value['resultado']}"
        )

        print(
            f"Ganancia: "
            f"{value['ganancia']}"
        )

        print("-" * 100)


if __name__ == "__main__":

    main()