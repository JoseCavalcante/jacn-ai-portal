import streamlit as st
import time

def render_user_management(service):
    st.markdown("""
    <div class="stHeader">
        <h1>👥 Gestão de Usuários</h1>
        <p>Painel Administrativo: Cadastro e Segurança de Colaboradores.</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_reg, tab_pass = st.tabs(["👤 Novo Cadastro", "🔐 Resetar Senha"])
    
    with tab_reg:
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("""
            <div class="saas-card" style="margin-top: 1rem;">
                <h3 style="margin-bottom: 1.5rem;">👤 Novo Cadastro</h3>
            """, unsafe_allow_html=True)
            with st.form("admin_register_form", clear_on_submit=True):
                u_reg = st.text_input("Nome de Usuário", placeholder="Ex: joao_silva")
                p_reg = st.text_input("Senha", type="password", placeholder="Senha temporária")
                p_conf = st.text_input("Confirmar Senha", type="password", placeholder="Repita a senha")
                reg_submitted = st.form_submit_button("Cadastrar Usuário 👤", use_container_width=True)
                
                if reg_submitted:
                    if not u_reg or not p_reg:
                        st.warning("Preencha todos os campos obrigatórios.")
                    elif p_reg != p_conf:
                        st.error("As senhas informadas não conferem.")
                    else:
                        res_reg = service.register_user(u_reg, p_reg)
                        if res_reg and res_reg.status_code == 200:
                            st.success(f"Usuário **{u_reg}** cadastrado com sucesso!")
                            st.balloons()
                        elif res_reg:
                            detail = res_reg.json().get("detail", "Erro ao cadastrar")
                            st.error(f"Falha no cadastro: {detail}")
                        else:
                            st.error(f"Erro de conexão: Não foi possível conectar ao serviço.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="saas-card" style="margin-top: 1rem; border-left: 4px solid var(--primary);">
                <h3>Diretrizes 💡</h3>
                <p style="font-size: 0.9rem; color: var(--text-muted);">Mantenha a organização segura seguindo os padrões:</p>
                <ul style="font-size: 0.85rem; color: var(--text-main); margin-top: 1rem;">
                    <li><b>Normalização</b>: Nomes de usuário tornam-se minúsculos.</li>
                    <li><b>Permissões</b>: Novos usuários têm acesso padrão aos hubs.</li>
                    <li><b>Segurança</b>: Recomende senhas fortes de 8+ caracteres.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with tab_pass:
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("""
            <div class="saas-card" style="margin-top: 1rem;">
                <h3 style="margin-bottom: 1.5rem;">🔐 Resetar Senha</h3>
            """, unsafe_allow_html=True)
            with st.form("admin_reset_password_form", clear_on_submit=True):
                u_target = st.text_input("Usuário Alvo", placeholder="Ex: jose")
                new_p = st.text_input("Nova Senha", type="password")
                conf_p = st.text_input("Confirmar Nova Senha", type="password")
                pass_submitted = st.form_submit_button("Atualizar Senha 🔐", use_container_width=True)
                
                if pass_submitted:
                    if not u_target or not new_p:
                        st.warning("Preencha o usuário e a nova senha.")
                    elif new_p != conf_p:
                        st.error("As senhas não conferem.")
                    else:
                        res = service.change_password(new_p, u_target)
                        if res and res.status_code == 200:
                            st.success(f"Senha de **{u_target}** atualizada com sucesso!")
                            time.sleep(1)
                        elif res:
                            detail = res.json().get("detail", "Erro ao processar")
                            st.error(f"Falha: {detail}")
                        else:
                            st.error(f"Erro de conexão: Não foi possível conectar ao serviço.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="saas-card" style="margin-top: 1rem; border-left: 4px solid #f59e0b;">
                <h3>Segurança 🔐</h3>
                <p style="font-size: 0.9rem; color: var(--text-muted);">Atenção ao resetar credenciais:</p>
                <ul style="font-size: 0.85rem; color: var(--text-main); margin-top: 1rem;">
                    <li><b>Imediato</b>: A alteração entra em vigor no próximo login.</li>
                    <li><b>Comunicação</b>: Informe o colaborador sobre a nova senha.</li>
                    <li><b>Auditoria</b>: Esta ação será registrada nos logs do sistema.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

def render_password_change(service):
    st.markdown("""
    <div class="stHeader">
        <h1>🔐 Alterar Minha Senha</h1>
        <p>Mantenha sua conta segura atualizando sua senha periodicamente.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, _ = st.columns([1.5, 1])
    
    with col1:
        st.markdown("""
        <div class="saas-card" style="margin-top: 1rem;">
            <h3>Segurança Pessoal</h3>
            <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Sua senha é pessoal e intransferível.</p>
        """, unsafe_allow_html=True)
        with st.form("user_change_password_form", clear_on_submit=True):
            st.write(f"Usuário: **{st.session_state.username}**")
            new_p = st.text_input("Nova Senha", type="password")
            conf_p = st.text_input("Confirmar Nova Senha", type="password")
            
            if st.form_submit_button("Atualizar Minha Senha 🔐", use_container_width=True):
                if not new_p:
                    st.warning("Informe a nova senha.")
                elif new_p != conf_p:
                    st.error("As senhas não conferem.")
                else:
                    res = service.change_password(new_p)
                    if res and res.status_code == 200:
                        st.success("Senha alterada com sucesso!")
                        time.sleep(1)
                    elif res:
                        detail = res.json().get("detail", "Erro ao processar")
                        st.error(f"Falha: {detail}")
                    else:
                        st.error(f"Erro de conexão: Não foi possível conectar ao serviço.")
        st.markdown("</div>", unsafe_allow_html=True)
