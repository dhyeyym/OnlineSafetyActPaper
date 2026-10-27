import asyncio
import os
import sys

import httpx
import pandas as pd

from config import RESULTS_DIR, GEMINI_MODEL, TOPIC_LABELS

GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

if not GEMINI_KEY:
    sys.exit("ERROR: set GEMINI_KEY")

PROMPT = """You are analysing Reddit posts from UK users discussing the UK Online Safety Act (OSA).
Below are posts from a single discussion cluster. Summarise in 5-7 sentences:
1. What specific concerns or arguments do users raise?
2. What examples, analogies, or real-world cases do they cite?
3. What is the overall tone and framing?
Be concrete and specific. Quote or paraphrase specific points where useful."""

DOCS_PER_TOPIC = 15
MAX_RETRIES = 8


def top_documents(assignments, corpus, topic_id):
    merged = assignments.merge(corpus[["author", "created_utc", "text"]], on=["author", "created_utc"], how="inner")

    if "text_y" in merged.columns:
        text_column = "text_y"
    else:
        text_column = "text"

    topic_docs = merged[merged["topic_id"] == topic_id]
    topic_docs = topic_docs.sort_values("topic_prob", ascending=False).head(DOCS_PER_TOPIC)

    return topic_docs[text_column].tolist()


def build_payload(texts):
    numbered = []
    for i, text in enumerate(texts):
        numbered.append(f"[{i + 1}] {str(text)[:400]}")

    documents = "\n\n---\n\n".join(numbered)

    return {
        "contents": [{"role": "user", "parts": [{"text": PROMPT + "\n\n" + documents}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
    }


async def summarise_topic(client, assignments, corpus, topic_id, label):
    texts = top_documents(assignments, corpus, topic_id)
    if len(texts) == 0:
        return topic_id, label, ""

    payload = build_payload(texts)

    for attempt in range(MAX_RETRIES):
        try:
            response = await client.post(GEMINI_URL, params={"key": GEMINI_KEY}, json=payload, timeout=120)
            data = response.json()

            if "error" in data:
                await asyncio.sleep(30)
                continue

            summary = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\n=== T{topic_id:02d} — {label} ===\n{summary}")
            return topic_id, label, summary
        except Exception as error:
            print(f"  T{topic_id:02d} attempt {attempt + 1}: {error}")
            await asyncio.sleep(10)

    return topic_id, label, "FAILED"


async def summarise_group(group):
    label_map = TOPIC_LABELS[group]
    assignments = pd.read_csv(RESULTS_DIR / f"lda_{group}_uk_assignments.csv")
    corpus = pd.read_csv(RESULTS_DIR / "rq2_corpus.csv")

    for df in [assignments, corpus]:
        df["created_utc"] = df["created_utc"].astype(str).str.strip()
        df["author"] = df["author"].astype(str).str.strip()

    assignments["topic_id"] = assignments["topic_id"].astype(int)
    assignments["topic_prob"] = assignments["topic_prob"].astype(float)

    results = []

    async with httpx.AsyncClient() as client:
        for topic_id in sorted(assignments["topic_id"].unique()):
            label = label_map.get(topic_id, f"Topic {topic_id}")
            _, _, summary = await summarise_topic(client, assignments, corpus, topic_id, label)
            results.append({"topic_id": topic_id, "label": label, "summary": summary})

    out = pd.DataFrame(results)
    out.to_csv(RESULTS_DIR / f"topic_summaries_{group}.csv", index=False)
    print(f"\nSaved topic_summaries_{group}.csv")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        group = sys.argv[1]
    else:
        group = "vpn"

    asyncio.run(summarise_group(group))
