# schemas.py (VERSÃO CORRIGIDA)
from pydantic import BaseModel

# A importação de HttpUrl não é mais necessária

class AgentCard(BaseModel):
    """
    Define a estrutura padrão para o cartão de visita de um agente,
    descrevendo suas capacidades e como invocá-lo.
    """
    agent_id: str
    name: str
    description: str
    version: str
    invocation_endpoint: str