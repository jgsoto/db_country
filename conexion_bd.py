import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def __init__(self):
        try:
            # Establecer la conexión como atributo de clase
            self.conexion = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASS'),
                port=os.getenv('DB_PORT')
            )
            self.cursor = self.conexion.cursor()
            print("Conexión establecida con éxito.")
            
        except Exception as error:
            print(f"Error al conectar: {error}")
            self.conexion = None

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

        return conexion   # 👈 IMPORTANTE

    except Exception as error:
        print(f"Error al conectar: {error}")
        return None

if __name__ == "__main__":
    conectar_db()