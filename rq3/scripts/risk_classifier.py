import pandas as pd
import os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'vpn_privacy_risk_google_trends.csv')
df = pd.read_csv(path)

print(f'Providers: {len(df)}')

print(f"\n--- Table 8 ---")
for cat in ['LOW', 'MEDIUM', 'HIGH']:
    print(f'  {cat}: {(df["risk_category"] == cat).sum()}')

markers = ['traffic_logging', 'connection_metadata', 'tracking_identifiers',
           'third_party_sharing', 'long_term_retention', 'policy_vagueness']

print(f"\n--- Marker counts (Section 6.1) ---")
for m in markers:
    print(f'  {m}: {(df[m].str.lower() == "yes").sum()}')
