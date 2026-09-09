# Online Safety Regulation Increases Attention to VPNs: Artifact

Artifact for: *Online Safety Regulation Increases Attention to VPNs: Privacy Implications of the UK Online Safety Act*

Proceedings on Privacy Enhancing Technologies 2027(X), 1–22.

## Repository Structure

```
├── ARTIFACT-APPENDIX.md
├── LICENSE
├── requirements.txt
│
├── prompts/                    Exact LLM prompts (Appendix B)
│   ├── vpn_relevance.txt
│   ├── politics_relevance.txt
│   ├── sentiment.txt
│   └── topic_summary.txt
│
├── classification_outputs/     LLM classification labels (text/authors removed)
│   ├── classified_vpn_submissions.csv
│   ├── classified_vpn_comments.csv
│   ├── classified_vpn_osa_submissions.csv
│   ├── classified_vpn_osa_comments.csv
│   ├── classified_politics_osa_submissions.csv
│   ├── classified_politics_osa_comments.csv
│   ├── classified_politics_vpn_submissions.csv
│   └── classified_politics_vpn_comments.csv
│
├── rq1/                        RQ1: Causal Impact
│   ├── scripts/                R scripts (run in RStudio)
│   │   ├── table_3.R               Content + users CausalImpact (Table 3)
│   │   ├── table_4.R               Google Trends CausalImpact (Table 4)
│   │   ├── table_12.R              User count effects (Table 12)
│   │   ├── table_13.R              Full filter-level breakdown (Table 13)
│   │   ├── table_16.R              Post-window robustness (Table 16)
│   │   └── table_17.R              UK-residency threshold sensitivity (Table 17)
│   └── data/
│       ├── index_document.csv
│       ├── vpn_time_series_classified_hp.csv
│       ├── politics_time_series_classified_hp.csv
│       ├── vpn_uk_content_timeseries_strict.csv
│       ├── politics_uk_content_timeseries_strict.csv
│       ├── google_trends_uk.csv
│       ├── google_trends_us.csv
│       ├── table13_weekly_series.csv
│       ├── table17_weekly_series.csv
│       ├── table12_user_weekly_series.csv
│       └── ...
│
├── rq2/                        RQ2: Discourse Framing
│   ├── scripts/                Python scripts
│   │   ├── config.py
│   │   ├── 01_build_corpus.py
│   │   ├── 02_lda_topics.py
│   │   ├── 03_sentiment_cardiff.py
│   │   ├── 04_sentiment_gemini.py
│   │   ├── 05_topic_sentiment.py
│   │   ├── 06_summarise_topics.py
│   │   └── 07_validation.py
│   └── data/
│       └── ...
│
└── rq3/                        RQ3: VPN Privacy Risk
    ├── README.md
    ├── scripts/
    │   └── risk_classifier.py
    └── data/
        └── vpn_privacy_risk_google_trends.csv
```

## Quick Verification

**RQ1** (R — open scripts in RStudio, set working directory to the artifact root, and run):
```r
setwd("/path/to/artifact")
source("rq1/scripts/table_3.R")
source("rq1/scripts/table_4.R")
```

**RQ2** (Python):
```bash
cd rq2/scripts && python 07_validation.py recount
```

**RQ3** (Python):
```bash
python rq3/scripts/risk_classifier.py
```

## Privacy

This artifact does **not** contain Reddit text, usernames, author identifiers, timestamps, or any UK-resident author list. Only document identifiers, derived labels, and subreddit names are released.