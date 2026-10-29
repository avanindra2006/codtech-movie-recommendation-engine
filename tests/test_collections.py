from fastapi.testclient import TestClient

from cinematch.api import create_app
from cinematch.collections import choose_genre_shelves


def test_favorites_choose_the_shelf_order(model):
    source, shelves = choose_genre_shelves(model, {1:5,2:5,3:1}, ["Drama","Sci-Fi"])
    assert source == "favorites"
    assert [s["genre"] for s in shelves] == ["Drama","Sci-Fi"]
    assert shelves[1]["watchedCount"] == 2


def test_history_counts_every_watched_movie_and_breaks_ties_consistently(model):
    source, shelves = choose_genre_shelves(model, {1:5,2:1,3:4}, [])
    assert source == "history"
    assert [s["genre"] for s in shelves] == ["Adventure","Sci-Fi","Drama","Romance"]
    assert [s["watchedCount"] for s in shelves] == [2,2,1,1]


def test_new_viewer_uses_honest_catalog_fallback(model):
    source, shelves = choose_genre_shelves(model, {}, [])
    assert source == "catalog" and len(shelves) == 3
    assert all(s["watchedCount"] == 0 for s in shelves)


def test_watched_format_tag_is_not_inferred_as_a_genre(model):
    model.genre_sets[model.index[1]].add("IMAX")
    _, shelves = choose_genre_shelves(model, {1:5}, [])
    assert "IMAX" not in [s["genre"] for s in shelves]


def test_home_shelves_exclude_watched_movies_and_respect_genre(model):
    with TestClient(create_app(model=model)) as client:
        response = client.post("/api/home", json={"ratings":[{"movieId":1,"rating":5}],
                                                 "favorite_genres":["Sci-Fi"]})
        assert response.status_code == 200
        body=response.json()
        assert body["genreSource"] == "favorites"
        assert len(body["recommendations"]) <= 10
        assert all(movie["movieId"] != 1 for movie in body["recommendations"])
        assert [shelf["genre"] for shelf in body["genres"]] == ["Sci-Fi"]
        assert all("Sci-Fi" in movie["genres"] and movie["movieId"] != 1
                   for movie in body["genres"][0]["movies"])
        assert client.post("/api/home",json={"favorite_genres":["Invented"]}).status_code == 422
