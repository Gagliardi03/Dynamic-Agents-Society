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

AGENT_CARD_ANALYSIS = AgentCard(
    agent_id="analysis_specialist_v1",
    name="Agente de Análise de Endereço",
    description="Especialista em realizar análises detalhadas de endereços a partir de um CEP. Fornece insights sobre o tipo de região, características da área e contexto geográfico. Ideal para quando o usuário pede para 'analisar' ou 'detalhar' um endereço.",
    version="1.0.0",
    invocation_endpoint="http://localhost:8001/sse",
)

http_client: httpx.AsyncClient | None = None
agent = Agent(
    "openai:gpt-4o-mini",
    instructions="""📜 Você é um assistente especialista em ANÁLISE DETALHADA de CEP. 
              Sua tarefa é receber uma análise do MCP Server e complementá-la com insights sobre desenvolvimento, tendências e oportunidades.""",
)
app = FastAPI(title=AGENT_CARD_ANALYSIS.name)


async def chamar_mcp_analisar_endereco(cep: str) -> str:
    """Chama ferramenta de análise no MCP Server."""
    assert http_client is not None, "HTTP Client não inicializado"
    try:
        response = await http_client.post(
            "http://localhost:8000/mcp/analisar_endereco", json={"cep": cep}, timeout=30
        )
        response.raise_for_status()
        data: dict = response.json()
        return data.get("output", "Erro na resposta do MCP")
    except Exception as e:
        return f"❌ Erro ao chamar MCP: {str(e)}"


@app.get("/card", response_model=AgentCard)
async def get_agent_card_ANALYSIS():
    """Retorna o cartão de visita deste agente."""
    return AGENT_CARD_ANALYSIS


@app.get("/")
async def health():
    """Retorna um health check simples."""
    return {
        "status": "✅ ONLINE",
        "service": AGENT_CARD_ANALYSIS.name,
        "id": AGENT_CARD_ANALYSIS.agent_id,
    }


@app.post("/sse")
async def a2a_endpoint(request: Request):
    """Endpoint principal de invocação do agente."""
    data = await request.json()
    message = data.get("message", "")
    cep_match = re.search(r"\b\d{5}-?\d{3}\b", message)
    if cep_match:
        cep = cep_match.group()
        resultado_mcp = await chamar_mcp_analisar_endereco(cep)
        if "❌" in resultado_mcp:
            return {"success": False, "response": resultado_mcp}
        prompt_complemento = (
            f"Como especialista, complemente esta análise de CEP: {resultado_mcp}."
        )
        result_agent = await agent.run(prompt_complemento)
        return {
            "success": True,
            "response": f"🧠 **ANÁLISE ADICIONAL**\n\n{result_agent.output}",
        }
    else:
        result = await agent.run(
            f"O usuário disse: '{message}'. Responda que você é um especialista em análises detalhadas e peça um CEP."
        )
        return {"success": True, "response": result.output}


@app.on_event("startup")
async def startup_event():
    global http_client
    http_client = httpx.AsyncClient(timeout=45.0)
    print(f"\n🚀 {AGENT_CARD_ANALYSIS.name} FUNCIONANDO INICIADO! (porta 8001)")


@app.on_event("shutdown")
async def shutdown_event():
    if http_client:
        await http_client.aclose()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
