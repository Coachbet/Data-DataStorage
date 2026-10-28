import json

import pytest
from vote_transfer.infrastructure.official import acquire_official


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
                            "id": str(number),
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
