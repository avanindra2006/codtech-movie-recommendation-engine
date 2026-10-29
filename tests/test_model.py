import numpy as np
import pandas as pd
import pytest

from cinematch.model import Recommender


def test_content_finds_shared_genres_and_excludes_every_rated_movie(model):
    rows = model.recommend({1: 5, 3: 1, 8: 3}, mode="content", k=3, diversity=0)
    assert rows[0]["movieId"] == 2
    assert not {1, 3, 8} & {row["movieId"] for row in rows}
    assert "Orbit" in rows[0]["reason"]


def test_low_rating_reduces_content_signal(model):
    _, positive = model.components({1:5})
    _, mixed = model.components({1:5, 3:1})
    assert mixed[model.index[4]] <= positive[model.index[4]]


def test_round_trip_preserves_ranking_without_pickle(model, tmp_path):
    model.save(tmp_path)
    loaded = Recommender.load(tmp_path)
    assert model.recommend({1:5}, k=5) == loaded.recommend({1:5}, k=5)
    assert not list(tmp_path.glob("*.pkl"))


def test_filters_and_cold_start(model):
    rows = model.recommend({}, genre="Sci-Fi", year_min=2002, k=5)
    assert [row["movieId"] for row in rows] == [2]
    assert model.recommend({}, year_min=2099) == []
    assert model.recommend({1:1}, k=3, diversity=0) == model.recommend(
        {1:3}, k=3, diversity=0
    )


def test_collaborative_patterns_and_unrated_movies(model):
    collaborative, _ = model.components({1:5})
    assert collaborative[model.index[2]] > collaborative[model.index[4]]
    assert collaborative[model.index[8]] == 0
    assert np.isfinite(collaborative).all()


def test_mmr_and_ranking_are_repeatable(model):
    a = model.recommend({1:5}, k=7, diversity=.5)
    assert a == model.recommend({1:5}, k=7, diversity=.5)
    assert len({row["movieId"] for row in a}) == len(a)
    assert len(a) == 7


@pytest.mark.parametrize("profile", [{999:5}, {1:float("nan")}, {1:6}, {1:0}])
def test_invalid_profile_rejected(model, profile):
    with pytest.raises(ValueError):
        model.recommend(profile)


def test_no_positive_training_interactions_still_serves_content(frames):
    movies, ratings = frames
    ratings["rating"] = 2.
    engine = Recommender.fit(movies, ratings)
    assert engine.recommend({1:5}, k=1, mode="content")[0]["movieId"] == 2


@pytest.mark.parametrize("diversity", [0, .15, .5])
def test_pagination_is_stable_and_never_repeats_movies(model, diversity):
    all_rows=model.recommend({1:5}, k=7, diversity=diversity)
    first=model.recommend({1:5}, k=3, offset=0, diversity=diversity)
    second=model.recommend({1:5}, k=3, offset=3, diversity=diversity)
    last=model.recommend({1:5}, k=3, offset=6, diversity=diversity)
    assert first + second + last == all_rows
    assert len({r["movieId"] for r in first+second+last}) == 7
    assert model.recommend({}, offset=1000) == []


def test_favorite_genres_boost_matching_films_without_excluding_other_genres(model):
    _, original, _, _=model.rank({}, k=8, diversity=0)
    _, boosted, _, _=model.rank({}, k=8, diversity=0, favorite_genres=["Sci-Fi"])
    assert boosted[0] > .8 * original[0]
    assert boosted[2] == pytest.approx(.8 * original[2])
    rows=model.recommend({}, k=8, favorite_genres=["Sci-Fi"])
    assert len(rows)==8
    assert any("Your favorite Sci-Fi" in row["reason"] for row in rows)
    with pytest.raises(ValueError, match="favorite genre"):
        model.rank({}, favorite_genres=["Invented"])


def test_pagination_crosses_diversity_shortlist_boundary(frames):
    movies, ratings=frames
    extras=pd.DataFrame({"movieId":range(100,380),
                         "title":[f"New film {i} (2005)" for i in range(280)],
                         "genres":["Drama" if i%2 else "Sci-Fi" for i in range(280)]})
    engine=Recommender.fit(pd.concat([movies,extras],ignore_index=True),ratings)
    combined=engine.recommend({},offset=240,k=30)
    pages=sum([engine.recommend({},offset=offset,k=10) for offset in [240,250,260]],[])
    assert pages == combined
    assert len({row["movieId"] for row in pages}) == 30
