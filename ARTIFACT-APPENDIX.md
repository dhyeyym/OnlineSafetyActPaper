# Artifact Appendix

Paper title: **Online Safety Regulation Increases Attention to VPNs: Privacy Implications of the UK Online Safety Act**

Requested Badge(s):
  - [x] **Available**
  - [x] **Functional**
  - [ ] **Reproduced**

## Description

This artifact accompanies the paper *Online Safety Regulation Increases Attention to VPNs: Privacy Implications of the UK Online Safety Act* by Dhyey Mehta, Eldar Jalilzade, Maksim Kalameyets, Rebecca Owens, Marc Juarez, Stergios Aidinlis, Lei Shi, and Tuğrulcan Elmas, published in Proceedings on Privacy Enhancing Technologies 2027(X).

The artifact contains:

1. **LLM classification outputs** for VPN and UK Politics subreddits — relevance labels for all keyword-matched documents, with text and author identifiers removed.
2. **RQ1 reproduction scripts and data**: R scripts using the `CausalImpact` package to reproduce the Bayesian Structural Time Series analyses reported in Tables 3, 4, 12, 13, 16, and 17, plus Python build scripts for regenerating the intermediate time series from raw data.
3. **RQ2 analysis code and data**: the complete Python pipeline for discourse framing and sentiment analysis, including the UK-resident corpus (identifiers only), LDA topic assignments, sentiment labels from two models (RoBERTa and Gemini), coherence sweep data, topic prevalence, and topic-level sentiment cross-tabulations.
4. **RQ3 dataset and code**: 69 VPN service privacy-policy records with six extracted privacy markers, monthly UK Google Trends attention, and the deterministic risk classifier script.
5. **LLM prompts**: exact prompts used for relevance classification, sentiment classification, and topic summarisation (Appendix B of the paper).

### Security/Privacy Issues and Ethical Concerns

This artifact poses no security or privacy risks to the reviewer's machine.

All data consists of publicly accessible Reddit posts and comments. The artifact does **not** distribute Reddit text, usernames, author identifiers, timestamps, or a list of likely UK-resident authors. Only document identifiers, derived labels, and subreddit names are included. All user opinions reported in the paper are paraphrased to prevent search-engine re-identification. No IRB review was sought, consistent with established practice in computational social science research using public platform data (see paper Section "Ethical Considerations").

## Basic Requirements

### Hardware Requirements

Can run on a laptop (no special hardware requirements).

GPU recommended but not required for `03_sentiment_cardiff.py` (RoBERTa inference). Without GPU, sentiment inference takes approximately 2–4 hours on CPU. All other scripts run in under 45 minutes.

### Software Requirements

- **OS**: Tested on Windows 11 and Ubuntu 22.04.
- **R**: 4.3+ with the `CausalImpact` and `zoo` packages (for RQ1). We recommend running R scripts in **RStudio** with the working directory set to the artifact root.
- **Python**: 3.11+ (for RQ2, RQ3, and data preparation).
- **Python packages** (see `requirements.txt`):
  - `pandas >= 2.0`, `numpy >= 1.24`, `gensim >= 4.3`, `spacy >= 3.7` with `en_core_web_sm`, `transformers >= 4.35`, `torch >= 2.1`, `scipy >= 1.11`, `matplotlib >= 3.8`, `tqdm`, `httpx`
- **API keys**: Gemini API key required only for `04_sentiment_gemini.py` and `06_summarise_topics.py` (set via `GEMINI_KEY` environment variable). Not required for reviewing frozen outputs.

### Estimated Time and Storage Consumption

| Component | Time | Storage |
|---|---|---|
| RQ1 Table 3 (`table_3.R`) | ~10 min | <1 MB |
| RQ1 Table 4 (`table_4.R`) | ~5 min | <1 MB |
| RQ1 Table 12 (`table_12.R`) | ~45 min | <1 MB |
| RQ1 Table 13 (`table_13.R`) | ~45 min | <1 MB |
| RQ1 Table 16 (`table_16.R`) | ~10 min | <1 MB |
| RQ1 Table 17 (`table_17.R`) | ~20 min | <1 MB |
| RQ2 verification (`05_topic_sentiment.py`, `07_validation.py`) | <1 min | <1 MB |
| RQ3 risk classification (`risk_classifier.py`) | <1 min | — |
| Total artifact on disk | — | ~350 MB (excl. Zenodo-hosted files) |

**Note**: RQ2 steps 01–04 require access to the raw classified Reddit CSV files containing author identifiers and document text, which are not distributed for privacy reasons. The frozen outputs of each step are provided.

## Environment

### Accessibility

The artifact is publicly available at: **[FILL WITH GITHUB/ZENODO URL]**

The per-document index (`index_document.csv`, 65.8M rows, ~2.3 GB) is hosted separately on Zenodo: **[FILL WITH ZENODO DOI/URL]**

