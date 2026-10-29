import pandas as pd
import pytest

from cinematch.model import Recommender


@pytest.fixture
def frames():
    movies = pd.DataFrame({
        "movieId": [1, 2, 3, 4, 5, 6, 7, 8],
        "title": ["Orbit (2001)", "Moon (2002)", "Garden (1995)", "Meadow (1998)",
                  "Chase (2010)", "Flight (2012)", "Silent (2013)", "Unknown year"],
        "genres": ["Sci-Fi|Adventure", "Sci-Fi|Adventure", "Romance|Drama", "Romance|Drama",
                   "Action|Thriller", "Action|Adventure", "Drama", "(no genres listed)"],
    })
    rows = []
    for uid, ids in [(1,[1,2,5,6,7,3]), (2,[1,2,5,6,7,4]), (3,[3,4,7,5,6,1]),
                     (4,[1,2,6,5,7,3]), (5,[3,4,7,5,1,2])]:
        for position, mid in enumerate(ids):
            rows.append([uid, mid, 4.5 if position < 5 else 2., uid*100+position])
    ratings = pd.DataFrame(rows, columns=["userId", "movieId", "rating", "timestamp"])
    return movies, ratings


@pytest.fixture
def model(frames):
    return Recommender.fit(*frames)
