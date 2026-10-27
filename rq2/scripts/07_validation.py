import sys

import pandas as pd

from config import RESULTS_DIR, TOPIC_LABELS

SEED = 42
SPOT_N = 10
SAMPLE_N = 50

GROUPS = ["vpn", "politics"]
MATCH_KEYS = ["group", "kind", "author", "created_utc"]
VALID_LABELS = {"negative", "neutral", "positive"}


def normalise(df):
    for column in MATCH_KEYS:
        if column in df.columns:
            df[column] = df[column].astype(str).str.strip()

    return df


def percent(part, whole):
    return part / whole * 100


def spot_check():
    for group in GROUPS:
        path = RESULTS_DIR / f"lda_{group}_uk_assignments.csv"
        if not path.exists():
            continue

        df = pd.read_csv(path, dtype=str)
        df["topic_id"] = df["topic_id"].astype(int)
        df["topic_prob"] = df["topic_prob"].astype(float)

        rows = []
        for topic_id in sorted(df["topic_id"].unique()):
            topic_docs = df[df["topic_id"] == topic_id]
            sample = topic_docs.sample(min(SPOT_N, len(topic_docs)), random_state=SEED)

            rank = 1
            for _, row in sample.iterrows():
                rows.append({
                    "group": group,
                    "topic_id": topic_id,
                    "label": TOPIC_LABELS[group].get(topic_id, f"Topic {topic_id}"),
                    "rank": rank,
                    "subreddit": row["subreddit"],
                    "topic_prob": round(row["topic_prob"], 3),
                    "text": str(row["text"])[:500],
                })
                rank += 1

        out = pd.DataFrame(rows)
        filename = f"lda_{group}_spot_check.csv"
        out.to_csv(RESULTS_DIR / filename, index=False)
        print(f"{group}: {len(out)} rows -> {filename}")


def make_sample():
    corpus = normalise(pd.read_csv(RESULTS_DIR / "rq2_corpus.csv", dtype=str))
    cardiff = normalise(pd.read_csv(RESULTS_DIR / "rq2_sentiment_cardiff.csv", dtype=str))
    gemini = normalise(pd.read_csv(RESULTS_DIR / "rq2_sentiment_gemini.csv", dtype=str))

    cardiff_labels = cardiff[MATCH_KEYS + ["cardiff_label"]].drop_duplicates(MATCH_KEYS)
    gemini_labels = gemini[MATCH_KEYS + ["gemini_label"]].drop_duplicates(MATCH_KEYS)

    df = corpus[MATCH_KEYS + ["text"]].drop_duplicates(MATCH_KEYS)
    df = df.merge(cardiff_labels, on=MATCH_KEYS).merge(gemini_labels, on=MATCH_KEYS)

    divergent = df[df["cardiff_label"] != df["gemini_label"]].copy()
    print("Divergent:", divergent.groupby("group").size().to_dict())

    parts = []
    for group in GROUPS:
        group_divergent = divergent[divergent["group"] == group]
        parts.append(group_divergent.sample(min(SAMPLE_N, len(group_divergent)), random_state=SEED))

    sample = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    sample["sample_id"] = range(len(sample))

    to_annotate = sample[["sample_id", "group"]].copy()
    to_annotate["text"] = sample["text"].str.slice(0, 1500)
    to_annotate["human_label"] = ""
    to_annotate.to_csv(RESULTS_DIR / "adjudication_TOANNOTATE.csv", index=False)

    key_columns = ["sample_id", "group", "kind", "author", "created_utc", "cardiff_label", "gemini_label"]
    sample[key_columns].to_csv(RESULTS_DIR / "adjudication_key.csv", index=False)

    print(f"Sampled {len(sample)}. Wrote adjudication_TOANNOTATE.csv + adjudication_key.csv")


def score_sample():
    annotated = pd.read_csv(RESULTS_DIR / "adjudication_TOANNOTATE.csv")
    key = pd.read_csv(RESULTS_DIR / "adjudication_key.csv")
    annotated["human_label"] = annotated["human_label"].astype(str).str.strip().str.lower()

    merged = annotated.merge(key, on=["sample_id", "group"])
    merged = merged[merged["human_label"].isin(VALID_LABELS)]

    total = len(merged)
    gemini_agree = (merged["human_label"] == merged["gemini_label"]).sum()
    roberta_agree = (merged["human_label"] == merged["cardiff_label"]).sum()
    neither = total - gemini_agree - roberta_agree

    print(
        f"\nN={total}  "
        f"Gemini: {gemini_agree} ({percent(gemini_agree, total):.0f}%)  "
        f"RoBERTa: {roberta_agree} ({percent(roberta_agree, total):.0f}%)  "
        f"Neither: {neither} ({percent(neither, total):.0f}%)"
    )

    for group, group_df in merged.groupby("group"):
        group_total = len(group_df)
        group_gemini = (group_df["human_label"] == group_df["gemini_label"]).sum()
        group_roberta = (group_df["human_label"] == group_df["cardiff_label"]).sum()
        print(
            f"  {group}: N={group_total} "
            f"Gemini {percent(group_gemini, group_total):.0f}% "
            f"RoBERTa {percent(group_roberta, group_total):.0f}%"
        )


def merge_sentiment(cardiff, gemini, gemini_column):
    if "doc_id" in cardiff.columns and "doc_id" in gemini.columns:
        cardiff_labels = cardiff[["doc_id", "cardiff_label"]].drop_duplicates("doc_id")
        gemini_labels = gemini[["doc_id", gemini_column]].drop_duplicates("doc_id")
        return cardiff_labels.merge(gemini_labels, on="doc_id")

    keys = []
    for column in ["author", "created_utc"]:
        if column in cardiff.columns and column in gemini.columns:
            keys.append(column)

    cardiff_labels = cardiff[keys + ["cardiff_label"]].drop_duplicates(keys)
    gemini_labels = gemini[keys + [gemini_column]].drop_duplicates(keys)
    return cardiff_labels.merge(gemini_labels, on=keys)


def find_gemini_column(gemini):
    for column in ["gemini_label", "label"]:
        if column in gemini.columns:
            return column

    return None


def recount():
    corpus = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")
    print(f"UK corpus: {len(corpus):,}")
    print(corpus.groupby("group").size().to_string())

    total_assigned = 0
    for group in GROUPS:
        path = RESULTS_DIR / f"lda_{group}_uk_assignments.csv"
        if not path.exists():
            continue

        assigned = len(pd.read_csv(path))
        group_size = (corpus["group"] == group).sum()
        print(f"  LDA {group}: {assigned:,} assigned of {group_size:,} (dropped {group_size - assigned:,})")
        total_assigned += assigned

    print(f"  Total assigned: {total_assigned:,}, dropped: {len(corpus) - total_assigned:,}")

    cardiff = pd.read_csv(RESULTS_DIR / "rq2_sentiment_cardiff.csv")
    gemini = pd.read_csv(RESULTS_DIR / "rq2_sentiment_gemini.csv")
    gemini_column = find_gemini_column(gemini)

    merged = merge_sentiment(cardiff, gemini, gemini_column)
    total = len(merged)
    agree = (merged["cardiff_label"] == merged[gemini_column]).sum()
    disagree = total - agree

    print(
        f"\nSentiment: {total:,} docs, "
        f"agree {percent(agree, total):.1f}%, "
        f"disagree {disagree:,} ({percent(disagree, total):.1f}%)"
    )


COMMANDS = {
    "spot_check": spot_check,
    "make_sample": make_sample,
    "score_sample": score_sample,
    "recount": recount,
}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "recount"

    COMMANDS[command]()
