import os
import logging
import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic_ai import Agent
from dotenv import load_dotenv
from typing import List, Dict
from schemas.schemas import AgentCard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
os.getenv("OPENAI_API_KEY")

# Lista de endereços base dos agentes que o coordenador tentará descobrir
SPECIALIST_AGENT_URLS = [
    "http://localhost:8001", # Agent Analysis
    "http://localhost:8002", # Agent Consult
]

# Esta lista será preenchida dinamicamente na inicialização
AVAILABLE_AGENTS: List[AgentCard] = []

http_client: httpx.AsyncClient | None = None
# O prompt do agente central agora é dinâmico, construído em tempo real
agent = Agent("openai:gpt-4o-mini")
app = FastAPI(title="Agent Central - Dynamic Coordinator")

@app.get("/")
async def health():
    """Mostra o status e os agentes que foram descobertos com sucesso."""
    return {
        "status": "✅ ONLINE",
        "service": "Agent Central Dynamic Coordinator",
        "discovered_agents": [agent.agent_id for agent in AVAILABLE_AGENTS]
    }

@app.post("/sse")
async def a2a_endpoint(request: Request):
    """
    Endpoint que usa um LLM para rotear a tarefa para o melhor agente
    descoberto na rede.
    """
    assert http_client is not None, "HTTP Client não inicializado"
    data = await request.json()
    
    input_data = data.get("input", {})
    message = input_data.get("input", "")

    if not message:
        return JSONResponse(status_code=400, content={"error": "Campo 'message' ou 'input' obrigatório no payload."})

    if not AVAILABLE_AGENTS:
        return JSONResponse(status_code=503, content={"error": "Nenhum agente especialista disponível no momento."})

    # 1. Monta a lista de ferramentas a partir dos cartões descobertos
    tools_description = "\n".join(
        [f"- ID do Agente: '{card.agent_id}', Nome: '{card.name}', Descrição: {card.description}" for card in AVAILABLE_AGENTS]
    )

    # 2. Cria o prompt de roteamento dinâmico para o LLM
    routing_prompt = f"""
    Você é um roteador inteligente de tarefas. Sua função é analisar um pedido do usuário e escolher o melhor especialista de uma lista.

    Pedido do usuário: "{message}"

    Especialistas disponíveis:
    {tools_description}

    Com base no pedido do usuário, qual é o 'ID do Agente' do especialista mais qualificado para esta tarefa? Responda APENAS com o 'ID do Agente' e nada mais.
    Se nenhum especialista for claramente adequado, responda com a palavra 'NONE'.
    """

    # 3. Primeira chamada ao LLM: Decidir qual agente usar
    logger.info("Decidindo rota com LLM...")
    chosen_agent_id = (await agent.run(routing_prompt)).output.strip().replace("'", "")
    logger.info(f"LLM escolheu o agente: {chosen_agent_id}")

    # 4. Encontra o cartão do agente escolhido
    chosen_agent_card = next((card for card in AVAILABLE_AGENTS if card.agent_id == chosen_agent_id), None)

    if chosen_agent_card:
        # 5. Segunda chamada: Invoca o agente especialista escolhido
        logger.info(f"Invocando o endpoint: {chosen_agent_card.invocation_endpoint}")
        try:
            # O endpoint do especialista espera um payload simples com "message"
            specialist_payload = {"message": message}
            response = await http_client.post(chosen_agent_card.invocation_endpoint, json=specialist_payload, timeout=45)
            response.raise_for_status()
            specialist_response = response.json()
            
            # Combina a resposta do especialista com o nome do agente usado
            final_response = f"{specialist_response.get('response', 'O agente especialista não retornou uma resposta.')}\n\n---\n*Agente utilizado: {chosen_agent_card.name}*"
            return {"output": {"output": final_response}}
            
        except Exception as e:
            logger.error(f"Erro ao contatar o agente {chosen_agent_card.name}: {e}")
            error_response = f"Desculpe, houve um erro ao tentar contatar o {chosen_agent_card.name}."
            return {"output": {"output": error_response}}
    else:
        # Nenhum especialista foi escolhido, o coordenador responde diretamente
        logger.info("Nenhum especialista adequado. Respondendo diretamente.")
        response_text = (await agent.run(f"O usuário disse: '{message}'. Responda que você é um coordenador de agentes de CEP, mas não encontrou um especialista para esta tarefa específica no momento. Peça para o usuário ser mais específico.")).output
        
        # Combina a resposta com o nome do agente usado
        final_response = f"{response_text}\n\n---\n*Agente utilizado: Agent Central (GPT)*"
        return {"output": {"output": final_response}}

@app.on_event("startup")
async def startup_event():
    """Na inicialização, descobre os agentes disponíveis lendo seus cartões."""
    global http_client, AVAILABLE_AGENTS
    http_client = httpx.AsyncClient()
    
    print("\n🚀 Iniciando Coordenador Dinâmico...")
    print("🔍 Descobrindo agentes especialistas na rede...")

    for url in SPECIALIST_AGENT_URLS:
        try:
            response = await http_client.get(f"{url}/card", timeout=5)
            if response.status_code == 200:
                card = AgentCard(**response.json())
                AVAILABLE_AGENTS.append(card)
                print(f"✅ Agente '{card.name}' descoberto em {url}")
            else:
                print(f"⚠️ Resposta inesperada de {url}/card: {response.status_code}")
        except Exception as e:
            print(f"❌ Falha ao descobrir agente em {url}: {e}")
    
    print(f"✨ Descoberta concluída. {len(AVAILABLE_AGENTS)} agentes disponíveis.")

@app.on_event("shutdown")
async def shutdown_event():
    if http_client:
        await http_client.aclose()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
