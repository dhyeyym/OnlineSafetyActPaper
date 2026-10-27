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

INDEX_COLUMNS = ["subreddit", "author", "created_utc", "keyword_matched", "classifier_a", "classifier_b"]
TRUE_VALUES = ["true", "1", "1.0", "yes"]

FILTERS = [
    "Unmatched (non-UK)", "Unmatched", "Unmatched (UK)", "Raw", "Raw (UK)",
    "Matched", "Matched (UK)", "Classified", "Classified (UK)",
]

OUTPUT_FILES = {
    ("VPN", "Classified"): "vpn_user_timeseries.csv",
    ("VPN", "Classified (UK)"): "vpn_uk_user_timeseries_classified.csv",
    ("VPN", "Raw (UK)"): "vpn_uk_user_timeseries.csv",
    ("Politics", "Classified"): "politics_user_timeseries.csv",
    ("Politics", "Classified (UK)"): "politics_uk_user_timeseries_classified.csv",
    ("Politics", "Raw (UK)"): "politics_uk_user_timeseries.csv",
}


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


def compute_user_series(pairs):
    if not pairs:
        return pd.DataFrame(columns=["week", "unique_users", "new_users", "cumulative_users"])

    df = pd.DataFrame(pairs, columns=["author", "week"]).drop_duplicates()
    weeks = sorted(df["week"].unique())

    seen = set()
    rows = []

    for week in weeks:
        week_authors = set(df.loc[df["week"] == week, "author"])
        new_authors = week_authors - seen
        seen |= week_authors

        rows.append({
            "week": week.strftime("%Y-%m-%d"),
            "unique_users": len(week_authors),
            "new_users": len(new_authors),
            "cumulative_users": len(seen),
        })

    return pd.DataFrame(rows)


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

    chunk["matched"] = is_true(chunk["keyword_matched"])

    classifier_a = is_true(chunk["classifier_a"])
    classifier_b = is_true(chunk["classifier_b"])
    is_politics_row = chunk["group"] == "Politics"
    chunk["classified"] = classifier_a & classifier_b
    chunk.loc[is_politics_row, "classified"] = classifier_a[is_politics_row]

    chunk["is_uk"] = chunk["author"].isin(uk_authors)

    return chunk


def add_pairs(chunk, pairs_by_series):
    authors = chunk["author"].values
    weeks = chunk["week"].values
    groups = chunk["group"].values
    matched = chunk["matched"].values
    classified = chunk["classified"].values
    is_uk = chunk["is_uk"].values

    for i in range(len(chunk)):
        pair = (authors[i], weeks[i])
        group = groups[i]

        pairs_by_series[(group, "Raw")].append(pair)
        if is_uk[i]:
            pairs_by_series[(group, "Raw (UK)")].append(pair)

        if matched[i]:
            pairs_by_series[(group, "Matched")].append(pair)
            if is_uk[i]:
                pairs_by_series[(group, "Matched (UK)")].append(pair)
        else:
            pairs_by_series[(group, "Unmatched")].append(pair)
            if is_uk[i]:
                pairs_by_series[(group, "Unmatched (UK)")].append(pair)
            else:
                pairs_by_series[(group, "Unmatched (non-UK)")].append(pair)

        if classified[i]:
            pairs_by_series[(group, "Classified")].append(pair)
            if is_uk[i]:
                pairs_by_series[(group, "Classified (UK)")].append(pair)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, help="Path to COMPLETE index_document.csv")
    parser.add_argument("--geo-dir", required=True)
    parser.add_argument("--original-dir", required=True)
    args = parser.parse_args()

    print("Building UK author set...")
    geo_authors = load_authors(UK_GEO_SUBREDDITS, args.geo_dir)
    vpn_authors = load_authors(VPN_SUBREDDITS, args.original_dir)
    politics_authors = load_authors(POLITICS_SUBREDDITS, args.original_dir)
    uk_authors = geo_authors & (vpn_authors | politics_authors)
    print(f"  UK authors: {len(uk_authors):,}")

    pairs_by_series = defaultdict(list)
    chunk_count = 0

    for chunk in pd.read_csv(args.index, usecols=INDEX_COLUMNS, dtype=str, chunksize=1_000_000):
        chunk_count += 1
        if chunk_count % 10 == 0:
            print(f"  chunk {chunk_count}...")

        prepared = prepare_chunk(chunk, uk_authors)
        if prepared is not None:
            add_pairs(prepared, pairs_by_series)

    print(f"Processed {chunk_count} chunks")

    os.makedirs(OUT_DIR, exist_ok=True)
    parts = []

    for group in ["VPN", "Politics"]:
        for filter_name in FILTERS:
            key = (group, filter_name)
            if key not in pairs_by_series:
                print(f"  SKIP {group} {filter_name}")
                continue

            print(f"  {group} {filter_name}: {len(pairs_by_series[key]):,} pairs...", end=" ")
            series = compute_user_series(pairs_by_series[key])
            series["group"] = group
            series["filter"] = filter_name
            parts.append(series)
            print(f"→ {len(series)} weeks")

    result = pd.concat(parts, ignore_index=True)
    result = result[["group", "filter", "week", "unique_users", "new_users", "cumulative_users"]]
    result.to_csv(os.path.join(OUT_DIR, "table12_user_weekly_series.csv"), index=False)

    for (group, filter_name), filename in OUTPUT_FILES.items():
        series = result[(result["group"] == group) & (result["filter"] == filter_name)]
        if len(series) == 0:
            continue

        columns = ["week", "unique_users", "new_users", "cumulative_users"]
        series[columns].to_csv(os.path.join(OUT_DIR, filename), index=False)
        print(f"  {filename}: {len(series)} weeks")

    print("Done.")


if __name__ == "__main__":
    main()
