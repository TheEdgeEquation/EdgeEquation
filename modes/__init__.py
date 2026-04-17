# modes/__init__.py

# ------------------------------------------------------------
# Legacy Modes
# ------------------------------------------------------------
from .legacy.daily_email import run_daily_email
from .legacy.system_status import run_system_status
from .legacy.daily import run_daily
from .legacy.gotd import run_gotd
from .legacy.potd import run_potd
from .legacy.first_inning_potd import run_first_inning_potd
from .legacy.results import run_results
from .legacy.weekly import run_weekly
from .legacy.monthly import run_monthly

# ------------------------------------------------------------
# US 3.0 Modes
# ------------------------------------------------------------
from .us3.model_notes import run_model_notes
from .us3.primary_signal import run_primary_signal
from .us3.prop_efficiency_signal import run_prop_efficiency_signal
from .us3.run_suppression_signal import run_run_suppression_signal
from .us3.high_confidence_outlier import run_high_confidence_outlier
from .us3.secondary_alignment import run_secondary_alignment

# ------------------------------------------------------------
# Global 3.0 Modes
# ------------------------------------------------------------
from .global3.global_primary_signal import run_global_primary_signal
from .global3.global_prop_efficiency_signal import run_global_prop_efficiency_signal
from .global3.global_run_suppression_signal import run_global_run_suppression_signal
from .global3.global_high_confidence_outlier import run_global_high_confidence_outlier
from .global3.global_secondary_alignment import run_global_secondary_alignment


# ------------------------------------------------------------
# Mode Registry
# ------------------------------------------------------------
MODES = {
    # Legacy
    "daily_email": run_daily_email,
    "system_status": run_system_status,
    "daily": run_daily,
    "gotd": run_gotd,
    "potd": run_potd,
    "first_inning_potd": run_first_inning_potd,
    "results": run_results,
    "weekly": run_weekly,
    "monthly": run_monthly,

    # US 3.0
    "model_notes": run_model_notes,
    "primary_signal": run_primary_signal,
    "prop_efficiency_signal": run_prop_efficiency_signal,
    "run_suppression_signal": run_run_suppression_signal,
    "high_confidence_outlier": run_high_confidence_outlier,
    "secondary_alignment": run_secondary_alignment,

    # Global 3.0
    "global_primary_signal": run_global_primary_signal,
    "global_prop_efficiency_signal": run_global_prop_efficiency_signal,
    "global_run_suppression_signal": run_global_run_suppression_signal,
    "global_high_confidence_outlier": run_global_high_confidence_outlier,
    "global_secondary_alignment": run_global_secondary_alignment,
}
from .edges import morning, evening

MODES = {
    "edges_morning": morning,
    "edges_evening": evening,
    # ...existing modes...
}
from .facts import domestic, overseas

MODES.update({
    "fact_domestic": domestic,
    "fact_overseas": overseas,
})


