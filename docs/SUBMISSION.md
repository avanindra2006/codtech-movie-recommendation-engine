# CODTECH submission package

Intern ID: **CITS9600** · Full name: **Bobbasani Avanindra** · Duration: **4 weeks**

Project: **CineMatch — Movie Recommendation Engine**

The final [submission handover](../SUBMISSION_READY.md) maps each internship requirement to included files and explains the upload step. The [project report](PROJECT_REPORT.md) describes the complete implementation and measured results.

## Included evidence

- Source code: `src/cinematch/`, `frontend/src/`, `scripts/`, `tests/`.
- Dataset files: complete original MovieLens CSV snapshot and original small demo CSVs in `data/`.
- Fitted artifacts: sparse matrices, movie metadata, and preprocessing/model config in `artifacts/model/`.
- Cleaning and analysis: `reports/cleaning.json`, `reports/figures/`.
- Prediction output: `reports/sample_recommendations.json`.
- Evaluation: `reports/RESULTS.md`, `evaluation.json`, per-viewer scores, validation tuning, split manifest.
- Application screenshots: `docs/screenshots/` (real browser captures).
- Documentation: root README, methodology, architecture, source notices, and this checklist.
- Reproducibility: source hashes, dependency pins, npm lock, verification output, GitHub Actions workflow.

## Short demonstration

1. Start the app with the README commands.
2. Open **Watched movies**, then select **try a sci-fi profile** to rate The Matrix, Inception, and Interstellar. Demonstrate adding, removing, and rating films here.
3. Return Home. Show the first three rows, followed by genres inferred from viewing history. Scroll a row sideways to its eleventh See more tile.
4. Open that collection and use **Load more movies**. Show its genre/era/ranking controls and recommendation explanations.
5. Bookmark a film, open Saved movies, and show Watch again. Choose a favorite genre and show how it takes precedence over inferred home rows.
6. Open the evaluation lab and explain the time-based held-out comparison.

## Before submitting the link

- Confirm the README internship fields.
- Create one dedicated GitHub repository for this project.
- Upload project files, source datasets/notices, final artifacts, charts, reports, and screenshots.
- Leave environments, installed packages, caches, and secrets out of Git.
- Check the published repository's README images and setup commands.
- Submit the repository URL through the internship portal before its deadline.

The local package does not by itself publish a GitHub repository or submit to the internship portal.
