# diagnostico_postgres.py

from conexion_bd import conectar_db

def diagnostico():
    conexion = conectar_db()

    if not conexion:
        print("No se pudo conectar a la base de datos")
        return

    try:
        cursor = conexion.cursor()

        print("\n=========== INFORMACIÓN DE CONEXIÓN ===========")

        # Base de datos actual
        cursor.execute("SELECT current_database();")
        db_actual = cursor.fetchone()[0]
        print(f"Base de datos actual: {db_actual}")

        # Usuario actual
        cursor.execute("SELECT current_user;")
        usuario = cursor.fetchone()[0]
        print(f"Usuario conectado: {usuario}")

        # Versión del servidor
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Versión PostgreSQL: {version}")

        print("\n=========== BASES DE DATOS EN EL SERVIDOR ===========")

        cursor.execute("""
        SELECT datname
        FROM pg_database
        WHERE datistemplate = false;
        """)

        for db in cursor.fetchall():
            print("-", db[0])

        print("\n=========== SCHEMAS ===========")

        cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        ORDER BY schema_name;
        """)

        for schema in cursor.fetchall():
            print("-", schema[0])

        print("\n=========== TABLAS ===========")

        cursor.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name;
        """)

        tablas = cursor.fetchall()

        if not tablas:
            print("No se encontraron tablas.")
        else:
            for schema, tabla in tablas:
                print(f"{schema}.{tabla}")

        cursor.close()

    except Exception as e:
        print("Error durante el diagnóstico:", e)

    finally:
        conexion.close()
        print("\nConexión cerrada")


if __name__ == "__main__":
    diagnostico()