"""Streamlit cover page for the vote-transfer explorer."""

import streamlit as st

from vote_transfer.application.project_overview import get_project_overview

st.set_page_config(
    page_title="Vote Transfer | France",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink: #172033; --blue: #2446a8; --red: #d93b4a; }
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #f5f7fb 65%, #eef2fa 100%); }
    .block-container { max-width: 1180px; padding-top: 2.4rem; padding-bottom: 4rem; }
    .eyebrow { color: var(--blue); font-size: .78rem; font-weight: 800; letter-spacing: .13em;
               text-transform: uppercase; margin-bottom: 1rem; }
    .hero { border-top: 5px solid var(--blue); padding: 2.8rem 0 2.2rem; }
    .hero h1 { color: var(--ink); font-size: clamp(2.7rem, 6vw, 5.7rem); line-height: .98;
               letter-spacing: -.055em; max-width: 900px; margin: 0 0 1.5rem; }
    .hero-copy { color: #4b5870; font-size: 1.18rem; line-height: 1.7; max-width: 760px; }
    .question { background: var(--ink); color: white; border-radius: 4px; padding: 1.8rem 2rem;
                margin: 1.4rem 0 2.2rem; box-shadow: 12px 12px 0 #dfe5f3; }
    .question-label { color: #9fb5ff; font-size: .75rem; font-weight: 800;
                      letter-spacing: .12em; text-transform: uppercase; }
    .question p { font-size: 1.35rem; line-height: 1.45; margin: .65rem 0 0; }
    .step { background: white; border: 1px solid #dde3ee; border-radius: 4px; min-height: 175px;
            padding: 1.25rem; margin-bottom: 1rem; }
    .step-no { color: var(--red); font-family: monospace; font-weight: 700; }
    .step h3 { color: var(--ink); margin: .8rem 0 .45rem; }
    .step p, .source-card p { color: #58647a; line-height: 1.55; }
    .source-card { border-left: 3px solid var(--blue); padding: .2rem 1rem; margin: .6rem 0; }
    .limitation { background: #fff3f3; border: 1px solid #f2c8cc; border-radius: 4px;
                  color: #712732; padding: 1rem 1.2rem; margin-top: 1rem; }
    [data-testid="stHeader"] { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)

overview = get_project_overview()
research = overview["research"]

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
    <div class="hero">
      <div class="eyebrow">Data · Data Storage · Data Collection</div>
      <h1>Where do eliminated votes go?</h1>
      <p class="hero-copy">
        A reproducible investigation of second-round vote transfers in French
        presidential elections, from official raw results to department-level evidence.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="question">
      <div class="question-label">Central research question</div>
      <p>{research["question"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.page_link(
    "pages/1_Transparence_IA.py",
    label="Consulter la déclaration de transparence IA",
    icon="🔎",
)

st.subheader("One question. One traceable workflow.")
columns = st.columns(len(overview["workflow"]))
for column, (number, title, description) in zip(columns, overview["workflow"], strict=True):
    with column:
        st.markdown(
            f"""
            <div class="step">
              <div class="step-no">{number}</div>
              <h3>{title}</h3>
              <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

left, right = st.columns([1.05, 0.95], gap="large")
with left:
    st.subheader("Evidence base")
    for source in overview["sources"]:
        st.markdown(f'<div class="source-card"><p>{source}</p></div>', unsafe_allow_html=True)

with right:
    st.subheader("What this project can—and cannot—say")
    st.write(
        "The analysis compares aggregate changes between rounds and tests whether a transparent "
        "department-level estimate can explain the national balance."
    )
    st.markdown(
        '<div class="limitation"><strong>Key limitation</strong><br>'
        f"{research['principal_limitation']}</div>",
        unsafe_allow_html=True,
    )

st.divider()
st.caption("Victor Henz · Edgar Gusching · Louis Bettelli · Lucas Magret Delord · Oscar Moulet")
