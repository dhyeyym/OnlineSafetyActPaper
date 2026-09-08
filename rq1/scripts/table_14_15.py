"""
reproduce_table14_15.py — Google Trends placebo and date-sensitivity tests.

Table 14: Placebo-date pre-trend test (fake dates before Age Verification).
Table 15: Date-sensitivity test (platform compliance date cluster).

Input:  rq1/data/google_trends_uk.csv
Output: rq1/data/table14_reproduced.csv, rq1/data/table15_reproduced.csv

Usage:
  python rq1/reproduce_table14_15.py
"""
import os, warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")
import pandas as pd

if not hasattr(pd.DataFrame, "applymap"):
    pd.DataFrame.applymap = pd.DataFrame.map
from causalimpact import CausalImpact

DATA_DIR = os.path.join("rq1", "data")


def run_ci(df_indexed, post_start):
    pre_end = post_start - pd.Timedelta(days=7)
    post_end = post_start + pd.Timedelta(days=7 * 7)
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
    gt = pd.read_csv(os.path.join(DATA_DIR, "google_trends_uk.csv"))
    gt.columns = gt.columns.str.strip()
    gt["week"] = pd.to_datetime(gt["week"])
    df = gt.set_index("week")[["vpn"]].astype(float)

    # --- Table 14: placebo dates before Age Verification ---
    print("=" * 60)
    print("TABLE 14 — Placebo-date pre-trend test")
    print("=" * 60)

    placebo_dates = [
        ("12 weeks before", pd.Timestamp("2025-04-27")),
        ("10 weeks before", pd.Timestamp("2025-05-11")),
        ("8 weeks before",  pd.Timestamp("2025-05-25")),
        ("6 weeks before",  pd.Timestamp("2025-06-08")),
        ("4 weeks before",  pd.Timestamp("2025-06-22")),
    ]

    t14_rows = []
    for label, date in placebo_dates:
        print(f"  {label} ({date.date()}) ...", end=" ", flush=True)
        rel, p = run_ci(df, date)
        sig = "**" if p and p < 0.05 else ("*" if p and p < 0.10 else "")
        print(f"{rel:+.1f}%{sig} (p={p:.2f})" if rel else "ERROR")
        t14_rows.append({"fake_date": str(date.date()), "weeks_before": label,
                         "relative_effect_pct": round(rel, 1) if rel else None,
                         "p_value": round(p, 2) if p else None})

    pd.DataFrame(t14_rows).to_csv(os.path.join(DATA_DIR, "table14_reproduced.csv"), index=False)
    print(f"Saved: {DATA_DIR}/table14_reproduced.csv")

    # --- Table 15: date-sensitivity across platform compliance dates ---
    print(f"\n{'=' * 60}")
    print("TABLE 15 — Date-sensitivity test")
    print("=" * 60)

    compliance_dates = [
        ("Discord (21 Jul)",  pd.Timestamp("2025-07-20")),
        ("Aylo (24 Jul)",     pd.Timestamp("2025-07-20")),
        ("Reddit (25 Jul)",   pd.Timestamp("2025-07-20")),
        ("X (26 Jul)",        pd.Timestamp("2025-07-20")),
    ]
    # All fall in same Sunday-indexed GT week (20 Jul)

    t15_rows = []
    for label, date in compliance_dates:
        print(f"  {label} ...", end=" ", flush=True)
        rel, p = run_ci(df, date)
        sig = "**" if p and p < 0.05 else ""
        print(f"{rel:+.1f}%{sig}" if rel else "ERROR")
        t15_rows.append({"treatment_date": label,
                         "relative_effect_pct": round(rel, 1) if rel else None,
                         "p_value": round(p, 4) if p else None})

    pd.DataFrame(t15_rows).to_csv(os.path.join(DATA_DIR, "table15_reproduced.csv"), index=False)
    print(f"Saved: {DATA_DIR}/table15_reproduced.csv")