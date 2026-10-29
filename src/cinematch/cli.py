"""Reproducible command-line entry points; paths resolve from the repository root."""

import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
ARCHIVE_SHA256 = "696d65a3dfceac7c45750ad32df2c259311949efec81f0f144fdfb91ebc9e436"


def download(destination):
    """Restore the exact documented dataset snapshot from the official host."""
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": "CineMatch/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive = response.read(20_000_001)
    if len(archive) > 20_000_000 or hashlib.sha256(archive).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Dataset archive changed or is incomplete; do not silently change the experiment")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        for filename in ["movies.csv", "ratings.csv", "links.csv", "tags.csv", "README.txt"]:
            # Explicit member names prevent archive path traversal.
            (destination / filename).write_bytes(zf.read("ml-latest-small/" + filename))
    (destination / "provenance.json").write_text(json.dumps({
        "url": DATA_URL, "archive_sha256": ARCHIVE_SHA256,
        "license": "See the unmodified README.txt in this directory",
    }, indent=2), encoding="utf-8")
    print(f"Verified MovieLens snapshot saved to {destination}")


def main():
    parser = argparse.ArgumentParser(description="CineMatch training and recommendation tools")
    sub = parser.add_subparsers(dest="command", required=True)
    get = sub.add_parser("download", help="Restore bundled MovieLens snapshot")
    get.add_argument("--data", type=Path, default=ROOT / "data/movielens")
    for name in ["train", "evaluate"]:
        command = sub.add_parser(name)
        command.add_argument("--data", type=Path, default=ROOT / "data/movielens")
        command.add_argument("--model", type=Path, default=ROOT / "artifacts/model")
        if name == "evaluate":
            command.add_argument("--output", type=Path, default=ROOT / "reports")
    recommend = sub.add_parser("recommend")
    recommend.add_argument("--likes", required=True, help="Comma-separated MovieLens movie IDs")
    recommend.add_argument("--model", type=Path, default=ROOT / "artifacts/model")
    sub.add_parser("serve")
    args = parser.parse_args()
    try:
        if args.command == "download":
            download(args.data)
        elif args.command == "evaluate":
            from .evaluate import run_experiment
            run_experiment(args.data, args.output, args.model)
        elif args.command == "train":
            from .data import read_data
            from .model import Recommender
            movies, ratings, report = read_data(args.data)
            Recommender.fit(movies, ratings).save(args.model)
            print(json.dumps(report, indent=2))
        elif args.command == "recommend":
            from .model import Recommender
            profile = {int(mid): 5. for mid in args.likes.split(",")}
            print(json.dumps(Recommender.load(args.model).recommend(profile), indent=2))
        else:
            import uvicorn
            uvicorn.run("cinematch.api:app", host="127.0.0.1", port=8000)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"CineMatch: {exc}\n")


if __name__ == "__main__":
    main()
