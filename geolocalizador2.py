from conexion_bd import conectar_db
from geopy.geocoders import Nominatim
from geotext import GeoText
import pycountry
import time

geolocator = Nominatim(user_agent="country_detector")

# cache para evitar repetir consultas
cache = {}


def detectar_pais_texto(texto):
    """Detecta país directamente del texto"""
    lugares = GeoText(texto)

    if lugares.countries:
        return lugares.countries[0]

    return None


def obtener_iso3(location):

    if location in cache:
        return cache[location]

    # 1️⃣ intentar detectar país directo del texto
    pais = detectar_pais_texto(location)

    if pais:
        try:
            country = pycountry.countries.lookup(pais)
            iso3 = country.alpha_3
            cache[location] = iso3
            return iso3
        except:
            pass

    # 2️⃣ fallback usando geocoder
    try:
        geo = geolocator.geocode(location, language="en", addressdetails=True)

        if geo:
            pais = geo.raw.get("address", {}).get("country")

            if pais:
                country = pycountry.countries.lookup(pais)
                iso3 = country.alpha_3
                cache[location] = iso3
                time.sleep(1)  # respetar límite API
                return iso3

    except:
        pass

    cache[location] = None
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
    LIMIT 500
    """

    cursor.execute(query)

    registros = cursor.fetchall()

    print("Total registros:", len(registros))

    contador = 0

    try:

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

            contador += 1

            # commit cada 100 registros
            if contador % 100 == 0:
                conexion.commit()
                print("Commit lote:", contador)

        conexion.commit()
        print("Proceso terminado")

    except Exception as e:

        print("Error:", e)
        conexion.rollback()
        print("Rollback ejecutado")

    finally:

        cursor.close()
        conexion.close()


if __name__ == "__main__":
    procesar_locations()