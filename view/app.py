# app.py (Ajustado para conversar com a arquitetura Pydantic A2A)
import streamlit as st
import httpx
from datetime import datetime

# O endpoint padrão do .to_a2a() pode ser diferente. Verifique em http://localhost:8004/docs
AGENT_URL = "http://localhost:8004/sse" 
TIMEOUT = 45

st.set_page_config(page_title="🤖 Chatbot A2A", page_icon="💬", layout="centered")

async def enviar_mensagem(mensagem: str, historico: list) -> dict:
    try:
        # O payload do .to_a2a() é mais complexo
        payload = {
            "input": {
                "input": mensagem,
                "chat_history": [
                    {"role": "user" if msg["tipo"] == "usuario" else "assistant", "content": msg["conteudo"]}
                    for msg in historico
                ]
            }
        }
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(AGENT_URL, json=payload)
        
        if response.status_code == 200:
            # A resposta também vem em uma estrutura diferente
            return {"sucesso": True, "resposta": response.json().get("output", {}).get("output", "Sem resposta")}
        else:
            return {"sucesso": False, "erro": f"Erro HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"sucesso": False, "erro": f"🐛 Erro inesperado: {str(e)}"}

async def main():
    st.title("🤖 Chatbot A2A - Pydantic Native")
    st.info(f"🔗 Conectado ao endpoint: {AGENT_URL}")

    if "historico" not in st.session_state:
        st.session_state.historico = []

    with st.form("chat_form", clear_on_submit=True):
        mensagem_usuario = st.text_input("💬 Sua mensagem:", placeholder="Ex: Analise o CEP 13571-385")
        enviado = st.form_submit_button("📤 Enviar", type="primary")

    if enviado and mensagem_usuario.strip():
        st.session_state.historico.append({"tipo": "usuario", "conteudo": mensagem_usuario})
        
        with st.spinner("🤖 Coordenador A2A processando..."):
            resultado = await enviar_mensagem(mensagem_usuario, st.session_state.historico)
            
            if resultado["sucesso"]:
                st.session_state.historico.append({"tipo": "agent", "conteudo": resultado["resposta"]})
            else:
                 st.session_state.historico.append({"tipo": "erro", "conteudo": resultado["erro"]})
        st.rerun()

    for msg in st.session_state.historico:
        avatar = "👤" if msg["tipo"] == "usuario" else "🤖" if msg["tipo"] == "agent" else "❌"
        with st.chat_message(msg["tipo"], avatar=avatar):
            st.markdown(msg["conteudo"])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())