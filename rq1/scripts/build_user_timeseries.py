"""
build_user_timeseries.py — Generate weekly user count series at all filter levels.

Requires the COMPLETE index_document.csv (with author + created_utc columns).

Outputs in rq1/data/:
  vpn_user_timeseries.csv, politics_user_timeseries.csv,
  vpn_uk_user_timeseries.csv, politics_uk_user_timeseries.csv,
  vpn_uk_user_timeseries_classified.csv, politics_uk_user_timeseries_classified.csv,
  combined_uk_user_timeseries.csv, combined_uk_user_timeseries_classified.csv,
  table12_user_weekly_series.csv

Usage (from artifact root):
  python rq1/scripts/build_user_timeseries.py --index path/to/index_document_full.csv
"""

import pandas as pd
import os, sys, argparse
from collections import defaultdict

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

def compute_ts(pairs):
    if not pairs:
        return pd.DataFrame(columns=["week", "unique_users", "new_users", "cumulative_users"])
    df = pd.DataFrame(pairs, columns=["author", "week"]).drop_duplicates()
    weeks = sorted(df["week"].unique())
    seen = set()
    rows = []
    for w in weeks:
        wa = set(df.loc[df["week"] == w, "author"])
        new = wa - seen; seen |= wa
        rows.append({"week": w.strftime("%Y-%m-%d"), "unique_users": len(wa),
                      "new_users": len(new), "cumulative_users": len(seen)})
    return pd.DataFrame(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, help="Path to COMPLETE index_document.csv")
    parser.add_argument("--geo-dir", required=True)
    parser.add_argument("--original-dir", required=True)
    args = parser.parse_args()

    print("Building UK author set...")
    geo = load_authors(UK_GEO_SUBREDDITS, args.geo_dir)
    vpn_a = load_authors(VPN_SUBREDDITS, args.original_dir)
    pol_a = load_authors(POLITICS_SUBREDDITS, args.original_dir)
    uk = geo & (vpn_a | pol_a)
    print(f"  UK authors: {len(uk):,}")

    USE = ["subreddit", "author", "created_utc", "keyword_matched", "classifier_a", "classifier_b"]
    data = defaultdict(list)

    chunk_n = 0
    for chunk in pd.read_csv(args.index, usecols=USE, dtype=str, chunksize=1_000_000):
        chunk_n += 1
        if chunk_n % 10 == 0: print(f"  chunk {chunk_n}...")

        chunk = chunk[chunk["author"].notna() & ~chunk["author"].isin(SKIP_AUTHORS)].copy()
        ts = pd.to_datetime(chunk["created_utc"].astype(float), unit="s", errors="coerce")
        mask = ts.notna() & (ts >= START) & (ts <= END)
        chunk = chunk[mask].copy()
        chunk["_week"] = ts[mask].dt.to_period("W-MON").dt.start_time
        if len(chunk) == 0: continue

        is_vpn = chunk["subreddit"].isin(VPN_SUBREDDITS)
        is_pol = chunk["subreddit"].isin(POLITICS_SUBREDDITS)
        chunk = chunk[is_vpn | is_pol].copy()
        chunk["_g"] = "VPN"
        chunk.loc[is_pol[chunk.index], "_g"] = "Politics"

        chunk["_matched"] = chunk["keyword_matched"].str.strip().str.lower().isin(["true", "1", "1.0", "yes"])
        chunk["_clf_a"] = chunk["classifier_a"].str.strip().str.lower().isin(["true", "1", "1.0", "yes"])
        chunk["_clf_b"] = chunk["classifier_b"].str.strip().str.lower().isin(["true", "1", "1.0", "yes"])
        chunk["_classified"] = chunk["_clf_a"] & chunk["_clf_b"]
        chunk.loc[chunk["_g"] == "Politics", "_classified"] = chunk.loc[chunk["_g"] == "Politics", "_clf_a"]
        chunk["_uk"] = chunk["author"].isin(uk)

        auth = chunk["author"].values
        week = chunk["_week"].values
        grp = chunk["_g"].values
        m = chunk["_matched"].values
        c = chunk["_classified"].values
        u = chunk["_uk"].values

        for i in range(len(chunk)):
            pair = (auth[i], week[i])
            g = grp[i]
            data[(g, "Raw")].append(pair)
            if u[i]: data[(g, "Raw (UK)")].append(pair)
            if m[i]:
                data[(g, "Matched")].append(pair)
                if u[i]: data[(g, "Matched (UK)")].append(pair)
            else:
                data[(g, "Unmatched")].append(pair)
                if u[i]: data[(g, "Unmatched (UK)")].append(pair)
                else: data[(g, "Unmatched (non-UK)")].append(pair)
            if c[i]:
                data[(g, "Classified")].append(pair)
                if u[i]: data[(g, "Classified (UK)")].append(pair)

    print(f"Processed {chunk_n} chunks")

    os.makedirs(OUT, exist_ok=True)
    filters = ["Unmatched (non-UK)", "Unmatched", "Unmatched (UK)", "Raw", "Raw (UK)",
               "Matched", "Matched (UK)", "Classified", "Classified (UK)"]
    all_rows = []
    for group in ["VPN", "Politics"]:
        for filt in filters:
            key = (group, filt)
            if key not in data: print(f"  SKIP {group} {filt}"); continue
            print(f"  {group} {filt}: {len(data[key]):,} pairs...", end=" ")
            ts = compute_ts(data[key])
            ts["group"] = group; ts["filter"] = filt
            all_rows.append(ts)
            print(f"→ {len(ts)} weeks")

    result = pd.concat(all_rows, ignore_index=True)
    result = result[["group", "filter", "week", "unique_users", "new_users", "cumulative_users"]]
    result.to_csv(os.path.join(OUT, "table12_user_weekly_series.csv"), index=False)


    file_map = {
        ("VPN", "Classified"):       "vpn_user_timeseries.csv",
        ("VPN", "Classified (UK)"):  "vpn_uk_user_timeseries_classified.csv",
        ("VPN", "Raw (UK)"):         "vpn_uk_user_timeseries.csv",
        ("Politics", "Classified"):  "politics_user_timeseries.csv",
        ("Politics", "Classified (UK)"): "politics_uk_user_timeseries_classified.csv",
        ("Politics", "Raw (UK)"):    "politics_uk_user_timeseries.csv",
    }
    for (g, f), fname in file_map.items():
        sub = result[(result["group"] == g) & (result["filter"] == f)]
        if len(sub) == 0: continue
        sub[["week", "unique_users", "new_users", "cumulative_users"]].to_csv(
            os.path.join(OUT, fname), index=False)
        print(f"  {fname}: {len(sub)} weeks")

    print("Done.")

if __name__ == "__main__":
    main()
