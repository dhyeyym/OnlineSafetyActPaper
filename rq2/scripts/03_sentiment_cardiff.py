"""
03_sentiment_cardiff.py — Run Cardiff RoBERTa sentiment on the UK corpus.

Output: rq2_sentiment_cardiff.csv
"""
import time
import pandas as pd
import torch
import numpy as np
from scipy.special import softmax
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
from config import RESULTS_DIR, CARDIFF_MODEL, SENTIMENT_LABELS

BATCH_SIZE = 32
MAX_LENGTH = 512

def get_device():
    if torch.cuda.is_available(): return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available(): return torch.device("mps")
    return torch.device("cpu")

def predict_batch(texts, tok, mdl, device):
    encoded = tok(texts, padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = mdl(**encoded).logits.float().cpu().numpy()
    results = []
    for row in logits:
        scores = softmax(row)
        idx = int(np.argmax(scores))
        results.append({"cardiff_label": SENTIMENT_LABELS[idx],
                        "cardiff_score_negative": round(float(scores[0]), 4),
                        "cardiff_score_neutral":  round(float(scores[1]), 4),
                        "cardiff_score_positive": round(float(scores[2]), 4)})
    return results

if __name__ == "__main__":
    corpus = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")
    print(f"Corpus: {len(corpus):,} docs")

    device = get_device(); print(f"Device: {device}")
    tok = AutoTokenizer.from_pretrained(CARDIFF_MODEL)
    mdl = AutoModelForSequenceClassification.from_pretrained(CARDIFF_MODEL)
    mdl.eval().to(device)

    all_results = []
    for i in tqdm(range(0, len(corpus), BATCH_SIZE), desc="Cardiff", unit="batch"):
        batch_df = corpus.iloc[i:i+BATCH_SIZE]
        batch_results = predict_batch(batch_df["text"].fillna("").tolist(), tok, mdl, device)
        for (_, row), sent in zip(batch_df.iterrows(), batch_results):
            all_results.append({
                "doc_id": row["doc_id"], "group": row["group"], "kind": row["kind"],
                "subreddit": row["subreddit"], "author": row["author"],
                "created_utc": row["created_utc"], **sent})

    out = pd.DataFrame(all_results)
    out.to_csv(RESULTS_DIR / "rq2_sentiment_cardiff.csv", index=False)
    print(f"\nSaved rq2_sentiment_cardiff.csv: {len(out):,} rows")
    print(out.groupby(["group", "cardiff_label"]).size().unstack(fill_value=0))
