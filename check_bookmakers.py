import os
import requests
from dotenv import load_dotenv


def main():

    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:
        print("ERROR: no se encontró ODDS_API_KEY")
        return

    url = "https://api.odds-api.io/v3/bookmakers"

    params = {
        "apiKey": api_key
    }

    print("=" * 70)
    print("BOOKMAKERS DISPONIBLES")
    print("=" * 70)

    try:

        respuesta = requests.get(
            url,
            params=params,
            timeout=15
        )

        print()
        print(
            f"HTTP STATUS: {respuesta.status_code}"
        )

        if respuesta.status_code != 200:

            print(respuesta.text[:3000])
            return

        datos = respuesta.json()

        print()
        print(f"Bookmakers recibidos: {len(datos)}")
        print()

        for bookmaker in datos:

            if isinstance(bookmaker, dict):

                nombre = bookmaker.get(
                    "name",
                    bookmaker.get("slug", "")
                )

                print(nombre)

            else:

                print(bookmaker)

    except requests.exceptions.RequestException as error:

        print()
        print("ERROR:")
        print(error)

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()