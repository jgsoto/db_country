from conexion_bd import conectar_db
from geopy.geocoders import Nominatim
import pycountry
import time

geolocator = Nominatim(user_agent="country_detector")

def obtener_iso3(location):

    try:
        geo = geolocator.geocode(location, language="en")

        if not geo:
            return None

        address = geo.raw.get("display_name", "")
        pais = address.split(",")[-1].strip()

        country = pycountry.countries.get(name=pais)

        if country:
            return country.alpha_3

    except:
        return None

    return None


def procesar_locations():

    conexion = conectar_db()
    cursor = conexion.cursor()

    query = """
    SELECT id, location
    FROM public.salert_basic
    WHERE red BETWEEN 1 AND 3
    AND location IS NOT NULL
    AND location != ''
    AND country IS NULL
    ORDER BY extract_date DESC
    LIMIT 100
    """

    cursor.execute(query)

    registros = cursor.fetchall()

    for id_registro, location in registros:

        print("Procesando:", location)

        iso3 = obtener_iso3(location)

        print("ISO3:", iso3)

        if iso3:
            cursor.execute(
                """
                UPDATE public.salert_basic
                SET country = %s
                WHERE id = %s
                """,
                (iso3, id_registro)
            )

            conexion.commit()

        time.sleep(1)  # evitar bloqueo de API


    cursor.close()
    conexion.close()


if __name__ == "__main__":
    procesar_locations()