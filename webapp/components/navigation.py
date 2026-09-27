"""Shared horizontal navigation for every Streamlit page."""

import streamlit as st

NAVIGATION = (
    ("Home.py", "Accueil", "🏠"),
    ("pages/2_Collecte.py", "Collecte", "↓"),
    ("pages/3_Nettoyage.py", "Nettoyage", "✓"),
    ("pages/4_Stockage.py", "Stockage", "▦"),
    ("pages/5_Analyse.py", "Analyse", "◫"),
    ("pages/6_Communication.py", "Communication", "◎"),
    ("pages/1_Transparence_IA.py", "Transparence IA", "◇"),
)


def render_navigation() -> None:
    """Render the project lifecycle as a persistent horizontal ribbon."""

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        .workflow-label { color: #667085; font-size: .72rem; font-weight: 800;
                          letter-spacing: .12em; text-transform: uppercase; margin-bottom: .3rem; }
        div[data-testid="stPageLink"] a { border: 1px solid #dce2ed; border-radius: 4px;
                                          background: #fff; min-height: 3rem;
                                          padding: .55rem .65rem;
                                          justify-content: center; }
        div[data-testid="stPageLink"] a:hover { border-color: #2446a8; color: #2446a8; }
        div[data-testid="stPageLink"] p { font-size: .86rem; font-weight: 700; }
        </style>
        <div class="workflow-label">Cycle du projet</div>
        """,
        unsafe_allow_html=True,
    )
    columns = st.columns(len(NAVIGATION), gap="small")
    for column, (path, label, icon) in zip(columns, NAVIGATION, strict=True):
        with column:
            st.page_link(path, label=label, icon=icon)
    st.markdown("---")
