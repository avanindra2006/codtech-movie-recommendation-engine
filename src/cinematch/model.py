"""Sparse, explainable item-neighbor and content hybrid; no pickle deserialization."""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


def genre_list(value):
    return [g for g in str(value).split("|") if g and g != "(no genres listed)"]


class Recommender:
    def __init__(self, movies, content, interactions, metadata):
        self.movies = movies.reset_index(drop=True)
        self.content = content.tocsr()
        self.interactions = interactions.tocsr()
        self.metadata = metadata
        self.ids = self.movies.movieId.to_numpy(dtype=int)
        self.index = {int(mid): i for i, mid in enumerate(self.ids)}
        self.popularity = self.movies.popularity.to_numpy(dtype=float)
        self.genre_sets = [set(genre_list(g)) for g in self.movies.genres]

    @classmethod
    def fit(cls, movies, ratings, alpha=.6):
        catalog = movies.copy().reset_index(drop=True)
        lookup = {mid: i for i, mid in enumerate(catalog.movieId)}
        documents = []
        for row in catalog.itertuples():
            genres = ["g_" + re.sub(r"\W", "", g.lower()) for g in genre_list(row.genres)]
            title = re.sub(r"\(\d{4}\)", "", row.title)
            words = ["t_" + w for w in re.findall(r"\w{2,}", title.lower())]
            documents.append(" ".join(genres * 3 + words + ["catalog"]))
        # Metadata is static. No user tags or held-out ratings enter this representation.
        vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", dtype=np.float32)
        content = vectorizer.fit_transform(documents)
        positive = ratings[ratings.rating >= 4].copy()
        users = sorted(ratings.userId.unique())
        user_lookup = {uid: i for i, uid in enumerate(users)}
        activity = positive.groupby("userId").size()
        weights = (positive.rating.to_numpy() - 3) / np.sqrt(
            positive.userId.map(activity).to_numpy()
        )
        interactions = sparse.csr_matrix((weights, (
            positive.movieId.map(lookup).to_numpy(), positive.userId.map(user_lookup).to_numpy()
        )), shape=(len(catalog), len(users)), dtype=np.float32)
        interactions = normalize(interactions)
        stats = ratings.groupby("movieId").rating.agg(["mean", "count"])
        catalog["rating_count"] = catalog.movieId.map(stats["count"]).fillna(0).astype(int)
        catalog["mean_rating"] = catalog.movieId.map(stats["mean"]).fillna(0)
        prior = float(ratings.rating.mean())
        counts = catalog.rating_count.to_numpy()
        bayesian = (counts * catalog.mean_rating.to_numpy() + 20 * prior) / (counts + 20)
        # Shrink small samples to the global mean and combine quality with engagement.
        activity_score = np.log1p(counts) / max(float(np.log1p(counts).max()), 1)
        catalog["popularity"] = .7 * activity_score + .3 * bayesian / 5
        catalog["year"] = pd.to_numeric(
            catalog.title.str.extract(r"\((\d{4})\)\s*$", expand=False), errors="coerce"
        ).fillna(0).astype(int)
        metadata = {
            "format_version": 1, "alpha": float(alpha), "popularity_weight": .1,
            "positive_threshold": 4, "training_ratings": len(ratings),
            "training_users": len(users), "training_max_timestamp": int(ratings.timestamp.max()),
            "features": vectorizer.get_feature_names_out().tolist(),
            "method": "activity-weighted positive item cosine + TF-IDF + Bayesian popularity",
        }
        return cls(catalog, content, interactions, metadata)

    def save(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.movies.to_csv(directory / "movies.csv", index=False)
        sparse.save_npz(directory / "content.npz", self.content)
        sparse.save_npz(directory / "interactions.npz", self.interactions)
        (directory / "config.json").write_text(json.dumps(self.metadata, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, directory: Path):
        metadata = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        if metadata.get("format_version") != 1:
            raise ValueError("Unsupported artifact format; retrain with this version")
        model = cls(pd.read_csv(directory / "movies.csv"),
                    sparse.load_npz(directory / "content.npz"),
                    sparse.load_npz(directory / "interactions.npz"), metadata)
        if model.content.shape[0] != len(model.ids) or model.interactions.shape[0] != len(model.ids):
            raise ValueError("Artifact matrix and catalog sizes do not match")
        return model

    def components(self, profile):
        """Profile is {movieId: explicit 0.5..5 rating}; neutral ratings only exclude items."""
        indices, weights = [], []
        for movie_id, rating in profile.items():
            if movie_id not in self.index:
                raise ValueError(f"Unknown movie ID: {movie_id}")
            if not np.isfinite(rating) or not .5 <= rating <= 5:
                raise ValueError("Ratings must be finite and between 0.5 and 5")
            indices.append(self.index[movie_id])
            weights.append(rating - 3)
        n = len(self.ids)
        if not indices or not any(w > 0 for w in weights):
            return np.zeros(n), np.zeros(n)
        weights = np.asarray(weights, dtype=np.float32)
        weights /= max(float(np.abs(weights).sum()), 1)
        result = []
        for matrix in [self.interactions, self.content]:
            query = sparse.csr_matrix(weights.reshape(1, -1)) @ matrix[indices]
            values = (matrix @ query.T).toarray().ravel()
            values = np.maximum(values, 0)
            result.append(values / max(float(values.max()), 1e-8))
        return tuple(result)

    def rank(self, profile, k=10, mode="hybrid", alpha=None, diversity=.15,
             genre=None, year_min=None, year_max=None, min_ratings=0,
             favorite_genres=None, offset=0, lookahead=False):
        if mode not in {"hybrid", "content", "collaborative", "popular"}:
            raise ValueError("Unknown recommendation mode")
        if not 1 <= k <= 30 or not 0 <= diversity <= .7:
            raise ValueError("Invalid result count or diversity")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be a nonnegative integer")
        favorites = set(favorite_genres or [])
        known_genres = {g for genres in self.genre_sets for g in genres}
        if not favorites.issubset(known_genres):
            raise ValueError("Unknown favorite genre")
        collaborative, content = self.components(profile)
        alpha = self.metadata["alpha"] if alpha is None else alpha
        if not 0 <= alpha <= 1:
            raise ValueError("alpha must be in [0, 1]")
        if mode == "popular" or not any(r > 3 for r in profile.values()):
            scores = self.popularity.copy()
        elif mode == "content":
            scores = .9 * content + .1 * self.popularity
        elif mode == "collaborative":
            scores = .9 * collaborative + .1 * self.popularity
        else:
            scores = .9 * (alpha * collaborative + (1 - alpha) * content) + .1 * self.popularity
        if favorites:
            affinity = np.array([len(gs & favorites) / max(len(gs), 1) for gs in self.genre_sets])
            scores = .8 * scores + .2 * affinity
        mask = ~np.isin(self.ids, list(profile))
        mask &= self.movies.rating_count.to_numpy() >= min_ratings
        if genre:
            mask &= np.array([genre in gs for gs in self.genre_sets])
        if year_min is not None:
            mask &= self.movies.year.to_numpy() >= year_min
        if year_max is not None:
            mask &= (self.movies.year.to_numpy() > 0) & (self.movies.year.to_numpy() <= year_max)
        candidates = np.flatnonzero(mask)
        ordered = candidates[np.lexsort((self.ids[candidates], -scores[candidates]))]
        end = offset + k + int(lookahead)
        if not diversity or len(ordered) <= 1:
            chosen = ordered[offset:end]
        else:
            # Rerank one fixed prefix so page size never changes previously displayed results.
            # Beyond that prefix, continue in base-score order without an N-by-N matrix.
            pool = ordered[:250]
            similarity = (self.content[pool] @ self.content[pool].T).toarray()
            selected = []
            remaining = np.ones(len(pool), dtype=bool)
            penalties = np.zeros(len(pool))
            for _ in range(min(end, len(pool))):
                objective = (1 - diversity) * scores[pool] - diversity * penalties
                best = int(np.argmax(np.where(remaining, objective, -np.inf)))
                selected.append(best)
                remaining[best] = False
                penalties = np.maximum(penalties, similarity[:, best])
            prefix = pool[selected]
            ranked = np.concatenate([prefix, ordered[250:]]) if end > 250 else prefix
            chosen = ranked[offset:end]
        return chosen, scores, collaborative, content

    def movie(self, index):
        row = self.movies.iloc[index]
        return {"movieId": int(row.movieId), "title": row.title,
                "genres": genre_list(row.genres), "year": int(row.year) or None,
                "meanRating": round(float(row.mean_rating), 2),
                "ratingCount": int(row.rating_count)}

    def recommend(self, profile, **kwargs):
        indices, scores, collaborative, content = self.rank(profile, **kwargs)
        liked = [(self.index[mid], rating) for mid, rating in profile.items() if rating > 3]
        results = []
        for index in indices:
            item = self.movie(index)
            reason = "Popular with MovieLens viewers"
            mode = kwargs.get("mode", "hybrid")
            if liked and mode != "popular":
                seed_indices = [j for j, _ in liked]
                affinity = (self.content[index] @ self.content[seed_indices].T).toarray().ravel()
                if mode in {"hybrid", "collaborative"}:
                    affinity += (self.interactions[index] @ self.interactions[seed_indices].T).toarray().ravel()
                best = int(np.argmax(affinity))
                if affinity[best] > 0:
                    reason = f"Related to {self.movies.iloc[seed_indices[best]].title}"
                    common = self.genre_sets[index] & self.genre_sets[seed_indices[best]]
                    if common:
                        reason += " · " + ", ".join(sorted(common)[:2])
            favorite_matches = self.genre_sets[index] & set(kwargs.get("favorite_genres") or [])
            if favorite_matches:
                reason = "Your favorite " + ", ".join(sorted(favorite_matches)) + " · " + reason
            item.update({"matchScore": round(float(scores[index]), 4), "reason": reason,
                         "signals": {"collaborative": round(float(collaborative[index]), 4),
                                     "content": round(float(content[index]), 4),
                                     "popularity": round(float(self.popularity[index]), 4)}})
            results.append(item)
        return results
