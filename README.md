# Online Safety Regulation Increases Attention to VPNs: Artifact

Artifact for: *Online Safety Regulation Increases Attention to VPNs: Privacy Implications of the UK Online Safety Act*

Proceedings on Privacy Enhancing Technologies 2027(X), 1–22.

## Repository Structure

```
├── ARTIFACT-APPENDIX.md        
├── LICENSE                     
├── requirements.txt            
├── prompts/                    Exact LLM prompts used in the paper
│   ├── vpn_relevance.txt           VPN relevance classifier (Appendix B.1)
│   ├── politics_relevance.txt      Politics relevance classifier (Appendix B.2)
│   ├── sentiment.txt               Sentiment classifier (Appendix B.3)
│   └── topic_summary.txt           Topic summarisation (Appendix B.4)
│
├── classification_outputs/     LLM classification labels (all text/authors removed)
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
│   ├── scripts/
│   │   ├── table_3.R               Content + users CausalImpact (Table 3)
│   │   ├── table_4.R               Google Trends CausalImpact (Table 4)
│   │   ├── table_12.R              User count effects (Table 12)
│   │   ├── table_13.R              Full filter-level breakdown (Table 13)
│   │   ├── table_14_15.R           Google Trends placebo + date sensitivity
│   │   ├── table_16.R              Post-window robustness (Table 16)
│   │   └── table_17.R              UK-residency threshold sensitivity (Table 17)
│   └── data/
│       ├── index_document.csv
│       ├── vpn_time_series_classified_hp.csv
│       ├── politics_time_series_classified_hp.csv
│       ├── vpn_uk_content_timeseries_strict.csv
│       ├── politics_uk_content_timeseries_strict.csv
│       ├── vpn_user_timeseries.csv
│       ├── vpn_uk_user_timeseries.csv
│       ├── vpn_user_timeseries_uk_filtered.csv
│       ├── politics_user_timeseries.csv
│       ├── politics_uk_user_timeseries.csv
│       ├── politics_user_timeseries_uk_filtered.csv
│       ├── combined_uk_user_timeseries.csv
│       ├── combined_user_timeseries_uk_filtered.csv
│       ├── google_trends_uk.csv
│       ├── google_trends_us.csv
│       ├── table13_weekly_series.csv
│       ├── table17_weekly_series.csv
│       ├── combined_time_series_classified.csv
│       ├── combined_uk_content_timeseries.csv
│       ├── sweep_summary.csv
│       └── sweep_bsts_results.csv
│
├── rq2/                        RQ2: Discourse Framing
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
│       ├── rq2_corpus_full.csv
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
└── rq3/                        RQ3: VPN Privacy Risk
    ├── README.md
    ├── scripts/
    │   └── risk_classifier.py
    └── data/
        └── vpn_privacy_risk_google_trends.csv
```

## Quick Verification

```bash
# RQ1 (requires R with CausalImpact package)
Rscript rq1/scripts/table_3.R
Rscript rq1/scripts/table_4.R

# RQ2 (requires Python 3.11+)
cd rq2/scripts && python 07_validation.py recount

# RQ3 (requires Python 3.11+)
python rq3/scripts/risk_classifier.py
```

## Privacy

This artifact does **not** contain Reddit text, usernames, author identifiers, timestamps, or any UK-resident author list. Only document identifiers, derived labels, and subreddit names are released.