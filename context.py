import psycopg2
from psycopg2.extras import RealDictCursor

# Conexión a la base de datos
conn = psycopg2.connect(
    host="82.29.197.144",
    database="clapzy",
    user="root",
    password="Clapzy.2025"
)

# Crear cursor
cur = conn.cursor(cursor_factory=RealDictCursor)


def getRestaurantContext(id):
    try:
        # Ejecutar una consulta
        cur.execute("SELECT * FROM restaurants WHERE id = %s", (id,))
        # Obtener resultados
        return cur.fetchone()
    except psycopg2.Error as e:
        # Manejar errores específicos de la base de datos
        print(f"Error al acceder al restaurante: {e}")
        return None


def getRestaurantDishesContext(id):
    try:
        # Ejecutar una consulta
        cur.execute("SELECT * FROM dishes WHERE restaurant_id = %s", (id,))
        # Obtener resultados
        return cur.fetchall()
    except psycopg2.Error as e:
        # Manejar errores específicos de la base de datos
        print(f"Error al acceder a los platillos: {e}")
        return None
