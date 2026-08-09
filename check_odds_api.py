import os
import requests
from dotenv import load_dotenv


def main():

    load_dotenv()

    api_key = os.getenv("ODDS_API_KEY")

    print("=" * 60)
    print("DIAGNÓSTICO ODDS-API.IO")
    print("=" * 60)

    if not api_key:

        print()
        print("ERROR: no se encontró ODDS_API_KEY en .env")
        return

    print()
    print("API KEY: encontrada")
    print(
        f"API KEY: {api_key[:4]}..."
    )

    url = "https://api.odds-api.io/v3/sports"

    headers = {
        "X-API-Key": api_key
    }

    try:

        respuesta = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        print(
            f"HTTP STATUS: "
            f"{respuesta.status_code}"
        )

        if respuesta.status_code == 200:

            print()
            print("CONEXIÓN: OK")
            print("API KEY: VÁLIDA")

            datos = respuesta.json()

            print()
            print(
                f"Deportes recibidos: "
                f"{len(datos)}"
            )

        else:

            print()
            print("CONEXIÓN: ERROR")

            print()
            print(
                "Respuesta de la API:"
            )

            print(
                respuesta.text[:1000]
            )

    except requests.exceptions.RequestException as error:

        print()
        print("ERROR DE CONEXIÓN")
        print(error)

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()