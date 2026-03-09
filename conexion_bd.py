import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def conectar_db():
    try:
        # Establecer la conexión
        conexion = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT')
        )
        
        cursor = conexion.cursor()
        print("¡Conexión exitosa a PostgreSQL!")

        # Ejemplo: Ejecutar una consulta
        cursor.execute('SELECT version();')
        db_version = cursor.fetchone()
        print(f"Versión del servidor: {db_version}")

        # Cerrar herramientas
        cursor.close()
        conexion.close()

    except Exception as error:
        print(f"Error al conectar: {error}")

if __name__ == "__main__":
    conectar_db()