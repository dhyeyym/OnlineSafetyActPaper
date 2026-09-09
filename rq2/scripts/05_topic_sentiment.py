"""
05_topic_sentiment.py — Cross-tabulate topics × sentiment, generate Figure 5.

Outputs per group:
  topic_sentiment_cardiff_{group}.csv
  topic_sentiment_gemini_{group}.csv
  topic_sentiment_gemini_{group}.png  (Figure 5)
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config import RESULTS_DIR, LDA_K, TOPIC_LABELS

plt.rcParams.update({"font.family": "serif", "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6})
NEG, NEU, POS = "#c0392b", "#aaaaaa", "#27ae60"
MAX_TOPICS = 17
FIG_HEIGHT = MAX_TOPICS * 0.22

def norm(df):
    for c in ["doc_id"]:
        if c in df.columns: df[c] = df[c].astype(str).str.strip()
    return df

def topic_sentiment(assignments, sentiment, label_col, group, k):
    merged = assignments.merge(sentiment[["doc_id", label_col]],
                               on="doc_id", how="inner")
    label_map = TOPIC_LABELS[group]
    rows = []
    for tid in range(k):
        tdf = merged[merged["topic_id"] == tid]
        n = len(tdf)
        if n < 1: continue
        rows.append({"topic_id": tid, "label": label_map.get(tid, f"Topic {tid}"), "n_docs": n,
                      "pct_negative": round((tdf[label_col] == "negative").mean() * 100, 1),
                      "pct_neutral":  round((tdf[label_col] == "neutral").mean() * 100, 1),
                      "pct_positive": round((tdf[label_col] == "positive").mean() * 100, 1)})
    return pd.DataFrame(rows)

def plot_sentiment(ts_df, group, out_path, model_name):
    df = ts_df.sort_values("n_docs", ascending=True).reset_index(drop=True)
    y = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(4.5, FIG_HEIGHT))
    ax.barh(y, df["pct_negative"],                                     color=NEG, label="Negative", height=0.55)
    ax.barh(y, df["pct_neutral"],  left=df["pct_negative"],            color=NEU, label="Neutral",  height=0.55)
    ax.barh(y, df["pct_positive"], left=df["pct_negative"]+df["pct_neutral"], color=POS, label="Positive", height=0.55)
    ax.set_yticks(y); ax.set_yticklabels(df["label"], fontsize=7)
    ax.set_xlabel("Share of documents (%)", fontsize=7); ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))
    ax.tick_params(labelsize=7)
    title = "VPN" if group == "vpn" else "UK Politics"
    ax.set_title(f"{title} subreddits — sentiment by topic ({model_name})", fontsize=8, pad=6)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=7, frameon=False, ncol=3)
    plt.tight_layout(); plt.savefig(out_path, dpi=300, bbox_inches="tight"); plt.close()

if __name__ == "__main__":
    cardiff = norm(pd.read_csv(RESULTS_DIR / "rq2_sentiment_cardiff.csv")) if (RESULTS_DIR / "rq2_sentiment_cardiff.csv").exists() else None
    gemini  = norm(pd.read_csv(RESULTS_DIR / "rq2_sentiment_gemini.csv"))  if (RESULTS_DIR / "rq2_sentiment_gemini.csv").exists() else None

    for group in ["vpn", "politics"]:
        k = LDA_K[group]
        apath = RESULTS_DIR / f"lda_{group}_uk_assignments.csv"
        if not apath.exists(): print(f"SKIP {group}"); continue
        assign = norm(pd.read_csv(apath))

        if cardiff is not None:
            ts = topic_sentiment(assign, cardiff, "cardiff_label", group, k)
            ts.to_csv(RESULTS_DIR / f"topic_sentiment_cardiff_{group}.csv", index=False)
            print(f"\n{group.upper()} Cardiff:")
            print(ts[["topic_id", "label", "n_docs", "pct_negative", "pct_neutral", "pct_positive"]].to_string(index=False))

        if gemini is not None:
            ts = topic_sentiment(assign, gemini, "gemini_label", group, k)
            ts.to_csv(RESULTS_DIR / f"topic_sentiment_gemini_{group}.csv", index=False)
            plot_sentiment(ts, group, RESULTS_DIR / f"topic_sentiment_gemini_{group}.png", "Gemini")
            print(f"\n{group.upper()} Gemini:")
            print(ts[["topic_id", "label", "n_docs", "pct_negative", "pct_neutral", "pct_positive"]].to_string(index=False))
            print(f"  Saved plot: topic_sentiment_gemini_{group}.png")
