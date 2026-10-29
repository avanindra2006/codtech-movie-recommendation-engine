# CineMatch — Movie Recommendation Engine

**Intern:** Bobbasani Avanindra · **ID:** CITS9600 · **Duration:** 4 weeks · **Domain:** Data Science / Machine Learning

## Objective and scope

CineMatch helps a viewer find films using ratings of movies they have seen and optional favorite genres. The project covers the full development workflow: source data, cleaning, exploratory charts, recommendation modeling, a reproducible evaluation, a local API, and a desktop web dashboard. It is designed as an educational internship submission with reproducible source and measured results.

## Data and preparation

The bundled MovieLens latest-small snapshot contains **9,742 movies, 100,836 ratings, and 610 anonymized viewers**. Movie IDs, titles, genres, ratings, timestamps, and external identifier mappings are retained. The original dataset notice, citation, and source hashes accompany the files.

Cleaning validates columns, IDs, finite numeric values, valid half-star ratings, timestamps, and movie references. Duplicate viewer/movie pairs retain the most recent rating. Release years are parsed from titles, with unknown years handled explicitly. Cleaning outcomes appear in `reports/cleaning.json`. A separate original synthetic dataset provides small reusable examples; the reported model quality uses MovieLens.

The supplied charts show catalog/genre composition, rating and activity patterns, temporal split sizes, and held-out ranking performance. The analysis script can recreate them from the bundled files.

## Recommendation approach

The system combines three signals:

- **Content similarity:** TF-IDF vectors of movie titles and genres.
- **Collaborative similarity:** cosine affinity from sparse movie-by-viewer positive-feedback vectors.
- **Popularity:** rating activity combined with a Bayesian average rating.

A viewer's rating above three contributes positive preference, while lower ratings reduce affinity. Already watched movies are excluded from new suggestions. A validation-selected blend combines the personalized signals with a small popularity contribution. With insufficient positive history, popularity provides a useful starting point. Optional diversity reranking reduces repetitive suggestions.

Favorite genres softly boost ranking and determine the home genre rows. When none are selected, genre rows use viewing-history counts; a new profile starts with common catalog genres. This home organization policy is separate from the recorded base-model experiment. Full equations, tie handling, candidate definitions, and assumptions are in `METHODOLOGY.md`.

## Application design

Python supplies the reusable model, command-line tools, data pipeline, and FastAPI service. React and Vite supply the orange-and-black desktop interface. Sparse fitted artifacts are included, so the app can start without training or downloading model checkpoints.

Home shows Movies you might like, Saved movies, Watch again, then genre collections. Each horizontal row holds up to ten actual films followed by a See more tile. Each tile opens a dedicated collection, with batches of 24 films for recommendation and genre pages. Watched-history management and favorite-genre selection have separate pages. The evaluation lab exposes the recorded experiment.

Posters and short synopses load on demand through public Cinemeta/MetaHub services using bundled IMDb mappings. They are display metadata, not model features. No API key is needed. A clapperboard fallback handles missing images, and unavailable descriptions do not prevent recommendations. Guest history, preferences, and bookmarks stay in browser storage; the local service processes ranking requests without a user database.

## Evaluation and results

The experiment splits ratings globally by time into **70,585 training**, **15,125 validation**, and **15,126 test** observations. Blend selection uses validation only. Final held-out scores use a model fitted before the test period; the serving model is refitted on all ratings only after evaluation. The full unseen catalog is ranked without sampled negative items.

| Method | NDCG@10 | Recall@10 | Precision@10 | Hit rate@10 |
|---|---:|---:|---:|---:|
| Popularity baseline | 0.1183 | 0.0432 | 0.0967 | 0.3000 |
| Content | 0.0246 | 0.0027 | 0.0233 | 0.1333 |
| Collaborative | 0.1193 | 0.0366 | 0.1067 | 0.4000 |
| Validation-selected hybrid | 0.1193 | 0.0366 | 0.1067 | 0.4000 |

Validation selected a collaborative share of **1.0**, so the final hybrid and collaborative mode have the same measured results. Only **30 eligible warm viewers** enter this test. The slight NDCG difference does not establish statistically significant superiority, and popularity retrieves a larger fraction of future likes by recall. This is a ranking experiment; no classification accuracy is claimed.

## Validation and limitations

The final verification includes **51 Python tests**, **4 frontend helper tests**, a production frontend build, Python correctness lint, dependency consistency checks, and interactive desktop workflows. Tests cover cleaning, ranking behavior, evaluation isolation, API validation, synopsis caching/failures, genre selection, and pagination. Real screenshots document the running app. See `../reports/VERIFICATION.md` for evidence and the upstream deprecation warning.

MovieLens is a small development collection with self-selected feedback and older titles. Missing ratings are not proven dislikes. The fixed metadata catalog does not recreate historical film availability. The warm-viewer evaluation does not establish performance for new users. External image/metadata services require internet and may be unavailable. Browser-local storage does not synchronize between devices.

## Outcome and future work

The project delivers a working, documented recommendation dashboard, reusable model/API code, source datasets, fitted artifacts, measured baselines, charts, screenshots, and repeatable setup instructions. Potential extensions include broader evaluation populations, controlled user studies, newer licensed metadata, and optional account-based synchronization. Those extensions are outside the submitted implementation.

## References

- MovieLens source and original terms: `../data/movielens/README.txt` and `../THIRD_PARTY_NOTICES.md`.
- Harper, F. M., and Konstan, J. A. (2015). *The MovieLens Datasets: History and Context.* ACM TiiS 5(4), Article 19. DOI: 10.1145/2827872.
- Exact experiment, fingerprints, per-viewer outputs, and split manifest: `../reports/`.
