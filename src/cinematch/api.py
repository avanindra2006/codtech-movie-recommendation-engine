"""Local FastAPI service. Models load once, profiles remain in the browser."""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Annotated

from .cli import ROOT
from .model import Recommender, genre_list
from .posters import PosterCatalog
from .metadata import MovieMetadata
from .collections import choose_genre_shelves


class Preference(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    movieId: int = Field(gt=0)
    rating: float = Field(ge=.5, le=5, multiple_of=.5)


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    ratings: list[Preference] = Field(default_factory=list, max_length=100)
    k: int = Field(default=12, ge=1, le=30)
    mode: Literal["hybrid", "content", "collaborative", "popular"] = "hybrid"
    diversity: float = Field(default=.15, ge=0, le=.7)
    genre: str | None = Field(default=None, max_length=40)
    year_min: int | None = Field(default=None, ge=1870, le=2100)
    year_max: int | None = Field(default=None, ge=1870, le=2100)
    min_ratings: int = Field(default=0, ge=0, le=1_000_000)
    offset: int = Field(default=0, ge=0, le=100_000)
    favorite_genres: list[Annotated[str, Field(max_length=40)]] = Field(
        default_factory=list, max_length=5
    )

    @model_validator(mode="after")
    def validate_profile(self):
        if len({r.movieId for r in self.ratings}) != len(self.ratings):
            raise ValueError("Each movie may occur only once in a profile")
        if self.year_min and self.year_max and self.year_min > self.year_max:
            raise ValueError("Minimum year must not exceed maximum year")
        if len(set(self.favorite_genres)) != len(self.favorite_genres):
            raise ValueError("Favorite genres must be unique")
        return self


def create_app(model=None, model_dir=None, poster_data=None, metadata_service=None):
    artifact = Path(model_dir or os.environ.get("CINEMATCH_MODEL", ROOT / "artifacts/model"))

    @asynccontextmanager
    async def lifespan(app):
        if app.state.engine is None:
            try:
                app.state.engine = Recommender.load(artifact)
            except (OSError, ValueError) as exc:
                raise RuntimeError("Model is missing or invalid. Run: cinematch train") from exc
        yield

    app = FastAPI(title="CineMatch API", version="1.0.0", lifespan=lifespan)
    app.state.engine = model
    app.state.posters = PosterCatalog.load(Path(poster_data or ROOT / "data/movielens"))
    app.state.metadata = metadata_service or MovieMetadata()
    app.add_middleware(CORSMiddleware,
                       allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    def validate_taste(request):
        engine = app.state.engine
        profile = {r.movieId: r.rating for r in request.ratings}
        if any(mid not in engine.index for mid in profile):
            raise HTTPException(422, "Your history contains a movie outside this catalog")
        known = {g for genres in engine.genre_sets for g in genres}
        if request.genre and request.genre not in known:
            raise HTTPException(422, "Unknown genre")
        if not set(request.favorite_genres).issubset(known):
            raise HTTPException(422, "Unknown favorite genre")
        return profile

    @app.post("/api/home")
    def home(request: RecommendationRequest):
        engine = app.state.engine
        profile = validate_taste(request)
        source, shelves = choose_genre_shelves(engine, profile, request.favorite_genres)
        options = {"mode": request.mode, "diversity": request.diversity,
                   "favorite_genres": request.favorite_genres}
        recommendations = engine.recommend(profile, k=10, **options)
        genres = [{**shelf, "movies": engine.recommend(
            profile, k=10, genre=shelf["genre"], **options
        )} for shelf in shelves]
        return {"recommendations": recommendations, "genreSource": source, "genres": genres}

    @app.get("/api/health")
    def health():
        return {"status": "ready", "model": "hybrid-item-content", "version": "1.0.0"}

    @app.get("/api/stats")
    def stats():
        engine = app.state.engine
        genres = sorted({g for value in engine.movies.genres for g in genre_list(value)})
        return {"movies": len(engine.ids), "ratings": engine.metadata["training_ratings"],
                "users": engine.metadata["training_users"], "genres": genres,
                "alpha": engine.metadata["alpha"], "dataset": "MovieLens latest-small",
                "scoreNote": "Match scores are relative ranking signals, not probabilities."}

    @app.get("/api/movies")
    def movies(q: str = Query(default="", max_length=100),
               limit: int = Query(default=12, ge=1, le=80),
               genre: str | None = Query(default=None, max_length=40)):
        engine = app.state.engine
        frame = engine.movies
        mask = frame.title.str.contains(q.strip(), case=False, regex=False)
        if genre:
            mask &= frame.genres.map(lambda value: genre in genre_list(value))
        indices = frame[mask].sort_values(
            ["popularity", "movieId"], ascending=[False, True]
        ).index[:limit]
        return {"movies": [engine.movie(int(i)) for i in indices]}

    @app.get("/api/movies/{movie_id}")
    def movie(movie_id: int):
        engine = app.state.engine
        if movie_id not in engine.index:
            raise HTTPException(404, "Movie was not found")
        return engine.movie(engine.index[movie_id])

    @app.post("/api/recommend")
    def recommend(request: RecommendationRequest):
        engine = app.state.engine
        profile = validate_taste(request)
        options = request.model_dump(exclude={"ratings"})
        page = engine.recommend(profile, **options, lookahead=True)
        results = page[:request.k]
        return {"recommendations": results, "count": len(results),
                "hasMore": len(page) > request.k,
                "nextOffset": request.offset + len(results),
                "coldStart": not any(r > 3 for r in profile.values()),
                "scoreNote": "Ranking signal, not a confidence percentage"}

    @app.get("/api/movies/{movie_id}/description")
    def description(movie_id: int):
        engine = app.state.engine
        if movie_id not in engine.index:
            raise HTTPException(404, "Movie was not found")
        title = engine.movies.iloc[engine.index[movie_id]].title
        imdb_id = app.state.posters.imdb_id(movie_id, title)
        text = app.state.metadata.get(imdb_id) if imdb_id else None
        return {"movieId": movie_id, "description": text,
                "available": bool(text), "source": "Cinemeta" if text else None}

    @app.get("/api/movies/{movie_id}/poster", response_class=RedirectResponse)
    def poster(movie_id: int):
        engine = app.state.engine
        if movie_id not in engine.index:
            raise HTTPException(404, "Movie was not found")
        title = engine.movies.iloc[engine.index[movie_id]].title
        url = app.state.posters.url(movie_id, title)
        if url is None:
            raise HTTPException(404, "No poster is available for this movie")
        # The browser fetches the image directly; no bulk downloads or image copies in Git.
        return RedirectResponse(url, status_code=307,
                                headers={"Cache-Control": "public, max-age=86400"})

    @app.get("/api/evaluation")
    def evaluation():
        path = ROOT / "reports/evaluation.json"
        if not path.exists():
            raise HTTPException(404, "No evaluation report yet. Run: cinematch evaluate")
        return json.loads(path.read_text(encoding="utf-8"))

    dist = ROOT / "frontend/dist"
    if (dist / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/")
        def index():
            return FileResponse(dist / "index.html")

    return app


app = create_app()
