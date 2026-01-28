# Documentação de Arquitetura - JACN AI Portal

Este documento detalha a estrutura interna do projeto, os padrões de design adotados e a interação entre os componentes.

## 1. Organização do Projeto

A estrutura de diretórios segue uma modularização clara entre responsabilidades:

```text
Streamlit_LLM/
├── api/                # Endpoints FastAPI (Routers)
├── components/         # Componentes de UI Streamlit
├── core/               # Configurações centrais, segurança e utilitários
├── db/                 # Modelos SQLAlchemy e conexão com banco
├── service/            # Camada de lógica de negócio e integração com APIs externas
├── jacn_ai_portal.py   # Ponto de entrada do Frontend
└── main.py             # Ponto de entrada do Backend
```

## 2. Camada de Backend (FastAPI)

O backend é construído com FastAPI, utilizando roteamento modular para facilitar a manutenção.

### Routers Principais:
- **`auth_API.py`**: Gerencia login, registro e validação de tokens JWT.
- **`rag_router_API.py`**: Endpoints para upload de documentos, busca semântica, perguntas e histórico de chat (RAG).
- **`prompt_router_API.py`**: Endpoints para interação direta com LLMs (Prompt Hub).

### Camada de Serviço (`service/`):
Atua como um intermediário entre os roteadores e os recursos externos/banco de dados.
- **`auth_service.py`**: Lógica de hashing de senha, geração de JWT e controle de tenants.
- **`rag_chain_service.py`**: Orquestra a cadeia LangChain para processamento RAG.
- **`search_service.py`**: Gerencia a criação e carga dos índices FAISS.
- **`portal_service.py`**: Classe utilitária utilizada pelo frontend para abstrair as chamadas HTTP para a API.

## 3. Camada de Frontend (Streamlit)

O frontend utiliza o Streamlit com uma abordagem baseada em componentes para escalabilidade.

- **`jacn_ai_portal.py`**: Gerencia o estado da sessão, navegação lateral e roteamento de páginas.
- **Componentes (`components/`)**:
    - `auth.py`: Telas de login e logout.
    - `dashboard.py`: Visualizações de métricas e analytics.
    - `rag_hub.py`: Interface de upload e chat com documentos.
    - `prompt_hub.py`: Interface de geração de conteúdo IA.
    - `history.py`: Visualização e exportação do histórico de interações.

## 4. Banco de Dados e Segurança

### Schema (SQLAlchemy):
- **User**: Informações de credenciais, papel (admin/member) e vínculo com tenant.
- **Tenant**: Dados da organização, limites de documentos/usuários e nível de assinatura.
- **ChatMessage**: Log de interações, incluindo fontes RAG e feedback do usuário.
- **PromptHistory**: Histórico específico do Prompt Hub.

### Modelo de Isolamento:
O isolamento de dados é garantido em três níveis:
1. **Banco de Dados**: Filtragem obrigatória por `tenant_id` em todas as queries.
2. **Sistema de Arquivos**: Documentos são salvos em `data/uploads/{tenant_id}_{slug}/{username}/`.
3. **Índice Vetorial**: Cada usuário possui seu próprio índice FAISS gerado dinamicamente a partir de seus arquivos.

## 5. Fluxo de Dados (RAG)

1. Usuário faz upload de um PDF.
2. Backend extrai o texto, realiza OCR se necessário.
3. Texto é dividido em chunks e convertido em embeddings (vetores).
4. Vetores são armazenados localmente via FAISS no diretório do usuário.
5. Ao perguntar, o sistema busca os chunks mais similares, injeta-os no contexto de um prompt e solicita a resposta à LLM.
