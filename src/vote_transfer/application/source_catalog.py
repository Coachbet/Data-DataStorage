"""Single, human-readable catalogue of project data sources."""

from vote_transfer.domain.data_source import AccessMethod, DataSource

SOURCES: tuple[DataSource, ...] = (
    DataSource(
        key="elections",
        name="Résultats électoraux consolidés",
        provider="data.gouv.fr / Ministère de l'Intérieur",
        purpose="Résultats généraux et par candidat, par bureau de vote, de 2002 à 2022.",
        landing_url="https://www.data.gouv.fr/datasets/donnees-des-elections-agregees",
        access_method=AccessMethod.DATAGOUV_DATASET,
        dataset_slug="donnees-des-elections-agregees",
        raw_directory="elections",
        preferred_format="parquet",
        title_contains=("Résultats généraux", "Résultats par candidat"),
        notes="Source principale. Filtrer les identifiants *_pres_t1 et *_pres_t2.",
    ),
    DataSource(
        key="presidentielle_2022_reference",
        name="Présidentielle 2022 - résultats officiels du second tour",
        provider="Ministère de l'Intérieur",
        purpose="Contrôle ponctuel des valeurs 2022 publiées dans la base consolidée.",
        landing_url=(
            "https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-"
            "avril-2022-resultats-definitifs-du-2nd-tour"
        ),
        access_method=AccessMethod.REFERENCE_ONLY,
        raw_directory="elections/reference_2022",
        notes=(
            "Non téléchargée en masse : les mêmes données figurent déjà dans la source principale."
        ),
        core=False,
    ),
    DataSource(
        key="cog",
        name="Code officiel géographique 2026",
        provider="INSEE",
        purpose="Harmoniser les codes des communes, départements et régions.",
        landing_url="https://www.insee.fr/fr/information/8740222",
        access_method=AccessMethod.INSEE_DOWNLOAD_PAGE,
        raw_directory="geography/cog_2026",
        preferred_format="zip",
        title_contains=("Ensemble des fichiers 2026",),
        notes="Le millésime doit être enregistré car les périmètres communaux évoluent.",
    ),
    DataSource(
        key="geo_api",
        name="Découpage administratif",
        provider="Etalab",
        purpose="Snapshot léger des départements utilisé pour les contrôles et libellés.",
        landing_url="https://geo.api.gouv.fr/decoupage-administratif",
        access_method=AccessMethod.JSON_API,
        raw_directory="geography/geo_api",
        endpoint="https://geo.api.gouv.fr/departements?fields=nom,code,codeRegion",
        preferred_format="json",
        notes="Le COG reste la référence historique; cette API simplifie les contrôles courants.",
    ),
    DataSource(
        key="contours",
        name="Contours administratifs",
        provider="Etalab",
        purpose="Géométries GeoJSON nécessaires aux cartes départementales Streamlit.",
        landing_url="https://www.data.gouv.fr/datasets/contours-administratifs",
        access_method=AccessMethod.DATAGOUV_DATASET,
        dataset_slug="contours-administratifs",
        raw_directory="geography/contours",
        preferred_format="geojson",
        title_contains=("Départements 2025 1000m (format GeoJSON)",),
        notes="Une géométrie simplifiée est préférable pour l'affichage web.",
    ),
    DataSource(
        key="reu",
        name="Table des bureaux de vote du REU",
        provider="INSEE",
        purpose="Rapprocher les identifiants de bureaux de vote et les territoires.",
        landing_url=(
            "https://www.data.gouv.fr/datasets/bureaux-de-vote-et-adresses-de-leurs-electeurs"
        ),
        access_method=AccessMethod.DATAGOUV_DATASET,
        dataset_slug="bureaux-de-vote-et-adresses-de-leurs-electeurs",
        raw_directory="geography/reu",
        preferred_format="parquet",
        title_contains=("table-bv-reu.parquet",),
        notes="Télécharger la table des bureaux, pas les adresses individuelles volumineuses.",
    ),
    DataSource(
        key="insee_local",
        name="Base du dossier complet",
        provider="INSEE",
        purpose="Indicateurs territoriaux sur population, emploi, revenus et urbanité.",
        landing_url="https://www.insee.fr/fr/statistiques/5359146",
        access_method=AccessMethod.INSEE_DOWNLOAD_PAGE,
        raw_directory="context/insee_local",
        preferred_format="zip",
        title_contains=("dossier_complet_31_12_2025",),
        notes="Ne conserver ensuite que les variables justifiées par la question.",
    ),
    DataSource(
        key="filosofi",
        name="Filosofi - revenus et pauvreté",
        provider="INSEE",
        purpose="Niveau de vie médian et pauvreté au niveau départemental.",
        landing_url="https://www.insee.fr/fr/statistiques/8984752",
        access_method=AccessMethod.INSEE_DOWNLOAD_PAGE,
        raw_directory="context/filosofi",
        preferred_format="zip",
        title_contains=("FILOSOFI_CC_csv",),
        notes="Respecter le millésime et les limites liées au secret statistique.",
    ),
    DataSource(
        key="unemployment",
        name="Taux de chômage localisés",
        provider="INSEE",
        purpose="Série départementale de chômage utilisée comme indicateur contextuel.",
        landing_url="https://www.insee.fr/fr/statistiques/2012804",
        access_method=AccessMethod.INSEE_DOWNLOAD_PAGE,
        raw_directory="context/unemployment",
        preferred_format="xls",
        title_contains=("série longue depuis 1982",),
        notes="Choisir une période cohérente avec chaque élection, sans valeur future.",
    ),
    DataSource(
        key="gdelt",
        name="Mentions médiatiques GDELT",
        provider="The GDELT Project",
        purpose="Extension expérimentale sur l'attention médiatique régionale.",
        landing_url="https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/",
        access_method=AccessMethod.PARAMETERIZED_API,
        raw_directory="media/gdelt",
        endpoint="https://api.gdeltproject.org/api/v2/doc/doc",
        preferred_format="json",
        notes="À lancer seulement avec candidats, période et médias définis; couverture à valider.",
        core=False,
    ),
)


def get_source(key: str) -> DataSource:
    """Return one source by stable key."""

    for source in SOURCES:
        if source.key == key:
            return source
    valid = ", ".join(source.key for source in SOURCES)
    raise KeyError(f"Source inconnue: {key}. Valeurs possibles: {valid}")
