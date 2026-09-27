"""Command-line entry point for understandable, selective data acquisition."""

import argparse
from pathlib import Path

from vote_transfer.application.source_catalog import SOURCES, get_source
from vote_transfer.domain.data_source import AccessMethod
from vote_transfer.infrastructure.acquisition import download_source, resolve_resources


def _size(value: int | None) -> str:
    if value is None:
        return "taille inconnue"
    return f"{value / 1_000_000:.1f} Mo"


def _print_catalog() -> None:
    print("Sources disponibles\n")
    for source in SOURCES:
        role = "principale" if source.core else "optionnelle / contrôle"
        print(f"- {source.key}: {source.name} [{role}]")
        print(f"  Utilité: {source.purpose}")
        print(f"  Accès: {source.access_method}")
        print(f"  Page: {source.landing_url}")
        print(f"  Note: {source.notes}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Résout ou télécharge les sources documentées du projet."
    )
    parser.add_argument("--list", action="store_true", help="afficher le catalogue des sources")
    parser.add_argument("--source", help="clé d'une source, ou 'core' pour les sources principales")
    parser.add_argument(
        "--download",
        action="store_true",
        help="télécharger réellement; sans cette option, aucun fichier n'est écrit",
    )
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()

    if args.list or not args.source:
        _print_catalog()
        if not args.source:
            return

    selected = (
        [source for source in SOURCES if source.core]
        if args.source == "core"
        else [get_source(args.source)]
    )
    for source in selected:
        print(f"\n{source.name}")
        print(f"  But: {source.purpose}")
        if source.access_method in {AccessMethod.PARAMETERIZED_API, AccessMethod.REFERENCE_ONLY}:
            print(f"  Non téléchargée automatiquement: {source.notes}")
            continue
        resources = resolve_resources(source)
        for resource in resources:
            details = f"{resource.format}, {_size(resource.expected_size)}"
            print(f"  Ressource: {resource.title} ({details})")
            print(f"  URL stable: {resource.url}")
        if args.download:
            records = download_source(source, args.data_root)
            for record in records:
                print(f"  Enregistré: {record['saved_as']} ({_size(record['downloaded_bytes'])})")
                print(f"  SHA-256: {record['sha256']}")
        else:
            print("  Simulation uniquement. Ajouter --download pour écrire les fichiers.")


if __name__ == "__main__":
    main()
