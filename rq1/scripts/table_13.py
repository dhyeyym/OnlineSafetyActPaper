"""
reproduce_table13.py — CausalImpact on all Table 13 filter levels.

162 models: 2 groups × 9 filters × 3 milestones × 3 metrics.

Input:  rq1/data/table13_weekly_series.csv
Output: rq1/data/table13_reproduced.csv

Usage:
  python rq1/reproduce_table13.py
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
FILTERS = ["Unmatched (non-UK)", "Unmatched", "Unmatched (UK)",
           "Raw", "Raw (UK)", "Matched", "Matched (UK)",
           "Classified", "Classified (UK)"]
METRICS = ["posts", "comments", "total"]


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
    weekly = pd.read_csv(os.path.join(DATA_DIR, "table13_weekly_series.csv"))
    weekly["week"] = pd.to_datetime(weekly["week"])

    total = len(GROUPS) * len(FILTERS) * len(MILESTONES) * len(METRICS)
    print(f"Running {total} Table 13 models...\n")

    rows = []
    count = 0
    for group in GROUPS:
        for filt in FILTERS:
            sub = weekly[(weekly["group"] == group) & (weekly["filter"] == filt)].sort_values("week")
            if len(sub) == 0: continue
            for ms_name, ms_date in MILESTONES.items():
                for metric in METRICS:
                    count += 1
                    print(f"[{count:3d}/{total}] {group:8s} {filt:22s} {metric:8s} {ms_name}", end=" ", flush=True)
                    try:
                        rel, p = run_ci(sub[metric], sub["week"], ms_date)
                        sig = "**" if p and p < 0.05 else ("*" if p and p < 0.10 else "")
                        print(f"{rel:+.0f}%{sig}" if rel else "ERROR")
                    except Exception as e:
                        rel, p = None, None
                        print(f"ERROR")
                    rows.append({"group": group, "filter": filt, "metric": metric,
                                 "milestone": ms_name,
                                 "relative_effect_pct": round(rel, 1) if rel else None,
                                 "p_value": round(p, 4) if p else None})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA_DIR, "table13_reproduced.csv"), index=False)
    print(f"\nSaved: {DATA_DIR}/table13_reproduced.csv ({len(out)} rows)")