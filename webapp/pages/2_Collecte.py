"""Collection status and source provenance page."""

from pathlib import Path

import streamlit as st

from vote_transfer.application.source_catalog import SOURCES
from webapp.components.navigation import render_navigation

st.set_page_config(page_title="Collecte | Vote Transfer", page_icon="↓", layout="wide")
render_navigation()

st.title("Collecte des données")
st.write(
    "Chaque source est reliée à la question de recherche, récupérée depuis son producteur et "
    "accompagnée d'un manifeste de provenance. Les données brutes ne sont jamais modifiées."
)

core_count = sum(source.core for source in SOURCES)
col_a, col_b, col_c = st.columns(3)
col_a.metric("Sources documentées", len(SOURCES))
col_b.metric("Sources principales", core_count)
col_c.metric("Manifestes présents", len(list(Path("data/raw").glob("**/manifest.json"))))

st.subheader("Catalogue de collecte")
for source in SOURCES:
    status = "Principale" if source.core else "Optionnelle / contrôle"
    with st.expander(f"{source.name} · {status}"):
        st.markdown(f"**Producteur :** {source.provider}")
        st.markdown(f"**Pourquoi :** {source.purpose}")
        st.markdown(f"**Accès :** {source.access_method}")
        st.markdown(f"**Sortie brute :** `data/raw/{source.raw_directory}/`")
        st.markdown(f"**Décision :** {source.notes}")
        st.link_button("Consulter la source officielle", source.landing_url)

st.subheader("Commandes reproductibles")
st.code(
    """# Comprendre ce qui sera utilisé
uv run python -m vote_transfer.infrastructure.collect --list

# Vérifier les URL et volumes sans écrire de données
uv run python -m vote_transfer.infrastructure.collect --source core

# Télécharger une source après vérification
uv run python -m vote_transfer.infrastructure.collect --source elections --download""",
    language="bash",
)
st.info(
    "Les téléchargements volumineux sont volontairement explicites. L'option --download évite "
    "qu'une simple inspection déclenche plusieurs gigaoctets de transfert."
)
