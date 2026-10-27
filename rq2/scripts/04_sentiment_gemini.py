import asyncio
import json
import os
import sys

import httpx
import pandas as pd
from tqdm.asyncio import tqdm as async_tqdm

from config import RESULTS_DIR, GEMINI_MODEL, SENTIMENT_LABELS

BATCH_SIZE = 25
MAX_RETRIES = 8
CONCURRENCY = 8

GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

if not GEMINI_KEY:
    sys.exit("ERROR: set GEMINI_KEY")

SYSTEM_PROMPT = """You are classifying Reddit posts and comments about the UK Online Safety Act (OSA) for a research study.

For each post, assign a sentiment label based on the author's attitude toward the OSA and related privacy/regulation topics:
- negative: the author is critical, opposed, frustrated, or concerned about the OSA, age verification, government surveillance, or internet censorship
- neutral: the author is informational, factual, or does not express a clear opinion
- positive: the author supports the OSA, age verification, or related regulatory measures

Respond with ONLY a JSON array of labels, one per post, in the same order.
Example for 3 posts: ["negative", "neutral", "positive"]
No explanation, no other text."""


def all_valid(labels):
    for label in labels:
        if label not in SENTIMENT_LABELS:
            return False

    return True


def parse_response(raw, expected_count):
    raw = raw.strip().strip("`\n ")
    if raw.startswith("json"):
        raw = raw[4:]

    try:
        labels = json.loads(raw)

        if len(labels) == expected_count and all_valid(labels):
            return labels

        if abs(len(labels) - expected_count) <= 2:
            padded = (labels + ["neutral"] * expected_count)[:expected_count]
            if all_valid(padded):
                return padded
    except Exception:
        pass

    return None


def build_payload(texts):
    numbered = []
    for i, text in enumerate(texts):
        numbered.append(f"[{i + 1}] {text[:500]}")

    user_message = "\n\n".join(numbered)

    return {
        "contents": [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_message}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 300},
    }


async def classify_batch(client, semaphore, texts, batch_index):
    payload = build_payload(texts)

    async with semaphore:
        for _ in range(MAX_RETRIES):
            try:
                response = await client.post(GEMINI_URL, params={"key": GEMINI_KEY}, json=payload, timeout=60)
                data = response.json()

                if "error" in data:
                    await asyncio.sleep(30)
                    continue

                raw = data["candidates"][0]["content"]["parts"][0]["text"]
                labels = parse_response(raw, len(texts))
                if labels is not None:
                    return batch_index, labels
            except Exception:
                await asyncio.sleep(5)

    return batch_index, None


async def classify_all(texts):
    batches = []
    for start in range(0, len(texts), BATCH_SIZE):
        batches.append(texts[start:start + BATCH_SIZE])

    results = [None] * len(batches)
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient() as client:
        tasks = []
        for i, batch in enumerate(batches):
            tasks.append(classify_batch(client, semaphore, batch, i))

        for task in async_tqdm(asyncio.as_completed(tasks), total=len(tasks), unit="batch"):
            batch_index, labels = await task
            results[batch_index] = labels

    labels = []
    for i, batch in enumerate(batches):
        if results[i] is None:
            labels.extend(["neutral"] * len(batch))
        else:
            labels.extend(results[i])

    return labels


def main():
    corpus = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")
    print(f"Corpus: {len(corpus):,} docs")

    labels = asyncio.run(classify_all(corpus["text"].fillna("").tolist()))

    out = corpus[["doc_id", "group", "kind", "subreddit", "author", "created_utc"]].copy()
    out["gemini_label"] = labels
    out.to_csv(RESULTS_DIR / "rq2_sentiment_gemini.csv", index=False)

    print(f"\nSaved rq2_sentiment_gemini.csv: {len(out):,} rows")
    print(out.groupby(["group", "gemini_label"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
