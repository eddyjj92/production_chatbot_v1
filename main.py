import os
import re
import requests
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.constants import END
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph
from typing import Dict, Optional

from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from models import llm  # Tu modelo CloudflareWorkersAI
from context import getEstablishmentContext, getChatbotContext, getRestaurantDishesContext, getRestaurantsContext
from langchain.tools import tool
import uuid  # Para generar IDs únicos

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧠 Memoria por sesión implementada manualmente
session_store: Dict[str, list] = {}
reservations_store: Dict[str, dict] = {}  # Almacenamiento de reservas
session_context_store: Dict[str, dict] = {}  # Nuevo: cache de contexto por sesión


def get_or_create_history(session_id: str) -> list:
    if session_id not in session_store:
        session_store[session_id] = []
    return session_store[session_id]


def get_or_create_session_context(session_id: str, restaurant_id: int) -> dict:
    context = session_context_store.get(session_id)

    if not context or context.get("restaurant_id") != restaurant_id:
        context = {
            "restaurant_id": restaurant_id,
            "establishment_context": getEstablishmentContext(restaurant_id),
            "dishes_context": getRestaurantDishesContext(restaurant_id),
            "chatbot_context": getChatbotContext(restaurant_id)
        }
        session_context_store[session_id] = context

    return context


# 📦 Modelo para la solicitud
class UserQuery(BaseModel):
    session_id: str
    question: str
    restaurant_id: int  # ← valor por defecto
    token: str


# 🔁 Nodo del grafo conversacional
MAX_HISTORY_LENGTH = 15  # número máximo de mensajes (puedes ajustarlo)


@tool
def detectar_intencion_reserva(question: str) -> bool:
    """Detecta si el usuario desea hacer una reserva."""
    palabras_clave_reserva = [
        r"\breservar\b", r"\breserva\b", r"\bquiero una mesa\b",
        r"\bpuedo reservar\b", r"\bhacer una reservación\b",
        r"\bdisponibilidad\b", r"\bmesa para\b"
    ]
    return any(re.search(palabra, question, re.IGNORECASE) for palabra in palabras_clave_reserva)


from datetime import datetime
from typing import Optional
import re


def validar_datos_reserva(data: dict) -> Optional[str]:
    """Valida los datos de reserva y devuelve un mensaje de error si algo falla."""
    fecha = data.get("fecha")
    hora = data.get("hora")
    personas = data.get("personas")

    # Validar formato de fecha (YYYY-MM-DD)
    if not fecha or not re.match(r"\d{4}-\d{2}-\d{2}", fecha):
        return "La fecha no es válida. Usa el formato YYYY-MM-DD."

    try:
        # Convertir la fecha proporcionada a un objeto datetime
        fecha_provided = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_actual = datetime.now().date()

        # Validar que la fecha sea mayor o igual a la fecha actual
        if fecha_provided.date() < fecha_actual:
            return "La fecha debe ser igual o posterior a la fecha actual."
    except ValueError:
        return "La fecha no es válida. Asegúrate de usar el formato correcto YYYY-MM-DD."

    # Validar formato de hora (HH:MM)
    if not hora:
        return "La hora no puede estar vacía."
    try:
        # Intentar convertir la hora a un objeto time
        datetime.strptime(hora, "%H:%M").time()
    except ValueError:
        return "La hora no es válida. Usa el formato HH:MM y asegúrate de que las horas y minutos sean válidos (ejemplo: 23:59)."

    print(fecha + " \n")
    print(hora + " \n")
    print(personas + " \n")
    # Validar número de personas
    if not personas or not personas.isdigit() or int(personas) <= 0:
        return "El número de personas debe ser un número positivo mayor que 0."

    return None


