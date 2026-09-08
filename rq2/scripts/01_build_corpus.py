"""
01_build_corpus.py — Build the RQ2 corpora from classified files.

Outputs:
  rq2_corpus_full.csv   (all authors — used to FIT the LDA)
  rq2_corpus.csv        (UK authors only — used for assignment + sentiment)
"""
import pandas as pd
import sys
from config import (
    ORIGINAL_DIR, GEO_DIR, RESULTS_DIR,
    START_DATE, END_DATE, SKIP_AUTHORS,
    VPN_SUBREDDITS, POLITICS_SUBREDDITS, UK_GEO_SUBREDDITS,
    CLASSIFIED_FILES,
)

def load_authors_from_raw(subreddits, directory):
    authors = set()
    sub_lower = {s.lower(): s for s in subreddits}
    for sub_lc, sub in sorted(sub_lower.items()):
        for kind in ("submissions", "comments"):
            path = directory / f"{sub}_{kind}.csv"
            if not path.exists():
                matches = [f for f in directory.iterdir()
                           if f.name.lower() == f"{sub_lc}_{kind}.csv"]
                if not matches:
                    continue
                path = matches[0]
            try:
                for chunk in pd.read_csv(path, usecols=["author"], dtype=str, chunksize=500_000):
                    valid = chunk["author"].dropna()
                    valid = valid[~valid.isin(SKIP_AUTHORS)]
                    authors.update(valid.tolist())
            except Exception:
                pass
    return authors

def build_uk_authors():
    geo = load_authors_from_raw(UK_GEO_SUBREDDITS, GEO_DIR)
    vpn = load_authors_from_raw(VPN_SUBREDDITS, ORIGINAL_DIR)
    pol = load_authors_from_raw(POLITICS_SUBREDDITS, ORIGINAL_DIR)
    uk  = geo & (vpn | pol)
    print(f"UK authors: {len(uk):,}")
    return uk

def get_text(row, kind):
    if kind == "comment":
        return str(row.get("body", "") or "").strip()
    title    = str(row.get("title", "") or "").strip()
    selftext = str(row.get("selftext", "") or "").strip()
    if selftext.lower() in ("", "[deleted]", "[removed]"):
        return title
    return f"{title} {selftext}".strip()

if __name__ == "__main__":
    start = pd.Timestamp(START_DATE)
    end   = pd.Timestamp(END_DATE)

    uk_authors = build_uk_authors()

    full_records, uk_records = [], []
    for fname, group, kind, rel_col in CLASSIFIED_FILES:
        path = RESULTS_DIR / fname
        if not path.exists():
            print(f"  MISSING: {fname}"); continue
        df = pd.read_csv(path, dtype=str)
        df = df[df[rel_col].astype(int) == 1]
        df = df[df["author"].notna() & ~df["author"].isin(SKIP_AUTHORS)]
        ts = pd.to_datetime(df["created_utc"].astype(float), unit="s", errors="coerce")
        df = df[(ts >= start) & (ts <= end)].copy()

        n_full = n_uk = 0
        for _, row in df.iterrows():
            text = get_text(row, kind)
            if len(text.strip()) < 10:
                continue
            rec = {"group": group, "kind": kind, "subreddit": row.get("subreddit", ""),
                   "author": row.get("author", ""), "created_utc": row.get("created_utc", ""),
                   "text": text}
            full_records.append(rec); n_full += 1
            if row.get("author") in uk_authors:
                uk_records.append(rec); n_uk += 1
        print(f"  {fname}: {n_full:,} relevant ({n_uk:,} UK)")

    full = pd.DataFrame(full_records).drop_duplicates(subset=["author", "text"]).reset_index(drop=True)
    full.index.name = "doc_id"; full = full.reset_index()
    full.to_csv(RESULTS_DIR / "rq2_corpus_full.csv", index=False)

    uk = pd.DataFrame(uk_records).drop_duplicates(subset=["author", "text"]).reset_index(drop=True)
    uk.index.name = "doc_id"; uk = uk.reset_index()
    uk.to_csv(RESULTS_DIR / "rq2_corpus.csv", index=False)

    print(f"\nrq2_corpus_full.csv: {len(full):,} docs")
    print(full.groupby(["group", "kind"]).size().to_string())
    print(f"\nrq2_corpus.csv (UK): {len(uk):,} docs")
    print(uk.groupby(["group", "kind"]).size().to_string())
