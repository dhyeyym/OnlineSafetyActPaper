"""
reproduce_table16.py — Post-window robustness (4, 8, 12 week windows).

Input:  rq1/data/vpn_time_series_classified_hp.csv
        rq1/data/politics_time_series_classified_hp.csv
        rq1/data/vpn_uk_content_timeseries_strict.csv
        rq1/data/politics_uk_content_timeseries_strict.csv
Output: rq1/data/table16_reproduced.csv

Usage:
  python rq1/reproduce_table16.py
"""
import os, warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")
import pandas as pd

if not hasattr(pd.DataFrame, "applymap"):
    pd.DataFrame.applymap = pd.DataFrame.map
from causalimpact import CausalImpact

DATA_DIR = os.path.join("rq1", "data")

MILESTONES = {
    "Oct2023": pd.Timestamp("2023-10-23"),
    "Mar2025": pd.Timestamp("2025-03-17"),
    "Jul2025": pd.Timestamp("2025-07-21"),
}

WINDOWS = [4, 8, 12]

SERIES = [
    ("VPN (all)",  "vpn_time_series_classified_hp.csv"),
    ("VPN (UK)",   "vpn_uk_content_timeseries_strict.csv"),
    ("Politics (all)", "politics_time_series_classified_hp.csv"),
    ("Politics (UK)",  "politics_uk_content_timeseries_strict.csv"),
]


def run_ci(df_indexed, post_start, window_weeks):
    pre_end = post_start - pd.Timedelta(days=7)
    post_end = post_start + pd.Timedelta(days=7 * (window_weeks - 1))
    ci = CausalImpact(df_indexed, [df_indexed.index.min(), pre_end],
                      [post_start, post_end], alpha=0.05)
    s = ci.summary()
    rel = p = None
    for line in s.split("\n"):
        if "Relative effect" in line and rel is None:
            for tok in line.split():
                try: rel = float(tok.strip("%()").replace(",", "")); break
                except: pass
        if "tail-area" in line:
            for tok in line.split():
                try:
                    v = float(tok)
                    if 0 <= v <= 1: p = v
                except: pass
    return rel, p


if __name__ == "__main__":
    print("TABLE 16 — Post-window robustness\n")

    rows = []
    for label, fname in SERIES:
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            print(f"SKIP {label}: {fname} not found"); continue

        df = pd.read_csv(path)
        df["week"] = pd.to_datetime(df["week"])
        df_i = df.set_index("week")[["total"]].astype(float)

        for ms_name, ms_date in MILESTONES.items():
            for w in WINDOWS:
                print(f"  {label} / {ms_name} / {w}wk ...", end=" ", flush=True)
                try:
                    rel, p = run_ci(df_i, ms_date, w)
                    sig = "**" if p and p < 0.05 else ("*" if p and p < 0.10 else "")
                    print(f"{rel:+.0f}%{sig}" if rel else "ERROR")
                except Exception as e:
                    rel, p = None, None
                    print("ERROR")
                rows.append({"series": label, "milestone": ms_name,
                             "window_weeks": w,
                             "relative_effect_pct": round(rel, 1) if rel else None,
                             "p_value": round(p, 4) if p else None})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA_DIR, "table16_reproduced.csv"), index=False)
    print(f"\nSaved: {DATA_DIR}/table16_reproduced.csv ({len(out)} rows)")