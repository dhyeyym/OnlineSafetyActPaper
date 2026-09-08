"""
07_validation.py — Spot checks, annotation sampling, and scoring.

Usage:
  python 07_validation.py spot_check
  python 07_validation.py make_sample
  python 07_validation.py score_sample
  python 07_validation.py recount
"""
import sys
import pandas as pd
from config import RESULTS_DIR, TOPIC_LABELS, LDA_K

SEED = 42
SPOT_N = 10
SAMPLE_N = 50

def norm(df):
    for c in ["group", "kind", "author", "created_utc"]:
        if c in df.columns: df[c] = df[c].astype(str).str.strip()
    return df

# --- Spot check: random sample per topic ---
def spot_check():
    for group in ["vpn", "politics"]:
        path = RESULTS_DIR / f"lda_{group}_uk_assignments.csv"
        if not path.exists(): continue
        df = pd.read_csv(path, dtype=str)
        df["topic_id"] = df["topic_id"].astype(int)
        df["topic_prob"] = df["topic_prob"].astype(float)
        rows = []
        for tid in sorted(df["topic_id"].unique()):
            sub = df[df["topic_id"] == tid]
            sample = sub.sample(min(SPOT_N, len(sub)), random_state=SEED)
            for rank, (_, row) in enumerate(sample.iterrows(), 1):
                rows.append({"group": group, "topic_id": tid,
                             "label": TOPIC_LABELS[group].get(tid, f"Topic {tid}"),
                             "rank": rank, "subreddit": row["subreddit"],
                             "topic_prob": round(row["topic_prob"], 3),
                             "text": str(row["text"])[:500]})
        out = pd.DataFrame(rows)
        fname = f"lda_{group}_spot_check.csv"
        out.to_csv(RESULTS_DIR / fname, index=False)
        print(f"{group}: {len(out)} rows -> {fname}")

# --- Make blind annotation sample from divergent docs ---
def make_sample():
    keys = ["group", "kind", "author", "created_utc"]
    corpus  = norm(pd.read_csv(RESULTS_DIR / "rq2_corpus.csv", dtype=str))
    cardiff = norm(pd.read_csv(RESULTS_DIR / "rq2_sentiment_cardiff.csv", dtype=str))
    gemini  = norm(pd.read_csv(RESULTS_DIR / "rq2_sentiment_gemini.csv", dtype=str))

    c = cardiff[keys + ["cardiff_label"]].drop_duplicates(keys)
    g = gemini[keys + ["gemini_label"]].drop_duplicates(keys)
    df = corpus[keys + ["text"]].drop_duplicates(keys).merge(c, on=keys).merge(g, on=keys)
    div = df[df["cardiff_label"] != df["gemini_label"]].copy()
    print("Divergent:", div.groupby("group").size().to_dict())

    parts = [div[div["group"] == grp].sample(min(SAMPLE_N, len(div[div["group"] == grp])),
             random_state=SEED) for grp in ["vpn", "politics"]]
    sample = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    sample["sample_id"] = range(len(sample))

    annot = sample[["sample_id", "group"]].copy()
    annot["text"] = sample["text"].str.slice(0, 1500)
    annot["human_label"] = ""
    annot.to_csv(RESULTS_DIR / "adjudication_TOANNOTATE.csv", index=False)

    key = sample[["sample_id", "group", "kind", "author", "created_utc", "cardiff_label", "gemini_label"]]
    key.to_csv(RESULTS_DIR / "adjudication_key.csv", index=False)
    print(f"Sampled {len(sample)}. Wrote adjudication_TOANNOTATE.csv + adjudication_key.csv")

# --- Score annotations ---
def score_sample():
    annot = pd.read_csv(RESULTS_DIR / "adjudication_TOANNOTATE.csv")
    key = pd.read_csv(RESULTS_DIR / "adjudication_key.csv")
    annot["human_label"] = annot["human_label"].astype(str).str.strip().str.lower()
    valid = {"negative", "neutral", "positive"}
    m = annot.merge(key, on=["sample_id", "group"])
    m = m[m["human_label"].isin(valid)]
    n = len(m)
    ag_gem = (m["human_label"] == m["gemini_label"]).sum()
    ag_rob = (m["human_label"] == m["cardiff_label"]).sum()
    print(f"\nN={n}  Gemini: {ag_gem} ({ag_gem/n*100:.0f}%)  RoBERTa: {ag_rob} ({ag_rob/n*100:.0f}%)  Neither: {n-ag_gem-ag_rob} ({(n-ag_gem-ag_rob)/n*100:.0f}%)")
    for grp, gdf in m.groupby("group"):
        k = len(gdf); ga = (gdf["human_label"] == gdf["gemini_label"]).sum()
        ra = (gdf["human_label"] == gdf["cardiff_label"]).sum()
        print(f"  {grp}: N={k} Gemini {ga/k*100:.0f}% RoBERTa {ra/k*100:.0f}%")

# --- Recount prose numbers ---
def recount():
    corpus = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")
    print(f"UK corpus: {len(corpus):,}")
    print(corpus.groupby("group").size().to_string())

    total_assigned = 0
    for group in ["vpn", "politics"]:
        ap = RESULTS_DIR / f"lda_{group}_uk_assignments.csv"
        if ap.exists():
            n = len(pd.read_csv(ap)); n_group = (corpus["group"] == group).sum()
            print(f"  LDA {group}: {n:,} assigned of {n_group:,} (dropped {n_group-n:,})")
            total_assigned += n
    print(f"  Total assigned: {total_assigned:,}, dropped: {len(corpus)-total_assigned:,}")

    c = norm(pd.read_csv(RESULTS_DIR / "rq2_sentiment_cardiff.csv"))
    g = norm(pd.read_csv(RESULTS_DIR / "rq2_sentiment_gemini.csv"))
    gem_col = next((col for col in ["gemini_label", "label"] if col in g.columns), None)
    m = c[["author", "created_utc", "cardiff_label"]].drop_duplicates(["author", "created_utc"]).merge(
        g[["author", "created_utc", gem_col]].drop_duplicates(["author", "created_utc"]),
        on=["author", "created_utc"])
    agree = (m["cardiff_label"] == m[gem_col]).sum()
    print(f"\nSentiment: {len(m):,} docs, agree {agree/len(m)*100:.1f}%, disagree {len(m)-agree:,} ({(len(m)-agree)/len(m)*100:.1f}%)")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "recount"
    {"spot_check": spot_check, "make_sample": make_sample,
     "score_sample": score_sample, "recount": recount}[cmd]()
