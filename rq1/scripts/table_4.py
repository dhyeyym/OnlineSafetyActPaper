"""
reproduce_table4.py — CausalImpact on UK VPN Google Trends search interest.

Inputs (in rq1/data/):
  google_trends_uk.csv
  google_trends_us.csv

Output: rq1/data/table4_reproduced.csv

Usage:
  python rq1/reproduce_table4.py
"""
import os, warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

if not hasattr(pd.DataFrame, "applymap"):
    pd.DataFrame.applymap = pd.DataFrame.map

from causalimpact import CausalImpact

DATA_DIR = os.path.join("rq1", "data")

# Google Trends uses Sunday-indexed weeks
GT_MILESTONES = {
    "Oct2023": pd.Timestamp("2023-10-22"),
    "Mar2025": pd.Timestamp("2025-03-16"),
    "Jul2025": pd.Timestamp("2025-07-20"),
}

def run_ci(df_indexed, post_start):
    pre_start = df_indexed.index.min()
    pre_end = post_start - pd.Timedelta(days=7)
    post_end = post_start + pd.Timedelta(days=7 * 7)
    ci = CausalImpact(df_indexed, [pre_start, pre_end], [post_start, post_end], alpha=0.05)
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

def sig(rel, p):
    if rel is None: return "ERROR"
    mark = "**" if p and p < 0.05 else ("*" if p and p < 0.10 else "")
    return f"{rel:+.1f}%{mark}"

if __name__ == "__main__":
    gt_uk = pd.read_csv(os.path.join(DATA_DIR, "google_trends_uk.csv"))
    gt_us = pd.read_csv(os.path.join(DATA_DIR, "google_trends_us.csv"))
    gt_uk.columns = gt_uk.columns.str.strip()
    gt_us.columns = gt_us.columns.str.strip()
    gt_uk["week"] = pd.to_datetime(gt_uk["week"])
    gt_us["week"] = pd.to_datetime(gt_us["week"])

    no_cov = gt_uk.set_index("week")[["vpn"]].astype(float)

    merged = gt_uk[["week", "vpn"]].merge(gt_us[["week", "vpn_us"]], on="week")
    us_cov = merged.set_index("week").astype(float)

    lag = gt_uk[["week", "vpn"]].copy()
    lag["vpn_lag52"] = lag["vpn"].shift(52)
    lag52 = lag.dropna().set_index("week").astype(float)

    specs = [("No covariate", no_cov), ("US covariate", us_cov), ("Lag-52", lag52)]

    rows = []
    for spec_name, df_i in specs:
        for ms_name, ms_date in GT_MILESTONES.items():
            print(f"  {spec_name} / {ms_name} ...", end=" ", flush=True)
            rel, p = run_ci(df_i, ms_date)
            print(sig(rel, p))
            rows.append({"specification": spec_name, "milestone": ms_name,
                         "relative_effect_pct": round(rel, 1) if rel else None,
                         "p_value": round(p, 4) if p else None})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA_DIR, "table4_reproduced.csv"), index=False)
    print(f"\n{out.to_string(index=False)}")
    print(f"\nSaved: {DATA_DIR}/table4_reproduced.csv")