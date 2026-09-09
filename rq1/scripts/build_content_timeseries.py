"""
build_content_timeseries.py — Generate weekly content time series at all filter levels.

Requires the COMPLETE index_document.csv (with created_utc column) and
the UK author set from geographic subreddit intersection.

Outputs in rq1/data/:
  vpn_classified_timeseries.csv, politics_classified_timeseries.csv,
  vpn_uk_classified_timeseries.csv, politics_uk_classified_timeseries.csv,
  combined_classified_timeseries.csv, combined_uk_classified_timeseries.csv,
  table13_weekly_series.csv

Usage (from artifact root):
  python rq1/scripts/build_content_timeseries.py --index path/to/index_document_full.csv
"""

import pandas as pd
import os, sys, argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rq2", "scripts"))
from config import VPN_SUBREDDITS, POLITICS_SUBREDDITS, UK_GEO_SUBREDDITS, SKIP_AUTHORS

START = pd.Timestamp("2021-10-26")
END   = pd.Timestamp("2025-10-26")
OUT   = os.path.join("rq1", "data")

def load_authors(subreddits, directory):
    authors = set()
    for sub in subreddits:
        for kind in ("submissions", "comments"):
            p = os.path.join(directory, f"{sub}_{kind}.csv")
            if not os.path.exists(p): continue
            for c in pd.read_csv(p, usecols=["author"], dtype=str, chunksize=500_000):
                authors.update(c["author"].dropna().loc[~c["author"].isin(SKIP_AUTHORS)].tolist())
    return authors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, help="Path to COMPLETE index_document.csv (with created_utc)")
    parser.add_argument("--geo-dir", required=True, help="Path to geo subreddit CSVs")
    parser.add_argument("--original-dir", required=True, help="Path to original subreddit CSVs")
    args = parser.parse_args()

    print("Building UK author set...")
    geo = load_authors(UK_GEO_SUBREDDITS, args.geo_dir)
    vpn_a = load_authors(VPN_SUBREDDITS, args.original_dir)
    pol_a = load_authors(POLITICS_SUBREDDITS, args.original_dir)
    uk = geo & (vpn_a | pol_a)
    print(f"  UK authors: {len(uk):,}")

    USE = ["subreddit", "type", "author", "created_utc", "keyword_matched", "classifier_a", "classifier_b"]
    all_records = []

   
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
        chunk["is_uk"] = chunk["author"].isin(uk)

        all_records.append(chunk[["group", "week", "is_post", "matched", "classified", "is_uk"]])

    print(f"Processed {chunk_n} chunks, merging...")
    df = pd.concat(all_records, ignore_index=True)

    filters = {
        "Raw":                  df,
        "Raw (UK)":             df[df["is_uk"]],
        "Matched":              df[df["matched"]],
        "Matched (UK)":         df[df["matched"] & df["is_uk"]],
        "Unmatched":            df[~df["matched"]],
        "Unmatched (UK)":       df[~df["matched"] & df["is_uk"]],
        "Unmatched (non-UK)":   df[~df["matched"] & ~df["is_uk"]],
        "Classified":           df[df["classified"]],
        "Classified (UK)":      df[df["classified"] & df["is_uk"]],
    }

    os.makedirs(OUT, exist_ok=True)
    table13_parts = []

    for filt_name, filt_df in filters.items():
        for group in ["VPN", "Politics"]:
            sub = filt_df[filt_df["group"] == group]
            weekly = sub.groupby("week").agg(
                posts=("is_post", "sum"),
                comments=("is_post", lambda x: (~x).sum())
            ).reset_index()
            weekly["total"] = weekly["posts"] + weekly["comments"]
            weekly["week"] = weekly["week"].dt.strftime("%Y-%m-%d")
            weekly["group"] = group
            weekly["filter"] = filt_name
            table13_parts.append(weekly)

    table13 = pd.concat(table13_parts, ignore_index=True)
    table13 = table13[["group", "filter", "week", "posts", "comments", "total"]]
    table13.to_csv(os.path.join(OUT, "table13_weekly_series.csv"), index=False)
    print(f"Saved table13_weekly_series.csv ({len(table13):,} rows)")

    for group, g_label in [("VPN", "vpn"), ("Politics", "politics")]:
        for filt, suffix in [("Classified", "classified_timeseries"),
                              ("Classified (UK)", "uk_classified_timeseries")]:
            sub = table13[(table13["group"] == group) & (table13["filter"] == filt)]
            fname = f"{g_label}_{suffix}.csv"
            sub[["week", "posts", "comments", "total"]].to_csv(os.path.join(OUT, fname), index=False)
            print(f"  {fname}: {len(sub)} weeks")

    for filt, suffix in [("Classified", "combined_classified_timeseries"),
                          ("Classified (UK)", "combined_uk_classified_timeseries")]:
        sub = table13[table13["filter"] == filt].groupby("week")[["posts", "comments", "total"]].sum().reset_index()
        sub.to_csv(os.path.join(OUT, f"{suffix}.csv"), index=False)

    print("Done")

if __name__ == "__main__":
    main()
