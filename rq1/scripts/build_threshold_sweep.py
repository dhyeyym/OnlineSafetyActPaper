import argparse
import os
import sys
from collections import defaultdict

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rq2", "scripts"))
from config import VPN_SUBREDDITS, POLITICS_SUBREDDITS, UK_GEO_SUBREDDITS, SKIP_AUTHORS

START = pd.Timestamp("2021-10-26")
END = pd.Timestamp("2025-10-26")
OUT_DIR = os.path.join("rq1", "data")
THRESHOLDS = [1, 2, 3, 4, 5]

INDEX_COLUMNS = ["subreddit", "type", "author", "created_utc", "keyword_matched", "classifier_a", "classifier_b"]
TRUE_VALUES = ["true", "1", "1.0", "yes"]


def load_geo_subreddits_per_author(geo_dir):
    subreddits_per_author = defaultdict(set)

    for subreddit in sorted(UK_GEO_SUBREDDITS):
        for kind in ("submissions", "comments"):
            path = os.path.join(geo_dir, f"{subreddit}_{kind}.csv")
            if not os.path.exists(path):
                continue

            for chunk in pd.read_csv(path, usecols=["author"], dtype=str, chunksize=500_000):
                for author in chunk["author"].dropna():
                    if author not in SKIP_AUTHORS:
                        subreddits_per_author[author].add(subreddit)

    return subreddits_per_author


def load_study_authors(study_subreddits, original_dir):
    authors = set()

    for subreddit in study_subreddits:
        for kind in ("submissions", "comments"):
            path = os.path.join(original_dir, f"{subreddit}_{kind}.csv")
            if not os.path.exists(path):
                continue

            for chunk in pd.read_csv(path, usecols=["author"], dtype=str, chunksize=500_000):
                valid = chunk["author"].dropna()
                valid = valid.loc[~chunk["author"].isin(SKIP_AUTHORS)]
                authors.update(valid.tolist())

    return authors


def build_uk_authors_at_thresholds(geo_dir, study_subreddits, original_dir):
    subreddits_per_author = load_geo_subreddits_per_author(geo_dir)
    study_authors = load_study_authors(study_subreddits, original_dir)

    uk_authors_at_k = {}

    for k in THRESHOLDS:
        uk_authors = set()
        for author, subreddits in subreddits_per_author.items():
            if len(subreddits) >= k and author in study_authors:
                uk_authors.add(author)

        uk_authors_at_k[k] = uk_authors
        print(f"  k>={k}: {len(uk_authors):,} UK authors")

    return uk_authors_at_k


def is_true(column):
    return column.str.strip().str.lower().isin(TRUE_VALUES)


def count_comments(is_post):
    return (~is_post).sum()


def prepare_chunk(chunk):
    chunk = chunk[chunk["author"].notna() & ~chunk["author"].isin(SKIP_AUTHORS)].copy()

    timestamps = pd.to_datetime(chunk["created_utc"].astype(float), unit="s", errors="coerce")
    in_window = timestamps.notna() & (timestamps >= START) & (timestamps <= END)
    chunk = chunk[in_window].copy()
    chunk["week"] = timestamps[in_window].dt.to_period("W-MON").dt.start_time

    if len(chunk) == 0:
        return None

    is_vpn = chunk["subreddit"].isin(VPN_SUBREDDITS)
    is_politics = chunk["subreddit"].isin(POLITICS_SUBREDDITS)
    chunk = chunk[is_vpn | is_politics].copy()
    chunk["group"] = "VPN"
    chunk.loc[is_politics[chunk.index], "group"] = "Politics"

    chunk["is_post"] = chunk["type"].str.lower().isin(["post", "submission"])
    chunk["matched"] = is_true(chunk["keyword_matched"])

    classifier_a = is_true(chunk["classifier_a"])
    classifier_b = is_true(chunk["classifier_b"])
    is_politics_row = chunk["group"] == "Politics"
    chunk["classified"] = classifier_a & classifier_b
    chunk.loc[is_politics_row, "classified"] = classifier_a[is_politics_row]

    return chunk[["group", "week", "is_post", "matched", "classified", "author"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--geo-dir", required=True)
    parser.add_argument("--original-dir", required=True)
    args = parser.parse_args()

    print("Building UK author sets at thresholds k=1..5...")
    study_subreddits = VPN_SUBREDDITS | POLITICS_SUBREDDITS
    uk_authors_at_k = build_uk_authors_at_thresholds(args.geo_dir, study_subreddits, args.original_dir)

    records = []
    chunk_count = 0

    for chunk in pd.read_csv(args.index, usecols=INDEX_COLUMNS, dtype=str, chunksize=1_000_000):
        chunk_count += 1
        if chunk_count % 10 == 0:
            print(f"  chunk {chunk_count}...")

        prepared = prepare_chunk(chunk)
        if prepared is not None:
            records.append(prepared)

    print(f"Processed {chunk_count} chunks, merging...")
    df = pd.concat(records, ignore_index=True)

    os.makedirs(OUT_DIR, exist_ok=True)
    parts = []

    for group in ["VPN", "Politics"]:
        for definition in ["Raw", "Classified"]:
            if definition == "Raw":
                subset = df[df["group"] == group]
            else:
                subset = df[(df["group"] == group) & df["classified"]]

            for k in THRESHOLDS:
                uk_subset = subset[subset["author"].isin(uk_authors_at_k[k])]

                weekly = uk_subset.groupby("week").agg(
                    posts=("is_post", "sum"),
                    comments=("is_post", count_comments),
                ).reset_index()
                weekly["total"] = weekly["posts"] + weekly["comments"]
                weekly["week"] = weekly["week"].dt.strftime("%Y-%m-%d")
                weekly["group"] = group
                weekly["definition"] = definition
                weekly["k"] = k
                parts.append(weekly)

                print(f"  {group} {definition} k>={k}: {len(weekly)} weeks, {int(weekly['total'].sum()):,} docs")

    result = pd.concat(parts, ignore_index=True)
    result = result[["group", "definition", "k", "week", "posts", "comments", "total"]]
    result.to_csv(os.path.join(OUT_DIR, "table17_weekly_series.csv"), index=False)
    print("Done")


if __name__ == "__main__":
    main()
