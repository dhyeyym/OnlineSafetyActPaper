"""
reproduce_table17.py — UK-residency threshold sensitivity (k=1..5).

60 models: 2 groups × 2 definitions × 5 thresholds × 3 milestones.

Input:  rq1/data/table17_weekly_series.csv
Output: rq1/data/table17_reproduced.csv

Usage:
  python rq1/reproduce_table17.py
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

GROUPS = ["VPN", "Politics"]
DEFINITIONS = ["Raw", "Classified"]
THRESHOLDS = [1, 2, 3, 4, 5]


def run_ci(values, weeks, post_start):
    df = pd.DataFrame({"y": values}, index=weeks).astype(float)
    pre_end = post_start - pd.Timedelta(days=7)
    post_end = post_start + pd.Timedelta(days=7 * 7)
    ci = CausalImpact(df, [df.index.min(), pre_end], [post_start, post_end], alpha=0.05)
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
    path = os.path.join(DATA_DIR, "table17_weekly_series.csv")
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        print("Copy table17_weekly_series.csv from your results/table17_independent/ directory.")
        exit(1)

    weekly = pd.read_csv(path)
    weekly["week"] = pd.to_datetime(weekly["week"])
    weekly["k"] = weekly["k"].astype(int)

    total = len(GROUPS) * len(DEFINITIONS) * len(THRESHOLDS) * len(MILESTONES)
    print(f"Running {total} Table 17 models...\n")

    rows = []
    count = 0
    for group in GROUPS:
        for defn in DEFINITIONS:
            for k in THRESHOLDS:
                sub = weekly[(weekly["group"] == group) & (weekly["definition"] == defn) &
                             (weekly["k"] == k)].sort_values("week")
                if len(sub) == 0: continue
                for ms_name, ms_date in MILESTONES.items():
                    count += 1
                    print(f"[{count:2d}/{total}] {group:8s} {defn:10s} k>={k} {ms_name}", end=" ", flush=True)
                    try:
                        rel, p = run_ci(sub["total"], sub["week"], ms_date)
                        sig = "**" if p and p < 0.05 else ("*" if p and p < 0.10 else "")
                        print(f"{rel:+.0f}%{sig}" if rel else "ERROR")
                    except:
                        rel, p = None, None
                        print("ERROR")
                    rows.append({"group": group, "definition": defn, "k": k,
                                 "milestone": ms_name,
                                 "relative_effect_pct": round(rel, 1) if rel else None,
                                 "p_value": round(p, 4) if p else None})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA_DIR, "table17_reproduced.csv"), index=False)
    print(f"\nSaved: {DATA_DIR}/table17_reproduced.csv ({len(out)} rows)")