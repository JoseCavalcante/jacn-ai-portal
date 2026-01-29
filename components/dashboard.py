import streamlit as st
from components.ui import metric_card, saas_card
from components.visualizations import render_usage_charts, render_storage_chart

def render_dashboard(service, logout_fn):
    stats = {
        "status": "Offline",
        "docs_count": 0,
        "api_lat": "N/A",
        "tenant_name": "N/A",
        "tier": "free",
        "max_docs": 0,
        "max_prompts": 0
    }
    
    import time
    start_time = time.time()
    data = service.get_tenant_info()
    if data:
        stats["status"] = "Online"
        stats["api_lat"] = f"{int((time.time() - start_time) * 1000)}ms"
        stats["tenant_name"] = data["name"]
        stats["tier"] = data["subscription_tier"]
        stats["docs_count"] = data["current_document_count"]
        stats["max_docs"] = data["max_documents"]
        stats["max_prompts"] = data["max_prompts_per_day"]

    # Ícones SVG Modernos
    icon_prompt = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>'
    icon_rag = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>'
    icon_ops = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'

    st.markdown(f"""
    <div style="margin-bottom: 2.5rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">👋 Bem-vindo, {st.session_state.username}</h1>
        <p style="color: var(--text-muted); font-size: 1.1rem;">Assuma o controle da sua inteligência artificial corporativa na <b>{stats['tenant_name']}</b>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas Principais
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        status_color = "#10b981" if stats['status'] == 'Online' else "#ef4444"
        metric_card("Status Global", stats['status'], f"Latência: {stats['api_lat']}", color=status_color)
    with m2:
        metric_card("Plano SaaS", stats['tier'].upper(), "Assinatura Profissional", color="#6366f1")
    with m3:
        metric_card("Armazenamento", f"{stats['docs_count']} / {stats['max_docs']}", "PDFs Indexados")
    with m4:
        metric_card("Quota Diária", f"{stats['max_prompts']}", "Prompts Disponíveis")

    st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)

    # Ações Rápidas (Cards Premium)
    st.markdown("<h2 style='margin-bottom: 1.5rem; font-size: 1.5rem;'>⚡ Ações Rápidas</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        saas_card(
            "Prompt Hub", 
            "Gere conteúdos técnicos, relatórios e automações com LLMs de alta performance.",
            icon_svg=icon_prompt
        )
        if st.button("Abrir Prompt Hub", key="dash_prompt", use_container_width=True):
            st.session_state.current_page = "Prompt Hub"
            st.rerun()

    with col2:
        saas_card(
            "Base de Conhecimento", 
            "Busca semântica avançada e chat contextual sobre sua base de documentos privada.",
            icon_svg=icon_rag
        )
        if st.button("Abrir RAG Hub", key="dash_rag", use_container_width=True):
            st.session_state.current_page = "RAG Hub"
            st.rerun()

    with col3:
        footer_html = f"""
            <div style="font-size: 0.85rem; color: var(--text-muted);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span>Sincronização</span>
                    <span style="color: #10b981; font-weight: 600;">Ativa</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Último Backup</span>
                    <span style="color: var(--text-main); font-weight: 600;">Hoje, 12:45</span>
                </div>
            </div>
        """
        saas_card(
            "Configurações", 
            "Gerencie usuários, permissões e monitore os logs de auditoria da organização.",
            icon_svg=icon_ops,
            footer_html=footer_html
        )
        if st.button("Painel Administrativo", key="dash_admin", use_container_width=True):
            if st.session_state.role == "admin":
                st.session_state.current_page = "Gestão de Usuários"
            else:
                st.warning("Acesso restrito a administradores.")
            st.rerun()

    st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)
    
    # Buscar histórico para os gráficos
    prompt_res = service.get_prompt_history()
    rag_res = service.get_rag_history()
    
    prompt_history = prompt_res.json() if prompt_res and prompt_res.status_code == 200 else []
    rag_history = rag_res.json() if rag_res and rag_res.status_code == 200 else []
    
    # Gráficos de Uso
    render_usage_charts(prompt_history, rag_history)
