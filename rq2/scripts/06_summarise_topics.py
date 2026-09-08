"""
06_summarise_topics.py — LLM-assisted topic summarisation.

For each topic, takes the top-15 docs by posterior probability and
asks Gemini to summarise concerns, examples, and tone.

Requires GEMINI_KEY environment variable.
Output: topic_summaries_{group}.csv
"""
import os, asyncio, sys
import pandas as pd
import httpx
from config import RESULTS_DIR, GEMINI_MODEL, TOPIC_LABELS

GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
if not GEMINI_KEY: sys.exit("ERROR: set GEMINI_KEY")

PROMPT = """You are analysing Reddit posts from UK users discussing the UK Online Safety Act (OSA).
Below are posts from a single discussion cluster. Summarise in 5-7 sentences:
1. What specific concerns or arguments do users raise?
2. What examples, analogies, or real-world cases do they cite?
3. What is the overall tone and framing?
Be concrete and specific. Quote or paraphrase specific points where useful."""

DOCS_PER_TOPIC = 15

async def summarise_topic(client, assignments, corpus, tid, label):
    merged = assignments.merge(corpus[["author", "created_utc", "text"]],
                               on=["author", "created_utc"], how="inner")
    text_col = "text_y" if "text_y" in merged.columns else "text"
    tdf = merged[merged["topic_id"] == tid].sort_values("topic_prob", ascending=False).head(DOCS_PER_TOPIC)
    if len(tdf) == 0: return tid, label, ""

    doc_text = "\n\n---\n\n".join(f"[{i+1}] {str(t)[:400]}" for i, t in enumerate(tdf[text_col].tolist()))
    payload = {"contents": [{"role": "user", "parts": [{"text": PROMPT + "\n\n" + doc_text}]}],
               "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}}

    for attempt in range(8):
        try:
            resp = await client.post(GEMINI_URL, params={"key": GEMINI_KEY}, json=payload, timeout=120)
            data = resp.json()
            if "error" in data: await asyncio.sleep(30); continue
            summary = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\n=== T{tid:02d} — {label} ===\n{summary}")
            return tid, label, summary
        except Exception as e:
            print(f"  T{tid:02d} attempt {attempt+1}: {e}"); await asyncio.sleep(10)
    return tid, label, "FAILED"

async def main(group):
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
        for tid in sorted(assignments["topic_id"].unique()):
            label = label_map.get(tid, f"Topic {tid}")
            _, _, summary = await summarise_topic(client, assignments, corpus, tid, label)
            results.append({"topic_id": tid, "label": label, "summary": summary})

    out = pd.DataFrame(results)
    out.to_csv(RESULTS_DIR / f"topic_summaries_{group}.csv", index=False)
    print(f"\nSaved topic_summaries_{group}.csv")

if __name__ == "__main__":
    group = sys.argv[1] if len(sys.argv) > 1 else "vpn"
    asyncio.run(main(group))
