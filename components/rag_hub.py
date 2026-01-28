import streamlit as st
import time

def render_rag_hub(service):
    st.markdown(f"""
    <div style="margin-bottom: 2.5rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">📚 RAG Hub</h1>
        <p style="color: var(--text-muted); font-size: 1.1rem;">Busca Semântica e Chat Contextual sobre sua base privada.</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔍 Busca Semântica", "🤖 Chat com Documentos", "📤 Upload & Gestão"])
    
    with tab1:
        st.subheader("Explorador Semântico")
        col1, col2 = st.columns([4, 1])
        query = col1.text_input("O que você procura nos seus documentos?", placeholder="Ex: Regras de segurança...")
        k = col2.slider("Resultados", 1, 10, 3)
        
        if st.button("Executar Busca 🔎"):
            try:
                res = service.rag_search(query, k)
                if res and res.status_code == 200:
                    results = res.json()["results"]
                    if not results:
                        st.info("Nenhum resultado encontrado.")
                    for doc in results:
                        footer = f"""
                            <div style="display: flex; gap: 10px;">
                                <span class="status-badge badge-process">📄 {doc['source']}</span>
                                <span class="status-badge badge-active">Pág. {doc['page']}</span>
                            </div>
                        """
                        saas_card(
                            "Resultado da Busca", 
                            doc['content'], 
                            footer_html=footer,
                            adaptive_height=True
                        )
                elif res:
                    detail = res.json().get("detail", res.text) if res.status_code != 500 else "Erro interno no servidor"
                    st.error(f"Erro na busca: {detail}")
                else:
                    st.error(f"Erro de conexão: Não foi possível conectar ao serviço.")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")

    with tab2:
        st.subheader("Chat com Documentos")
        
        # Configurações Avançadas
        with st.expander("⚙️ Configurações de Busca"):
            col_k, col_t = st.columns(2)
            st.session_state.rag_k = col_k.slider(
                "Profundidade (K)", 1, 10, st.session_state.rag_k,
                help="Número de fragmentos de documentos a serem consultados."
            )
            st.session_state.rag_threshold = col_t.slider(
                "Sensibilidade (Threshold)", 0.0, 2.0, st.session_state.rag_threshold, 0.1,
                help="Quanto menor o valor, mais rigorosa é a busca. Valores altos permitem respostas mais amplas, mas com risco de alucinação."
            )
            if st.button("Resetar Padrões"):
                st.session_state.rag_k = 4
                st.session_state.rag_threshold = 1.1
                st.rerun()

        # Container para o histórico de chat
        chat_container = st.container(height=400)
        
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Input de chat
        if prompt := st.chat_input("Pergunte algo sobre seus documentos..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                with st.spinner("Consultando base de dados..."):
                    res = service.rag_ask(prompt, st.session_state.rag_k, st.session_state.rag_threshold)
                    if res and res.status_code == 200:
                        data = res.json()
                        answer = data["answer"]
                        st.markdown(answer)
                        
                        if data["sources"]:
                            st.markdown("<h4 style='margin: 1.5rem 0 0.8rem 0; font-size: 1.1rem;'>📚 Fontes Consultadas</h4>", unsafe_allow_html=True)
                            source_cols = st.columns(min(len(data["sources"]), 3))
                            for idx, s in enumerate(data["sources"]):
                                with source_cols[idx % 3]:
                                    st.markdown(f"""
                                    <div style="padding: 1rem; border-radius: 12px; background: white; border: 1px solid var(--border-light); box-shadow: 0 2px 4px rgba(0,0,0,0.02); height: 100%;">
                                        <div style="font-weight: 700; font-size: 0.85rem; color: var(--primary); display: flex; align-items: center; gap: 6px; margin-bottom: 0.5rem;">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                                            {s['source']}
                                        </div>
                                        <div style="font-size: 0.75rem; color: var(--text-muted);">Fragmento da Página <b>{s['page']}</b></div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        # Feedback UI refined
                        st.markdown("<div style='margin-top: 2rem; border-top: 1px solid var(--border-light); padding-top: 1rem;'></div>", unsafe_allow_html=True)
                        f_col1, f_col2, f_col3 = st.columns([0.5, 0.5, 4])
                        
                        msg_id = data.get("message_id")
                        
                        with f_col1:
                            if st.button("👍", key=f"up_{msg_id}"):
                                if service.update_rag_feedback(msg_id, 1):
                                    st.toast("Obrigado pelo feedback!", icon="✅")
                        with f_col2:
                            if st.button("👎", key=f"down_{msg_id}"):
                                if service.update_rag_feedback(msg_id, -1):
                                    st.toast("Lamentamos. Vamos melhorar!", icon="⚠️")
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    elif res:
                        st.error("Erro ao consultar a base de conhecimento.")
                    else:
                        st.error(f"Erro de conexão: Não foi possível conectar ao serviço.")
            st.rerun()

        if st.button("Limpar Conversa 🗑️"):
            st.session_state.chat_history = []
            st.rerun()

    with tab3:
        st.subheader("Gestão de Documentos Privados")
        st.write(f"Gerencie os documentos acessíveis apenas por **{st.session_state.username}**.")
        
        # Seção de Upload
        with st.expander("📤 Subir Novo Documento", expanded=False):
            uploaded = st.file_uploader("Escolha um arquivo PDF", type="pdf")
            if uploaded and st.button("Processar Documento 🚀"):
                with st.spinner("Vetorizando arquivo..."):
                    res = service.upload_file(uploaded)
                    if res and res.status_code == 200:
                        st.success(f"Documento '{uploaded.name}' indexado com sucesso!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    elif res: 
                        st.error(f"Falha ao processar arquivo: {res.text}")
        
        st.divider()
        
        # Seção de Lista e Exclusão
        st.markdown("### 📄 Arquivos Ativos")
        res = service.list_files()
        if res and res.status_code == 200:
            files = res.json()
            if not files:
                st.info("Nenhum documento encontrado na sua pasta.")
            else:
                for f in files:
                    col_info, col_del = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"**{f['name']}**")
                        st.caption(f"Tamanho: {f['size'] // 1024} KB | Criado em: {f['created_at'][:16].replace('T', ' ')}")
                    with col_del:
                        if st.button("Excluir 🗑️", key=f"del_{f['name']}", type="secondary", width='stretch'):
                            with st.spinner("Removendo..."):
                                res_del = service.delete_file(f['name'])
                                if res_del and res_del.status_code == 200:
                                    st.toast(f"Arquivo {f['name']} removido!", icon="✅")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Erro ao deletar arquivo.")
                    st.divider()
        elif res:
            st.error("Erro ao carregar lista de arquivos.")
