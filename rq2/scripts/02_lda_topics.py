import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import spacy
from gensim import corpora
from gensim.models import LdaModel

from config import RESULTS_DIR, LDA_K, LDA_RANDOM_STATE, LDA_PASSES, EXTRA_STOPWORDS, TOPIC_LABELS

nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
STOPWORDS = nlp.Defaults.stop_words | EXTRA_STOPWORDS

TOP_WORDS = 10
TOP_DOCS = 5
MIN_TOKENS = 3


def keep_token(token):
    lemma = token.lemma_.lower()

    if token.is_punct or token.is_space:
        return False
    if lemma in STOPWORDS:
        return False
    if len(token.lemma_) <= 2:
        return False

    return token.lemma_.isalpha()


def preprocess(texts, batch_size=500):
    tokenized = []

    for start in range(0, len(texts), batch_size):
        batch = list(nlp.pipe(texts[start:start + batch_size], batch_size=batch_size))

        for doc in batch:
            tokens = []
            for token in doc:
                if keep_token(token):
                    tokens.append(token.lemma_.lower())
            tokenized.append(tokens)

        if (start // batch_size) % 10 == 0:
            print(f"  {min(start + batch_size, len(texts)):,}/{len(texts):,}")

    return tokenized


def topic_label(label_map, topic_id):
    return label_map.get(topic_id, f"Topic {topic_id}")


def save_topic_words(lda, k, group):
    topic_words = []
    for topic_id in range(k):
        words = [word for word, _ in lda.show_topic(topic_id, topn=TOP_WORDS)]
        topic_words.append(words)

    rows = []
    for topic_id, words in enumerate(topic_words):
        rows.append({"topic_id": topic_id, "top_words": ", ".join(words)})

    pd.DataFrame(rows).to_csv(RESULTS_DIR / f"lda_{group}_topics.csv", index=False)

    return topic_words


def infer_topic_probabilities(lda, bows, k):
    probabilities = np.zeros((len(bows), k))

    for i, bow in enumerate(bows):
        for topic_id, probability in lda.get_document_topics(bow, minimum_probability=0):
            probabilities[i, topic_id] = probability

    return probabilities


def save_prevalence(probabilities, topic_words, label_map, k, group):
    mass = probabilities.sum(axis=0)
    share = mass / mass.sum() * 100

    prevalence = pd.DataFrame({
        "topic_id": range(k),
        "label": [topic_label(label_map, i) for i in range(k)],
        "top_words": [", ".join(words) for words in topic_words],
        "prevalence_pct": np.round(share, 1),
    })
    prevalence = prevalence.sort_values("prevalence_pct", ascending=False)

    prevalence.to_csv(RESULTS_DIR / f"lda_{group}_prevalence.csv", index=False)
    print(prevalence[["topic_id", "label", "prevalence_pct"]].to_string(index=False))


def save_top_docs(uk_docs, assignments, top_probabilities, k, group):
    rows = []

    for topic_id in range(k):
        indices = np.where(assignments == topic_id)[0]
        if len(indices) == 0:
            continue

        order = np.argsort(top_probabilities[indices])[::-1][:TOP_DOCS]
        top_indices = indices[order]

        for rank, i in enumerate(top_indices):
            row = uk_docs.iloc[i]
            rows.append({
                "topic_id": topic_id,
                "rank": rank + 1,
                "prob": round(float(top_probabilities[i]), 4),
                "subreddit": row.get("subreddit", ""),
                "text": str(row["text"])[:500],
            })

    pd.DataFrame(rows).to_csv(RESULTS_DIR / f"lda_{group}_topdocs.csv", index=False)


def run_group(group, full_corpus, uk_corpus):
    k = LDA_K[group]
    label_map = TOPIC_LABELS[group]

    full_texts = full_corpus[full_corpus["group"] == group]["text"].astype(str).tolist()
    uk_group = uk_corpus[uk_corpus["group"] == group].reset_index(drop=True)
    uk_texts = uk_group["text"].astype(str).tolist()
    print(f"\n{group.upper()} — full: {len(full_texts):,}, UK: {len(uk_texts):,}, K={k}")

    print("Preprocessing full corpus...")
    full_tokens = []
    for tokens in preprocess(full_texts):
        if len(tokens) >= MIN_TOKENS:
            full_tokens.append(tokens)

    dictionary = corpora.Dictionary(full_tokens)
    dictionary.filter_extremes(no_below=5, no_above=0.85)
    full_bows = [dictionary.doc2bow(tokens) for tokens in full_tokens]

    print(f"Fitting LDA K={k}, passes={LDA_PASSES}...")
    lda = LdaModel(
        corpus=full_bows,
        id2word=dictionary,
        num_topics=k,
        random_state=LDA_RANDOM_STATE,
        passes=LDA_PASSES,
        alpha="auto",
        eta="auto",
    )

    topic_words = save_topic_words(lda, k, group)

    print("Inferring topics for UK corpus...")
    uk_tokens = preprocess(uk_texts)

    kept_indices = []
    for i, tokens in enumerate(uk_tokens):
        if len(tokens) >= MIN_TOKENS:
            kept_indices.append(i)

    uk_bows = [dictionary.doc2bow(uk_tokens[i]) for i in kept_indices]
    uk_docs = uk_group.iloc[kept_indices].reset_index(drop=True)
    print(f"  UK docs assigned: {len(kept_indices):,} (dropped {len(uk_texts) - len(kept_indices):,})")

    probabilities = infer_topic_probabilities(lda, uk_bows, k)
    np.save(RESULTS_DIR / f"lda_{group}_uk_probs.npy", probabilities)

    assignments = probabilities.argmax(axis=1)
    top_probabilities = probabilities.max(axis=1)

    save_prevalence(probabilities, topic_words, label_map, k, group)

    uk_docs = uk_docs.copy()
    uk_docs["topic_id"] = assignments
    uk_docs["topic_prob"] = top_probabilities
    uk_docs.to_csv(RESULTS_DIR / f"lda_{group}_uk_assignments.csv", index=False)

    save_top_docs(uk_docs, assignments, top_probabilities, k, group)


def main():
    full = pd.read_csv(RESULTS_DIR / "rq2_corpus_all_authors.csv")
    uk = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")

    for group in ["vpn", "politics"]:
        run_group(group, full, uk)

    print("\nDone. Inspect lda_{group}_topics.csv and update TOPIC_LABELS in config.py if needed.")


if __name__ == "__main__":
    main()
