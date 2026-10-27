import pandas as pd

from config import (
    ORIGINAL_DIR, GEO_DIR, RESULTS_DIR,
    START_DATE, END_DATE, SKIP_AUTHORS,
    VPN_SUBREDDITS, POLITICS_SUBREDDITS, UK_GEO_SUBREDDITS,
    CLASSIFIED_FILES,
)

MIN_TEXT_LENGTH = 10


def find_subreddit_file(directory, subreddit, kind):
    path = directory / f"{subreddit}_{kind}.csv"
    if path.exists():
        return path

    target = f"{subreddit.lower()}_{kind}.csv"
    for candidate in directory.iterdir():
        if candidate.name.lower() == target:
            return candidate

    return None


def load_authors_from_raw(subreddits, directory):
    authors = set()
    subreddits_by_lowercase = {subreddit.lower(): subreddit for subreddit in subreddits}

    for _, subreddit in sorted(subreddits_by_lowercase.items()):
        for kind in ("submissions", "comments"):
            path = find_subreddit_file(directory, subreddit, kind)
            if path is None:
                continue

            try:
                for chunk in pd.read_csv(path, usecols=["author"], dtype=str, chunksize=500_000):
                    valid = chunk["author"].dropna()
                    valid = valid[~valid.isin(SKIP_AUTHORS)]
                    authors.update(valid.tolist())
            except Exception:
                pass

    return authors


def build_uk_authors():
    geo_authors = load_authors_from_raw(UK_GEO_SUBREDDITS, GEO_DIR)
    vpn_authors = load_authors_from_raw(VPN_SUBREDDITS, ORIGINAL_DIR)
    politics_authors = load_authors_from_raw(POLITICS_SUBREDDITS, ORIGINAL_DIR)

    uk_authors = geo_authors & (vpn_authors | politics_authors)
    print(f"UK authors: {len(uk_authors):,}")

    return uk_authors


def get_text(row, kind):
    if kind == "comment":
        return str(row.get("body", "") or "").strip()

    title = str(row.get("title", "") or "").strip()
    selftext = str(row.get("selftext", "") or "").strip()

    if selftext.lower() in ("", "[deleted]", "[removed]"):
        return title

    return f"{title} {selftext}".strip()


def load_relevant_rows(path, relevance_column, start, end):
    df = pd.read_csv(path, dtype=str)
    df = df[df[relevance_column].astype(int) == 1]
    df = df[df["author"].notna() & ~df["author"].isin(SKIP_AUTHORS)]

    timestamps = pd.to_datetime(df["created_utc"].astype(float), unit="s", errors="coerce")
    return df[(timestamps >= start) & (timestamps <= end)].copy()


def to_corpus(records):
    corpus = pd.DataFrame(records).drop_duplicates(subset=["author", "text"]).reset_index(drop=True)
    corpus.index.name = "doc_id"
    return corpus.reset_index()


def main():
    start = pd.Timestamp(START_DATE)
    end = pd.Timestamp(END_DATE)

    uk_authors = build_uk_authors()

    all_records = []
    uk_records = []

    for filename, group, kind, relevance_column in CLASSIFIED_FILES:
        path = RESULTS_DIR / filename
        if not path.exists():
            print(f"  MISSING: {filename}")
            continue

        df = load_relevant_rows(path, relevance_column, start, end)

        all_count = 0
        uk_count = 0

        for _, row in df.iterrows():
            text = get_text(row, kind)
            if len(text.strip()) < MIN_TEXT_LENGTH:
                continue

            record = {
                "group": group,
                "kind": kind,
                "subreddit": row.get("subreddit", ""),
                "author": row.get("author", ""),
                "created_utc": row.get("created_utc", ""),
                "text": text,
            }

            all_records.append(record)
            all_count += 1

            if row.get("author") in uk_authors:
                uk_records.append(record)
                uk_count += 1

        print(f"  {filename}: {all_count:,} relevant ({uk_count:,} UK)")

    full = to_corpus(all_records)
    full.to_csv(RESULTS_DIR / "rq2_corpus_all_authors.csv", index=False)

    uk = to_corpus(uk_records)
    uk.to_csv(RESULTS_DIR / "rq2_corpus.csv", index=False)

    print(f"\nrq2_corpus_all_authors.csv: {len(full):,} docs")
    print(full.groupby(["group", "kind"]).size().to_string())

    print(f"\nrq2_corpus.csv (UK): {len(uk):,} docs")
    print(uk.groupby(["group", "kind"]).size().to_string())


if __name__ == "__main__":
    main()
