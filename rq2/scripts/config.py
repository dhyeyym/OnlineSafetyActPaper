from pathlib import Path
import os

BASE_DIR     = Path(os.getenv("OSA_BASE_DIR", Path(__file__).resolve().parent.parent))
ORIGINAL_DIR = BASE_DIR / "data" / "original"
GEO_DIR      = BASE_DIR / "data" / "geo"
RESULTS_DIR  = BASE_DIR / "data"

START_DATE = "2021-10-26"
END_DATE   = "2025-10-26"

SKIP_AUTHORS = {"[deleted]", "AutoModerator", ""}

VPN_SUBREDDITS = {
    "MullvadVPN", "nordvpn", "PrivateInternetAccess", "ProtonVPN",
    "Surfshark", "Windscribe", "VPN", "PrivacyGuides", "privacy",
    "degoogle", "censorship",
}

POLITICS_SUBREDDITS = {
    "AskUK", "BritishProblems", "CasualUK", "England", "FreeSpeech",
    "GreenAndPleasant", "labour", "LabourUK", "LegalAdviceUK", "LibDem",
    "NorthernIreland", "Scotland", "Tories", "UKGreens", "uklaw",
    "ukpolitics", "UnitedKingdom", "Wales",
}

UK_GEO_SUBREDDITS = {
    "london", "Edinburgh", "glasgow", "manchester", "Birmingham",
    "bristol", "Cardiff", "Leeds", "Liverpool", "Belfast",
    "AskLondon", "LondonUnderground", "londonersr4r",
    "NorthEastUK", "UKJobs", "uklandlords",
    "drivingUK", "policeuk", "CoronavirusUK", "heyUK", "BirminghamUK",
    "MakeFriendsUK", "MakeMoneyInUK", "UK_Food", "UK_Pets", "UK_News24",
    "UKcoins", "SkilledWorkerVisaUK", "HumanResourcesUK", "ContractorUK",
    "ActuaryUK", "ArchitectsUK", "AmazonFlexUK", "AmexUK", "apprenticeuk",
    "JustEatUK", "McDonaldsUK",
}

CLASSIFIED_FILES = [
    ("classified_vpn_submissions_strict.csv",     "vpn",      "submission", "relevant_strict"),
    ("classified_vpn_comments_strict.csv",        "vpn",      "comment",    "relevant_strict"),
    ("classified_vpn_osa_submissions_strict.csv",  "vpn",      "submission", "relevant_strict"),
    ("classified_vpn_osa_comments_strict.csv",     "vpn",      "comment",    "relevant_strict"),
    ("classified_politics_submissions.csv",        "politics", "submission", "relevant"),
    ("classified_politics_comments.csv",           "politics", "comment",    "relevant"),
    ("classified_politics_vpn_submissions.csv",    "politics", "submission", "relevant"),
    ("classified_politics_vpn_comments.csv",       "politics", "comment",    "relevant"),
]

LDA_K = {"vpn": 12, "politics": 17}
LDA_RANDOM_STATE = 42
LDA_PASSES = 15

EXTRA_STOPWORDS = {
    "vpn", "reddit", "use", "like", "want", "know", "think", "people",
    "thing", "just", "get", "would", "could", "really", "also", "make",
    "need", "time", "way", "one", "even", "say", "see", "go", "look",
    "come", "give", "take", "good", "new", "uk", "post", "comment",
}

VPN_LABELS = {
    0:  "App/browser access",
    1:  "ISP visibility, DNS & Tor",
    2:  "Geo-blocking & site access",
    3:  "VPN no-logs & court orders",
    4:  "Government surveillance & OSA",
    5:  "Surveillance & anonymity",
    6:  "Opsec & anonymity practices",
    7:  "Age verification & digital ID",
    8:  "Censorship circumvention & streaming",
    9:  "VPN bans & state censorship",
    10: "End-to-end encryption",
    11: "VPN connectivity & blocking",
}

POLITICS_LABELS = {
    0:  "Ofcom notices & media",
    1:  "Technical circumvention",
    2:  "OSA circumvention & petitions",
    3:  "Subscription costs & ISP services",
    4:  "OSA parliamentary debate",
    5:  "Moderation",
    6:  "Online abuse & harmful content",
    7:  "Parliamentary process",
    8:  "End-to-end encryption & security",
    9:  "OSA general discussion",
    10: "Government ministers & offices",
    11: "Ofcom & broadcast regulation",
    12: "Platform compliance & liability",
    13: "Child safety & age-restricted content",
    14: "Free speech & social media",
    15: "Facial recognition & policing",
    16: "Age verification mechanisms",
}

TOPIC_LABELS = {"vpn": VPN_LABELS, "politics": POLITICS_LABELS}

CARDIFF_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
GEMINI_MODEL  = "gemini-2.5-flash-lite"
SENTIMENT_LABELS = ["negative", "neutral", "positive"]
