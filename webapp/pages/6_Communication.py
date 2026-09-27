"""Communication deliverables page."""

import streamlit as st

from webapp.components.navigation import render_navigation

st.set_page_config(page_title="Communication | Vote Transfer", page_icon="◎", layout="wide")
render_navigation()

st.title("Communication")
st.write("Les trois livrables devront raconter la même histoire et reproduire les mêmes chiffres.")

report, slides, app = st.columns(3)
report.subheader("Rapport")
report.write("Cinq pages maximum : question, données, méthode, résultats et limites.")
slides.subheader("Présentation")
slides.write("Quinze minutes centrées sur les preuves et les décisions importantes.")
app.subheader("Application")
app.write("Exploration des transferts estimés et de leur effet sur l'équilibre national.")

st.info("Les graphiques seront générés par le même code que les tables utilisées dans le rapport.")
