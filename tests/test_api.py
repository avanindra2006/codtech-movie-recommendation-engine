import pytest
from fastapi.testclient import TestClient

from cinematch.api import create_app


@pytest.fixture
def client(model):
    with TestClient(create_app(model=model)) as test_client:
        yield test_client


def test_search_is_literal_and_health_and_stats_work(client):
    assert client.get("/api/health").json()["status"] == "ready"
    assert client.get("/api/stats").json()["movies"] == 8
    assert client.get("/api/movies?q=(2001)").json()["movies"][0]["movieId"] == 1
    assert client.get("/api/movies?q=[").json()["movies"] == []
    assert client.get("/api/movies/999").status_code == 404


def test_recommend_endpoint_handles_cold_and_warm_profiles(client):
    assert client.post("/api/recommend", json={}).json()["coldStart"] is True
    response = client.post("/api/recommend", json={"ratings":[{"movieId":1,"rating":5}],
                                                  "mode":"content", "diversity":0, "k":3})
    assert response.status_code == 200
    body = response.json()
    assert body["coldStart"] is False
    assert body["recommendations"][0]["movieId"] == 2


@pytest.mark.parametrize("payload", [
    {"ratings":[{"movieId":999,"rating":5}]},
    {"ratings":[{"movieId":1,"rating":5},{"movieId":1,"rating":1}]},
    {"ratings":[{"movieId":1,"rating":5.1}]},
    {"ratings":[{"movieId":1,"rating":3.2}]},
    {"k":1000}, {"diversity":1}, {"mode":"invented"},
    {"year_min":2010,"year_max":1990}, {"genre":"invented"}, {"extra":"unexpected"},
])
def test_invalid_requests_have_actionable_validation(client, payload):
    assert client.post("/api/recommend", json=payload).status_code == 422


def test_search_limits_are_bounded(client):
    assert client.get("/api/movies?limit=10000").status_code == 422
    assert client.get("/api/movies?q=" + "a"*101).status_code == 422


def test_missing_artifact_has_clear_startup_error(tmp_path):
    with pytest.raises(RuntimeError, match="cinematch train"):
        with TestClient(create_app(model_dir=tmp_path)):
            pass


def test_paged_recommendations_report_more_and_end(client):
    first=client.post("/api/recommend", json={"k":3}).json()
    second=client.post("/api/recommend", json={"k":3,"offset":first["nextOffset"]}).json()
    last=client.post("/api/recommend", json={"k":3,"offset":second["nextOffset"]}).json()
    assert first["hasMore"] and second["hasMore"]
    assert last["hasMore"] is False and last["count"]==2
    ids=[r["movieId"] for page in [first,second,last] for r in page["recommendations"]]
    assert len(ids)==len(set(ids))==8


@pytest.mark.parametrize("payload", [
    {"offset":-1}, {"favorite_genres":["Invented"]},
    {"favorite_genres":["Drama","Drama"]},
    {"favorite_genres":["Drama"]*6},
])
def test_invalid_pagination_and_favorites_are_rejected(client,payload):
    assert client.post("/api/recommend", json=payload).status_code == 422
