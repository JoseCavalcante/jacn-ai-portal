import streamlit as st

def saas_card(title, description, icon_svg=None, footer_html=None, adaptive_height=False, extra_classes=""):
    """
    Renderiza um card SaaS premium com suporte a ícones SVG e layout refinado.
    """
    icon_html = f'<div class="icon-container">{icon_svg}</div>' if icon_svg else ''
    footer = f'<div style="margin-top: auto; padding-top: 1.5rem; border-top: 1px solid var(--border-light);">{footer_html}</div>' if footer_html else ''
    card_class = "saas-card" if adaptive_height else "saas-card standard-height"
    if extra_classes:
        card_class += f" {extra_classes}"
    
    st.markdown(f'<div class="{card_class}">{icon_html}<b style="display: block; font-size: 1.25rem; margin-bottom: 0.8rem; color: #0f172a;">{title}</b><p>{description}</p>{footer}</div>', unsafe_allow_html=True)

def metric_card(label, value, subtext=None, color=None):
    """
    Renderiza um card de métrica alinhado ao novo design system.
    """
    color_style = f"color: {color};" if color else ""
    color_style = f"color: {color};" if color else ""
    st.markdown(f'<div class="saas-card metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="{color_style}">{value}</div><div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">{subtext if subtext else ""}</div></div>', unsafe_allow_html=True)

def render_offline_state():
    """
    Exibe uma tela de erro elegante quando a API está offline.
    """
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; text-align: center;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔌</div>
        <h2 style="color: #64748b;">Sistema Indisponível</h2>
        <p style="color: #94a3b8; max-width: 500px; margin-bottom: 2rem;">
            Não foi possível estabelecer conexão com o servidor. Por favor, verifique se a API está rodando e tente novamente.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Tentar Reconectar", use_container_width=True):
            st.rerun()
    
    st.stop()
