from database.odds_history import crear_tablas_odds


def main():

    crear_tablas_odds()

    print(
        "Tablas odds creadas correctamente."
    )


if __name__ == "__main__":

    main()