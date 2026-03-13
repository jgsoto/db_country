from conexion_bd import conectar_db
from datetime import timedelta, datetime
from dotenv import load_dotenv
from country_ia import IAGroqPais
from country_clean import obtener_iso3
import time

load_dotenv()

def obtener_fechas_pendientes(cursor):

    cursor.execute(
        """
        SELECT DISTINCT DATE(extract_date)
        FROM public.salert_basic
        WHERE red BETWEEN 1 AND 3
          AND location IS NOT NULL
          AND location != ''
          AND country IS NULL
        ORDER BY 1 DESC
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
        ORDER BY 1 DESC
        """,
        (fecha,),
    )

    return [row[0] for row in cursor.fetchall()]


def procesar_locations():

    ia_client = IAGroqPais()
    conexion = conectar_db()
    cursor = conexion.cursor()

    fechas = obtener_fechas_pendientes(cursor)

    if not fechas:
        print("No hay registros pendientes")
        return

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
                    ORDER BY extract_date DESC
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
                        
                    if valor_country:

                        cursor.execute(
                            """
                            UPDATE public.salert_basic
                            SET country = %s
                            WHERE id = %s
                            """,
                            (valor_country, id_registro),
                        )

                    time.sleep(0.2)

                conexion.commit()

                print(f"Commit realizado para la hora {inicio}")

        conexion.commit()

        print("\nProceso terminado")

    except Exception as e:

        print("Error:", e)

        conexion.rollback()

        print("Rollback ejecutado")

    finally:

        cursor.close()

        conexion.close()


if __name__ == "__main__":
    procesar_locations()