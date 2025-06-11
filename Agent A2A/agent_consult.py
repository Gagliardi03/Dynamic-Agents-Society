import os
import re
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic_ai import Agent
import uvicorn
from schemas.schemas import AgentCard

load_dotenv()
os.getenv("OPENAI_API_KEY")

AGENT_CARD_CONSULT = AgentCard(
    agent_id="consult_specialist_v1",
    name="Agente de Consulta de CEP",
    description="Especialista em realizar consultas rápidas e básicas de CEP, retornando logradouro, bairro, cidade e estado. Ideal para quando o usuário pede para 'consultar' ou 'verificar' um CEP.",
    version="1.0.0",
    invocation_endpoint="http://localhost:8002/sse",
)

http_client: httpx.AsyncClient | None = None
# O prompt do agente pode ser simplificado, pois a lógica de quando usá-lo está no seu cartão.
agent = Agent(
    "openai:gpt-4o-mini",
    instructions="""📜 Você é um assistente especialista em CONSULTAS BÁSICAS de CEP. 
              Sua tarefa é receber dados de CEP já consultados e formatá-los de maneira clara e útil para o usuário.""",
)
app = FastAPI(title=AGENT_CARD_CONSULT.name)


async def chamar_mcp_consultar_cep(cep: str) -> str:
    """Chama ferramenta de consulta no MCP Server."""
    assert http_client is not None, "HTTP Client não inicializado"
    try:
        response = await http_client.post(
            "http://localhost:8000/mcp/consultar_cep", json={"cep": cep}, timeout=15
        )
        response.raise_for_status()
        data: dict = response.json()
        return data.get("output", "Erro na resposta do MCP")
    except Exception as e:
        return f"❌ Erro ao chamar MCP: {str(e)}"


@app.get("/card", response_model=AgentCard)
async def get_agent_card_CONSULT():
    """Retorna o cartão de visita deste agente."""
    return AGENT_CARD_CONSULT


@app.get("/")
async def health():
    """Retorna um health check simples."""
    return {
        "status": "✅ ONLINE",
        "service": AGENT_CARD_CONSULT.name,
        "id": AGENT_CARD_CONSULT.agent_id,
    }


@app.post("/sse")
async def a2a_endpoint(request: Request):
    """Endpoint principal de invocação do agente."""
    data = await request.json()
    message = data.get("message", "")
    cep_match = re.search(r"\b\d{5}-?\d{3}\b", message)
    if cep_match:
        cep = cep_match.group()
        resultado_mcp = await chamar_mcp_consultar_cep(cep)
        if "❌" in resultado_mcp:
            return {"success": False, "response": resultado_mcp}
        prompt_formatacao = (
            f"Formate esta resposta de CEP de forma clara e útil: {resultado_mcp}"
        )
        result_agent = await agent.run(prompt_formatacao)
        return {"success": True, "response": result_agent.output}
    else:
        # Se chamado sem CEP, ele se apresenta.
        result = await agent.run(
            f"O usuário disse: '{message}'. Responda que você é um especialista em consultas de CEP e peça um CEP."
        )
        return {"success": True, "response": result.output}


@app.on_event("startup")
async def startup_event():
    global http_client
    http_client = httpx.AsyncClient(timeout=20.0)
    print(f"\n🚀 {AGENT_CARD_CONSULT.name} FUNCIONANDO INICIADO! (porta 8002)")


@app.on_event("shutdown")
async def shutdown_event():
    if http_client:
        await http_client.aclose()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
