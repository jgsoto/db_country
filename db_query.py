from conexion_bd import conectar_db

def consultar_tabla():
    conexion = conectar_db()
    if not conexion:
        return

    try:
        cursor = conexion.cursor()

        query = "SELECT name, username, location, country, pic FROM public.salert_basic WHERE red BETWEEN 1 AND 3 AND location IS NOT NULL AND location != '' AND country IS NOT NULL ORDER BY extract_date DESC "
        cursor.execute(query)

        resultados = cursor.fetchall()

        for fila in resultados:
            print(fila)

        cursor.close()

    except Exception as e:
        print("Error en la consulta:", e)

    finally:
        conexion.close()


if __name__ == "__main__":
    consultar_tabla()