### Set Up the Environment

```r
# R (for RQ1) — in RStudio
install.packages(c("CausalImpact", "zoo"))
```

```bash
# Python (for RQ2 and RQ3)
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Testing the Environment

```bash
cd rq2/scripts
python 07_validation.py recount
```

Expected output:
```
UK corpus: 45,438
group
politics    42970
vpn          2468
  LDA vpn: 2,430 assigned of 2,468 (dropped 38)
  LDA politics: 41,881 assigned of 42,970 (dropped 1,089)
  Total assigned: 44,311, dropped: 1,127

Sentiment: 45,541 docs, agree 63.7%, disagree 16,546 (36.3%)
```

## Artifact Evaluation

### Main Results and Claims

The paper's central finding is that the UK Online Safety Act's July 2025 age-verification deadline produced a large, concentrated increase in VPN-related attention — both in Reddit discourse and Google search interest — driven by privacy and surveillance concerns rather than access-seeking, with no corresponding shift toward higher-risk VPN providers.

The following experiments verify the key quantitative claims supporting this finding.

#### Main Result 1: Age Verification Drove VPN and Politics Discourse (Table 3 Classified rows, Section 4)

VPN classified content increased by +328% and UK-resident VPN classified content by +1265% at the July 2025 deadline. Politics classified content increased by +1474%. These effects were absent at Royal Assent and Enforcement. Reproduced by [Experiment 1](#experiment-1-reproduce-table-3), where the classified content rows match the paper within ±5%.

#### Main Result 2: Google Trends Confirms the Displacement (Table 4, Section 4)

UK VPN Google Trends search interest increased by +147% (no covariate), +135% (US covariate), and +144% (lag-52 covariate) at the age-verification deadline. All three specifications are reproduced within ±5% by [Experiment 2](#experiment-2-reproduce-table-4).

#### Main Result 3: Effect Holds Across Filter Levels (Table 13 Classified rows, Section 4)

The age-verification effect is present across all nine filter levels, with classified content showing the largest effects. Classified rows at July 2025 match within ±5% by [Experiment 4](#experiment-4-reproduce-table-13).

#### Main Result 4: Users Frame VPN Attention Around Privacy, Not Access (Tables 5–6, Section 5)

LDA topic modelling identifies 12 VPN topics and 17 Politics topics. Surveillance- and rights-oriented framings dominate (53.3% of VPN discourse). Sentiment is predominantly negative with near-zero pro-OSA sentiment (4–7% positive). Both classifiers agree on 63.7% of documents, with human adjudication favouring Gemini (63%) over RoBERTa (31%). Reproduced exactly by [Experiment 7](#experiment-7-reproduce-rq2-discourse-framing).

#### Main Result 5: No Shift Toward Higher-Risk Providers (Table 8, Section 6)

69 VPN services are classified into Low (26), Medium (35), and High (8) disclosed privacy-risk categories. All marker counts and risk category totals match exactly by [Experiment 8](#experiment-8-reproduce-rq3-risk-classification).

### Experiments

All RQ1 R scripts should be run in **RStudio** with the working directory set to the artifact root:
```r
setwd("/path/to/artifact")
```

#### Experiment 1: Reproduce Table 3

- **Claim**: Classified content and user counts increased sharply at the Age Verification deadline.

```r
source("rq1/scripts/table_3.R")
```

Output: `rq1/data/table3_reproduced.csv`. The classified content rows at July 2025 reproduce within ±5% of the paper. Small-baseline rows (Raw, Unmatched) and pre-deadline milestones (October 2023, March 2025) may vary by up to ±10 percentage points due to BSTS posterior sampling on low-count series.

#### Experiment 2: Reproduce Table 4

- **Claim**: UK VPN Google Trends search interest increased by +147% at the age-verification deadline.

```r
source("rq1/scripts/table_4.R")
```

Output: `rq1/data/table4_reproduced.csv`. All three July 2025 specifications (no covariate, US covariate, lag-52) reproduce within ±5%.

#### Experiment 3: Reproduce Table 12

- **Claim**: User count effects are consistent across unique, new, and cumulative user metrics.

```r
source("rq1/scripts/table_12.R")
```

Output: `rq1/data/table12_reproduced.csv`. Classified user-count effects at July 2025 reproduce within ±5%.

#### Experiment 4: Reproduce Table 13

- **Claim**: The age-verification effect holds across all nine filter levels.

```r
source("rq1/scripts/table_13.R")
```

Output: `rq1/data/table13_reproduced.csv`. Runs 162 CausalImpact models (2 groups × 9 filters × 3 milestones × 3 metrics). Classified rows at July 2025 reproduce within ±5%.

#### Experiment 5: Reproduce Table 16

- **Claim**: Effects are robust to post-window length (4, 8, and 12 weeks).

```r
source("rq1/scripts/table_16.R")
```

Output: `rq1/data/table16_reproduced.csv`.

#### Experiment 6: Reproduce Table 17

- **Claim**: Effects strengthen with UK-residency confidence (threshold k=1..5).

```r
source("rq1/scripts/table_17.R")
```

Output: `rq1/data/table17_reproduced.csv`. The k≥1 threshold reproduces within ±5%.

#### Experiment 7: Reproduce RQ2 Discourse Framing (Tables 5–6, Figures 4–5)

- **Claim**: LDA identifies K=12 VPN topics and K=17 Politics topics; sentiment is predominantly negative with near-zero pro-OSA voices.
- **Time**: <1 minute

```bash
cd rq2/scripts
python 05_topic_sentiment.py
python 07_validation.py recount
```

Verify that:
- VPN has 12 topics, Politics has 17 (Table 5)
- Prevalence percentages match Table 5
- Sentiment distributions match Table 6
- Coherence peaks at K=12 for VPN (C_V = 0.533) and K=17 for Politics (C_V = 0.536)
- Sentiment classifiers agree on 63.7% of documents

All RQ2 numbers reproduce exactly from the frozen data.

#### Experiment 8: Reproduce RQ3 Risk Classification (Table 8)

- **Claim**: 69 VPN services classified into Low (26), Medium (35), and High (8) risk categories.
- **Time**: <1 minute

```bash
python rq3/scripts/risk_classifier.py
```

Expected output:
```
Providers: 69

