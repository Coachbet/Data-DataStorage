"""Public disclosure of AI assistance used to prepare the project repository."""

import streamlit as st

st.set_page_config(
    page_title="Transparence IA | Vote Transfer",
    page_icon="◉",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root { --ink: #172033; --blue: #2446a8; --red: #d93b4a; }
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #f5f7fb 65%, #eef2fa 100%); }
    .block-container { max-width: 1050px; padding-top: 2.8rem; padding-bottom: 4rem; }
    .eyebrow { color: var(--blue); font-size: .78rem; font-weight: 800; letter-spacing: .13em;
               text-transform: uppercase; margin-bottom: .8rem; }
    .page-title { color: var(--ink); font-size: clamp(2.7rem, 6vw, 4.9rem); line-height: 1;
                  letter-spacing: -.05em; margin: 0 0 1rem; }
    .intro { color: #4b5870; font-size: 1.1rem; line-height: 1.7; max-width: 760px; }
    .metadata { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem;
                margin: 2rem 0; }
    .metadata-card { background: var(--ink); color: white; border-radius: 4px; padding: 1.4rem; }
    .metadata-label { color: #9fb5ff; font-size: .75rem; font-weight: 800;
                      letter-spacing: .1em; text-transform: uppercase; }
    .metadata-value { font-size: 1.2rem; font-weight: 700; margin-top: .4rem; }
    .work-item { background: white; border: 1px solid #dde3ee; border-left: 4px solid var(--blue);
                 border-radius: 4px; padding: 1rem 1.2rem; margin-bottom: .75rem; }
    .work-item strong { color: var(--ink); }
    .work-item p { color: #58647a; line-height: 1.55; margin: .35rem 0 0; }
    .notice { background: #fff3f3; border: 1px solid #f2c8cc; border-radius: 4px;
              color: #712732; padding: 1.1rem 1.25rem; margin-top: 1.5rem; line-height: 1.6; }
    @media (max-width: 680px) { .metadata { grid-template-columns: 1fr; } }
    [data-testid="stHeader"] { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Navigation")
    st.page_link("Home.py", label="Accueil", icon="🏠")
    st.page_link(
        "pages/1_Transparence_IA.py",
        label="Transparence IA",
        icon="🔎",
    )

st.markdown(
    """
    <div class="eyebrow">Documentation du projet</div>
    <h1 class="page-title">Transparence sur l’usage de l’IA</h1>
    <p class="intro">
      Cette page documente l’assistance d’intelligence artificielle utilisée pour
      préparer la structure technique initiale du projet. Elle permet d’identifier
      l’outil, la date d’intervention et la nature exacte des contributions.
    </p>
    <div class="metadata">
      <div class="metadata-card">
        <div class="metadata-label">Date de l’intervention</div>
        <div class="metadata-value">27 septembre 2026</div>
      </div>
      <div class="metadata-card">
        <div class="metadata-label">Modèle utilisé</div>
        <div class="metadata-value">GPT-5 · Codex · OpenAI</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Travaux réalisés avec l’assistance de l’IA")

contributions = (
    (
        "Lecture et synthèse des consignes",
        "Analyse du sujet, de la proposition du groupe, des diapositives du cours et des "
        "retours de l’enseignant afin d’identifier les livrables et contraintes.",
    ),
    (
        "Organisation du dépôt",
        "Création d’une structure séparant les données, la documentation, le rapport, la "
        "présentation, les tests, l’application web et le code métier selon une approche DDD.",
    ),
    (
        "Environnement reproductible",
        "Configuration de uv, des dépendances Python, du fichier de verrouillage et des règles "
        "Git permettant d’exclure les données volumineuses, secrets et fichiers générés.",
    ),
    (
        "Documentation méthodologique",
        "Rédaction du périmètre initial, des règles de reproductibilité et d’un premier "
        "dictionnaire des concepts et variables à opérationnaliser.",
    ),
    (
        "Interface Streamlit",
        "Création de la page d’accueil et de la présente page de transparence, avec une mise en "
        "forme cohérente avec le sujet de l’étude.",
    ),
    (
        "Vérifications techniques",
        "Exécution du formatage, de l’analyse statique, des tests automatisés, de la compilation "
        "Python et d’un test de démarrage de l’application.",
    ),
)

for title, description in contributions:
    st.markdown(
        f"""
        <div class="work-item">
          <strong>{title}</strong>
          <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="notice">
      <strong>Responsabilité humaine</strong><br>
      L’IA a servi d’outil d’assistance à la rédaction et au développement. Elle n’a pas collecté
      les données électorales, réalisé l’analyse finale, choisi seule la méthodologie ni produit
      les conclusions scientifiques. Le groupe reste responsable de vérifier le code, les sources,
      les hypothèses, les résultats et leur interprétation avant toute remise.
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Dernière mise à jour de cette déclaration : 27 septembre 2026")
