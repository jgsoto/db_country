from conexion_bd import conectar_db


def sincronizar_country():

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:

        print("Iniciando sincronización de country...")

        cursor.execute(
            """
            UPDATE public.salert_post_temp p
            SET pais = b.country
            FROM public.salert_basic b
            WHERE p.page_id = b.id
            AND p.pais IS NULL
            AND b.country IS NOT NULL
            """
        )

        filas_actualizadas = cursor.rowcount

        conexion.commit()

        print(f"Sincronización completada")
        print(f"Registros actualizados: {filas_actualizadas}")

    except Exception as e:

        print("Error durante la sincronización:", e)
        conexion.rollback()
        print("Rollback ejecutado")

    finally:

        cursor.close()
        conexion.close()


if __name__ == "__main__":
    sincronizar_country()