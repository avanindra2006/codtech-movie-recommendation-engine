from fastapi.testclient import TestClient

from cinematch.api import create_app
from cinematch.metadata import MovieMetadata, short_description


def test_synopsis_normalization_length_and_identity():
    text = short_description({"meta":{"id":"tt0133093", "description":"<b>A &amp; B</b>\n travel."}}, "tt0133093")
    assert text == "A & B travel."
    long = short_description({"meta":{"id":"tt0133093", "description":"A long journey. "*100}}, "tt0133093")
    assert len(long) <= 320 and long.endswith("…")
    assert short_description({"meta":{"id":"tt0000001","description":"Wrong film"}}, "tt0133093") is None
    assert short_description({"meta":None}, "tt0133093") is None


def test_metadata_success_and_failures_are_cached():
    calls=[]
    def fetch(imdb_id):
        calls.append(imdb_id)
        if imdb_id == "tt0000001":
            raise OSError("offline")
        return "A short movie description."
    service=MovieMetadata(fetcher=fetch)
    assert service.get("tt0133093") == service.get("tt0133093") == "A short movie description."
    assert calls == ["tt0133093"]
    assert service.get("tt0000001") is None
    assert service.get("tt0000001") is None
    assert service.get("https://elsewhere.example") is None
    assert calls == ["tt0133093", "tt0000001"]


def test_description_api_uses_matched_catalog_and_handles_missing_synopsis(model, tmp_path):
    (tmp_path/"movies.csv").write_text("movieId,title,genres\n1,Orbit (2001),Sci-Fi\n", encoding="utf-8")
    (tmp_path/"links.csv").write_text("movieId,imdbId,tmdbId\n1,0133093,603\n", encoding="utf-8")
    service=MovieMetadata(fetcher=lambda _: "A distant journey through space.")
    with TestClient(create_app(model=model, poster_data=tmp_path, metadata_service=service)) as client:
        body=client.get("/api/movies/1/description").json()
        assert body["description"] == "A distant journey through space."
        assert body["source"] == "Cinemeta" and body["available"] is True
        assert client.get("/api/movies/2/description").json()["available"] is False
        assert client.get("/api/movies/999/description").status_code == 404
