import os
import httpx
import uvicorn
import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic_ai import Agent

# ✅ Configuração
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise RuntimeError("❌ ERRO: OPENAI_API_KEY não encontrada!")
print(f"✅ OpenAI API Key: {openai_key[:10]}...")

# ✅ Cliente HTTP e Agente IA
http_client: httpx.AsyncClient | None = None
server_agent = Agent(
    "openai:gpt-4o-mini",
    instructions="""🏠 Assistente Especialista em Endereços Brasileiros. Analise informações de CEP, identifique características da região e forneça insights úteis. Use emojis e seja conciso.""",
)

app = FastAPI(
    title="MCP Server - CEP Tools",
    description="Servidor com ferramentas de CEP funcionando via FastAPI",
    version="1.0.0",
)


# ✅ FUNÇÃO 1: CONSULTAR CEP
async def consultar_cep_funcao(cep: str) -> str:
    """🔍 Consulta CEP via ViaCEP"""
    print(f"🔍 [MCP] Consultando CEP: {cep}")
    cep_limpo = "".join(filter(str.isdigit, cep))
    if len(cep_limpo) != 8:
        return f"❌ CEP inválido: '{cep}'. Use formato: 01310-100"

    try:
        global http_client
        if http_client is None:
            http_client = httpx.AsyncClient(timeout=10.0)
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        response = await http_client.get(url)
        response.raise_for_status()
        dados = response.json()

        if dados.get("erro"):
            return f"❌ CEP {cep_limpo} não encontrado"

        resultado = f"""📍 **CEP Encontrado: {dados.get('cep', cep_limpo)}**
🛣️ **Logradouro:** {dados.get('logradouro') or '⚠️ Não informado'}
🏘️ **Bairro:** {dados.get('bairro') or '⚠️ Não informado'}
🏙️ **Cidade:** {dados.get('localidade') or '⚠️ Não informado'}
🗺️ **Estado:** {dados.get('uf') or '⚠️ Não informado'}
📮 **DDD:** {dados.get('ddd') or '⚠️ Não informado'}
✅ **Consulta realizada via ViaCEP**"""
        print(f"✅ [MCP] CEP encontrado: {dados.get('localidade')}/{dados.get('uf')}")
        return resultado

    except Exception as e:
        return f"❌ Erro na consulta: {str(e)}"


# ✅ FUNÇÃO 2: ANALISAR ENDEREÇO
async def analisar_endereco_funcao(cep: str) -> str:
    """🧠 Análise completa do endereço"""
    print(f"🧠 [MCP] Analisando CEP: {cep}")
    dados_cep = await consultar_cep_funcao(cep)
    if "❌" in dados_cep:
        return f"🧠 **Análise de Endereço**\n\n⚠️ Não foi possível analisar pois a consulta básica falhou:\n\n{dados_cep}"

    try:
        prompt = f"""Analise as informações de endereço brasileiro: {dados_cep}. Forneça uma análise que inclua: Tipo de região, Características da área, Contexto geográfico e Informações úteis. Use emojis e seja conciso."""
        resultado_ia = await server_agent.run(prompt)
        resposta_final = f"""🧠 **Análise Completa de Endereço**
        📊 **DADOS BÁSICOS**
        {dados_cep}
        🤖 **ANÁLISE INTELIGENTE** 
        {resultado_ia.output}"""
        print("✅ [MCP] Análise completa finalizada")
        return resposta_final

    except Exception as e:
        return f"🧠 **Análise de Endereço**\n\n✅ **Dados básicos:**\n{dados_cep}\n\n❌ **Erro na análise IA:** {str(e)}"


@app.post("/mcp/consultar_cep")
async def mcp_consultar_cep(request: Request):
    data = await request.json()
    cep = data.get("cep", "")
    resultado = await consultar_cep_funcao(cep)
    return {
        "success": "❌" not in resultado,
        "tool": "mcp:consultar_cep",
        "input": cep,
        "output": resultado,
    }


@app.post("/mcp/analisar_endereco")
async def mcp_analisar_endereco(request: Request):
    data = await request.json()
    cep = data.get("cep", "")
    resultado = await analisar_endereco_funcao(cep)
    return {
        "success": "❌" not in resultado,
        "tool": "mcp:analisar_endereco",
        "input": cep,
        "output": resultado,
    }


# ✅ EVENTOS DE STARTUP E SHUTDOWN
@app.on_event("startup")
async def startup_event():
    global http_client
    http_client = httpx.AsyncClient(timeout=10.0)
    print(
        "\n"
        + "=" * 60
        + "\n🚀 MCP SERVER FUNCIONANDO INICIADO! (porta 8000)\n"
        + "=" * 60
    )


@app.on_event("shutdown")
async def shutdown_event():
    if http_client:
        await http_client.aclose()
        print("\n⏹️ Cliente HTTP do MCP Server fechado.")


# ✅ MAIN
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
