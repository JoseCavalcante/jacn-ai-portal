import streamlit as st
import requests
import time

class PortalService:
    def __init__(self, api_url):
        self.api_url = api_url

    def get_headers(self):
        token = st.session_state.get("token")
        return {"Authorization": f"Bearer {token}"} if token else {}

    def check_health(self):
        """Verifica se a API está online."""
        try:
            # Endpoint dedicado leve sem autenticação
            res = requests.get(f"{self.api_url}/health", timeout=2)
            return res.status_code == 200
        except:
            return False

    def _safe_request(self, method, endpoint, **kwargs):
        """
        Helper para executar chamadas API com tratamento de erro centralizado.
        """
        try:
            url = f"{self.api_url}{endpoint}"
            headers = self.get_headers()
            if "headers" in kwargs:
                headers.update(kwargs.pop("headers"))
            
            # Timeout padrão de 10s para evitar hangs
            if "timeout" not in kwargs:
                kwargs["timeout"] = 10
                
            res = requests.request(method, url, headers=headers, **kwargs)
            
            # Tratamento global de expiração de token
            if res.status_code == 401:
                # Evita loop infinito se já estiver na página de login
                if endpoint != "/auth/login":
                    st.error("Sessão expirada. Por favor, faça login novamente.")
                    st.session_state.token = None
                    time.sleep(1)
                    st.rerun()
                
            return res
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Erro de conexão: O servidor da API parece estar offline.")
        except requests.exceptions.Timeout:
            st.error("⌛ A requisição demorou muito para responder (Timeout).")
        except Exception as e:
            st.error(f"❌ Erro inesperado: {str(e)}")
        return None

    def login(self, username, password):
        res = self._safe_request("POST", "/auth/login", params={"usuario": username, "senha": password})
        if res and res.status_code == 200:
            data = res.json()
            st.session_state.token = data["token"]
            st.session_state.username = data["user"]["username"]
            st.session_state.role = data["user"]["role"]
            st.session_state.tenant_id = data["user"]["tenant_id"]
            return True, "Acesso autorizado!"
        elif res:
            detail = res.json().get("detail", "Erro desconhecido") if res.status_code != 500 else "Erro interno no servidor"
            return False, f"Falha no login: {detail}"
        return False, "Não foi possível completar o acesso."

    def register_tenant(self, username, password, tenant_name):
        res = self._safe_request("POST", "/auth/register", params={
            "usuario": username, 
            "senha": password,
            "tenant_name": tenant_name
        })
        if res and res.status_code == 200:
            return True, "Organização criada! Agora faça o login."
        elif res:
            return False, f"Erro: {res.json().get('detail')}"
        return False, "Falha na conexão."

    def get_tenant_info(self):
        res = self._safe_request("GET", "/auth/me/tenant", timeout=2)
        if res and res.status_code == 200:
            return res.json()
        return None

    def generate_content(self, tema):
        return self._safe_request("POST", "/prompt/gerar_conteudo", params={"tema": tema})

    def rag_search(self, query, k):
        return self._safe_request("GET", "/rag/search", params={"msg": query, "k": k})

    def rag_ask(self, question, k, threshold):
        payload = {"question": question, "k": k, "score_threshold": threshold}
        return self._safe_request("POST", "/rag/ask_prompt", json=payload)

    def update_rag_feedback(self, message_id, value):
        return self._safe_request("POST", "/rag/feedback", json={"message_id": message_id, "value": value})

    def update_prompt_feedback(self, prompt_id, value):
        return self._safe_request("POST", "/prompt/feedback", json={"prompt_id": prompt_id, "value": value})

    def list_files(self):
        return self._safe_request("GET", "/rag/list_files")

    def upload_file(self, uploaded_file):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        return self._safe_request("POST", "/rag/upload", files=files)

    def delete_file(self, filename):
        return self._safe_request("DELETE", "/rag/delete_file", params={"filename": filename})

    def change_password(self, new_password, user_target=None):
        params = {"nova_senha": new_password}
        if user_target:
            params["usuario_alvo"] = user_target
        return self._safe_request("POST", "/auth/change-password", params=params)

    def register_user(self, username, password):
        return self._safe_request("POST", "/auth/register", params={"usuario": username, "senha": password})

    def get_prompt_history(self):
        return self._safe_request("GET", "/prompt/historico")

    def get_rag_history(self):
        return self._safe_request("GET", "/rag/historico")
