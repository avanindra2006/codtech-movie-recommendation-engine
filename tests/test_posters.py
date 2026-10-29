import csv

from fastapi.testclient import TestClient

from cinematch.api import create_app
from cinematch.posters import PosterCatalog


def write_catalog(directory):
    (directory / "movies.csv").write_text(
        "movieId,title,genres\n1,Orbit (2001),Sci-Fi\n2,Moon (2002),Sci-Fi\n", encoding="utf-8"
    )
    with (directory / "links.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerows([["movieId", "imdbId", "tmdbId"], [1, "0133093", 603],
                         [2, "https://untrusted.example/poster", 0]])


def test_poster_mapping_preserves_leading_zeroes_and_rejects_mismatches(tmp_path):
    write_catalog(tmp_path)
    posters = PosterCatalog.load(tmp_path)
    assert posters.url(1, "Orbit (2001)") == (
        "https://images.metahub.space/poster/medium/tt0133093/img"
    )
    assert posters.url(1, "Unrelated demo movie") is None
    assert posters.url(2, "Moon (2002)") is None
    assert PosterCatalog.load(tmp_path / "absent").url(1, "Orbit (2001)") is None


def test_poster_endpoint_redirects_only_matched_catalog_ids(model, tmp_path):
    write_catalog(tmp_path)
    with TestClient(create_app(model=model, poster_data=tmp_path)) as client:
        response = client.get("/api/movies/1/poster", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"].endswith("/tt0133093/img")
        assert response.headers["cache-control"] == "public, max-age=86400"
        assert client.get("/api/movies/2/poster").status_code == 404
        assert client.get("/api/movies/999/poster").status_code == 404
