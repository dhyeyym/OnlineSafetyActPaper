"""
rq3_risk_classifier.py — Deterministic privacy-risk classification (Section 6).

    Risk(VPN) =
        High   if T ∨ (M ∧ R ∧ S)
        Medium if M ∨ I ∨ S ∨ (V ∧ R)
        Low    otherwise

    T = traffic_logging, M = connection_metadata, S = third_party_sharing,
    R = long_term_retention, I = tracking_identifiers, V = policy_vagueness.
    Unclear values treated as absence (False).

Usage:
    python rq3_risk_classifier.py

Reads:  data/vpn_privacy_risk_google_trends.csv
Prints: Table 8 counts and per-marker counts (Section 6.1)
"""
import pandas as pd

def classify_risk(T, M, S, R, I, V):
    if T or (M and R and S):
        return "HIGH"
    if M or I or S or (V and R):
        return "MEDIUM"
    return "LOW"

if __name__ == "__main__":
    df = pd.read_csv("data/vpn_privacy_risk_google_trends.csv")
    markers = ["traffic_logging", "connection_metadata", "tracking_identifiers",
               "third_party_sharing", "long_term_retention", "policy_vagueness"]

    reproduced = df.apply(lambda r: classify_risk(
        *(r[m].strip().lower() == "yes" for m in markers)), axis=1)

    mismatches = (reproduced != df["risk_category"]).sum()
    print(f"Providers: {len(df)}")
    print(f"Classification mismatches vs dataset: {mismatches}")

    print(f"\n--- Table 8 ---")
    for cat in ["LOW", "MEDIUM", "HIGH"]:
        print(f"  {cat}: {(reproduced == cat).sum()}")

    print(f"\n--- Marker counts (Section 6.1) ---")
    for m in markers:
        print(f"  {m}: {(df[m].str.lower() == 'yes').sum()}")