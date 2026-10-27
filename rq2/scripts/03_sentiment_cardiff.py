import numpy as np
import pandas as pd
import torch
from scipy.special import softmax
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from config import RESULTS_DIR, CARDIFF_MODEL, SENTIMENT_LABELS

BATCH_SIZE = 32
MAX_LENGTH = 512


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


def predict_batch(texts, tokenizer, model, device):
    encoded = tokenizer(texts, padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt").to(device)

    with torch.no_grad():
        logits = model(**encoded).logits.float().cpu().numpy()

    results = []
    for row in logits:
        scores = softmax(row)
        best = int(np.argmax(scores))

        results.append({
            "cardiff_label": SENTIMENT_LABELS[best],
            "cardiff_score_negative": round(float(scores[0]), 4),
            "cardiff_score_neutral": round(float(scores[1]), 4),
            "cardiff_score_positive": round(float(scores[2]), 4),
        })

    return results


def main():
    corpus = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")
    print(f"Corpus: {len(corpus):,} docs")

    device = get_device()
    print(f"Device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(CARDIFF_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(CARDIFF_MODEL)
    model.eval().to(device)

    results = []

    for start in tqdm(range(0, len(corpus), BATCH_SIZE), desc="Cardiff", unit="batch"):
        batch = corpus.iloc[start:start + BATCH_SIZE]
        predictions = predict_batch(batch["text"].fillna("").tolist(), tokenizer, model, device)

        for (_, row), prediction in zip(batch.iterrows(), predictions):
            record = {
                "doc_id": row["doc_id"],
                "group": row["group"],
                "kind": row["kind"],
                "subreddit": row["subreddit"],
                "author": row["author"],
                "created_utc": row["created_utc"],
            }
            record.update(prediction)
            results.append(record)

    out = pd.DataFrame(results)
    out.to_csv(RESULTS_DIR / "rq2_sentiment_cardiff.csv", index=False)

    print(f"\nSaved rq2_sentiment_cardiff.csv: {len(out):,} rows")
    print(out.groupby(["group", "cardiff_label"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
