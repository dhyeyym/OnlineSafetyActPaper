# Online Safety Regulation Increases Attention to VPNs: Artifact

Artifact for: *Online Safety Regulation Increases Attention to VPNs: Privacy Implications of the UK Online Safety Act*

Proceedings on Privacy Enhancing Technologies 2027, 1–22.

## Repository Structure

```
├── ARTIFACT-APPENDIX.md
├── LICENSE
├── requirements.txt
│
├── prompts/                            Exact LLM prompts (Appendix B)
│   ├── vpn_relevance.txt                   VPN relevance classifier (B.1)
│   ├── politics_relevance.txt              Politics relevance classifier (B.2)
│   ├── sentiment.txt                       Sentiment classifier (B.3)
│   └── topic_summary.txt                   Topic summarisation (B.4)
│
├── classification_outputs/             LLM classification labels (text/authors removed)
│   ├── classified_vpn_submissions.csv
│   ├── classified_vpn_comments.csv
│   ├── classified_vpn_osa_submissions.csv
│   ├── classified_vpn_osa_comments.csv
│   ├── classified_politics_osa_submissions.csv
│   ├── classified_politics_osa_comments.csv
│   ├── classified_politics_vpn_submissions.csv
│   └── classified_politics_vpn_comments.csv
│
├── rq1/                                RQ1: Causal Impact
│   ├── scripts/
│   │   ├── table_3.R                       Content + users CausalImpact (Table 3)
│   │   ├── table_4.R                       Google Trends CausalImpact (Table 4)
│   │   ├── table_12.R                      User count effects (Table 12)
│   │   ├── table_13.R                      Filter-level breakdown (Table 13)
│   │   ├── table_16.R                      Post-window robustness (Table 16)
│   │   ├── table_17.R                      Threshold sensitivity (Table 17)
│   │   ├── build_content_timeseries.py     Generate content series from raw data
│   │   ├── build_user_timeseries.py        Generate user series from raw data
│   │   └── build_threshold_sweep.py        Generate threshold sweep from raw data
│   └── data/
│       ├── vpn_classified_timeseries.csv
│       ├── politics_classified_timeseries.csv
│       ├── vpn_uk_classified_timeseries.csv
│       ├── politics_uk_classified_timeseries.csv
│       ├── combined_classified_timeseries.csv
│       ├── combined_uk_classified_timeseries.csv
│       ├── vpn_user_timeseries.csv
│       ├── vpn_uk_user_timeseries.csv
│       ├── vpn_uk_user_timeseries_classified.csv
│       ├── politics_user_timeseries.csv
│       ├── politics_uk_user_timeseries.csv
│       ├── politics_uk_user_timeseries_classified.csv
│       ├── combined_uk_user_timeseries.csv
│       ├── combined_uk_user_timeseries_classified.csv
│       ├── google_trends_uk.csv
│       ├── google_trends_us.csv
│       ├── table12_user_weekly_series.csv
│       ├── table13_weekly_series.csv
│       ├── table17_weekly_series.csv
│       ├── sweep_summary.csv
│       └── sweep_bsts_results.csv
│
├── rq2/                                RQ2: Discourse Framing
│   ├── scripts/
│   │   ├── config.py
│   │   ├── 01_build_corpus.py
│   │   ├── 02_lda_topics.py
│   │   ├── 03_sentiment_cardiff.py
│   │   ├── 04_sentiment_gemini.py
│   │   ├── 05_topic_sentiment.py
│   │   ├── 06_summarise_topics.py
│   │   └── 07_validation.py
│   └── data/
│       ├── rq2_corpus.csv
│       ├── rq2_corpus_all_authors.csv
│       ├── lda_vpn_topics.csv
│       ├── lda_politics_topics.csv
│       ├── lda_vpn_uk_assignments.csv
│       ├── lda_politics_uk_assignments.csv
│       ├── lda_vpn_prevalence.csv
│       ├── lda_politics_prevalence.csv
│       ├── lda_coherence_sweep.csv
│       ├── rq2_sentiment_cardiff.csv
│       ├── rq2_sentiment_gemini.csv
│       ├── topic_sentiment_gemini_vpn.csv
│       └── topic_sentiment_gemini_politics.csv
│
└── rq3/                                RQ3: VPN Privacy Risk
    ├── README.md
    ├── scripts/
    │   └── risk_classifier.py
    └── data/
        └── vpn_privacy_risk_google_trends.csv
```

## Quick Verification

**RQ1** — open in RStudio, set working directory to the artifact root:
```r
setwd("/path/to/artifact")
source("rq1/scripts/table_3.R")
source("rq1/scripts/table_4.R")
```

**RQ2:**
```bash
cd rq2/scripts && python 07_validation.py recount
```

**RQ3:**
```bash
python rq3/scripts/risk_classifier.py
```

## Regenerating Intermediate Data from Raw Sources

The time series CSVs in `rq1/data/` are provided as frozen intermediate outputs. For researchers with access to the **complete** raw data obtainable via [Arctic Shift](https://arctic-shift.photon-reddit.com/), three build scripts can regenerate them from scratch.

All three scripts require:
- The **complete** `index_document.csv`. It should contain document-level metadata (subreddit, type, keyword match, classifier labels) with author identifiers and timestamps.
- Raw geographic subreddit CSVs (`--geo-dir`)
- Raw study subreddit CSVs (`--original-dir`)

**1. Content time series** — generates `table13_weekly_series.csv` and all `*_classified_timeseries.csv` files:
```bash
python rq1/scripts/build_content_timeseries.py \
  --index /path/to/index_document_full.csv \
  --geo-dir /path/to/geo/ \
  --original-dir /path/to/original/
```

**2. User time series** — generates all `*_user_timeseries*.csv` files:
```bash
python rq1/scripts/build_user_timeseries.py \
  --index /path/to/index_document_full.csv \
  --geo-dir /path/to/geo/ \
  --original-dir /path/to/original/
```

**3. Threshold sweep** — generates `table17_weekly_series.csv` at UK-residency thresholds k=1..5:
```bash
python rq1/scripts/build_threshold_sweep.py \
  --index /path/to/index_document_full.csv \
  --geo-dir /path/to/geo/ \
  --original-dir /path/to/original/
```

These scripts are provided for transparency and full reproducibility.

## Privacy

This artifact does **not** contain Reddit text, usernames, author identifiers, timestamps, or any UK-resident author list. Only document identifiers, derived labels, and subreddit names are released.