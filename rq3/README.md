# Online Safety Regulation Increases Attention to VPNs: Artifact

Artifact for: *Online Safety Regulation Increases Attention to VPNs: Privacy Implications of the UK Online Safety Act*

Proceedings on Privacy Enhancing Technologies 2027(X), 1–22.

## Repository Structure

```
├── ARTIFACT-APPENDIX.md        Artifact evaluation guide (PoPETs format)
├── LICENSE                     MIT (code) + CC-BY-4.0 (data)
├── requirements.txt            Python dependencies
│
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
│   ├── reproduce_table3.py         CausalImpact on classified content (Table 3)
│   ├── reproduce_table4.py         CausalImpact on Google Trends (Table 4)
│   └── data/
│       ├── vpn_time_series_classified_hp.csv
│       ├── politics_time_series_classified_hp.csv
│       ├── vpn_uk_content_timeseries_strict.csv
│       ├── politics_uk_content_timeseries_strict.csv
│       ├── google_trends_uk.csv
│       ├── google_trends_us.csv
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
│       ├── topic_sentiment_gemini_politics.csv
│       ├── adjudication_TOANNOTATE.csv
│       └── adjudication_key.csv
│
└── rq3/                        RQ3: VPN Privacy Risk
    ├── README.md
    ├── rq3_risk_classifier.py
    └── data/
        └── vpn_privacy_risk_google_trends.csv
```

## Quick Verification

```bash
# RQ1: reproduce Tables 3 and 4
pip install tfcausalimpact
python rq1/reproduce_table3.py
python rq1/reproduce_table4.py

# RQ2: check corpus counts and sentiment adjudication
cd rq2/scripts && python 07_validation.py recount
cd rq2/scripts && python 07_validation.py score_sample

# RQ3: verify risk classification
python rq3/rq3_risk_classifier.py
```

## Privacy

This artifact does **not** contain Reddit text, usernames, author identifiers, timestamps, or any UK-resident author list. Only document identifiers, derived labels, and subreddit names are released. See ARTIFACT-APPENDIX.md for details.