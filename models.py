#from langchain_community.llms.cloudflare_workersai import CloudflareWorkersAI
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
dev = os.getenv("DEVELOPMENT")

if dev == 'true':
    # Configuración de proxy si es necesario
    os.environ['HTTP_PROXY'] = 'http://localhost:5000'
    os.environ['HTTPS_PROXY'] = 'http://localhost:5000'

#llm = CloudflareWorkersAI(
#account_id="a51174406b2caffc701c2099f894d92e",
#api_token="Yicz1t75aNEkg2ZoGhKe3ZxP5TXZYpHosoZPdqnI",
#model="@cf/meta/llama-3.3-70b-instruct-fp8-fast",
#)


llm = ChatOpenAI(
    api_key=api_key,
    model="gpt-4o-mini",
    temperature=0,
    top_p=0.9,
)
