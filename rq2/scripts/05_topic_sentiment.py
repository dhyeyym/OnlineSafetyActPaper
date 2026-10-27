import warnings

warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from config import RESULTS_DIR, LDA_K, TOPIC_LABELS

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
})

NEGATIVE_COLOUR = "#c0392b"
NEUTRAL_COLOUR = "#aaaaaa"
POSITIVE_COLOUR = "#27ae60"

MAX_TOPICS = 17
FIG_HEIGHT = MAX_TOPICS * 0.22

SUMMARY_COLUMNS = ["topic_id", "label", "n_docs", "pct_negative", "pct_neutral", "pct_positive"]


def normalise_ids(df):
    if "doc_id" in df.columns:
        df["doc_id"] = df["doc_id"].astype(str).str.strip()

    return df


def load_if_exists(path):
    if not path.exists():
        return None

    return normalise_ids(pd.read_csv(path))


def percentage(labels, value):
    return round((labels == value).mean() * 100, 1)


def topic_sentiment(assignments, sentiment, label_column, group, k):
    merged = assignments.merge(sentiment[["doc_id", label_column]], on="doc_id", how="inner")
    label_map = TOPIC_LABELS[group]

    rows = []
    for topic_id in range(k):
        topic_docs = merged[merged["topic_id"] == topic_id]
        if len(topic_docs) < 1:
            continue

        labels = topic_docs[label_column]
        rows.append({
            "topic_id": topic_id,
            "label": label_map.get(topic_id, f"Topic {topic_id}"),
            "n_docs": len(topic_docs),
            "pct_negative": percentage(labels, "negative"),
            "pct_neutral": percentage(labels, "neutral"),
            "pct_positive": percentage(labels, "positive"),
        })

    return pd.DataFrame(rows)


def format_percent(x, _):
    return f"{int(x)}%"


def plot_sentiment(summary, group, out_path, model_name):
    df = summary.sort_values("n_docs", ascending=True).reset_index(drop=True)
    y = np.arange(len(df))

    fig, ax = plt.subplots(figsize=(4.5, FIG_HEIGHT))

    neutral_left = df["pct_negative"]
    positive_left = df["pct_negative"] + df["pct_neutral"]

    ax.barh(y, df["pct_negative"], color=NEGATIVE_COLOUR, label="Negative", height=0.55)
    ax.barh(y, df["pct_neutral"], left=neutral_left, color=NEUTRAL_COLOUR, label="Neutral", height=0.55)
    ax.barh(y, df["pct_positive"], left=positive_left, color=POSITIVE_COLOUR, label="Positive", height=0.55)

    ax.set_yticks(y)
    ax.set_yticklabels(df["label"], fontsize=7)
    ax.set_xlabel("Share of documents (%)", fontsize=7)
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_percent))
    ax.tick_params(labelsize=7)

    if group == "vpn":
        title = "VPN"
    else:
        title = "UK Politics"

    ax.set_title(f"{title} subreddits — sentiment by topic ({model_name})", fontsize=8, pad=6)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=7, frameon=False, ncol=3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()


def main():
    cardiff = load_if_exists(RESULTS_DIR / "rq2_sentiment_cardiff.csv")
    gemini = load_if_exists(RESULTS_DIR / "rq2_sentiment_gemini.csv")

    for group in ["vpn", "politics"]:
        k = LDA_K[group]

        assignments_path = RESULTS_DIR / f"lda_{group}_uk_assignments.csv"
        if not assignments_path.exists():
            print(f"SKIP {group}")
            continue

        assignments = normalise_ids(pd.read_csv(assignments_path))

        if cardiff is not None:
            summary = topic_sentiment(assignments, cardiff, "cardiff_label", group, k)
            summary.to_csv(RESULTS_DIR / f"topic_sentiment_cardiff_{group}.csv", index=False)

            print(f"\n{group.upper()} Cardiff:")
            print(summary[SUMMARY_COLUMNS].to_string(index=False))

        if gemini is not None:
            summary = topic_sentiment(assignments, gemini, "gemini_label", group, k)
            summary.to_csv(RESULTS_DIR / f"topic_sentiment_gemini_{group}.csv", index=False)
            plot_sentiment(summary, group, RESULTS_DIR / f"topic_sentiment_gemini_{group}.png", "Gemini")

            print(f"\n{group.upper()} Gemini:")
            print(summary[SUMMARY_COLUMNS].to_string(index=False))
            print(f"  Saved plot: topic_sentiment_gemini_{group}.png")


if __name__ == "__main__":
    main()
