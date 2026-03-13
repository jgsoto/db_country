from conexion_bd import conectar_db
from datetime import timedelta, datetime

def obtener_fechas_pendientes(cursor):

    cursor.execute(
        """
        SELECT DISTINCT DATE(b.extract_date)
        FROM public.salert_basic b
        JOIN public.salert_post_temp p
        ON p.page_id = b.id
        WHERE b.country IS NOT NULL
        AND p.pais IS NULL
        ORDER BY 1 DESC
        """
    )

    return [row[0] for row in cursor.fetchall()]

def obtener_horas(cursor, fecha):

    cursor.execute(
        """
        SELECT DISTINCT DATE_TRUNC('hour', extract_date)
        FROM public.salert_basic
        WHERE DATE(extract_date) = %s
        AND country IS NOT NULL
        ORDER BY 1 DESC
        """,
        (fecha,),
    )

    return [row[0] for row in cursor.fetchall()]

def sincronizar_post():

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:

        fechas = obtener_fechas_pendientes(cursor)

        if not fechas:
            print("No hay registros para sincronizar")
            return

        total_actualizados = 0

        for fecha in fechas:

            print("\nProcesando fecha:", fecha)

            horas = obtener_horas(cursor, fecha)

            print("Horas encontradas:", len(horas))

            for hora in horas:

                inicio = hora

                if isinstance(inicio, str):
                    inicio = datetime.fromisoformat(inicio)

                fin = inicio + timedelta(hours=1)

                print("\nSincronizando hora:", inicio)

                cursor.execute(
                    """
                    UPDATE public.salert_post_temp p
                    SET pais = b.country
                    FROM public.salert_basic b
                    WHERE page_id = b.id
                    AND p.pais IS NULL
                    AND b.country IS NOT NULL
                    AND b.extract_date >= %s
                    AND b.extract_date < %s
                    """,
                    (inicio, fin),
                )

                actualizados = cursor.rowcount
                total_actualizados += actualizados

                print("Registros actualizados:", actualizados)

                conexion.commit()

        print("\nSincronización terminada")
        print("Total registros actualizados:", total_actualizados)

    except Exception as e:

        print("Error:", e)
        conexion.rollback()
        print("Rollback ejecutado")

    finally:

        cursor.close()
        conexion.close()
        
def sincronizar_posts_por_hora(cursor, inicio, fin):

    cursor.execute(
        """
        UPDATE public.salert_post_temp p
        SET pais = b.country
        FROM public.salert_basic b
        WHERE p.page_id = b.id
        AND p.pais IS NULL
        AND b.country IS NOT NULL
        AND b.extract_date >= %s
        AND b.extract_date < %s
        """,
        (inicio, fin),
    )

    actualizados = cursor.rowcount

    print("Posts sincronizados:", actualizados)

    return actualizados