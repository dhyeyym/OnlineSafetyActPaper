"""
reproduce_table3.py — CausalImpact on classified Reddit content.

Inputs (in rq1/data/):
  vpn_time_series_classified_hp.csv
  politics_time_series_classified_hp.csv

Output: rq1/data/table3_reproduced.csv

Usage:
  python rq1/reproduce_table3.py
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

MILESTONES = {
    "Oct2023": pd.Timestamp("2023-10-23"),
    "Mar2025": pd.Timestamp("2025-03-17"),
    "Jul2025": pd.Timestamp("2025-07-21"),
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
    files = {
        "VPN": "vpn_time_series_classified_hp.csv",
        "Politics": "politics_time_series_classified_hp.csv",
    }

    rows = []
    for group, fname in files.items():
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            print(f"SKIP {group}: {fname} not found"); continue
        df = pd.read_csv(path)
        df["week"] = pd.to_datetime(df["week"])
        df_i = df.set_index("week")[["total"]].astype(float)

        for ms_name, ms_date in MILESTONES.items():
            print(f"  {group} / {ms_name} ...", end=" ", flush=True)
            rel, p = run_ci(df_i, ms_date)
            print(sig(rel, p))
            rows.append({"group": group, "milestone": ms_name,
                         "relative_effect_pct": round(rel, 1) if rel else None,
                         "p_value": round(p, 4) if p else None})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA_DIR, "table3_reproduced.csv"), index=False)
    print(f"\n{out.to_string(index=False)}")
    print(f"\nSaved: {DATA_DIR}/table3_reproduced.csv")