"""
02_lda_topics.py — Fit LDA on full corpus, assign topics to UK corpus.

Outputs per group:
  lda_{group}_topics.csv, lda_{group}_uk_probs.npy,
  lda_{group}_uk_assignments.csv, lda_{group}_prevalence.csv,
  lda_{group}_topdocs.csv
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import spacy
from gensim import corpora
from gensim.models import LdaModel
from config import RESULTS_DIR, LDA_K, LDA_RANDOM_STATE, LDA_PASSES, EXTRA_STOPWORDS, TOPIC_LABELS

nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
STOPWORDS = nlp.Defaults.stop_words | EXTRA_STOPWORDS
TOP_WORDS = 10
TOP_DOCS  = 5
MIN_TOKENS = 3

def preprocess(texts, batch_size=500):
    tokenized = []
    for i in range(0, len(texts), batch_size):
        batch = list(nlp.pipe(texts[i:i+batch_size], batch_size=batch_size))
        for doc in batch:
            tokens = [t.lemma_.lower() for t in doc
                      if not t.is_punct and not t.is_space
                      and t.lemma_.lower() not in STOPWORDS
                      and len(t.lemma_) > 2 and t.lemma_.isalpha()]
            tokenized.append(tokens)
        if (i // batch_size) % 10 == 0:
            print(f"  {min(i+batch_size, len(texts)):,}/{len(texts):,}")
    return tokenized

def run_group(group, full_corpus, uk_corpus):
    k = LDA_K[group]
    label_map = TOPIC_LABELS[group]
    full_texts = full_corpus[full_corpus["group"] == group]["text"].astype(str).tolist()
    uk_subdf   = uk_corpus[uk_corpus["group"] == group].reset_index(drop=True)
    uk_texts   = uk_subdf["text"].astype(str).tolist()
    print(f"\n{group.upper()} — full: {len(full_texts):,}, UK: {len(uk_texts):,}, K={k}")

    print("Preprocessing full corpus...")
    tok_full = [t for t in preprocess(full_texts) if len(t) >= MIN_TOKENS]
    dictionary = corpora.Dictionary(tok_full)
    dictionary.filter_extremes(no_below=5, no_above=0.85)
    bow_full = [dictionary.doc2bow(t) for t in tok_full]

    print(f"Fitting LDA K={k}, passes={LDA_PASSES}...")
    lda = LdaModel(corpus=bow_full, id2word=dictionary, num_topics=k,
                   random_state=LDA_RANDOM_STATE, passes=LDA_PASSES, alpha="auto", eta="auto")

    topic_words = [[w for w, _ in lda.show_topic(tid, topn=TOP_WORDS)] for tid in range(k)]
    pd.DataFrame([{"topic_id": i, "top_words": ", ".join(w)}
                  for i, w in enumerate(topic_words)]).to_csv(
        RESULTS_DIR / f"lda_{group}_topics.csv", index=False)

    print("Inferring topics for UK corpus...")
    tok_uk = preprocess(uk_texts)
    valid  = [i for i, t in enumerate(tok_uk) if len(t) >= MIN_TOKENS]
    bow_uk = [dictionary.doc2bow(tok_uk[i]) for i in valid]
    uk_valid = uk_subdf.iloc[valid].reset_index(drop=True)
    print(f"  UK docs assigned: {len(valid):,} (dropped {len(uk_texts)-len(valid):,})")

    all_probs = np.zeros((len(bow_uk), k))
    for i, bow in enumerate(bow_uk):
        for tid, prob in lda.get_document_topics(bow, minimum_probability=0):
            all_probs[i, tid] = prob
    np.save(RESULTS_DIR / f"lda_{group}_uk_probs.npy", all_probs)

    assignments = all_probs.argmax(axis=1)
    top_probs   = all_probs.max(axis=1)

    
    mass  = all_probs.sum(axis=0)
    share = mass / mass.sum() * 100
    prev = pd.DataFrame({"topic_id": range(k),
                          "label": [label_map.get(i, f"Topic {i}") for i in range(k)],
                          "top_words": [", ".join(w) for w in topic_words],
                          "prevalence_pct": np.round(share, 1)
                         }).sort_values("prevalence_pct", ascending=False)
    prev.to_csv(RESULTS_DIR / f"lda_{group}_prevalence.csv", index=False)
    print(prev[["topic_id", "label", "prevalence_pct"]].to_string(index=False))

    
    uk_valid = uk_valid.copy()
    uk_valid["topic_id"]   = assignments
    uk_valid["topic_prob"] = top_probs
    uk_valid.to_csv(RESULTS_DIR / f"lda_{group}_uk_assignments.csv", index=False)

    
    rows = []
    for tid in range(k):
        idx = np.where(assignments == tid)[0]
        if len(idx) == 0: continue
        top_idx = idx[np.argsort(top_probs[idx])[::-1][:TOP_DOCS]]
        for rank, i in enumerate(top_idx):
            row = uk_valid.iloc[i]
            rows.append({"topic_id": tid, "rank": rank+1,
                         "prob": round(float(top_probs[i]), 4),
                         "subreddit": row.get("subreddit", ""),
                         "text": str(row["text"])[:500]})
    pd.DataFrame(rows).to_csv(RESULTS_DIR / f"lda_{group}_topdocs.csv", index=False)

if __name__ == "__main__":
    full = pd.read_csv(RESULTS_DIR / "rq2_corpus_all_authors.csv")
    uk   = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")
    for group in ["vpn", "politics"]:
        run_group(group, full, uk)
    print("\nDone. Inspect lda_{group}_topics.csv and update TOPIC_LABELS in config.py if needed.")
