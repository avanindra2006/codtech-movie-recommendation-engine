"""Map the bundled catalog to public Cinemeta/MetaHub poster images, without API keys."""

import csv
import re
from pathlib import Path

POSTER_BASE = "https://images.metahub.space/poster/medium"


class PosterCatalog:
    def __init__(self, entries=None):
        self.entries = entries or {}

    @classmethod
    def load(cls, directory: Path):
        try:
            with (directory / "movies.csv").open(encoding="utf-8", newline="") as stream:
                titles = {row["movieId"]: row["title"] for row in csv.DictReader(stream)}
            entries = {}
            with (directory / "links.csv").open(encoding="utf-8", newline="") as stream:
                for row in csv.DictReader(stream):
                    imdb_id = row.get("imdbId", "").strip()
                    movie_id = row.get("movieId", "")
                    if re.fullmatch(r"\d{7,10}", imdb_id) and movie_id in titles:
                        entries[int(movie_id)] = (titles[movie_id], "tt" + imdb_id)
            return cls(entries)
        except (OSError, KeyError, ValueError):
            # Posters are optional: a missing link file must not stop recommendations.
            return cls()

    def imdb_id(self, movie_id: int, title: str):
        source = self.entries.get(movie_id)
        # Custom/demo models may reuse MovieLens numeric IDs for entirely different films.
        if source is None or source[0] != title:
            return None
        return source[1]

    def url(self, movie_id: int, title: str):
        imdb_id = self.imdb_id(movie_id, title)
        return f"{POSTER_BASE}/{imdb_id}/img" if imdb_id else None
