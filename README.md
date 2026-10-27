# Online Safety Regulation Increases Attention to VPNs

Artifact for *Online Safety Regulation Increases Attention to VPNs: Privacy Implications of the UK Online Safety Act*, Proceedings on Privacy Enhancing Technologies 2027, 1–22.

## Structure

`rq1/` has the CausalImpact scripts for the RQ1 tables and the weekly series they read. `rq2/` has the topic modelling and sentiment pipeline for RQ2. `rq3/` has the VPN privacy policy coding for RQ3. `prompts/` holds the exact LLM prompts from Appendix B, and `classification_outputs/` holds the classifier labels with text and authors removed.

```
.
├── classification_outputs
│   ├── classified_politics_osa_comments.csv
│   ├── classified_politics_osa_submissions.csv
│   ├── classified_politics_vpn_comments.csv
│   ├── classified_politics_vpn_submissions.csv
│   ├── classified_vpn_comments.csv
│   ├── classified_vpn_osa_comments.csv
│   ├── classified_vpn_osa_submissions.csv
│   └── classified_vpn_submissions.csv
├── prompts
│   ├── politics_relevance.txt
│   ├── sentiment.txt
│   ├── topic_summary.txt
│   └── vpn_relevance.txt
├── rq1
│   ├── data
│   │   ├── combined_classified_timeseries.csv
│   │   ├── combined_uk_classified_timeseries.csv
│   │   ├── combined_uk_user_timeseries.csv
│   │   ├── combined_uk_user_timeseries_classified.csv
│   │   ├── google_trends_uk.csv
│   │   ├── google_trends_us.csv
│   │   ├── politics_classified_timeseries.csv
│   │   ├── politics_uk_classified_timeseries.csv
│   │   ├── politics_uk_user_timeseries.csv
│   │   ├── politics_uk_user_timeseries_classified.csv
│   │   ├── politics_user_timeseries.csv
│   │   ├── sweep_bsts_results.csv
│   │   ├── sweep_summary.csv
│   │   ├── table12_user_weekly_series.csv
│   │   ├── table13_weekly_series.csv
│   │   ├── table17_weekly_series.csv
│   │   ├── vpn_classified_timeseries.csv
│   │   ├── vpn_uk_classified_timeseries.csv
│   │   ├── vpn_uk_user_timeseries.csv
│   │   ├── vpn_uk_user_timeseries_classified.csv
│   │   └── vpn_user_timeseries.csv
│   └── scripts
│       ├── build_content_timeseries.py
│       ├── build_threshold_sweep.py
│       ├── build_user_timeseries.py
│       ├── table_12.R
│       ├── table_13.R
│       ├── table_16.R
│       ├── table_17.R
│       ├── table_3.R
│       └── table_4.R
├── rq2
│   ├── data
│   │   ├── lda_coherence_sweep.csv
│   │   ├── lda_politics_prevalence.csv
│   │   ├── lda_politics_topics.csv
│   │   ├── lda_politics_uk_assignments.csv
│   │   ├── lda_vpn_prevalence.csv
│   │   ├── lda_vpn_topics.csv
│   │   ├── lda_vpn_uk_assignments.csv
│   │   ├── rq2_corpus.csv
│   │   ├── rq2_corpus_all_authors.csv
│   │   ├── rq2_sentiment_cardiff.csv
│   │   ├── rq2_sentiment_gemini.csv
│   │   ├── topic_sentiment_gemini_politics.csv
│   │   └── topic_sentiment_gemini_vpn.csv
│   └── scripts
│       ├── 01_build_corpus.py
│       ├── 02_lda_topics.py
│       ├── 03_sentiment_cardiff.py
│       ├── 04_sentiment_gemini.py
│       ├── 05_topic_sentiment.py
│       ├── 06_summarise_topics.py
│       ├── 07_validation.py
│       └── config.py
├── rq3
│   ├── data
│   │   └── vpn_privacy_risk_google_trends.csv
│   └── scripts
│       └── risk_classifier.py
├── ARTIFACT-APPENDIX.md
├── Dockerfile
├── LICENSE
├── README.md
└── requirements.txt
```

## Running with Docker

Build the image once:

```bash
docker build -t osa-artifact .
```

Then run everything from the artifact root.

Linux / macOS:

```bash
docker run --rm -v "$PWD:/artifact" -w /artifact osa-artifact bash -c '
  for t in 3 4 12 13 16 17; do
    echo "Table $t"
    Rscript rq1/scripts/table_$t.R
  done
  cd rq2/scripts && python 07_validation.py recount
  cd ../.. && python rq3/scripts/risk_classifier.py
'
```

Windows (CMD):

```cmd
docker run --rm -v "%cd%:/artifact" -w /artifact osa-artifact bash -c "for t in 3 4 12 13 16 17; do echo Table $t; Rscript rq1/scripts/table_$t.R; done; cd rq2/scripts && python 07_validation.py recount; cd ../.. && python rq3/scripts/risk_classifier.py"
```

## Running manually

RQ1 scripts expect the working directory to be the artifact root. In R or RStudio:

```r
setwd("/path/to/artifact")
source("rq1/scripts/table_3.R")
source("rq1/scripts/table_4.R")
```

RQ2:

```bash
cd rq2/scripts && python 07_validation.py recount
```

RQ3:

```bash
python rq3/scripts/risk_classifier.py
```

## Rebuilding the RQ1 series from raw data

The CSVs in `rq1/data/` are frozen intermediate outputs. If you have the full raw data from [Arctic Shift](https://arctic-shift.photon-reddit.com/), the three `build_*.py` scripts regenerate them. Each one needs:

- the full `index_document.csv`, with subreddit, type, keyword match, classifier labels, author and timestamp for every document
- the raw geographic subreddit CSVs (`--geo-dir`)
- the raw study subreddit CSVs (`--original-dir`)

Content series, which writes `table13_weekly_series.csv` and the `*_classified_timeseries.csv` files:

```bash
python rq1/scripts/build_content_timeseries.py \
  --index /path/to/index_document_full.csv \
  --geo-dir /path/to/geo/ \
  --original-dir /path/to/original/
```

User series, which writes `table12_user_weekly_series.csv` and the `*_user_timeseries*.csv` files:

```bash
python rq1/scripts/build_user_timeseries.py \
  --index /path/to/index_document_full.csv \
  --geo-dir /path/to/geo/ \
  --original-dir /path/to/original/
```

Threshold sweep, which writes `table17_weekly_series.csv` for UK-residency thresholds k = 1 to 5:

```bash
python rq1/scripts/build_threshold_sweep.py \
  --index /path/to/index_document_full.csv \
  --geo-dir /path/to/geo/ \
  --original-dir /path/to/original/
```

## Privacy

The artifact contains no Reddit text, usernames, author identifiers, timestamps or list of UK-resident authors. Only document identifiers, derived labels and subreddit names are released.
