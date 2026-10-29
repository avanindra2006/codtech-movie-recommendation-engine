# Verification record

Date: 29 October 2026 (Asia/Kolkata).

- Python model/data/evaluation/API suite: **51 passed**, 0 failed.
- Frontend route and Watch again helper tests: **4 passed**.
- Frontend production build: passed (Vite 7.3.7).
- Python correctness lint: `ruff check --select E9,F63,F7,F82` passed.
- Desktop layout checked interactively at **1440 x 1000**, with no page overflow. Movie rows scroll horizontally.
- Home row order, ten movies plus the eleventh See more tile, and separation of the watched editor were verified.
- Recommendation collection preserves the home preview; loading another batch produced 48 distinct movie IDs.
- Saved, Watch again, and genre links open their own collections. Genre links survive refresh.
- Watched search/add/remove/rating controls, low-rating exclusion from Watch again, favorite precedence, and watched-genre inference were verified in an isolated test origin, without changing the main browser's saved data.
- Real API posters and summaries appear on the new desktop pages. Missing-image clapperboard fallback was verified in the earlier theme update.

Current evidence: `test-results.xml`, `home-layout-checks.json`, and `docs/screenshots/home-rows-desktop.jpg`, `watched-page.jpg`, and `genre-collection.jpg`. The optional `frontend/browser-check.cjs` was updated for the current desktop flow and syntax-checked; the current flow was exercised interactively, rather than running that script.

Earlier `poster-checks.json`, `theme-checks.json`, `discovery-checks.json`, and `browser-checks.json` record the previous iterations. Their older list sizes and mobile screenshots describe those iterations, not the current desktop-focused design.

The Python test run emitted one upstream Starlette/httpx TestClient deprecation warning. It did not affect the results. Earlier environment checks (`pip check`, editable installation, and the recommendation CLI) passed; no dependencies were added for the home-row update.

The recorded temporal experiment has 70,585 training, 15,125 validation, and 15,126 test ratings, with strict timestamp separation. The snapshot contains 100,836 ratings, 9,742 movies, and 610 viewers. The small warm-viewer test population limits quality conclusions; see RESULTS.md. The home-row update did not retrain the model or alter those measurements. GitHub-hosted CI has not run locally.

## Final submission audit

The final Python suite, frontend helper suite, production build, correctness lint, and `pip check` were rerun successfully. A clean archive was extracted under a new directory. Its own Python source and bundled production model passed local API checks using the verified Python runtime; the extracted frontend passed `npm ci`, all four helper tests, and a production build. Package installation used internet after an offline attempt found a missing cached dependency. Required files, README internship fields, local Markdown links, dataset source hashes, and archive exclusions were checked. See `submission-audit.json` for the record. GitHub publication and portal submission remain the final external actions.
