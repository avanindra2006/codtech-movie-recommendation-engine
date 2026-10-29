"""Full-catalog, warm-user temporal ranking evaluation with validation-only tuning."""

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from .data import read_data, temporal_split
from .model import Recommender


def ranking_metrics(predicted, relevant, k):
    hits = np.array([mid in relevant for mid in predicted[:k]], dtype=float)
    dcg = float((hits / np.log2(np.arange(len(hits)) + 2)).sum())
    ideal = float((1 / np.log2(np.arange(min(k, len(relevant))) + 2)).sum())
    return {"precision": float(hits.sum() / k), "recall": float(hits.sum() / len(relevant)),
            "ndcg": dcg / ideal if ideal else 0., "hit_rate": float(hits.any())}


def evaluate(model, history, heldout, mode, k=10, alpha=None):
    histories = {int(uid): dict(zip(g.movieId.astype(int), g.rating.astype(float)))
                 for uid, g in history.groupby("userId")}
    rows, covered = [], set()
    eligible_heldout = heldout.userId.nunique()
    for uid, future in heldout.groupby("userId"):
        profile = histories.get(int(uid), {})
        if sum(r >= 4 for r in profile.values()) < 5:
            continue
        relevant = set(future.loc[future.rating >= 4, "movieId"].astype(int)) - set(profile)
        if not relevant:
            continue
        indices, _, _, _ = model.rank(profile, k=k, mode=mode, alpha=alpha, diversity=0)
        predictions = model.ids[indices].tolist()
        covered.update(predictions)
        metrics = ranking_metrics(predictions, relevant, k)
        genre_sim = []
        for a, left in enumerate(indices):
            for right in indices[a + 1:]:
                lset, rset = model.genre_sets[left], model.genre_sets[right]
                genre_sim.append(1 - len(lset & rset) / max(len(lset | rset), 1))
        counts = model.movies.iloc[indices].rating_count.to_numpy()
        metrics["novelty_bits"] = float((-np.log2((counts + 1) /
                                         (model.movies.rating_count.sum() + len(model.ids)))).mean())
        metrics["genre_diversity"] = float(np.mean(genre_sim)) if genre_sim else 0.
        rows.append({"userId": int(uid), "relevant_items": len(relevant), **metrics})
    if not rows:
        raise ValueError("No eligible evaluation users: need 5 historical likes and a future novel like")
    frame = pd.DataFrame(rows)
    summary = {key: float(frame[key].mean()) for key in
               ["precision", "recall", "ndcg", "hit_rate", "novelty_bits", "genre_diversity"]}
    summary.update({"evaluated_users": len(rows), "heldout_users": int(eligible_heldout),
                    "excluded_users": int(eligible_heldout - len(rows)),
                    "catalog_coverage": len(covered) / len(model.ids)})
    return summary, frame


def run_experiment(data_dir: Path, output: Path, model_dir: Path, k=10):
    output.mkdir(parents=True, exist_ok=True)
    movies, ratings, cleaning = read_data(data_dir)
    train, validation, test = temporal_split(ratings)
    print(f"Temporal split: {len(train):,} train / {len(validation):,} validation / {len(test):,} test")
    train_model = Recommender.fit(movies, train)
    tuning = []
    for alpha in [0., .25, .5, .75, 1.]:
        summary, _ = evaluate(train_model, train, validation, "hybrid", k, alpha)
        tuning.append({"alpha": alpha, "validation_ndcg": summary["ndcg"],
                       "evaluated_users": summary["evaluated_users"]})
    best = max(tuning, key=lambda row: row["validation_ndcg"])["alpha"]
    print(f"Validation selected collaborative weight: {best}")
    pretest = pd.concat([train, validation], ignore_index=True)
    test_model = Recommender.fit(movies, pretest, best)
    results = {}
    for mode in ["popular", "content", "collaborative", "hybrid"]:
        summary, per_user = evaluate(test_model, pretest, test, mode, k)
        results[mode] = summary
        per_user.to_csv(output / f"test_users_{mode}.csv", index=False)
        print(f"{mode:14} NDCG@{k}: {summary['ndcg']:.4f} | Recall@{k}: {summary['recall']:.4f}")
    manifest = pd.concat([g.assign(split=name) for name, g in
                          [("train", train), ("validation", validation), ("test", test)]])
    manifest[["userId", "movieId", "timestamp", "split"]].to_csv(
        output / "split_manifest.csv", index=False
    )
    report = {
        "dataset": "MovieLens latest-small", "k": k, "cleaning": cleaning,
        "protocol": "global temporal 70/15/15; full fixed metadata catalog; warm users; binary relevance >=4; no sampled negatives; diversity off",
        "minimum_history_likes": 5,
        "candidate_policy": "All catalog movies except those seen before the evaluation window. Static full catalog metadata is known; historical release availability is not reconstructed.",
        "split_sizes": {"train": len(train), "validation": len(validation), "test": len(test)},
        "time_boundaries": {"train_max": int(train.timestamp.max()),
                            "validation_min": int(validation.timestamp.min()),
                            "validation_max": int(validation.timestamp.max()),
                            "test_min": int(test.timestamp.min())},
        "validation_tuning": tuning, "selected_alpha": best,
        "test": results,
        "source_sha256": {name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
                          for name in ["movies.csv", "ratings.csv"]},
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "pandas": pd.__version__, "scikit_learn": sklearn.__version__},
        "limitations": [
            "Warm-user benchmark excludes new users and users without future positive feedback.",
            "Unobserved films are not proven dislikes; missing ratings bias offline metrics.",
            "Static metadata includes later catalog entries; this is not a historical deployment simulation.",
            "MovieLens latest-small is a development dataset, not a stable research benchmark.",
            "Match scores are ranking signals, not calibrated probabilities or predicted star ratings.",
            "Production artifacts are refitted on all ratings after evaluation; reported metrics use only pre-test fitting.",
        ],
    }
    (output / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(tuning).to_csv(output / "validation_tuning.csv", index=False)
    # Deployment may use all observations only after the test protocol has been recorded.
    production = Recommender.fit(movies, ratings, best)
    production.metadata["dataset_sha256"] = report["source_sha256"]
    production.metadata["fit_scope"] = "all cleaned ratings; not used to compute held-out metrics"
    production.save(model_dir)
    return report
