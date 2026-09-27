"""HTTP acquisition adapters with provenance manifests and safe file writes."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from vote_transfer.domain.data_source import AccessMethod, DataSource

USER_AGENT = "vote-transfer-student-project/0.1 (reproducible academic acquisition)"
CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True, slots=True)
class ResolvedResource:
    """A concrete file selected from a documented source."""

    title: str
    url: str
    format: str
    expected_size: int | None = None


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    return session


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def resolve_resources(source: DataSource) -> list[ResolvedResource]:
    """Resolve a catalogue entry without downloading its data files."""

    if source.access_method == AccessMethod.DATAGOUV_DATASET:
        return _resolve_datagouv(source)
    if source.access_method == AccessMethod.JSON_API:
        return [
            ResolvedResource(
                title=source.name,
                url=source.endpoint or source.landing_url,
                format=source.preferred_format or "json",
            )
        ]
    if source.access_method == AccessMethod.INSEE_DOWNLOAD_PAGE:
        return _resolve_insee_page(source)
    return []


def _resolve_datagouv(source: DataSource) -> list[ResolvedResource]:
    api_url = f"https://www.data.gouv.fr/api/1/datasets/{source.dataset_slug}/"
    response = _session().get(api_url, timeout=60)
    response.raise_for_status()
    resources = response.json().get("resources", [])
    wanted_titles = tuple(_normalized(value) for value in source.title_contains)
    matches = []
    for resource in resources:
        title = str(resource.get("title", ""))
        resource_format = str(resource.get("format") or "").casefold()
        title_match = not wanted_titles or any(
            value in _normalized(title) for value in wanted_titles
        )
        format_match = (
            not source.preferred_format
            or resource_format == source.preferred_format
            or (not resource_format and source.preferred_format in _normalized(title))
        )
        if title_match and format_match:
            matches.append(
                ResolvedResource(
                    title=title or source.name,
                    url=resource.get("latest") or resource["url"],
                    format=resource_format or source.preferred_format or "bin",
                    expected_size=resource.get("filesize"),
                )
            )
    if not matches:
        raise RuntimeError(f"Aucune ressource correspondant aux critères de {source.name}.")
    return matches


def _resolve_insee_page(source: DataSource) -> list[ResolvedResource]:
    response = _session().get(source.landing_url, timeout=60)
    response.raise_for_status()
    parser = _LinkParser()
    parser.feed(response.text)
    terms = tuple(_normalized(value) for value in source.title_contains)
    candidates: list[ResolvedResource] = []
    for href, label in parser.links:
        combined = _normalized(f"{label} {href}")
        suffix = Path(urlparse(href).path).suffix.casefold().lstrip(".")
        term_match = not terms or all(term in combined for term in terms)
        format_match = not source.preferred_format or suffix == source.preferred_format
        if term_match and format_match:
            candidates.append(
                ResolvedResource(
                    title=label or source.name,
                    url=urljoin(source.landing_url, href),
                    format=suffix or source.preferred_format or "bin",
                )
            )
    if not candidates:
        raise RuntimeError(
            f"Lien de téléchargement introuvable pour {source.name}. "
            "La page INSEE a peut-être changé; vérifier la page source."
        )
    return candidates[:1]


def download_source(source: DataSource, data_root: Path) -> list[dict[str, object]]:
    """Download resolved resources and write one provenance manifest."""

    resources = resolve_resources(source)
    destination = data_root / "raw" / source.raw_directory
    destination.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    session = _session()
    for index, resource in enumerate(resources, start=1):
        stem = re.sub(r"[^a-z0-9]+", "_", _normalized(resource.title)).strip("_")
        filename = f"{stem or source.key}_{index}.{resource.format}"
        target = destination / filename
        temporary = target.with_suffix(target.suffix + ".part")
        digest = hashlib.sha256()
        size = 0
        with session.get(resource.url, stream=True, timeout=(30, 300)) as response:
            response.raise_for_status()
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        output.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
        temporary.replace(target)
        records.append(
            {
                **asdict(resource),
                "saved_as": str(target),
                "downloaded_bytes": size,
                "sha256": digest.hexdigest(),
            }
        )
    manifest = {
        "source": asdict(source),
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "resources": records,
    }
    manifest_path = destination / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return records
