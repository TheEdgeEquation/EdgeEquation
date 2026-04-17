# core/formatting.py

from datetime import datetime

BRAND_TAG = "#AnalyticsNotFeelings"

def _today_tag():
    return datetime.utcnow().strftime("%Y-%m-%d")

# ---------- FACTS ----------

def format_domestic_fact(text: str) -> str:
    return (
        f"📊 Domestic Fact of the Day — {_today_tag()}\n\n"
        f"{text}\n\n"
        f"{BRAND_TAG}"
    )

def format_overseas_fact(text: str) -> str:
    return (
        f"🌍 Overseas Fact of the Day — {_today_tag()}\n\n"
        f"{text}\n\n"
        f"{BRAND_TAG}"
    )

# ---------- EDGES ----------

def format_edges_morning(body: str) -> str:
    return (
        f"📈 Morning Edges — {_today_tag()}\n\n"
        f"{body}\n\n"
        f"{BRAND_TAG}"
    )

def format_edges_evening(body: str) -> str:
    return (
        f"🌙 Evening Edges — {_today_tag()}\n\n"
        f"{body}\n\n"
        f"{BRAND_TAG}"
    )

# ---------- SPOTLIGHT ----------

def format_spotlight(insight: str) -> str:
    return (
        f"🔦 Spotlight Insight — {_today_tag()}\n\n"
        f"{insight}\n\n"
        f"#MLB {BRAND_TAG}"
    )

# ---------- RESULTS ----------

def format_results(summary: str) -> str:
    return (
        f"📊 Daily Results — {_today_tag()}\n\n"
        f"{summary}\n\n"
        f"{BRAND_TAG}"
    )
