from collections import Counter

from database.database import Database


def main():

    db = Database()

    partidos = db.obtener_partidos()

    print(f"\nHay {len(partidos)} partidos en la base de datos.\n")

    ligas = Counter()

    for partido in partidos:
        ligas[partido["liga"]] += 1

    print("===== LIGAS =====\n")

    for liga, cantidad in ligas.most_common():

        print(f"{liga}: {cantidad} partidos")


if __name__ == "__main__":
    main()