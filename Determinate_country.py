from conexion_bd import conectar_db
from geopy.geocoders import Nominatim
from geotext import GeoText
import pycountry
import time
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

geolocator = Nominatim(user_agent="country_detector")
cache = {}

# Diccionario de alias para abreviaturas y nombres comunes
ALIASES = {
    "Guayaqui": "Guayaquil",
    "B.A.": "Buenos Aires",
    "Ec": "Ecuador",
    "Argen": "Argentina",
    "Bs. As.": "Buenos Aires"
}

def limpiar_location(location):
    """Elimina caracteres irrelevantes y aplica alias"""
    loc = location.strip()
    # reemplazar alias
    for k, v in ALIASES.items():
        loc = re.sub(rf"\b{k}\b", v, loc, flags=re.IGNORECASE)
    # eliminar emojis y símbolos extraños
    loc = re.sub(r"[^\w\s,.-]", "", loc)
    return loc

def es_texto_valido(location):
    """Filtra textos irrelevantes"""
    if len(location.strip()) < 3:
        return False
    if re.search(r"http[s]?://", location):
        return False
    if re.search(r"[0-9]{3,}", location):
        return False
    return True

class IAGroqPais:
    """Cliente Groq para inferir ISO3"""

    def __init__(self):
        self.api_key = os.environ.get("GROQCLOUD_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    def obtener_iso3_ia(self, location):
        prompt = f"""
        Analiza la siguiente ubicación y determina el país correspondiente en formato ISO3 (solo el código):
        Ubicación: "{location}"
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en geografía."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            iso3 = response.choices[0].message.content.strip().upper()
            if pycountry.countries.get(alpha_3=iso3):
                return iso3
        except Exception as e:
            print("Error IA Groq:", e)
        return None

def detectar_pais_texto(texto):
    lugares = GeoText(texto)
    if lugares.countries:
        return lugares.countries[0]
    return None

def obtener_iso3(location, ia_client):
    """Función principal para obtener ISO3 y su fuente"""
    if location in cache:
        return cache[location]

    loc_limpia = limpiar_location(location)
    if not es_texto_valido(loc_limpia):
        cache[location] = (None, None)
        return None, None

    # 1️⃣ GeoText/Geopy solo si confiable
    pais = detectar_pais_texto(loc_limpia)
    if pais:
        try:
            country = pycountry.countries.lookup(pais)
            iso3 = country.alpha_3
            cache[location] = (iso3, "GEO")
            return iso3, "GEO"
        except:
            pass

    try:
        geo = geolocator.geocode(loc_limpia, language="en", addressdetails=True)
        if geo:
            pais = geo.raw.get("address", {}).get("country")
            if pais:
                country = pycountry.countries.lookup(pais)
                iso3 = country.alpha_3
                cache[location] = (iso3, "GEO")
                time.sleep(1)  # respetar límite API
                return iso3, "GEO"
    except:
        pass

    # 2️⃣ Fallback Groq IA
    iso3_ia = ia_client.obtener_iso3_ia(loc_limpia)
    if iso3_ia:
        cache[location] = (iso3_ia, "GROQ")
        return iso3_ia, "GROQ"

    cache[location] = (None, None)
    return None, None

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
            iso3, fuente = obtener_iso3(location, ia_client)
            print("ISO3:", iso3, "| Fuente:", fuente)

            if iso3:
                cursor.execute(
                    """
                    UPDATE public.salert_basic
                    SET country = %s
                    WHERE id = %s
                    """,
                    (iso3, id_registro)
                )
                aciertos += 1

            contador += 1
            if contador % 100 == 0:
                conexion.commit()
                print("Commit lote:", contador)

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