import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rq2", "scripts"))
from config import VPN_SUBREDDITS, POLITICS_SUBREDDITS, UK_GEO_SUBREDDITS, SKIP_AUTHORS

START = pd.Timestamp("2021-10-26")
END = pd.Timestamp("2025-10-26")
OUT_DIR = os.path.join("rq1", "data")

INDEX_COLUMNS = ["subreddit", "type", "author", "created_utc", "keyword_matched", "classifier_a", "classifier_b"]
TRUE_VALUES = ["true", "1", "1.0", "yes"]


def load_authors(subreddits, directory):
    authors = set()

    for subreddit in subreddits:
        for kind in ("submissions", "comments"):
            path = os.path.join(directory, f"{subreddit}_{kind}.csv")
            if not os.path.exists(path):
                continue

            for chunk in pd.read_csv(path, usecols=["author"], dtype=str, chunksize=500_000):
                valid = chunk["author"].dropna()
                valid = valid.loc[~chunk["author"].isin(SKIP_AUTHORS)]
                authors.update(valid.tolist())

    return authors


def is_true(column):
    return column.str.strip().str.lower().isin(TRUE_VALUES)


def count_comments(is_post):
    return (~is_post).sum()


def prepare_chunk(chunk, uk_authors):
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

    chunk["is_uk"] = chunk["author"].isin(uk_authors)

    return chunk[["group", "week", "is_post", "matched", "classified", "is_uk"]]


def build_filters(df):
    return {
        "Raw": df,
        "Raw (UK)": df[df["is_uk"]],
        "Matched": df[df["matched"]],
        "Matched (UK)": df[df["matched"] & df["is_uk"]],
        "Unmatched": df[~df["matched"]],
        "Unmatched (UK)": df[~df["matched"] & df["is_uk"]],
        "Unmatched (non-UK)": df[~df["matched"] & ~df["is_uk"]],
        "Classified": df[df["classified"]],
        "Classified (UK)": df[df["classified"] & df["is_uk"]],
    }


def weekly_counts(df):
    weekly = df.groupby("week").agg(
        posts=("is_post", "sum"),
        comments=("is_post", count_comments),
    ).reset_index()

    weekly["total"] = weekly["posts"] + weekly["comments"]
    weekly["week"] = weekly["week"].dt.strftime("%Y-%m-%d")

    return weekly


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, help="Path to COMPLETE index_document.csv (with created_utc)")
    parser.add_argument("--geo-dir", required=True, help="Path to geo subreddit CSVs")
    parser.add_argument("--original-dir", required=True, help="Path to original subreddit CSVs")
    args = parser.parse_args()

    print("Building UK author set...")
    geo_authors = load_authors(UK_GEO_SUBREDDITS, args.geo_dir)
    vpn_authors = load_authors(VPN_SUBREDDITS, args.original_dir)
    politics_authors = load_authors(POLITICS_SUBREDDITS, args.original_dir)
    uk_authors = geo_authors & (vpn_authors | politics_authors)
    print(f"  UK authors: {len(uk_authors):,}")

    records = []
    chunk_count = 0

    for chunk in pd.read_csv(args.index, usecols=INDEX_COLUMNS, dtype=str, chunksize=1_000_000):
        chunk_count += 1
        if chunk_count % 10 == 0:
            print(f"  chunk {chunk_count}...")

        prepared = prepare_chunk(chunk, uk_authors)
        if prepared is not None:
            records.append(prepared)

    print(f"Processed {chunk_count} chunks, merging...")
    df = pd.concat(records, ignore_index=True)

    os.makedirs(OUT_DIR, exist_ok=True)
    parts = []

    for filter_name, filtered in build_filters(df).items():
        for group in ["VPN", "Politics"]:
            weekly = weekly_counts(filtered[filtered["group"] == group])
            weekly["group"] = group
            weekly["filter"] = filter_name
            parts.append(weekly)

    table13 = pd.concat(parts, ignore_index=True)
    table13 = table13[["group", "filter", "week", "posts", "comments", "total"]]
    table13.to_csv(os.path.join(OUT_DIR, "table13_weekly_series.csv"), index=False)
    print(f"Saved table13_weekly_series.csv ({len(table13):,} rows)")

    group_outputs = [("VPN", "vpn"), ("Politics", "politics")]
    filter_outputs = [("Classified", "classified_timeseries"), ("Classified (UK)", "uk_classified_timeseries")]

    for group, prefix in group_outputs:
        for filter_name, suffix in filter_outputs:
            series = table13[(table13["group"] == group) & (table13["filter"] == filter_name)]
            filename = f"{prefix}_{suffix}.csv"
            series[["week", "posts", "comments", "total"]].to_csv(os.path.join(OUT_DIR, filename), index=False)
            print(f"  {filename}: {len(series)} weeks")

    combined_outputs = [("Classified", "combined_classified_timeseries"), ("Classified (UK)", "combined_uk_classified_timeseries")]

    for filter_name, filename in combined_outputs:
        series = table13[table13["filter"] == filter_name]
        series = series.groupby("week")[["posts", "comments", "total"]].sum().reset_index()
        series.to_csv(os.path.join(OUT_DIR, f"{filename}.csv"), index=False)

    print("Done")


if __name__ == "__main__":
    main()
