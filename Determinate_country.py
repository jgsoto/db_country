from conexion_bd import conectar_db
import pycountry
import os
import time
import re
import unicodedata
from datetime import timedelta, datetime
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
            match = re.search(r"\b[A-Z]{3}\b", resultado)
            if match and pycountry.countries.get(alpha_3=match.group(0)):
                return match.group(0)
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
    loc = re.sub(r"[^\w\s,.-]", "", loc)  # quitar emojis
    loc = quitar_acentos(loc)  # quitar acentos
    loc = re.sub(r"\s+", " ", loc)  # espacios duplicados
    loc = re.sub(r"\+?\d[\d\s\-]{6,}", "", loc)  # eliminar números de teléfono
    loc = re.sub(r"#\d+", "", loc)  # eliminar direcciones
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

    iso3_directo = detectar_pais_directo(loc_limpia)
    if iso3_directo:
        cache[location] = iso3_directo
        return iso3_directo

    iso3 = ia_client.obtener_iso3_ia(loc_limpia)
    cache[location] = iso3
    return iso3


# --------------------------------------------------
# FECHAS PENDIENTES
# --------------------------------------------------
def obtener_fechas_pendientes(cursor):
    cursor.execute(
        """
        SELECT DISTINCT DATE(extract_date)
        FROM public.salert_basic
        WHERE red BETWEEN 1 AND 3
          AND location IS NOT NULL
          AND location != ''
          AND country IS NULL
        ORDER BY 1
        """
    )
    return [row[0] for row in cursor.fetchall()]


def obtener_horas_con_registros(cursor, fecha):
    cursor.execute(
        """
        SELECT DISTINCT DATE_TRUNC('hour', extract_date)
        FROM public.salert_basic
        WHERE DATE(extract_date) = %s
          AND country IS NULL
        ORDER BY 1
        """,
        (fecha,),
    )
    return [row[0] for row in cursor.fetchall()]


# --------------------------------------------------
# PROCESAR LOCATIONS
# --------------------------------------------------
def procesar_locations():
    ia_client = IAGroqPais()
    conexion = conectar_db()
    cursor = conexion.cursor()

    fechas = obtener_fechas_pendientes(cursor)
    if not fechas:
        print("No hay registros pendientes")
        return

    contador = 0

    try:
        for fecha in fechas:
            print("\nProcesando fecha:", fecha)
            horas = obtener_horas_con_registros(cursor, fecha)
            print("Horas con registros:", len(horas))

            for hora in horas:
                inicio = hora
                if isinstance(inicio, str):
                    inicio = datetime.fromisoformat(inicio)
                fin = inicio + timedelta(hours=1)

                print("\nProcesando hora:", inicio)

                cursor.execute(
                    """
                    SELECT id, location
                    FROM public.salert_basic
                    WHERE red BETWEEN 1 AND 3
                      AND location IS NOT NULL
                      AND location != ''
                      AND country IS NULL
                      AND extract_date >= %s
                      AND extract_date < %s
                    """,
                    (inicio, fin),
                )
                registros = cursor.fetchall()
                print("Registros encontrados:", len(registros))

                for id_registro, location in registros:
                    print("Procesando:", location)
                    iso3 = obtener_iso3(location, ia_client)
                    print("ISO3:", iso3)

                    if iso3:
                        valor_country = iso3
                    else:
                        valor_country = "UNK"

                    cursor.execute(
                        """
                        UPDATE public.salert_basic
                        SET country = %s
                        WHERE id = %s
                        """,
                        (valor_country, id_registro),
                    )

                    contador += 1

                    # Commit y pregunta cada 100 registros
                    if contador % 100 == 0:
                        conexion.commit()
                        print(f"\nCommit completado: {contador} registros procesados")
                        respuesta = (
                            input("¿Desea continuar procesando? (s/n): ")
                            .strip()
                            .lower()
                        )
                        if respuesta != "s":
                            print("Proceso detenido por el usuario")
                            cursor.close()
                            conexion.close()
                            return

                    time.sleep(0.2)

        # Commit final al terminar todas las fechas
        conexion.commit()
        print("\nProceso terminado")

    except Exception as e:
        print("Error:", e)
        conexion.rollback()
        print("Rollback ejecutado")

    finally:
        cursor.close()
        conexion.close()


# --------------------------------------------------
if __name__ == "__main__":
    procesar_locations()
