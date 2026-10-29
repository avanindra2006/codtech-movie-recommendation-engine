# Third-party sources

## MovieLens latest-small

Source: https://grouplens.org/datasets/movielens/latest/

Official archive: https://files.grouplens.org/datasets/movielens/ml-latest-small.zip

The exact snapshot includes 100,836 ratings by 610 viewers over 9,742 movies. Its original usage license, citation, and conditions are reproduced unmodified in `data/movielens/README.txt`. The dataset files, their transformations in `artifacts/model/`, and the data-derived reports are supplied under those original conditions, including research use, attribution, no implied endorsement, and permission requirements for commercial/revenue-bearing use. They are not covered by the repository's MIT grant. Preserve the original README when redistributing them.

Citation: F. Maxwell Harper and Joseph A. Konstan. 2015. *The MovieLens Datasets: History and Context.* ACM Transactions on Interactive Intelligent Systems 5, 4, Article 19. https://doi.org/10.1145/2827872

`data/movielens/provenance.json` records the source and archive/file SHA-256 hashes. `reports/evaluation.json` records the actual input fingerprints. The latest-small collection is intended for education/development and can change upstream; the restore command refuses an archive that differs from the recorded snapshot.

## Software and artwork

Python dependencies include NumPy, SciPy, pandas, scikit-learn, FastAPI, and Uvicorn. The interface uses React, Vite, and Lucide React. They retain their respective upstream licenses; dependency versions are locked in `constraints.txt` and `frontend/package-lock.json`. Lucide icons use the ISC license: https://github.com/lucide-icons/lucide/blob/main/LICENSE

DM Sans and Space Grotesk are loaded optionally through Google Fonts under the SIL Open Font License; the interface falls back to system fonts without internet. Fonts: https://github.com/google/fonts/tree/main/ofl/dmsans and https://github.com/google/fonts/tree/main/ofl/spacegrotesk

The hero clapperboard and fallback title cards are original CSS artwork. Movie posters load remotely from Cinemeta/MetaHub through the public endpoint documented in the [Stremio catalog guide](https://stremio.github.io/stremio-addon-guide/step3). MovieLens links.csv supplies IMDb identifiers. No API key or bulk image download is needed. Poster artwork retains its original owners’ rights and is not covered by the repository MIT license. No standalone poster files are bundled; application screenshots show posters within the running interface for demonstration. Movie titles/genres come from the attributed dataset.

Movie descriptions are fetched on demand from the public [Cinemeta metadata API](https://stremio.github.io/stremio-addon-sdk/api/responses/meta.html) and credited in the interface. The application caches short excerpts in memory; they retain their source rights and are display metadata, not CineMatch-authored training data.
