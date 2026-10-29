"""Choose home shelves from explicit favorites, viewing history, or catalog coverage."""

from collections import Counter


def choose_genre_shelves(engine, profile, favorites, limit=5):
    watched = Counter()
    for movie_id in profile:
        watched.update(genre for genre in engine.genre_sets[engine.index[movie_id]] if genre != "IMAX")
    if favorites:
        return "favorites", [{"genre": genre, "watchedCount": watched[genre]}
                             for genre in favorites[:limit]]
    if watched:
        ordered = sorted(watched, key=lambda genre: (-watched[genre], genre))[:limit]
        return "history", [{"genre": genre, "watchedCount": watched[genre]} for genre in ordered]
    catalog = Counter(genre for genres in engine.genre_sets for genre in genres if genre != "IMAX")
    ordered = sorted(catalog, key=lambda genre: (-catalog[genre], genre))[:3]
    return "catalog", [{"genre": genre, "watchedCount": 0} for genre in ordered]
