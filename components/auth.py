import streamlit as st
import time

def login_page(service):
    # Injeta classe para o body do login via JS (hack necessário no Streamlit)
    st.markdown("""
    <script>
        var body = window.parent.document.querySelector(".stApp");
        if (body) {
            body.classList.add("login-page");
        }
    </script>
    <style>
        /* Estilo local para o fundo do login quando a classe está ativa */
        .login-page {
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    
    with col:
        st.write("") # Espaçador
        st.write("") 
        
        tab_login, tab_signup = st.tabs(["Entrar", "Criar Organização"])
        
        with tab_login:
            with st.form("login_form"):
                st.markdown("""
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <h1 style="color: #0f172a; font-size: 2.5rem; margin-bottom: 0.5rem;">🛡️ JACN AI</h1>
                        <p style="color: #64748b;">Central de Inteligência Avançada</p>
                    </div>
                """, unsafe_allow_html=True)
                
                u = st.text_input("Usuário", placeholder="Seu nome de usuário")
                p = st.text_input("Senha", type="password", placeholder="Sua senha")
                submitted = st.form_submit_button("Acessar Sistema →", use_container_width=True)
                
                if submitted:
                    success, message = service.login(u, p)
                    if success:
                        st.success(message)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)

        with tab_signup:
            with st.form("signup_form"):
                st.markdown("""
                    <div style="text-align: center; margin-bottom: 1rem;">
                        <h2 style="color: #0f172a;">🚀 Começar como SaaS</h2>
                        <p style="color: #64748b;">Crie sua conta e sua organização.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                new_u = st.text_input("Usuário Admin", placeholder="Ex: admin_empresa")
                new_p = st.text_input("Senha", type="password")
                org_name = st.text_input("Nome da Empresa / Org", placeholder="Ex: Minha Empresa LTDA")
                
                signup_submitted = st.form_submit_button("Criar Minha Conta SaaS →", use_container_width=True)
                
                if signup_submitted:
                    if not new_u or not new_p or not org_name:
                        st.warning("Preencha todos os campos.")
                    else:
                        success, message = service.register_tenant(new_u, new_p, org_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

def logout():
    # Remove a classe do login page caso ela tenha sido adicionada
    st.markdown("""
    <script>
        var body = window.parent.document.querySelector(".stApp");
        if (body) {
            body.classList.remove("login-page");
        }
    </script>
    """, unsafe_allow_html=True)
    st.session_state.token = None
    st.session_state.username = ""
    st.session_state.role = "member"
    st.session_state.tenant_id = None
    st.rerun()
