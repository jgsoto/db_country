from conexion_bd import conectar_db
from geopy.geocoders import Nominatim
import pycountry
import time
import re

geolocator = Nominatim(user_agent="country_detector")

CACHE = {}

def limpiar_location(texto):

    texto = texto.lower()

    texto = re.sub(r"http\S+", "", texto)
    texto = re.sub(r"[^\w\s,]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def obtener_iso3(location):

    location = limpiar_location(location)

    if location in CACHE:
        return CACHE[location]

    try:

        geo = geolocator.geocode(
            location,
            addressdetails=True,
            language="en"
        )

        if not geo:
            CACHE[location] = None
            return None

        address = geo.raw.get("address", {})

        country_code = address.get("country_code")

        if not country_code:
            CACHE[location] = None
            return None

        country = pycountry.countries.get(alpha_2=country_code.upper())

        if country:

            iso3 = country.alpha_3
            CACHE[location] = iso3

            return iso3

    except Exception as e:

        print("Error:", e)

    CACHE[location] = None
    return None


def procesar_locations():

    conexion = conectar_db()
    cursor = conexion.cursor()

    BATCH = 20

    while True:

        cursor.execute(f"""
        SELECT id, location
        FROM public.salert_basic
        WHERE red BETWEEN 1 AND 3
        AND location IS NOT NULL
        AND location != ''
        AND country IS NULL
        LIMIT {BATCH}
        """)

        registros = cursor.fetchall()

        if not registros:
            break

        for id_registro, location in registros:

            print("Procesando:", location)

            iso3 = obtener_iso3(location)

            print("ISO3:", iso3)

            if iso3:

                cursor.execute("""
                UPDATE public.salert_basic
                SET country = %s
                WHERE id = %s
                """, (iso3, id_registro))

        conexion.commit()

        time.sleep(1)

    cursor.close()
    conexion.close()


if __name__ == "__main__":
    procesar_locations()