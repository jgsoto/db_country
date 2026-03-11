import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def conectar_db():
    try:
        conexion = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT')
        )

        print("¡Conexión exitosa a PostgreSQL!")

        # Mostrar versión (opcional)
        cursor = conexion.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("Versión del servidor:", db_version)

        cursor.close()

        return conexion   # 🔑 IMPORTANTE

    except Exception as error:
        print(f"Error al conectar: {error}")
        return None


if __name__ == "__main__":
    conexion = conectar_db()

    if conexion:
        print("Conexión lista para usarse")
        conexion.close()