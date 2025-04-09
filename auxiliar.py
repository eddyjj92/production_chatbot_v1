from langchain_core.prompts import PromptTemplate
from models import llm
import json
import re

def obtener_claves_relevantes(estructura, pregunta):
    # Crear el prompt
    prompt = """
    Tienes la siguiente estructura de un objeto que describe un restaurante:
    {estructura}
    El usuario ha hecho la siguiente pregunta:
    Pregunta: "{pregunta}"
    Tu tarea es decidir cuáles son las claves más relevantes de esta estructura que ayudarán a responder la pregunta. Devuelve una lista json (por ejemplo: ["name", "description", "schedule"]). No devuelvas detalles sobre los valores, solo las claves.
    """
    # Crear el prompt con la pregunta y la estructura
    formatted_prompt = prompt.format(estructura=get_structure(estructura), pregunta=pregunta)

    # Llamar al modelo LLM
    response = llm.invoke(formatted_prompt)
    print(response.content)
    # Limpieza común: eliminar Markdown, espacios y saltos de línea
    cleaned = re.sub(r"^```(?:json)?|```$", "", response.content.strip(), flags=re.IGNORECASE).strip()
    print(cleaned)
    try:
        claves_relevantes = json.loads(cleaned)
        if not isinstance(claves_relevantes, list):
            print("⚠️ La respuesta no es una lista:", type(claves_relevantes))
            claves_relevantes = []
    except (json.JSONDecodeError, TypeError) as e:
        print("❌ Error al parsear la respuesta del modelo:", e)
        claves_relevantes = []

    return claves_relevantes


def get_structure(data):
    if isinstance(data, dict):
        return {k: get_structure(v) for k, v in data.items()}
    elif isinstance(data, list):
        if len(data) > 0:
            return [get_structure(data[0])]
        else:
            return ["unknown"]  # Lista vacía, no se puede inferir tipo
    else:
        return type(data).__name__