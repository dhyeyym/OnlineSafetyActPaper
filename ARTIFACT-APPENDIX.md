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
2. **RQ1 reproduction scripts and data**: Python scripts to reproduce the Bayesian Structural Time Series analyses reported in Tables 3, 4, 13, 14, 15, 16, and 17, along with the frozen weekly time series, Google Trends data, and the per-document index (with sensitive fields removed).
3. **RQ2 analysis code and data**: the complete pipeline for discourse framing and sentiment analysis, including the UK-resident corpus (identifiers only), LDA topic assignments, sentiment labels from two models (RoBERTa and Gemini), coherence sweep data, topic prevalence, and topic-level sentiment cross-tabulations.
4. **RQ3 dataset and code**: 69 VPN service privacy-policy records with six extracted privacy markers, monthly UK Google Trends attention, and the deterministic risk classifier script.
5. **LLM prompts**: exact prompts used for relevance classification, sentiment classification, and topic summarisation (Appendix B of the paper).

### Security/Privacy Issues and Ethical Concerns

This artifact poses no security or privacy risks to the reviewer's machine.

All data consists of publicly accessible Reddit posts and comments. The artifact does **not** distribute Reddit text, usernames, author identifiers, timestamps, or a list of likely UK-resident authors. Only document identifiers, derived labels, and subreddit names are included. All user opinions reported in the paper are paraphrased to prevent search-engine re-identification. No IRB review was sought, consistent with established practice in computational social science research using public platform data (see paper Section "Ethical Considerations").

## Basic Requirements

### Hardware Requirements

Can run on a laptop (no special hardware requirements).

GPU recommended but not required for `03_sentiment_cardiff.py` (RoBERTa inference). Without GPU, sentiment inference takes approximately 2–4 hours on CPU. All other scripts run in under 30 minutes.

### Software Requirements

- **OS**: Tested on Windows 11 and Ubuntu 22.04. Should work on any OS with Python 3.11+.
- **Python**: 3.11+
- **Python packages** (see `requirements.txt`):
  - `pandas >= 2.0`
  - `numpy >= 1.24`
  - `gensim >= 4.3` (LDA topic modelling)
  - `spacy >= 3.7` with `en_core_web_sm` model
  - `transformers >= 4.35` (RoBERTa sentiment)
  - `torch >= 2.1`
  - `scipy >= 1.11`
  - `matplotlib >= 3.8`
  - `tqdm`
  - `httpx` (async HTTP for Gemini API)
  - `tfcausalimpact` (Bayesian Structural Time Series for RQ1)
- **API keys**: Gemini API key required only for `04_sentiment_gemini.py` and `06_summarise_topics.py` (set via `GEMINI_KEY` environment variable). Not required for reviewing frozen outputs.

No other software is required.

### Estimated Time and Storage Consumption

| Component | Time | Storage |
|---|---|---|
| RQ1 Table 3 (`table_3.py`) | ~5 min | <1 MB |
| RQ1 Table 4 (`table_4.py`) | ~5 min | <1 MB |
| RQ1 Table 13 (`table_13.py`) | ~30 min | <1 MB |
| RQ1 Tables 14–15 (`table_14_15.py`) | ~3 min | <1 MB |
| RQ1 Table 16 (`table_16.py`) | ~15 min | <1 MB |
| RQ1 Table 17 (`table_17.py`) | ~20 min | <1 MB |
| RQ2 topic × sentiment (`05_topic_sentiment.py`) | <1 min | <1 MB |
| RQ2 validation (`07_validation.py`) | <1 min | — |
| RQ3 risk classification (`risk_classifier.py`) | <1 min | — |
| Total artifact on disk | — | ~5 GB (mostly `index_document.csv`) |

**Note**: RQ2 steps 01–04 require access to the raw classified Reddit CSV files containing author identifiers and document text, which are not distributed for privacy reasons. The frozen outputs of each step are provided.

## Environment

### Accessibility

The artifact is publicly available at: **[FILL WITH GITHUB/ZENODO URL]**

### Set Up the Environment

```bash
git clone [REPO_URL]
cd osa-vpn-artifact
pip install -r requirements.txt
pip install tfcausalimpact
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
```

## Artifact Evaluation

### Main Results and Claims

#### Main Result 1: RQ1 Causal Impact on Discourse (Tables 3–4)

