import numpy as np
import pandas as pd
import pytest

from cinematch.data import read_data, temporal_split
from cinematch.evaluate import evaluate, ranking_metrics
from cinematch.model import Recommender


def test_cleaning_removes_invalid_rows_and_latest_duplicate(frames, tmp_path):
    movies, ratings = frames
    movies.to_csv(tmp_path / "movies.csv", index=False)
    extra = pd.DataFrame([
        [1, 1, 3., 999], [99, 999, 5., 9], [1, 2, 9., 10], [1, 3, np.nan, 11],
        [1, 4, 3.2, 12], [1.2, 1, 5., 13],
    ], columns=ratings.columns)
    pd.concat([ratings, extra]).to_csv(tmp_path / "ratings.csv", index=False)
    _, cleaned, report = read_data(tmp_path)
    assert report["invalid_rows_removed"] == 5
    assert report["duplicate_pairs_removed"] == 1
    assert cleaned[(cleaned.userId == 1) & (cleaned.movieId == 1)].iloc[0].rating == 3


def test_global_time_windows_never_share_timestamps():
    rows = pd.DataFrame({"timestamp": np.repeat(np.arange(20), 4), "rating": 5})
    train, val, test = temporal_split(rows)
    assert train.timestamp.max() < val.timestamp.min()
    assert val.timestamp.max() < test.timestamp.min()
    assert len(train) + len(val) + len(test) == len(rows)


def test_metrics_against_hand_computed_ranking():
    metrics = ranking_metrics([9, 2, 3], {2, 3}, 3)
    assert metrics["precision"] == pytest.approx(2/3)
    assert metrics["recall"] == 1
    assert metrics["ndcg"] == pytest.approx((1/np.log2(3)+.5)/(1+1/np.log2(3)))
    assert metrics["hit_rate"] == 1


def test_heldout_ratings_cannot_change_train_model(frames):
    movies, ratings = frames
    train, _, test = temporal_split(ratings)
    engine = Recommender.fit(movies, train)
    test.loc[:, "rating"] = .5
    again = Recommender.fit(movies, train)
    assert (engine.interactions != again.interactions).nnz == 0
    assert engine.movies.equals(again.movies)
    assert engine.metadata["training_max_timestamp"] < int(test.timestamp.min())


def test_evaluation_excludes_cold_users_and_seen_items(frames, model):
    _, history = frames
    heldout = pd.DataFrame([[1,8,5,1000],[99,8,5,1000],[2,1,5,1000]],
                          columns=history.columns)
    summary, users = evaluate(model, history, heldout, "popular", k=2)
    assert summary["evaluated_users"] == 1
    assert summary["excluded_users"] == 2
    assert users.userId.tolist() == [1]


def test_bad_schema_and_no_distinct_time_windows_raise(tmp_path):
    pd.DataFrame({"wrong":[1]}).to_csv(tmp_path / "movies.csv", index=False)
    pd.DataFrame({"wrong":[1]}).to_csv(tmp_path / "ratings.csv", index=False)
    with pytest.raises(ValueError, match="movies.csv"):
        read_data(tmp_path)
    with pytest.raises(ValueError, match="distinct"):
        temporal_split(pd.DataFrame({"timestamp":[1,1,1]}))
