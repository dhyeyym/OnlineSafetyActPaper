"""
04_sentiment_gemini.py — Run Gemini sentiment on the UK corpus.

Requires GEMINI_KEY environment variable.
Output: rq2_sentiment_gemini.csv
"""
import os, json, asyncio, sys
import pandas as pd
import httpx
from tqdm.asyncio import tqdm as atqdm
from config import RESULTS_DIR, GEMINI_MODEL, SENTIMENT_LABELS

BATCH_SIZE   = 25
MAX_RETRIES  = 8
CONCURRENCY  = 8
GEMINI_KEY   = os.getenv("GEMINI_KEY", "").strip()
GEMINI_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
if not GEMINI_KEY: sys.exit("ERROR: set GEMINI_KEY")

SYSTEM_PROMPT = """You are classifying Reddit posts and comments about the UK Online Safety Act (OSA) for a research study.

For each post, assign a sentiment label based on the author's attitude toward the OSA and related privacy/regulation topics:
- negative: the author is critical, opposed, frustrated, or concerned about the OSA, age verification, government surveillance, or internet censorship
- neutral: the author is informational, factual, or does not express a clear opinion
- positive: the author supports the OSA, age verification, or related regulatory measures

Respond with ONLY a JSON array of labels, one per post, in the same order.
Example for 3 posts: ["negative", "neutral", "positive"]
No explanation, no other text."""

def parse_response(raw, n):
    raw = raw.strip().strip("`\n ")
    if raw.startswith("json"): raw = raw[4:]
    try:
        labels = json.loads(raw)
        valid = set(SENTIMENT_LABELS)
        if len(labels) == n and all(l in valid for l in labels): return labels
        if abs(len(labels) - n) <= 2:
            labels = (labels + ["neutral"] * n)[:n]
            if all(l in valid for l in labels): return labels
    except Exception: pass
    return None

async def classify_batch(client, sem, texts, idx):
    user_msg = "\n\n".join(f"[{i+1}] {t[:500]}" for i, t in enumerate(texts))
    payload = {"contents": [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_msg}]}],
               "generationConfig": {"temperature": 0, "maxOutputTokens": 300}}
    async with sem:
        for attempt in range(MAX_RETRIES):
            try:
                r = await client.post(GEMINI_URL, params={"key": GEMINI_KEY}, json=payload, timeout=60)
                data = r.json()
                if "error" in data: await asyncio.sleep(30); continue
                raw = data["candidates"][0]["content"]["parts"][0]["text"]
                labs = parse_response(raw, len(texts))
                if labs is not None: return idx, labs
            except Exception: await asyncio.sleep(5)
    return idx, None

async def classify_all(texts):
    batches = [texts[i:i+BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
    results = [None] * len(batches)
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = [classify_batch(client, sem, b, i) for i, b in enumerate(batches)]
        for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), unit="batch"):
            idx, labs = await coro
            results[idx] = labs
    out = []
    for i, b in enumerate(batches):
        out.extend(results[i] if results[i] is not None else ["neutral"] * len(b))
    return out

if __name__ == "__main__":
    corpus = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")
    print(f"Corpus: {len(corpus):,} docs")
    labels = asyncio.run(classify_all(corpus["text"].fillna("").tolist()))

    out = corpus[["doc_id", "group", "kind", "subreddit", "author", "created_utc"]].copy()
    out["gemini_label"] = labels
    out.to_csv(RESULTS_DIR / "rq2_sentiment_gemini.csv", index=False)
    print(f"\nSaved rq2_sentiment_gemini.csv: {len(out):,} rows")
    print(out.groupby(["group", "gemini_label"]).size().unstack(fill_value=0))
