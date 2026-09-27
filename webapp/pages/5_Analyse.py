"""Analysis scope page."""

import streamlit as st

from webapp.components.navigation import render_navigation

st.set_page_config(page_title="Analyse | Vote Transfer", page_icon="◫", layout="wide")
render_navigation()

st.title("Analyse")
st.write(
    "L'analyse partira des différences observées entre les deux tours à l'échelle départementale. "
    "La méthode finale ne sera choisie qu'après inspection de la qualité et de la couverture."
)

st.subheader("Sorties attendues")
st.markdown(
    """
- parts de voix et abstention par département, année et tour ;
- comparaison des reports plausibles entre blocs ;
- agrégation nationale des scénarios départementaux ;
- incertitude et sensibilité aux hypothèses ;
- distinction explicite entre observations et interprétations.
"""
)
st.error(
    "Les reports individuels ne sont pas observés. Toute estimation à partir de résultats agrégés "
    "reste exposée au risque d'erreur écologique."
)
