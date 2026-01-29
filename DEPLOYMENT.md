# Guia de Deploy - JACN AI Portal

Este documento fornece instruções detalhadas sobre como realizar o deploy do JACN AI Portal em diferentes ambientes.

## 🚀 Deploy com Docker Compose (Recomendado)

Esta é a forma mais fácil e robusta de rodar o projeto, pois isola as dependências e configura a comunicação entre o frontend e o backend automaticamente.

### Pré-requisitos
- Docker instalado ([Instalação](https://docs.docker.com/get-docker/))
- Docker Compose instalado

### Passo a Passo

1. **Configurar Variáveis de Ambiente:**
   Certifique-se de que o arquivo `.env` na raiz do projeto contenha suas chaves de API:
   ```env
   OPENAI_API_KEY=sua_chave
   GROQ_API_KEY=sua_chave
   JWT_SECRET=seu_segredo_jwt
   ```

2. **Subir os Serviços:**
   No diretório raiz do projeto, execute:
   ```bash
   docker-compose up --build -d
   ```

3. **Acessar o Portal:**
   - **Frontend:** [http://localhost:8501](http://localhost:8501)
   - **Documentação da API (Backend):** [http://localhost:8000/docs](http://localhost:8000/docs)

### 💾 Persistência de Dados
O `docker-compose.yml` está configurado para persistir:
- **Banco de Dados:** O arquivo `app_v2.db` é mapeado do seu computador para o contêiner.
- **Uploads:** A pasta `data/` é mapeada para garantir que arquivos enviados ao RAG Hub não sejam perdidos.

---

## ☁️ Deploy em Produção (VPS / Nuvem)

Para colocar o portal na internet, você precisará de uma VPS (como DigitalOcean, AWS EC2, Google Cloud) com Linux (Ubuntu recomendado).

1. **Instalar Docker na VPS.**
2. **Clonar seu repositório.**
3. **Configurar o `.env` na VPS.**
4. **Executar o Docker Compose.**
5. **Configurar DNS e Certificado SSL:**
   Recomendamos usar o **Nginx** ou **Traefik** como proxy reverso para fornecer HTTPS (porta 443) e apontar para a porta 8501 (Frontend).

---

## 🛠️ Solução de Problemas

- **Erro de conexão com o banco:** Verifique se o arquivo `app_v2.db` tem permissões de leitura e escrita.
- **Frontend não fala com o Backend:** No `docker-compose.yml`, o frontend usa `API_URL=http://backend:8000`. Não altere o nome do serviço `backend` a menos que saiba o que está fazendo.
- **Memória:** Processamento de RAG (vetorização) pode consumir memória. Recomenda-se pelo menos 2GB de RAM na VPS.
