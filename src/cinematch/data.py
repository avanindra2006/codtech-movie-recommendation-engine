"""Validate movie metadata and ratings before any model fitting."""

from pathlib import Path

import numpy as np
import pandas as pd


def read_data(directory: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    movies = pd.read_csv(directory / "movies.csv")
    ratings = pd.read_csv(directory / "ratings.csv")
    if not {"movieId", "title", "genres"}.issubset(movies.columns):
        raise ValueError("movies.csv requires movieId,title,genres")
    if not {"userId", "movieId", "rating", "timestamp"}.issubset(ratings.columns):
        raise ValueError("ratings.csv requires userId,movieId,rating,timestamp")
    initial = len(ratings)
    movies = movies[["movieId", "title", "genres"]].copy()
    movies["movieId"] = pd.to_numeric(movies.movieId, errors="raise")
    if (movies.movieId <= 0).any() or (movies.movieId % 1 != 0).any():
        raise ValueError("Movie IDs must be positive integers")
    movies["movieId"] = movies.movieId.astype(int)
    if movies.movieId.duplicated().any() or movies.title.isna().any():
        raise ValueError("Movie IDs must be unique and titles must be present")
    movies["genres"] = movies.genres.fillna("(no genres listed)")
    for column in ["userId", "movieId", "rating", "timestamp"]:
        ratings[column] = pd.to_numeric(ratings[column], errors="coerce")
    valid = np.isfinite(ratings[["userId", "movieId", "rating", "timestamp"]]).all(axis=1)
    valid &= ratings.rating.between(0.5, 5) & (ratings.rating * 2 % 1 == 0)
    valid &= (ratings.userId > 0) & (ratings.userId % 1 == 0)
    valid &= (ratings.movieId % 1 == 0) & ratings.movieId.isin(movies.movieId)
    valid &= (ratings.timestamp >= 0) & (ratings.timestamp % 1 == 0)
    ratings = ratings.loc[valid].copy()
    invalid = initial - len(ratings)
    # Keep the latest opinion per user/movie before splitting; ties keep the last source row.
    ratings = ratings.sort_values("timestamp", kind="stable").drop_duplicates(
        ["userId", "movieId"], keep="last"
    )
    for column in ["userId", "movieId", "timestamp"]:
        ratings[column] = ratings[column].astype("int64")
    if ratings.empty or movies.empty:
        raise ValueError("No valid movies or ratings remain after cleaning")
    report = {
        "input_ratings": initial, "invalid_rows_removed": invalid,
        "duplicate_pairs_removed": initial - invalid - len(ratings),
        "clean_ratings": len(ratings), "movies": len(movies),
        "users": int(ratings.userId.nunique()),
        "unrated_movies": int((~movies.movieId.isin(ratings.movieId)).sum()),
    }
    return movies.sort_values("movieId").reset_index(drop=True), ratings.reset_index(drop=True), report


def temporal_split(ratings: pd.DataFrame):
    """Global 70/15/15 time windows; equal timestamps never cross a boundary."""
    timestamps = ratings.timestamp.sort_values().to_numpy()
    first, second = timestamps[int(len(timestamps) * .7)], timestamps[int(len(timestamps) * .85)]
    train = ratings[ratings.timestamp < first].copy()
    validation = ratings[(ratings.timestamp >= first) & (ratings.timestamp < second)].copy()
    test = ratings[ratings.timestamp >= second].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("Need ratings at enough distinct times for three nonempty windows")
    return train, validation, test