CausalImpact analysis shows that classified VPN content increased by +328% and classified Politics content increased by +1474% at the Age Verification deadline (July 2025), with no significant change at Royal Assent or Enforcement. UK Google Trends VPN search interest increased by +147%. These results are reproduced by [Experiment 1](#experiment-1-reproduce-table-3) and [Experiment 2](#experiment-2-reproduce-table-4).

#### Main Result 2: RQ1 Robustness (Tables 13, 14–17)

The Age Verification effect holds across all filter levels (Table 13), is not present at placebo dates (Table 14), is stable across platform compliance dates (Table 15), across post-window lengths (Table 16), and strengthens with UK-residency confidence (Table 17). These are reproduced by [Experiments 3–6](#experiment-3-reproduce-table-13).

#### Main Result 3: RQ2 Discourse Framing (Tables 5–6, Figures 4–5)

LDA identifies K=12 VPN topics and K=17 Politics topics. Sentiment is predominantly negative with near-zero pro-OSA sentiment (4–7% positive). Reproduced by [Experiment 7](#experiment-7-reproduce-rq2-topic-prevalence-and-sentiment).

#### Main Result 4: RQ3 VPN Privacy-Risk Classification (Table 8)

69 VPN services classified into Low (26), Medium (35), and High (8) risk categories. Reproduced by [Experiment 8](#experiment-8-reproduce-rq3-risk-classification).

### Experiments

#### Experiment 1: Reproduce Table 3

- Time: ~5 compute-minutes

```bash
python rq1/scripts/table_3.py
```

Reproduces CausalImpact relative effects for VPN and Politics classified content across three OSA milestones. Results may differ by up to ±5% from the paper due to the stochastic nature of Bayesian Structural Time Series inference.

#### Experiment 2: Reproduce Table 4

- Time: ~5 compute-minutes

```bash
python rq1/scripts/table_4.py
```

Reproduces CausalImpact on UK VPN Google Trends search interest under three specifications (no covariate, US covariate, lag-52 covariate).

#### Experiment 3: Reproduce Table 13

- Time: ~30 compute-minutes

```bash
python rq1/scripts/table_13.py
```

Runs 162 CausalImpact models across 2 groups × 9 filter levels × 3 milestones × 3 metrics. Output: `rq1/data/table13_reproduced.csv`.

#### Experiment 4: Reproduce Tables 14–15

- Time: ~3 compute-minutes

```bash
python rq1/scripts/table_14_15.py
```

Table 14: placebo-date pre-trend test with fake intervention dates before Age Verification. Table 15: date-sensitivity test across platform compliance dates.

#### Experiment 5: Reproduce Table 16

- Time: ~15 compute-minutes

```bash
python rq1/scripts/table_16.py
```

Post-window robustness: re-estimates effects at 4-week, 8-week, and 12-week windows.

#### Experiment 6: Reproduce Table 17

- Time: ~20 compute-minutes

```bash
python rq1/scripts/table_17.py
```

UK-residency threshold sensitivity: 60 models across k=1..5 thresholds.

#### Experiment 7: Reproduce RQ2 Topic Prevalence and Sentiment (Tables 5–6, Figure 5)

- Time: <1 minute

```bash
cd rq2/scripts
python 05_topic_sentiment.py
python 07_validation.py recount
```

Verify that VPN has 12 topics, Politics has 17, prevalence matches Table 5, and sentiment distributions match Table 6.

#### Experiment 8: Reproduce RQ3 Risk Classification (Table 8)

- Time: <1 minute

```bash
python rq3/scripts/risk_classifier.py
```

Expected output:
```
Providers: 69
Classification mismatches vs dataset: 0

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

#### Experiment 9: Verify Classification Outputs

- Time: <1 minute

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

#### Experiment 10: Verify Coherence Sweep (Figure 4)

- Time: <1 minute

```bash
python -c "
import pandas as pd
df = pd.read_csv('rq2/data/lda_coherence_sweep.csv')
print(df.to_string(index=False))
"
```

Coherence peaks at K=12 for VPN (C_V = 0.533) and K=17 for Politics (C_V = 0.536).

## Limitations

1. **CausalImpact is stochastic.** Bayesian Structural Time Series models involve posterior sampling, so reproduced effect sizes may differ by up to ±5% across runs. All directional findings and statistical significance are preserved.

2. **RQ2 corpus construction requires raw Reddit data.** Steps 01–04 of the RQ2 pipeline require the classified Reddit CSV files containing author identifiers and document text, which are not distributed for privacy reasons. The frozen outputs of each pipeline step are provided.

3. **LLM outputs are non-deterministic.** Re-running Gemini classification or sentiment analysis will produce different outputs because hosted models change between API versions. The frozen outputs used for the paper's reported results are provided.

4. **The "Reproduced" badge is not requested** because RQ2 corpus construction requires private data. We apply for "Available" and "Functional" badges, which are supported by the provided frozen outputs, verification scripts, and reproduction code.

## Notes on Reusability

- The **RQ1 reproduction scripts** demonstrate how to apply Bayesian Structural Time Series to weekly content and search-interest time series for causal inference around policy milestones.
- The **RQ2 pipeline** (scripts 01–07) is a reusable framework for Reddit discourse analysis combining LDA topic modelling with multi-model sentiment classification.
- The **RQ3 risk classification** is a deterministic, rule-based framework extensible to additional VPN providers.
- The **LLM prompts** provide templates for relevance classification and sentiment analysis of policy-related social media discourse.
- The **classification outputs** and **per-document index** enable researchers to construct alternative time series or apply different causal inference methods without needing access to Reddit text.