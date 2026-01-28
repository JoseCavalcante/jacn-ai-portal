import streamlit as st

def saas_card(title, description, icon_svg=None, footer_html=None, adaptive_height=False):
    """
    Renderiza um card SaaS premium com suporte a ícones SVG e layout refinado.
    """
    icon_html = f'<div class="icon-container">{icon_svg}</div>' if icon_svg else ''
    footer = f'<div style="margin-top: auto; padding-top: 1.5rem; border-top: 1px solid var(--border-light);">{footer_html}</div>' if footer_html else ''
    card_class = "saas-card" if adaptive_height else "saas-card standard-height"
    
    st.markdown(f"""
    <div class="{card_class}">
        {icon_html}
        <h3>{title}</h3>
        <p>{description}</p>
        {footer}
    </div>
    """, unsafe_allow_html=True)

def metric_card(label, value, subtext=None, color=None):
    """
    Renderiza um card de métrica alinhado ao novo design system.
    """
    color_style = f"color: {color};" if color else ""
    st.markdown(f"""
    <div class="saas-card metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="{color_style}">{value}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">{subtext if subtext else ''}</div>
    </div>
    """, unsafe_allow_html=True)
