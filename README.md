**FALTA IMPLEMEMTAR: MEMORIA NO CHAT**


🤖 Sociedade de Agentes A2A para Consultas de CEP
Este projeto implementa uma arquitetura de múltiplos agentes (A2A - Agent-to-Agent) para criar um sistema inteligente e escalável de consulta e análise de CEPs brasileiros. A principal característica é a utilização de um padrão de descoberta dinâmica de serviços através de "Agent Cards", permitindo que um agente coordenador central descubra e delegue tarefas para agentes especialistas de forma inteligente.

🏛️ Arquitetura: Uma Sociedade de Agentes Dinâmica
Em vez de uma abordagem monolítica, o sistema é dividido em microsserviços, onde cada agente é um serviço independente com uma responsabilidade única.

A arquitetura é composta por 4 camadas:

Camada de Apresentação (app.py): Uma interface web construída com Streamlit que serve como o ponto de entrada para as interações do usuário.

Camada de Coordenação (agent_central_a2a.py): O cérebro do sistema. Este agente não executa tarefas diretamente. Sua função é receber o pedido do usuário, usar seu LLM para interpretar a intenção e, com base nos "Agent Cards" descobertos, rotear a tarefa para o especialista mais adequado.

Camada de Especialistas (agent_consult.py e agent_analysis.py): Agentes inteligentes focados em tarefas específicas. Cada um oferece um "Agent Card" (GET /card) descrevendo suas capacidades, permitindo que sejam descobertos dinamicamente pelo Coordenador.

Camada de Ferramentas (mcp_server.py): Um servidor de ferramentas base que oferece serviços não inteligentes, como a consulta a uma API externa (ViaCEP). Ele serve como a "caixa de ferramentas" para os agentes especialistas.

✨ Principais Funcionalidades
Descoberta Dinâmica de Agentes: O Coordenador descobre automaticamente quais especialistas estão disponíveis na rede lendo seus "Agent Cards" na inicialização.

Roteamento Inteligente baseado em LLM: A decisão de qual especialista usar para uma tarefa é feita por um LLM, tornando o sistema flexível a diferentes tipos de pedidos do usuário.

Escalabilidade: Novos agentes especialistas podem ser adicionados à rede sem a necessidade de alterar o código do Coordenador.

Arquitetura de Microsserviços: Cada componente é um servidor FastAPI independente, facilitando a manutenção e o desenvolvimento.

🚀 Tecnologias Utilizadas
Python 3.12+

Pydantic-AI: Framework principal para a criação dos agentes.

FastAPI: Para construir as APIs de cada agente e servidor.

Streamlit: Para a criação da interface web interativa.

Uvicorn: Como servidor ASGI para rodar as aplicações FastAPI.

HTTPX: Para a comunicação HTTP assíncrona entre os agentes.

python-dotenv: Para gerenciamento de variáveis de ambiente e segredos (API Keys).

⚙️ Configuração e Instalação
Siga os passos abaixo para configurar e executar o projeto localmente.

1. Pré-requisitos
Python 3.12 ou superior

Git

2. Passos de Instalação
a. Clone o Repositório

git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio

b. Crie e Ative um Ambiente Virtual

# Para Unix/macOS
python3 -m venv .venv
source .venv/bin/activate

# Para Windows
python -m venv .venv
.\.venv\Scripts\activate

c. Instale as Dependências
O projeto usa o requirements.txt para gerenciar as dependências.

pip install -r requirements.txt

d. Configure suas Credenciais
Este projeto precisa de uma chave de API da OpenAI.

Crie uma cópia do arquivo de exemplo .env.example.

cp .env.example .env

Abra o novo arquivo .env e insira sua chave da OpenAI.

OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

IMPORTANTE: O arquivo .env está listado no .gitignore e nunca deve ser enviado para o repositório.

▶️ Como Executar o Sistema
Para que a "sociedade de agentes" funcione, todos os servidores precisam estar rodando ao mesmo tempo. Você precisará abrir 5 terminais separados e executar os seguintes comandos, um em cada terminal, na ordem indicada.

1. Terminal 1: Servidor de Ferramentas

python mcp_server.py

2. Terminal 2: Agente de Consulta

python agent_consult.py

3. Terminal 3: Agente de Análise

python agent_analysis.py

4. Terminal 4: Agente Coordenador Central
(Observe o log deste terminal. Ele mostrará o processo de descoberta dos outros agentes).

python agent_central_a2a.py

5. Terminal 5: Interface do Usuário
(Após iniciar, este comando abrirá uma nova aba no seu navegador).

streamlit run app.py

Agora você pode interagir com o sistema através da interface web!

Exemplos de Teste
Para testar o Agente de Consulta: Consulte o CEP 01001-000

Para testar o Agente de Análise: Faça uma análise detalhada do endereço do CEP 04538-132

Para testar o Agente Central: Olá, o que você faz?