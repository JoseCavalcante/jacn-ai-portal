import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

def render_usage_charts(prompt_history, rag_history):
    """
    Renderiza gráficos de uso baseados no histórico.
    """
    st.markdown("### 📊 Analítico de Uso")
    
    col1, col2 = st.columns(2)
    
    # Processamento de Prompts
    if prompt_history:
        df_prompts = pd.DataFrame(prompt_history)
        df_prompts['created_at'] = pd.to_datetime(df_prompts['created_at'])
        df_prompts['date'] = df_prompts['created_at'].dt.date
        usage_prompts = df_prompts.groupby('date').size().reset_index(name='count')
        
        with col1:
            fig_prompts = px.area(usage_prompts, x='date', y='count', 
                                title='<b>Geração de Conteúdo</b> (Prompts/Dia)',
                                labels={'count': 'Quantidade', 'date': 'Data'},
                                color_discrete_sequence=['#6366f1'])
            fig_prompts.update_traces(
                line_width=3, 
                fillcolor='rgba(99, 102, 241, 0.1)',
                marker=dict(size=8, color='#6366f1', opacity=0.8)
            )
            fig_prompts.update_layout(
                font_family="Plus Jakarta Sans",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                height=350,
                xaxis=dict(showgrid=False, color='#94a3b8'),
                yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.1)', color='#94a3b8'),
                title_font_size=18
            )
            st.plotly_chart(fig_prompts, use_container_width=True)
            
            # Gráfico de Sentimento (Prompts)
            if 'feedback' in df_prompts.columns:
                sent_counts = df_prompts['feedback'].value_counts().reset_index(name='count')
                sent_counts['label'] = sent_counts['feedback'].map({1: 'Positivo', 0: 'Neutro', -1: 'Negativo'})
                fig_sent = px.pie(sent_counts, values='count', names='label', hole=0.5,
                                title='Satisfação (Prompts)',
                                color='label',
                                color_discrete_map={'Positivo': '#10b981', 'Neutro': '#94a3b8', 'Negativo': '#ef4444'})
                fig_sent.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
                st.plotly_chart(fig_sent, use_container_width=True)
    else:
        col1.info("Sem dados de prompts para o gráfico.")

    # Processamento de RAG (Buscas/Perguntas)
    if rag_history:
        df_rag = pd.DataFrame(rag_history)
        df_rag['created_at'] = pd.to_datetime(df_rag['created_at'])
        df_rag['date'] = df_rag['created_at'].dt.date
        usage_rag = df_rag.groupby('date').size().reset_index(name='count')
        
        with col2:
            fig_rag = px.line(usage_rag, x='date', y='count', 
                             title='<b>Interações RAG</b> (Consultas/Dia)',
                             labels={'count': 'Interações', 'date': 'Data'},
                             color_discrete_sequence=['#a855f7'])
            fig_rag.update_traces(
                line_width=3, 
                mode='lines+markers',
                marker=dict(size=8, color='#a855f7', symbol='circle')
            )
            fig_rag.update_layout(
                font_family="Plus Jakarta Sans",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                height=350,
                xaxis=dict(showgrid=False, color='#94a3b8'),
                yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.1)', color='#94a3b8'),
                title_font_size=18
            )
            st.plotly_chart(fig_rag, use_container_width=True)

            # Gráfico de Sentimento (RAG)
            if 'feedback' in df_rag.columns:
                sent_counts_rag = df_rag['feedback'].value_counts().reset_index(name='count')
                sent_counts_rag['label'] = sent_counts_rag['feedback'].map({1: 'Positivo', 0: 'Neutro', -1: 'Negativo'})
                fig_sent_rag = px.pie(sent_counts_rag, values='count', names='label', hole=0.5,
                                    title='Satisfação (RAG)',
                                    color='label',
                                    color_discrete_map={'Positivo': '#10b981', 'Neutro': '#94a3b8', 'Negativo': '#ef4444'})
                fig_sent_rag.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
                st.plotly_chart(fig_sent_rag, use_container_width=True)
    else:
        col2.info("Sem dados de RAG para o gráfico.")

    # 3. Gráfico de Horários de Pico (Combinado)
    st.markdown("---")
    all_data = []
    if prompt_history:
        for p in prompt_history:
            all_data.append({'hour': pd.to_datetime(p['created_at']).hour, 'type': 'Prompt'})
    if rag_history:
        for r in rag_history:
            all_data.append({'hour': pd.to_datetime(r['created_at']).hour, 'type': 'RAG'})
    
    if all_data:
        df_hours = pd.DataFrame(all_data)
        usage_hours = df_hours.groupby(['hour', 'type']).size().reset_index(name='count')
        
        fig_hours = px.bar(usage_hours, x='hour', y='count', color='type',
                          title='<b>Distribuição de Uso por Hora</b>',
                          labels={'count': 'Requisições', 'hour': 'Hora do Dia'},
                          barmode='group',
                          color_discrete_map={'Prompt': '#6366f1', 'RAG': '#a855f7'})
        
        fig_hours.update_layout(
            font_family="Plus Jakarta Sans",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(tickmode='linear', tick0=0, dtick=1, color='#94a3b8'),
            yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.1)', color='#94a3b8'),
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_hours, use_container_width=True)

def render_storage_chart(current_docs, max_docs):
    """
    Gráfico de rosca para ocupação de documentos.
    """
    labels = ['Ocupado', 'Disponível']
    values = [current_docs, max(0, max_docs - current_docs)]
    
    fig = px.pie(names=labels, values=values, hole=0.7,
                color_discrete_sequence=['#6366f1', '#e2e8f0'],
                title="<b>Ocupação</b> de Documentos")
    
    fig.update_layout(
        font_family="Plus Jakarta Sans",
        showlegend=False,
        margin=dict(l=0, r=0, t=50, b=0),
        height=250,
        annotations=[dict(
            text=f"<b>{int(current_docs/max_docs*100)}%</b>", 
            x=0.5, y=0.5, 
            font_size=24, 
            showarrow=False,
            font_color='#0f172a'
        )]
    )
    st.plotly_chart(fig, use_container_width=True)