def procesar_reserva(state: dict) -> dict:
    """Procesa los datos de reserva y genera un ID único."""
    session_id = state["session_id"]
    history = get_or_create_history(session_id)
    user_data = state.get("user_data", {})

    validation_error = validar_datos_reserva(user_data)
    if validation_error:
        response = f"Lo siento, hubo un problema con tus datos: {validation_error}. 😔 Por favor, inténtalo de nuevo."
        reservation_id = None
    else:
        reservation_id = str(uuid.uuid4())  # Generar un ID único
        reservations_store[reservation_id] = {
            "session_id": session_id,
            "restaurant_id": state["restaurant_id"],
            "fecha": user_data["fecha"],
            "hora": user_data["hora"],
            "personas": user_data["personas"]
        }

        url = "https://www.clapzy.app/api/reservations"
        headers = {
            "Authorization": f"Bearer {state["token"]}",  # Reemplaza con tu token real
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "date": user_data["fecha"],  # Usa una fecha válida en formato YYYY-MM-DD
            "time": user_data["hora"],  # Hora en formato HH:MM
            "peoples": user_data["personas"],
            "restaurant_id": state["restaurant_id"]  # ID real del restaurante
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200 or response.status_code == 201:
            print("Reserva creada:", response.json())
            response = response.json()
            response = (
                f"¡Tu reserva ha sido confirmada! ✅ Aquí está tu ID de reserva (guardar para futuras consultas o "
                f"cancelación): {response["reservation"]["uuid"]}."
                "¿Necesitas ayuda con algo más? 🌟"
            )
        else:
            print("Error al crear la reserva:", response.status_code, response.text)
            response = (
                f"😡 Error al crear la reserva: {response.status_code, response.text}",
                "Inténtalo de Nuevo 😕👉😌"
            )

    history.append(AIMessage(content=response))
    return {"response": response, "reservation_id": reservation_id}


def conversational_node(state: dict) -> dict:
    session_id = state["session_id"]
    question = state["question"]
    restaurant_id = state["restaurant_id"]
    history = get_or_create_history(session_id)
    context = get_or_create_session_context(session_id, restaurant_id)

    # Mensaje del sistema con contexto actualizado
    system_message = SystemMessage(content=f"""
            Te llamas {context['chatbot_context']['name']} y eres un mesero en el restaurante {context['establishment_context']['name']}, atendiendo con un tono de comunicacion {context['chatbot_context']['communication_tone']}. Tu objetivo es ayudar con el menú, tomar pedidos y responder preguntas con precisión. Sigue estas reglas:  

            - Preséntate de forma elocuente y responde en frases de máximo 40 palabras.
            - No hables de productos o servicios externos ni inventes información. 
            - Siempre proporciona información nutricional cuando te la pidan.  
            - Si un cliente pregunta por la información nutricional de un platillo y no está en los datos del restaurante, usa tu conocimiento general para responder.  
            - Incluye íconos relacionados al tema al final de cada oración.
            - Si te hablan de ofertas o menus, reponde con los datos de los platillos.
            - Cierra con preguntas de retroalimentación variadas sobre el tema, excepto si el cliente quiere terminar la conversacion despídete cortésmente y no hagas mas preguntas.  
            - Solo procesarás reservas si el usuario proporciona **explícitamente** las palabras "fecha", "hora" y "personas" antes de los valores correspondientes.  
              - Ejemplo correcto: "Quiero hacer una reserva para la fecha 2023-12-01, la hora 19:00 y para 4 personas." ✅  
              - Ejemplo incorrecto: "Quiero hacer una reserva para 2023-12-01 a las 19:00 para 4." ❌  
            - Si falta alguna palabra clave o dato, responde:  
              "❌ Necesito la palabra 'fecha' seguida de la fecha (YYYY-MM-DD), la palabra 'hora' seguida de la hora (HH:MM) y la palabra 'personas' seguida del número de personas (número entero). ¿Podrías proporcionarlos en este formato?"  
            - Si te hablan de pedidos, di que solo puedes hacer reservas.  
            - Responde en el mismo idioma de la pregunta del usuario.
            - Usa esta información para responder:  
                - **Restaurante**: {context['establishment_context']}
                - **Platillos**: {context['dishes_context']}
        """)

    # Asegurar que el mensaje del sistema esté siempre actualizado y en la primera posición
    if history and isinstance(history[0], SystemMessage):
        history[0] = system_message
    else:
        history.insert(0, system_message)

    history.append(HumanMessage(content=question))

    # Detectar intención de reserva
    if detectar_intencion_reserva.invoke(question):
        response = "Entiendo que desea hacer una reserva. ¿Podría proporcionarme más detalles, como la fecha (YYYY-MM-DD), hora (HH:MM) y número de personas?"
    elif "user_data" in state:
        # Procesar datos de reserva
        result = procesar_reserva(state)
        return {
            "response": result["response"],
            "reservation_id": result["reservation_id"],
            "session_id": session_id,
            "question": question,
            "restaurant_id": restaurant_id
        }
    else:
        chain = llm | StrOutputParser()
        response = chain.invoke(history)

    history.append(AIMessage(content=response))

    # Limitar historial
    if len(history) > MAX_HISTORY_LENGTH:
        keep = [system_message] if history[0] == system_message else []
        history[:] = keep + history[-(MAX_HISTORY_LENGTH - len(keep)):]

    return {
        "response": response,
        "session_id": session_id,
        "question": question,
        "restaurant_id": restaurant_id
    }


# ⚙️ Grafo conversacional
graph_builder = StateGraph(dict)
graph_builder.add_node("chat", conversational_node)
graph_builder.set_entry_point("chat")
graph_builder.set_finish_point("chat")
chat_graph = graph_builder.compile()


# 🚀 Endpoint principal
@app.post("/chat")
async def chat_endpoint(user_query: UserQuery):
    state = {
        "session_id": user_query.session_id,
        "question": user_query.question,
        "restaurant_id": user_query.restaurant_id,
        "token": user_query.token
    }

    # Detectar si el usuario está proporcionando datos de reserva
    if "fecha" in user_query.question and "hora" in user_query.question and "personas" in user_query.question:
        try:
            state["user_data"] = {
                "fecha": re.search(r"(\d{4}-\d{2}-\d{2})", user_query.question).group(1),
                "hora": re.search(r"(\d{2}:\d{2})", user_query.question).group(1),
                "personas": re.search(r"(?<=\s)(\d{1,2})(?=\s)", user_query.question).group(1)
            }
        except Exception as e:
            print(e)

    result = chat_graph.invoke(state)

    return {
        "response": get_or_create_history(user_query.session_id)[-1],  # result["response"]
        "reservation_id": result.get("reservation_id"),
    }


@app.get("/restaurants")
async def chat_endpoint():
    restaurants = getRestaurantsContext()
    return {
        "restaurants": restaurants
    }


class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)

        # Forzar el tipo MIME correcto para archivos JS
        if path.endswith(".js"):
            response.headers["Content-Type"] = "application/javascript"
        return response


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/assets", CustomStaticFiles(directory=os.path.join(BASE_DIR, "public/spa/assets")), name="assets")
app.mount("/", CustomStaticFiles(directory=os.path.join(BASE_DIR, "public/spa"), html=True, check_dir=True), name="spa")


# Manejar rutas desconocidas redirigiéndolas al index.html (para SPA)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    index_path = os.path.join("public/spa", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html no encontrado"}


# 🖥️ Ejecutar el servidor
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, proxy_headers=True)
