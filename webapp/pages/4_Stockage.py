"""Storage choices page."""

import streamlit as st

from webapp.components.navigation import render_navigation

st.set_page_config(page_title="Stockage | Vote Transfer", page_icon="▦", layout="wide")
render_navigation()

st.title("Stockage")
st.write("Le stockage sépare la preuve originale des tables optimisées pour l'analyse.")

st.markdown(
    """
| Couche | Format prévu | Rôle |
|---|---|---|
| `data/raw` | formats publiés + manifestes JSON | archive immutable et provenance |
| `data/interim` | Parquet | données harmonisées et contrôlées |
| `data/processed` | Parquet / DuckDB | tables départementales prêtes pour l'analyse |
| Streamlit | lectures DuckDB/Parquet | visualisation sans dupliquer les calculs |
"""
)

st.subheader("Pourquoi Parquet et DuckDB ?")
st.write(
    "Parquet conserve les types, compresse les gros fichiers et permet de ne lire que les colonnes "
    "utiles. DuckDB exécute des requêtes analytiques directement sur ces fichiers sans serveur."
)
st.caption(
    "Alternative à comparer dans le rapport : une base relationnelle PostgreSQL centralisée."
)
