"""Planned cleaning workflow page."""

import streamlit as st

from webapp.components.navigation import render_navigation

st.set_page_config(page_title="Nettoyage | Vote Transfer", page_icon="✓", layout="wide")
render_navigation()

st.title("Nettoyage et contrôles")
st.write(
    "Cette étape transformera les fichiers bruts en tables comparables sans jamais les écraser."
)

checks = (
    ("Schémas", "Détecter les changements de colonnes entre millésimes, notamment celui de 2026."),
    ("Identifiants", "Normaliser année, tour, commune, département, bureau et candidat."),
    ("Cohérence des voix", "Comparer exprimés, blancs, nuls et somme des voix par candidat."),
    ("Géographie", "Projeter les communes dans un référentiel documenté et tracer les fusions."),
    ("Valeurs manquantes", "Distinguer absence réelle, secret statistique et erreur de jointure."),
)
for title, description in checks:
    st.markdown(f"**{title}**  \n{description}")

st.warning("Aucune donnée nettoyée n'est encore produite : la collecte doit d'abord être validée.")
