import os
import re
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph
from typing import Dict, Optional

from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from models import llm  # Tu modelo CloudflareWorkersAI
from context import getRestaurantContext, getRestaurantDishesContext
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


def get_or_create_history(session_id: str) -> list:
    if session_id not in session_store:
        session_store[session_id] = []
    return session_store[session_id]


# 📦 Modelo para la solicitud
class UserQuery(BaseModel):
    session_id: str
    question: str
    restaurant_id: Optional[int] = 7  # ← valor por defecto


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


def validar_datos_reserva(data: dict) -> Optional[str]:
    """Valida los datos de reserva y devuelve un mensaje de error si algo falla."""
    fecha = data.get("fecha")
    hora = data.get("hora")
    personas = data.get("personas")

    if not fecha or not re.match(r"\d{4}-\d{2}-\d{2}", fecha):  # Formato YYYY-MM-DD
        return "La fecha no es válida. Usa el formato YYYY-MM-DD."
    if not hora or not re.match(r"\d{2}:\d{2}", hora):  # Formato HH:MM
        return "La hora no es válida. Usa el formato HH:MM."
    if not personas or not personas.isdigit() or int(personas) <= 0:
        return "El número de personas debe ser un número positivo."

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
        response = (
            f"¡Tu reserva ha sido confirmada! ✅ Aquí está tu ID de reserva: {reservation_id}. "
            "¿Necesitas ayuda con algo más? 🌟"
        )

    history.append(AIMessage(content=response))
    return {"response": response, "reservation_id": reservation_id}


def conversational_node(state: dict) -> dict:
    session_id = state["session_id"]
    question = state["question"]
    restaurant_id = state["restaurant_id"]
    history = get_or_create_history(session_id)

    # Obtener contexto del restaurante dinámicamente
    restaurant_context = getRestaurantContext(restaurant_id)
    dishes_context = getRestaurantDishesContext(restaurant_id)

    # Mensaje del sistema con contexto actualizado
    system_message = SystemMessage(content=f"""
        Eres un mesero en un restaurante elegante, atendiendo con cortesía y profesionalismo. Tu objetivo es ayudar con el menú, tomar pedidos y responder preguntas con precisión. Sigue estas reglas:  

        - Preséntate de forma elocuente y responde en frases de máximo 30 palabras.  
        - No hables de productos o servicios externos ni inventes información.  
        - Siempre proporciona información nutricional cuando te la pidan.  
        - Si un cliente pregunta por la información nutricional de un platillo y no está en los datos del restaurante, usa tu conocimiento general para responder.  
        - Incluye íconos relacionados al tema al final de cada oración.  
        - Si el cliente quiere terminar, despídete cortésmente; de lo contrario, cierra con una pregunta de retroalimentación.  
        - Solo procesarás reservas si el usuario proporciona **fecha (YYYY-MM-DD), hora (HH:MM) y número de personas (número entero)**. Si falta un dato, responde:  
          "❌ Necesito la fecha, hora y número de personas para procesar tu reserva. ¿Podrías proporcionarlos en este formato: **fecha (YYYY-MM-DD), hora (HH:MM) y número de personas (número entero)**?"  
        - Usa esta información para responder:  
          - **Restaurante**: {restaurant_context}  
          - **Platillos**: {dishes_context}  
    """)

    if not history:
        history.append(system_message)

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
        "restaurant_id": user_query.restaurant_id
    }

    # Detectar si el usuario está proporcionando datos de reserva
    if "fecha" in user_query.question and "hora" in user_query.question and "personas" in user_query.question:
        state["user_data"] = {
            "fecha": re.search(r"(\d{4}-\d{2}-\d{2})", user_query.question).group(1),
            "hora": re.search(r"(\d{2}:\d{2})", user_query.question).group(1),
            "personas": re.search(r"(\d+)", user_query.question).group(1)
        }

    result = chat_graph.invoke(state)

    return {"response": result["response"], "reservation_id": result.get("reservation_id")}


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
