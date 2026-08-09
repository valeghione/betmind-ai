import os
import requests
from dotenv import load_dotenv


def main():

    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:
        print("ERROR: no se encontró ODDS_API_KEY")
        return

    url = "https://api.odds-api.io/v3/leagues"

    params = {
        "apiKey": api_key,
        "sport": "football"
    }

    print("=" * 70)
    print("BUSCANDO LIGAS — ODDS-API.IO")
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

            print()
            print("ERROR:")
            print(respuesta.text[:2000])

            return

        ligas = respuesta.json()

        print()
        print(
            f"Ligas encontradas: {len(ligas)}"
        )

        print()

        encontradas = 0

        for liga in ligas:

            nombre = str(
                liga.get("name", "")
            )

            slug = str(
                liga.get("slug", "")
            )

            if (
                "argentin" in nombre.lower()
                or
                "argentin" in slug.lower()
                or
                "primera" in nombre.lower()
                or
                "primera" in slug.lower()
            ):

                print(
                    f"Nombre: {nombre}"
                )

                print(
                    f"Slug:   {slug}"
                )

                print(
                    f"Datos:  {liga}"
                )

                print()

                encontradas += 1

        if encontradas == 0:

            print(
                "No se encontró automáticamente "
                "una liga argentina."
            )

            print()
            print(
                "Primeras ligas disponibles:"
            )

            for liga in ligas[:30]:

                print(
                    f"- {liga.get('name')} "
                    f"→ {liga.get('slug')}"
                )

    except requests.exceptions.RequestException as error:

        print()
        print("ERROR DE CONEXIÓN:")
        print(error)

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()