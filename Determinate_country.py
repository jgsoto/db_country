from conexion_bd import conectar_db
import pycountry
import os
import time
import re
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

        prompt = f"""
        Determina el país del siguiente texto de ubicación de una biografía de red social.

        Reglas:
        - Si aparece una ciudad conocida, deduce su país.
        - Si hay abreviaturas (ej: FL, BA, CABA) infiere el país.
        - Si hay múltiples países, elige el más probable.
        - Si realmente no se puede inferir el país responde SOLO: NONE

        Responde SOLO con el código ISO3 del país.

        Texto:
        "{location}"
        """
        try:

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres experto en geografía y análisis de redes sociales.",
                    },
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

    # eliminar emojis
    loc = re.sub(r"[^\w\s,.-]", "", loc)

    # eliminar espacios duplicados
    loc = re.sub(r"\s+", " ", loc)
    
    # eliminar números de teléfono
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
# PIPELINE
# --------------------------------------------------


def obtener_iso3(location, ia_client):

    if location in cache:
        return cache[location]

    loc_limpia = limpiar_location(location)

    if not es_texto_valido(loc_limpia):
        cache[location] = None
        return None

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

            time.sleep(0.3)

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
