import json

import pytest
from vote_transfer.infrastructure.official import RESOURCE_IDS, acquire_official


class Response:
    def __init__(self, payload=None, content=b"", url="https://example.test/source"):
        self.payload, self.content, self.url = payload, content, url

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload

    def iter_content(self, _):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


class Session:
    def __init__(self, rounds):
        self.headers, self.calls, self.rounds = {}, [], rounds

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def get(self, url, **_):
        self.calls.append(url)
        number = 1 if "1er" in url or url.endswith("/1") else 2
        content = self.rounds[number]
        if "/datasets/" in url:
            return Response(
                {
                    "license": "notspecified",
                    "resources": [
                        {
                            "id": RESOURCE_IDS[2022, number],
                            "format": "txt",
                            "filesize": len(content),
                            "title": f"resultats-par-niveau-burvot-t{number}-france-entiere.txt",
                            "url": f"https://example.test/files/{number}",
                        }
                    ],
                }
            )
        return Response(content=content, url=url)


def test_verified_resume_preserves_original_provenance(raw_dataset, tmp_path, monkeypatch):
    rounds = {n: (raw_dataset / f"raw/official/2022/round_{n}.txt").read_bytes() for n in (1, 2)}
    session = Session(rounds)
    monkeypatch.setattr("vote_transfer.infrastructure.official.requests.Session", lambda: session)
    target = tmp_path / "download"
    first = acquire_official(2022, target)
    assert len(session.calls) == 4
    session.calls.clear()
    assert acquire_official(2022, target) == first
    assert not session.calls
    manifest = json.loads((target / "raw/official/2022/manifest.json").read_text())
    assert all(item["bytes"] and item["retrieved_at_utc"] for item in manifest["files"])


def test_modified_raw_file_is_not_overwritten(raw_dataset, monkeypatch):
    path = raw_dataset / "raw/official/2022/round_1.txt"
    path.write_bytes(b"modified")
    session = Session({})
    monkeypatch.setattr("vote_transfer.infrastructure.official.requests.Session", lambda: session)
    with pytest.raises(ValueError, match="Unverified"):
        acquire_official(2022, raw_dataset)
    assert path.read_bytes() == b"modified"
    assert not session.calls


def test_historical_shared_file_is_downloaded_only_once(tmp_path, monkeypatch):
    content = b"1;01;001;Synthetic;0001;100;80;75;1;ALPHA;Test;X;75\n"

    class HistoricalSession(Session):
        def get(self, url, **kwargs):
            self.calls.append(url)
            if "/datasets/" in url:
                return Response(
                    {
                        "license": "fr-lo",
                        "resources": [
                            {
                                "id": RESOURCE_IDS[2002, 1],
                                "format": "txt",
                                "title": "PR02_BVot_T1T2.txt",
                                "url": "https://example.test/both_rounds",
                                "filesize": len(content),
                            }
                        ],
                    }
                )
            return Response(content=content, url=url)

    session = HistoricalSession({})
    monkeypatch.setattr("vote_transfer.infrastructure.official.requests.Session", lambda: session)
    manifest = acquire_official(2002, tmp_path)
    assert len(session.calls) == 2  # One dataset metadata request and one download.
    assert len(manifest["files"]) == 2
    assert {r["file"] for r in manifest["files"]} == {"both_rounds.txt"}
    assert len({r["sha256"] for r in manifest["files"]}) == 1
    session.calls.clear()
    assert acquire_official(2002, tmp_path) == manifest
    assert session.calls == []


def test_fresh_download_must_match_pinned_manifest(raw_dataset, tmp_path, monkeypatch):
    rounds = {n: (raw_dataset / f"raw/official/2022/round_{n}.txt").read_bytes() for n in (1, 2)}
    session = Session(rounds)
    monkeypatch.setattr("vote_transfer.infrastructure.official.requests.Session", lambda: session)
    target = tmp_path / "clone"
    pinned = acquire_official(2022, target)
    folder = target / "raw/official/2022"
    # A fresh clone has the versioned manifest but no raw bytes yet.
    for n in (1, 2):
        (folder / f"round_{n}.txt").unlink()
    assert acquire_official(2022, target) == pinned  # Original provenance is retained.
    (folder / "round_1.txt").unlink()
    session.rounds[1] = rounds[1] + b"replaced upstream\n"
    with pytest.raises(ValueError, match="pinned checksum"):
        acquire_official(2022, target)
    assert not (folder / "round_1.txt").exists()
    assert json.loads((folder / "manifest.json").read_text()) == pinned


def test_replacement_resource_is_not_substituted(raw_dataset, tmp_path, monkeypatch):
    rounds = {n: (raw_dataset / f"raw/official/2022/round_{n}.txt").read_bytes() for n in (1, 2)}

    class ReplacedSession(Session):
        def get(self, url, **kwargs):
            response = super().get(url, **kwargs)
            if "/datasets/" in url:
                response.payload["resources"][0]["id"] = "replacement-resource"
            return response

    session = ReplacedSession(rounds)
    monkeypatch.setattr("vote_transfer.infrastructure.official.requests.Session", lambda: session)
    with pytest.raises(ValueError, match="exactly one"):
        acquire_official(2022, tmp_path / "fresh")
    assert len(session.calls) == 1  # Metadata only; nothing downloaded.
