import os

import pandas as pd

ARTIFACT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ARTIFACT_DIR, "data", "vpn_privacy_risk_google_trends.csv")

RISK_CATEGORIES = ["LOW", "MEDIUM", "HIGH"]
MARKERS = [
    "traffic_logging",
    "connection_metadata",
    "tracking_identifiers",
    "third_party_sharing",
    "long_term_retention",
    "policy_vagueness",
]

df = pd.read_csv(DATA_PATH)

print(f"Providers: {len(df)}")

print("\n--- Table 8 ---")
for category in RISK_CATEGORIES:
    count = (df["risk_category"] == category).sum()
    print(f"  {category}: {count}")

print("\n--- Marker counts (Section 6.1) ---")
for marker in MARKERS:
    count = (df[marker].str.lower() == "yes").sum()
    print(f"  {marker}: {count}")
