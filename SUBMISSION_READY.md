# CineMatch: submission handover

| Required field | Submission value |
|---|---|
| Intern ID | CITS9600 |
| Full Name | Bobbasani Avanindra |
| No. of Weeks | 4 |
| Project Name | CineMatch — Movie Recommendation Engine |
| Project Scope | An explainable hybrid movie recommender with data cleaning, analysis, temporal evaluation, a local API, and a desktop web dashboard. |

## Start and review

1. Extract the project ZIP. Open a terminal inside the extracted `codtech-movie-recommendation-engine` folder, where `README.md` is located.
2. Follow the [README setup instructions](README.md#quick-start--windows-powershell). Python 3.13, Node.js 22.12+ or 24 LTS, and internet for the first dependency installation are required. The fitted model and datasets are included.
3. Open http://127.0.0.1:8000. Internet is needed for optional posters and descriptions; recommendation scoring runs locally.
4. Follow the [short demonstration](docs/SUBMISSION.md#short-demonstration). Read the [project report](docs/PROJECT_REPORT.md), [measured results](reports/RESULTS.md), and [verification record](reports/VERIFICATION.md).

## Internship requirements

| Requirement | Included evidence |
|---|---|
| Complete code with explanatory comments | `src/cinematch/`, `frontend/src/`, `scripts/` |
| Neatly organized folders | Repository map in `README.md`; exact archive inventory in `SUBMISSION_FILES.txt` |
| README internship fields and project scope | `README.md` and this handover |
| Dataset files | `data/movielens/` and original synthetic examples in `data/demo/` |
| Data cleaning | `src/cinematch/data.py`, `reports/cleaning.json` |
| Visualization and analysis | `scripts/create_analysis.py`, `reports/figures/` |
| Prediction/recommendation models | `src/cinematch/model.py`, fitted `artifacts/model/`, `reports/sample_recommendations.json` |
| Dashboard | Desktop React interface in `frontend/src/`, served by FastAPI |
| Graphs, output images, screenshots | `reports/figures/`, current screenshots listed in `docs/screenshots/README.md` |
| Documentation | README, project report, architecture, methodology, submission guide |
| Test and reproducibility evidence | `tests/`, `frontend/tests/`, `reports/VERIFICATION.md`, dependency locks, GitHub Actions |
| Source attribution | `THIRD_PARTY_NOTICES.md`, original MovieLens README and provenance |
| One unique GitHub repository and submitted link | Final action after uploading; the local archive is prepared for this step |

## Upload and submit

Suggested repository name: **codtech-movie-recommendation-engine**.

Create a dedicated GitHub repository and upload the **contents of the extracted project folder**. Put `README.md`, `src`, `frontend`, `data`, `artifacts`, `reports`, and `docs` at the repository root. Upload the extracted files, rather than only the ZIP, so reviewers can browse the code and images.

The ZIP excludes installed packages, environments, caches, and generated frontend build files. If you ran setup before uploading, use Git with the supplied `.gitignore` to leave those generated folders out. Keep the original datasets, notices, fitted model, charts, and screenshots in the repository.

Verify that the repository README and screenshots render and that the repository is accessible to the internship reviewer. Copy the **GitHub repository page link** into the internship submission portal. The local `127.0.0.1` app address is a development preview and is not the submission link.

GitHub publication and portal submission have not been performed by this package.
