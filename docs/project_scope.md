# Project scope

## Approved direction

The project investigates aggregate second-round vote transfers in French
presidential elections. The applied output is an explorer for hypothetical 2027
finalists, with results presented by department and aggregated nationally.

## Scope guardrails from teacher feedback

- Begin with the central question and retain only variables required to answer it.
- Keep every analysis tied to the same investigation.
- Operationalise terms such as *transfer*, *abstention*, *bloc* and *estimate*.
- Prefer a smaller, justified evidence base over unrelated additional datasets.
- Inspect feasibility and data quality before choosing sophisticated methods.
- Do not use advanced statistics or machine learning without teacher approval.

## Current source priority

1. Official first- and second-round presidential election results.
2. Official geographic identifiers needed to harmonise communes and departments.
3. Contextual indicators only when a stated analytical need justifies them.

Regional media attention remains a possible extension, not a core dependency,
until its relevance, coverage and acquisition feasibility are demonstrated.

## Architectural boundaries

- **Domain:** election concepts, definitions and validation rules.
- **Application:** collection, cleaning, storage and analysis use cases.
- **Infrastructure:** data.gouv.fr/INSEE clients, files and database adapters.
- **Presentation:** the Streamlit app, written report and group presentation.
