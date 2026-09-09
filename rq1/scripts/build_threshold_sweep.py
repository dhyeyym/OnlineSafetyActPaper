"""
build_threshold_sweep.py — Generate Table 17 weekly series at UK-residency thresholds k=1..5.

For each threshold k, a user is "UK-resident" only if they posted in ≥k
distinct UK geographic subreddits. The script recomputes weekly classified
content counts for each threshold.

Requires the COMPLETE index_document.csv (with author + created_utc) and
raw geographic subreddit CSVs.

Output: rq1/data/table17_weekly_series.csv

Usage (from artifact root):
  python rq1/scripts/build_threshold_sweep.py --index path/to/index_document_full.csv
"""

import pandas as pd
import os, sys, argparse
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rq2", "scripts"))
from config import VPN_SUBREDDITS, POLITICS_SUBREDDITS, UK_GEO_SUBREDDITS, SKIP_AUTHORS

START = pd.Timestamp("2021-10-26")
END   = pd.Timestamp("2025-10-26")
OUT   = os.path.join("rq1", "data")
THRESHOLDS = [1, 2, 3, 4, 5]

def build_uk_authors_at_thresholds(geo_dir, study_subs, original_dir):
    """Build UK author sets at different thresholds k=1..5."""
    author_geo_counts = defaultdict(set)
    for sub in sorted(UK_GEO_SUBREDDITS):
        for kind in ("submissions", "comments"):
            p = os.path.join(geo_dir, f"{sub}_{kind}.csv")
            if not os.path.exists(p): continue
            for c in pd.read_csv(p, usecols=["author"], dtype=str, chunksize=500_000):
                for a in c["author"].dropna():
                    if a not in SKIP_AUTHORS:
                        author_geo_counts[a].add(sub)

    study_authors = set()
    for sub in study_subs:
        for kind in ("submissions", "comments"):
            p = os.path.join(original_dir, f"{sub}_{kind}.csv")
            if not os.path.exists(p): continue
            for c in pd.read_csv(p, usecols=["author"], dtype=str, chunksize=500_000):
                study_authors.update(c["author"].dropna().loc[~c["author"].isin(SKIP_AUTHORS)].tolist())

    uk_at_k = {}
    for k in THRESHOLDS:
        uk_at_k[k] = {a for a, subs in author_geo_counts.items()
                       if len(subs) >= k and a in study_authors}
        print(f"  k>={k}: {len(uk_at_k[k]):,} UK authors")
    return uk_at_k

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--geo-dir", required=True)
    parser.add_argument("--original-dir", required=True)
    args = parser.parse_args()

    print("Building UK author sets at thresholds k=1..5...")
    all_study_subs = VPN_SUBREDDITS | POLITICS_SUBREDDITS
    uk_at_k = build_uk_authors_at_thresholds(args.geo_dir, all_study_subs, args.original_dir)

    USE = ["subreddit", "type", "author", "created_utc", "keyword_matched", "classifier_a", "classifier_b"]

    
    records = []
    chunk_n = 0
    for chunk in pd.read_csv(args.index, usecols=USE, dtype=str, chunksize=1_000_000):
        chunk_n += 1
        if chunk_n % 10 == 0: print(f"  chunk {chunk_n}...")

        chunk = chunk[chunk["author"].notna() & ~chunk["author"].isin(SKIP_AUTHORS)].copy()
        ts = pd.to_datetime(chunk["created_utc"].astype(float), unit="s", errors="coerce")
        mask = ts.notna() & (ts >= START) & (ts <= END)
        chunk = chunk[mask].copy()
        chunk["week"] = ts[mask].dt.to_period("W-MON").dt.start_time
        if len(chunk) == 0: continue

        is_vpn = chunk["subreddit"].isin(VPN_SUBREDDITS)
        is_pol = chunk["subreddit"].isin(POLITICS_SUBREDDITS)
        chunk = chunk[is_vpn | is_pol].copy()
        chunk["group"] = "VPN"
        chunk.loc[is_pol[chunk.index], "group"] = "Politics"

        chunk["is_post"] = chunk["type"].str.lower().isin(["post", "submission"])
        chunk["matched"] = chunk["keyword_matched"].str.strip().str.lower().isin(["true", "1", "1.0", "yes"])
        chunk["clf_a"] = chunk["classifier_a"].str.strip().str.lower().isin(["true", "1", "1.0", "yes"])
        chunk["clf_b"] = chunk["classifier_b"].str.strip().str.lower().isin(["true", "1", "1.0", "yes"])
        chunk["classified"] = chunk["clf_a"] & chunk["clf_b"]
        chunk.loc[chunk["group"] == "Politics", "classified"] = chunk.loc[chunk["group"] == "Politics", "clf_a"]

        records.append(chunk[["group", "week", "is_post", "matched", "classified", "author"]])

    print(f"Processed {chunk_n} chunks, merging...")
    df = pd.concat(records, ignore_index=True)

    os.makedirs(OUT, exist_ok=True)
    all_rows = []

    for group in ["VPN", "Politics"]:
        for definition in ["Raw", "Classified"]:
            if definition == "Raw":
                sub = df[df["group"] == group]
            else:
                sub = df[(df["group"] == group) & df["classified"]]

            for k in THRESHOLDS:
                uk_set = uk_at_k[k]
                uk_sub = sub[sub["author"].isin(uk_set)]
                weekly = uk_sub.groupby("week").agg(
                    posts=("is_post", "sum"),
                    comments=("is_post", lambda x: (~x).sum())
                ).reset_index()
                weekly["total"] = weekly["posts"] + weekly["comments"]
                weekly["week"] = weekly["week"].dt.strftime("%Y-%m-%d")
                weekly["group"] = group
                weekly["definition"] = definition
                weekly["k"] = k
                all_rows.append(weekly)
                print(f"  {group} {definition} k>={k}: {len(weekly)} weeks, {int(weekly['total'].sum()):,} docs")

    result = pd.concat(all_rows, ignore_index=True)
    result = result[["group", "definition", "k", "week", "posts", "comments", "total"]]
    result.to_csv(os.path.join(OUT, "table17_weekly_series.csv"), index=False)
    print(f"Done")
    
if __name__ == "__main__":
    main()
