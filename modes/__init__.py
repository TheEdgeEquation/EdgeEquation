# modes/__init__.py

from .facts.domestic import run as run_fact_domestic
from .facts.overseas import run as run_fact_overseas

from .edges.morning import run as run_edges_morning
from .edges.evening import run as run_edges_evening

from .spotlight.run import run as run_spotlight
from .results.run import run as run_results

# IMPORTANT:
# All legacy imports removed because the folder no longer exists.

MODES = {
    "fact_domestic": run_fact_domestic,
    "fact_overseas": run_fact_overseas,
    "edges_morning": run_edges_morning,
    "edges_evening": run_edges_evening,
    "spotlight": run_spotlight,
    "results": run_results,
}
