from conexion_bd import conectar_db
import pycountry
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

cache_memoria = {}

# --------------------------------------------------
# IA GROQ
# --------------------------------------------------

class IAGroqPais:

    def __init__(self):

        self.api_key = os.environ.get("GROQCLOUD_API_KEY")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    def obtener_iso3_ia(self, location):

        prompt = f"""
Return the ISO3 country code for this social media location text.
If the country cannot be inferred return NONE.

Text: {location}
"""

        try:

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Return only ISO3 country code."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )

            resultado = response.choices[0].message.content.strip().upper()

            if resultado == "NONE":
                return None

            if pycountry.countries.get(alpha_3=resultado):
                return resultado

        except Exception as e:
            print("Error IA:", e)

        return None


# --------------------------------------------------
# LIMPIEZA TEXTO
# --------------------------------------------------

def limpiar_location(location):

    loc = location.strip()

    loc = re.sub(r"[^\w\s,.-]", "", loc)
    loc = re.sub(r"\s+", " ", loc)
    loc = re.sub(r"\+?\d[\d\s\-]{6,}", "", loc)

    return loc


def es_texto_valido(location):

    if len(location.strip()) < 3:
        return False

    if re.search(r"http", location):
        return False

    if re.search(r"[0-9]{5,}", location):
        return False

    return True


# --------------------------------------------------
# CACHE BD
# --------------------------------------------------

def buscar_cache(cursor, location):

    cursor.execute(
        """
        SELECT iso3
        FROM location_iso_cache
        WHERE location = %s
        """,
        (location,),
    )

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    return None


def guardar_cache(cursor, location, iso3):

    cursor.execute(
        """
        INSERT INTO location_iso_cache (location, iso3)
        VALUES (%s,%s)
        ON CONFLICT (location)
        DO NOTHING
        """,
        (location, iso3),
    )


# --------------------------------------------------
# PIPELINE ISO3
# --------------------------------------------------

def obtener_iso3(location, ia_client, cursor):

    loc_limpia = limpiar_location(location)

    if loc_limpia in cache_memoria:
        return cache_memoria[loc_limpia]

    if not es_texto_valido(loc_limpia):
        cache_memoria[loc_limpia] = None
        return None

    # buscar en cache BD
    iso3_cache = buscar_cache(cursor, loc_limpia)

    if iso3_cache:
        print("ISO3 cache BD:", iso3_cache)
        cache_memoria[loc_limpia] = iso3_cache
        return iso3_cache

    # llamar IA
    iso3 = ia_client.obtener_iso3_ia(loc_limpia)

    guardar_cache(cursor, loc_limpia, iso3)

    cache_memoria[loc_limpia] = iso3

    return iso3


# --------------------------------------------------
# PROCESAR DB
# --------------------------------------------------

def procesar_locations():

    ia_client = IAGroqPais()

    conexion = conectar_db()
    cursor = conexion.cursor()

    query = """
    SELECT DISTINCT location
    FROM public.salert_basic
    WHERE red BETWEEN 1 AND 3
    AND location IS NOT NULL
    AND location != ''
    AND country IS NULL
    LIMIT 1000
    """

    cursor.execute(query)

    locations = cursor.fetchall()

    print("Locations únicas encontradas:", len(locations))

    procesadas = 0
    aciertos = 0

    try:

        for (location,) in locations:

            print("\nProcesando:", location)

            iso3 = obtener_iso3(location, ia_client, cursor)

            print("ISO3:", iso3)

            if iso3:

                cursor.execute(
                    """
                    UPDATE public.salert_basic
                    SET country = %s
                    WHERE location = %s
                    AND country IS NULL
                    """,
                    (iso3, location),
                )

                aciertos += 1

            procesadas += 1

            if procesadas % 50 == 0:

                conexion.commit()

                print("Commit lote:", procesadas)

        conexion.commit()

        print("\nProceso terminado")

        efectividad = (aciertos / procesadas) * 100

        print(f"Efectividad aproximada: {efectividad:.2f}%")

    except Exception as e:

        print("Error:", e)

        conexion.rollback()

        print("Rollback ejecutado")

    finally:

        cursor.close()
        conexion.close()


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    procesar_locations()