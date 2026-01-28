import streamlit as st
import time

def render_prompt_hub(service, logout_fn):
    st.markdown(f"""
    <div style="margin-bottom: 2.5rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">🚀 Prompt Hub</h1>
        <p style="color: var(--text-muted); font-size: 1.1rem;">Geração de conteúdo técnico e profissional via LLM de alta performance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        tema = st.text_area("Digite o tema ou assunto do conteúdo:", 
                           placeholder="Ex: Arquitetura de Microserviços com Python...",
                           help="A IA estruturará o conteúdo com base neste tema.")
        
        if st.button("Gerar Conteúdo ✨"):
            if not tema:
                st.warning("Informe um tema para continuar.")
            else:
                with st.spinner("Estruturando e processando via LLM..."):
                    res = service.generate_content(tema)
                    if res and res.status_code == 200:
                        data = res.json()
                        st.balloons()
                        st.subheader("✅ Resultado Gerado")
                        saas_card(
                            "Conteúdo Estruturado", 
                            data['conteudo_gerado'], 
                            adaptive_height=True
                        )
                        
                        # Feedback UI
                        st.markdown("<div style='margin-top: 1.5rem; border-top: 1px solid var(--border-light); padding-top: 1rem;'></div>", unsafe_allow_html=True)
                        f_col1, f_col2, f_col3 = st.columns([0.5, 0.5, 4])
                        
                        p_id = data.get("prompt_id")
                        
                        with f_col1:
                            if st.button("👍", key=f"p_up_{p_id}"):
                                if service.update_prompt_feedback(p_id, 1):
                                    st.toast("Gostamos que gostou!", icon="✨")
                        with f_col2:
                            if st.button("👎", key=f"p_down_{p_id}"):
                                if service.update_prompt_feedback(p_id, -1):
                                    st.toast("Vamos ajustar a IA!", icon="🔧")

                        st.download_button("📥 Baixar Conteúdo (.txt)", data['conteudo_gerado'], file_name="ai_content.txt")
                    elif res and res.status_code == 401:
                        st.error("Sessão expirada.")
                        logout_fn()
                    elif res:
                        st.error(f"Erro na API: {res.text}")
                    else:
                        st.error(f"Erro ao chamar a API.")
