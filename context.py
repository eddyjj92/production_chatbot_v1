import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Conexión a la base de datos
conn = psycopg2.connect(
    host="82.29.197.144",
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD")
)

# Crear cursor
cur = conn.cursor(cursor_factory=RealDictCursor)


def getEstablishmentContext(id):
    try:
        # Ejecutar una consulta
        cur.execute("SELECT * FROM establishments WHERE id = %s", (id,))
        # Obtener resultados
        return cur.fetchone()
    except psycopg2.Error as e:
        # Manejar errores específicos de la base de datos
        print(f"Error al acceder al restaurante: {e}")
        return None

def getChatbotContext(id):
    try:
        # Ejecutar una consulta
        cur.execute("SELECT * FROM chatbots WHERE establishment_id = %s", (id,))
        # Obtener resultados
        return cur.fetchone()
    except psycopg2.Error as e:
        # Manejar errores específicos de la base de datos
        print(f"Error al acceder al restaurante: {e}")
        return None


def getRestaurantDishesContext(id):
    try:
        # Ejecutar una consulta
        cur.execute("SELECT * FROM dishes WHERE establishment_id = %s", (id,))
        # Obtener resultados
        return cur.fetchall()
    except psycopg2.Error as e:
        # Manejar errores específicos de la base de datos
        print(f"Error al acceder a los platillos: {e}")
        return None


def getRestaurantsContext():
    try:
        # Ejecutar una consulta
        cur.execute("SELECT * FROM establishments")
        # Obtener resultados
        return cur.fetchall()
    except psycopg2.Error as e:
        # Manejar errores específicos de la base de datos
        print(f"Error al acceder a los restaurantes: {e}")
        return None

