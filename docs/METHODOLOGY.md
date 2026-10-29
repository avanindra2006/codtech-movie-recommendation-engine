# How CineMatch recommends films

## Inputs and cleaning

The bundled official MovieLens latest-small snapshot supplies movie IDs, titles, pipe-separated genres, and anonymized explicit ratings. The untouched upstream README and SHA-256 provenance are in `data/movielens/`. Tags and external links are retained as source files but are not model features. External links support optional API posters and summaries in the interface; neither those display assets nor cast credits enter model training. The catalog does not claim current-release coverage.

`read_data` checks required columns and unique movie IDs, coerces numeric ratings, removes missing/non-finite/invalid IDs, half-star values outside 0.5–5, unknown movies, and invalid timestamps. Repeated user/movie pairs keep their latest timestamp. The snapshot has one opinion per pair; this policy is for custom inputs. Cleaning counts are recorded. Unknown genre metadata remains a usable catalog entry. Movie years are parsed from the trailing title year; missing years are unknown.

## Model

1. **Content:** TF-IDF over genre tokens repeated three times and title words, with the release year removed. A common `catalog` token ensures a valid vector for otherwise empty metadata. Every row is L2 normalized. The representation fits on the fixed metadata catalog; no ratings or user tags enter it.
2. **Audience patterns:** a sparse movie-by-user matrix uses only training ratings ≥4. Each value is `(rating−3)/sqrt(number of likes by that viewer)`. L2 normalization of movie rows makes their dot product cosine affinity. Weighting limits domination by prolific raters. Items with no observed likes have zero audience vectors.
3. **Popularity:** `0.7 * normalized log(1+rating_count) + 0.3 * Bayesian_mean/5`. The Bayesian mean shrinks each movie's observed mean toward the training global mean with 20 prior observations. Every rating statistic is fitted on the current training window.
4. **Profile:** each guest rating contributes `rating−3` to the content and audience vectors, normalized by the sum of absolute profile weights (at least 1). Dislikes reduce affinity. Scores are clipped at zero then divided by their catalog maximum. Every rated movie, including a neutral rating, is excluded from results. With no positively rated movie the system falls back to popularity.
5. **Blend:** `0.9 * (alpha * audience + (1−alpha) * content) + 0.1 * popularity`. Alternative modes retain a 10% popularity stabilizer. Alpha is selected from 0, 0.25, 0.5, 0.75, and 1 on validation NDCG@10; ties choose the first value. Match signals are not probabilities or predicted star ratings.
6. **Diversity:** the interface defaults to maximum marginal relevance with diversity 0.15. Iteratively choose the candidate maximizing `(1−diversity)*base_score − diversity*maximum_content_similarity_to_selected`. A shortlist of up to 250 candidates limits work. Evaluation sets diversity to zero to compare base rankers consistently. The returned matchScore is the base score, not the MMR selection objective.

Reasons identify the most similar liked seed using content affinity, plus audience affinity for the collaborative/hybrid modes, and list overlapping genres. This is a local similarity explanation, not a causal explanation or an exact decomposition of the blended score.

## Reproducible evaluation

Sort cleaned ratings globally by Unix timestamp. Let the timestamps at the 70th and 85th percentile row positions define the boundaries. Train uses times strictly before boundary 1; validation is `[boundary1,boundary2)`; test begins at boundary 2. A timestamp cannot be shared between windows. Actual counts are recorded because ties can change exact percentages.

Tune alpha using the training model and validation events. Freeze alpha, refit on train+validation, and evaluate the final test window. Only after recording results is a production model refitted on all observations. The production artifact is never used to compute held-out scores.

Evaluate viewers who have at least five earlier ratings ≥4 and at least one **new** held-out movie rated ≥4. Exclude every item in each viewer's earlier profile from candidates. Rank the full remaining catalog without sampled negatives. Low earlier ratings remain in the profile to reduce affinity. Test likes do not enter the query. Each viewer has equal weight when averaging metrics. Both included and excluded viewer counts are reported; results do not characterize cold users.

This is a **fixed-catalog temporal rating benchmark**. Static catalog/title/genre metadata includes entries from the complete snapshot, including films not historically available at every cutoff; exact release availability is not reconstructed. It prevents future rating leakage but is not a full historical deployment simulation. MovieLens is a development dataset with incomplete and self-selected feedback; an unrated item is not necessarily disliked.

## Metrics

- Precision@10: number of retrieved future liked movies divided by 10.
- Recall@10: retrieved future likes divided by all new future likes for that viewer.
- NDCG@10: binary gain discounted by `log2(rank+1)`, divided by ideal DCG for up to ten relevant items.
- Hit rate@10: fraction of eligible viewers with at least one relevant result.
- Catalog coverage: union of recommended movie IDs divided by the complete catalog size.
- Novelty: mean `−log2((training_count+1)/(all_training_ratings+catalog_size))` in bits.
- Genre diversity: average pairwise Jaccard distance between recommended genre sets.

No accuracy percentage is invented: this is a ranking problem rather than genre classification. The recorded table may favor a baseline; the report preserves the measured outcome. `split_manifest.csv`, per-viewer CSVs, source fingerprints, validation grid, and package versions make the calculation auditable.

## Efficiency and reuse

Sparse CSR matrices avoid storing a dense catalog-by-catalog similarity table. Scoring a guest profile combines a small number of rows and sparse products; the diversity step uses a bounded shortlist. Catalog vectors, interaction vectors, metadata, and configuration are saved as CSV, NPZ, and JSON. There is no pickle model deserialization and no runtime network service requirement. The core `Recommender` accepts a profile dictionary and can be reused independently of FastAPI and React in a later project.

## Optional favorite genres and pagination

For explicit favorite genres, score each movie's genre affinity as the fraction of its genres in the selected favorites. After the normal blend, use `0.8 * base_score + 0.2 * genre_affinity`. This is a soft preference rather than a filter; the separate genre filter remains exact. It also personalizes cold-start popularity recommendations without needing rated seeds. Favorite matches are named in the reason. The recorded historical evaluation has no guest genre selections, so its measurements describe the original base rankers, not the new preference boost.

Paging takes a stable slice of the same ranking with an offset. For diversity, MMR reranks the fixed first 250 base candidates, then browsing continues through the remaining base order. The pool does not grow when page size or offset changes, so earlier pages do not move or repeat. An extra lookahead item determines whether another page exists. No new dense full-catalog similarity table is built.

Home genre rows use explicit favorites in their selected order. If none are selected, each watched film contributes one count to each of its genres, regardless of its rating; the five most frequent genres are shown, with alphabetical tie-breaking. IMAX is excluded because it describes a format. With neither favorites nor history, the three most common catalog genres provide a clearly labeled starting point. This display policy does not change the recorded historical ranking evaluation.
