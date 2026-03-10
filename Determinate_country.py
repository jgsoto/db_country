from conexion_bd import conectar_db
import pycountry
import os
import time
import re
import unicodedata
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

cache = {}

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

        # PROMPT ULTRA OPTIMIZADO
        prompt = f"""
        Infer the country from this social media location.
        Use cities, regions, or abbreviations if present.
        If impossible return NONE.

        Return ONLY the ISO3 code.

        Location: "{location}"
        """
        try:

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=4,
            )

            resultado = response.choices[0].message.content.strip().upper()

            # Buscar código ISO3 válido
            match = re.search(r"\b[A-Z]{3}\b", resultado)

            if match:
                iso3 = match.group(0)

                if pycountry.countries.get(alpha_3=iso3):
                    return iso3

            if "NONE" in resultado:
                return None

        except Exception as e:
            print("Error IA:", e)

        return None


# --------------------------------------------------
# LIMPIEZA TEXTO
# --------------------------------------------------


def quitar_acentos(texto):

    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def limpiar_location(location):

    loc = location.strip()

    # eliminar emojis
    loc = re.sub(r"[^\w\s,.-]", "", loc)

    # eliminar acentos
    loc = quitar_acentos(loc)

    # eliminar espacios duplicados
    loc = re.sub(r"\s+", " ", loc)

    # eliminar números de teléfono
    loc = re.sub(r"\+?\d[\d\s\-]{6,}", "", loc)

    # eliminar direcciones
    loc = re.sub(r"#\d+", "", loc)

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
# DETECCIÓN DIRECTA DE PAÍS (sin IA)
# --------------------------------------------------


def detectar_pais_directo(location):

    loc_lower = location.lower()

    for country in pycountry.countries:

        if country.name.lower() in loc_lower:
            return country.alpha_3

    return None


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------


def obtener_iso3(location, ia_client):

    if location in cache:
        return cache[location]

    loc_limpia = limpiar_location(location)

    if not es_texto_valido(loc_limpia):
        cache[location] = None
        return None

    # intentar detectar país sin IA
    iso3_directo = detectar_pais_directo(loc_limpia)

    if iso3_directo:
        cache[location] = iso3_directo
        return iso3_directo

    # usar IA
    iso3 = ia_client.obtener_iso3_ia(loc_limpia)

    cache[location] = iso3

    return iso3


# --------------------------------------------------
# PROCESAR DB
# --------------------------------------------------


def procesar_locations():

    ia_client = IAGroqPais()

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

    print("Total registros:", len(registros))

    contador = 0
    aciertos = 0

    try:

        for id_registro, location in registros:

            print("Procesando:", location)

            iso3 = obtener_iso3(location, ia_client)

            print("ISO3:", iso3)

            if iso3:

                cursor.execute(
                    """
                    UPDATE public.salert_basic
                    SET country = %s
                    WHERE id = %s
                    """,
                    (iso3, id_registro),
                )

                aciertos += 1

            contador += 1

            if contador % 100 == 0:

                conexion.commit()

                print("Commit lote:", contador)

            time.sleep(0.2)

        conexion.commit()

        print("Proceso terminado")

        efectividad = (aciertos / contador) * 100

        print(f"Efectividad aproximada: {efectividad:.2f}%")

    except Exception as e:

        print("Error:", e)

        conexion.rollback()

        print("Rollback ejecutado")

    finally:

        cursor.close()
        conexion.close()


if __name__ == "__main__":
    procesar_locations()