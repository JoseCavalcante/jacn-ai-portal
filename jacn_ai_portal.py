import streamlit as st
import os
from service.portal_service import PortalService
from components.auth import login_page, logout
from components.dashboard import render_dashboard
from components.prompt_hub import render_prompt_hub
from components.rag_hub import render_rag_hub
from components.user_mgmt import render_user_management, render_password_change
from components.history import render_history, render_subscription

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="JACN AI Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração da API
API_URL = "http://127.0.0.1:8000"
service = PortalService(API_URL)

# --- DESIGN SYSTEM ---
def load_css():
    if os.path.exists("premium.css"):
        with open("premium.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --- ESTADO DA SESSÃO ---
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "member"
if "tenant_id" not in st.session_state:
    st.session_state.tenant_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "rag_k" not in st.session_state:
    st.session_state.rag_k = 4
if "rag_threshold" not in st.session_state:
    st.session_state.rag_threshold = 1.1

# --- NAVEGAÇÃO PRINCIPAL ---
def main():
    if not st.session_state.token:
        login_page(service)
    else:
        # Sidebar
        with st.sidebar:
            st.title("🛡️ JACN AI")
            st.write(f"👤 Usuário: **{st.session_state.username}**")
            st.divider()
            
            nav_options = ["Dashboard", "Prompt Hub", "RAG Hub", "Histórico", "Trocar Senha"]
            if st.session_state.role == "admin":
                nav_options.append("Gestão de Usuários")
                nav_options.append("Assinatura")
            
            # Garantir que a página atual ainda é válida nas opções
            if st.session_state.current_page not in nav_options:
                st.session_state.current_page = "Dashboard"
                
            current_index = nav_options.index(st.session_state.current_page)
            new_selection = st.radio("Navegação", nav_options, index=current_index)
            
            if new_selection != st.session_state.current_page:
                st.session_state.current_page = new_selection
                st.rerun()

            st.divider()
            if st.button("Sair do Sistema"):
                logout()
            
            st.caption("JACN AI Portal v3.0")

        # Conteúdo baseado na opção selecionada
        if st.session_state.current_page == "Dashboard":
            render_dashboard(service, logout)
        elif st.session_state.current_page == "Prompt Hub":
            render_prompt_hub(service, logout)
        elif st.session_state.current_page == "RAG Hub":
            render_rag_hub(service)
        elif st.session_state.current_page == "Histórico":
            render_history(service)
        elif st.session_state.current_page == "Trocar Senha":
            render_password_change(service)
        elif st.session_state.current_page == "Gestão de Usuários":
            render_user_management(service)
        elif st.session_state.current_page == "Assinatura":
            render_subscription(service)

if __name__ == "__main__":
    main()