--- Table 8 ---
  LOW: 26
  MEDIUM: 35
  HIGH: 8

--- Marker counts (Section 6.1) ---
  traffic_logging: 4
  connection_metadata: 29
  tracking_identifiers: 24
  third_party_sharing: 30
  long_term_retention: 11
  policy_vagueness: 11
```

All counts match the paper exactly.

#### Experiment 9: Verify Classification Outputs

- **Time**: <1 minute

```bash
python -c "
import pandas as pd, os
for f in sorted(os.listdir('classification_outputs')):
    df = pd.read_csv(f'classification_outputs/{f}')
    rel_col = 'relevant_strict' if 'relevant_strict' in df.columns else 'relevant'
    pos = (df[rel_col].astype(int) == 1).sum()
    print(f'{f}: {len(df):>10,} docs, {pos:>8,} relevant')
"
```

Verifies that classification output files contain only document identifiers, subreddit names, and relevance labels — no text, usernames, or timestamps.

#### Experiment 10: Verify Coherence Sweep (Figure 4)

- **Time**: <1 minute

```bash
python -c "
import pandas as pd
df = pd.read_csv('rq2/data/lda_coherence_sweep.csv')
print(df.to_string(index=False))
"
```

Coherence peaks at K=12 for VPN (C_V = 0.533) and K=17 for Politics (C_V = 0.536), matching Figure 4.

## Limitations

1. **CausalImpact is stochastic.** Bayesian Structural Time Series models involve posterior sampling, so reproduced effect sizes vary across runs. Headline classified effects at the July 2025 Age Verification deadline — the paper's central claim — reproduce within ±5% of reported values. Small-baseline series (Raw, Unmatched) and pre-deadline milestones are more sensitive to posterior sampling and may vary by up to ±10 percentage points. All directional findings and statistical significance are preserved.

2. **RQ2 corpus construction requires raw Reddit data.** Steps 01–04 of the RQ2 pipeline require the classified Reddit CSV files containing author identifiers and document text, which are not distributed for privacy reasons. The frozen outputs of each step are provided.

3. **LLM outputs are non-deterministic.** Re-running Gemini classification or sentiment analysis will produce different outputs because hosted models change between API versions. The frozen outputs used for the paper's reported results are provided.

4. **The "Reproduced" badge is not requested** because RQ2 corpus construction requires private data. We apply for "Available" and "Functional" badges, which are supported by the provided frozen outputs, verification scripts, and reproduction code.

## Notes on Reusability

- The **RQ1 R scripts** demonstrate how to apply CausalImpact to weekly content and search-interest time series for causal inference around policy milestones, including window robustness and threshold sensitivity analyses.
- The **RQ1 Python build scripts** (`build_content_timeseries.py`, `build_user_timeseries.py`, `build_threshold_sweep.py`) show how to construct weekly aggregated time series from a per-document index, enabling researchers with access to the raw Reddit data to regenerate all intermediate data from scratch.
- The **RQ2 pipeline** (scripts 01–07) is a reusable framework for Reddit discourse analysis combining LDA topic modelling with multi-model sentiment classification.
- The **RQ3 risk classification** is a deterministic, rule-based framework extensible to additional VPN providers.
- The **LLM prompts** provide templates for relevance classification and sentiment analysis of policy-related social media discourse.
- The **classification outputs** and **per-document index** enable researchers to construct alternative time series or apply different causal inference methods without needing access to Reddit text.