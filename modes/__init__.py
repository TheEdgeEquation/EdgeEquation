# modes/__init__.py

from .facts.domestic import run as run_fact_domestic
from .facts.overseas import run as run_fact_overseas

from .edges.morning import run as run_edges_morning
from .edges.evening import run as run_edges_evening

from .spotlight.run import run as run_spotlight
from .results.run import run as run_results

# Legacy modes that still exist and do NOT import broken engine modules
from .legacy.daily import run_daily
from .legacy.gotd import run_gotd
from .legacy.potd import run_potd
from .legacy.results import run_results_legacy
from .legacy.system_status import run_system_status

# IMPORTANT:
# Removed this broken import:
# from .legacy.daily_email import run_daily_email
# because it referenced engine.email_sender which no longer exists.

MODES = {
    # New architecture
    "fact_domestic": run_fact_domestic,
    "fact_overseas": run_fact_overseas,
    "edges_morning": run_edges_morning,
    "edges_evening": run_edges_evening,
    "spotlight": run_spotlight,
    "results": run_results,

    # Legacy (still functional)
    "daily": run_daily,
    "gotd": run_gotd,
    "potd": run_potd,
    "results_legacy": run_results_legacy,
    "system_status": run_system_status,
}
