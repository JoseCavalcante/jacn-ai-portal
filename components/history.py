import streamlit as st
from components.ui import saas_card
import pandas as pd
import io
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'JACN AI Portal - Relatorio', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def to_pdf(df, title):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=title, ln=True, align='L')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=10)
    # Basic list dump
    for i, row in df.iterrows():
        # Clean text to avoid encoding errors in standard FPDF
        line = ""
        for val in row.values:
            clean_val = str(val).replace('\u2013', '-').replace('\u2014', '-')
            line += f"{clean_val} | "
        
        # Multi_cell is safer for long text
        try:
             pdf.multi_cell(0, 8, txt=line[:500].encode('latin-1', 'replace').decode('latin-1'))
        except:
             pdf.multi_cell(0, 8, txt="[Erro de codificacao na linha]")
        pdf.ln(2)
        
    return pdf.output(dest='S').encode('latin-1')

def render_history(service):
    st.markdown("""
    <div class="stHeader">
        <h1>📜 Histórico de Atividade</h1>
        <p>Revise suas interações passadas com a IA.</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_prompts, tab_rag = st.tabs(["🚀 Prompt Hub", "📚 RAG Hub"])
    
    with tab_prompts:
        try:
            res = service.get_prompt_history()
            if res and res.status_code == 200:
                data = res.json()
                if not data:
                    st.info("Nenhum prompt gerado ainda.")
                else:
                    # Export Button
                    df = pd.DataFrame(data)
                    if 'feedback' in df.columns:
                        df['Sentimento'] = df['feedback'].map({1: 'Positivo', 0: 'Neutro', -1: 'Negativo'})
                        # Remover ou renomear colunas técnicas
                        df = df.rename(columns={'tema': 'Tema', 'conteudo': 'Conteudo', 'created_at': 'Data Criação'})
                        export_df = df[['Data Criação', 'Tema', 'Conteudo', 'Sentimento']]
                    else:
                        export_df = df

                    csv = export_df.to_csv(index=False).encode('utf-8')
                    pdf_data = to_pdf(export_df, "Historico de Prompts")
                    
                    cex1, cex2 = st.columns(2)
                    with cex1:
                        st.download_button(
                            label="📥 Exportar CSV",
                            data=csv,
                            file_name='historico_prompts.csv',
                            mime='text/csv',
                            use_container_width=True
                        )
                    with cex2:
                        st.download_button(
                            label="📄 Exportar PDF",
                            data=pdf_data,
                            file_name='historico_prompts.pdf',
                            mime='application/pdf',
                            use_container_width=True
                        )
                    st.divider()
                for item in data:
                    fb_icon = " ✨" if item.get('feedback') == 1 else (" 🔧" if item.get('feedback') == -1 else "")
                    with st.expander(f"📌 {item['tema']}{fb_icon} ({item['created_at'][:16].replace('T', ' ')})"):
                        content_html = item['conteudo'].replace('\n', '<br>')
                        saas_card(
                            item['tema'],
                            item['conteudo'],
                            adaptive_height=True
                        )
                        st.download_button(f"Baixar conteúdo", item['conteudo'], file_name=f"prompt_{item['id']}.txt", key=f"dl_{item['id']}")
            elif res:
                st.error("Falha ao carregar histórico de prompts.")
            else:
                st.error(f"Erro de conexão: Não foi possível conectar ao serviço.")
        except Exception as e:
            st.error(f"Erro de conexão: {e}")

    with tab_rag:
        try:
            res = service.get_rag_history()
            if res and res.status_code == 200:
                data = res.json()
                if not data:
                    st.info("Nenhuma conversa no RAG ainda.")
                else:
                    # Export Button
                    df = pd.DataFrame(data)
                    if 'feedback' in df.columns:
                        df['Sentimento'] = df['feedback'].map({1: 'Positivo', 0: 'Neutro', -1: 'Negativo'})
                        df = df.rename(columns={'pergunta': 'Pergunta', 'resposta': 'Resposta', 'created_at': 'Data Criação'})
                        export_df = df[['Data Criação', 'Pergunta', 'Resposta', 'Sentimento']]
                    else:
                        export_df = df

                    csv = export_df.to_csv(index=False).encode('utf-8')
                    pdf_data_rag = to_pdf(export_df, "Historico RAG")
                    
                    cr1, cr2 = st.columns(2)
                    with cr1:
                        st.download_button(
                            label="📥 Exportar CSV",
                            data=csv,
                            file_name='historico_rag.csv',
                            mime='text/csv',
                            use_container_width=True
                        )
                    with cr2:
                        st.download_button(
                            label="📄 Exportar PDF",
                            data=pdf_data_rag,
                            file_name='historico_rag.pdf',
                            mime='application/pdf',
                            use_container_width=True
                        )
                    st.divider()
                for item in data:
                    fb_icon = " ✅" if item.get('feedback') == 1 else (" ⚠️" if item.get('feedback') == -1 else "")
                    with st.expander(f"💬 {item['pergunta'][:50]}...{fb_icon} ({item['created_at'][:16].replace('T', ' ')})"):
                        st.write(f"**Pergunta:** {item['pergunta']}")
                        response_html = item['resposta'].replace('\n', '<br>')
                        saas_card(
                            item['pergunta'],
                            item['resposta'],
                            adaptive_height=True
                        )
                        if item['sources']:
                            st.write("**Fontes:**")
                            for s in item['sources']:
                                st.caption(f"- {s['source']} (Pág {s['page']})")
            elif res:
                st.error("Falha ao carregar histórico do RAG.")
            else:
                st.error(f"Erro de conexão: Não foi possível conectar ao serviço.")
        except Exception as e:
            st.error(f"Erro de conexão: {e}")

def render_subscription(service):
    st.markdown("""
    <div class="stHeader">
        <h1>💳 Minha Assinatura</h1>
        <p>Gerencie seu plano, faturamento e limites de uso.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Reutilizando a lógica de stats rápida para assinatura
    data = service.get_tenant_info()
    if data:
        stats = {
            "tier": data["subscription_tier"],
            "tenant_name": data["name"],
            "docs_count": data["current_document_count"],
            "max_docs": data["max_documents"],
            "max_prompts": data["max_prompts_per_day"]
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            saas_card(
                f"Plano Atual: {stats['tier'].upper()}",
                f"Sua organização: {stats['tenant_name']}",
                footer_html=f"""
                <div style="margin: 1.5rem 0; padding: 1rem; background: rgba(99, 102, 241, 0.05); border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.1);">
                    <p style="margin-bottom: 0.5rem;">📄 Documentos: <b>{stats['docs_count']} / {stats['max_docs']}</b></p>
                    <div style="width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                        <div style="width: {(stats['docs_count']/stats['max_docs'])*100}%; height: 100%; background: var(--primary);"></div>
                    </div>
                </div>
                <div style="margin: 1rem 0;">
                    <p>🤖 Prompts Diários: <b>Limite de {stats['max_prompts']}</b></p>
                </div>
                """,
                adaptive_height=True
            )

        with col2:
            saas_card(
                "Upgrade de Plano 🚀",
                "Obtenha mais espaço e recursos ilimitados para sua equipe.",
                footer_html="""
                <div style="padding: 1.2rem; background: #f8fafc; border-radius: 16px; margin: 1.5rem 0; border: 1px dashed #cbd5e1;">
                    <p style="font-size: 1.1rem; color: var(--primary);"><b>Plano PRO</b></p>
                    <p style="font-size: 1.5rem; font-weight: 800; margin: 0.5rem 0;">$49<span style="font-size: 0.9rem; font-weight: 400; color: var(--text-muted);">/mês</span></p>
                    <ul style="font-size: 0.9rem; color: var(--text-muted); padding-left: 1.2rem;">
                        <li>Até 50 documentos indexados</li>
                        <li>500 prompts diários de alta performance</li>
                        <li>Suporte prioritário 24/7</li>
                        <li>Exportação avançada de dados</li>
                    </ul>
                </div>
                """,
                adaptive_height=True
            )
            if st.button("Fazer Upgrade Agora"):
                st.info("Integração com Stripe em breve! Entre em contato com o suporte.")
    else:
        st.error("Erro ao carregar informações de assinatura.")
